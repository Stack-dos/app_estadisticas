# Benchmarks de consultas — cómo se miden, cómo se leen y qué encontramos

> Guía de referencia de `tests/benchmarks/` y del segundo comentario que deja el CI en cada PR. Las secciones 1 a 6
> explican **qué es → qué problema resuelve → cómo funciona → ejemplo del proyecto → errores comunes**. La sección 7
> es el **informe de los primeros resultados** (2026-11-22): qué consultas escalan bien, cuáles no y por qué.

## Índice

1. [Qué es un benchmark (y en qué se diferencia de un test)](#1-qué-es-un-benchmark-y-en-qué-se-diferencia-de-un-test)
2. [Las estadísticas: mediana, IQR, OPS](#2-las-estadísticas-mediana-iqr-ops)
3. [Datos de volumen y escalas](#3-datos-de-volumen-y-escalas)
4. [El plan de ejecución: `EXPLAIN QUERY PLAN`](#4-el-plan-de-ejecución-explain-query-plan)
5. [Cómo está armado en el proyecto](#5-cómo-está-armado-en-el-proyecto)
6. [Agregar un benchmark nuevo y errores comunes](#6-agregar-un-benchmark-nuevo-y-errores-comunes)
7. [Informe de resultados (2026-11-22)](#7-informe-de-resultados-2026-11-22)

---

## 1. Qué es un benchmark (y en qué se diferencia de un test)

**Concepto.** Un test responde *"¿anda?"* (sí o no). Un **benchmark** responde *"¿cuánto tarda?"*: corre la misma
función muchas veces (cada vez es una **ronda**, *round*) y resume los tiempos con estadísticas.

**Problema que resuelve.** Una consulta puede estar bien (el test pasa) y aun así volverse lenta cuando la base crece:
con 30 partidos nadie lo nota, con 3.000 la pantalla tarda. El benchmark lo detecta antes de que lo note el usuario, y
en cada PR muestra si un cambio hizo algo más lento.

**Cómo funciona.** `pytest-benchmark` agrega el fixture `benchmark`: `benchmark(funcion, *args)` llama a la función
cientos o miles de veces (hasta llenar el tiempo de `--benchmark-max-time`), mide cada llamada y guarda las estadísticas
en `bench.json`. Las primeras llamadas sirven de calentamiento (*warmup*), para no medir cachés vacías.

**Por qué no hace fallar el CI.** Los runners de GitHub son máquinas compartidas: el mismo código puede tardar 20 % más
en una corrida que en otra. Un umbral duro daría falsos rojos. Por eso el reporte **avisa** (⚠️) y no bloquea.

## 2. Las estadísticas: mediana, IQR, OPS

| Estadística | Qué es | Para qué sirve |
|---|---|---|
| **Mediana** | el tiempo del medio, ordenando todas las rondas | **la que se compara**: una ronda rara (el runner ocupado) no la mueve |
| Media | el promedio | se distorsiona con un solo valor alto (ver `partido.buscar_por_club`: mediana 397 µs, media 464 µs, máx 13 ms) |
| Mín / Máx | la ronda más rápida y la más lenta | el máx casi siempre es ruido; el mín es "lo mejor posible" |
| Desv. est. | cuánto se alejan las rondas de la media | grande = medición inestable |
| **IQR** | rango entre el cuartil 1 (25 %) y el 3 (75 %) | como la desviación, pero sin dejarse llevar por los extremos |
| OPS | operaciones por segundo = 1 / media | lo mismo dado vuelta: útil para pensar "cuántas veces por segundo aguanta" |
| Rondas | cuántas veces se midió | las rápidas tienen miles; las lentas, pocas (ver la vista de totales: 8) |

**Ejemplo.** `usuario.encontrar_por_mail`: mediana 3 µs, IQR 0,1 µs, 13.551 rondas → medición muy estable.
`vista_totales_temporada_completa` en `x10`: mediana 68 ms con solo 8 rondas → el número sirve, pero tiene menos muestras.

## 3. Datos de volumen y escalas

**Problema.** `seed.sql` tiene 11 inserts: sobre esa base todas las consultas tardan ~1 µs y no se aprende nada.

**Cómo funciona.** `construir_base()` (en `tests/benchmarks/ayudantes_bench.py`) arma una base en memoria con el
schema y las vistas **reales** y la llena con una liga simulada, con semilla fija (siempre los mismos datos):

| Escala | Qué simula | jugadores | partidos | filas de boxscore |
|---|---|---|---|---|
| `temporada` | 16 clubes de 15 jugadores, ida y vuelta | 240 | 240 | 5.760 |
| `x10` | diez temporadas, con 3 bajas y 3 altas por club cada año | 672 | 2.400 | 57.600 |

Cada benchmark corre en las dos escalas. El **crecimiento** es la mediana en `x10` dividida la de `temporada`:

| Crecimiento | Qué significa | Ejemplo |
|---|---|---|
| **constante** (< x2) | el tiempo no depende del tamaño: va directo a las filas con un índice | `partido.buscar_por_id`: x1,0 |
| **lineal** (~x10) | recorre algo que crece con los datos (O(n)) | `partido.buscar_por_club`: x9,8 |
| **más que lineal** (> x15) | crece más rápido que los datos (O(n log n), O(n²)): hay que mirarlo | ninguna hoy |

Ojo: "lineal" no siempre es malo. Si la consulta **tiene** que leer todo (`obtener_todas`, la vista completa para
el motor estadístico), lineal es lo esperable. El problema es una consulta que pide **unas pocas filas** y crece lineal:
señal de que recorre la tabla entera para encontrarlas.

## 4. El plan de ejecución: `EXPLAIN QUERY PLAN`

**Concepto.** Antes de ejecutar una consulta, SQLite decide *cómo* hacerlo. `EXPLAIN QUERY PLAN <consulta>` muestra
esa decisión sin ejecutarla:

| Paso del plan | Qué hace | Costo |
|---|---|---|
| `SEARCH partido USING INTEGER PRIMARY KEY (rowid=?)` | va directo a la fila por su id | constante |
| `SEARCH usuario USING INDEX sqlite_autoindex_usuario_1 (email=?)` | busca en un índice (el que crea `UNIQUE`) | constante (log n) |
| `SEARCH ... USING COVERING INDEX ...` | igual, y además todo lo que pide está en el índice: ni lee la tabla | constante |
| `SCAN partido` | **recorre la tabla entera** | lineal |
| `SCAN jc USING INDEX ...` | recorre un índice entero (más chico que la tabla, pero entero) | lineal en el tamaño del índice |
| `USE TEMP B-TREE FOR ORDER BY / GROUP BY` | arma una estructura temporal para ordenar o agrupar | n log n sobre las filas que llegan |
| `CO-ROUTINE v_...` | calcula una subconsulta (acá, una vista con `GROUP BY`) | lo que cueste adentro |

**Por qué importa en el reporte.** A diferencia del tiempo, **el plan no tiene ruido**: da lo mismo en cualquier máquina.
Si una PR hace aparecer un `SCAN` que antes no estaba (🆕), es un cambio real, no una corrida lenta.

**Cómo se captura sin copiar el SQL.** `plan_de_ejecucion()` usa `conexion.set_trace_callback`, que recibe cada
sentencia que ejecuta la conexión **con los valores ya reemplazados**; después le corre `EXPLAIN QUERY PLAN` a cada
`SELECT`. Así el plan sale del SQL que el repositorio ejecuta de verdad, y si alguien cambia la consulta, el plan cambia solo.

**Dos reglas de índices que explican casi todos los hallazgos:**

1. **Un índice compuesto solo sirve desde su primera columna.** La clave primaria de `jugadorPartido` es
   `(idJugador, idPartido)`: sirve para "las filas de este jugador", **no** para "las filas de este partido". Es como una
   guía telefónica ordenada por apellido y nombre: sirve para buscar "Pérez, Juan", no para buscar a todos los "Juan".
2. **SQLite no crea índices para las claves foráneas.** `FOREIGN KEY (idClubLocal) REFERENCES club` valida que el club
   exista, pero no indexa `partido.idClubLocal`. (MySQL sí lo hace solo; SQLite y PostgreSQL, no.)

## 5. Cómo está armado en el proyecto

```
tests/benchmarks/
  ayudantes_bench.py       construir_base (datos), copiar_base, plan_de_ejecucion, medir_lectura
  conftest.py              fixture `datos`: una base por escala, una sola vez por corrida (scope="session")
  test_bench_lecturas.py   una consulta de cada repositorio, agrupadas por repositorio (group=...)
  test_bench_vistas.py     las vistas de views.sql que todavía no usa ningún repositorio (base de la US-203)
  test_bench_escrituras.py las escrituras transaccionales (benchmark.pedantic, con una copia nueva por ronda)
.github/scripts/reporte_benchmark.py   arma el segundo comentario de la PR a partir de bench.json
```

- **Fuera de la suite normal:** `pyproject.toml` tiene `addopts = ["-m", "not benchmark"]`. Para correrlos:
  `uv run pytest tests/benchmarks -m benchmark --benchmark-only` (el último `-m` gana).
- **En el CI:** el job `benchmark` los corre en cada PR **y en cada push a una rama base**; el `resumen-pr` compara contra
  la última corrida de la rama base y publica el reporte en un **segundo comentario** (marca `<!-- resumen-benchmark -->`),
  que se edita en cada push. El comentario principal solo muestra una línea en el semáforo.
- **Lecturas:** comparten la base de la escala (no la modifican). **Escrituras:** `benchmark.pedantic(..., setup=...)`
  copia la base antes de cada ronda (`copiar_base`, con `Connection.backup`), y esa copia **no se mide**.

## 6. Agregar un benchmark nuevo y errores comunes

```python
@pytest.mark.benchmark(group="partido")              # el grupo = la tabla del reporte
def test_bench_partido_lo_que_mide(benchmark, datos):  # "datos" = corre en las dos escalas
    repo = SqlitePartidoRepositorio(datos.conexion)
    assert medir_lectura(benchmark, datos, repo.metodo, datos.ids["id_club"])
```

1. Si la consulta necesita un id que no está en `datos.ids`, se agrega en `construir_base()`.
2. El `assert` no es decorativo: un benchmark que mide una consulta que devuelve vacío mide la nada.
3. Para escrituras, copiar el patrón de `test_bench_escrituras.py` (pedantic + `copiar_base`).

**Errores comunes:**

- **Medir sobre `seed.sql`:** todo tarda lo mismo. Siempre con `datos`.
- **Escribir sobre la base compartida:** la siguiente ronda (y los otros benchmarks) encuentran una base distinta.
- **Comparar medias:** una ronda de 13 ms arruina el promedio. El reporte compara medianas.
- **Creer en un ⚠️ aislado:** si una sola corrida sale 25 % más lenta y el plan no cambió, probablemente es el runner.
  Correr de nuevo antes de investigar.
- **Comparar números de máquinas distintas:** los valores de esta guía son de una PC de desarrollo; los del CI van a ser
  otros. Lo que se compara es **la misma consulta en la misma máquina** (base vs PR) y **el crecimiento entre escalas**.
- **"Tiene SCAN, entonces está mal":** un SCAN sobre `club` (16 filas) o sobre `competencia` (10) no importa. Importa
  sobre las tablas que crecen con cada partido: `partido`, `jugadorPartido`, `jugadorListaBuenaFe`.

---

## 7. Informe de resultados (2026-11-22)

Corrida local (Windows, Python 3.12, SQLite 3.53), escala `x10` salvo que se diga otra cosa. **19 consultas: 8 van
directo con índice y 11 tienen algún `SCAN`.** Ninguna crece más que lineal y todas tardan menos de 1,2 ms, salvo las
dos vistas de totales (68 ms la completa y 8,7 ms la de un año). Hoy nada es un problema para el usuario; el informe sirve para saber **qué va a
crecer con cada temporada cargada** y dónde mirar cuando haga falta.

### 7.1 Lo que está bien

| Consulta | x10 | Por qué es rápida |
|---|---|---|
| `usuario.encontrar_por_mail` (login) | 3,1 µs | `UNIQUE` en `email` crea un índice |
| `club.buscar_por_id_usuario` | 2,1 µs | la PK de `usuarioClub` empieza por `idUsuario` (índice cubriente) |
| `jugador.club_activo` | 2,1 µs | el índice parcial `uq_jugadorclub_activo_por_jugador` |
| `jugador.historial_vinculos` | 3,4 µs | la PK de `jugadorClub` empieza por `idJugador` |
| `competencia.categorias_de_competencia` | 4,7 µs | la PK de `competenciaCategoria` empieza por `idCompetencia` |
| `partido.buscar_por_id` | 2,6 µs | clave primaria |
| `vista_lista_de_una_inscripcion` (casi toda) | 63 µs | todo por PK, salvo `jugadorListaBuenaFe` (ver 7.3) |
| Escrituras (`save_with_boxscore`, competencia + categorías) | 0,2–0,35 ms | constantes: las validaciones previas buscan por PK |

### 7.2 Lo que crece con cada temporada (prioridad media)

**`partido.buscar_por_club` y `partido.resumen_por_club` — `SCAN partido`, x9,8 (397 µs y 461 µs).**
Piden los 30 partidos de un club por temporada y recorren **todos** los partidos de todos los clubes. Causa: regla 2
(`idClubLocal` e `idClubVisitante` son claves foráneas sin índice), y además la condición es un `OR` entre las dos
columnas. Con un índice en **cada** columna, SQLite puede resolver el `OR` buscando en los dos (*multi-index OR*).
Las usan la pantalla de partidos de la US-112 y la carga de la US-108.

**`vista_boxscore_de_un_partido` — `SCAN part`, x7,8 (1,17 ms).** Pide las 24 filas de un partido y recorre las
57.600 de `jugadorPartido`. Causa: regla 1 (la PK es `(idJugador, idPartido)`). Es la consulta que **más va a crecer**:
cada partido cargado suma 24 filas. La va a usar el boxscore de la US-112 y el motor de la US-203. Un índice en
`jugadorPartido(idPartido)` la volvería constante, y además acelera el chequeo de la FK cuando se borra un partido.

### 7.3 Tablas que crecen más despacio (prioridad baja)

| Consulta | x10 | Causa | Índice candidato |
|---|---|---|---|
| `competencia.inscripciones_por_club` | 13 µs, x3,8 | `SCAN inscripcion` (regla 2: `idClub` es FK sin índice) | `inscripcion(idClub)` |
| `competencia.jugadores_lista` | 42 µs, x4,2 | `SCAN jugadorListaBuenaFe` (regla 1: la PK empieza por `idJugador`) | `jugadorListaBuenaFe(idListaBuenaFe)` |
| `vista_lista_de_una_inscripcion` | 63 µs, x4,1 | el mismo `SCAN` de `jugadorListaBuenaFe` | el mismo |
| `jugador.buscar_por_club` | 33 µs, x1,0 | `SCAN` del índice parcial de vínculos **activos**: no crece con las temporadas (siempre hay 240 activos), pero los recorre todos para quedarse con los 15 del club | `jugadorClub(idClub) WHERE fechaHasta IS NULL` |

### 7.4 Lo que no es un problema

- `club.buscar_por_nombre` — `SCAN club`: usa `LIKE '%texto%'`, y un comodín al principio impide usar cualquier índice.
  Con 16 clubes no importa. Si algún día hay miles, la herramienta es FTS5 (búsqueda de texto de SQLite), no un índice.
- `competencia.obtener_todas` — `SCAN competencia`: pide todas, así que tiene que recorrerlas. Lineal y correcto.

### 7.5 Las vistas de totales (para la US-203)

- **`vista_totales_temporada_completa` — 68 ms, x12,5.** Agrupa las 57.600 filas de boxscore (`USE TEMP B-TREE FOR GROUP
  BY`). Es la más cara, pero es una lectura de todo para el motor de Pandas: se hace **una vez** por cálculo, no por cada
  fila de una pantalla. Ningún índice la evita: tiene que leer todo. Si un día molesta, la opción es guardar los totales
  ya calculados (una tabla que se actualiza al cargar un partido), no un índice.
- **`vista_totales_de_un_anio` — 8,7 ms, x1,6, pero con `SCAN jp`.** Parece contradictorio: recorre todo y casi no crece.
  SQLite empuja el filtro del año adentro de la vista (*push-down*), así que **agrupa** solo las filas de ese año; el
  recorrido de las 57.600 filas es barato comparado con agrupar. Con muchas más temporadas, el recorrido empezaría a pesar.

### 7.6 Qué índices mirar, en orden

Los índices son decisiones de diseño del schema (y desde la US-204, de una migración): este informe **no** los agrega.
Si se decide agregarlos, el benchmark lo va a mostrar en la PR (el plan pasa de `SCAN` a `SEARCH` y el crecimiento a constante).

1. `jugadorPartido(idPartido)` — boxscore de un partido (US-112, US-203) y borrado de partidos.
2. `partido(idClubLocal)` y `partido(idClubVisitante)` — partidos de un club (US-112, US-108).
3. `jugadorListaBuenaFe(idListaBuenaFe)` e `inscripcion(idClub)` — listas e inscripciones (US-107).

**Para pensar antes de agregar uno:** cada índice acelera las lecturas que lo usan, pero **hace más lenta cada escritura**
(hay que actualizarlo) y ocupa espacio. Por eso existen los benchmarks de escritura: después de agregar
`jugadorPartido(idPartido)`, `guardar_partido_con_boxscore` debería subir un poco. Medirlo es la forma de decidir.
