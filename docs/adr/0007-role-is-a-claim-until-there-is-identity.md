# ADR-0007: El rol de esta versión es una declaración, no una identidad

Estado: Accepted
Fecha: 2026-10-23

## Context

El filtro de [ADR-0002](0002-role-filter-before-the-model.md) necesita un rol ya decidido. Construir sesiones, contraseñas o un proveedor de identidad ahora mezcla dos problemas y retrasa el retrieval. Presentar el header como si fuera acceso de producción sería falso.

## Decision

El cliente envía `role` con un valor cerrado, `operator` o `auditor`. Anchora confía en ese valor. No hay usuario, sesión ni firma. La documentación y el README lo dicen en una frase, no en un apartado escondido.

## Alternatives

**JWT de demostración con un secreto en el repositorio.** Descartado: parece autenticación y no lo es. El secreto terminaría copiado.

**No filtrar por rol en esta versión.** Descartado: el hueco de “el modelo vio el otro manual” es el que este proyecto quiere tener cerrado. El hueco de “quién dice el rol” se admite aparte.

## Trade-offs

Se gana un filtro comprobable con un test de integración, sin fingir login. Se paga que cualquiera que alcance la API elige el rol. No es un sistema para datos reales de una empresa.

## Consequences

Un ADR posterior tiene que sacar el rol de una identidad antes de conectar manuales que no sean sintéticos, y antes de AWS con datos que importen. El test de aislamiento sigue siendo obligatorio: dado un rol, el otro manual no llega al modelo.
