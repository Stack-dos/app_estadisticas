# Vistas SQL — Documentación Técnica

---

## 1. Introducción y Propósito

### ¿Qué es una vista SQL?

Una **vista** es una consulta `SELECT` con nombre, almacenada en la base de datos y tratable como si fuera una tabla. No almacena datos propios: cada vez que se la consulta, SQLite ejecuta la query subyacente en tiempo real sobre las tablas base.

### Rol de las vistas en StatsPro Basketball

Las vistas cumplen una función de **contrato estable entre la base de datos y la capa de análisis**. Actúan como una interfaz pública del modelo relacional hacia:

- **Motor analítico de Pandas:** los DataFrames se construyen directamente desde las vistas. Pandas recibe datos ya estructurados, renombrados y con columnas calculadas listas para graficar.
- **Futura interfaz de usuario:** los listados de partidos, boxscores y habilitados se renderizan desde estas vistas sin lógica adicional de transformación en Python.

```text
tablas base (jugadorPartido, partido, jugador, …)
          │
          ▼
  ┌───────────────────┐
  │   vistas SQL      │  ← contrato estable, nombres snake_case, tipos resueltos
  └───────────────────┘
          │
          ▼
pandas.read_sql(…)  /  cursor.execute("SELECT * FROM v_…")
```

**Beneficios clave:**

| Beneficio           | Detalle                                                                                                                                              |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **DRY en cálculos** | Los porcentajes y acumulados se calculan una vez en SQL, no en cada función de Python.                                                               |
| **Desacoplamiento** | Cambiar el nombre de una columna interna solo requiere actualizar la vista; Python sigue leyendo el mismo alias snake_case.                          |
| **Eficiencia**      | Pandas recibe el resultado pre-agregado y pre-filtrado; no itera filas crudas en memoria.                                                            |
| **Legibilidad**     | Las columnas expuestas tienen nombres descriptivos (`total_puntos`, `porcentaje_t2`) en lugar de los nombres técnicos de la tabla (`puntos`, `T2C`). |

---

## 2. Catálogo de Vistas Operativas

El sistema dispone de **4 vistas operativas**, creadas en el orden indicado al final de `views.sql`:

| Vista                         | Propósito principal                                               |
| ----------------------------- | ----------------------------------------------------------------- |
| `v_partidos_resumen`          | Listado de partidos con nombres legibles (sin IDs)                |
| `v_boxscore_completo`         | Estadísticas individuales por partido (fuente primaria de Pandas) |
| `v_jugador_totales_temporada` | Acumulados y porcentajes por jugador y año de competencia         |
| `v_listas_detalle`            | Jugadores habilitados por inscripción (listas de buena fe)        |

---

## 3. Detalle de Cada Vista

---

### 3.1 `v_partidos_resumen`

#### Descripción funcional

Expone cada partido con los nombres legibles de competencia, club local y club visitante. Elimina la necesidad de hacer JOINs en la capa de aplicación para construir listados de partidos en la UI. Cada fila representa **un partido único**.

#### Tablas involucradas

```txt
partido  →  competencia  (INNER JOIN por idCompetencia)
partido  →  club (alias cl)  (INNER JOIN por idClubLocal)
partido  →  club (alias cv)  (INNER JOIN por idClubVisitante)
```

#### Columnas expuestas

| Columna            | Tipo SQLite         | Origen / Cálculo           | Descripción                          |
| ------------------ | ------------------- | -------------------------- | ------------------------------------ |
| `id_partido`       | `INTEGER`           | `partido.idPartido`        | Clave primaria del partido           |
| `fecha_partido`    | `TEXT`              | `partido.fecha`            | Fecha en formato `YYYY-MM-DD`        |
| `estadio`          | `TEXT` _(nullable)_ | `partido.estadio`          | Nombre del estadio; puede ser `NULL` |
| `competencia`      | `TEXT`              | `competencia.nombre`       | Nombre de la competencia             |
| `anio_competencia` | `INTEGER`           | `competencia.anio`         | Año de la competencia (> 1900)       |
| `club_local`       | `TEXT`              | `club.nombre` (alias `cl`) | Nombre del club que juega de local   |
| `club_visitante`   | `TEXT`              | `club.nombre` (alias `cv`) | Nombre del club visitante            |
| `id_club_local`    | `INTEGER`           | `partido.idClubLocal`      | Id del club local (para filtrar)     |
| `id_club_visitante`| `INTEGER`           | `partido.idClubVisitante`  | Id del club visitante (para filtrar) |

> **Nota:** Los ids de los clubes se agregaron para poder filtrar por club (`WHERE id_club_local = ? OR id_club_visitante = ?`) sin perder los nombres: es lo que usa `PartidoRepositorio.resumen_por_club`
> (y por lo tanto `stats partido list`). Los partidos sin estadio asignado retornan `NULL` en la columna `estadio`.

---

### 3.2 `v_boxscore_completo`

#### Descripción funcional

