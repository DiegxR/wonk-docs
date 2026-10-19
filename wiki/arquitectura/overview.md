# Visión transversal

Wonk es un conjunto de repositorios que hoy cada cual explica por su cuenta.
Esta página es el mapa: qué hace cada uno y dónde queda la documentación que lo
cubre.

## Repositorios

| Repo | Papel | Documentación |
| --- | --- | --- |
| `wonk-pilot` | piloto mínimo de la tubería de documentación | `runtime/wonk-pilot/` |
| `wonk-2` | backend principal (FastAPI) | pendiente de fase 2 |
| `wonk-2-ui` | frontend | pendiente |
| `wonk-dags` | DAGs de orquestación | pendiente |
| `wonk-infra` | infraestructura (Terraform) | pendiente |
| `wonk-gitops` | despliegue GitOps | pendiente |
| `wonk-scripts` | scripts de apoyo | pendiente |
| `wonk-local-deployment` | levantamiento local | pendiente |
| `wonk-docs` | este repo: documentación transversal | `wiki/` + `runtime/` |

## Flujo end-to-end

1. Un PR se fusiona a `main` en un repo de código.
2. Ese repo corre su `notify-wonk-docs.yml`, filtra ruido (pruebas, artefactos,
   datasets) y envía `repository_dispatch` con el SHA nuevo, el anterior, los
   archivos cambiados, el diff y su README/CLAUDE.md.
3. `sync-from-repo.yml` aquí arma el manifiesto, cruza los cambios con el
   `rutas` de cada página y clasifica el cambio en caso A, B, C o D.
4. El agente escribe solo en `runtime/`. Sin API key corre en dry-run y publica
   el manifiesto como PR de prueba.
5. El PR sale con `needs-review`; una persona lo revisa y fusiona.
6. Al fusionar, `pages.yml` republica el sitio.
7. `drift-check.yml` barrera semanalmente lo que ningún aviso alcanzó a cubrir.

## Ancla de frescura

Cada página guarda `commit_verificado`. Ese SHA es al mismo tiempo la base de
los permalinks (`blob/<sha>`) y el punto de comparación del barrido:
`git diff <commit_verificado>..HEAD -- <ruta>` dice si la página envejeció.
