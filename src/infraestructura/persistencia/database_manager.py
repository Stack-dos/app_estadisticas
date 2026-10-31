import sqlite3

import config.rutas as r
from infraestructura.logger import get_logger

logger = get_logger(__name__)


def abrir_conexion() -> sqlite3.Connection:
    """Abre la conexión a la base de datos real de la aplicación (``estadisticas.db``).

    Es el atajo que usan los comandos de la CLI para armar sus repositorios: evita repetir en cada
    comando la construcción de :class:`SQLiteManager` con las rutas del proyecto.

    Returns:
        sqlite3.Connection: conexión activa, con claves foráneas y ``row_factory`` ya configurados.
    """
    return SQLiteManager(r.DB_FILE, r.SCHEMA_SQL, r.VISTA_SQL).connect()


class SQLiteManager:
    """Gestor de conexión y operaciones sobre una base de datos SQLite.

    Centraliza la creación de la conexión, la inicialización del esquema y las
    vistas, la carga de datos semilla y la limpieza de la base de datos.

    Args:
        db_path (str): Ruta al archivo ``.db`` de SQLite (se crea si no existe).
        schema_path (str): Ruta al archivo SQL que define las tablas.
        views_path (str): Ruta al archivo SQL que define las vistas.
        seed_path (str | None): Ruta al archivo SQL con datos de prueba.
            Si es ``None`` :meth:`cargar_seed` no ejecutará ningún script.
        limpieza_path (str | None): Ruta al archivo SQL de limpieza de datos.
            Si es ``None`` :meth:`limpieza` no ejecutará ningún script.

    Attributes:
        conexion (sqlite3.Connection | None): Conexión activa a la base de
            datos; ``None`` mientras no se haya llamado a :meth:`connect`.
    """

    def __init__(
        self,
        db_path: str,
        schema_path: str,
        views_path: str,
        seed_path: str | None = None,
        limpieza_path: str | None = None,
    ):
        self.db_path = db_path
        self.schema_path = schema_path
        self.views_path = views_path
        self.seed_path = seed_path
        self.limpieza_path = limpieza_path
        self.conexion: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        """Abre la conexión con la base de datos SQLite.

        Si la conexión ya está abierta la devuelve directamente sin crear una
        nueva. Al crear una conexión nueva:

        - Activa las restricciones de clave foránea con ``PRAGMA foreign_keys = ON``.
        - Configura ``row_factory`` a :class:`sqlite3.Row` para acceder a las
          columnas por nombre.

        Returns:
            sqlite3.Connection: conexión activa a la base de datos.
        """
        if self.conexion is None:
            self.conexion = sqlite3.connect(self.db_path)
            self.conexion.execute("PRAGMA foreign_keys = ON;")  # Activo las claves foraneas
            self.conexion.row_factory = sqlite3.Row  # Habilito acceso por nombre de columnas
        return self.conexion

    def inicializar_schema(self) -> None:
        """Ejecuta los scripts SQL de esquema y vistas sobre la conexión activa.

        Carga y ejecuta primero ``schema.sql`` (tablas) y luego ``views.sql``
        (vistas). Los errores se registran en el logger pero no se propagan,
        permitiendo que la aplicación continúe.

        Raises:
            No propaga excepciones; registra :class:`sqlite3.Error`,
            :class:`FileNotFoundError` y :class:`OSError` vía logger.

        Returns:
            None
        """
        if self.conexion is None:
            logger.error("No se puede inicializar el esquema: La conexion no fue abierta (falta llamar a connect())")
            return
        try:
            # 1. Cargamos las tablas (schema.sql)
            with open(self.schema_path, encoding="utf-8") as archivo_sql:
                schema = archivo_sql.read()
            self.conexion.executescript(schema)

            # 2. Cargamos las vistas (views.sql) - si es que hay
            with open(self.views_path, encoding="utf-8") as archivo_vistas:
                vistas = archivo_vistas.read()
            self.conexion.executescript(vistas)

            logger.info("Esquema de db y vistas creado correctamente")
        except (sqlite3.Error, FileNotFoundError, OSError) as e:
            logger.error(f"Error al crear la vistas o la db: {e}")
            return

    def cargar_seed(self) -> None:
        """Carga el script SQL de datos semilla en la base de datos.

        Lee el archivo indicado en ``seed_path`` y lo ejecuta con
        ``executescript``. Si ``seed_path`` es ``None`` se captura el
        :class:`TypeError` y se registra en el logger.

        Raises:
            No propaga excepciones; registra :class:`sqlite3.Error` y
            :class:`TypeError` vía logger.

        Returns:
            None
        """
        if self.conexion is None:
            logger.error("No se puede inicializar el seed: La conexion no fue abierta (falta llamar a connect())")
            return
        if self.seed_path is None:
            logger.error("No se puede inicializar el seed: Falta el archivo o la ruta al mismo")
            return
        try:
            with open(self.seed_path, encoding="utf-8") as archivo_sql:
                schema = archivo_sql.read()
            self.conexion.executescript(schema)
            logger.info("Seed de datos cargado correctamente")
        except (sqlite3.Error, TypeError) as e:
            logger.error(f"Error al cargar seed de datos: {e}")
            return

    def get_connection(self) -> sqlite3.Connection | None:
        """Devuelve la conexión activa o ``None`` si no fue abierta.

        Returns:
            sqlite3.Connection | None: conexión activa, o ``None`` si
            :meth:`connect` no fue llamado previamente.
        """
        if self.conexion is not None:
            return self.conexion
        else:
            return None

    def close_connection(self) -> None:
        """Cierra la conexión con la base de datos y libera el recurso.

        Si no hay conexión activa la operación no hace nada. Tras cerrar,
        :attr:`conexion` se establece en ``None``.

        Returns:
            None
        """
        if self.conexion is not None:
            self.conexion.close()
            self.conexion = None

    def limpieza(self) -> None:
        """Ejecuta el script SQL de limpieza sobre la base de datos.

        Lee el archivo indicado en ``limpieza_path`` y lo ejecuta para eliminar
        los datos semilla u otros registros temporales. Los errores de SQLite se
        registran en el logger sin propagarse.

        Raises:
            No propaga excepciones; registra :class:`sqlite3.Error` vía logger.

        Returns:
            None
        """
        if self.conexion is None:
            logger.error("No se puede inicializar la limpieza: La conexion no fue abierta (falta llamar a connect())")
            return
        if self.limpieza_path is None:
            logger.error("No se puede inicializar la limpieza: falta el archivo o la ruta al mismo")
            return
        try:
            with open(self.limpieza_path, encoding="utf-8") as archivo_sql:
                schema = archivo_sql.read()
            self.conexion.executescript(schema)
            logger.info("Limpieza correcta")
        except sqlite3.Error as e:
            logger.error(f"Error al limpiar base de datos: {e}")
            return
