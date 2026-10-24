# Architecture Decision Records

Un ADR se escribe cuando la decisión es cara de revertir. No se escribe para elegir un nombre de variable.

Son inmutables. Si una decisión cambia, un ADR nuevo la reemplaza. No se reescribe el viejo.

## Estados

`Accepted` — vigente.
`Superseded by ADR-XXXX` — reemplazado.

## Índice

| ADR | Título | Estado |
| --- | --- | --- |
| [0001](0001-excerpt-comes-from-the-chunk.md) | La cita la copia el servidor desde el trozo | Accepted |
| [0002](0002-role-filter-before-the-model.md) | El rol filtra en SQL, antes del modelo | Accepted |
| [0003](0003-reciprocal-rank-fusion.md) | La fusión es RRF, no una suma de scores | Accepted |
| [0004](0004-exact-vector-search-until-measured.md) | Búsqueda vectorial exacta hasta que una medición pida otra cosa | Accepted |
| [0005](0005-embedding-identity-on-each-chunk.md) | Cada trozo recuerda qué embedding lo creó | Accepted |
| [0006](0006-stable-chunk-identity.md) | El id del trozo sale del documento, la sección y el ordinal | Accepted |
| [0007](0007-role-is-a-claim-until-there-is-identity.md) | El rol de esta versión es una declaración, no una identidad | Accepted |
| [0008](0008-public-corpus-is-english.md) | El corpus público está en inglés | Accepted |
