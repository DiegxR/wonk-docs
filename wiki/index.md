# Wonk Docs

Documentación transversal de Wonk, mantenida viva por una tubería que avisa,
clasifica y propone. Aquí empiezan las tres cosas que faltaban: un hogar
transversal, un ancla de frescura (`commit_verificado`) y un mecanismo que no
dependa de que alguien se acuerde.

## Cómo navegar

- [Visión transversal](arquitectura/overview.md): cómo encajan los repos.
- [Repositorios](repos/wonk-pilot.md): hub por repo y sus páginas base.
- [Runbooks](runbooks/runbook-sincronizacion.md): procedimientos, incluida la
  prueba del disparador.
- `runtime/`: lo generado por la máquina, con frontmatter y permalinks.
- `adr/`: decisiones.

## Reglas

La regla de generación vive en [CLAUDE.md](https://github.com/DiegxR/wonk-docs/blob/main/CLAUDE.md).
Resumen: el código manda, un dato tiene un solo hogar, nada escribe directo en
`main`, y toda cita usa `blob/<sha>` nunca `blob/main`.
