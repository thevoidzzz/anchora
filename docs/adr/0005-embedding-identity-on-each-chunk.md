# ADR-0005: Cada trozo recuerda qué embedding lo creó

Estado: Accepted
Fecha: 2026-10-23

## Context

Un vector no significa nada sin el modelo que lo produjo. Consultar con otro modelo, u otra versión, compara espacios distintos. El síntoma es un recall que se cae sin un cambio de texto visible.

## Decision

Cada trozo guarda nombre y versión del embedding. La ingesta rechaza un lote si no coincide con el modelo ya almacenado. Cambiar de modelo es vaciar los vectores y reingerir. La consulta usa el mismo par nombre-versión.

## Alternatives

**Asumir un solo modelo y no guardarlo.** Descartado: el día del cambio no queda rastro de con qué se construyó el índice.

**Traducir vectores de un modelo a otro.** Descartado: no hay una función así que esta versión sepa justificar.

## Trade-offs

Se gana un fallo ruidoso en el cambio de modelo, en vez de un recall silencioso. Se paga una reingesta completa cuando el modelo cambia, y una columna que la evaluación debe imprimir junto al número.

## Consequences

El informe de evaluación nombra el modelo. Un README que publique hit@5 sin ese nombre no cumple el contrato de este ADR.
