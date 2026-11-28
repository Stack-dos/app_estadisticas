# ADR-003: Protocolo de Ingesta de archivos de Gesdeportiva (Excel y PDF)

- **Estado**: Pendiente — propuesta con archivos reales; falta elegir la librería de PDF
- **Fecha**: 2026-10-03 · **Actualizado**: 2026-10-31 (se revisaron archivos reales)

## Contexto

Las US-201 y US-206 (Hito 2) convierten archivos que exporta Gesdeportiva, el sistema de la CAB
(Confederación Argentina de Básquetbol), en datos persistibles sin transcripción manual. Hasta el
2026-10-31 este ADR era un borrador, porque no había ningún archivo real para fijar el mapeo.

El 2026-10-31 se revisaron archivos reales de un partido U13 del Asociativo 2026. En el repositorio
están en `data/`, pero tienen nombres reales de menores de edad, así que no se suben: los tests
usan copias anonimizadas.

Hay **dos tipos de archivo**, y cada uno viene en **dos formatos** (Excel y PDF) con el mismo
contenido:

| Archivo               | Para qué sirve                                   | Historia |
| --------------------- | ------------------------------------------------ | -------- |
| Planilla de partido   | Boxscore de los dos equipos de un partido        | US-201   |
| Listado de jugadores  | Lista de buena fe de un club en una competencia  | US-206   |

### Respuestas a las preguntas que dejaba abiertas el borrador

1. **¿El formato es siempre el mismo?** Con un solo partido y un solo listado no se puede
   confirmar que no cambie entre categorías o competencias. Lo que sí se ve es que el archivo
   tiene marcadores de texto fijos (`Nombre`, `TOTALES`, `Apellidos y Nombre`). Conviene buscar
   esos marcadores en vez de confiar en posiciones.
2. **¿Una hoja o varias?** Una sola hoja por archivo: `Estadísticas-` en la planilla de partido y
   `Jugadores-Equipo` en el listado.
3. **Casos borde encontrados:**
   - El título va en celdas combinadas y concentra los datos del contexto, separados por un guion entre espacios.
     En la planilla: `Estadísticas - LOCAL vs VISITANTE - CATEGORÍA - CIUDAD - COMPETENCIA -
     TEMPORADA - ORGANIZADOR - AÑO`. En el listado: `Jugadores - CLUB - CATEGORÍA - CIUDAD -
     COMPETENCIA - TEMPORADA - ORGANIZADOR - AÑO`.
   - Los encabezados no están en la primera fila, y en la planilla los dos equipos no están en
     filas fijas (el segundo bloque arranca en la fila 31, con una fila vacía antes del primer
     jugador).
   - **Todas las celdas son texto**, incluso los números. Los minutos vienen como `mm:ss`, los
     tiros como `convertidos/lanzados` en una celda (`1/8`), y los promedios del listado con coma
     decimal (`21,2`).
   - Hay nombres con espacios al final (`JUNCOS, FRANCISCO JOAQUÍN `).
   - Los dos archivos nombran distinto la misma categoría (`U13MX` en la planilla, `INFANTILES
     MIXTO` en el listado) y al organizador (`CABB` y `FEDERACION DE BASQUETBOL DE LA PROVINCIA
     DE CORDOBA`).
   - **Ninguno trae DNI, año de nacimiento, fecha del partido ni estadio.**
   - El PDF de la planilla marca titulares (`*`), capitán (`(CAP)`) y entrenador; el Excel no.

## Alternativas Consideradas

### Cómo mapear las columnas

- **Mapeo fijo en código, buscando los encabezados por texto:** el parser busca la fila que tiene
  `Nombre` (o `Apellidos y Nombre`) y toma cada columna por su título, no por su posición. Es
  simple y aguanta que los bloques se corran de fila.
- **Mapeo configurable (archivo externo):** el mapeo vive en un `.yaml` aparte. Sirve si hay varias
  fuentes o formatos que cambian seguido; acá hay una sola fuente (Gesdeportiva).
- **Detección por similitud de nombre (fuzzy matching):** más tolerante, pero menos predecible y
  más difícil de testear. Con títulos de columna fijos no hace falta.

### Cómo leer el PDF

- **`pdfplumber`:** extrae tablas con la posición de cada celda; Python puro, licencia MIT.
- **`pypdf`:** extrae texto, pero no la estructura de tabla: habría que separar las columnas a mano.
- **`camelot`:** bueno para tablas, pero necesita Ghostscript u OpenCV instalados, lo que complica
  el empaquetado (US-404).

## Decisión Tomada

**Propuesta, a confirmar entre los dos:**

- Mapeo fijo en código, buscando los encabezados por texto.
- `pdfplumber` para el PDF.
- `pandas` + `openpyxl` para el Excel (`pandas` ya es dependencia).
- Cada parser devuelve el mismo DTO para los dos formatos (`PlanillaPartidoDTO` o
  `ListadoJugadoresDTO`), así el resto de la ingesta no sabe de qué formato vino el archivo.
- Competencia, categoría y fecha no se toman del archivo: los nombres no coinciden entre archivos
  y la fecha no viene. Se eligen en la pantalla, con una sugerencia cuando el nombre coincide.

## Ventajas y Desventajas

- **Ventajas:**
  - No se agrega configuración que hoy no hace falta.
  - Los encabezados buscados por texto aguantan filas corridas.
  - El DTO común permite probar la ingesta sin archivos.
- **Desventajas:**
  - Si Gesdeportiva cambia los títulos de las columnas, hay que tocar código. Se mitiga con
    `FormatoArchivoInvalidoError`, que dice qué encabezado faltó.
  - `pdfplumber` suma una dependencia (más `pdfminer.six`).
  - Leer el PDF es más frágil que leer el Excel: si el PDF da problemas, se puede dejar solo el
    Excel sin tocar el resto.
