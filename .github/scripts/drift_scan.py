#!/usr/bin/env python3
"""Barrido semanal de desfase (sin IA).

Compara `commit_verificado` de cada página con el HEAD de su repo fuente y, si
hubo cambios en las rutas del frontmatter desde ese commit, marca la página
como desactualizada.

Salidas:
  - <out-dir>/drift.md        informe markdown
  - <out-dir>/drift.json      {"stale": [...], "ok": [...], "unknown": [...]}
  - GITHUB_OUTPUT: stale=<n>, title=<titulo si hay desfase>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_manifest import gh_token, load_pages, ruta_base  # noqa: E402


def api_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "wonk-docs-drift",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def head_sha(repo: str, token: str) -> tuple[str, str]:
    data = api_get(f"https://api.github.com/repos/{repo}", token)
    branch = data.get("default_branch", "main")
    commit = api_get(f"https://api.github.com/repos/{repo}/commits/{branch}", token)
    return commit["sha"], branch


def changed_files(repo: str, base: str, head: str, token: str) -> set[str] | None:
    try:
        data = api_get(f"https://api.github.com/repos/{repo}/compare/{base}...{head}", token)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
    return {f.get("filename", "") for f in data.get("files", [])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out-dir", default="_run")
    args = ap.parse_args()

    root = Path(args.repo_root)
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    token = gh_token()

    pages = load_pages(root, source_repo="")
    heads: dict[str, tuple[str, str]] = {}
    stale, ok, unknown = [], [], []

    for page in pages:
        repo = page["fuente_repo"]
        anchor = page["commit_verificado"]
        if not repo or not anchor:
            unknown.append({**page, "detalle": "sin fuente_repo o sin commit_verificado"})
            continue
        try:
            if repo not in heads:
                heads[repo] = head_sha(repo, token)
            sha, branch = heads[repo]
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            unknown.append({**page, "detalle": f"no se pudo leer {repo}: {exc}"})
            continue

        if sha == anchor:
            ok.append(page)
            continue

        changed = changed_files(repo, anchor, sha, token)
        if changed is None:
            unknown.append({**page, "detalle": f"compare falló ({anchor} -> {sha})"})
            continue
        rutas = {ruta_base(r) for r in page["rutas"]}
        hit = sorted(r for r in rutas if r in changed)
        if hit:
            stale.append({**page, "detalle": f"HEAD {branch} = {sha[:7]}; cambiaron {', '.join(hit)}"})
        else:
            ok.append(page)

    lines = ["# Barrido de desfase", ""]
    lines.append(f"Páginas: {len(pages)} | al día: {len(ok)} | desactualizadas: {len(stale)} "
                 f"| sin resolver: {len(unknown)}")
    if stale:
        lines += ["", "## Desactualizadas", "", "| Página | Repo | commit_verificado | Detalle |",
                  "| --- | --- | --- | --- |"]
        lines += [f"| `{s['page']}` | {s['fuente_repo']} | `{s['commit_verificado']}` | {s['detalle']} |"
                  for s in stale]
    if unknown:
        lines += ["", "## Sin verificar", ""]
        lines += [f"- `{u['page']}`: {u['detalle']}" for u in unknown]

    (out_dir / "drift.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "drift.json").write_text(
        json.dumps({"stale": stale, "ok": ok, "unknown": unknown}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    out_path = os.environ.get("GITHUB_OUTPUT")
    if out_path:
        with open(out_path, "a", encoding="utf-8") as fh:
            fh.write(f"stale={len(stale)}\n")
            fh.write(f"unknown={len(unknown)}\n")
            fh.write("title=documentación desactualizada\n" if stale else "title=\n")

    print(f"stale={len(stale)} ok={len(ok)} unknown={len(unknown)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
