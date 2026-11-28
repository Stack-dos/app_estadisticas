# 2026-10-31 — Se retira la CLI y la GUI pasa al Hito 1

## Decisión

Terminada la US-104, se decidió dejar de construir la CLI y pasar a la GUI de escritorio (Flet)
desde ya. Motivos:

- El usuario final es un DT, no alguien que use la terminal.
- La carga de partido, la consulta de estadísticas y los dashboards se iban a construir dos veces
  (consola y después Flet).
- La sesión persistente obligatoria existía solo porque cada comando de la CLI era un proceso
  nuevo.
- Con la arquitectura limpia, el cambio solo toca `ui/`.

## Renumeración del Hito 1

| Historia                                 | Antes  | Ahora  |
| ---------------------------------------- | ------ | ------ |
| Interfaz gráfica base y retiro de la CLI | —      | US-105 |
| Sesión persistente y club activo         | US-105 | US-106 |
| Pantallas de gestión                     | US-107 | US-107 |
| Carga atómica de partido                 | US-106 | US-108 |
| Entorno de desarrollo y CI/CD            | US-109 | US-109 |
| Monitoreo y trazabilidad                 | US-108 | US-110 |

La US-105 también borra `ui/cli/`, sus tests, `tabulate` y la carpeta `scripts/`.

## Qué se cambió en la documentación

- **PRD:** las historias del Hito 1 se reescribieron para la GUI. En los Hitos 2 a 4 las salidas
  de consola pasaron a pantallas: `ImportScreen` en la US-201, pantallas de consulta en la US-205,
  y `DashboardScreen` con `ChartComponent` en la US-301. La US-401 quedó con lo que no tenía dueño
  (perfil de jugador, backup, tema, mobile). La US-404 quedó sin la parte de la CLI.
- **Guías, README y RUNBOOK:** donde describen el código actual (la CLI todavía existe) llevan un
  aviso de que se reescriben en la US-105. Los textos que hablaban del futuro se corrigieron ya.
- **ADRs:** ADR-002 tiene una sección de actualización con el adelanto de la GUI. ADR-007, 008 y
  009 dejaron de nombrar a la CLI como consumidor.
- Los informes anteriores de `docs/context_ia/` no se tocaron: son registro histórico.

## Hallazgos de las tres revisiones del PRD

- **Datos desactualizados:**
  - Nombres que ya no existen (`JuegoRepositorio`, `EstadisticaJugadorPartido`, DTOs de ejemplo).
  - La US-101 decía que `schema.sql` hace `DROP TABLE` (se corrigió en la US-103).
  - Las secciones 17, 19 y 20 tenían estados viejos (repositorios "no funcionales", "53 tests",
    "falta el job agregador").
  - Las rutas de tests decían `test/` cuando la carpeta real es `tests/unit|integration`.
- **Nombres:** `aplicacion/services/` pasó a `aplicacion/servicios/` y `AnalyticsService` a
  `dominio/servicios/`, para alinearlos con `dominio/servicios/` del código (US-104).
- **Huecos entre historias:**
  - El listado de jugadores no tenía DNI en `JugadorDTO`, y no había forma de buscar un jugador
    que todavía no está en el club. La US-107 suma `BuscarJugadorPorDniUseCase` y el DNI en el
    DTO.
  - Ninguna historia creaba `ObtenerLideresTemporadaUseCase` en versión básica; ahora lo hace la
    US-205 y la US-301 lo amplía.
  - El club rival de un partido no es del usuario, pero `CrearClubUseCase` va a vincularlo
    siempre (US-106) y no hay forma de listar todos los clubes. Queda como decisión pendiente de
    la US-108.
- **Contradicción:** la US-108 decía que el club activo era siempre el local, lo que hacía
  imposible cargar partidos de visitante y vaciaba el filtro local/visitante de la US-301. Se
  corrigió: el club activo es uno de los dos equipos y el formulario pregunta la condición.

## Plan de trabajo en paralelo

