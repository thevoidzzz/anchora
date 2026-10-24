# ADR-0001: La cita la copia el servidor desde el trozo

Estado: Accepted
Fecha: 2026-10-23

## Context

Si el modelo redacta la cita, puede nombrar una página y un entrecomillado que no están en el manual. Comprobar luego si esa frase es subcadena del trozo falla con espacios, cortes y paráfrasis, y deja pasar una cita casi cierta. Había que decidir quién es la fuente del extracto antes de escribir el contrato.

## Decision

El modelo devuelve identificadores de trozo y un borrador de respuesta. El servidor construye cada cita copiando el extracto del trozo recuperado para ese rol. Un id que no esté en ese conjunto se descarta. Si no queda ningún id permitido, la respuesta es un rechazo `no_valid_citation` y el borrador no se entrega.

## Alternatives

**Dejar que el modelo escriba la cita y buscarla como subcadena.** Descartado: un espacio o una paráfrasis convierten una cita buena en falsa, y una cita casi copiada cuela.

**No citar y devolver solo el texto.** Descartado: sin pasaje comprobable, Anchora es un chat.

## Trade-offs

Se gana una validez de cita determinista, con barra del 100% sobre las citas emitidas. Se paga que una respuesta bien razonada, si no señala un id, se rechaza. El usuario ve menos respuestas y ninguna cita inventada.

## Consequences

El esquema de salida del modelo no tiene un campo de cita libre. El test del contrato incluye un id ajeno y exige rechazo o cita solo del conjunto permitido. El servidor no publica una cita que no haya copiado.
