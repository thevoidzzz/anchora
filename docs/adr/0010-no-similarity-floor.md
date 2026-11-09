# ADR-0010: No hay suelo de similitud

Estado: Accepted
Fecha: 2026-11-09

## Context

Nueve preguntas del conjunto fijo debían rechazarse y el sustituto las contestó. El rol sigue viendo otros pasajes, y el embedder fijo no codifica significado: cada texto es un vector unitario en una de ocho posiciones. Un suelo de distancia coseno solo sería válido si separa esas nueve de las preguntas con evidencia, sin rechazos indebidos.

## Decision

No hay suelo. Con ese embedder, la distancia del vecino más cercano vale 0 o 1 en los dos grupos. Ningún corte convierte las nueve omisiones en rechazos correctos sin rechazar también preguntas con evidencia. El informe sigue publicando `missed_refusals` 9.

## Alternatives

**Cortar cuando la distancia es mayor que 0.** Descartado: varias preguntas con evidencia quedan a distancia 1 de todo pasaje visible, y pasarían a rechazo indebido.

**Inventar un corte intermedio.** Descartado: este embedder no produce distancias entre 0 y 1.

## Trade-offs

Se gana no publicar un umbral que el conjunto desmiente. Se pagan las nueve omisiones, que siguen siendo el hueco de este sustituto.

## Consequences

Un suelo entra solo con otro embedder, o con este, el día que una corrida del mismo conjunto muestre que las distancias se separan. Hasta entonces la respuesta no mira la distancia.
