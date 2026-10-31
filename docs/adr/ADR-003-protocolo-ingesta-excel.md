# ADR-003: Protocolo de Ingesta de Excel (Ges Deportivo)

- **Estado**: Pendiente — borrador, falta un archivo de ejemplo real para cerrarlo
- **Fecha**: 2026-10-03

## Contexto

La US-201 (Hito 2) pide convertir planillas Excel exportadas desde Ges Deportivo en datos
persistibles, sin transcripción manual. Para poder mapear columnas del Excel a los campos
internos (`club`, `jugador`, `competencia`, `partido`, `jugadorPartido`) hace falta saber primero
cómo es ese export en la realidad: qué columnas tiene, si el orden/nombre es siempre igual, si
varía según el club o la competencia, si viene todo en una sola hoja o en varias.

**Nada de esto está confirmado todavía:** al momento de escribir este ADR no hay ningún archivo de
ejemplo de Ges Deportivo en el repositorio ni se inspeccionó ninguno — el Hito 2 todavía no
arrancó. Por eso este ADR queda como borrador: compara alternativas de **diseño** (cómo estructurar
el mapeo), pero no fija columnas ni nombres reales, para no inventar un contrato que después no
coincida con el archivo real.

## Alternativas Consideradas

- **Mapeo fijo en código:** un diccionario `{columna_excel: campo_interno}` hardcodeado dentro de
  `GesDeportivoExcelParser`. Simple, pero si Ges Deportivo cambia el formato de export (o si varía
  entre clubes/ligas), hay que tocar código y redeployar.
- **Mapeo configurable (archivo externo):** el mapeo vive en un `.yaml`/`.json` versionado aparte
  del código (ej. `config/ges_deportivo_mapping.yaml`), que el parser lee al arrancar. Permite
  ajustar el mapeo sin tocar Python, a costa de una capa extra de configuración.
- **Detección automática por similitud de nombre (fuzzy matching):** el parser intenta
  emparejar columnas por parecido de texto en vez de un mapeo exacto. Más tolerante a pequeñas
  variaciones, pero menos predecible y más difícil de testear con casos borde.

## Decisión Tomada

**Todavía no se toma.** Ver la pregunta abierta más abajo — se necesita un archivo real de Ges
Deportivo antes de poder elegir entre las alternativas con fundamento, en vez de adivinar.

## Pregunta abierta (a resolver entre nosotros antes de cerrar este ADR)

> Nico mencionó que puede conseguir un archivo de ejemplo real exportado de Ges Deportivo.
> **Falta conseguirlo y revisarlo juntos** para responder, con datos reales en mano:
>
> 1. ¿El formato de columnas es siempre el mismo, sin importar el club o la competencia, o varía?
> 2. ¿Viene todo en una sola hoja del Excel, o hay datos repartidos en varias hojas (ej. una hoja
>    de jugadores y otra de partidos)?
> 3. ¿Hay algún caso borde ya conocido de antemano (filas vacías, encabezados en una fila distinta
>    a la primera, columnas que a veces no vienen)?
>
> Con esas respuestas se elige una de las tres alternativas de arriba (lo más probable, a juzgar
> por el resto del proyecto, es la opción de **mapeo configurable**: es la que más se parece al
> espíritu del loader de configuración ya adoptado en la US-105 — pero se confirma recién cuando
> se vea el archivo real) y se completan las secciones de Ventajas/Desventajas.

## Ventajas y Desventajas

_Pendiente — depende de la decisión final, ver la pregunta abierta arriba._
