# ADR-0009: El rerank reordena los cinco y no sustituye la fusión

Estado: Accepted
Fecha: 2026-11-09

## Context

La fusión por reciprocal rank fusion ya tiene una corrida guardada. Un rerank que ocupara su lugar dejaría un número suelto: no se sabría si el cambio viene del orden nuevo o de haber tirado la línea de base. Un modelo de rerank hospedado, o uno descargado, metería una clave o un peso que el chequeo no puede fijar.

## Decision

Sobre los cinco pasajes que ya devolvió la fusión, una segunda pasada cuenta los tokens compartidos entre la pregunta y el texto del pasaje. Un token es una secuencia de letras o dígitos, en minúsculas. El empate conserva el orden de la fusión. El modelo sigue recibiendo ese orden de fusión. El informe imprime hit@5 y recall@5 de las dos órdenes, en el mismo conjunto.

## Alternatives

**Un cross-encoder local o un rerank hospedado.** Descartado: el primero baja un peso que el chequeo no fija, y el segundo cobra y pide una clave.

**Sustituir la lista que ve el modelo.** Descartado: la corrida de fusión dejaría de ser la que produce las citas, y el antes y el después se mezclarían.

## Trade-offs

Se gana una comparación reproducible, sin red. Se paga que el solapamiento de tokens favorece al pasaje que repite las palabras de la pregunta. Una paráfrasis puede quedar detrás de un eco léxico. Por eso las citas siguen saliendo del orden de la fusión.

## Consequences

El README copia las dos tasas solo si el comando las imprimió. Cambiar la regla del token es otra corrida del mismo conjunto. Que el modelo vea el orden reordenado exige otro ADR.
