# Wonk Docs

Hogar transversal de la documentación de Wonk. Este repositorio no reescribe los
README ni los CLAUDE.md que ya existen: los usa como fuente, los cita y mantiene
encima la capa que no estaba en ningún lado, cómo encajan los repos entre sí.

Tres reglas gobiernan todo lo de aquí:

1. El código manda. Ninguna página contradice el código.
2. Un dato tiene un solo hogar. Si un README ya lo dice, se enlaza.
3. Nada escribe directo en `main`. Toda actualización entra como PR con
   `needs-review`.

## Mapa

| Carpeta | Quién la toca | Qué contiene |
| --- | --- | --- |
| `wiki/` | personas | páginas curadas: visión transversal, hubs de repo, runbooks |
| `runtime/` | Actions (agente) | fragmentos por repo con frontmatter y permalinks |
| `adr/` | personas | decisiones que deben sobrevivir a quien las tomó |
| `raw/` | personas | contexto que no sale del código: notas, antecedentes |
| `.github/` | Actions | workflows, scripts del manifiesto y prompt del agente |

## Tubería

```
push a main en un repo de código
  -> notify-wonk-docs.yml (ese repo) avisa por repository_dispatch
     -> sync-from-repo.yml (aquí) arma el manifiesto y clasifica A-D
        -> agente (claude-code-action) o dry-run sin API key
           -> PR con needs-review -> revisión humana -> merge -> Pages
drift-check.yml: barrido semanal sin IA, recoge lo que ningún aviso cubrió
```

El detalle de cada paso está en la hoja de ruta
`Wonk daily/documentación/Hoja-de-ruta-Documentacion-Dinamica.pdf` y en
`wiki/runbooks/runbook-sincronizacion.md`.

## Estado

Fase 0 y 1 de la hoja de ruta: repos creados, páginas base sembradas y
disparador listo para probar. Falta la API key del agente para salir del
dry-run.
