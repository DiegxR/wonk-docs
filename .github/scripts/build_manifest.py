#!/usr/bin/env python3
"""Arma el manifiesto que recibe el agente y clasifica el cambio (casos A-D).

Entradas:
  - event JSON ($GITHUB_EVENT_PATH) de repository_dispatch / workflow_dispatch
  - o argumentos explícitos (--repo, --sha, --before, --files, --diff)

Salidas:
  - <out-dir>/manifest.json   manifiesto estructurado (entrada del agente)
  - <out-dir>/manifest.md     manifiesto legible (se le pasa al modelo)
  - GITHUB_OUTPUT: case, reason, candidates, pages_count

Si el payload no trae la lista de archivos cambiados, se consulta la API de
GitHub con el token disponible (AGENT_READ_TOKEN si existe, si no GITHUB_TOKEN).
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Mismas exclusiones que el aviso del repo de código (defensa en profundidad).
EXCLUDE_PATTERNS = [
    "*.log", "*.xml", ".coverage", "coverage.xml",
    "dist/*", "build/*", "node_modules/*", ".venv/*", "venv/*",
    "*__pycache__/*", "*.pyc", "*.pyo", "*.pytest_cache/*", "*.ruff_cache/*",
    "*.lock", "uv.lock", "package-lock.json",
    "insumos/*", "*insumos/*", "ttls/*", "*.ttl",
    "*.tfvars", "*.tfstate", "bootstrap/*-creds.yaml", "externalsecret*.yaml",
    "*.svg", "*.png", "*.jpg", "*.pdf",
]

NOISE_PATTERNS = [
    "*tests/*", "test_*", "*_test.py", "*_test.ts",
    "*.md", ".github/*", "*.example", "Makefile", "CHANGELOG*",
]

DOC_EXTENSIONS = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".kt",
    ".rb", ".rs", ".php", ".cs", ".sql", ".sh", ".bash", ".yml", ".yaml",
    ".toml", ".json", ".ini", ".cfg", ".tf", ".hcl", ".proto", ".graphql",
}

DOC_NAMES = {"Dockerfile", "docker-compose.yml", "pyproject.toml", "setup.py", "Makefile"}

# Un refactor "grande" se reconoce con esta cantidad de renames/borrados.
RENAMING_THRESHOLD = 5

STATUS_MAP = {"added": "A", "modified": "M", "removed": "D", "renamed": "R",
              "copied": "C", "changed": "M", "unchanged": "M"}


# ---------------------------------------------------------------- utilidades

def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def is_documentable(path: str) -> bool:
    if matches(path, EXCLUDE_PATTERNS) or matches(path, NOISE_PATTERNS):
        return False
    if Path(path).name in DOC_NAMES:
        return True
    return Path(path).suffix.lower() in DOC_EXTENSIONS


def api_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "wonk-docs-manifest",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def gh_token() -> str:
    return os.environ.get("AGENT_READ_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""


def parse_frontmatter(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    try:
        end = text.index("\n---", 3)
    except ValueError:
        return None
    block = text[3:end]
    data: dict = {}
    current_list: str | None = None
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.lstrip().startswith("- ") and current_list:
            data[current_list].append(line.lstrip()[2:].strip().strip("'\""))
            continue
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        if value == "":
            data[key] = []
            current_list = key
        else:
            data[key] = value.strip("'\"")
            current_list = None
    return data


def load_pages(repo_root: Path, source_repo: str) -> list[dict]:
    pages = []
    for base in ("runtime", "wiki"):
        root = repo_root / base
        if not root.exists():
            continue
        for md in sorted(root.rglob("*.md")):
            fm = parse_frontmatter(md)
            if not fm:
                continue
            fuente = str(fm.get("fuente_repo", ""))
            if source_repo and fuente and source_repo.split("/")[-1] not in fuente:
                continue
            rutas = fm.get("rutas", [])
            if isinstance(rutas, str):
                rutas = [rutas]
            pages.append({
                "page": str(md.relative_to(repo_root)).replace("\\", "/"),
                "fuente_repo": fuente,
                "commit_verificado": str(fm.get("commit_verificado", "")),
                "estado": str(fm.get("estado", "")),
                "titulo": str(fm.get("titulo", md.stem)),
                "rutas": [str(r) for r in rutas],
            })
    return pages


def ruta_base(ruta: str) -> str:
    return ruta.split("#", 1)[0].strip()


def covers(page: dict, path: str) -> bool:
    for r in page["rutas"]:
        base = ruta_base(r)
        if base == path or base.startswith(path + "/") or path.startswith(base + "/"):
            return True
    return False


def diff_solo_comentarios(diff: str) -> bool:
    """True si el diff solo agrega/quita líneas en blanco o comentarios."""
    interesting = 0
    for line in diff.splitlines():
        if not (line.startswith("+") or line.startswith("-")):
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        body = line[1:].strip()
        if not body:
            continue
        if body.startswith(("#", "//", "*", '"""', "'''", "--", "%", "@")):
            continue
        interesting += 1
    return interesting == 0


