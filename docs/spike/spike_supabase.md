# Spike: Sincronización Local-First con Supabase

| Campo           | Valor                                                                   |
| --------------- | ----------------------------------------------------------------------- |
| Estado          | Propuesto (no iniciado)                                                 |
| Fecha           | 2026-10-17                                                              |
| Rama sugerida   | `spike/sync-supabase`                                                   |
| Timebox         | 2–3 días de trabajo. Si se pasa, se corta y se documenta lo aprendido. |
| Relacionado con | ADR-001 (Local-First), NFR-6 (Offline), Hito 5 del roadmap (sección 16) |
| Entregable      | Este documento completado + borrador de `docs/adr/ADR-010-sincronizacion-cloud.md` |

---

## 1. Contexto y motivación

Hoy la app es **100% local**: una base SQLite (`estadisticas.db`) por instalación. Eso cumple el
NFR-6 (offline), pero cada dispositivo es una isla: si el DT carga un partido en el celular en la
cancha, no lo ve después en la PC de su casa — y el plan (sección 2) dice que _"la mayoría analiza
las estadísticas de forma diferida en sus casas"_.

El Hito 5 del roadmap ya prevé una _"sincronización cloud híbrida, manteniendo la app 100%
funcional offline"_. Este spike adelanta **la investigación técnica** (no la implementación) para
responder si es viable con Supabase y cuánto cuesta en diseño de datos.

**Por qué no "migrar a Supabase" directo:** si la app leyera y escribiera directamente contra la
nube, sin red no funcionaría — rompe ADR-001 y NFR-6, que son bloqueantes. Por eso el enfoque es
**local-first**: SQLite sigue siendo la fuente de verdad del dispositivo y Supabase es solo el
punto de encuentro entre dispositivos.

## 2. Pregunta que el spike tiene que responder

> **¿Puedo sincronizar `partido` + `jugadorPartido` entre dos bases SQLite, pasando por
> Supabase, con uno de los dispositivos cargando datos sin conexión, sin perder ni duplicar
> datos?**

Preguntas secundarias:

1. ¿Cuánto cambia el esquema actual (IDs, timestamps, borrados)?
2. ¿Qué tan complejo es el código de sync en Python (sin SDK oficial para Flet)?
3. ¿Cómo se comportan los conflictos (mismo registro editado en dos dispositivos)?
4. ¿Cuánto espacio ocupa realmente en Postgres? ¿Alcanza el plan gratis?
5. ¿Cómo encaja en la arquitectura hexagonal (puerto/adaptador)?

**Fuera de alcance del spike:** autenticación con Supabase Auth, Row Level Security completa,
UI, cobro/suscripciones, sincronizar todas las tablas. Si el spike sale bien, eso va en el plan
real del Hito 5.

## 3. Cómo funciona la sincronización local-first

```
 Celular (SQLite local)                                   PC (SQLite local)
 ┌────────────────────┐                                   ┌────────────────────┐
 │ la app lee/escribe │                                   │ la app lee/escribe │
 │ SIEMPRE acá        │                                   │ SIEMPRE acá        │
 │                    │   push (cuando hay red)           │                    │
 │ tabla outbox ──────┼──────────►  ┌──────────┐  ◄───────┼── tabla outbox     │
 │                    │             │ Supabase │          │                    │
 │ pull ◄─────────────┼──────────── │ Postgres │ ─────────┼──► pull            │
 └────────────────────┘             └──────────┘          └────────────────────┘
```

1. **Escritura local:** cada alta/modificación/baja se guarda en SQLite y, en la misma
   transacción, se agrega una fila a la tabla `outbox` ("cambios pendientes de subir").
2. **Push:** cuando hay conexión, se suben las filas pendientes del `outbox` a Supabase (upsert)
   y se marcan como enviadas.
3. **Pull:** se piden a Supabase los registros con `updated_at` mayor al último pull exitoso
   (guardado en una tabla `sync_estado`) y se aplican localmente.
