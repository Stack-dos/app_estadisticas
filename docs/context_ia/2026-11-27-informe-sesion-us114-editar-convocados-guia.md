# Informe de sesión — US-114: editar partidos, convocados y guía de uso (2026-11-27)

Rama: `feature/epica2`. Nueva US-114 del PRD; cierra los tres pendientes de la US-113.

## Por qué

Al probar la US-113, Nico pidió un botón para editar un partido ya cargado y cargar solo a los
convocados (no toda la lista de buena fe). También pidió una "Guía" abajo a la izquierda que
explique la app de forma simple. La simulación del flujo de un entrenador había dejado además
seis recomendaciones.

## Decisiones (de Nico)

- **D1 = a:** se edita todo el partido, reusando la pantalla de carga llena con lo guardado. Se suma
  "Eliminar partido" con confirmación.
- **D2 = a y b:** máximo 12 jugadores por equipo, fijo y obligatorio. El mínimo (5) solo avisa.
- **D3 = a:** convocados con casillas; la planilla muestra solo a los marcados.
- **D4 = a:** pantalla `/guia` que muestra `src/assets/guia.md`, con el botón "Guía" abajo del
  menú y el link "¿Cómo se usa?" en el login.
- **Partidos de otros clubes:** quedan fuera, porque ya están planificados en la US-201 (importar
  planillas de cualquier club) y la US-207 (carga masiva).
- **Recomendaciones aplicadas:**
  - rechazar empates;
  - mostrar el error una sola vez;
  - crear el rival junto con el partido;
  - avisar si el partido ya existe;
  - "Agregar todo el plantel a la lista" al inscribirse;
  - sección "Clubes rivales".
  - El orden del último partido no hacía falta: el repositorio ya ordena por fecha e id.

## Qué cambió

- **Dominio:**
  - constantes `MAX_JUGADORES_PARTIDO`, `MIN_JUGADORES_PARTIDO` e `ID_CLUB_NUEVO`, y la excepción
    `ClubEnUsoError`;
  - en el repositorio de partidos: `save_with_boxscore` hace UPDATE si hay `idPartido` y recibe
    `club_rival_nuevo`; métodos nuevos `eliminar` y `cuartos_por_partido`;
  - en el repositorio de clubes: `listar_sin_usuario`, `actualizar`, `eliminar`, `tiene_partidos` y
    `tiene_usuarios`.
- **Aplicación:**
  - `CargarPartidoUseCase` valida el máximo de 12 y el empate, recibe `nombre_rival_nuevo` y edita
    cuando viene `idPartido`;
  - casos de uso nuevos: `ObtenerPartidoUseCase`, `EliminarPartidoUseCase`,
    `ListarClubesRivalesUseCase`, `RenombrarClubUseCase` y `EliminarClubUseCase`.
- **GUI:**
  - **Carga de partido:**
    - convocados con contador;
    - "¿Guardar igual?" con menos de 5 jugadores o un partido repetido;
    - el error de la planilla se ve una sola vez;
    - modo edición.
  - **Partidos:** "Editar" y "Eliminar" en el detalle.
  - **Inscripciones:** "Agregar todo el plantel a la lista".
  - **Mis clubes:** sección "Clubes rivales".
  - **Pantalla Guía:** botón abajo del menú y link en el login.
  - **Rutas:** `/partidos/editar/{id}` (con `separar_ruta`) y `/guia`.
- **Sin cambios de esquema.** La base real no se tocó en esta historia.
- **Docs:**
  - PRD (sección 6, Hito 1, US-113 y US-114 nueva);
  - `03-casos-de-uso.md` (3.19 y la nueva 3.20);
  - RUNBOOK (qué se puede hacer y qué no);
  - guía de Flet (sección 19);
  - el manual `src/assets/guia.md`.

## Cómo se verificó

- En una copia del repo, nunca sobre la base ni el `.venv` reales:
  - la suite completa y los benchmarks;
  - `ruff check`, `ruff format --check` y `mypy --strict`.
- **Simulación del flujo de un entrenador** sobre las pantallas reales, con una base nueva:
  1. guía sin sesión;
  2. registro y club;
  3. 14 jugadores;
  4. inscripción con todo el plantel;
  5. partido con convocados (el número 13 se rechaza) contra "Pezca";
  6. duplicado y empate;
  7. error de planilla;
  8. editar el partido;
  9. eliminar el otro;
  10. renombrar "Pezca" a "Pesca";
  11. intentar borrarlo (lo rechaza porque tiene partidos);
  12. guía con sesión.
