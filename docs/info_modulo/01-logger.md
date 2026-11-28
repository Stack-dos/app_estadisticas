# Logger

***Que es un logger***
Un logger es una herramienta o librería que se encarga de registrar eventos, procesos y errores que ocurren mientras tu aplicación se está ejecutando
A diferencia de las simples funciones de impresión (como print o Console.log) mediante un logger se permite:

1. Clasificación por severidad (Niveles): Te permite categorizar qué tan grave o importante es el mensaje. No es lo mismo un error que tira abajo la base de datos, que un simple aviso de que el inicio de sesion de un usuario ha fallado. Hay distintos tipos de niveles de severidad, como DEBUG(para detalles de desarrollo), INFO(para funcionamkiento normal), WARNING(alertas), ERROR y CRITICAL(para ocurrencia de fallos graves).

2. Persistencia (Transportes): En lugar de solo mostrar el texto en la pantalla, el logger puede enviar esa información a distintos destinos simultáneamente: guardarlo en un ***archivo.log***, enviarlo a una base de datos externa, o mandar una alerta a un servicio de monitoreo.

3. Formateo estructurado: Convierte los mensajes de texto plano a formatos fáciles de leer por otras máquinas, como JSON, lo que facilita muchísimo la búsqueda y el filtrado cuando tenés miles de registros.

***configuracion Tipica de un logger***
cuando se trabaja en un entorno como Node.js, la configuracion tipica es la siguiente:

1. Levels(Niveles): Definís a partir de qué nivel querés registrar, por ejemplo en desarrollo de un software o programa, querés ver todo (nivel debug), pero en producción solo querés registrar errores graves (nivel error) para no llenar el disco con datos innecesarios.
La jetarquia de los niveles son:

- error: Fallos críticos.
- warn: Advertencias (algo raro pasó, pero la app sigue funcionando).
- info: Información general (ej. "Servidor iniciado en puerto 3000").
- debug: Datos muy detallados para rastrear bugs.

2. Transports (Transportes): Permite guardar esta información en archivos de texto, enviarla a una consola o transmitirla a servidores remotos para su posterior análisis o depuración. Podés configurar un transporte para que los errores (y solo los errores) vayan a un archivo llamado errores.log, y que toda la información general (info) salga por la consola

3. Format (Formato): Definís la estructura visual. Podés pedirle que al mensaje le agregue colores en la consola, o que lo empaquete en un JSON estricto

***¿Que datos relevantes tiene(o deberia tener) un registro log?***
Para garantizar la eficacia en la resolución de incidentes críticos y facilitar el proceso de depuración (debugging) del sistema, todo registro de log debe estructurarse con la siguiente información esencial:

- Timestamp (Marca de Tiempo): Elemento indispensable para establecer la cronología exacta de los eventos. Debe registrarse con precisión de milisegundos y, de forma estandarizada, utilizar el formato temporal UTC (Tiempo Universal Coordinado) para evitar discrepancias entre diferentes zonas horarias.

  Nivel de Severidad (Severity Level): Clasificación que indica la urgencia o gravedad del evento (ej. INFO, WARN, ERROR). Esto permite un triaje rápido, facilita el filtrado de registros y es vital para la configuración de alertas automatizadas.

- Mensaje Descriptivo: Declaración concisa y explícita que describe la naturaleza de la acción o el fallo ocurrido (por ejemplo: "Fallo de conexión a la base de datos principal").

***Contexto y Metadatos Extendidos***
Además de la información básica, es fundamental incluir datos contextuales que permitan reconstruir el estado del entorno al momento del suceso:

- Información de identificador de Trazabilidad (Trace ID / Transaction ID): Un código alfanumérico unívoco asignado a una petición específica. Permite auditar y seguir el ciclo de vida completo de dicha solicitud a través de los diferentes componentes y capas del sistema.

- Datos del Entorno y del Cliente: Parámetros que identifican el origen de la interacción. Esto incluye, entre otros, la dirección IP del cliente o el identificador único del usuario (User ID) si la acción se realizó bajo una sesión autenticada.

- Información de la Traza de la Pila (Stack Trace): En escenarios de excepciones o errores críticos, es imperativo adjuntar la traza completa de ejecución. Esto permite a los desarrolladores localizar con exactitud el archivo, método y línea de código donde se originó la falla estructural.

# Utilizacion de Logger en aplicacion App Estadistica

El proyecto implementa un sistema de registro de eventos (logging) estructurado y persistente, diseñado para auditar las operaciones del backend, monitorear el flujo de la aplicación y facilitar la depuración técnica.
Arquitectura y Configuración
1. Archivo logger.py (Configuración Central)
Este módulo centraliza la configuración del logger raíz de la aplicación, garantizando que cualquier componente del sistema herede parámetros estandarizados de registro.
A. Gestión de Directorios: Implementa la función crear_carpeta_logs(), la cual asegura la existencia del directorio de destino antes de inicializar los registros.
B. Rotación de Archivos: Para prevenir el agotamiento del espacio en almacenamiento, emplea la clase *RotatingFileHandler*. El sistema está configurado para archivar el registro actual (app.log) al alcanzar un tamaño máximo de 10 MB (maxBytes=10_000_000), manteniendo un historial máximo de 5 archivos de respaldo (backupCount=5) antes de eliminar los registros más antiguos.
C. Estructura de Metadatos: Se define un formato estricto mediante la clase *logging.Formatter*. Cada línea de registro captura: marca de tiempo exacta *(%(asctime)s)*, nombre del módulo emisor *(%(name)s)*, nivel de severidad *(%(levelname)s)* y el mensaje descriptivo del evento *(%(message)s)*.
D. Niveles de Severidad: El manejador de archivos (handler) restringe la escritura a eventos con nivel INFO o superior, filtrando el exceso de información en entornos de producción.
2. Archivo rutas.py (Definición de Ubicaciones)
Este módulo centraliza y abstrae la estructura de directorios del proyecto.Define las constantes *LOG_DIR* y *APP_LOG_FILE*, determinando que el historial de eventos se almacene físicamente en una carpeta denominada logs ubicada en la raíz del proyecto.
3. Archivo database_manager.py (Implementación)
Este módulo ilustra la aplicación del sistema de auditoría dentro de las operaciones transaccionales y de persistencia de datos.