El equipo es de dos, así que en la sección 9 del PRD se agregó un plan en dos pistas: **A**
(interfaz) y **B** (backend). Todas las historias pendientes tienen un bloque "Reparto en dos
pistas". La US-105 bloquea todas las pantallas: la hace A, y B solo aporta el `SessionManager`. El
Hito 1 va en cuatro rondas. Antes de cada ronda se acuerdan juntos los contratos (DTOs y firmas).

## Partidos de otros clubes e importación (decisiones del 2026-10-31)

El problema: si solo se cargan los partidos del club propio, ese club tiene N partidos y cada
rival 0 o 1. El promedio de un rival con un solo partido no dice nada. Decisiones:

1. **Cualquier partido de la competencia.** Se puede cargar aunque el club activo no juegue; el club
   activo solo viene preseleccionado (US-108).
2. **Las listas de buena fe se generan al importar.** Cada competencia (con su temporada) tiene
   categorías, y cada categoría tiene una lista por club. Hay dos formas de cargarlas:
   - importar una planilla de partido genera o completa las listas de los dos clubes (US-201);
   - importar el listado "Jugadores" de la CAB carga la lista de un club (US-206, nueva).
   Los jugadores importados no exigen DNI, porque los archivos no lo traen.
3. **El partido guarda la categoría.** La misma categoría juega varias competencias y temporadas, y
   cada una tiene listas distintas.

Con los archivos reales de `data/` (Excel y PDF de Gesdeportiva):

- **ADR-003:** pasó de borrador a propuesta. Mapeo fijo buscando encabezados por texto, y
  `pdfplumber` para el PDF.
- **US-201:** reescrita con el formato real. Su AC3 ahora se valida contra la fila `TOTALES`, así
  que ya no depende de la US-204.
- **Nombre del producto:** se corrigió de "Ges Deportivo" a "Gesdeportiva".

Hallazgos del formato:

- Ninguno de los dos archivos trae DNI, fecha ni estadio.
- Los dos archivos nombran distinto la misma categoría (`U13MX` y `INFANTILES MIXTO`).
- En el Excel todas las celdas son texto.
- Los titulares y el capitán solo vienen en el PDF.

## Segunda tanda de decisiones (2026-10-31)

- **Los jugadores no tienen DNI.** No aporta a las estadísticas y los archivos no lo traen. Un
  jugador se identifica por apellido y nombre dentro de su club, y el año de nacimiento pasa a ser
  opcional.
  - El cambio de código va en un **ajuste previo a la US-105**, en su propia rama
    (`feature/quitar-dni-jugador`). No es un `hotfix/`: todavía no hay nada en producción.
  - El ajuste lo hace la Pista B en la ronda 1. La Pista A borra la CLI recién cuando el ajuste
    está mergeado.
  - La US-107 cambia la búsqueda por DNI por una búsqueda por nombre. La US-206 ya no tiene el caso
    de uso para completar el DNI.
- **`partido.idCategoria`:** se cambia `schema.sql` en la US-108 y cada uno recrea su base local.
- **US-201:**
  - Dorsal, titular, capitán, entrenador, `VAL` y `+/-` no se guardan en v0.2.
  - Lo que se crea antes del partido (clubes, jugadores, inscripciones) puede quedar guardado si el
    partido falla, pero reimportar no lo duplica.
- **Muestra chica** (sección 6 y las US-202, US-205 y US-301):
  - siempre se muestran los partidos jugados (PJ);
  - los rankings piden un mínimo de partidos (configurable, 3 por defecto);
  - las comparaciones con poca muestra llevan un aviso;
  - se ofrecen valores cada 40 minutos.
- `data/` quedó en el `.gitignore`.

## Pendiente

- Al arrancar la US-105:
  - elegir y fijar la versión de Flet;
  - definir cómo se testean las pantallas.
- Al arrancar la US-106: decidir si la sesión se guarda a través de un puerto (como
  `PasswordHasher`).
- Antes de las US-206 y US-201: confirmar el ADR-003 (mapeo por encabezados y `pdfplumber`).
- El ajuste previo actualiza las guías que hoy describen el DNI: `03`, `04`, `07` y `09` de
  `docs/info_modulo/`, `01-repository-pattern.md`, el DER, `RUNBOOK.md` y `README.md`.
