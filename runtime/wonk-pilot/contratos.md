---
titulo: Contratos de wonk-pilot
fuente_repo: GetWonk/wonk-pilot
rutas:
  - src/pilot/calculo.py
commit_verificado: 0000000
permalink_base: https://github.com/GetWonk/wonk-pilot/blob/0000000
ultima_revision: 2026-10-18
estado: borrador
generado_por: manual
revisado_por: diego
---

# Contratos de wonk-pilot

La superficie pública con la que se puede escribir contra el piloto.

| Función | Firma | Comportamiento |
| --- | --- | --- |
| `total_con_iva` | `(monto: float, iva: float = 0.19) -> float` | devuelve `monto * (1 + iva)` redondeado a 2 decimales; lanza `ValueError` si `monto < 0` o si `iva` no está en `[0, 1]` |
| `desglose` | `(monto: float, iva: float = 0.19) -> dict` | devuelve `base`, `impuesto` y `total` |
| `IVA_DEFECTO` | `0.19` | IVA usado por defecto |

Las firmas están en `src/pilot/calculo.py#L1-L30`. Si cambia una firma, esta
página entra en el caso B del clasificador y debe actualizarse con el nuevo
`commit_verificado`.
