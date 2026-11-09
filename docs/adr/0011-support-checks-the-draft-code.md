# ADR-0011: El apoyo mira el código del borrador, no un juez de pago

Estado: Accepted
Fecha: 2026-11-09

## Context

Recall y validez de cita ya se imprimen. Eso no dice si el borrador añadió un dato que el pasaje no tiene. Un juez de pago, o un acuerdo con personas, queda fuera de esta versión: el chequeo no puede depender de una clave ni de una lectura que el comando no imprime.

## Decision

Una respuesta entregada está apoyada cuando cada token del borrador que contiene un dígito aparece en algún extracto citado. Un rechazo no entra en la tasa. El informe imprime `supported_answers` aparte de hit@5, recall@5 y la validez de cita. El sustituto escribe `See the cited passages.`, que no trae un código, así que no añade un dato.

## Alternatives

**Exigir que cada palabra del borrador esté en el extracto.** Descartado: el puntero del sustituto usa palabras que el manual no tiene, y la tasa mediría la frase fija en vez del dato.

**Un modelo que puntúe fidelidad.** Descartado: cobra, o baja un peso que el chequeo no fija, y esta versión no afirma un contraste con personas.

## Trade-offs

Se gana un chequeo reproducible de códigos inventados. Se paga que una paráfrasis sin dígitos sigue contando como apoyada.

## Consequences

El README copia `supported_answers` solo si el comando lo imprimió, y dice que no es un acuerdo con personas. Un contraste humano, si se hace, no entra al README desde aquí.