- **No es un click real en la ventana**: no se miró la ubicación visual del botón Guía.

## Ajuste visual después de probar la ventana real

Nico probó la app y mandó capturas con tres problemas. Los tests no los veían.

- **Tablas angostas, mucho espacio vacío:** `crear_tabla_datos` ahora devuelve la `DataTable` con
  `expand=True` dentro de una `Row`, así ocupa todo el ancho. Vale para todas las pantallas.
- **Convocados en una columna larga:**
  - ahora van en un `ExpansionTile` (sección plegable) con el contador en el título;
  - las casillas están en una `ResponsiveRow`, de 2 a 6 por fila según el ancho;
  - la sección viene plegada si ya están todos marcados y abierta si hay que elegir.
- **Casilleros de cuartos con rótulos partidos:** ahora son una grilla con encabezados (Q1..Q4, PR) y
  casilleros sin rótulo de 56 px. En los tests se buscan por `key` (`clave_casillero_cuarto`).
- Guía de Flet: sección 20 nueva. RUNBOOK: la línea de convocados.
- **Verificación:** la suite, ruff, format y mypy. **No se sacó captura de la ventana:** el entorno
  no dejó abrirla ni capturar la pantalla. Falta mirarlo en la app.

## Ajuste con la maqueta (muestrario de la US-111)

Nico comparó la app con la maqueta y listó las diferencias. Todo se hizo en la misma US-114:

- **Mis clubes:**
  - círculo con las iniciales;
  - resumen «n categorías · n jugadores», con las categorías distintas de sus inscripciones y el plantel.
  - Vale también para los rivales.
- **Jugadores:**
  - buscador que filtra mientras se escribe;
  - selector «Del club» / «En todos los clubes». Este último es de consulta, con el club actual;
    `ListarJugadoresTodosUseCase` y `listar_con_club_actual` son nuevos.
  - Se quitó «Vincular jugador existente»: un jugador siempre se crea con club y la regla del dominio
    no deja traerlo de otro club.
  - Si al dar de alta aparece un homónimo **sin club**, se ofrece sumarlo, y en «En todos los clubes»
    se puede eliminar a quien quedó sin club. Era lo único que hacía el buscador viejo que seguía
    teniendo sentido.
- **Partidos:**
  - columnas Cat. y G/P;
  - el filtro de categoría ofrece todo el catálogo (antes solo las inscriptas);
  - «Ver» abre `/partidos/ver/{id}`: marcador, cuartos en tabla, totales y un boxscore por equipo.
- **Inscripciones:** «Jugadores en la lista» en vez de «Lista #n».
- **Carga de partido:**
  - asistente de tres pasos;
  - los avisos van en el resumen del paso 3 y reemplazan al diálogo «¿Guardar igual?».
- **Color** (Nico mandó una captura del detalle: «le falta algo, color capaz»):
  - encabezado de tablas con fondo `SECONDARY_CONTAINER` en toda la app;
  - tarjeta de marcador con el ganador en el color principal y «Victoria/Derrota»;
  - PTS y Total resaltados.
- **Docs:**
  - guía de Flet (sección 21);
  - RUNBOOK;
  - `03-casos-de-uso.md`;
  - PRD (AC9 de la US-114);
  - el manual `guia.md`.
- **Verificación:** en la copia pasaron la suite, los benchmarks, ruff, format y mypy. No se miró en la
  ventana real: el entorno no deja abrirla.

## Pendiente / para mirar

- **Avisos antes que errores:** _resuelto en parte con el asistente._ Los avisos ya no frenan con un
  diálogo: se ven en el resumen. El empate y el tope de 12 los sigue validando el caso de uso al tocar
  «Guardar», o sea en el paso 3 y no en el 2.
- **Conteos de a uno:** «Jugadores en la lista» y el resumen de cada club hacen una consulta por fila
  (marcado con `shortcut:`). Alcanza para un club; si crece, conviene un `COUNT` agrupado.
- **El aviso de partido repetido compara nombres** (competencia, categoría y rival), porque
  `PartidoResumenDTO` no trae ids.
- **Verificar en la ventana real:**
  - el botón Guía abajo del menú;
  - las casillas de convocados con 15 o más jugadores;
  - cómo se ve el Markdown.
