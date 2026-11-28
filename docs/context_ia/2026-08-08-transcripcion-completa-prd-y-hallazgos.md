# Sesión 2026-08-08 — Expansión de ideas, diagnóstico de bug y transcripción completa del PRD

> Continúa desde `2026-07-31-exploracion-inicial.md`. Ver ese archivo primero si es tu primera
> vez en este proyecto.

## Qué se pidió (en orden)

1. Expandir `docs/ideas-aprendizaje.md`: más profundidad en la idea del "loader de
   configuración" (cómo funciona, conexión con el empaquetado de Hito 4, qué configs migrarían
   desde `rutas.py`).
2. Sumar a `docs/ideas-aprendizaje.md` una sección con ideas para completar el pipeline de CI más
   allá de solo correr tests.
3. Diagnóstico de un `ImportError` real que le tiró pytest al usuario.
4. Pregunta abierta sobre armar un benchmark de rendimiento — se empezó a explorar en Plan Mode y
   quedó **interrumpida sin resolver** (ver pendientes).
5. Generar `docs/context_ia/resumen-conversacion-completa.md`: un resumen para pasar de contexto
   a otro chat (pedido puntual, ya cumplido, archivo separado).
6. **Tarea grande de la sesión:** reescribir `docs/plan_desarrollo_detallado.md` para que sea una
   **transcripción completa y fiel del PRD original** (no un resumen) — todas las US, épicas,
   hitos, criterios de aceptación, archivos a crear y funciones — usando como referencia de
   formato el `tp.md` de otro proyecto del usuario (EOP), y documentando en el mismo documento
   cualquier inconsistencia encontrada al transcribir.

## Qué se hizo

### 1-2. `docs/ideas-aprendizaje.md` ampliado

- **Config loader:** se agregó el detalle de `.env`/`.env.example`, un módulo `Settings`, tabla
  mapeando los valores actuales de `rutas.py` a futuras variables de entorno, y la conexión con
  el empaquetado de Hito 4 (US-404) vía `~/.statspro/config.json`.
- **Sección 7 nueva — "Completar el pipeline de CI":** 8 sub-ideas concretas: cobertura que
  bloquee de verdad (`--cov-fail-under=80`), `ruff format --check`, `mypy` (con un bug real de
  tipado ya detectado: `sqlite_club_repositorio.py::buscar_por_id` declarado `-> Club` pero puede
  devolver `None`), `pip-audit`, `gitleaks`, separar tests rápidos/lentos, Dependabot, build de
  Docker en CI.

### 3. Diagnóstico del `ImportError`

`ModuleNotFoundError: No module named 'entidades'` al correr `test/test_repositorios.py`. Causa:
los 5 archivos de `src/dominio/repositorios/*.py` importaban `from entidades.X import ...` en vez
de `from dominio.entidades.X import ...` — con `pythonpath = src` en `pytest.ini`, solo la ruta
completa (`dominio.entidades`) es resoluble. Solo se explicó, no se tocó código (regla del
proyecto). **Verificado más tarde en esta misma sesión que el equipo ya lo corrigió** — los 5
archivos usan el import correcto ahora.

### 4. Benchmark — abierto, sin resolver

El usuario preguntó si valdría la pena un benchmark de rendimiento de la app. Se entró en Plan
Mode, hubo algo de exploración de solo lectura, y la conversación giró hacia el pedido de resumen
(punto 5) antes de llegar a un plan concreto. **No hay nada decidido ni descartado** — si se
retoma, hay que arrancar de cero la conversación sobre alcance (¿qué se mide? ¿tiempo de ingesta
Excel, tiempo de queries con las vistas, tiempo de arranque de la futura GUI?).

### 5. `docs/context_ia/resumen-conversacion-completa.md`

Creado para pegar como contexto en otro chat — no se detalla más acá para no duplicar, ver ese
archivo directamente si hace falta.

### 6. Transcripción completa del PRD → `docs/plan_desarrollo_detallado.md`

Se reescribió el archivo por completo (reemplaza la versión simplificada de la sesión anterior).
Fusiona las dos fuentes del submódulo del compañero:

