import sqlite3

from dominio.entidades.partido import JugadorPartido, Partido, PartidoResumen
from dominio.repositorios.partido_repositorio import PartidoRepositorio
from infraestructura.logger import get_logger

logger = get_logger(__name__)


class SqlitePartidoRepositorio(PartidoRepositorio):
    def __init__(self, conexion: sqlite3.Connection):
        """
        Funcion que se encarga de inicializar el repositorio de partidos

        Args:
            conexion (sqlite3.Connection): Conexion a la base de datos SQLite.
        """
        self.conexion = conexion

    def _row_to_entity_Partido(self, row: sqlite3.Row) -> Partido:
        """
        Esta funcion toma una fila de la tabla partido de la base de datos y la convierte en una instancia,
        que es una entidad del dominio de la aplicacion, en este caso un objeto de la clase Partido

        Args:
            row (sqlite3.Row): Fila de la tabla partido de la BD

        Returns:
            Partido: Retorna una instancia de la entidad Partido construida a partir de la fila de la base de datos.
        """
        return Partido(
            fecha=row["fecha"],
            estadio=row["estadio"],
            idCompetencia=row["idCompetencia"],
            idClubLocal=row["idClubLocal"],
            idClubVisitante=row["idClubVisitante"],
            idPartido=row["idPartido"],
        )

    def buscar_por_club(self, id_club: int) -> list[Partido] | None:
        """
        Funcion que se encarga de buscar los partidos en los cuales participo un determinado club

        Args:
            id_club (int): ID del club para el cual se buscan los partidos.

        Returns:
            list[Partido] | None: Retorna una lista de partidos en los cuales participo el club asociado o
            Retorna None si no encuentra ninguna
        """
        cursor = self.conexion.cursor()

        query = "SELECT * FROM partido WHERE idClubLocal = ? OR idClubVisitante = ?"
        cursor.execute(query, (id_club, id_club))
        rows = cursor.fetchall()
        if not rows:
            return None
        return [self._row_to_entity_Partido(row) for row in rows]

    def buscar_por_id(self, idPartido: int) -> Partido | None:
        """
        Funcion que se encarga de buscar un partido por su ID en el cual fue registrado en la BD
        en el caso de que exista, retorna el partido, sino retorna None si no se encuentra
        Args:
            idPartido (int): ID del partido a buscar.

        Returns:
            Partido | None: Retorna el partido encontrado o None si no se encuentra.
        """
        cursor = self.conexion.cursor()

        query = "SELECT * FROM partido WHERE idPartido = ?"
        cursor.execute(query, (idPartido,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity_Partido(row)

    def guardar_partido(self, partido: Partido) -> Partido | None:
        """
        Funcion que se encarga de guardar un partido en la BD
        Args:
            partido (Partido): Entidad Partido a guardar.

        Returns:
            Partido | None: Retorna el partido guardado con su ID asignado en la BD o None si ocurre un error.
        """
        cursor = self.conexion.cursor()
        try:
            query = """
            SELECT * FROM competencia WHERE idCompetencia = ?;
            """
            cursor.execute(query, (partido.idCompetencia,))
            row = cursor.fetchone()
            if row is None:
                logger.warning(
                    "No se pudo guardar partido: competencia inexistente (idCompetencia=%s)",
                    partido.idCompetencia,
                )
                return None

            query = """
            SELECT * FROM club WHERE idClub IN (?,?);
            """
            cursor.execute(query, (partido.idClubLocal, partido.idClubVisitante))
            row = cursor.fetchall()
            if not row or len(row) < 2:
                logger.warning(
                    "No se pudo guardar partido: club local o visitante inexistente "
                    "(idClubLocal=%s, idClubVisitante=%s)",
                    partido.idClubLocal,
                    partido.idClubVisitante,
                )
                return None
            query = """
            INSERT INTO partido (fecha, estadio, idCompetencia, idClubLocal, idClubVisitante)
            VALUES (?, ?, ?, ?, ?)
            """
            cursor.execute(
                query,
                (partido.fecha, partido.estadio, partido.idCompetencia, partido.idClubLocal, partido.idClubVisitante),
            )
            self.conexion.commit()

            id_partido = cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error al guardar partido: {e}", exc_info=True)
            return None

        try:
            return Partido(
                fecha=partido.fecha,
                estadio=partido.estadio,
                idCompetencia=partido.idCompetencia,
                idClubLocal=partido.idClubLocal,
                idClubVisitante=partido.idClubVisitante,
                idPartido=id_partido,
            )
        except TypeError as e:
            logger.critical(f"""Partido guardado (id_partido={id_partido})
                                pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def guardar_boxscore(self, boxscore: JugadorPartido) -> JugadorPartido | None:
        """
        Funcion que se encarga de guardar un boxscore de un jugador en un partido especifico en la BD
        Args:
            boxscore (JugadorPartido): Entidad JugadorPartido a guardar.

        Returns:
            JugadorPartido | None: Retorna el boxscore guardado con su ID asignado en la BD o None si ocurre un error.
        """
        try:
            cursor = self.conexion.cursor()

            query = """
            SELECT * FROM partido WHERE idPartido = ?;
            """
            cursor.execute(query, (boxscore.idPartido,))
            row = cursor.fetchone()
            if row is None:
                return None

            query = """
            SELECT * FROM jugador WHERE idJugador = ?;
            """
            cursor.execute(query, (boxscore.idJugador,))
            row = cursor.fetchone()
            if row is None:
                return None

            query = """
            SELECT * FROM club WHERE idClub = ?;
            """
            cursor.execute(query, (boxscore.idClub,))
            row = cursor.fetchone()
            if row is None:
                return None

            query = """
                INSERT INTO jugadorPartido
                (idJugador,idPartido,idClub,minutosJugados,puntos,T2C,T2L,T3C,T3L,T1C,T1L,
                rebotesDef,rebotesOf,asistencias,recuperos,perdidas,taponesRecibidos,taponesRealizados,
                faltasRecibidas,faltasCometidas)
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                """
            cursor.execute(
                query,
                (
                    boxscore.idJugador,
                    boxscore.idPartido,
                    boxscore.idClub,
                    boxscore.minutosJugados,
                    boxscore.puntos,
                    boxscore.t2c,
                    boxscore.t2l,
                    boxscore.t3c,
                    boxscore.t3l,
                    boxscore.t1c,
                    boxscore.t1l,
                    boxscore.rebotesDef,
                    boxscore.rebotesOf,
                    boxscore.asistencias,
                    boxscore.recuperos,
                    boxscore.perdidas,
                    boxscore.taponesRecibidos,
                    boxscore.taponesRealizados,
                    boxscore.faltasRecibidas,
                    boxscore.faltasCometidas,
                ),
            )
            self.conexion.commit()
        except sqlite3.Error as e:
            logger.error(f"Error al guardar boxscore: {e}", exc_info=True)
            return None

        try:
            return JugadorPartido(
                idJugador=boxscore.idJugador,
                idPartido=boxscore.idPartido,
                idClub=boxscore.idClub,
                minutosJugados=boxscore.minutosJugados,
                puntos=boxscore.puntos,
                t2c=boxscore.t2c,
                t2l=boxscore.t2l,
                t3c=boxscore.t3c,
                t3l=boxscore.t3l,
                t1c=boxscore.t1c,
                t1l=boxscore.t1l,
                rebotesDef=boxscore.rebotesDef,
                rebotesOf=boxscore.rebotesOf,
                asistencias=boxscore.asistencias,
                recuperos=boxscore.recuperos,
                perdidas=boxscore.perdidas,
                taponesRecibidos=boxscore.taponesRecibidos,
                taponesRealizados=boxscore.taponesRealizados,
                faltasRecibidas=boxscore.faltasRecibidas,
                faltasCometidas=boxscore.faltasCometidas,
            )
        except TypeError as e:
            logger.critical(f"""Boxscore guardado pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def save_with_boxscore(
        self, partido: Partido, boxscore: list[JugadorPartido]
    ) -> tuple[Partido, list[JugadorPartido]] | None:
        """
            Función que se encarga de guardar el partido y el boxscore de todos los jugadores en una
            única transacción atómica.

        Utiliza el context manager de sqlite3  que realiza
        COMMIT automático al salir sin error o ROLLBACK ante cualquier excepción.
        Si falla cualquier fila del boxscore, el partido tampoco queda guardado.

        Args:
            boxscore (JugadorPartido): Entidad JugadorPartido a guardar.
            partido (Partido): Entidad Partido a guardar.

        Returns:
            JugadorPartido | None: Retorna el boxscore guardado con su ID asignado en la BD o None si ocurre un error.
        """
        try:
            with self.conexion:
                cursor = self.conexion.cursor()

                # Validar que la competencia y los clubes del partido existan.
                cursor.execute("SELECT * FROM competencia WHERE idCompetencia = ?", (partido.idCompetencia,))
                if cursor.fetchone() is None:
                    raise sqlite3.IntegrityError(f"La competencia con id {partido.idCompetencia} no existe.")

                cursor.execute(
                    "SELECT COUNT(*) FROM club WHERE idClub IN (?, ?)", (partido.idClubLocal, partido.idClubVisitante)
                )
                if cursor.fetchone()[0] < 2:
                    raise sqlite3.IntegrityError("El club local o visitante no existe.")

                # 2. Validar que todos los jugadores y clubes del boxscore existan.
                jugadores_ids = {bs.idJugador for bs in boxscore}

                if jugadores_ids:  # Solo validar si la lista no está vacía
                    placeholders = ",".join("?" for _ in jugadores_ids)
                    # El f-string solo arma los "?"; los valores van aparte, como parametros
                    cursor.execute(
                        f"SELECT idJugador FROM jugador WHERE idJugador IN ({placeholders})",  # noqa: S608
                        tuple(jugadores_ids),
                    )
                    jugadores_existentes_ids = {row[0] for row in cursor.fetchall()}

                    jugadores_faltantes = sorted(jugadores_ids - jugadores_existentes_ids)

                    if jugadores_faltantes:
                        raise sqlite3.IntegrityError(
                            f"Jugadores faltantes en boxscore (idJugador): {jugadores_faltantes}"
                        )

                # --- Fin Validación ---

                # Insertar cabecera del partido
                cursor.execute(
                    """
                    INSERT INTO partido (fecha, estadio, idCompetencia, idClubLocal, idClubVisitante)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        partido.fecha,
                        partido.estadio,
                        partido.idCompetencia,
                        partido.idClubLocal,
                        partido.idClubVisitante,
                    ),
                )
                id_partido = cursor.lastrowid

                # Insertar cada fila del boxscore
                filas_guardadas = []
                for bs in boxscore:
                    cursor.execute(
                        """
                        INSERT INTO jugadorPartido
                        (idJugador, idPartido, idClub, minutosJugados, puntos,
                         T2C, T2L, T3C, T3L, T1C, T1L,
                         rebotesDef, rebotesOf, asistencias, recuperos, perdidas,
                         taponesRecibidos, taponesRealizados, faltasRecibidas, faltasCometidas)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            bs.idJugador,
                            id_partido,
                            bs.idClub,
                            bs.minutosJugados,
                            bs.puntos,
                            bs.t2c,
                            bs.t2l,
                            bs.t3c,
                            bs.t3l,
                            bs.t1c,
                            bs.t1l,
                            bs.rebotesDef,
                            bs.rebotesOf,
                            bs.asistencias,
                            bs.recuperos,
                            bs.perdidas,
                            bs.taponesRecibidos,
                            bs.taponesRealizados,
                            bs.faltasRecibidas,
                            bs.faltasCometidas,
                        ),
                    )
                    filas_guardadas.append(bs)

            partido_guardado = Partido(
                fecha=partido.fecha,
                estadio=partido.estadio,
                idCompetencia=partido.idCompetencia,
                idClubLocal=partido.idClubLocal,
                idClubVisitante=partido.idClubVisitante,
                idPartido=id_partido,
            )
            return (partido_guardado, filas_guardadas)

        except sqlite3.Error as e:
            logger.error(
                "Error en save_with_boxscore (transacción revertida): %s | "
                "partido(fecha=%s, competencia=%s, local=%s, visitante=%s) | "
                "filas_boxscore=%s",
                e,
                partido.fecha,
                partido.idCompetencia,
                partido.idClubLocal,
                partido.idClubVisitante,
                len(boxscore),
                exc_info=True,
            )

            return None

    def resumen_por_club(self, id_club: int) -> list[PartidoResumen]:
        """
        Funcion que se encarga de listar los partidos de un club (como local o visitante) con los nombres
        de la competencia y de los clubes, usando la vista `v_partidos_resumen`.

        Args:
            id_club (int): ID del club para el cual se buscan los partidos.

        Returns:
            list[PartidoResumen]: Partidos del club, del mas antiguo al mas reciente
            (lista vacia si el club no tiene partidos).
        """
        cursor = self.conexion.cursor()

        query = """
        SELECT id_partido, fecha_partido, estadio, competencia, anio_competencia, club_local, club_visitante
        FROM v_partidos_resumen
        WHERE id_club_local = ? OR id_club_visitante = ?
        ORDER BY fecha_partido, id_partido;
        """
        cursor.execute(query, (id_club, id_club))

        return [
            PartidoResumen(
                idPartido=row["id_partido"],
                fecha=row["fecha_partido"],
                estadio=row["estadio"],
                competencia=row["competencia"],
                anioCompetencia=row["anio_competencia"],
                clubLocal=row["club_local"],
                clubVisitante=row["club_visitante"],
            )
            for row in cursor.fetchall()
        ]