4. **Conflictos:** _last-write-wins_ por `updated_at`. En este dominio un partido lo carga una
   sola persona, así que los conflictos reales deberían ser rarísimos.

### Cambios de esquema que exige

| Cambio | Por qué | Costo si se hace tarde |
| ------ | ------- | ---------------------- |
| **PK UUID** (texto) en vez de `INTEGER AUTOINCREMENT` | Dos dispositivos offline generarían el mismo `idPartido = 5` | **Alto**: hay que reescribir todas las FKs con datos reales de usuarios |
| Columna `updated_at` (ISO-8601 UTC) | Saber qué cambió desde el último pull y resolver conflictos | Medio |
| Borrado lógico `deleted_at` | Un `DELETE` físico no se puede sincronizar (no queda nada que subir) | Medio |
| Tablas `outbox` y `sync_estado` | Cola de cambios pendientes y marca del último pull | Bajo (son nuevas) |

> `jugadorPartido` ya tiene PK compuesta `(idJugador, idPartido)`: si esas dos son UUID, la PK
> compuesta sirve tal cual.

## 4. Preparación del entorno

> ⚠️ **Nunca usar `estadisticas.db` ni el `.venv` real del proyecto** (Windows y WSL comparten la
> carpeta). El spike trabaja con bases propias en `spike/datos/` y con dependencias aisladas.

### 4.1 Rama y carpeta

```bash
git checkout main && git pull
git checkout -b spike/sync-supabase
mkdir -p spike/datos
echo "spike/datos/" >> .gitignore
echo "spike/.env" >> .gitignore
```

El código del spike vive en `spike/` (en la raíz, **fuera de `src/`**): es descartable y no debe
mezclarse con el código de producción ni entrar en la cobertura.

### 4.2 Proyecto en Supabase

1. Crear cuenta en <https://supabase.com> y un proyecto nuevo (plan Free, región más cercana,
   p. ej. `sa-east-1` São Paulo).
2. Guardar la contraseña de la base que pide al crearlo.
3. En **Project Settings → Database → Connection string**, copiar la URI del **Session pooler**
   (funciona con IPv4, la conexión directa puede requerir IPv6).
4. Crear `spike/.env` (ignorado por git):

   ```env
   SUPABASE_DB_URL=postgresql://postgres.<ref>:<password>@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
   ```

### 4.3 Dependencias

Usar `psycopg` (SQL puro, como hoy con SQLite) en vez del cliente `supabase-py`, para que el
adaptador se parezca a los repositorios actuales y sea portable a cualquier Postgres (incluido
el FastAPI + Postgres que menciona el Hito 5).

```bash
uv add --group spike "psycopg[binary]" python-dotenv
```

> Si se prefiere no tocar `pyproject.toml` en el spike: `uv run --with "psycopg[binary]" --with python-dotenv python spike/...`.

## 5. Paso a paso

### Paso 1 — Esquema remoto (Supabase)

En **SQL Editor** de Supabase, ejecutar `spike/sql/remoto.sql`:

```sql
CREATE TABLE partido (
    id_partido        uuid PRIMARY KEY,
    fecha             date NOT NULL,
    estadio           text,
    id_club_local     uuid NOT NULL,
    id_club_visitante uuid NOT NULL,
    updated_at        timestamptz NOT NULL,
    deleted_at        timestamptz,
    CHECK (id_club_local <> id_club_visitante)
);

CREATE TABLE jugador_partido (
    id_jugador      uuid NOT NULL,
    id_partido      uuid NOT NULL REFERENCES partido (id_partido),
    id_club         uuid NOT NULL,
    minutos_jugados real NOT NULL DEFAULT 0,
    puntos          integer NOT NULL DEFAULT 0 CHECK (puntos >= 0),
    t2c integer NOT NULL DEFAULT 0, t2l integer NOT NULL DEFAULT 0,
    t3c integer NOT NULL DEFAULT 0, t3l integer NOT NULL DEFAULT 0,
    t1c integer NOT NULL DEFAULT 0, t1l integer NOT NULL DEFAULT 0,
    rebotes_def integer NOT NULL DEFAULT 0, rebotes_of integer NOT NULL DEFAULT 0,
    asistencias integer NOT NULL DEFAULT 0,
    updated_at      timestamptz NOT NULL,
    deleted_at      timestamptz,
    PRIMARY KEY (id_jugador, id_partido)
);

CREATE INDEX ix_partido_updated ON partido (updated_at);
CREATE INDEX ix_jp_updated ON jugador_partido (updated_at);
```

