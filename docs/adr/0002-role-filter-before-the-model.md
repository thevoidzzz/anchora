# ADR-0002: El rol filtra en SQL, antes del modelo

Estado: Accepted
Fecha: 2026-10-23

## Context

El manual de auditoría y el de operación no son el mismo texto. Si la búsqueda trae todo y el filtro ocurre después, en el prompt o en la respuesta, el modelo ya vio el otro manual. Un filtro tarde no se puede deshacer.

## Decision

Las consultas léxica y vectorial incluyen la audiencia del rol en el `WHERE`. El modelo solo recibe pasajes que ya pasaron ese filtro. Si no hay filas, no hay llamada al modelo y la respuesta es `no_evidence`.

## Alternatives

**Recuperar en ancho y borrar trozos en aplicación.** Descartado: el otro rol ya estuvo en memoria del proceso de generación, y un olvido en el armado del prompt lo filtra mal.

**Un índice por rol.** Descartado con este tamaño: duplica la ingesta y se desalinea cuando un documento tiene dos audiencias.

## Trade-offs

Se gana que el texto prohibido no entra al proveedor. Se paga un predicado en ambas consultas, y un test de integración por rol. Un documento con dos audiencias sigue siendo una fila visible para ambos, no dos copias.

## Consequences

El test de “la misma pregunta con el otro rol” mira la llamada al modelo, no solo el JSON final: el doble del modelo no debe haber recibido el trozo ajeno. Una instrucción dentro de un trozo permitido es otro fallo, y este filtro no lo cubre.
