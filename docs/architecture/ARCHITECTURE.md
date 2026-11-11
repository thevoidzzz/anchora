# ARCHITECTURE — Anchora

Estado: Aprobada
Fecha: 2026-10-23

Este documento manda sobre el código de esta versión. Las decisiones caras de revertir están en [los ADR](../adr/README.md).

- [CONTEXT.md](CONTEXT.md) — quién usa el sistema y qué queda fuera
- [DATA.md](DATA.md) — trozos, identidad, búsqueda
- [EVALUATION.md](EVALUATION.md) — qué número cuenta y qué número no
- [SECURITY.md](SECURITY.md) — qué está cerrado y qué hueco se admite

## Forma

Un proceso. Una base PostgreSQL. Sin microservicios: no hay un límite de dominio que justifique otro despliegue, y un fallo de red entre “retrieval” y “generación” no aporta nada con este tamaño.

```mermaid
sequenceDiagram
  participant Cliente
  participant API
  participant Base
  participant Modelo

  Cliente->>API: pregunta, rol
  API->>Base: léxico y vector, ya filtrados por rol
  Base-->>API: pasajes permitidos
  alt no hay pasajes
    API-->>Cliente: rechazo, sin llamar al modelo
  else hay pasajes
    API->>Modelo: pregunta y pasajes marcados como datos
    Modelo-->>API: ids de trozo y borrador
    API->>API: arma la cita desde el trozo, descarta ids ajenos
    alt no queda ninguna cita válida
      API-->>Cliente: rechazo
    else
      API-->>Cliente: respuesta y citas
    end
  end
```

El modelo no escribe la cita. Elige identificadores. El servidor copia el extracto desde el trozo que ya recuperó. Si el identificador no estaba en ese conjunto, se tira. Si no queda ninguno, hay rechazo y el borrador no se entrega. Así una cita no puede apuntar a texto que el modelo haya inventado. El costo es que una paráfrasis correcta, sin usar el id, cuenta como rechazo. Es el trade-off de [ADR-0001](../adr/0001-excerpt-comes-from-the-chunk.md).

El orden de las citas es el de los ids del modelo. Un id repetido se publica una vez, en su primera aparición. El extracto es el texto completo de la ventana recuperada. Un id repetido dentro de lo recuperado es un error de la búsqueda, no una cita doble. El rechazo porque la búsqueda no devolvió filas es otro (`no_evidence`) y ocurre antes de llamar al modelo.

La evaluación reordena esos cinco por los tokens que comparten con la pregunta e imprime hit@5 y recall@5 de la fusión y del rerank. El modelo sigue viendo el orden de la fusión. [ADR-0009](../adr/0009-rerank-is-a-second-pass.md).

## Módulos

| Módulo | Puede importar | No puede |
| --- | --- | --- |
| `domain` | nada de infraestructura | Postgres, HTTP, SDK del modelo |
| `application` | `domain` y puertos | drivers concretos |
| `infrastructure` | puertos | handlers HTTP |
| `api` | casos de uso | SQL |

Un test de arquitectura, cuando exista el paquete, falla si `domain` importa `infrastructure` o `api`. Hasta ese commit, la regla está escrita aquí para no abrir el código en la dirección contraria.

## Contrato HTTP

`POST /v1/answers`

Entrada: `question` (texto no vacío, tope de longitud) y `role` (`operator` o `auditor`).

Salida 200:

- `refused: false`, `answer`, `citations[]` con `chunk_id`, documento, sección, página y `excerpt` copiado del trozo
- o `refused: true`, `reason` (`no_evidence` o `no_valid_citation`), `citations: []`

No es un error que el manual no contenga la respuesta. El error es de transporte, de entrada o del proveedor.

El proceso escucha en el 8000. Compose publica ese puerto en el host, o el valor de `PUBLISH_PORT` cuando el 8000 del host ya está ocupado. La base no se publica.

Errores en `application/problem+json`:

| Caso | Estado |
| --- | --- |
| Pregunta vacía, rol desconocido, cuerpo ilegible | 400 |
| El modelo no responde a tiempo | 504 |
| El modelo responde algo que no cumple el esquema, después de un reintento | 502 |
| La base no está | 503 |

Cada respuesta lleva `request_id`. El log de una respuesta contestada o rechazada incluye rol, latencias de búsqueda y de generación, nombre del modelo, tokens de entrada y de salida, ids usados y si hubo rechazo. No incluye la clave. La pregunta sí se registra en esta versión porque el corpus es sintético y sin ella no se depura el retrieval. El día que el corpus tenga datos de personas, ese campo se apaga. Está en [SECURITY.md](SECURITY.md).

## Qué no se esconde

Esta versión mide si un código del borrador está en el extracto citado. No mide una paráfrasis ni un acuerdo con personas. [ADR-0011](../adr/0011-support-checks-the-draft-code.md). Un modelo puede citar un trozo cercano y decir otra cosa sin números: ese hueco sigue abierto.

Tampoco hay umbral de similitud. Se midió la distancia coseno del vecino más cercano con el embedder fijo: las preguntas con evidencia y las nueve omisiones aparecen en 0 y en 1. Ningún corte separa los dos grupos. [ADR-0010](../adr/0010-no-similarity-floor.md). Las escalas léxica y vectorial no se suman. Si la fusión devuelve pasajes, el modelo los ve. El rechazo por “no hay nada” ocurre cuando la búsqueda no devuelve filas para ese rol, o cuando el modelo no elige un id permitido. El 2026-11-11 esa misma corrida imprimió `retrieval_ms_p95` 11.930 y hit@5 0.951. El scan sigue exacto. [ADR-0013](../adr/0013-measured-latency-keeps-exact-search.md).

## Idioma

Los manuales del conjunto publicado, el README, la API, los tests y los commits de esta versión están en inglés. Esta arquitectura y los ADR están en español. Ese conjunto usa el diccionario `english`. Un manual puede declarar `spanish`; esa corrida no entra en el conjunto. [ADR-0008](../adr/0008-public-corpus-is-english.md). [ADR-0012](../adr/0012-spanish-manual-is-a-separate-run.md).

## Prueba

El codespace usa la imagen Linux por defecto y 2 núcleos. No hay prebuild. El README levanta el mismo Compose: el sustituto, sin clave, y la base sin puerto publicado. Un comando carga los manuales del conjunto y sustituye el catálogo de esa base. Sin ese comando el catálogo sigue vacío. Borrar el codespace apaga la prueba.

## Versión siguiente, todavía no

Juez contrastado con personas. Trazas, y un MCP cuando otro proceso llame a esta API. Interfaz web. AWS cuando el servicio ya corra en Docker, con el mismo contenedor y sin NAT gateway.
