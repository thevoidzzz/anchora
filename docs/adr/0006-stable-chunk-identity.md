# ADR-0006: El id del trozo sale del documento, la sección y el ordinal

Estado: Accepted
Fecha: 2026-10-23

## Context

El conjunto de evaluación tiene que señalar secciones concretas. Un UUID nuevo en cada ingesta rompe esas referencias aunque el texto no haya cambiado. Hace falta un id que sobreviva a reingerir.

## Decision

La identidad de un trozo es el documento, la ruta de sección y el ordinal dentro de esa sección. Reingerir actualiza texto y vector en esa misma fila. Borrar una sección del archivo deja de ofrecer ese id. No se recicla el ordinal de una sección distinta.

## Alternatives

**UUID por ingesta.** Descartado: el conjunto de evaluación se vuelve mentira después de cada carga.

**Hash del texto.** Descartado como id primario: una corrección de una palabra cambia el id y parece un trozo nuevo. El hash del texto se guarda aparte, para saber si el vector está viejo.

## Trade-offs

Se gana un conjunto de evaluación estable. Se paga disciplina en las rutas de sección: renombrar un encabezado es un cambio de id y obliga a tocar el conjunto.

## Consequences

La evaluación falla en CI si un id relevante no existe en el corpus. Así un rename no pasa en silencio. El hash de contenido no es la clave.
