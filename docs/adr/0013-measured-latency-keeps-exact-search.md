# ADR-0013: La latencia medida no pide un índice aproximado

Estado: Accepted
Fecha: 2026-11-11

## Context

[ADR-0004](0004-exact-vector-search-until-measured.md) deja la búsqueda vectorial en un scan exacto hasta que una medición pida otra cosa. Un índice aproximado, antes de existir, necesita un ADR que cite la latencia medida y el hit@5. El 2026-11-11 `python -m anchora.eval` imprimió `retrieval_ms_p95: 11.930` y `hit_at_5: 0.951` sobre las 50 preguntas, con el embedder fijo. El corpus sigue siendo un puñado de manuales.

## Decision

No se crea HNSW ni IVFFlat. La búsqueda vectorial sigue en `ORDER BY` distancia coseno. 11.930 milisegundos en el percentil 95 no es una latencia que obligue a aproximar, y el hit@5 de esa corrida es el de la búsqueda exacta.

## Alternatives

**Crear HNSW para que el repositorio muestre el índice.** Descartado: no hay una latencia que lo pida, y un índice aproximado puede dejar fuera el vecino correcto. El hit@5 dejaría de atribuirse al embedding y al troceo.

## Trade-offs

Se gana que el fallo de recall, si aparece, siga significando el embedding o el trozo. Se paga un scan que, con miles de trozos, dejará de servir.

## Consequences

La migración no incluye un índice aproximado. Un ADR posterior que lo cree tiene que citar la latencia y el hit@5 de antes y de después. Esta corrida es el antes. No hay un después, porque el índice no se creó. [ADR-0004](0004-exact-vector-search-until-measured.md) sigue vigente.
