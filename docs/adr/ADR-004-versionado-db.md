# ADR-004: Versionado de Esquema de Base de Datos

- **Estado**: Aprobado
- **Fecha**: 2026-11-28

## Contexto

Desde la v1.0.0 hay instalaciones con datos reales en `~/.statspro/`. La aplicación debe poder
agregar cambios de esquema sin borrar ni alterar esos datos. Hoy los repositorios trabajan
directamente con `sqlite3.Connection` y SQL; el proyecto no usa ORM ni modelos de SQLAlchemy.

La aplicación de escritorio ejecuta su punto de entrada en Python y se distribuye con `flet build`.
Las migraciones deben poder ejecutarse desde el arranque de la app, sin depender de que el usuario
tenga una CLI instalada ni de iniciar un proceso externo.

## Alternativas Consideradas

- **yoyo-migrations:** biblioteca Python con API programática y CLI. Permite mantener migraciones
  SQL y ejecutarlas desde el código de la aplicación. Añade una dependencia, pero evita implementar
  y mantener un runner propio.
- **Alembic:** runner maduro del ecosistema Python, pero su integración principal depende de
  SQLAlchemy. Sin modelos ORM no se aprovecharía la autogeneración y se sumaría una dependencia
  que el proyecto no necesita.
- **Runner manual propio:** no agrega dependencias, pero obliga a implementar y mantener detección
  de pendientes, orden, bloqueo, registro de versiones y aplicación segura de migraciones.

## Decisión Tomada

Se elige **yoyo-migrations** y se invoca mediante su API Python desde la infraestructura de
persistencia. La CLI queda disponible para desarrollo y mantenimiento; la aplicación de escritorio
no la invoca como subproceso. La dependencia y los archivos SQL deben estar disponibles en el
artefacto generado por `flet build`, lo cual se verifica en la US-204.

La primera migración es una copia exacta del `schema.sql` de v1.0.0. En una base nueva se ejecuta;
en una base existente de v1.0.0 se reconoce el esquema y se marca la migración base como aplicada
sin ejecutarla. Las migraciones posteriores se aplican al arrancar antes de construir repositorios
y vistas que dependan del nuevo esquema.

Las migraciones son inmutables una vez incorporadas a `main`. Se permiten cambios aditivos y
backfills explícitos de metadatos técnicos cuando una historia aprobada los requiera; no se
actualizan ni eliminan datos de negocio. Un fallo detiene el arranque, se registra y se informa:
la app no debe continuar con una base parcialmente migrada. El backup anterior a migraciones queda
en US-208 / ADR-008.

## Ventajas y Desventajas

### Ventajas

- El runner y el registro de migraciones son responsabilidad de una biblioteca probada, no código
  propio.
- Las migraciones siguen siendo archivos revisables y versionados, alineados con el uso actual de
  SQL crudo.
- La API Python permite migrar durante el arranque de la app empaquetada sin requerir Node,
  SQLAlchemy ni una CLI externa.
- El baseline protege las bases existentes de v1.0.0 y permite crear bases nuevas desde cero.

### Desventajas

- Se agrega una dependencia que debe incluirse y probarse en el empaquetado de Flet.
- La detección del baseline y los backfills requieren pruebas específicas; no se debe asumir que
  cualquier base con tablas es una instalación válida de v1.0.0.
- SQLite limita los rollbacks de cambios estructurales. Las migraciones `down` solo se usan cuando
  son seguras; ante cambios complejos se restaura un backup completo (ADR-008).
