import sqlite3

from dominio.entidades.club import Club, UsuarioClub
from dominio.repositorios.club_repositorio import ClubRepositorio
from infraestructura.logger import get_logger

logger = get_logger(__name__)


class SqliteClubRepositorio(ClubRepositorio):
    def __init__(self, conexion: sqlite3.Connection):
        """Inicializa el repositorio de clubes con una conexión a la base de datos.

        Args:
            conexion (sqlite3.Connection): Conexión a la base de datos SQLite.

        """
        self.conexion = conexion

    def _row_to_entity_Club(self, row: sqlite3.Row) -> Club:
        """Convierte una fila de la base de datos en una entidad Club.

        Args:
            row (sqlite3.Row): Fila de la base de datos que representa un club.

        Returns:
            Club: Entidad Club construida a partir de la fila.
        """
        return Club(
            idClub=row["idClub"],
            nombre=row["nombre"],
        )

    def _row_to_entity_UsuarioClub(self, row: sqlite3.Row) -> UsuarioClub:
        """Convierte una fila de la base de datos en una entidad UsuarioClub.

        Args:
            row (sqlite3.Row): Fila de la base de datos que representa un usuario en un club.

        Returns:
            UsuarioClub: Entidad UsuarioClub construida a partir de la fila.
        """
        return UsuarioClub(
            idClub=row["idClub"],
            idUsuario=row["idUsuario"],
            rol=row["rolEntrenador"],
        )

    def buscar_por_id_usuario(self, id_usuario: int) -> list[Club] | None:
        """Funcion que se encarga de buscar los clubes a los que pertenece un usuario

        Args:
            id_usuario (int): ID del usuario para el cual se buscan los clubes.

        Returns:
            list[Club] | None: Lista de clubes a los que pertenece el usuario o None si no se encuentra ninguno.
        """
        cursor = self.conexion.cursor()

        query = """
        SELECT c.idClub,c.nombre FROM club c
        JOIN usuarioClub uc ON c.idClub = uc.idClub
        WHERE uc.idUsuario = ?;
        """
        cursor.execute(query, (id_usuario,))
        rows = cursor.fetchall()
        if not rows:
            return None

        lista_clubes = []
        for r in rows:
            aux = self._row_to_entity_Club(r)
            lista_clubes.append(aux)
        return lista_clubes

    def buscar_por_id(self, id_club: int) -> Club | None:
        """Funcion que se encarga de buscar un club por su ID en la base de datos.

        Args:
            id_club (int): ID del club que se desea buscar.

        Returns:
            Club | None: Entidad Club correspondiente al ID proporcionado o None si no se encuentra.
        """
        cursor = self.conexion.cursor()

        query = "SELECT * FROM club WHERE idClub = ?;"
        cursor.execute(query, (id_club,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity_Club(row)

    def buscar_por_nombre(self, nombre: str) -> list[Club] | None:
        """Funcion que se encarga de buscar clubes por su nombre en la base de datos.

        Args:
            nombre (str): Nombre del club que se desea buscar.

        Returns:
            list[Club] | None: Lista de clubes que coinciden con el nombre proporcionado
            o None si no se encuentra ninguno.
        """
        cursor = self.conexion.cursor()

        query = "SELECT * FROM club WHERE nombre LIKE ?;"
        cursor.execute(query, (f"%{nombre}%",))
        rows = cursor.fetchall()
        if not rows:
            return None
        resultados = []
        for r in rows:
            aux = self._row_to_entity_Club(r)
            resultados.append(aux)
        return resultados

    def guardar(self, club: Club) -> Club | None:
        """Función para guardar un club en la base de datos.

        Args:
            club (Club): Entidad Club que se desea guardar en la base de datos.

        Returns:
            Club | None: Entidad Club guardada en la base de datos o None si ocurre un error.
        """
        cursor = self.conexion.cursor()

        try:
            query = "INSERT INTO club (nombre) VALUES (?);"
            cursor.execute(query, (club.nombre,))
            self.conexion.commit()
            id_club = cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error al guardar club: {e}", exc_info=True)
            return None

        try:
            return Club(idClub=id_club, nombre=club.nombre)
        except TypeError as e:
            logger.critical(f"""Club guardado (id_club={id_club})
                                pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def link_user_to_club(self, us_club: UsuarioClub) -> UsuarioClub | None:
        """Funcion para linkear un usuario a un club especifico

        Args:
            us_club (UsuarioClub): Entidad UsuarioClub que representa la relación entre un usuario y un club.

        Returns:
            UsuarioClub | None: Entidad UsuarioClub guardada en la base de datos o None si ocurre un error.
        """
        cursor = self.conexion.cursor()

        try:
            query = """
            SELECT * FROM usuario WHERE idUsuario = ?;
            """
            cursor.execute(query, (us_club.idUsuario,))
            row = cursor.fetchone()
            if row is None:
                return None

            query = """
            SELECT * FROM club WHERE idClub = ?;
            """
            cursor.execute(query, (us_club.idClub,))
            row = cursor.fetchone()
            if row is None:
                return None

            query = """
            INSERT INTO usuarioClub (idUsuario, idClub, rolEntrenador) VALUES (?, ?, ?);
            """
            cursor.execute(query, (us_club.idUsuario, us_club.idClub, us_club.rol))
            self.conexion.commit()
        except sqlite3.Error as e:
            logger.error(f"Error al linkear club y usuario: {e}", exc_info=True)
            return None

        try:
            return UsuarioClub(idUsuario=us_club.idUsuario, idClub=us_club.idClub, rol=us_club.rol)
        except TypeError as e:
            logger.critical(f"""Club linkeado pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise
