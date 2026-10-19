# Runbook: prueba del disparador de documentación dinámica

Objetivo: validar de punta a punta que un push a `main` en un repo de código
llegue hasta el paso del modelo en `wonk-docs`, sin API key todavía.

## Requisitos previos (fase 0)

1. Crear `wonk-pilot` y `wonk-docs` en GitHub (bajo el dueño que corresponda).
2. Subir cada carpeta local a su repo y dejar `main` como rama por defecto.
3. En `wonk-pilot`: Settings > Secrets and variables > Actions > New
   repository secret:
   - `WONK_DOCS_TOKEN`: PAT clasic con alcance `repo` (permite llamar a la API
     de `wonk-docs`; el `GITHUB_TOKEN` del repo no cruza repositorios).
4. En `wonk-docs`: crear los secretos:
   - `AGENT_READ_TOKEN`: PAT de solo lectura sobre los repos de código (lo usa
     el manifiesto y el barrido para comparar commits). Opcional mientras los
     dos repos sean públicos: si falta, se usa `GITHUB_TOKEN`.
   - `ANTHROPIC_API_KEY`: todavía no existe; su ausencia activa el dry-run.
5. En `wonk-docs`: Settings > Pages > Source = GitHub Actions.

## Caso B (el camino feliz)

1. En `wonk-pilot`, modificar `src/pilot/app.py` y subir a `main`.
2. Verificar en Actions de `wonk-pilot`:
   - `notify-wonk-docs` termina en verde y dice
     "Aviso enviado a wonk-docs (2 rutas documentables)".
3. Verificar en Actions de `wonk-docs`:
   - `sync-from-repo` aparece solo, sin que nadie lo lance.
   - Paso "Construir manifiesto": `caso B: rutas cambiadas cubiertas...`.
   - Paso "Sin API key": avisa dry-run.
   - Paso "Abrir PR": deja un PR `[dry-run]` con etiquetas
     `needs-review` y `dry-run`.
4. Revisar el PR: el manifiesto completo está en
   `runtime/wonk-pilot/_dryrun/manifest.md`.
5. Cerrar el PR sin fusionar (es una prueba).

## Caso A (que no dispare)

1. En `wonk-pilot`, tocar solo `tests/test_calculo.py` y subir.
2. `notify-wonk-docs` debe terminar en verde con el aviso
   "Caso A: el diff solo tocó pruebas/formato/excluidos" y no debe generarse
   ninguna corrida en `wonk-docs`.

## Caso D (ruta sin página)

1. Agregar `wonk-pilot/src/pilot/nuevo_modulo.py` y subir.
2. En `wonk-docs`, el manifiesto debe clasificar `caso D` y listar la ruta en
   "Rutas sin página".

## Disparador manual

Ambos workflows aceptan `workflow_dispatch`:

- En `wonk-pilot`: botón "Run workflow" con `force=true` envía el aviso aunque
  no haya rutas documentables.
- En `wonk-docs`: botón "Run workflow" con `source_repo=DiegxR/wonk-pilot`
  arma el manifiesto sin esperar al otro repo. Útil para depurar el clasificador.

## Cuando llegue la API key

1. Agregar `ANTHROPIC_API_KEY` en `wonk-docs`.
2. Repetir el Caso B: ahora el paso
   "Agente real (claude-code-action)" debe correr y escribir en
   `runtime/wonk-pilot/`, y el PR dejará de llamarse `dry-run`.
3. Revisar el PR con la checklist que trae el cuerpo: `commit_verificado` con el
   SHA correcto, permalinks `blob/<sha>`, nada tocado en `wiki/`.

## Red de seguridad

`drift-check.yml` corre los lunes 06:17 UTC y también a mano. Compara
`commit_verificado` con el HEAD de cada repo fuente y abre (o actualiza) un
issue `docs-drift` con las páginas que quedaron viejas.
