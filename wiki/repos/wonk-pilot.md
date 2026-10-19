# wonk-pilot

| Campo | Valor |
| --- | --- |
| Repositorio | `GetWonk/wonk-pilot` |
| Rama principal | `main` |
| Dueño | Diego Rojas |
| Papel | piloto mínimo para probar el disparador de documentación dinámica |
| Lenguaje | Python 3.11+ (sin dependencias) |
| Disparador | `.github/workflows/notify-wonk-docs.yml` |

## Páginas

| Página | Cubre |
| --- | --- |
| [Visión general](../../runtime/wonk-pilot/vision-general.md) | `README.md`, `pyproject.toml` |
| [Arquitectura](../../runtime/wonk-pilot/arquitectura.md) | `src/pilot/app.py` |
| [Cómo correr](../../runtime/wonk-pilot/como-correr.md) | `README.md`, `pyproject.toml` |
| [Cómo probar](../../runtime/wonk-pilot/como-probar.md) | `tests/test_calculo.py` |
| [Contratos](../../runtime/wonk-pilot/contratos.md) | `src/pilot/calculo.py` |

## Nota

Este repo no es producto. Existe para ejercitar el aviso hacia `wonk-docs` y la
clasificación A-D antes de conectar los repos reales (fase 3 de la hoja de
ruta). Cuando el piloto cumpla su función, se retira junto con su entrada aquí.
