# Contrato del agente — wonk-docs

Este archivo es la regla dura de decisión. El agente lo recibe junto con el
manifiesto (`_run/manifest.md`) y debe aplicarlo literalmente.

## Qué recibes

El manifiesto trae: repo fuente, SHA nuevo, SHA anterior, archivos cambiados
(added/modified/removed/renamed), el diff, la documentación existente del repo
(README y CLAUDE.md) y las páginas candidatas que salen de cruzar los archivos
cambiados con el `rutas` del frontmatter. No explorues el repo a ciegas: trabaja
sobre ese paquete. Si necesitas verificar una ruta concreta, léela con Read.

## Casos

- **A. No hay nada que agregar.** Solo pruebas, formato, comentarios,
  dependencias sin cambio de contrato o archivos excluidos. No toques nada.
- **B. Cambio incremental.** Una ruta cambiada aparece en el `rutas` de una
  página existente y no se movieron módulos. Actualiza esa página: ajusta
  contenido y rutas, y sube `commit_verificado` al SHA nuevo.
- **C. Refactor grande.** Muchos archivos movidos o renombrados, cambios de
  arquitectura, o rutas del frontmatter que dejan de existir. No parchees:
  reescribe la página afectada, marca las obsoletas como
  `estado: desactualizado` y explica el movimiento en el cuerpo del PR... aquí
  explica en el manifiesto final. Si te falta contexto, escribe menos antes que
  inventar.
- **D. Contenido nuevo.** Aparece un módulo, endpoint o repo sin página que lo
  cubra. Crea la página base que falte con frontmatter completo.

La clasificación del manifiesto (`Clasificación propuesta`) es una
recomendación determinista: puedes corregirla si el código te da otra señal, y
debes decirlo en tu resumen.

## Reglas de seguridad

1. Solo escribe dentro de `runtime/`. Jamás toques `wiki/`, `adr/`, `raw/`,
   `CLAUDE.md`, `mkdocs.yml` ni `.github/`.
2. Nunca hagas commit ni abras PR: eso lo hace el workflow. Tampoco hagas push.
3. Máximo 5 páginas por corrida. Si el cambio es más grande, documenta lo
   esencial y deja el resto para la siguiente corrida.
4. Si la confianza es baja, no adivines: escribe solo lo verificable y
   decláralo en tu resumen final.
5. Nunca copies bloques largos de código: enlaza `ruta#Lx-Ly` con el permalink
   `https://github.com/<repo>/blob/<sha>/<ruta>#Lx-Ly`. El `<sha>` es siempre el
   SHA del manifiesto, nunca `main`.

## Frontmatter obligatorio

```yaml
---
titulo: <título corto>
fuente_repo: <owner/repo fuente>
rutas:
  - <ruta/relativa/al/archivo>#Lx-Ly
commit_verificado: <SHA nuevo del manifiesto>
permalink_base: https://github.com/<repo>/blob/<SHA>
ultima_revision: <YYYY-MM-DD>
estado: verificado
generado_por: claude-code-action
---
```

`commit_verificado` es el ancla de frescura: sin ella la página no sirve.

## Formato

Español. Frases directas, sin relleno. Sin em-dashes (—). Identificadores,
rutas y nombres de API en su idioma original. Un dato tiene un solo hogar: si el
README o el CLAUDE.md del repo ya lo dicen, enlázalos; no los dupliques.

## Exclusiones (nunca documentar)

Artefactos (`*.log`, `*.xml` de resultados, `.coverage`, `dist/`,
`node_modules/`), datasets (`insumos/`, `ttls/`, `*.ttl`), secretos
(`*.tfvars`, `*.tfstate`, `bootstrap/*-creds.yaml`, `externalsecret*.yaml`),
`.venv/` y `uv.lock`.