Es la **fuente primaria de datos para el análisis con Pandas**. Une la tabla `jugadorPartido` con `jugador` y `club` para exponer toda la estadística individual de un jugador en un partido, reemplazando los IDs por nombres legibles y normalizando los nombres de columna a snake_case. Cada fila representa **la actuación de un jugador en un partido específico**.

#### Tablas involucradas

```txt
jugadorPartido  →  jugador  (INNER JOIN por idJugador)
jugadorPartido  →  club     (INNER JOIN por idClub)
```

#### Columnas expuestas

| Columna              | Tipo SQLite | Origen / Cálculo                   | Descripción                   |
| -------------------- | ----------- | ---------------------------------- | ----------------------------- |
| `id_partido`         | `INTEGER`   | `jugadorPartido.idPartido`         | FK al partido                 |
| `id_jugador`         | `INTEGER`   | `jugadorPartido.idJugador`         | FK al jugador                 |
| `id_club`            | `INTEGER`   | `jugadorPartido.idClub`            | FK al club con el que jugó    |
| `nombre_jugador`     | `TEXT`      | `nombre \|\| ' ' \|\| apellido`    | Nombre completo concatenado   |
| `nombre_club`        | `TEXT`      | `club.nombre`                      | Nombre del club               |
| `minutos_jugados`    | `REAL`      | `jugadorPartido.minutosJugados`    | Entre 0 y 48                  |
| `puntos`             | `INTEGER`   | `jugadorPartido.puntos`            | Puntos totales anotados       |
| `t2c`                | `INTEGER`   | `jugadorPartido.T2C`               | Tiros de 2 puntos convertidos |
| `t2l`                | `INTEGER`   | `jugadorPartido.T2L`               | Tiros de 2 puntos lanzados    |
| `t3c`                | `INTEGER`   | `jugadorPartido.T3C`               | Tiros de 3 puntos convertidos |
| `t3l`                | `INTEGER`   | `jugadorPartido.T3L`               | Tiros de 3 puntos lanzados    |
| `t1c`                | `INTEGER`   | `jugadorPartido.T1C`               | Tiros libres convertidos      |
| `t1l`                | `INTEGER`   | `jugadorPartido.T1L`               | Tiros libres lanzados         |
| `rebotes_def`        | `INTEGER`   | `jugadorPartido.rebotesDef`        | Rebotes defensivos            |
| `rebotes_of`         | `INTEGER`   | `jugadorPartido.rebotesOf`         | Rebotes ofensivos             |
| `rebotes_totales`    | `INTEGER`   | `rebotesDef + rebotesOf`           | Suma calculada en SQL         |
| `asistencias`        | `INTEGER`   | `jugadorPartido.asistencias`       | Asistencias                   |
| `recuperos`          | `INTEGER`   | `jugadorPartido.recuperos`         | Recuperos de balón            |
| `perdidas`           | `INTEGER`   | `jugadorPartido.perdidas`          | Pérdidas de balón             |
| `tapones_recibidos`  | `INTEGER`   | `jugadorPartido.taponesRecibidos`  | Tapones recibidos             |
| `tapones_realizados` | `INTEGER`   | `jugadorPartido.taponesRealizados` | Tapones realizados            |
| `faltas_recibidas`   | `INTEGER`   | `jugadorPartido.faltasRecibidas`   | Faltas recibidas              |
| `faltas_cometidas`   | `INTEGER`   | `jugadorPartido.faltasCometidas`   | Faltas cometidas              |

> **Importante:** Esta vista no incluye porcentajes de tiro. Los porcentajes individuales por partido se calculan en Pandas o se consumen desde `v_jugador_totales_temporada` para acumulados.

---

### 3.3 `v_jugador_totales_temporada`

#### Descripción funcional

Agrega toda la producción estadística de cada jugador **por año de competencia**. Incluye sumas de todas las categorías estadísticas y los tres porcentajes de tiro calculados de forma segura ante divisiones por cero. Cada fila representa **el acumulado de un jugador en un año de competencia**.

#### Tablas involucradas

```
jugadorPartido  →  jugador     (INNER JOIN por idJugador)
jugadorPartido  →  partido     (INNER JOIN por idPartido)
partido         →  competencia (INNER JOIN por idCompetencia)
GROUP BY jugador.idJugador, competencia.anio
```

#### Columnas expuestas

