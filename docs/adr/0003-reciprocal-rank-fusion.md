# ADR-0003: La fusión es RRF, no una suma de scores

Estado: Accepted
Fecha: 2026-10-23

## Context

La búsqueda léxica devuelve un rank de `tsvector`. La vectorial devuelve una distancia. Sumarlas, o hacer una media, compara unidades distintas. Un peso “0.5 y 0.5” sería un número sin medición.

## Decision

Cada lista aporta `1 / (k + rank)` por trozo, con `k` fijo y documentado en configuración. El top que ve el modelo es el de esa suma de recíprocos. No hay peso entre léxico y vector en esta versión.

## Alternatives

**Suma ponderada de scores normalizados.** Descartado: la normalización depende de la consulta y el peso seguiría siendo un gusto hasta tener el conjunto de evaluación.

**Solo vectores.** Descartado: códigos, umbrales y nombres propios del manual son el caso en el que el léxico gana, y el conjunto de evaluación incluye uno.

**Solo léxico.** Descartado: la paráfrasis es el otro caso del conjunto.

## Trade-offs

Se gana una fusión que no finge una calibración. Se paga que un trozo mediocre en las dos listas puede ganar a uno excelente en una sola. El rerank, si entra, se mide contra esta fusión, no la reemplaza en silencio.

## Consequences

El informe de evaluación guarda la corrida de RRF como línea de base. Cambiar `k` es un cambio de comportamiento y va con una corrida nueva del mismo conjunto, no con un ajuste suelto.
