# ADR-004: Versionado de Esquema de Base de Datos

- **Estado**: Pendiente — ver pregunta abierta antes de cerrarlo
- **Fecha**: 2026-10-03

## Contexto

La US-204 (Hito 2) pide que el esquema de la base evolucione entre versiones sin perder datos: un
mecanismo que aplique cambios de esquema en orden, sepa qué versión está instalada
(`schema_version`) y, en lo posible, permita volver atrás. Hoy el esquema completo vive en un
único archivo (`src/infraestructura/persistencia/sql/schema.sql`), sin ningún versionado — cada
arranque de la CLI simplemente ejecuta ese archivo contra la base.

**Dato técnico relevante para esta decisión:** el proyecto no usa ningún ORM. Los 5 repositorios
(`src/infraestructura/repositorios/`) trabajan directo contra `sqlite3.Connection` con SQL crudo
— no hay modelos de SQLAlchemy en ningún lado del código. Esto importa porque **Alembic está
construido sobre SQLAlchemy** y su funcionalidad más fuerte (`alembic revision --autogenerate`,
que compara modelos ORM contra la base y genera el script de migración solo) requiere justamente
esos modelos que este proyecto no tiene. Usar Alembic acá significaría agregar SQLAlchemy como
dependencia nueva, y usarlo solo en su modo "offline" de scripts SQL escritos a mano — sin la
feature que más lo diferencia de escribir los scripts a mano directamente.

## Alternativas Consideradas

- **Alembic:** herramienta de migraciones estándar del ecosistema Python/SQLAlchemy. Provee un
  runner maduro (`upgrade`/`downgrade`), un historial de migraciones versionado automáticamente,
  y comandos CLI propios (`alembic upgrade head`). En este proyecto, al no haber modelos
  SQLAlchemy, se usaría en modo scripts SQL manuales — pierde la ventaja de autogeneración, pero
  conserva el runner y las convenciones de nomenclatura/versionado ya resueltas y probadas por
  una herramienta externa en vez de mantenidas a mano.
- **Migraciones manuales con runner propio:** scripts `NNN_descripcion.sql` versionados a mano
  (ya descritos en el listado de archivos de la US-204: `001_init.sql`, `002_*.sql`,
  `migration_runner.py`), con una tabla `schema_version` que el propio runner actualiza. Cero
  dependencias nuevas, consistente con el resto del proyecto (sin ORM), pero el runner (aplicar en
  orden, detectar pendientes, bloquear si hay incompatibilidad) hay que escribirlo y mantenerlo
  nosotros.

## Decisión Tomada

**Todavía no se toma** — ver la pregunta abierta.

## Pregunta abierta (a resolver entre nosotros antes de cerrar este ADR)

> El punto central a decidir es: **¿vale la pena agregar SQLAlchemy como dependencia nueva solo
> para tener el runner de Alembic, sabiendo que no se va a usar su autogeneración (no hay ORM en
> el resto del proyecto) y que de todos modos los scripts SQL se van a escribir a mano?**
>
> - Si la respuesta es que el runner maduro + el historial versionado de Alembic justifican la
>   dependencia nueva aunque sea en modo manual, se elige Alembic.
> - Si la respuesta es que no vale la pena una dependencia nueva (y el stack de SQLAlchemy que
>   trae) para un runner que de todos modos no vamos a aprovechar al máximo, se elige el runner
>   propio — es más trabajo inicial (hay que escribirlo), pero es más chico y más consistente con
>   "sin ORM en ningún lado" que ya es la convención establecida del proyecto.
>
> **Sobre el alcance del rollback (AC3 de la US-204), ya resuelto independientemente de esta
> pregunta:** SQLite tiene soporte muy limitado para deshacer cambios de esquema (no se puede
> borrar una columna con `ALTER TABLE` en versiones viejas; hay que recrear la tabla entera). El
> rollback real (`down`) solo se escribe a mano cuando el cambio lo permite de forma simple (ej.
> agregar/quitar una fila de seed, agregar una columna con default). Para cambios de estructura
> complejos, la única forma real de "volver atrás" es restaurar un backup completo (ver ADR-008)
> — no un `down` por migración. Esto aplica igual eligiendo Alembic o un runner propio.

## Ventajas y Desventajas

_Pendiente — depende de la decisión final, ver la pregunta abierta arriba._
