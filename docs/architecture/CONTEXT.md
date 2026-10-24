# CONTEXT — Anchora

Estado: Aprobada
Fecha: 2026-10-23

Anchora responde preguntas sobre manuales de operación. El usuario trae una pregunta y un rol. El sistema devuelve una respuesta con citas tomadas del texto recuperado, o un rechazo si ese rol no tiene un pasaje que sirva.

## Actores

| Actor | Qué hace |
| --- | --- |
| Operador | Pregunta por procedimientos que su rol puede ver |
| Auditor | Pregunta solo por el subconjunto marcado para auditoría |
| Autor del corpus | Publica manuales sintéticos en el repositorio. No hay un editor dentro del servicio |
| Evaluación | Corre el conjunto fijo y lee los números. No es un usuario de la API |

## Dentro de esta versión

Manuales sintéticos en inglés, troceo por sección, búsqueda léxica y vectorial, filtro por rol antes del modelo, respuesta con cita textual o rechazo, comando de evaluación, Docker y CI. El diseño se escribe en español. [ADR-0008](../adr/0008-public-corpus-is-english.md).

## Fuera

Identidad real, interfaz web, documentos escaneados, gráficos, AWS y un juez de faithfulness. El detalle está en [ARCHITECTURE.md](ARCHITECTURE.md).

## Sistemas externos

Un proveedor de embeddings y un modelo de generación, detrás de puertos. Las pruebas no los llaman: usan dobles deterministas. La clave, si hace falta en local, viene del entorno.

No hay cola, caché, bus de eventos ni segundo servicio. El corpus cabe en una base.
