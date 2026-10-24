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

Faithfulness. Exige un juez y un contraste con personas. Hasta entonces, Anchora no afirma que la respuesta se desprenda del pasaje. Afirma que el pasaje está y que la cita es real.

Latencia p95 y coste por respuesta salen del log de la corrida de evaluación, no de una sola llamada manual.

## Antes y después

La primera corrida guardada es léxico más vector sin rerank. El rerank, si entra, se compara contra esa corrida en el mismo conjunto. Sin la corrida previa, no hay mejora: hay un número suelto.

## Comando

Un comando local lee el conjunto, corre retrieval (y, en las preguntas de respuesta, el contrato completo con el doble o con el modelo configurado) y escribe el informe. CI de esta versión corre los tests con dobles. La corrida con modelo de pago no es obligatoria en CI: si lo fuera, el build dependería de una clave y de una factura. El informe con modelo real se genera a mano y se pega en el README con la fecha.
