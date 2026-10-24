# ADR-0008: El corpus público está en inglés

Estado: Accepted
Fecha: 2026-10-23

## Context

El lector de manuales acepta texto en español: el id del archivo es un slug ASCII y la ruta conserva tildes. El perfil y el README públicos ya están en inglés. El primer número de Anchora tiene que atribuirse a la búsqueda. Un corpus en dos idiomas mezclaría ese número con el diccionario de PostgreSQL y con el modelo de embeddings.

## Decision

Lo que un extraño lee está en inglés: los manuales de esta versión, el README, los mensajes de la API, los tests y los commits. Lo que fija el diseño está en español: la arquitectura y estos ADR.

La configuración de `tsvector` de esta versión es `english`. El conjunto de evaluación no mezcla idiomas.

## Alternatives

**Corpus en español.** Descartado para esta versión: el perfil público ya está en inglés, y el primer hit@5 mediría a la vez el retrieval y el diccionario.

**Corpus bilingüe desde el primer conjunto.** Descartado: dos configuraciones de texto y un conjunto partido. El número deja de tener una causa.

## Trade-offs

Se gana una línea de base explicable. Se paga que el operador de un manual real en español no es el usuario de esta versión.

## Consequences

La búsqueda léxica de esta versión usa `english`. Un manual en español entra en este mismo repositorio después de la primera corrida guardada: el mismo troceo, diccionario `spanish`, y hit@5 y recall@5 de antes y de después. Hasta esa corrida, el corpus publicado es inglés. El lector no se cierra a Unicode para cumplir esta decisión.
