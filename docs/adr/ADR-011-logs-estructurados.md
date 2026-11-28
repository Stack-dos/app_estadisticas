# ADR-011: Logs estructurados con correlation_id

- **Estado**: Aprobado (ya implementado en la US-110)
- **Fecha**: 2026-11-27

## Contexto

Hasta la US-110 los logs eran texto (`fecha - modulo - nivel - mensaje`) en `~/.statspro/logs/app.log`.
Cuando un entrenador reporta "me salió un error al guardar el partido", en el archivo hay líneas de la
pantalla, del caso de uso y del repositorio mezcladas con las de otros clics, y no hay forma de saber
cuáles son de ese clic. La US-110 pide:

- JSON con niveles (AC1), para filtrar con herramientas y no a ojo.
- Un `correlation_id` (UUIDv4) por acción del usuario, que llegue hasta los repositorios (AC2).
- Secretos tapados en todos los niveles (AC3).
- Elegir el destino por configuración, sin tocar código de negocio (AC4).

Y hay una restricción de arquitectura: la capa de aplicación no importa infraestructura.

## Alternativas Consideradas

1. **Pasar el `correlation_id` por parámetro** (un `ExecutionContext` en cada caso de uso y repositorio).
   Explícito, pero cambia la firma de casi todo el sistema y ensucia el dominio con un dato técnico.
2. **`structlog` o `python-json-logger`.** Resuelven el JSON y el contexto, pero suman una dependencia
   para unas 30 líneas, y `structlog` trae su propia API de logging que la capa de aplicación tendría que
   importar.
3. **Biblioteca estándar: `ContextVar` + filtros y formatter en el handler (elegida).** El id viaja en una
   `ContextVar` (una variable "global" pero propia de cada hilo/tarea); un `logging.Filter` en el
   handler lo copia a cada registro; un `logging.Formatter` propio arma el JSON. Los casos de uso siguen
   usando `logging.getLogger(__name__)` y no se enteran.
4. **Un servicio de logs (Seq, SigNoz) con `docker compose` para desarrollo.** Lindo para buscar, pero
   es una app de escritorio offline: en producción no existe, y en desarrollo `STATSPRO_LOG_SINK=consola`
   con `jq` alcanza. Descartado por ahora.

## Decisión

Alternativa 3, en `src/infraestructura/observabilidad.py`:

- `nueva_accion(nombre)`: context manager que abre la acción con un UUIDv4 y la cierra al salir (también
  con excepción). Anidada, reutiliza la de afuera.
- `FiltroContexto`, `FiltroSecretos` y `FormateadorJson`, enganchados al **handler** en `logger.py`
  (los filtros de un logger no se aplican a lo que propagan sus hijos; los del handler, sí).
- Las acciones nacen en tres lugares de la GUI: `ejecutar_mostrando_errores(..., nombre="pantalla.accion")`
  (cada clic), `al_cambiar_ruta` ("navegar") y `ejecutar()` ("arranque": esquema y sesión recordada).
- Sink y nivel por `STATSPRO_LOG_SINK` (`archivo`|`consola`) y `STATSPRO_LOG_NIVEL`; valores desconocidos
  usan el default.

## Consecuencias

- **+** Cero dependencias nuevas; la capa de aplicación no cambia de API.
- **+** Una línea JSON por evento: `jq 'select(.correlation_id=="...")'` muestra un clic completo.
- **−** La `ContextVar` no cruza a hilos creados a mano dentro de una acción (`threading.Thread` arranca
  con contexto vacío). Hoy no hay ninguno; si aparece, hay que usar `contextvars.copy_context().run`.
- **−** `ft.run` tiene que quedar **fuera** de cualquier acción: las tareas de asyncio copian el contexto
  de quien las crea, y todos los clics heredarían el mismo id.
- **−** La redacción es por nombre de clave y por patrón (`password=...`, emails): un secreto logueado sin
  clave reconocible (por ejemplo, `logger.info(password)`) no se tapa. La regla sigue siendo no loguear
  secretos; el filtro es la red de seguridad.
