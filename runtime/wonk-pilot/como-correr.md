---
titulo: Cómo correr wonk-pilot
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

# Cómo correr wonk-pilot

No hay servicio que levantar: es una librería. Para usarla hay que tener el
paquete en el path.

```bash
python -c "from pilot.app import saludar; print(saludar('Diego'))"
```

Instalación editable:

```bash
pip install -e ".[dev]"
```

Los detalles de empaquetado están en `pyproject.toml` y no se duplican aquí.
