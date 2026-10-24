# SECURITY — Cerrado y admitido

Estado: Aprobada
Fecha: 2026-10-23

Anchora no es un pentest y no describe cómo romper un modelo. Este documento fija qué garantiza el servicio y qué hueco queda abierto a propósito.

## Cerrado en esta versión

- El texto de otro rol no sale de la base hacia el modelo. El filtro va en la consulta. [ADR-0002](../adr/0002-role-filter-before-the-model.md).
- La cita la copia el servidor desde un trozo de ese conjunto. Un id fuera del conjunto se descarta.
- La clave del modelo no se commitea y no se escribe en el log.
- La pregunta y los pasajes tienen tope. Un cuerpo enorme es 400, no un prompt ilimitado.
- El proveedor tiene tiempo máximo. Si vence, la respuesta es 504, no un cuelgue.

## Hueco admitido: el rol no es una identidad

En esta versión el cliente dice su rol. No hay sesión ni firma. Quien pueda llamar a la API puede decir `auditor` u `operator`. El filtro se prueba asumiendo que el rol ya se decidió. No se presenta como autorización de una empresa.

Cerrarlo de verdad es otro cambio: una identidad, y el rol sale de esa identidad, nunca del cuerpo libre. Un eval posterior puede medir si, aun con el filtro, un documento o una pregunta saca texto de más. No sustituye la identidad. [ADR-0007](../adr/0007-role-is-a-claim-until-there-is-identity.md).

## Hueco admitido: el manual es dato no confiable

El trozo se marca como dato en el prompt. Eso no impide que un párrafo del manual intente dar instrucciones al modelo. Esta versión no afirma que eso esté resuelto. Un eval posterior puede medirlo contra esta misma API, con categorías y tasas. Este repositorio no publica una colección de ataques.

## Hueco admitido: citar no es comprender

Una cita válida puede acompañar una respuesta que no se sigue del pasaje. Está nombrado en [EVALUATION.md](EVALUATION.md). Esta versión no afirma que la respuesta se desprenda del pasaje.

## Hueco admitido: la pregunta queda en el log

Hace falta para depurar retrieval sobre un corpus sintético. Si más adelante el manual tiene datos de personas, se deja de registrar el texto y se registra un identificador. No se espera a ese día para darse cuenta.

