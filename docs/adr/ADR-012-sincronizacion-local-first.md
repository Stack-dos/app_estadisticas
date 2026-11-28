# ADR-012: Preparación Local-First para Sincronización

- **Estado**: Aprobado para la preparación local de Hito 2; proveedor y protocolo remoto pendientes del spike
- **Fecha**: 2026-11-28

## Contexto

La aplicación es hoy local-first: cada instalación trabaja con su propia base SQLite y debe operar
sin internet. El roadmap propone sincronización multi-dispositivo en el Hito 5 y
`docs/spike/spike_supabase.md` investiga Supabase, pero el spike sigue sin ejecutar y sus escenarios
no tienen resultados.

Preparar esa evolución en Hito 2 reduce el costo de asignar identidades globales después de que
crezcan las bases instaladas. La preparación debe respetar las PK/FK actuales y no convertir una
función futura en requisito de conexión para usar la aplicación.

## Alternativas Consideradas

1. **Reemplazar ahora las PK enteras por UUID.** Facilitaría la identidad remota, pero exigiría
   reconstruir tablas, transformar todas las FK y aumentar el riesgo de migración de datos reales.
2. **Agregar una identidad `sync_id` UUID aparte de las PK locales (elegida).** Mantiene intactas
   las relaciones y consultas existentes, a la vez que ofrece un identificador estable entre
   instalaciones.
3. **Posponer toda preparación hasta el Hito 5.** Reduce trabajo inmediato, pero deja para entonces
   el backfill de identificadores y cambios a operaciones de alta, edición y baja.
4. **Conectar los repositorios directamente con Supabase.** Simplifica el acceso remoto, pero hace
   depender la operación de internet y contradice ADR-001 y NFR-6.

## Decisión Tomada

### Preparación en Hito 2

- SQLite sigue siendo la base operativa y la fuente de verdad local. La UI y los casos de uso
  continúan leyendo y escribiendo localmente; «caché» no significa que se pueda descartar la base,
  especialmente mientras existan cambios pendientes de sincronización.
- Las entidades del primer agregado sincronizable conservan sus PK/FK actuales y reciben una
  columna `sync_id` UUID estable y única y un `updated_at` UTC. Una migración asigna estos
  metadatos a las filas existentes sin modificar sus datos de negocio; la aplicación los mantiene
  para las escrituras nuevas.
- Se agrega un `sync_outbox` transaccional para registrar altas, cambios y bajas de las entidades
  sincronizables, más almacenamiento local de cursor/estado. La escritura del registro y del evento
  de outbox ocurre en la misma transacción SQLite. No se usa un `is_dirty` genérico como reemplazo
  del outbox.
- Las bajas sincronizables se representan con tombstones (`deleted_at`) y se conservan hasta que el
  futuro protocolo pueda propagarlas. Las consultas ordinarias siguen ocultando esos registros.
- Hito 2 no incorpora conexión de red, credenciales, SDK de Supabase ni hilo de sincronización.
  La tabla y las entidades exactas del agregado inicial se confirman antes de implementar US-231.

### Sincronización en Hito 5

- La app mantiene el acceso local; un servicio de sincronización en segundo plano será un adaptador
  de infraestructura detrás de un puerto de aplicación. No bloquea la UI ni comparte una conexión
  `sqlite3.Connection` entre hilos; el worker abre y administra su propia conexión.
- Push y pull deben ser idempotentes, reintentables y paginables. El estado/cursor se persiste
  localmente y el push confirma los eventos solo después de que el servidor los acepte.
- Supabase queda como candidato, no como decisión de proveedor ya validada. Se confirma después de
  completar los escenarios E1–E7 del spike, medir almacenamiento y cerrar autenticación, RLS,
  privacidad y conflictos. No se distribuye una contraseña de PostgreSQL, clave de servicio ni
  secreto privilegiado dentro de la app de escritorio; el diseño de producción requiere
  autenticación y políticas de acceso remotas o una API intermedia.
- No se adopta todavía last-write-wins basado solo en el reloj local: la propia spike identifica
  relojes desincronizados como riesgo. El cursor remoto y la política de conflicto se deciden con
  los resultados del spike; un timestamp no debe ser el único mecanismo para detectar cambios.
- La sincronización de datos personales de menores requiere revisar consentimiento y obligaciones
  de protección de datos antes de habilitar el envío de datos reales.

## Ventajas y Desventajas

### Ventajas

- Conserva las PK locales y evita una reconstrucción general de tablas para migrar identificadores.
- La app puede seguir creando, consultando y modificando datos sin internet.
- El outbox registra los cambios de forma atómica; los tombstones permiten propagar bajas offline.
- La arquitectura deja intercambiar Supabase por otro backend sin acoplar los repositorios ni el
  dominio al proveedor.

### Desventajas

- Añade columnas y tablas locales, lógica de outbox y pruebas de migración antes de que exista un
  servidor sincronizador.
- La consistencia entre dispositivos, la resolución de conflictos, autenticación, RLS y privacidad
  siguen siendo trabajo significativo del Hito 5.
- El backfill de identidades y timestamps debe probarse con bases reales de v1.0.0 y no puede
  alterar datos de negocio; una identidad UUID no resuelve por sí sola la propiedad o el acceso a
  los datos remotos.
