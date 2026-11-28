# Informe de sesión — US-113: carga de partido centrada en el club propio y pantallas (2026-11-27)

Rama: `feature/epica2`. Nueva US-113 del PRD; revisa la decisión 1 y el AC5 de la US-108. ADR-010.

## Por qué

Al probar la app con la planilla real de una temporada: el rival no se podía escribir, había que
crearlo en "Mis clubes" como club propio, se le exigía inscripción y lista, y el formulario de
varios pasos era angosto. Del rival el entrenador casi siempre tiene solo los totales.

## Decisiones (de Nico)

- **D1 = C:** del rival, totales (o solo el resultado) o su boxscore; con boxscore, sus jugadores
  van a la base y se les crea inscripción y lista en la misma transacción (**1A**).
- **D2 = A:** el rival es un club sin usuario, escribible con autocompletar; "Mis clubes" solo
  muestra los propios.
- **D3:** campo Rival + Local/Visitante.
- **D4 = A-A:** ancho completo y una sola pantalla de carga tipo Excel.
- **2A:** tabla `estadisticaEquipoPartido` + vista `v_totales_equipo_partido`.
- **T2C/T2L** como en la planilla.
- **Alta masiva** en la lista de buena fe: no "todo o nada".
- Resto de las pantallas (Jugadores, Competencias, Inicio) con las recomendaciones propuestas.

## Qué cambió

- **Base:** tabla `estadisticaEquipoPartido`; vistas `v_totales_equipo_partido`, `v_lideres_club`, y
  `v_partidos_resumen` con los puntos de cada equipo.
- **Dominio:** `EstadisticaEquipo`, `AltaPlantelRival`, `JugadorRivalNuevo`, `TotalesEquipoFila`,
  `LiderClub`; `save_with_boxscore` con `totales` y `alta_rival`.
- **Aplicación:** `CargarPartidoUseCase` rehecho; nuevos `ObtenerTotalesPartidoUseCase`,
  `ListarLideresClubUseCase` y `AgregarJugadoresAListaBuenaFeUseCase`.
- **GUI:** `planilla_boxscore.py`; carga de partido en una pantalla; Partidos con resultado y totales;
  Inicio con tablero; Jugadores con diálogos e íconos; Listas con casillas; Competencias con las
  categorías por fila y la pestaña nueva Categorías; `crear_pagina` sin ancho máximo.
- **Datos reales:** "Pesca" estaba vinculado al usuario porque se creó en "Mis clubes". Se borró solo
  esa fila de `usuarioClub` en `~/.statspro/estadisticas.db` (con copia de respaldo antes); el club
  sigue existiendo y ahora aparece como rival.
- **Docs:** PRD (sección 6, Hito 1, US-108, US-113, ADR), ADR-010, `03-casos-de-uso.md` (3.19 y
  estado en la GUI), RUNBOOK (qué se puede hacer y qué no), guía de Flet (sección 18).

## Cómo se verificó

- Suite completa, benchmarks, `ruff check`, `ruff format --check` y `mypy --strict`, en una copia del
  repo (nunca sobre la base ni el `.venv` reales).
- Un recorrido de entrenador sobre las pantallas reales (`_main` + `construir_dependencias` con una
  base nueva y una `page` falsa): registro → club → 4 jugadores → categoría y competencia →
  inscripción → lista masiva → partido con totales del rival nuevo → partido de visitante con
  boxscore del rival → tercer partido que reconoce a los jugadores del rival → errores → detalle e
  inicio. **No es un click real en la ventana**: la ventana no se abrió.

## Encontrado en el recorrido (pendiente)

- **Empates:** se guardó un partido 2 - 2. En básquet no hay empates.
- **El error se ve dos veces** (en la planilla y al lado de Guardar).
- **Crear el rival no es atómico con el partido:** si el guardado falla después, el club queda.
- **No hay aviso de partido repetido** (misma fecha y mismo rival).
- **Partidos entre dos clubes ajenos:** ya no se pueden cargar desde la pantalla (decisión pendiente).
- **Antes del primer partido hay cuatro pantallas** (Categorías → Competencias → Inscripciones →
  Listas).