- `PRD/Plan_Requerimientos_Producto_Pro.tex` (LaTeX — más completo en descripción general,
  reglas de negocio consolidadas, NFRs, DoD, catálogo de criticidad, proceso de release, y
  **es la única fuente que tenía completos los Hitos 3 y 4**).
- `PRD/plan_desarrollo_detallado.md` (el `.md` del submódulo — más rico en Hito 1-2 con firmas
  exactas de método por interfaz de repositorio).

El resultado tiene 20 secciones, cubre las **24 historias de usuario completas** (US-101 a
US-108, US-201 a US-205, US-301 a US-303, US-401 a US-404) con Objetivo Funcional, desglose por
capa (Dominio/Aplicación/Infraestructura), Criterios de Aceptación completos, Reglas de Negocio,
Testing Mínimo y archivos a crear — nada resumido.

## Hallazgos nuevos de esta sesión (documentados en la sección 20 del plan, no corregidos en código)

1. **Grande — el `.md` del submódulo tenía Hito 3 y 4 incompletos.** Le faltaba entera la épica
   de Scouting (US-303) y las tres épicas de Backup/Seguridad/Empaquetado (US-402, US-403,
   US-404). Solo estaban en el LaTeX. Ya están completas en nuestra copia.
2. **Patrón de conexión de repositorios partido a la mitad:** `SqliteUsuarioRepositorio` y
   `SqliteClubRepositorio` ya migraron a recibir `sqlite3.Connection` crudo (funciona, testeado —
   25 tests pasan). `SqliteJugadorRepositorio` y `SqliteJuegoRepositorio` **siguen** importando la
   clase `SqliteConexion`, que nunca se creó. Recomendación (solo documentada): unificar todos al
   patrón que ya funciona.
3. `sqlite_juego_repositorio.py` sigue con tabla `Juego`/`idJuego` en vez de `partido`/`idPartido`.
4. ✅ `sqlite_usuario_repositorio.py` — el bug de tabla/columna de la sesión anterior **ya está
   resuelto** por el equipo.
5. **Tres versiones distintas de la Definición de "Hecho"** repartidas entre el LaTeX y dos
   puntos distintos del `.md` del submódulo — se consolidaron en una sola en el documento nuevo.
6. El `.md` del submódulo no tenía sección de NFRs ni de Proceso de Liberación de Versiones —
   solo estaban en el LaTeX. Ya agregadas.
7. El propio LaTeX se contradice sobre a qué hito bloquean ADR-002 y ADR-008 (el texto narrativo
   dice un hito, la tabla de ADRs dice otro) — quedó documentado como discrepancia sin resolver
   unilateralmente, para que el equipo lo confirme.
8. Typo cosmético que persiste: la clase `SquliteJugadorRepositorio` (falta una "i").
9. La tabla "Estructura de Repositorios" seguía sin la fila de Competencia en ambas fuentes
   originales — corregida en nuestra copia (no se toca el submódulo).

## Qué queda pendiente

- Todo lo técnico de la sesión anterior sigue pendiente para el equipo (crear
  `SqliteCompetenciaRepositorio`, unificar el patrón de conexión, corregir
  `sqlite_juego_repositorio.py`, corregir el typo de clase).
- **Benchmark de rendimiento:** conversación abierta, sin plan ni alcance definido — retomar si
  el usuario lo trae de nuevo.
- Escribir los 9 ADRs pendientes (tabla en `docs/plan_desarrollo_detallado.md`, sección 8/18) —
  seguimos sin hacerlo nosotros salvo pedido explícito.
- Resolver la contradicción de a qué hito bloquean ADR-002 y ADR-008 (hallazgo #7 de arriba).

## Dónde está cada cosa (actualizado)

- Plan de trabajo **completo y detallado** (nuevo, reemplaza la versión resumida):
  `docs/plan_desarrollo_detallado.md`
- PRD formal completo (LaTeX): `docs/documentacion_app_estadistica/PRD/Plan_Requerimientos_Producto_Pro.tex`
- Ideas de aprendizaje (ampliadas hoy): `docs/ideas-aprendizaje.md`
- Guía de Docker: `docs/info_modulo/10-docker-para-tests.md`
- Resumen de contexto para otro chat: `docs/context_ia/resumen-conversacion-completa.md`
- Sesión anterior: `docs/context_ia/2026-07-31-exploracion-inicial.md`
