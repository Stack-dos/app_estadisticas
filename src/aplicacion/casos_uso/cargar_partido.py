import logging
from dataclasses import fields
from datetime import date

from aplicacion.dtos.partido_dto import BoxscoreDTO, CuartoDTO, EstadisticaInputDTO, PartidoDTO, TotalesEquipoDTO
from dominio.entidades.club import Club
from dominio.entidades.competencia import Inscripcion
from dominio.entidades.jugador import Jugador
from dominio.entidades.partido import (
    ID_CLUB_NUEVO,
    MAX_JUGADORES_PARTIDO,
    AltaPlantelRival,
    EstadisticaEquipo,
    JugadorPartido,
    JugadorRivalNuevo,
    Partido,
    PartidoCuarto,
)
from dominio.exceptions import (
    CuartosInconsistentesError,
    DatoInvalidoError,
    InscripcionNoEncontradaError,
    JugadorNoEstaEnListaError,
    JugadorNoPerteneceAlClubError,
    ListaBuenaFeNoEncontradaError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from dominio.repositorios.partido_repositorio import PartidoRepositorio
from utils import id_persistido, normalizar_texto

# Campos numericos de EstadisticaInputDTO que pasan tal cual a JugadorPartido (todo menos la identidad).
_CAMPOS_IDENTIDAD = {"idJugador", "nombre", "apellido"}
_CAMPOS_ESTADISTICA = tuple(f.name for f in fields(EstadisticaInputDTO) if f.name not in _CAMPOS_IDENTIDAD)


def _clave_nombre(nombre: str, apellido: str) -> str:
    """Clave para reconocer a un jugador por nombre y apellido, sin tildes ni mayusculas."""
    return f"{normalizar_texto(nombre)}|{normalizar_texto(apellido)}"


# logging de la biblioteca estandar: el correlation_id lo agrega el handler (US-110).
logger = logging.getLogger(__name__)


class CargarPartidoUseCase:
    """Registra un partido del club propio contra un rival, de forma atomica (US-108, rediseñado en US-113).

    - El club propio carga su boxscore por jugador: el club tiene que estar inscripto en la competencia y
      categoria, y cada jugador tiene que estar en su lista de buena fe.
    - El rival se carga de una de dos formas: con su boxscore por jugador (si se tiene la planilla) o solo
      con sus totales de equipo (o solo el resultado). Si se carga su boxscore, lo que le falte se da de alta
      solo: su inscripcion y lista, y los jugadores que todavia no existian en el club rival.

    US-114:
    - Con `partido_dto.idPartido` reemplaza ese partido (edicion) con las mismas validaciones.
    - Con `nombre_rival_nuevo` el rival no existe todavia: su id en el partido y en `rival` es `ID_CLUB_NUEVO`
      y el club se crea en la misma transaccion del partido (si algo falla, no queda un club suelto).
    - Hasta `MAX_JUGADORES_PARTIDO` jugadores por equipo, y no hay empates.
    """

    def __init__(
        self,
        repo_partido: PartidoRepositorio,
        repo_competencia: CompetenciaRepositorio,
        repo_jugador: JugadorRepositorio,
    ):
        self.repo_partido = repo_partido
        self.repo_competencia = repo_competencia
        self.repo_jugador = repo_jugador

    def ejecutar(
        self,
        partido_dto: PartidoDTO,
        boxscore_propio: BoxscoreDTO,
        rival: BoxscoreDTO | TotalesEquipoDTO,
        nombre_rival_nuevo: str | None = None,
    ) -> PartidoDTO | None:
        """Valida todo y guarda partido, boxscores, totales del rival, cuartos y alta del rival en una transaccion.

        Args:
            partido_dto (PartidoDTO): Datos del partido (competencia, categoria, clubes, fecha, estadio, cuartos).
            boxscore_propio (BoxscoreDTO): Estadisticas por jugador del club propio (local o visitante).
            rival (BoxscoreDTO | TotalesEquipoDTO): El otro club: su boxscore por jugador o sus totales.
            nombre_rival_nuevo (str | None): Nombre del club rival si todavia no existe (su id es `ID_CLUB_NUEVO`).

        Raises:
            DatoInvalidoError: Fecha invalida, clubes repetidos o que no juegan el partido, boxscore vacio,
                mas de 12 jugadores, jugadores repetidos, estadisticas incoherentes o empate.
            InscripcionNoEncontradaError: Si el club propio no esta inscripto en esa competencia y categoria.
            JugadorNoEstaEnListaError: Si un jugador propio no esta en la lista de buena fe.
            JugadorNoPerteneceAlClubError: Si se manda un jugador rival por id que no es del club rival.
            CuartosInconsistentesError: Si los puntos por cuarto no cierran con el total de cada equipo.

        Returns:
            PartidoDTO | None: DTO del partido guardado con su `idPartido`, o None si fallo la persistencia.
        """
        self._validar_fecha(partido_dto.fecha)
        id_local, id_visitante = partido_dto.idClubLocal, partido_dto.idClubVisitante
        if id_local == id_visitante:
            raise DatoInvalidoError("El club local y el club visitante no pueden ser el mismo.")
        clubes_del_partido = {id_local, id_visitante}
        if boxscore_propio.idClub not in clubes_del_partido:
            raise DatoInvalidoError(
                f"El boxscore propio (idClub={boxscore_propio.idClub}) no es de ninguno de los clubes del partido."
            )
        if rival.idClub not in clubes_del_partido or rival.idClub == boxscore_propio.idClub:
            raise DatoInvalidoError(
                f"El rival (idClub={rival.idClub}) tiene que ser el otro club del partido, no el propio."
            )
        club_nuevo = self._club_rival_nuevo(rival.idClub, nombre_rival_nuevo)

        partido = Partido(
            fecha=partido_dto.fecha,
            estadio=partido_dto.estadio,
            idCompetencia=partido_dto.idCompetencia,
            idCategoria=partido_dto.idCategoria,
            idClubLocal=id_local,
            idClubVisitante=id_visitante,
            idPartido=partido_dto.idPartido,
        )

        filas_propias = self._validar_boxscore_propio(boxscore_propio, partido)
        puntos_por_club = {boxscore_propio.idClub: sum(f.puntos for f in filas_propias)}

        totales: list[EstadisticaEquipo] = []
        alta_rival: AltaPlantelRival | None = None
        filas_rival: list[JugadorPartido] = []
        if isinstance(rival, TotalesEquipoDTO):
            tot = EstadisticaEquipo(**{f.name: getattr(rival, f.name) for f in fields(TotalesEquipoDTO)})
            totales.append(tot)
            puntos_por_club[rival.idClub] = tot.puntos
        else:
            filas_rival, alta_rival = self._preparar_boxscore_rival(rival, partido)
            nuevos = alta_rival.nuevos if alta_rival is not None else []
            puntos_por_club[rival.idClub] = sum(f.puntos for f in filas_rival) + sum(
                n.estadistica.puntos for n in nuevos
            )

        if puntos_por_club[id_local] == puntos_por_club[id_visitante]:
            raise DatoInvalidoError(
                f"En básquet no hay empates: los dos equipos tienen {puntos_por_club[id_local]} puntos. "
                "Revisá los puntos (si hubo prórroga, va sumada)."
            )

        cuartos = self._validar_y_construir_cuartos(
            cuartos_dto=partido_dto.cuartos,
            id_local=id_local,
            id_visitante=id_visitante,
            puntos_local=puntos_por_club[id_local],
            puntos_visitante=puntos_por_club[id_visitante],
        )

        edicion = partido_dto.idPartido is not None
        logger.info(
            "Inicio de la transaccion del partido", extra={"evento": "partido_transaccion_inicio", "edicion": edicion}
        )
        guardado = self.repo_partido.save_with_boxscore(
            partido=partido,
            boxscore=[*filas_propias, *filas_rival],
            cuartos=cuartos or None,
            totales=totales or None,
            alta_rival=alta_rival,
            club_rival_nuevo=club_nuevo,
        )
        if guardado is None:
            logger.error("La transaccion del partido fallo", extra={"evento": "partido_transaccion_fin", "ok": False})
            return None

        partido_guardado, _ = guardado
        logger.info(
            "Partido actualizado" if edicion else "Partido creado",
            extra={
                "evento": "partido_transaccion_fin",
                "ok": True,
                "id_partido": partido_guardado.idPartido,
                "edicion": edicion,
            },
        )
        return PartidoDTO(
            fecha=partido_guardado.fecha,
            estadio=partido_guardado.estadio,
            idCompetencia=partido_guardado.idCompetencia,
            idCategoria=partido_guardado.idCategoria,
            idClubLocal=partido_guardado.idClubLocal,
            idClubVisitante=partido_guardado.idClubVisitante,
            cuartos=list(partido_dto.cuartos),
            idPartido=id_persistido(partido_guardado.idPartido, "Partido"),
        )

    @staticmethod
    def _club_rival_nuevo(id_rival: int, nombre: str | None) -> Club | None:
        """El club rival a crear, o None si ya existe. El id provisorio y el nombre tienen que venir juntos."""
        if nombre is None:
            if id_rival == ID_CLUB_NUEVO:
                raise DatoInvalidoError("Falta el nombre del club rival nuevo.")
            return None
        if id_rival != ID_CLUB_NUEVO:
            raise DatoInvalidoError("Un rival nuevo no puede venir con el id de un club que ya existe.")
        return Club(nombre=nombre.strip())  # valida que no este vacio

    @staticmethod
    def _validar_cantidad(estadisticas: list[EstadisticaInputDTO], equipo: str) -> None:
        if len(estadisticas) > MAX_JUGADORES_PARTIDO:
            raise DatoInvalidoError(
                f"En un partido entran hasta {MAX_JUGADORES_PARTIDO} jugadores por equipo: "
                f"{equipo} tiene {len(estadisticas)} con estadísticas."
            )

    @staticmethod
    def _validar_fecha(fecha: str) -> None:
        try:
            date.fromisoformat(fecha.strip())
        except ValueError as err:
            raise DatoInvalidoError(
                f"La fecha del partido tiene que tener formato AAAA-MM-DD (recibido: '{fecha}')."
            ) from err

    @staticmethod
    def _fila(est: EstadisticaInputDTO, id_jugador: int, id_club: int) -> JugadorPartido:
        """Convierte la estadistica de entrada en la entidad que valida las reglas del boxscore."""
        return JugadorPartido(
            idJugador=id_jugador,
            idPartido=0,
            idClub=id_club,
            **{c: getattr(est, c) for c in _CAMPOS_ESTADISTICA},
        )

    def _buscar_inscripcion(self, id_club: int, partido: Partido) -> Inscripcion | None:
        return next(
            (
                i
                for i in self.repo_competencia.obtener_inscripciones_por_club(id_club)
                if i.idCompetencia == partido.idCompetencia and i.idCategoria == partido.idCategoria
            ),
            None,
        )

    def _ids_en_lista(self, id_inscripcion: int, id_club: int) -> tuple[int, set[int]]:
        lista = self.repo_competencia.obtener_lista_por_inscripcion(id_inscripcion)
        if lista is None:
            raise ListaBuenaFeNoEncontradaError(
                f"La inscripcion del club (idClub={id_club}) no tiene lista de buena fe."
            )
        id_lista = id_persistido(lista.idListaBuenaFe, "ListaBuenaFe")
        return id_lista, {j.idJugador for j in self.repo_competencia.obtener_jugadores_lista(id_lista)}

    def _validar_boxscore_propio(self, boxscore: BoxscoreDTO, partido: Partido) -> list[JugadorPartido]:
        """El club propio: inscripto, con lista, y cada jugador habilitado en ella."""
        if not boxscore.estadisticas:
            raise DatoInvalidoError("Cargá al menos un jugador de tu equipo en el boxscore.")
        self._validar_cantidad(boxscore.estadisticas, "tu equipo")
        inscripcion = self._buscar_inscripcion(boxscore.idClub, partido)
        if inscripcion is None:
            raise InscripcionNoEncontradaError(
                f"Tu club (idClub={boxscore.idClub}) no esta inscripto en la competencia {partido.idCompetencia} "
                f"y categoria {partido.idCategoria}. Inscribilo en Torneos > Inscripciones."
            )
        _, habilitados = self._ids_en_lista(id_persistido(inscripcion.idInscripcion, "Inscripcion"), boxscore.idClub)

        vistos: set[int] = set()
        filas: list[JugadorPartido] = []
        for est in boxscore.estadisticas:
            if est.idJugador is None:
                raise DatoInvalidoError("Cada jugador de tu equipo tiene que venir de tu lista de buena fe.")
            if est.idJugador in vistos:
                raise DatoInvalidoError(f"El jugador idJugador={est.idJugador} aparece repetido en tu boxscore.")
            vistos.add(est.idJugador)
            if est.idJugador not in habilitados:
                raise JugadorNoEstaEnListaError(
                    f"El jugador idJugador={est.idJugador} de tu equipo (idClub={boxscore.idClub}) "
                    "no esta en la lista de buena fe de esa competencia y categoria."
                )
            filas.append(self._fila(est, est.idJugador, boxscore.idClub))
        return filas

    def _preparar_boxscore_rival(
        self, boxscore: BoxscoreDTO, partido: Partido
    ) -> tuple[list[JugadorPartido], AltaPlantelRival | None]:
        """Resuelve cada jugador rival (existente o nuevo) y arma lo que haya que dar de alta.

        Returns:
            tuple: Las filas de jugadores rivales que ya existen, y el alta (None si no hay nada que crear).
        """
        if not boxscore.estadisticas:
            raise DatoInvalidoError("Cargá al menos un jugador del rival, o cargá solo sus totales.")
        self._validar_cantidad(boxscore.estadisticas, "el rival")
        id_club = boxscore.idClub
        inscripcion = self._buscar_inscripcion(id_club, partido)
        id_lista: int | None = None
        habilitados: set[int] = set()
        if inscripcion is not None:
            id_lista, habilitados = self._ids_en_lista(id_persistido(inscripcion.idInscripcion, "Inscripcion"), id_club)

        plantel = self.repo_jugador.buscar_por_club(id_club) or []
        ids_plantel = {id_persistido(j.idJugador, "Jugador") for j in plantel}
        por_nombre = {_clave_nombre(j.nombre, j.apellido): id_persistido(j.idJugador, "Jugador") for j in plantel}

        filas: list[JugadorPartido] = []
        habilitar: list[int] = []
        nuevos: list[JugadorRivalNuevo] = []
        vistos_id: set[int] = set()
        vistos_nombre: set[str] = set()
        for est in boxscore.estadisticas:
            id_jugador = est.idJugador
            if id_jugador is None:
                jugador = Jugador(nombre=est.nombre.strip(), apellido=est.apellido.strip())  # valida nombre y apellido
                clave = _clave_nombre(jugador.nombre, jugador.apellido)
                if clave in vistos_nombre:
                    raise DatoInvalidoError(f"{jugador.nombre_completo} aparece dos veces en el boxscore del rival.")
                vistos_nombre.add(clave)
                id_jugador = por_nombre.get(clave)
                if id_jugador is None:
                    nuevos.append(JugadorRivalNuevo(jugador=jugador, estadistica=self._fila(est, 0, id_club)))
                    continue
            elif id_jugador not in ids_plantel and id_jugador not in habilitados:
                raise JugadorNoPerteneceAlClubError(
                    f"El jugador idJugador={id_jugador} no es del club rival (idClub={id_club})."
                )
            if id_jugador in vistos_id:
                raise DatoInvalidoError(f"El jugador idJugador={id_jugador} aparece repetido en el boxscore del rival.")
            vistos_id.add(id_jugador)
            if id_jugador not in habilitados:
                habilitar.append(id_jugador)
            filas.append(self._fila(est, id_jugador, id_club))

        if id_lista is not None and not habilitar and not nuevos:
            return filas, None
        alta = AltaPlantelRival(
            idClub=id_club,
            idCompetencia=partido.idCompetencia,
            idCategoria=partido.idCategoria,
            fecha=partido.fecha,
            idListaBuenaFe=id_lista,
            habilitar=habilitar,
            nuevos=nuevos,
        )
        return filas, alta

    def _validar_y_construir_cuartos(
        self,
        cuartos_dto: list[CuartoDTO],
        id_local: int,
        id_visitante: int,
        puntos_local: int,
        puntos_visitante: int,
    ) -> list[PartidoCuarto]:
        """Valida consistencia de puntos por cuarto entre ambos equipos y contra el total de cada uno (AC7)."""
        if not cuartos_dto:
            return []

        entidades = [PartidoCuarto(idClub=c.idClub, nroCuarto=c.nroCuarto, puntos=c.puntos) for c in cuartos_dto]

        por_club: dict[int, dict[int, int]] = {id_local: {}, id_visitante: {}}
        for c in entidades:
            if c.idClub not in por_club:
                raise CuartosInconsistentesError(
                    f"Los cuartos incluyen un club (idClub={c.idClub}) que no juega este partido."
                )
            if c.nroCuarto in por_club[c.idClub]:
                raise CuartosInconsistentesError(
                    f"El periodo {c.nroCuarto} esta repetido para el club idClub={c.idClub}."
                )
            por_club[c.idClub][c.nroCuarto] = c.puntos

        if not por_club[id_local]:
            raise CuartosInconsistentesError(f"Faltan los puntos por cuarto del equipo local (idClub={id_local}).")
        if not por_club[id_visitante]:
            raise CuartosInconsistentesError(
                f"Faltan los puntos por cuarto del equipo visitante (idClub={id_visitante})."
            )

        periodos_local = sorted(por_club[id_local].keys())
        periodos_visitante = sorted(por_club[id_visitante].keys())
        if periodos_local != periodos_visitante:
            raise CuartosInconsistentesError(
                f"Los equipos tienen distinta cantidad o numeracion de periodos: "
                f"local={periodos_local}, visitante={periodos_visitante}."
            )

        esperados = list(range(1, len(periodos_local) + 1))
        if periodos_local != esperados:
            raise CuartosInconsistentesError(
                f"Los numeros de periodo deben ser consecutivos desde 1 (recibidos: {periodos_local})."
            )

        self._verificar_suma_cuartos("local", id_local, sum(por_club[id_local].values()), puntos_local)
        self._verificar_suma_cuartos("visitante", id_visitante, sum(por_club[id_visitante].values()), puntos_visitante)
        return entidades

    @staticmethod
    def _verificar_suma_cuartos(rol_equipo: str, id_club: int, suma_cuartos: int, puntos_total: int) -> None:
        if suma_cuartos == puntos_total:
            return
        diferencia = suma_cuartos - puntos_total
        detalle = f"sobran {diferencia}" if diferencia > 0 else f"faltan {-diferencia}"
        raise CuartosInconsistentesError(
            f"La suma de cuartos del equipo {rol_equipo} (idClub={id_club}) es {suma_cuartos}, "
            f"pero su total es {puntos_total} ({detalle} puntos)."
        )
