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

## Pendiente / para mirar

- **Avisos antes que errores:** "¿Guardar igual?" aparece antes de que el caso de uso valide. Con un
  empate, el entrenador primero confirma el aviso y recién después ve que no se puede guardar.
  Mejora posible: validar primero (sin guardar) y avisar después.
- **El aviso de partido repetido compara nombres** (competencia, categoría y rival), porque
  `PartidoResumenDTO` no trae ids.
- **Verificar en la ventana real:**
  - el botón Guía abajo del menú;
  - las casillas de convocados con 15 o más jugadores;
  - cómo se ve el Markdown.
