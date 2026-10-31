# ADR-008: Estrategia de Backup y Restauración

- **Estado**: Aprobado
- **Fecha**: 2026-10-03

## Contexto

La US-402 (Hito 4, Épica H4-E2) pide proteger la continuidad operativa con exportación/importación
completa de la base, verificación de integridad post-restore, y un botón de
"Sincronización/Backup" en la futura GUI. Como toda la base vive en un único archivo SQLite, la
pregunta de fondo es cómo generar esa copia de forma segura (sin corromper datos si el archivo
está en uso) y cómo verificar después que la restauración fue completa.

**Nota sobre una contradicción que tenía el plan:** el documento fuente (LaTeX) decía que este
ADR bloqueaba el Hito 3, la tabla de ADRs decía Hito 4. Todo el contenido real de backup (US-402,
Épica H4-E2) vive en el Hito 4 — no hay ninguna tarea de backup en el Hito 3. Se resuelve la
contradicción a favor de **Hito 4**.

## Alternativas Consideradas

- **Copia directa del archivo `.db` (file copy):** simple, pero riesgosa si hay una escritura en
  curso en el momento de copiar — puede copiar un archivo a mitad de una transacción.
- **`VACUUM INTO` / API de backup online de SQLite:** SQLite expone un mecanismo pensado
  específicamente para generar una copia consistente de la base mientras está en uso (sin
  necesidad de que nadie la tenga cerrada), evitando el riesgo de la copia directa.
- **Backup automático programado** (ej. al cerrar la app, o cada N días), además del manual: más
  cobertura ante el olvido del usuario, pero agrega un componente nuevo (programación de tareas)
  que no pide el AC de la US-402 y que no se decide todavía.

## Decisión Tomada

Exportación **manual**, a iniciativa del usuario (comando CLI / botón en la GUI, como ya describe
la US-402), usando el mecanismo de copia segura de SQLite (`VACUUM INTO` o la API de backup
online, a elegir en el momento de implementar `backup_service.py` — ambas evitan el riesgo de
copiar un archivo a mitad de escritura) en vez de una copia directa del archivo. Cada backup
incluye metadata (versión de schema, fecha/hora, hash de integridad), tal como ya pide el AC1 de
la US-402. **No se contempla backup automático programado por ahora** — queda como posible mejora
futura, fuera del alcance de esta ADR y de la US-402 tal como está definida hoy.

## Ventajas y Desventajas

### Ventajas

- `VACUUM INTO`/backup online evita copiar un archivo a mitad de una transacción — más seguro que
  una copia de archivo directa, sin agregar ninguna dependencia nueva (es parte de SQLite).
- El usuario tiene control explícito de cuándo hacer un backup, sin sorpresas de un proceso
  corriendo en segundo plano.
- Metadata (versión de schema + hash) permite detectar si un backup es compatible con la versión
  actual del código antes de intentar restaurarlo.

### Desventajas

- Al ser manual, depende de que el usuario se acuerde de hacerlo — no hay red de seguridad si
  nunca lo ejecuta. Es un riesgo aceptado por ahora (ver alternativa de backup automático,
  descartada por ahora, no eliminada para siempre).
- La restauración sobre una instancia con datos existentes (AC2) implica decidir qué pasa con los
  datos actuales antes de sobreescribirlos — el AC no especifica si se pide confirmación
  explícita al usuario; vale la pena tenerlo en cuenta al implementar la US-402 (no es una
  pregunta que haga falta resolver en este ADR, es un detalle de UX de esa US).