| Columna                    | Tipo SQLite | Origen / Cálculo                    | Descripción                            |
| -------------------------- | ----------- | ----------------------------------- | -------------------------------------- |
| `nombre_jugador`           | `TEXT`      | `nombre \|\| ' ' \|\| apellido`     | Nombre completo del jugador            |
| `anio_competencia`         | `INTEGER`   | `competencia.anio`                  | Año de la temporada                    |
| `partidos_jugados`         | `INTEGER`   | `COUNT(jp.idPartido)`               | Partidos en los que registró actuación |
| `total_puntos`             | `INTEGER`   | `SUM(puntos)`                       | Puntos totales acumulados              |
| `total_t2c`                | `INTEGER`   | `SUM(T2C)`                          | Tiros de 2 convertidos acumulados      |
| `total_t2l`                | `INTEGER`   | `SUM(T2L)`                          | Tiros de 2 lanzados acumulados         |
| `total_t3c`                | `INTEGER`   | `SUM(T3C)`                          | Tiros de 3 convertidos acumulados      |
| `total_t3l`                | `INTEGER`   | `SUM(T3L)`                          | Tiros de 3 lanzados acumulados         |
| `total_t1c`                | `INTEGER`   | `SUM(T1C)`                          | Tiros libres convertidos acumulados    |
| `total_t1l`                | `INTEGER`   | `SUM(T1L)`                          | Tiros libres lanzados acumulados       |
| `total_rebotes_def`        | `INTEGER`   | `SUM(rebotesDef)`                   | Rebotes defensivos acumulados          |
| `total_rebotes_of`         | `INTEGER`   | `SUM(rebotesOf)`                    | Rebotes ofensivos acumulados           |
| `total_rebotes`            | `INTEGER`   | `SUM(rebotesDef + rebotesOf)`       | Total de rebotes (def + of)            |
| `total_asistencias`        | `INTEGER`   | `SUM(asistencias)`                  | Asistencias acumuladas                 |
| `total_recuperos`          | `INTEGER`   | `SUM(recuperos)`                    | Recuperos acumulados                   |
| `total_perdidas`           | `INTEGER`   | `SUM(perdidas)`                     | Pérdidas acumuladas                    |
| `total_tapones_realizados` | `INTEGER`   | `SUM(taponesRealizados)`            | Tapones realizados acumulados          |
| `total_tapones_recibidos`  | `INTEGER`   | `SUM(taponesRecibidos)`             | Tapones recibidos acumulados           |
| `total_faltas_cometidas`   | `INTEGER`   | `SUM(faltasCometidas)`              | Faltas cometidas acumuladas            |
| `total_faltas_recibidas`   | `INTEGER`   | `SUM(faltasRecibidas)`              | Faltas recibidas acumuladas            |
| `porcentaje_t2`            | `REAL`      | `CASE WHEN SUM(T2L) > 0 … ELSE 0.0` | % efectividad tiros de 2               |
| `porcentaje_t3`            | `REAL`      | `CASE WHEN SUM(T3L) > 0 … ELSE 0.0` | % efectividad tiros de 3               |
| `porcentaje_t1`            | `REAL`      | `CASE WHEN SUM(T1L) > 0 … ELSE 0.0` | % efectividad tiros libres             |

---

### 3.4 `v_listas_detalle`

#### Descripción funcional

Recorre la cadena completa de habilitación: inscripción → lista de buena fe → jugadores de esa lista. Permite verificar qué jugadores están habilitados para competir en una inscripción específica. Cada fila representa **un jugador habilitado en una inscripción a una competencia**.

#### Tablas involucradas

```
inscripcion
  → club              (INNER JOIN por idClub)
  → categoria         (INNER JOIN por idCategoria)
  → competencia       (INNER JOIN por idCompetencia)
  → listaBuenaFe      (INNER JOIN por idInscripcion)
      → jugadorListaBuenaFe  (INNER JOIN por idListaBuenaFe)
          → jugador          (INNER JOIN por idJugador)
```

#### Columnas expuestas

| Columna              | Tipo SQLite | Origen / Cálculo                | Descripción                                         |
| -------------------- | ----------- | ------------------------------- | --------------------------------------------------- |
| `id_inscripcion`     | `INTEGER`   | `inscripcion.idInscripcion`     | Clave de la inscripción; usar como filtro principal |
| `nombre_club`        | `TEXT`      | `club.nombre`                   | Nombre del club inscripto                           |
| `nombre_categoria`   | `TEXT`      | `categoria.nombre`              | Categoría de la inscripción (ej. "U21")             |
| `nombre_competencia` | `TEXT`      | `competencia.nombre`            | Nombre de la competencia                            |
| `nombre_jugador`     | `TEXT`      | `nombre \|\| ' ' \|\| apellido` | Nombre completo del jugador habilitado              |

---

## 4. Ciclo de vida de las vistas y limitaciones conocidas

### Las vistas se recrean en cada arranque

`views.sql` empieza con `DROP VIEW IF EXISTS` para las cuatro vistas y luego las crea de nuevo. Como el esquema y las vistas se ejecutan **cada vez que arranca la aplicación** (hoy la CLI, desde la US-105 la GUI),
las vistas siempre quedan con su definición más reciente sin necesidad de migraciones. Esto es seguro porque una vista **no guarda datos** (solo una consulta).
Con las **tablas** es al revés: `schema.sql` **no** borra nada (solo `CREATE TABLE IF NOT EXISTS`), porque borrar una tabla borraría los datos del usuario.

### Limitaciones a tener en cuenta

- **`v_jugador_totales_temporada` agrupa por año, no por competencia** (`GROUP BY jugador, competencia.anio`). Si un club juega dos competencias distintas en el mismo año
  (ej. "Liga Provincial" y "Copa de Verano"), la vista **mezcla ambas en una sola fila**. Hay que corregirla (o reemplazarla por una agregación en Pandas) antes de construir filtros por competencia.
- **No existe ningún agregado a nivel club/equipo**: solo hay acumulados por jugador.
