---
titulo: Arquitectura de wonk-pilot
fuente_repo: DiegxR/wonk-pilot
rutas:
  - src/pilot/app.py
  - src/pilot/__init__.py
commit_verificado: 0000000
permalink_base: https://github.com/DiegxR/wonk-pilot/blob/0000000
ultima_revision: 2026-10-18
estado: borrador
generado_por: manual
revisado_por: diego
---

# Arquitectura de wonk-pilot

Dos módulos, sin capas intermedias.

`src/pilot/app.py` es la entrada: `saludar`, `atender_solicitud` y `health`
componen el comportamiento visible del piloto.

`src/pilot/calculo.py` concentra la lógica de negocio y sus reglas de validación;
`app.py` solo lo invoca. Esa separación es lo que hace que cambiar
`src/pilot/app.py` sea un caso B incremental y no un refactor.

Verificado contra el código: `src/pilot/app.py#L1-L30`.
