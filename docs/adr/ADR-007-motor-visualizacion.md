# ADR-007: Motor de Generación de Gráficos

- **Estado**: Aprobado
- **Fecha**: 2026-10-03

## Contexto

La US-301 (Hito 3) pide un `ChartGenerator` que transforme DataFrames en figuras (tendencia de un
jugador, comparativas) con un requisito concreto de rendimiento: generar figuras en **menos de 2
segundos** para un dataset de referencia (3 temporadas, 20 equipos, 1200 filas de boxscore). El
consumo principal en ese momento es la CLI (figuras PNG mostradas o guardadas en disco, sin
servidor ni navegador); más adelante, en el Hito 4, la US-401 reutiliza ese mismo motor a través
de un `ChartComponent` para la GUI de Flet.

## Alternativas Consideradas

- **`matplotlib`:** genera figuras estáticas (PNG, SVG) de forma nativa y offline, sin ningún
  proceso ni dependencia adicional — es la librería de gráficos estándar del ecosistema
  Python/Pandas.
- **`plotly`:** genera gráficos interactivos (zoom, hover con tooltips) pensados principalmente
  para renderizarse en un navegador o servidor (Dash). Para exportar esos gráficos como imagen
  estática (lo que pide el AC2 de la US-301) necesita una dependencia extra y pesada,
  `kaleido`, que no hace falta para nada más en este proyecto.

## Decisión Tomada

**`matplotlib`.** El uso principal (CLI, figuras estáticas, sin navegador ni servidor) coincide
exactamente con lo que `matplotlib` hace nativamente, sin agregar una dependencia extra solo para
exportar a imagen. Si en el Hito 4 se quiere interactividad rica dentro de la GUI de Flet (zoom,
tooltips), es una decisión de la capa de UI a evaluar en su momento (ej. un componente de
gráficos interactivo propio de Flet) — no cambia el motor de generación de datos de este ADR, que
sigue sirviendo como base (`ChartGenerator` ya devuelve figuras a partir de DataFrames,
independientemente de cómo la GUI decida mostrarlas después).

## Ventajas y Desventajas

### Ventajas

- Sin dependencias adicionales más allá de lo que Pandas/el ecosistema científico de Python ya
  trae habitualmente.
- Genera PNG nativo, cumple el AC2 de rendimiento sin pasos intermedios de renderizado en
  navegador/servidor.
- Es la opción más simple y más probada para el caso de uso real: figuras estáticas consumidas
  desde una CLI offline.

### Desventajas

- No da interactividad nativa (zoom, hover) — si la GUI de Flet (Hito 4) termina necesitando eso
  de verdad, hay que resolverlo en esa capa aparte, no lo da este motor.
- Los gráficos por defecto de `matplotlib` requieren algo de ajuste de estilos para verse
  "profesionales" (tipografía, colores) — no es un problema técnico, pero sí un costo de pulido
  que no tendría una librería más orientada a dashboards modernos.
