# ADR-002: Framework de UI (Flet)

- **Estado**: Aprobado
- **Fecha**: 2026-10-03

## Contexto

El proyecto arrancó como una CLI (US-103 y US-104) y el PRD pedía una interfaz gráfica para
Desktop y Mobile recién en el Hito 4 (US-401), incluyendo un APK de Android (US-404). Todo el resto del
proyecto — dominio, aplicación, infraestructura — está escrito en Python; cualquier framework de
UI que obligue a otro lenguaje implica mantener dos stacks y un puente entre ellos para invocar
los mismos casos de uso.

## Alternativas Consideradas

- **Flet:** framework de UI en Python puro (basado en Flutter por debajo), permite escribir
  pantallas de desktop y mobile desde el mismo lenguaje que el resto del proyecto.
- **Compose Multiplatform:** framework de JetBrains en Kotlin, también multiplataforma
  (desktop/Android/iOS), pero exige un lenguaje y un stack de build distintos a los de toda la
  capa de dominio/aplicación/infraestructura ya escrita en Python.

## Decisión Tomada

Se confirma **Flet**.

### Actualización (2026-10-31): la GUI se adelanta al Hito 1 y la CLI se retira

Al terminar la US-104 se decidió no seguir construyendo la CLI. El usuario final es un DT, y las
próximas historias (carga de partido, consulta de estadísticas, dashboards) se iban a construir
primero en consola y después rehacer en Flet. La GUI pasa a ser la **única** interfaz desde la
**US-105** (desktop); mobile y empaquetado siguen en el Hito 4 (US-401 y US-404). La decisión de
framework no cambia: el adelanto solo hace que el riesgo de la última desventaja (rendimiento y
madurez de Flet) se valide antes, en la US-105, en vez de en la US-401.

## Ventajas y Desventajas

### Ventajas

- Mismo lenguaje (Python) en toda la aplicación: las pantallas de la GUI pueden llamar
  directamente a los casos de uso ya escritos (`src/aplicacion/casos_uso/`), sin un puente entre
  lenguajes ni duplicar lógica de negocio.
- Un solo stack de build y de dependencias (`pyproject.toml`/`uv`) para todo el proyecto.
- Soporta desktop y mobile (incluido Android) desde la misma base de código, que es justo lo que
  pide la US-401 y el empaquetado de la US-404.
- Curva de aprendizaje menor para el equipo: no hace falta aprender Kotlin ni un ecosistema de
  build nuevo (Gradle) solo para la interfaz.

### Desventajas

- Ecosistema más chico y más joven que Compose Multiplatform: menos componentes y temas
  prearmados, menos ejemplos y respuestas de la comunidad ante problemas puntuales.
- Al estar construido sobre Flutter por debajo, la madurez y el rendimiento en mobile dependen en
  parte de esa capa — menos control fino que con un framework nativo de Kotlin si en algún
  momento hiciera falta optimizar algo muy específico de la plataforma.
- No se hizo una prueba de carga/rendimiento real todavía de Flet (ej. tiempo de arranque, que
  el NFR-5 exige por debajo de 3 segundos) — se valida en la US-105 (AC1) para desktop y en la
  US-401 para mobile.
- La API de Flet cambió de forma incompatible entre la serie 0.x y la 1.0: hay que fijar la
  versión exacta en `pyproject.toml` y revisar las notas de cada actualización.
