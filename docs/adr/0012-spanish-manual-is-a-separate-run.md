# ADR-0012: El manual en español se mide aparte

Estado: Accepted
Fecha: 2026-11-11

## Context

La primera corrida guardada ya existe. [ADR-0008](0008-public-corpus-is-english.md) dejó el corpus publicado en inglés y el `tsvector` en `english`, y reservó un manual en español para después: el mismo troceo, diccionario `spanish`, y hit@5 y recall@5 de antes y de después. Meter ese manual en el conjunto de las 50 preguntas mezclaría el diccionario con la línea de base.

## Decision

Cada trozo guarda `lexicon`, `english` o `spanish`. Si el manual no lo declara, queda `english`. El `tsvector` se escribe al guardar con `to_tsvector` de ese diccionario. Una columna generada no sirve: PostgreSQL no trata esa llamada como inmutable cuando la configuración sale de la misma fila. La consulta léxica usa el diccionario de la fila.

El manual en español no vive en `eval/corpus`. `python -m anchora.eval` sigue cargando solo el conjunto inglés. `python -m anchora.eval.spanish` imprime hit@5 y recall@5 del mismo texto con `english` y luego con `spanish`. El troceo no cambia: los ids son los mismos.

## Alternatives

**Cambiar el diccionario de todo el catálogo a `spanish`.** Descartado: la línea de base inglesa dejaría de medirse con el diccionario con el que se publicó.

**Añadir el manual al conjunto de 50.** Descartado: un conjunto en dos idiomas ya no tiene una sola causa para el hit@5.

## Trade-offs

Se gana una comparación del diccionario sobre el mismo texto. Se paga un campo más en cada fila y una corrida que no sustituye a la de las 50 preguntas.

## Consequences

El README puede copiar las cuatro tasas solo si ese comando las imprimió. La corrida inglesa sigue siendo la línea de base. Un índice aproximado sigue esperando su propia medición.
