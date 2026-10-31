import sqlite3

from dominio.entidades.usuario import Usuario
from dominio.repositorios.usuario_repositorio import UsuarioRepositorio
from infraestructura.logger import get_logger

logger = get_logger(__name__)

# importacion de la clase SqliteConexion para poder conectarse a la base de datos sqlite y realizar operaciones CRUD
# en la tabla Usuarios, tambien se importa UsuarioRepositorio para la implementacion


class SqliteUsuarioRepositorio(UsuarioRepositorio):
    def __init__(self, conexion: sqlite3.Connection):
        """
        Implementamos la interfaz UsuarioRepositorio, la cual encarga de realizar
        operaciones CRUD(Create, Read, Update, Delete)
        en la tabla Usuarios de la base de datos sqlite

        Args:
            conexion (sqlite3.Connection): Conexion a la base de datos SQLite.

        """
        self.conexion = conexion

    def _row_to_entity(self, row: sqlite3.Row) -> Usuario:
        """Esta funcion toma una fila de la tabla Usuarios de la base de datos y la convierte en una instancia,
            que es una entidad del dominio de la aplicacion, en este caso un objeto de la clase Usuario.

        Args:
            row (sqlite3.Row): Fila de la tabla Usuarios de la base de datos.

        Returns:
            Usuario: Entidad Usuario construida a partir de la fila de la base de datos.
        """
        return Usuario(
            nombre=row["nombre"],
            email=row["email"],
            password_hash=row["contrasenia"],
            idUsuario=row["idUsuario"],
            #
        )

    def encontrar_por_id(self, id: int) -> Usuario | None:
        """
        Funcion que se encarga de buscar a un usuario por su ID en el cual fue registrado en la BD
        en el caso de que exista, retorna el usuario, sino retorna None si no se encuentra

        Args:
            id (int): ID del usuario a buscar.

        Returns:
            Usuario | None: Retorna el usuario encontrado o None si no se encuentra.
        """

        cursor = self.conexion.cursor()  # con este cursor ejecutamos las consultas SQL

        query = "SELECT * FROM usuario WHERE idUsuario = ?"  # esto sirve para buscar un usuario por su ID
        cursor.execute(query, (id,))  # ejecutamos la consulta SQL con el ID del usuario que queremos buscar
        row = cursor.fetchone()
        # acá saca la primer coincidencia que encuentra en la BD

        if row is None:  # si no encuentra nada en la BD, retorna None
            return None

        # si encuentra un usuario, lo convierte en una entidad y lo retorna
        return self._row_to_entity(row)

    def encontrar_por_mail(self, email: str) -> Usuario | None:
        """Funcion para buscar un determinado Usuario por su direccion de mail

        Args:
            email (str): Direccion de email del usuario a buscar.

        Returns:
            Usuario | None: Retorna el usuario asociado al email o None si no se encuentra.
        """
        cursor = self.conexion.cursor()

        query = "SELECT * FROM usuario WHERE email = ?"
        cursor.execute(query, (email,))

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_entity(row)

    def guardar(self, us_aux: Usuario) -> Usuario | None:
        """Funcion que se encarga de guardar un usuario en la BD

        Args:
            us_aux (Usuario): Entidad Usuario a guardar.

        Returns:
            Usuario | None: Retorna el usuario guardado con su ID asignado en la BD o None si ocurre un error.
        """
        try:
            cursor = self.conexion.cursor()
            query = "INSERT INTO usuario (email, nombre, contrasenia) VALUES (?, ?, ?)"
            cursor.execute(query, (us_aux.email, us_aux.nombre, us_aux.password_hash))
            self.conexion.commit()
            idUsuario = cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error al guardar usuario: {e}", exc_info=True)
            return None

        try:
            return Usuario(
                nombre=us_aux.nombre, email=us_aux.email, password_hash=us_aux.password_hash, idUsuario=idUsuario
            )
        except TypeError as e:
            logger.critical(f"""Usuario guardado (idUsuario={idUsuario})
                            pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    # Estos comentarios son de ayuda propia para poder entender que significa cada parte del codigo,
    # que hace cada funcion y como poder implementar las logica de negocio
