# ADR 0001: Documentación dinámica con ancla de frescura

Fecha: 2026-10-14
Estado: propuesta, sometida al equipo

## Contexto

La documentación de Wonk es buena pero dispersa y sin garantía de frescura:
ningún repo guarda cuándo se verificó una página contra el código, las
decisiones quedan en chats y el mantenimiento depende de la disciplina manual.
`wonk-2` lo admite en su propio `STATUS.md`.

## Decisión

Añadir una capa encima de lo existente, sin reescribir nada:

1. `wonk-docs` como hogar transversal, separando `wiki/` (curado a mano) de
   `runtime/` (generado por la máquina).
2. Cinco páginas base por repo con frontmatter que declara `rutas` y
   `commit_verificado`.
3. Disparador por `repository_dispatch` desde cada repo de código hacia un
   único workflow que piensa.
4. Agente que decide entre cuatro casos (A sin cambios, B incremental,
   C refactor, D contenido nuevo) a partir de un manifiesto, no del repo entero.
5. Siempre PR con `needs-review`; jamás escritura directa en `main`.
6. Barrido semanal sin IA que recoge lo que el disparador deje pasar.

## Consecuencias

- El desfase se vuelve visible: `commit_verificado` contra HEAD.
- El costo de IA se controla filtrando antes de llamar al modelo (caso A no
  gasta tokens).
- Se agregan tres secretos: PAT de aviso, PAT de lectura y la clave del agente.
- Riesgo: el agente puede mentir. Mitigación: revisión humana obligatoria,
  permalinks con SHA y exclusiones de artefactos y datasets.
- GBrain queda para después: indexa documentación, no código, así que primero
  hay que producir documentación fresca.

## Alternativas descartadas

- Reescribir READMEs a mano: no escala y vuelve a envejecer.
- Generar sin PR: rompe la regla acordada de nada directo en `main`.
- Usar `pull_request_target`: descartado por seguridad.
