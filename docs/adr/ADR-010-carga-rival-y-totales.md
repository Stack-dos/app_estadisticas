# ADR-010: Cómo se carga y se guarda el rival de un partido

- **Estado**: Aprobado (ya implementado en la US-113)
- **Fecha**: 2026-11-27

## Contexto

La US-108 cargaba un partido con el boxscore completo de **los dos** equipos, y cada uno tenía que
estar inscripto en la competencia, con su lista de buena fe. Al probarla con la planilla real de una
temporada aparecieron tres problemas:

- Un entrenador tiene el boxscore de su equipo, pero del rival casi siempre solo tiene los totales
  (la fila "Equipo Rival" de su Excel) o directamente el resultado.
- Para cargar un rival había que crearlo en "Mis clubes", como si fuera un club propio, y armarle
  una inscripción y una lista de buena fe que el entrenador no conoce.
- El resultado del partido no estaba guardado en ningún lado: salía de sumar el boxscore, y sin el
  boxscore del rival no hay resultado.

Hay que decidir qué se carga del rival y dónde se guarda.

## Alternativas Consideradas

1. **Exigir el boxscore del rival (como en la US-108).** Simple, una sola fuente de datos. Pero
   obliga a inventar jugadores o a no cargar el partido, que es lo peor para las estadísticas.
2. **Del rival, solo totales, en columnas nuevas de `partido`** (`puntosLocal`, `t2cLocal`,...,
   `puntosVisitante`...). Una tabla, pero con ~30 columnas duplicadas y dos fuentes que se pueden
   contradecir cuando sí hay boxscore.
3. **Totales o boxscore, a elección (elegida).** Del rival se cargan sus totales **o**, si se tiene
   la planilla, su boxscore por jugador. Los totales van en una tabla aparte, una fila por equipo y
   partido; el boxscore, en `jugadorPartido` como siempre.

Para el boxscore del rival se consideró también **validarlo contra su lista de buena fe** (como al
club propio), pero el entrenador no la tiene: se descartó a favor de crearla sola.

## Decisión Tomada

- **Tabla `estadisticaEquipoPartido`** `(idPartido, idClub, puntos, t2c ... faltasCometidas)`, con
  clave primaria `(idPartido, idClub)`, borrado en cascada desde `partido` y las mismas reglas de la
  sección 6 del PRD (no negativos, convertidos ≤ lanzados). Si se cargan tiros, los puntos tienen que
  cerrar; si no, alcanza con los puntos.
- **Vista `v_totales_equipo_partido`**: une la suma del boxscore (`origen = 'boxscore'`) con los
  totales cargados (`origen = 'totales'`) para los equipos que no tienen boxscore. Todo lo que muestra
  un resultado (listado de partidos, detalle, inicio) lee de ahí, así hay **una sola** forma de
  obtener los puntos de un equipo y no puede haber dos números distintos.
- **Boxscore del rival con alta automática:** en la **misma transacción** que el partido se crean la
  inscripción y la lista del rival si no tenía, los jugadores nuevos (reconocidos por nombre y
  apellido normalizados dentro de su plantel vigente) con su vínculo al club desde la fecha del
  partido, y se habilitan en la lista los que faltaban. Si algo falla, no queda nada.
- **El club rival no se vincula al usuario** (`usuarioClub`): no aparece en "Mis clubes".
- La regla de la lista de buena fe sigue valiendo **solo para el club propio**.

## Ventajas y Desventajas

**Ventajas**

- Se puede cargar cualquier partido real, con la información que el entrenador tenga.
- Los datos del rival que sí se cargan (sus jugadores) quedan en la base para el scouting de la
  US-205, sin tener que armarle nada a mano.
- El resultado tiene una sola fuente (la vista): no hay columnas que mantener sincronizadas.

**Desventajas**

- Los totales del rival no tienen minutos ni datos por jugador: algunas métricas avanzadas
  (US-205) no se pueden calcular para esos partidos.
- Reconocer jugadores por nombre puede fallar con homónimos o nombres mal escritos ("Ramon" y
  "Ramón" se reconocen; "Ramón Perez" y "Ramón Pérez Gil", no).
- Crear el club rival (si se escribió uno nuevo) pasa **antes** de la transacción del partido: si el
  guardado falla, el club queda creado, vacío y sin usuario.
