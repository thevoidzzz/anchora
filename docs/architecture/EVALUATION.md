# EVALUATION — Qué se mide

Estado: Aprobada
Fecha: 2026-10-23

Un número entra al README solo si el comando de evaluación lo imprimió sobre el conjunto fijo.

## Conjunto

Archivo versionado, escrito a mano, del orden de 50 preguntas. Cada ítem tiene id, rol, pregunta, ids de sección relevante, y si se espera rechazo.

El conjunto no se usa como ejemplos dentro del prompt. Si se filtra al modelo, el número deja de medir generalización.

Incluye, a propósito:

- una pregunta cuya respuesta está en una sola sección
- una cuya respuesta queda partida por el solapamiento
- una paráfrasis, no una copia del encabezado
- un término exacto que la búsqueda léxica debe salvar (código, umbral, nombre propio)
- una pregunta ausente del corpus
- la misma pregunta con el rol que no ve ese manual

## Métricas de esta versión

| Métrica | Definición | Barra |
| --- | --- | --- |
| Hit@5 | fracción de preguntas con evidencia en las que al menos una sección relevante está entre los cinco primeros | se publica el valor; no hay una barra inventada antes de la primera corrida |
| Recall@5 | secciones relevantes recuperadas en el top 5, sobre las relevantes | igual |
| Validez de cita | entre las citas devueltas, cuántas son extracto del trozo recuperado | 100%. Es un chequeo del servidor, no una opinión |
| Acierto de rechazo | rechazos correctos y rechazos indebidos, por separado | se publican los dos. Un sistema que rechaza todo no pasa |

Hit@5 y recall@5 se calculan sobre las preguntas que tienen evidencia para ese rol. El rechazo va en su propia tabla. Mezclarlos en un solo accuracy esconde si el fallo es de búsqueda o de cautela.

## Qué no se imprime todavía

Un contraste con personas. `supported_answers` mira si un token con dígito del borrador está en el extracto citado. No afirma que una paráfrasis se desprenda del pasaje, ni un acuerdo con lectores. [ADR-0011](../adr/0011-support-checks-the-draft-code.md).

Latencia p95 y el total de tokens salen del log de la corrida de evaluación, no de una sola llamada manual. Esta versión no imprime un importe.

## Antes y después

La corrida de la fusión sigue impresa como hit@5 y recall@5. El mismo comando imprime `rerank_hit_at_5` y `rerank_recall_at_5` sobre esos cinco, reordenados por tokens compartidos con la pregunta. El modelo no cambia de lista. Sin las dos líneas, no hay comparación. [ADR-0009](../adr/0009-rerank-is-a-second-pass.md).

`python -m anchora.eval.spanish` no carga las cincuenta. Carga un manual, `lote`, lo guarda una vez con `english` y otra con `spanish`, y imprime hit@5 y recall@5 de cada diccionario. El troceo es el mismo. Cinco manuales de relleno quedan más cerca en el espacio del embedder fijo, así que un fallo léxico sale de los cinco fusionados. Esos números no sustituyen la línea de base inglesa. [ADR-0012](../adr/0012-spanish-manual-is-a-separate-run.md).

## Comando

El informe separa hit@5 y recall@5 de los rechazos. Hit@5 y recall@5 usan solo las preguntas con evidencia: el recall es micro, las secciones distintas presentes en los cinco primeros trozos sobre las secciones relevantes. Un trozo de más no cuenta. Los rechazos correctos, los indebidos (se rechazó una pregunta con evidencia) y los omitidos (se contestó una pregunta que debía rechazarse) van en líneas distintas. La validez de cita es la fracción de extractos idénticos al trozo guardado; si hay citas y no es 1, el comando termina con error. El informe nombra el modelo de embedding y el modelo de lenguaje. Imprime latencia p95 y tokens. No imprime un importe: esta versión no tiene una tarifa.

CI de esta versión corre los tests con dobles. La corrida con modelo de pago no es obligatoria en CI: si lo fuera, el build dependería de una clave y de una factura. El informe con modelo real se genera a mano y se pega en el README con la fecha.
