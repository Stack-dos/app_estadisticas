# ADR-005: Librería para Generación de Reportes PDF

- **Estado**: Aprobado
- **Fecha**: 2026-10-03

## Contexto

La US-302 (Hito 3) pide exportar un reporte formal de partido o temporada en PDF: encabezado con
nombres de clubes/fecha/metadata, y tablas de boxscore y métricas avanzadas con alineación
numérica y cabeceras claras — un documento mayormente tabular, no una pieza de diseño gráfico
elaborado. El entorno de desarrollo del proyecto es Windows, lo cual pesa en esta decisión: hay
librerías de generación de PDF que dependen de binarios de sistema que son conocidos por dar
problemas de instalación en Windows.

## Alternativas Consideradas

- **`reportlab`:** librería Python pura para generar PDF mediante una API programática
  (`platypus` para tablas, estilos y flujo de texto). Sin dependencias de sistema fuera de pip.
- **`weasyprint`:** renderiza HTML/CSS a PDF — da más libertad visual (maquetar con CSS, insertar
  logos e imágenes con estilos ricos) pero depende de librerías de sistema (Pango, Cairo, GDK-PixBuf)
  que en Windows requieren instalación aparte (GTK runtime) y son una fuente frecuente de
  problemas de instalación y de reproducibilidad entre máquinas de distintos desarrolladores.

## Decisión Tomada

**`reportlab`.** El reporte que pide la US-302 es fundamentalmente tabular (boxscore, métricas,
encabezado con metadata) — exactamente lo que `platypus` (el módulo de tablas de `reportlab`)
maneja de forma nativa. No se necesita la libertad de maquetado HTML/CSS de `weasyprint` para este
caso de uso, y se evita por completo el riesgo de instalación de sus dependencias de sistema en
Windows, que es el entorno real de desarrollo del equipo.

## Ventajas y Desventajas

### Ventajas

- Python puro: se instala con `pip`/`uv` igual que el resto de las dependencias del proyecto, sin
  binarios de sistema que configurar aparte.
- Mismo comportamiento garantizado en cualquier máquina del equipo y en el CI (Linux, Windows,
  Docker) — sin depender de qué versión de Pango/Cairo tenga instalada cada entorno.
- `platypus` (tablas, estilos de párrafo, flujo de página) cubre exactamente lo que pide el AC1
  de la US-302 sin necesitar nada adicional.

### Desventajas

- Maquetar layouts complejos (multi-columna, estilos muy visuales, elementos gráficos elaborados)
  es más verboso que con CSS — si en el futuro se pide un reporte con un diseño mucho más
  elaborado (branding fuerte, gráficos incrustados con estilos ricos), puede hacer falta
  reconsiderar esta decisión.
- No reutiliza conocimiento de HTML/CSS que el equipo ya tenga de otros contextos — la curva de
  `reportlab` es su propia API, distinta a maquetar una página web.
