# DATA — Trozos y búsqueda

Estado: Aprobada
Fecha: 2026-10-23

## Documento

El corpus de esta versión son manuales sintéticos en inglés, de operación financiera: cierre, matriz de aprobación, límites. No son documentos de un empleador. El README, los mensajes de la API, los tests y los commits van en inglés. Estos documentos van en español. [ADR-0008](../adr/0008-public-corpus-is-english.md).

Cada archivo es Markdown y abre con tres campos: `id` (slug en minúsculas), `title` y `audience` (`operator`, `auditor` o `both`). La audiencia es del archivo entero. Un campo desconocido, repetido o vacío no se lee.

Una sección empieza en un `##` en la columna cero. Un `###` cuelga del `##` anterior y su ruta es `Encabezado / Subencabezado`. Otro nivel de encabezado es un error. Antes del primer `##` no hay texto. La primera línea no vacía de la sección es `page: N`, con N entero a partir de 1: es la página que el autor escribió, no un cálculo de PDF. Una sección sin página, sin texto, o con una ruta repetida en el mismo archivo, no se trocea. El encabezado se guarda con los espacios extremos recortados y los internos colapsados. La ruta conserva ese texto, mayúsculas incluidas. No se convierte en slug.

## Trozo

Un trozo es una sección. Si el texto pasa `max_chars`, se parte en ventanas fijas de caracteres: el corte cae en `max_chars` y la siguiente ventana empieza `overlap_chars` antes. `overlap_chars` es mayor o igual que 0 y menor que `max_chars`. Cuando una ventana ya incluye el último carácter, no se emite otra. Todas las ventanas de una sección guardan la misma ruta y la misma página. El ordinal, desde 0, distingue la ventana.

El valor inicial de esta versión es 1500 y 200. No es un óptimo medido. Existe para que una sección corta de un manual quepa en un trozo, y el test inyecta una ventana chica para comprobar el corte. Un borde de palabra sería otra decisión, el día que el recall muestre que partir una palabra duele.

La evaluación marca como relevante la sección (el `id` del documento más la ruta), no cada ventana. Si no, el solapamiento infla el recall.

El id canónico es `{id}#{ruta}#{ordinal}`. Ni el id del documento ni la ruta contienen `#`. Reingerir el mismo archivo actualiza el texto y no cambia el id de esa ruta y ese ordinal. Renombrar el encabezado cambia el id. Corregir una palabra no lo cambia. Dos secciones distintas empiezan cada una en el ordinal 0. [ADR-0006](../adr/0006-stable-chunk-identity.md).

Cada fila guarda el modelo de embedding con nombre y versión. Una ingesta que mezcle dos modelos falla. Cambiar de modelo es borrar y reingerir, no un `UPDATE` a medias. [ADR-0005](../adr/0005-embedding-identity-on-each-chunk.md).

## Búsqueda

Dos consultas, las dos con `WHERE` de audiencia del rol, y luego fusión por reciprocal rank fusion. La configuración de `tsvector` de esta versión es `english`. [ADR-0008](../adr/0008-public-corpus-is-english.md). No se suman el score de `tsvector` y la distancia del vector: no viven en la misma escala. [ADR-0002](../adr/0002-role-filter-before-the-model.md). [ADR-0003](../adr/0003-reciprocal-rank-fusion.md).

La búsqueda vectorial de esta versión es exacta, `ORDER BY` distancia coseno (`<=>`), sin umbral de similitud. El corpus de demostración no justifica un índice aproximado: la migración no crea HNSW ni IVFFlat. Un índice aproximado entra cuando una medición de latencia lo pida, con un ADR nuevo. [ADR-0004](../adr/0004-exact-vector-search-until-measured.md).

El doble de pruebas no llama a un proveedor. Devuelve vectores fijos. La prueba de integración de búsqueda usa PostgreSQL real. Un mock de SQL no sirve para afirmar que el filtro de rol está en la consulta.

## Tope

La pregunta tiene un máximo de caracteres. Cada trozo que viaja al modelo tiene un máximo. El número de pasajes enviados al modelo es el top de la fusión, pequeño y fijo. Esos topes están en configuración, con test de que un exceso se rechaza o se corta en el borde definido, no en silencio a mitad de una cita.

La cita que publica esta versión es la ventana entera. El servidor no la recorta ni la sustituye por una frase del borrador.