Se simplifica a propósito: sin FKs a `club`/`competencia`/`jugador` y con solo algunas métricas.
Alcanza para probar el mecanismo; el esquema completo es trabajo del Hito 5.

> **Nota de dialecto:** Postgres pasa a minúsculas los identificadores sin comillas
> (`idPartido` → `idpartido`). Por eso el remoto usa `snake_case`; el mapeo camelCase ↔
> snake_case es parte de lo que el spike tiene que medir.

### Paso 2 — Esquema local (SQLite)

`spike/sql/local.sql`: las mismas dos tablas en SQLite (`STRICT`, PK `text` con UUID,
`updated_at text`, `deleted_at text NULL`) más las de sincronización:

```sql
CREATE TABLE outbox (
    id          integer PRIMARY KEY AUTOINCREMENT,  -- local, nunca se sincroniza
    tabla       text NOT NULL,                      -- 'partido' | 'jugador_partido'
    pk          text NOT NULL,                      -- JSON con la PK del registro
    creado_en   text NOT NULL,
    enviado_en  text NULL
) STRICT;

CREATE TABLE sync_estado (
    clave text PRIMARY KEY,   -- 'ultimo_pull'
    valor text NOT NULL
) STRICT;
```

El `outbox` guarda **qué** cambió, no el contenido: al hacer push se lee la fila actual de la
tabla, así varias ediciones seguidas del mismo partido se suben una sola vez.

### Paso 3 — Escritura local con outbox

`spike/local.py`: funciones `crear_partido(...)`, `cargar_estadistica(...)`,
`borrar_partido(...)` que:

1. Generan `uuid.uuid4()` como PK.
2. Setean `updated_at = datetime.now(UTC).isoformat()`.
3. En **una misma transacción** escriben la tabla y agregan la fila al `outbox` (mismo criterio
   que la carga atómica de US-106: o entra todo o nada).
4. `borrar_partido` hace `UPDATE ... SET deleted_at = ?, updated_at = ?`, nunca `DELETE`.

### Paso 4 — Push

`spike/sync.py → push(conn_local, conn_remota)`:

1. Leer `outbox WHERE enviado_en IS NULL` ordenado por `id`.
2. Para cada PK, leer la fila actual local y hacer en Postgres:

   ```sql
   INSERT INTO partido (...) VALUES (...)
   ON CONFLICT (id_partido) DO UPDATE SET ...
   WHERE partido.updated_at < EXCLUDED.updated_at;   -- last-write-wins
   ```

3. Subir `partido` antes que `jugador_partido` (por la FK remota).
4. Recién después del `COMMIT` remoto, marcar `enviado_en` en el outbox local. Si se corta la red
   en el medio, se reintenta: el upsert es **idempotente**.

### Paso 5 — Pull

`spike/sync.py → pull(conn_local, conn_remota)`:

1. Leer `ultimo_pull` de `sync_estado` (o `1970-01-01` la primera vez).
2. `SELECT * FROM partido WHERE updated_at > %s`, idem `jugador_partido`.
3. Aplicar localmente con `INSERT ... ON CONFLICT DO UPDATE ... WHERE excluded.updated_at > updated_at`
   (SQLite soporta upsert desde 3.24).
4. Guardar como nuevo `ultimo_pull` el **máximo `updated_at` recibido** (no la hora local, para
   no depender de relojes desincronizados entre dispositivo y servidor).

> **Orden recomendado:** primero `push`, después `pull`.