- Identificación Dinámica: Instancia el registro utilizando *get_logger(__name__)*. Esta directiva asegura que cada entrada en el archivo de logs refleje automáticamente el nombre del archivo subyacente, facilitando la trazabilidad del código.

- Auditoría de Procesos Exitosos: Mediante el nivel INFO, el sistema documenta hitos críticos del ciclo de vida de la base de datos, tales como la inicialización de esquemas y vistas, la carga de datos iniciales o seeds, y la correcta ejecución de rutinas de limpieza.

- Manejo de Excepciones: Dentro de los bloques try/except, el módulo utiliza el nivel ERROR para capturar fallos operativos (por ejemplo, excepciones de tipo sqlite3.Error o archivos no localizados). El sistema registra la traza exacta de la excepción generada, garantizando que los detalles técnicos necesarios para la resolución del problema queden persistidos sin interrumpir abruptamente el flujo de la aplicación.

# Desde la US-110: JSON, correlation_id y secretos tapados

> Esta sección reemplaza los puntos **C** y **D** de arriba (el formato de texto y el nivel fijo) y la ubicación de `rutas.py`:
> los logs viven en `~/.statspro/logs/app.log` desde la US-109. La decisión está en el ADR-011.

**Concepto.** Un `correlation_id` (también _trace id_) es un identificador único que se le pone a **todos** los logs de una misma
operación. **Problema que resuelve:** en el archivo, las líneas de un clic se mezclan con las de otros; con el id se filtran las de uno
solo. **Ejemplo real:** es el `X-Request-ID` que agregan Nginx o Heroku a cada pedido HTTP; acá la "petición" es un clic.

**Cómo funciona.** Tres piezas en `src/infraestructura/observabilidad.py`:

1. **`ContextVar`** (módulo `contextvars` de la biblioteca estándar): una variable que parece global, pero cada hilo y cada tarea de
   asyncio ve su propio valor. `nueva_accion("clubes.crear")` guarda ahí un `ContextoAccion(correlation_id, accion)` y lo borra al
   salir del `with` (con `token = var.set(...)` / `var.reset(token)`, aunque haya excepción).
2. **Filtros del handler.** Un `logging.Filter` puede modificar el registro antes de escribirlo. `FiltroContexto` le copia
   `correlation_id` y `accion` de la `ContextVar`; `FiltroSecretos` tapa claves secretas (`password`, `hash`, `token`...) y emails en
   el mensaje, en los extras y en el traceback.
3. **`FormateadorJson`**: un `logging.Formatter` que devuelve `json.dumps(...)` con `ts` (UTC, milisegundos), `nivel`, `logger`,
   `mensaje`, `correlation_id`, `accion`, los campos de `extra=` y `exc` (el traceback).

```python
with nueva_accion("clubes.crear"):                      # lo hace ejecutar_mostrando_errores
    logger.info("Club creado", extra={"evento": "club_creado", "id_club": 7})
# -> {"ts": "...", "nivel": "INFO", ..., "correlation_id": "b92b...", "accion": "clubes.crear", "evento": "club_creado", "id_club": 7}
```

**Detalles técnicos.**

- **Los filtros van en el handler, no en el logger raíz.** Un filtro de logger solo ve lo que se loguea **en ese logger**; lo que llega
  propagado desde `aplicacion.casos_uso.crear_club` no pasa por él. Los filtros de un handler ven todo lo que el handler escribe.
- **La aplicación no importa nada de esto:** usa `logging.getLogger(__name__)`. El id lo pone el handler, al final del camino.
- **`extra=`** agrega campos al registro; el formatter los detecta comparando contra los atributos que todo `LogRecord` ya trae.
- **Sink y nivel:** `crear_handler(sink, nivel)` en `logger.py`, leído de `STATSPRO_LOG_SINK` y `STATSPRO_LOG_NIVEL` (ver el RUNBOOK).
- **En los tests**, pytest ya puso sus handlers en el logger raíz y `configuracion_log()` no agrega el suyo (el `if logger.handlers`).
  Para ver el `correlation_id`, la fixture `registros_log` de `tests/conftest.py` agrega un handler de lista con los filtros reales.

**Errores comunes.**

- Llamar a un módulo propio `logging.py`: tapa al de la biblioteca estándar en todos los `import logging`.
- Abrir una acción alrededor de `ft.run(...)`: las tareas de asyncio copian el contexto de quien las crea y **todos** los clics
  saldrían con el mismo id.
- Loguear con f-string un dato sensible sin clave (`logger.info(f"{password}")`): el filtro no sabe que es un secreto. El filtro es la
  red de seguridad, no un permiso para loguear secretos.
- Esperar el id en un `threading.Thread` creado a mano: arranca con el contexto vacío (usar `contextvars.copy_context().run`).
