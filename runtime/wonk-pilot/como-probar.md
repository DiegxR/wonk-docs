---
titulo: Cómo probar wonk-pilot
fuente_repo: GetWonk/wonk-pilot
rutas:
  - tests/test_calculo.py
commit_verificado: 0000000
permalink_base: https://github.com/GetWonk/wonk-pilot/blob/0000000
ultima_revision: 2026-10-18
estado: borrador
generado_por: manual
revisado_por: diego
---

# Cómo probar wonk-pilot

```bash
python -m pytest
# sin pytest instalado:
python -m unittest discover -s tests
```

`tests/test_calculo.py` cubre cálculo con IVA, validación de monto negativo,
desglose y el saludo de `app.py`.

Cambio de comportamiento previsto: mientras un PR solo toque `tests/`, el
disparador lo clasifica como caso A y no abre nada en `wonk-docs`.