### Paso 6 — Script de escenarios

`spike/escenarios.py` crea `spike/datos/celu.db` y `spike/datos/pc.db` desde cero y ejecuta
los escenarios de la sección 6, imprimiendo ✅/❌ en cada uno. Para simular "sin conexión",
simplemente no se llama a `push`/`pull` (o se pasa una URL inválida para probar el manejo de error).

```bash
uv run python spike/escenarios.py
```

### Paso 7 — Medir espacio

Cargar datos sintéticos realistas (p. ej. 20 equipos × 30 partidos × 15 jugadores = 9.000 filas
de `jugador_partido`) y medir en Supabase:

```sql
SELECT pg_size_pretty(pg_total_relation_size('jugador_partido'));
SELECT pg_size_pretty(pg_database_size(current_database()));
```

Con eso se calcula KB por temporada-equipo y cuántas entran en el plan Free (500 MB).

### Paso 8 — Encaje en la arquitectura

Sin implementarlo, bocetar en el ADR cómo quedaría en el proyecto real:

- **Puerto** en dominio/aplicación: `SincronizadorPort` con `sincronizar() -> ResultadoSync`.
- **Adaptador** en `src/infraestructura/sync/supabase_sincronizador.py`.
- El outbox se llena desde los repositorios SQLite existentes (o con triggers SQLite, alternativa
  a evaluar: menos código Python, pero lógica escondida en la base).
- El caso de uso no sabe que existe Supabase: si mañana se cambia por FastAPI + Postgres, solo
  cambia el adaptador.

## 6. Escenarios de prueba (criterios de éxito)

| # | Escenario | Resultado esperado |
| - | --------- | ------------------ |
| E1 | Celu crea partido + 10 estadísticas offline → push → PC hace pull | PC tiene el partido y las 10 filas, con los mismos UUID |
| E2 | Celu y PC crean partidos distintos offline → ambos sincronizan | Ambos tienen los 2 partidos, sin choque de IDs |
| E3 | Se corta la red a mitad del push (simular con excepción) → reintento | Sin duplicados ni pérdidas; outbox vacío al final |
| E4 | Mismo partido editado en celu (10:00) y en PC (10:05) → ambos sincronizan | Gana la edición de las 10:05 en los dos dispositivos |
| E5 | Celu borra un partido → sincroniza → PC hace pull | En PC queda con `deleted_at` y las consultas lo ocultan |
| E6 | Push/pull ejecutados dos veces seguidas sin cambios | No se modifica nada (idempotencia) |
| E7 | Sin red, la app sigue creando y consultando datos | Funciona igual (NFR-6), solo crece el outbox |

**El spike es exitoso si pasan E1–E7.** Si E3 o E4 no se pueden resolver de forma simple, es una
señal fuerte para evaluar PowerSync/ElectricSQL o postergar.

## 7. Alternativas a evaluar en el ADR

| Opción | A favor | En contra |
| ------ | ------- | --------- |
| **Sync propio + Supabase (este spike)** | Control total, Python puro, sin dependencias raras | Hay que escribir y testear la lógica de sync |
| **PowerSync** (integración oficial con Supabase) | Resuelve outbox, conflictos y reintentos | Sin SDK Python/Flet; obligaría a cambiar de stack de UI (contradice ADR-002) |
| **ElectricSQL** | Sync Postgres ↔ cliente | Orientado a JS/web; mismo problema que PowerSync |
| **FastAPI + Postgres propio** (lo que dice el Hito 5) | Sin dependencia de proveedor | Hay que operar un servidor; más trabajo que Supabase |
| **Exportar/importar archivo** (Drive, mail, etc.) | Trivial, ya existe base con ADR-008 | Manual, sin merge: pisa los datos del otro dispositivo |

## 8. Costos y plan gratis (a verificar en el spike)