# ----------------------------------------------------------------- payloads

def load_event(args: argparse.Namespace) -> dict:
    """Normaliza el evento a {source_repo, sha, before, files, diff, ...}."""
    event: dict = {}
    path = os.environ.get("GITHUB_EVENT_PATH")
    if path and Path(path).exists():
        event = json.loads(Path(path).read_text(encoding="utf-8"))

    if event.get("client_payload"):
        p = event["client_payload"]
    elif event.get("inputs"):
        p = event["inputs"]
    else:
        p = {}

    payload = {
        "source_repo": p.get("source_repo") or args.repo or "",
        "sha": p.get("sha") or args.sha or "",
        "before": p.get("before") or args.before or "",
        "compare_url": p.get("compare_url") or "",
        "commit_message": p.get("commit_message") or "",
        "pusher": p.get("pusher") or "",
        "run_url": p.get("run_url") or "",
        "files": p.get("files") or [],
        "diff": p.get("diff") or "",
        "source_docs": p.get("source_docs") or {},
        "open_pr": str(p.get("open_pr", "true")).lower() != "false",
    }
    if args.files:
        payload["files"] = json.loads(args.files)
    if args.diff:
        payload["diff"] = args.diff
    if not payload["source_repo"] and args.repo:
        payload["source_repo"] = args.repo
    return payload


def fetch_files_from_api(source_repo: str, sha: str, before: str) -> list[dict]:
    """Último recurso: si el payload no trae archivos, los pide a la API."""
    token = gh_token()
    if not token or not source_repo:
        return []
    zero = "0" * 40
    base = f"https://api.github.com/repos/{source_repo}"
    try:
        if before and before != zero:
            data = api_get(f"{base}/compare/{before}...{sha}", token)
            raw = data.get("files", [])
        else:
            data = api_get(f"{base}/commits/{sha}", token)
            raw = data.get("files", [])
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        print(f"::warning::no se pudo leer los archivos de {source_repo}: {exc}")
        return []
    out = []
    for f in raw:
        out.append({
            "status": STATUS_MAP.get(f.get("status", "M"), "M"),
            "path": f.get("filename", ""),
            "old_path": f.get("previous_filename"),
        })
    return out


# ----------------------------------------------------------- clasificación

def classify(payload: dict, pages: list[dict]) -> dict:
    files = payload.get("files") or []
    if not files and payload.get("source_repo"):
        files = fetch_files_from_api(
            payload["source_repo"], payload.get("sha", ""), payload.get("before", "")
        )
        payload["files"] = files

    documentable = [f for f in files if is_documentable(f.get("path", ""))]
    excluded = [f for f in files if f not in documentable]

    if not documentable:
        return {"case": "A", "reason": "sin rutas documentables (pruebas, formato o exclusiones)",
                "documentable": [], "excluded": excluded, "candidates": [], "uncovered": []}

    diff = payload.get("diff", "")
    if diff and diff_solo_comentarios(diff):
        return {"case": "A", "reason": "el diff solo cambia comentarios o líneas en blanco",
                "documentable": documentable, "excluded": excluded, "candidates": [], "uncovered": []}

    rutas_idx = {}
    for page in pages:
        for r in page["rutas"]:
            rutas_idx.setdefault(ruta_base(r), []).append(page["page"])

    renames = [f for f in documentable if f.get("status") == "R"]
    deletes = [f for f in documentable if f.get("status") == "D"]

    stale_rutas = []
    for r in rutas_idx:
        if any(f.get("path") == r for f in deletes):
            stale_rutas.append(r)
        if any(f.get("old_path") == r for f in renames):
            stale_rutas.append(r)

    if len(renames) + len(deletes) >= RENAMING_THRESHOLD or stale_rutas:
        why = []
        if stale_rutas:
            why.append(f"rutas del frontmatter que dejan de existir: {', '.join(sorted(set(stale_rutas))[:5])}")
        if len(renames) + len(deletes) >= RENAMING_THRESHOLD:
            why.append(f"{len(renames)} renames / {len(deletes)} borrados (>= {RENAMING_THRESHOLD})")
        return {"case": "C", "reason": "; ".join(why),
                "documentable": documentable, "excluded": excluded,
                "candidates": [p["page"] for p in pages], "uncovered": []}

    covered, uncovered = [], []
    for f in documentable:
        path = f.get("path", "")
        hits = [p["page"] for p in pages if covers(p, path)]
        if hits:
            covered.append({"path": path, "status": f.get("status", ""), "pages": hits})
        else:
            uncovered.append({"path": path, "status": f.get("status", "")})

    candidates = sorted({hit for c in covered for hit in c["pages"]})

    if uncovered:
        return {"case": "D", "reason": "contenido nuevo sin página que lo cubra",
                "documentable": documentable, "excluded": excluded,
                "candidates": candidates, "uncovered": uncovered}

    return {"case": "B", "reason": "rutas cambiadas cubiertas por páginas existentes",
            "documentable": documentable, "excluded": excluded,
            "candidates": candidates, "uncovered": []}


