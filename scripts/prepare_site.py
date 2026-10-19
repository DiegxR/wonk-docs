#!/usr/bin/env python3
"""Prepara el árbol de MkDocs en docs/ (staging, no versionado).

MkDocs exige que docs_dir sea un hijo del config. En vez de mover el contenido
(wiki/, runtime/, adr/, raw/ viven en la raíz por el contrato de CLAUDE.md),
se copia tal cual a docs/ para que los enlaces relativos se comporten igual.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

FOLDERS = ("wiki", "runtime", "adr", "raw")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    docs = root / "docs"
    if docs.exists():
        shutil.rmtree(docs)
    docs.mkdir(parents=True)
    copied = 0
    for name in FOLDERS:
        src = root / name
        if not src.exists():
            print(f"aviso: falta {name}/")
            continue
        shutil.copytree(src, docs / name,
                        ignore=shutil.ignore_patterns("_dryrun", "__pycache__"))
        copied += sum(1 for _ in (docs / name).rglob("*") if _.is_file())
    print(f"staging listo: docs/ con {copied} archivos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
