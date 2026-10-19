#!/usr/bin/env python3
"""Simulador de documentación sin IA (dry-run con cambios reales en runtime/).

Lee `_run/manifest.json` (salida de build_manifest.py) y aplica acciones
deterministas según el caso A-D, sin llamar a ningún modelo:

  - A: no toca nada.
  - B: sube `commit_verificado` de las páginas candidatas al SHA nuevo.
  - C: marca las páginas candidatas como `estado: desactualizado`.
  - D: crea páginas stub para cada ruta sin página (más lo del caso B).

Toda acción se registra en `_run/actions.txt` con mensajes del tipo
"se creó el archivo X" / "se actualizó el archivo X", que el workflow imprime
como ::notice:: y agrega al cuerpo del PR.

Salvaguardas (mismas reglas que el agente real):
  - solo escribe bajo `runtime/<repo-fuente>/`;
  - máximo MAX_PAGES páginas por corrida;
  - las páginas creadas quedan en `estado: borrador` y
    `generado_por: simulacion`, para que nadie las confirme con las reales.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

MAX_PAGES = 10


def slugify(path: str) -> str:
    stem = Path(path.split("#", 1)[0]).stem
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return slug or "pagina"


def set_frontmatter_value(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^({re.escape(key)}):.*$", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(f"{key}: {value}", text, count=1)
    # Sin la clave: se inserta justo después del --- inicial.
    return re.sub(r"^---\n", f"---\n{key}: {value}\n", text, count=1)


def append_registro(path: Path, sha: str, caso: str, detalle: str) -> None:
    hoy = date.today().isoformat()
    registro = (
        f"\n## Registro de simulación\n\n"
        f"- {hoy} `{sha[:8]}` caso {caso}: {detalle}\n"
        f"  Generado por el simulador (sin IA); el agente real reescribirá esta página.\n"
    )
    path.write_text(path.read_text(encoding="utf-8") + registro, encoding="utf-8")


def ensure_under_runtime(repo_root: Path, target: Path) -> None:
    runtime = (repo_root / "runtime").resolve()
    if not target.resolve().is_relative_to(runtime):
        raise SystemExit(f"::error::el simulador solo escribe bajo runtime/: {target}")


def update_page(repo_root: Path, page_rel: str, sha: str, caso: str, motivo: str) -> str:
    path = repo_root / page_rel
    ensure_under_runtime(repo_root, path)
    if not path.exists():
        return f"se omitió el archivo {page_rel} (ya no existe)"
    text = path.read_text(encoding="utf-8")
    text = set_frontmatter_value(text, "commit_verificado", sha)
    text = set_frontmatter_value(text, "generado_por", "simulacion")
    text = set_frontmatter_value(text, "ultima_revision", date.today().isoformat())
    path.write_text(text, encoding="utf-8")
    append_registro(path, sha, caso, motivo)
    return f"se actualizó el archivo {page_rel} ({motivo})"


def mark_stale(repo_root: Path, page_rel: str, sha: str, motivo: str) -> str:
    path = repo_root / page_rel
    ensure_under_runtime(repo_root, path)
    if not path.exists():
        return f"se omitió el archivo {page_rel} (ya no existe)"
    text = path.read_text(encoding="utf-8")
    text = set_frontmatter_value(text, "estado", "desactualizado")
    text = set_frontmatter_value(text, "generado_por", "simulacion")
    path.write_text(text, encoding="utf-8")
    append_registro(path, sha, "C", motivo)
    return f"se marcó como desactualizado el archivo {page_rel} ({motivo})"


def create_stub(repo_root: Path, source_repo: str, ruta: str, sha: str) -> str:
    name = source_repo.split("/")[-1]
    slug = slugify(ruta)
    path = repo_root / "runtime" / name / f"{slug}.md"
    ensure_under_runtime(repo_root, path)
    if path.exists():
        return f"se omitió el archivo {path.relative_to(repo_root).as_posix()} (ya existía)"
    path.parent.mkdir(parents=True, exist_ok=True)
    hoy = date.today().isoformat()
    path.write_text(
        "---\n"
        f"titulo: {slug}\n"
        f"fuente_repo: {source_repo}\n"
        "rutas:\n"
        f"  - {ruta}\n"
        f"commit_verificado: {sha}\n"
        f"permalink_base: https://github.com/{source_repo}/blob/{sha}\n"
        f"ultima_revision: {hoy}\n"
        "estado: borrador\n"
        "generado_por: simulacion\n"
        "---\n\n"
        f"# {slug}\n\n"
        f"Página stub creada por el simulador (sin IA) porque `{ruta}` no tenía\n"
        "página que la cubriera. El agente real escribirá el contenido cuando\n"
        "se agregue la API key.\n",
        encoding="utf-8",
    )
    return f"se creó el archivo {path.relative_to(repo_root).as_posix()} (ruta nueva: {ruta})"


def simulate(manifest: dict, repo_root: Path) -> list[str]:
    caso = manifest.get("case", "A")
    sha = manifest.get("sha", "") or "0" * 40
    source_repo = manifest.get("source_repo", "")
    if not source_repo:
        return ["sin source_repo: nada que simular"]

    if caso == "A":
        return [f"caso A: documentación al día ({manifest.get('reason', '')})"]

    actions: list[str] = []
    candidates = list(manifest.get("candidates") or [])
    uncovered = list(manifest.get("uncovered") or [])

    if caso in ("B", "C", "D"):
        for page in candidates[:MAX_PAGES]:
            if caso == "C":
                motivo = f"cambio grande reportado: {manifest.get('reason', '')[:80]}"
                actions.append(mark_stale(repo_root, page, sha, motivo))
            else:
                acciones = ", ".join(
                    f.get("path", "") for f in (manifest.get("documentable") or [])[:5]
                )
                motivo = f"cambios en {acciones or 'rutas cubiertas'}"
                actions.append(update_page(repo_root, page, sha, caso, motivo))
        if len(candidates) > MAX_PAGES:
            actions.append(f"... y {len(candidates) - MAX_PAGES} páginas candidatas omitidas (tope {MAX_PAGES})")

    for u in uncovered[:MAX_PAGES]:
        actions.append(create_stub(repo_root, source_repo, u.get("path", ""), sha))
    if len(uncovered) > MAX_PAGES:
        actions.append(f"... y {len(uncovered) - MAX_PAGES} rutas nuevas omitidas (tope {MAX_PAGES})")

    return actions or ["caso sin acciones simulables"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out-dir", default="_run")
    args = ap.parse_args()

    root = Path(args.repo_root)
    out_dir = root / args.out_dir
    manifest_path = out_dir / "manifest.json"
    if not manifest_path.exists():
        print("::error::falta _run/manifest.json (corre build_manifest.py antes)")
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actions = simulate(manifest, root)

    (out_dir / "actions.txt").write_text("\n".join(actions) + "\n", encoding="utf-8")
    for line in actions:
        print(f"::notice::{line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