# --------------------------------------------------------------- manifiesto

CASE_TITLES = {
    "A": "A. No hay nada que agregar",
    "B": "B. Cambio incremental",
    "C": "C. Refactor grande",
    "D": "D. Contenido nuevo",
}


def render_markdown(payload: dict, verdict: dict, pages: list[dict]) -> str:
    lines = [
        "# Manifiesto de sincronización",
        "",
        f"- Repo: `{payload['source_repo']}`",
        f"- SHA nuevo: `{payload['sha']}`",
        f"- SHA anterior: `{payload['before'] or 'n/a'}`",
        f"- Commit: {payload['commit_message'] or '(sin mensaje)'}",
        f"- Autor del push: {payload['pusher'] or 'n/a'}",
        f"- Comparación: {payload['compare_url'] or 'n/a'}",
        f"- Corrida: {payload['run_url'] or 'n/a'}",
        "",
        f"**Clasificación propuesta: {CASE_TITLES[verdict['case']]}**",
        "",
        f"Motivo: {verdict['reason']}",
        "",
        "## Archivos cambiados",
        "",
        "| Estado | Archivo |",
        "| --- | --- |",
    ]
    for f in payload["files"]:
        status = {"A": "added", "M": "modified", "D": "removed", "R": "renamed"}.get(
            f.get("status", ""), f.get("status", ""))
        name = f.get("path", "")
        if f.get("old_path"):
            name = f"{f['old_path']} -> {name}"
        lines.append(f"| {status} | `{name}` |")
    if not payload["files"]:
        lines.append("| - | (sin archivos en el payload) |")

    lines += ["", "## Excluidos o sin interés documental", ""]
    if verdict["excluded"]:
        lines += [f"- `{f.get('path', '')}`" for f in verdict["excluded"]]
    else:
        lines.append("- (ninguno)")

    lines += ["", "## Páginas candidatas", ""]
    if verdict["candidates"]:
        for page in verdict["candidates"]:
            meta = next((p for p in pages if p["page"] == page), {})
            lines.append(f"- `{page}` (commit_verificado: `{meta.get('commit_verificado', 'n/a')}`, "
                         f"estado: {meta.get('estado', 'n/a')})")
            for r in meta.get("rutas", []):
                lines.append(f"  - rutas: `{r}`")
    else:
        lines.append("- (ninguna: no hay páginas que cubran estas rutas)")

    if verdict["uncovered"]:
        lines += ["", "## Rutas sin página (posible caso D)", ""]
        lines += [f"- `{u['path']}`" for u in verdict["uncovered"]]

    lines += ["", "## Diff (recortado)", "", "```diff"]
    diff = payload.get("diff", "")
    lines.append(diff[:40000] if diff else "(sin diff: se recomienda enviarlo desde el aviso del repo)")
    if len(diff) > 40000:
        lines.append("... diff truncado ...")
    lines += ["```", "", "## Documentación existente del repo fuente", ""]

    for name, content in (payload.get("source_docs") or {}).items():
        lines += [f"### {name}", "", "```markdown", content[:8000], "```", ""]

    lines += [
        "## Contrato del agente (recordatorio)",
        "",
        "1. Solo escribe en `runtime/`; nunca toca `wiki/` ni escribe en `main`.",
        "2. Sube `commit_verificado` al SHA nuevo y usa permalinks `blob/<sha>`.",
        "3. Máximo acotado de páginas por corrida; si la confianza es baja, abre un issue.",
        "4. Nunca copia bloques largos de código: enlaza `ruta#Lx-Ly`.",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out-dir", default="_run")
    ap.add_argument("--repo", default="")
    ap.add_argument("--sha", default="")
    ap.add_argument("--before", default="")
    ap.add_argument("--files", default="")
    ap.add_argument("--diff", default="")
    args = ap.parse_args()

    root = Path(args.repo_root)
    payload = load_event(args)
    pages = load_pages(root, payload["source_repo"])
    verdict = classify(payload, pages)

    manifest = {**payload, "pages": pages, **verdict}
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "manifest.md").write_text(render_markdown(payload, verdict, pages), encoding="utf-8")

    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as fh:
            fh.write(f"case={verdict['case']}\n")
            fh.write(f"reason={verdict['reason'].replace(chr(10), ' ')[:200]}\n")
            fh.write(f"candidates={' '.join(verdict['candidates'])}\n")
            fh.write(f"uncovered={len(verdict['uncovered'])}\n")
            fh.write(f"open_pr={'true' if payload['open_pr'] else 'false'}\n")
            fh.write(f"source_repo={payload['source_repo']}\n")
            fh.write(f"sha={payload['sha']}\n")

    print(f"caso {verdict['case']}: {verdict['reason']}")
    print(f"paginas candidatas: {len(verdict['candidates'])} | sin cubrir: {len(verdict['uncovered'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
