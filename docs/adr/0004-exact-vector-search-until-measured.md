# ADR-0004: Búsqueda vectorial exacta hasta que una medición pida otra cosa

Estado: Accepted
Fecha: 2026-10-23

## Context

Un índice HNSW aproximado acelera corpora grandes y puede dejar fuera el vecino correcto. El corpus de Anchora en esta versión es un puñado de manuales. No hay una latencia medida que obligue a aproximar.

## Decision

La búsqueda vectorial ordena por distancia exacta. No se crea un índice aproximado en la migración de esta versión.

## Alternatives

**HNSW desde el primer commit.** Descartado: añade un parámetro (`ef_search`) y un hueco de recall que el conjunto de evaluación atribuiría al embedding o al troceo.

## Trade-offs

Se gana un vecino correcto y un fallo de recall que significa “el embedding o el trozo”, no “el índice”. Se paga un scan que, con miles de trozos, dejará de servir.

## Consequences

Otro ADR tiene que existir antes de crear un índice aproximado, y tiene que citar la latencia medida y el hit@5 antes y después. Mientras tanto, la migración no incluye HNSW.