Estimación previa: una fila de `jugadorPartido` ≈ 0,5 KB con índices → una temporada-equipo
(15 jugadores × 30 partidos) ≈ 225 KB → **500 MB ≈ 2.000 temporadas-equipo**. El espacio no
parece ser el límite si **no** se suben los Excel de Ges Deportivo (se procesan localmente).

Limitaciones del plan Free que sí importan para producción:

- El proyecto **se pausa tras ~1 semana sin actividad**.
- Sin backups descargables; máximo 2 proyectos.
- No pensado para uso comercial → el plan Pro (≈ USD 25/mes, 8 GB) es el costo base a cubrir.

> Verificar precios y límites vigentes en <https://supabase.com/pricing> al momento del spike.

## 9. Riesgos conocidos

- **Migración de IDs a UUID:** es el cambio más invasivo y toca todo el Hito 1. Conviene decidirlo
  antes de tener usuarios reales, aunque la sync se implemente en el Hito 5.
- **Relojes desincronizados:** _last-write-wins_ depende de `updated_at`; un dispositivo con la
  hora mal puede "ganar" siempre. Mitigación posible: que el servidor estampe la hora en el push.
- **Seguridad:** sin RLS, cualquiera con la cadena de conexión ve todo. En el spike no importa
  (datos sintéticos); en producción la app **nunca** debe llevar la contraseña de la base — hace
  falta Supabase Auth + RLS o una API intermedia.
- **Datos personales de menores** (categorías formativas): subirlos a la nube exige consentimiento
  y revisar la Ley 25.326 de Protección de Datos Personales.
- **Estado del Hito 1:** la sección 20 del plan marca repositorios con bugs
  (`SqliteJuegoRepositorio` no funcional). El spike no debe desviar el foco de cerrar el Hito 1.

## 10. Modelo de negocio (contexto, no se valida en el spike)

La sync tiene costo recurrente, así que es candidata natural a ser la parte paga:

| Modelo | Idea | A favor | En contra |
| ------ | ---- | ------- | --------- |
| **Freemium local + sync paga** ⭐ | App completa gratis offline; sync, backup cloud y multi-dispositivo pagos | Usuarios gratis no generan costo de servidor; se cobra lo que cuesta | Hay que convencer de que la sync vale la pena |
| Suscripción por DT | ~USD 3–5/mes | Simple, recurrente | Alta sensibilidad al precio en formativas |
| Plan por club | El club paga por varios DTs/categorías | Ticket más alto; encaja con `usuarioClub` | Venta más lenta |
| Licencia única | Pago único por la app local | Sin costo recurrente para el usuario | No cubre servidores |
| B2B federaciones | Hito 8 | Contratos grandes | Muy lejano |

Notas: Google Play exige su facturación para suscripciones dentro de la app (~15%). A USD 4/mes,
unos 7–10 suscriptores cubren Supabase Pro. **El riesgo real es la disposición a pagar**:
validarlo con una pregunta en la próxima encuesta a DTs antes de programar el cobro.

## 11. Entregables al cerrar el spike

- [ ] Código en `spike/` (rama `spike/sync-supabase`, **no se mergea a `main`**).
- [ ] Tabla de la sección 6 completada con ✅/❌ y observaciones.
- [ ] Números reales de espacio (Paso 7).
- [ ] Borrador de `docs/adr/ADR-010-sincronizacion-cloud.md` con la plantilla canónica
      (Contexto → Alternativas → Decisión → Ventajas y Desventajas).
- [ ] Decisión explícita sobre **UUIDs en el esquema actual** (adoptar ya o no).
- [ ] Actualizar el plan (`docs/plan_desarrollo_detallado.md`, secciones 8, 16 y 18) con el ADR-010.

## 12. Resultados

_(Completar al terminar el spike.)_

| Escenario | Resultado | Observaciones |
| --------- | --------- | ------------- |
| E1 | | |
| E2 | | |
| E3 | | |
| E4 | | |
| E5 | | |
| E6 | | |
| E7 | | |

**Espacio medido:** _…_

**Líneas de código del sync:** _…_

**Conclusión / recomendación:** _…_
