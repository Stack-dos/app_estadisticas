# Sesión 2026-07-31 — Exploración inicial y corrección del plan de desarrollo

> **Cómo usar esta carpeta:** cada sesión de trabajo con IA sobre este proyecto debería dejar un
> archivo acá (`YYYY-MM-DD-titulo-corto.md`) con qué se hizo, qué se encontró y qué queda
> pendiente. La idea es que la próxima sesión (con esta IA o cualquier otra) pueda leer el último
> archivo y entender el estado del proyecto en un minuto, sin tener que re-explorar todo de cero.

## Qué se pidió

Explorar `/docs` para entender el proyecto, completar y corregir el PRD, pasarlo a un `.md`
simple y usable, revisar el código actual contra ese plan, y dejar este registro de contexto.
Mencionaron puntualmente que notaron que faltaba una entidad/repositorio que maneje competencia,
inscripciones, etc.

**Aclaración importante recibida a mitad de sesión:** el usuario no quiere que la IA toque
código — de eso se encarga el equipo. El rol de la IA en este proyecto, al menos por ahora, es
**solo documentación** (y sugerencias/ideas conceptuales, no implementación).

## Qué se exploró

- Todo `/docs`: el submódulo git `docs/documentacion_app_estadistica/` (repo del compañero,
  `marcosbattigane/documentacion_app_estadistica`) con el PRD formal en LaTeX/PDF, la versión
  Markdown del plan de desarrollo, y el material de `contexto_aux/`.
- Todo `src/`: entidades de dominio, interfaces de repositorio, las 4 implementaciones SQLite
  existentes, `database_manager.py`, `main.py`, `config/rutas.py`, `infraestructura/logger.py`.
- Todo `test/`: se corrió la suite completa (`pytest -v`) — los 19 tests existentes pasan, pero
  ninguno ejercita los repositorios de `infraestructura/repositorios/`.
- Los scripts SQL reales (`schema.sql`, `views.sql`, `seed.sql`, `limpieza.sql`).

## Qué se encontró (hallazgos, no arreglados — solo documentados)

1. **El gap que mencionó el usuario, confirmado:** la interfaz `CompetenciaRepositorio` existe
   completa en `dominio/repositorios/`, pero no tiene implementación concreta
   (`SqliteCompetenciaRepositorio`) en `infraestructura/repositorios/`. Además, la tabla resumen
   "Estructura de Repositorios" del plan de desarrollo se había olvidado de listarlo (ya
   corregido en la actualización de este mismo día — ver `docs/plan_desarrollo_detallado.md`).

2. **Hallazgo adicional, no mencionado por el usuario:** las 4 implementaciones SQLite que sí
   existen (`sqlite_club_repositorio.py`, `sqlite_juego_repositorio.py`,
   `sqlite_jugador_repositorio.py`, `sqlite_usuario_repositorio.py`) importan
   `from infraestructura.persistencia.sqlite_conexion import SqliteConexion` — **esa clase no
   existe en ningún lado del proyecto**. Ninguno de los 4 repositorios se puede importar hoy sin
   `ModuleNotFoundError`. Es probablemente la razón real por la que nadie llegó a escribir el de
   competencia todavía: falta esta pieza de conexión antes.

3. **Segundo hallazgo:** `sqlite_juego_repositorio.py` y `sqlite_usuario_repositorio.py` además
   apuntan a nombres de tabla/columna que no coinciden con `schema.sql` real (`Juego` en vez de
   `partido`, `idJuego` en vez de `idPartido`, `Usuarios` en vez de `usuario`, `id_usuario` en vez
   de `idUsuario`, `pw` en vez de `contrasenia`). El `INSERT` de `guardar_boxscore` en
   `sqlite_juego_repositorio.py` tiene además la lista de columnas desalineada de los valores.

4. `docs/plan_desarrollo_detallado.md` (raíz, fuera del submódulo) estaba **desactualizado**
   respecto a la copia dentro del submódulo — le faltaba toda mención de
   `CompetitionRepository`/`SQLiteCompetitionRepository`. Ya se corrigió/sincronizó.

5. `database_manager.py` (el `SQLiteManager`) está sólido y bien testeado — es la parte más
   madura del código hoy.

## Qué se hizo en esta sesión

- Se actualizó `docs/plan_desarrollo_detallado.md`: versión simplificada (menos densa que el
  PRD en LaTeX), con la tabla de repositorios corregida y una sección nueva de "Estado real del
  código vs. plan" documentando los 3 hallazgos de arriba.
- Se creó esta carpeta `docs/context_ia/` con este registro.
- Se creó `docs/info_modulo/10-docker-para-tests.md` — guía conceptual de Docker para correr los tests
  (sin escribir el Dockerfile real, eso lo hace el equipo).
- Se creó `docs/ideas-aprendizaje.md` — propuestas de funcionalidades chicas pensadas como
  ejercicios de aprendizaje (decorador de retry/backoff, cache simple, exportador CSV, loader de
  configuración por entorno, validadores de dominio como funciones puras, mini-CLI de prueba).

**Nota:** en un momento de la sesión, antes de que el usuario aclarara "no toques código", se
llegaron a crear por error dos archivos (`sqlite_conexion.py` y
`sqlite_competencia_repositorio.py`). El usuario pidió borrarlos y así se hizo — no quedan
rastros de esos archivos en el repo.

## Qué queda pendiente (para el equipo, no para la IA)

- Crear la clase `SqliteConexion` faltante (desbloquea los 4 repositorios existentes).
- Corregir las tablas/columnas mal referenciadas en `sqlite_juego_repositorio.py` y
  `sqlite_usuario_repositorio.py`.
- Implementar `SqliteCompetenciaRepositorio` (el gap original).
- Agregar tests de integración que efectivamente importen y ejerciten los 5 repositorios — hoy
  ese hueco de cobertura es la razón por la que los bugs de arriba pasaron desapercibidos.
- Escribir los 9 ADRs pendientes (tabla en `docs/plan_desarrollo_detallado.md`, sección 5),
  empezando por los que bloquean el hito más próximo.
- Si les sirve, armar el Dockerfile real siguiendo `docs/info_modulo/10-docker-para-tests.md`.

## Dónde está cada cosa (índice rápido para la próxima sesión)

- Plan de trabajo simplificado: `docs/plan_desarrollo_detallado.md`
- PRD formal completo: `docs/documentacion_app_estadistica/PRD/Plan_Requerimientos_Producto_Pro.tex` (submódulo)
- Arquitectura en detalle: `docs/info_modulo/04-arquitectura.md`
- Vistas SQL explicadas: `docs/info_modulo/08-vistas-sql.md`
- Ideas de aprendizaje: `docs/ideas-aprendizaje.md`
- Guía de Docker: `docs/info_modulo/10-docker-para-tests.md`
