---
titulo: Visión general de wonk-pilot
fuente_repo: GetWonk/wonk-pilot
rutas:
  - README.md
  - pyproject.toml
commit_verificado: 0000000
permalink_base: https://github.com/GetWonk/wonk-pilot/blob/0000000
ultima_revision: 2026-10-18
estado: borrador
generado_por: manual
revisado_por: diego
---

# Visión general de wonk-pilot

Repositorio piloto de la tubería de documentación dinámica. No es producto:
existe para que un push a `main` dispare el aviso hacia `wonk-docs` y para
probar la clasificación de cambios (A-D) antes de conectar los repos reales.

- Python 3.11+ sin dependencias en tiempo de ejecución.
- Un solo workflow propio: `notify-wonk-docs.yml`.
- Código fuente en `src/pilot/`, pruebas en `tests/`.

El detalle de por qué existe está en
[wonk-pilot (hub)](../../wiki/repos/wonk-pilot.md).

`commit_verificado: 0000000` es un marcador de fase 0: se reemplaza por el SHA
real cuando se suba el primer commit a `main`.
