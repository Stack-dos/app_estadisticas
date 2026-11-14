import sqlite3

from dominio.entidades.competencia import Categoria, Competencia, Inscripcion, JugadorListaBuenaFe, ListaBuenaFe
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from infraestructura.logger import get_logger

logger = get_logger(__name__)


class SqliteCompetenciaRepositorio(CompetenciaRepositorio):
    def __init__(self, conexion: sqlite3.Connection):
        """Implementamos la interfaz CompetenciaRepositorio, la cual encarga de realizar operaciones CRUD
        (Create, Read, Update, Delete) en la tabla competencia de la base de datos sqlite

        Args:
            conexion (sqlite3.Connection): Conexion a la base de datos SQLite.
        """
        self.conexion = conexion

    def _row_to_entity_Competencia(self, row: sqlite3.Row) -> Competencia:
        """Funcion que se encarga de convertir una fila de la tabla competencia en una entidad Competencia

        Args:
            row (sqlite3.Row): Fila de la tabla competencia de la base de datos.

        Returns:
            Competencia: Entidad Competencia construida a partir de la fila de la base de datos.
        """
        return Competencia(nombre=row["nombre"], anio=row["anio"], tipo=row["tipo"], idCompetencia=row["idCompetencia"])

    def _row_to_entity_Categoria(self, row: sqlite3.Row) -> Categoria:
        """Funcion que se encarga de convertir una fila de la tabla categoria en una entidad Categoria

        Args:
            row (sqlite3.Row): Fila de la tabla categoria de la base de datos.

        Returns:
            Categoria: Entidad Categoria construida a partir de la fila de la base de datos.
        """
        return Categoria(nombre=row["nombre"], idCategoria=row["idCategoria"])

    def _row_to_entity_Inscripciones(self, row: sqlite3.Row) -> Inscripcion:
        """Funcion que se encarga de convertir una fila de la tabla inscripciones en una entidad Inscripcion.

        Args:
            row (sqlite3.Row): Fila de la tabla inscripciones de la base de datos.

        Returns:
            Inscripcion: Entidad Inscripcion construida a partir de la fila de la base de datos.
        """
        return Inscripcion(
            idClub=row["idClub"],
            idCategoria=row["idCategoria"],
            idCompetencia=row["idCompetencia"],
            idInscripcion=row["idInscripcion"],
        )

    def _row_to_entity_ListaBuenaFe(self, row: sqlite3.Row) -> ListaBuenaFe:
        """Funcion que se encarga de convertir una fila de la tabla listaBuenaFe en una entidad ListaBuenaFe

        Args:
            row (sqlite3.Row): Fila de la tabla listaBuenaFe de la base de datos.

        Returns:
            ListaBuenaFe: Entidad ListaBuenaFe construida a partir de la fila de la base de datos.
        """
        return ListaBuenaFe(
            fechaPresentacion=row["fechaPresentacion"],
            idInscripcion=row["idInscripcion"],
            idListaBuenaFe=row["idListaBuenaFe"],
        )

    def guardar_competencia(self, compe: Competencia) -> Competencia | None:
        """Funcion que se encarga de guardar una competencia en la base de datos.

        Args:
            compe (Competencia): Entidad Competencia a guardar.

        Returns:
            Competencia | None: Retorna la competencia guardada con su ID asignado en la BD o None si ocurre un error.
        """
        try:
            cursor = self.conexion.cursor()
            query = """
            INSERT INTO competencia (nombre,anio,tipo) VALUES (?,?,?);
            """
            cursor.execute(query, (compe.nombre, compe.anio, compe.tipo))
            self.conexion.commit()
            idCompetencia = cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error al guardar Competencia: {e}", exc_info=True)
            return None

        try:
            return Competencia(nombre=compe.nombre, anio=compe.anio, tipo=compe.tipo, idCompetencia=idCompetencia)
        except TypeError as e:
            logger.critical(f"""Competencia guardado (idCompetencia={idCompetencia})
                                pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def guardar_competencia_con_categorias(self, compe: Competencia, idCategorias: list[int]) -> Competencia | None:
        """Guarda una competencia y habilita sus categorias en una unica transaccion atomica.

        Utiliza el context manager de sqlite3 (COMMIT al salir sin error, ROLLBACK ante cualquier excepcion):
        si una categoria no existe (la rechaza la FK) o esta repetida en la lista (la rechaza la PK compuesta),
        la competencia tampoco queda guardada.

        Args:
            compe (Competencia): Entidad Competencia a guardar (sin ID).
            idCategorias (list[int]): IDs de las categorias que juega. Puede venir vacia.

        Returns:
            Competencia | None: La competencia guardada con su ID, o None si ocurre un error.
        """
        try:
            with self.conexion:
                cursor = self.conexion.cursor()
                cursor.execute(
                    "INSERT INTO competencia (nombre,anio,tipo) VALUES (?,?,?);", (compe.nombre, compe.anio, compe.tipo)
                )
                idCompetencia = cursor.lastrowid
                if idCompetencia is None:
                    raise sqlite3.DatabaseError("SQLite no devolvio el id de la competencia recien insertada")
                # Un mismo INSERT, una fila por categoria: [(5, 2), (5, 3)] inserta (5, 2) y despues (5, 3)
                cursor.executemany(
                    "INSERT INTO competenciaCategoria (idCompetencia, idCategoria) VALUES (?, ?);",
                    [(idCompetencia, idCategoria) for idCategoria in idCategorias],
                )
        except sqlite3.Error as e:
            logger.error(f"Error al guardar la competencia con sus categorias: {e}", exc_info=True)
            return None

        return Competencia(nombre=compe.nombre, anio=compe.anio, tipo=compe.tipo, idCompetencia=idCompetencia)

    def buscar_competencia_por_id(self, idCompetencia: int) -> Competencia | None:
        """Funcion que se encarga de buscar una competencia por su ID

        Args:
            idCompetencia (int): ID de la competencia a buscar.

        Returns:
            Competencia | None: Retorna la competencia encontrada o None si no se encuentra.
        """
        cursor = self.conexion.cursor()
        query = """
        SELECT * FROM competencia WHERE idCompetencia = ?;
        """
        cursor.execute(query, (idCompetencia,))
        rows = cursor.fetchone()
        if rows is None:
            return None
        return self._row_to_entity_Competencia(rows)

    def obtener_todas_competencias(self) -> list[Competencia]:
        """Funcion que se encarga de obtener todas las competencias existentes en la base de datos

        Returns:
            list[Competencia]: Lista de competencias existentes en la base de datos.
        """

        cursor = self.conexion.cursor()
        query = "SELECT * FROM competencia;"
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            return []
        lista_competencias = []
        for r in rows:
            aux = self._row_to_entity_Competencia(r)
            lista_competencias.append(aux)
        return lista_competencias

    def guardar_categoria(self, cat: Categoria) -> Categoria | None:
        """Funcion que se encarga de guardar una categoria en la base de datos

        Args:
            cat (Categoria): Entidad Categoria a guardar.

        Returns:
            Categoria | None: Retorna la categoria guardada con su ID asignado en la BD o None si ocurre un error.
        """
        try:
            cursor = self.conexion.cursor()
            query = """
            INSERT INTO categoria (nombre) VALUES (?);
            """
            cursor.execute(query, (cat.nombre,))
            self.conexion.commit()
            idCategoria = cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error al guardar Categoria: {e}", exc_info=True)
            return None
        try:
            return Categoria(nombre=cat.nombre, idCategoria=idCategoria)
        except TypeError as e:
            logger.critical(f"""Categoria guardada (idCategoria={idCategoria})
                                pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def obtener_categorias(self) -> list[Categoria]:
        """Funcion que se encarga de obtener todas las categorias existentes en la base de datos.

        Returns:
            list[Categoria]: Lista de categorias existentes en la base de datos.
        """
        cursor = self.conexion.cursor()
        query = "SELECT * FROM categoria;"
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            return []
        lista_categorias = []
        for r in rows:
            aux = self._row_to_entity_Categoria(r)
            lista_categorias.append(aux)
        return lista_categorias

    def habilitar_categoria(self, idCompetencia: int, idCategoria: int) -> bool:
        """Habilita una categoria en una competencia (fila nueva en competenciaCategoria).

        Args:
            idCompetencia (int): ID de la competencia.
            idCategoria (int): ID de la categoria a habilitar.

        Returns:
            bool: True si se habilito. False si ya estaba habilitada, si alguna de las dos no existe
            o si ocurre un error.
        """
        cursor = self.conexion.cursor()
        try:
            cursor.execute(
                "INSERT INTO competenciaCategoria (idCompetencia, idCategoria) VALUES (?, ?);",
                (idCompetencia, idCategoria),
            )
            self.conexion.commit()
        except sqlite3.Error as e:
            logger.error(f"Error al habilitar la categoria en la competencia: {e}", exc_info=True)
            return False
        return True

    def obtener_categorias_de_competencia(self, idCompetencia: int) -> list[Categoria]:
        """Devuelve las categorias que juega una competencia, ordenadas por nombre.

        Args:
            idCompetencia (int): ID de la competencia.

        Returns:
            list[Categoria]: Categorias habilitadas en la competencia. Lista vacia si no tiene o si no existe.
        """
        cursor = self.conexion.cursor()
        cursor.execute(
            """
            SELECT c.idCategoria, c.nombre
            FROM categoria c
            JOIN competenciaCategoria cc ON cc.idCategoria = c.idCategoria
            WHERE cc.idCompetencia = ?
            ORDER BY c.nombre;
            """,
            (idCompetencia,),
        )
        return [self._row_to_entity_Categoria(row) for row in cursor.fetchall()]

    def quitar_categoria(self, idCompetencia: int, idCategoria: int) -> bool:
        """Quita una categoria de una competencia.

        Args:
            idCompetencia (int): ID de la competencia.
            idCategoria (int): ID de la categoria a quitar.

        Returns:
            bool: True si estaba habilitada y se quito. False si no estaba habilitada o si ocurre un error
            (por ejemplo, la FK compuesta de inscripcion lo impide si hay clubes inscriptos).
        """
        cursor = self.conexion.cursor()
        try:
            cursor.execute(
                "DELETE FROM competenciaCategoria WHERE idCompetencia = ? AND idCategoria = ?;",
                (idCompetencia, idCategoria),
            )
            self.conexion.commit()
        except sqlite3.Error as e:
            logger.error(f"Error al quitar la categoria de la competencia: {e}", exc_info=True)
            return False
        return cursor.rowcount > 0

    def tiene_inscripciones(self, idCompetencia: int, idCategoria: int) -> bool:
        """Indica si hay clubes inscriptos en una competencia y categoria.

        Args:
            idCompetencia (int): ID de la competencia.
            idCategoria (int): ID de la categoria.

        Returns:
            bool: True si hay al menos una inscripcion.
        """
        cursor = self.conexion.cursor()
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM inscripcion WHERE idCompetencia = ? AND idCategoria = ?);",
            (idCompetencia, idCategoria),
        )
        return bool(cursor.fetchone()[0])

    def guardar_inscripcion(self, inscripcion: Inscripcion) -> Inscripcion | None:
        """Funcion que se encarga de guardar una inscripcion en la base de datos
        Args:
            inscripcion (Inscripcion): Entidad Inscripcion a guardar.

        Returns:
            Inscripcion | None: Retorna la inscripcion guardada con su ID asignado en la BD o None si ocurre un error.
        """
        cursor = self.conexion.cursor()
        try:
            query = """
            INSERT INTO inscripcion (idClub,idCategoria,idCompetencia) VALUES (?, ?, ?);
            """
            cursor.execute(query, (inscripcion.idClub, inscripcion.idCategoria, inscripcion.idCompetencia))
            self.conexion.commit()
            idInscripcion = cursor.lastrowid

        except sqlite3.Error as e:
            logger.error(f"Error al guardar inscripcion: {e}", exc_info=True)
            return None
        try:
            return Inscripcion(
                inscripcion.idClub, inscripcion.idCategoria, inscripcion.idCompetencia, idInscripcion=idInscripcion
            )
        except TypeError as e:
            logger.critical(f"""Inscripcion guardada (idCategoria={idInscripcion})
            pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def inscribir_con_lista(
        self, inscripcion: Inscripcion, fecha_presentacion: str
    ) -> tuple[Inscripcion, ListaBuenaFe] | None:
        """Funcion que se encarga de guardar una inscripcion y su lista de buena fe vacia (relacion 1:1)
        en una unica transaccion atomica.

        Utiliza el context manager de sqlite3, que realiza COMMIT automatico al salir sin error o
        ROLLBACK ante cualquier excepcion. Si falla el guardado de la lista, la inscripcion tampoco
        queda guardada (no pueden existir inscripciones huerfanas, sin su lista).

        Args:
            inscripcion (Inscripcion): Entidad Inscripcion a guardar (sin ID).
            fecha_presentacion (str): Fecha de presentacion de la lista de buena fe.

        Returns:
            tuple[Inscripcion, ListaBuenaFe] | None: Retorna la inscripcion y su lista guardadas, ambas con su
            ID asignado en la BD, o None si ocurre un error.
        """
        try:
            with self.conexion:
                cursor = self.conexion.cursor()
                cursor.execute(
                    "INSERT INTO inscripcion (idClub,idCategoria,idCompetencia) VALUES (?, ?, ?);",
                    (inscripcion.idClub, inscripcion.idCategoria, inscripcion.idCompetencia),
                )
                idInscripcion = cursor.lastrowid
                if idInscripcion is None:
                    raise sqlite3.DatabaseError("SQLite no devolvio el id de la inscripcion recien insertada")

                cursor.execute(
                    "INSERT INTO listaBuenaFe (fechaPresentacion,idInscripcion) VALUES (?,?);",
                    (fecha_presentacion, idInscripcion),
                )
                idListaBuenaFe = cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error al inscribir con lista de buena fe: {e}", exc_info=True)
            return None

        try:
            return (
                Inscripcion(
                    idClub=inscripcion.idClub,
                    idCategoria=inscripcion.idCategoria,
                    idCompetencia=inscripcion.idCompetencia,
                    idInscripcion=idInscripcion,
                ),
                ListaBuenaFe(
                    fechaPresentacion=fecha_presentacion,
                    idInscripcion=idInscripcion,
                    idListaBuenaFe=idListaBuenaFe,
                ),
            )
        except TypeError as e:
            logger.critical(f"""Inscripcion guardada (idInscripcion={idInscripcion})
            pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def buscar_inscripcion_por_id(self, idInscripcion: int) -> Inscripcion | None:
        """Funcion que se encarga de devolver informacion de una inscripcion por ID

        Args:
            idInscripcion (int): ID de la inscripcion a buscar.

        Returns:
            Inscripcion | None: Retorna la inscripcion encontrada o None si no se encuentra.
        """
        cursor = self.conexion.cursor()
        query = "SELECT * FROM inscripcion WHERE idInscripcion = ?;"
        cursor.execute(query, (idInscripcion,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_entity_Inscripciones(row)

    def obtener_inscripciones_por_club(self, idClub: int) -> list[Inscripcion]:
        """Funcion que se encarga de devolver todas las inscripciones de un club

        Args:
            idClub (int): ID del club del cual se desean obtener las inscripciones.

        Returns:
            list[Inscripcion]: Lista de inscripciones del club especificado.
            Retorna una lista vacía si no se encuentran inscripciones.
        """
        cursor = self.conexion.cursor()

        query = "SELECT * FROM club WHERE idClub = ?;"
        cursor.execute(query, (idClub,))
        row = cursor.fetchall()
        if not row:
            return []

        query = "SELECT * FROM inscripcion WHERE idClub = ?;"
        cursor.execute(query, (idClub,))
        row = cursor.fetchall()
        if not row:
            return []
        lista_inscripciones = []
        for r in row:
            aux = self._row_to_entity_Inscripciones(r)
            lista_inscripciones.append(aux)
        return lista_inscripciones

    def guardar_lista_buena_fe(self, listaBF: ListaBuenaFe) -> ListaBuenaFe | None:
        """
        Funcion que se encarga de guardar una lista de buena fe en la base de datos
        Args:
            listaBF (ListaBuenaFe): Entidad ListaBuenaFe a guardar.
        Returns:
            ListaBuenaFe | None: Retorna la lista de buena fe guardada con su ID asignado en la BD
            o None si ocurre un error.
        """
        cursor = self.conexion.cursor()
        try:
            query = """
            INSERT INTO listaBuenaFe (fechaPresentacion,idInscripcion) VALUES (?,?);
            """
            cursor.execute(query, (listaBF.fechaPresentacion, listaBF.idInscripcion))
            self.conexion.commit()
            idListaBuenaFe = cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error al guardar lista de buena fe: {e}", exc_info=True)
            return None

        try:
            return ListaBuenaFe(
                fechaPresentacion=listaBF.fechaPresentacion,
                idInscripcion=listaBF.idInscripcion,
                idListaBuenaFe=idListaBuenaFe,
            )
        except TypeError as e:
            logger.critical(f"""Lista de buena fe guardada (idListaBuenaFe={idListaBuenaFe})
            pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def obtener_lista_por_inscripcion(self, idInscripcion: int) -> ListaBuenaFe | None:
        """Funcion que se encarga de devolver la lista de buena fe de una inscripcion

        Args:
            idInscripcion (int): ID de la inscripcion de la cual se desea obtener la lista de buena fe.

        Returns:
            ListaBuenaFe | None: Retorna la lista de buena fe
            correspondiente a la inscripcion especificada o None si no se encuentra.
        """

        cursor = self.conexion.cursor()

        query = """
        SELECT * FROM inscripcion WHERE idInscripcion = ?;
        """
        cursor.execute(query, (idInscripcion,))
        rows = cursor.fetchone()
        if rows is None:
            return None

        query = """
        SELECT * FROM listaBuenaFe WHERE idInscripcion = ?;
        """
        cursor.execute(query, (idInscripcion,))
        rows = cursor.fetchone()
        if rows is None:
            return None
        return self._row_to_entity_ListaBuenaFe(rows)

    def agregar_jugador_lista(self, idJugador: int, idListaBuenaFe: int) -> JugadorListaBuenaFe | None:
        """Funcion que se encarga de agregar un jugador a una lista de buena fe

        Args:
            idJugador (int): ID del jugador a agregar.
            idListaBuenaFe (int): ID de la lista de buena fe a la cual se desea agregar el jugador.

        Returns:
            JugadorListaBuenaFe | None: Retorna la entidad JugadorListaBuenaFe correspondiente al jugador agregado
            a la lista de buena fe o None si ocurre un error.
        """
        cursor = self.conexion.cursor()
        try:
            query = """
            INSERT INTO jugadorListaBuenaFe (idJugador, idListaBuenaFe)
            VALUES (?, ?);
            """
            cursor.execute(query, (idJugador, idListaBuenaFe))
            self.conexion.commit()

        except sqlite3.Error as e:
            logger.error(f"Error al agregar jugador a la lista: {e}", exc_info=True)
            return None

        try:
            return JugadorListaBuenaFe(
                idJugador=idJugador,
                idListaBuenaFe=idListaBuenaFe,
            )
        except TypeError as e:
            logger.critical(f"""Jugador agregado a la lista pero no se pudo reconstruir el objeto de retorno: {e}""")
            raise

    def obtener_jugadores_lista(self, idListaBuenaFe: int) -> list[JugadorListaBuenaFe]:
        """Funcion que se encarga de devolver todos los jugadores de una lista de buena fe

        Args:
            idListaBuenaFe (int): ID de la lista de buena fe de la cual se desean obtener los jugadores.

        Returns:
            list[JugadorListaBuenaFe]: Lista de entidades JugadorListaBuenaFe
            correspondientes a los jugadores de la lista de buena fe.
        """
        cursor = self.conexion.cursor()
        query = """
            SELECT *
            FROM jugadorListaBuenaFe
            WHERE idListaBuenaFe = ?;
        """
        cursor.execute(query, (idListaBuenaFe,))
        rows = cursor.fetchall()
        if not rows:
            return []

        return [
            JugadorListaBuenaFe(
                idJugador=row["idJugador"],
                idListaBuenaFe=row["idListaBuenaFe"],
            )
            for row in rows
        ]

    def quitar_jugador_lista(self, idJugador: int, idListaBuenaFe: int) -> bool:
        """Funcion que se encarga de quitar a un jugador de una lista de buena fe

        Args:
            idJugador (int): ID del jugador a quitar.
            idListaBuenaFe (int): ID de la lista de buena fe de la cual se lo quiere quitar.

        Returns:
            bool: True si el jugador estaba en la lista y se quito. False si no estaba en la lista
            o si ocurre un error.
        """
        cursor = self.conexion.cursor()
        try:
            cursor.execute(
                "DELETE FROM jugadorListaBuenaFe WHERE idJugador = ? AND idListaBuenaFe = ?;",
                (idJugador, idListaBuenaFe),
            )
            self.conexion.commit()
        except sqlite3.Error as e:
            logger.error(f"Error al quitar jugador de la lista: {e}", exc_info=True)
            return False
        return cursor.rowcount > 0
