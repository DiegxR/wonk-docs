# CLAUDE.md — wonk-docs

Guía para Claude Code (y cualquier agente) cuando trabaja en este repositorio.
Este repo es la **documentación transversal y el second brain de Wonk**. Las reglas de aquí
gobiernan cómo se **genera, estructura y mantiene** la documentación automática.

## Qué es este repositorio

Capa de documentación nueva, encima de los repos que ya existen. No reescribe nada: resume el
código y **lo cita**. El código es la fuente de verdad; este repo la documenta.

## Principios (reglas duras)

1. **El código manda.** Ninguna página puede contradecir el código. Ante duda, enlaza al archivo;
   no copies bloques largos que se van a desactualizar.
2. **Un dato, un solo hogar.** Si el `README.md` o el `CLAUDE.md` de un repo ya lo dice, se enlaza
   o se cita; no se duplica.
3. **Markdown plano como formato canónico.** Todo `.md` para que lo lea una persona, la wiki
   (MkDocs) y las herramientas de búsqueda.
4. **Frontmatter obligatorio** en toda página (contrato de abajo). Sin él, la página se considera
   incompleta.
5. **Nada escribe directo en `main`.** Toda actualización automática entra como PR con etiqueta
   `needs-review`. Una persona la revisa antes del merge.

## Estructura del repositorio

```
wonk-docs/
├── CLAUDE.md                 # este archivo: reglas de generación
├── mkdocs.yml                # sitio MkDocs Material (vitrina humana)
├── .gbrain-source            # declara este repo como source del brain
├── .github/workflows/
│   ├── sync-from-repo.yml     # recibe el aviso de los repos de código
│   ├── drift-check.yml        # barrido semanal de desfase (sin IA)
│   └── pages.yml              # publica MkDocs en GitHub Pages
├── wiki/                     # CURADO: páginas revisadas por humanos
│   ├── arquitectura/  runbooks/  contratos/  repos/
├── adr/                      # decisiones (NNNN-titulo.md)
├── raw/                      # contexto NO derivado del código (notas, decisiones)
└── runtime/                  # GENERADO: fragmentos por repo (machine-managed)
    ├── wonk-2/  wonk-2-ui/  wonk-scripts/  wonk-dags/ ...
```

**Separa siempre `wiki/` (curado) de `runtime/` (generado).** `wiki/` lo edita una persona;
`runtime/` lo sobrescriben las Actions. Nunca edites `runtime/` a mano: las correcciones van a
`wiki/`, y `wiki/` cita a `runtime/` en vez de copiarlo.

## Contrato de página (frontmatter obligatorio)

```yaml
---
fuente_repo: DiegxR/wonk-2            # repo del que sale esta página
rutas:                               # archivos que esta página documenta
  - src/wonk2/app/routers/auth.py#L42-L88
  - src/wonk2/app/services/auth_base.py#L1-L30
commit_verificado: a1b2c3d           # SHA del commit que se documentó (ancla de frescura)
permalink_base: https://github.com/DiegxR/wonk-2/blob/a1b2c3d
ultima_revision: 2026-10-14
estado: verificado                   # verificado | desactualizado | borrador
generado_por: claude-code-action     # o "manual"
revisado_por: diego
---
```

**Regla de permalinks:** toda cita de código usa `blob/<sha>/...` y **nunca** `blob/main/...`.
El SHA congela la referencia y es el mismo valor que guarda `commit_verificado`.

## Cómo generar una página (procedimiento)

1. **Elige el alcance.** Una página por tema, no un volcado del repo. Las cinco base por repo son:
   visión general, arquitectura, cómo correr, cómo probar y contratos/API.
2. **Lee el código real.** Usa los `.md` existentes (README, CLAUDE.md, PLAN.md, docs/) y el
   código fuente del repo. No inventes: si no está en el código, no lo afirmes.
3. **Fija el SHA.** Obtén el SHA de `main` del repo (`git -C <repo> rev-parse main`). Ese es
   `commit_verificado` y la base de `permalink_base`.
4. **Ubica la página.** Contenido derivado del código va a `wiki/` (o `runtime/` si lo genera una
   Action). Contexto no derivado del código va a `raw/`. Una decisión va a `adr/NNNN-titulo.md`.
5. **Escribe el frontmatter completo** y el cuerpo citando cada archivo con `ruta#Lx-Ly` y el
   permalink correspondiente. Un enlace entre páginas usa `[[source/slug]]`.
6. **No dupliques.** Si el repo ya lo explica, enlaza a `ruta@commit` o al `raw/` correspondiente.
7. **Abre un PR** (nunca push a `main`). El PR lleva `needs-review`. Al fusionar, la wiki se
   republica y el índice se reindexa.

## Formato por tipo de carpeta

- `wiki/arquitectura/` — visión transversal: cómo se relacionan los repos, flujo end-to-end.
- `wiki/repos/<repo>/` — páginas por repositorio (las cinco base).
- `wiki/repos/<repo>.md` — página **hub** del repo: lenguaje, rama principal, dueño, URL y
  enlaces a sus páginas. Es el ancla desde la que cuelga todo lo demás.
- `wiki/contratos/` — interfaces y APIs entre repos.
- `wiki/runbooks/` — procedimientos operativos (desplegar, levantar, recuperar).
- `adr/NNNN-titulo.md` — contexto / decisión / consecuencias.
- `runtime/<repo>/` — fragmentos generados por la Action, con frontmatter y permalinks.
- `raw/` — contexto que no está en el código (notas, decisiones, antecedentes).

## Idioma y tono

- Español. Frases directas, sin relleno.
- Sin em-dashes (—) ni viñetas con guion en prosa: prosa o numeración.
- Los identificadores, rutas y nombres de API se dejan en su idioma original.

## Exclusiones (nunca documentar)

- Artefactos: `pytest-run.log`, `*.xml` de resultados, `.coverage`, `dist/`, `node_modules/`.
- Datasets: `insumos/*.ttl` y datos masivos (2.4 GB), `.venv/`, `ttls/`.
- Secretos: `*.tfvars`, `*.tfstate`, `bootstrap/*-creds.yaml`, `externalsecret*.yaml`.
- `insumos` no entra en la generación automática (es fuente de verdad de la ontología, se edita a
  mano); solo se documenta su propósito en una página fija.

## Detección de desfase (mantenimiento)

- `commit_verificado` es el ancla: `git diff <commit_verificado>..HEAD -- <ruta>` dice si la página
  quedó vieja. El barrido semanal (`drift-check.yml`) corre esto sin IA y abre un issue con la
  lista de páginas desactualizadas.
- Si una página contradice el código, gana el código: actualízala o márcala
  `estado: desactualizado` y explica el cambio en el PR.

## Automatización (resumen de la tubería)

```
PR fusionado a main en un repo de código
  -> workflow del repo: si toca rutas documentables, avisa por repository_dispatch
  -> workflow de wonk-docs: regenera las páginas afectadas y abre un PR auto,needs-review
  -> revisión humana -> merge -> republica la wiki + reindexa el brain
```

Nunca uses `pull_request_target`. El agente solo puede abrir PR, nunca escribir en `main`.
