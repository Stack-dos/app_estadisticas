# Informe de sesión — US-110: logs JSON con correlation_id (2026-11-27)

Rama: `feature/epica2`. Cierra la US-110, lo último que faltaba del Hito 1.

## Por qué

Los logs eran texto suelto: ante un "me falló al guardar", no había forma de separar las líneas de ese
clic de las de otros. La US-110 pide JSON con niveles, un `correlation_id` (UUIDv4) por acción del
usuario que llegue hasta los repositorios, los secretos tapados y el sink elegido por configuración.

## Decisiones (de Nico: "vamos con lo que recomendás")

- **D0 = a:** Claude implementa todo (las dos pistas de la US).
- **D1 = a:** nombre explícito de cada acción, `nombre="pantalla.que_hace"`, obligatorio.
- **D2 = a:** JSON con la biblioteca estándar (`json`), sin `structlog`.
- **D3 = a:** `STATSPRO_LOG_SINK=archivo|consola` (default `archivo`) y `STATSPRO_LOG_NIVEL` (default `INFO`).
- **D4 = a:** los eventos de altas/ediciones/bajas van en los casos de uso, con `logging.getLogger(__name__)`.
- **D5 = a:** el arranque (esquema y sesión recordada) es la acción `arranque`; cada cambio de pantalla, `navegar`.
- **Sin Seq/SigNoz:** se evaluó un `docker compose` para desarrollo y se descartó.
- Queda en el ADR-011.

## Qué cambió

- **Nuevo `src/infraestructura/observabilidad.py`:** `nueva_accion` (context manager sobre una `ContextVar`),
  `FiltroContexto`, `FiltroSecretos` (claves secretas y emails, en mensaje, extras y traceback), `FormateadorJson`.
- **`logger.py`:** `crear_handler(sink, nivel)` arma el handler (archivo rotativo o stderr) con los filtros y el
  formatter; `configuracion_log()` lo elige con las variables de entorno. Se mantiene el corte si ya hay handlers.
- **`errores.py`:** `ejecutar_mostrando_errores(accion, etiqueta, *, nombre)` abre la acción y loguea
  `accion_inicio` y `accion_fin` (`resultado` y `duracion_ms`); `error_dominio` como WARNING y `error_inesperado`
  como ERROR. Las 34 llamadas de las pantallas tienen su nombre (`clubes.crear`, `carga_partido.guardar`...).
- **`app.py`:** `al_cambiar_ruta` envuelve el dibujo en `nueva_accion("navegar")` (la lógica pasó a `_dibujar_ruta`);
  `ejecutar()` envuelve esquema y dependencias en `nueva_accion("arranque")`, con `ft.run` afuera a propósito.
- **Eventos en aplicación:** `login_ok` / `login_fallido` (sin email), `logout`, `set_active_club`,
  `partido_transaccion_inicio` / `_fin` en `CargarPartidoUseCase`, y `usuario_creado`, `club_creado`,
  `club_actualizado`, `club_eliminado`, `jugador_creado`, `jugador_actualizado`, `jugador_eliminado`,
  `competencia_creada`, `categoria_creada`, `inscripcion_creada`, `partido_eliminado`.
- **Repositorio de clubes:** un `DEBUG` en cada INSERT, para que el test de integración pruebe que el id llega
  hasta la base.
- **Tests:** `tests/unit/test_observabilidad.py`, `tests/integration/test_observabilidad_flujo.py`, eventos en
  `test_uc_auth.py` y `test_session_manager.py`, la fixture `registros_log` en `tests/conftest.py`, y `test_errores.py`
  con el `nombre`.
- **Docs:** PRD (US-110 hecha, decisiones, ADR-011 en la tabla, composition root), `docs/adr/ADR-011-logs-estructurados.md`,
  RUNBOOK ("Leer los logs": formato, eventos, variables, `jq` y PowerShell), `01-logger.md` (sección US-110),
  `13-gui-flet-y-eventos.md` (sección 22 y la firma nueva) y `09-testing.md` (`registros_log`).

## Verificado

Suite completa, benchmarks, `ruff check`, `ruff format --check` y `mypy --strict` en verde, en una copia del repo.
Prueba de humo con el `configuracion_log()` real escribiendo a un archivo temporal: cuatro líneas JSON con el mismo
`correlation_id`, `password_hash` y el email tapados.

## Pendiente / riesgos

- No se abrió la app real: conviene correrla con `STATSPRO_LOG_SINK=consola` y ver que cada clic y cada cambio de
  pantalla tengan su propio id.
- La redacción es por clave y patrón: un secreto logueado sin clave reconocible no se tapa.
- Importación Excel y backup/restore se suman a los eventos cuando existan (US-201, US-402).
