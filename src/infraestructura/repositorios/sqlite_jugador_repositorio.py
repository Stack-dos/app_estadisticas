import sqlite3

from dominio.entidades.club import Club
from dominio.entidades.jugador import Jugador, JugadorClub
from dominio.exceptions import VinculoActivoExistenteError
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from infraestructura.logger import get_logger

logger = get_logger(__name__)


class SqliteJugadorRepositorio(JugadorRepositorio):
    def __init__(self, conexion: sqlite3.Connection):
        """
        Inicializa el repositorio de jugadores con una conexión a la base de datos SQLite.

        Args:
            conexion (sqlite3.Connection):  Conexion a la base de datos SQLite.
        """
        self.conexion = conexion

    def _row_to_entity(self, row: sqlite3.Row) -> Jugador:
        """Convierte una fila de la base de datos en una entidad Jugador.

        Args:
            row (sqlite3.Row): Fila de la base de datos que representa un jugador.

        Returns:
            Jugador: Entidad Jugador construida a partir de la fila.
        """
        return Jugador(
            nombre=row["nombre"],
            apellido=row["apellido"],
            anioNacimiento=row["anioNacimiento"],
            idJugador=row["idJugador"],
        )

    def buscar_por_id(self, id_jugador: int) -> Jugador | None:
        """Funcion que se encarga de buscar un jugador por su ID en la base de datos en el cual fue registrado,
        en el caso de que exista, retorna el jugador, sino retorna None si no se encuentra

        Args:
            id_jugador (int): ID del jugador a buscar.

        Returns:
            Jugador | None: Retorna el jugador encontrado o None si no se encuentra.
        """
        cursor = self.conexion.cursor()

        query = "SELECT * FROM jugador WHERE idJugador = ?"
        cursor.execute(query, (id_jugador,))
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_entity(row)

    def buscar_por_club(self, idClub: int) -> list[Jugador]:
        """Funcion que se encarga de buscar los jugadores actuales de un club en la base de datos.
        Solo se consideran los vinculos vigentes (fechaHasta IS NULL): los jugadores que ya se
        fueron del club no aparecen.

        Args:
            idClub (int): ID del club del cual se quieren buscar los jugadores.

        Returns:
            list[Jugador]: Lista de jugadores con vinculo vigente en el club.
        """
        cursor = self.conexion.cursor()

        query = """
        SELECT j.idJugador,j.nombre,j.apellido,j.anioNacimiento
        FROM jugadorClub jc
        JOIN jugador j ON j.idJugador = jc.idJugador
        WHERE jc.idClub = ? AND jc.fechaHasta IS NULL;
        """
        cursor.execute(query, (idClub,))

        rows = cursor.fetchall()
        if not rows:
            return []

        resultado = []
        for r in rows:
            j_aux = self._row_to_entity(r)
            resultado.append(j_aux)
        return resultado

    def guardar(self, jugador: Jugador) -> Jugador | None:
        """Funcion que se encarga de guardar un jugador en la BD

        Args:
            jugador (Jugador): Entidad Jugador a guardar.

        Returns:
            Jugador | None: Retorna el jugador guardado con su ID asignado en la BD o None si ocurre un error.
        """
        cursor = self.conexion.cursor()
        try:
            query = """
            INSERT INTO jugador (nombre, apellido, anioNacimiento) VALUES (?, ?, ?);
            """
            cursor.execute(
                query,
                (jugador.nombre, jugador.apellido, jugador.anioNacimiento),
            )
            self.conexion.commit()
            id_jugador = cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error al guardar Jugador: {e}", exc_info=True)
            return None

        try:
            return Jugador(
                nombre=jugador.nombre,
                apellido=jugador.apellido,
                anioNacimiento=jugador.anioNacimiento,
                idJugador=id_jugador,
            )
        except TypeError as e:
            logger.critical(f"""Jugador guardado (idJugador={id_jugador})
                                pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def link_to_club(self, jc: JugadorClub) -> JugadorClub | None:
        """
        Funcion que se encarga de linkear un jugador con un club en la base de datos.

        Args:
            jc (JugadorClub): Entidad JugadorClub a linkear.

        Returns:
            JugadorClub | None: Retorna el jugador linkeado con el club o None si ocurre un error.
        """
        try:
            cursor = self.conexion.cursor()
            query = "INSERT INTO jugadorClub (idJugador, idClub, fechaDesde) VALUES (?, ?, ?)"
            cursor.execute(query, (jc.idJugador, jc.idClub, jc.fechaDesde))
            self.conexion.commit()
        except sqlite3.IntegrityError as e:
            if str(e) == "UNIQUE constraint failed: jugadorClub.idJugador":
                raise VinculoActivoExistenteError(
                    f"El jugador (idJugador={jc.idJugador}), ya tiene un club activo"
                ) from e
            logger.error(f"Error al linkear jugador con club: {e}", exc_info=True)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error al linkear jugador con club: {e}", exc_info=True)
            return None

        try:
            return JugadorClub(
                fechaDesde=jc.fechaDesde,
                fechaHasta=None,
                idJugador=jc.idJugador,
                idClub=jc.idClub,
            )
        except TypeError as e:
            logger.critical(f"""Jugador linkeado pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def club_activo(self, id_jugador: int) -> Club | None:
        """
        Funcion que se encarga de buscar el club activo de un jugador en la base de datos.

        Args:
            id_jugador (int): ID del jugador del cual se quiere buscar el club activo.
        Returns:
            Club | None: Retorna el club activo del jugador o None si no se encuentra.
        """
        cursor = self.conexion.cursor()

        query = """
        SELECT c.* FROM club c
        JOIN jugadorClub jc ON c.idClub = jc.idClub
        WHERE jc.idJugador = ? AND jc.fechaHasta IS NULL;
        """

        cursor.execute(query, (id_jugador,))
        row = cursor.fetchone()

        if row is None:
            return None

        return Club(nombre=row["nombre"], idClub=row["idClub"])

    def historial_vinculos(self, id_jugador: int) -> list[JugadorClub]:
        """
        Funcion que se encarga de devolver todos los vinculos de un jugador con clubes.

        Args:
            id_jugador (int): ID del jugador del cual se quiere obtener el historial.

        Returns:
            list[JugadorClub]: Vinculos vigentes y cerrados, del mas antiguo al mas reciente
            (lista vacia si el jugador nunca estuvo vinculado a un club).
        """
        cursor = self.conexion.cursor()

        query = """
        SELECT idJugador, idClub, fechaDesde, fechaHasta
        FROM jugadorClub
        WHERE idJugador = ?
        ORDER BY fechaDesde, idClub;
        """
        cursor.execute(query, (id_jugador,))

        return [
            JugadorClub(
                fechaDesde=row["fechaDesde"],
                fechaHasta=row["fechaHasta"],
                idJugador=row["idJugador"],
                idClub=row["idClub"],
            )
            for row in cursor.fetchall()
        ]

    def cerrar_vinculo(self, id_jugador: int, fecha_hasta: str) -> JugadorClub | None:
        """
        Funcion que se encarga de cerrar el vinculo vigente de un jugador con su club, cargando su fechaHasta.

        Args:
            id_jugador (int): ID del jugador que deja su club.
            fecha_hasta (str): Fecha de baja (AAAA-MM-DD). No puede ser anterior a la fecha de inicio del vinculo:
                la base lo rechaza con un CHECK.

        Returns:
            JugadorClub | None: El vinculo ya cerrado, o None si el jugador no tenia un vinculo vigente
            o si ocurre un error.
        """
        cursor = self.conexion.cursor()
        try:
            cursor.execute(
                "SELECT idClub, fechaDesde FROM jugadorClub WHERE idJugador = ? AND fechaHasta IS NULL;",
                (id_jugador,),
            )
            vigente = cursor.fetchone()
            if vigente is None:
                return None

            cursor.execute(
                "UPDATE jugadorClub SET fechaHasta = ? WHERE idJugador = ? AND idClub = ? AND fechaDesde = ?;",
                (fecha_hasta, id_jugador, vigente["idClub"], vigente["fechaDesde"]),
            )
            self.conexion.commit()
        except sqlite3.Error as e:
            logger.error(f"Error al cerrar el vinculo del jugador: {e}", exc_info=True)
            return None

        try:
            return JugadorClub(
                fechaDesde=vigente["fechaDesde"],
                fechaHasta=fecha_hasta,
                idJugador=id_jugador,
                idClub=vigente["idClub"],
            )
        except TypeError as e:
            logger.critical(f"""Vinculo cerrado pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise
