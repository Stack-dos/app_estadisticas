from aplicacion.dtos.partido_dto import BoxscoreDTO, CuartoDTO, PartidoDTO
from dominio.entidades.partido import JugadorPartido, Partido, PartidoCuarto
from dominio.exceptions import (
    CuartosInconsistentesError,
    DatoInvalidoError,
    InscripcionNoEncontradaError,
    JugadorNoEstaEnListaError,
    ListaBuenaFeNoEncontradaError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from dominio.repositorios.partido_repositorio import PartidoRepositorio
from utils import id_persistido


class CargarPartidoUseCase:
    """Registra un partido con los boxscores de ambos equipos y cuartos opcionales de forma atomica (US-108)."""

    def __init__(
        self,
        repo_partido: PartidoRepositorio,
        repo_competencia: CompetenciaRepositorio,
    ):
        self.repo_partido = repo_partido
        self.repo_competencia = repo_competencia

    def ejecutar(
        self,
        partido_dto: PartidoDTO,
        boxscore_local: BoxscoreDTO,
        boxscore_visitante: BoxscoreDTO,
    ) -> PartidoDTO | None:
        """Valida listas de buena fe, estadisticas y cuartos antes de persistir todo en una transaccion.

        Args:
            partido_dto (PartidoDTO): Datos del partido (competencia, categoria, clubes, fecha, estadio, cuartos).
            boxscore_local (BoxscoreDTO): Estadisticas individuales del equipo local.
            boxscore_visitante (BoxscoreDTO): Estadisticas individuales del equipo visitante.

        Returns:
            PartidoDTO | None: DTO del partido guardado con su `idPartido`, o None si fallo la persistencia.
        """
        if partido_dto.idClubLocal == partido_dto.idClubVisitante:
            raise DatoInvalidoError("El club local y el club visitante no pueden ser el mismo.")
        if boxscore_local.idClub != partido_dto.idClubLocal:
            raise DatoInvalidoError(
                f"El boxscore local (idClub={boxscore_local.idClub}) no coincide con el club local "
                f"(idClub={partido_dto.idClubLocal})."
            )
        if boxscore_visitante.idClub != partido_dto.idClubVisitante:
            raise DatoInvalidoError(
                f"El boxscore visitante (idClub={boxscore_visitante.idClub}) no coincide con el club visitante "
                f"(idClub={partido_dto.idClubVisitante})."
            )

        partido = Partido(
            fecha=partido_dto.fecha,
            estadio=partido_dto.estadio,
            idCompetencia=partido_dto.idCompetencia,
            idCategoria=partido_dto.idCategoria,
            idClubLocal=partido_dto.idClubLocal,
            idClubVisitante=partido_dto.idClubVisitante,
        )

        filas_local = self._validar_y_construir_boxscore(
            boxscore=boxscore_local,
            rol_equipo="local",
            id_competencia=partido.idCompetencia,
            id_categoria=partido.idCategoria,
        )
        filas_visitante = self._validar_y_construir_boxscore(
            boxscore=boxscore_visitante,
            rol_equipo="visitante",
            id_competencia=partido.idCompetencia,
            id_categoria=partido.idCategoria,
        )

        puntos_local = sum(f.puntos for f in filas_local)
        puntos_visitante = sum(f.puntos for f in filas_visitante)
        cuartos = self._validar_y_construir_cuartos(
            cuartos_dto=partido_dto.cuartos,
            id_local=partido.idClubLocal,
            id_visitante=partido.idClubVisitante,
            puntos_local=puntos_local,
            puntos_visitante=puntos_visitante,
        )

        guardado = self.repo_partido.save_with_boxscore(
            partido=partido,
            boxscore=[*filas_local, *filas_visitante],
            cuartos=cuartos or None,
        )
        if guardado is None:
            return None

        partido_guardado, _ = guardado
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

    def _validar_y_construir_boxscore(
        self,
        boxscore: BoxscoreDTO,
        rol_equipo: str,
        id_competencia: int,
        id_categoria: int,
    ) -> list[JugadorPartido]:
        """Valida que el club este inscripto y que cada jugador del boxscore pertenezca a su lista de buena fe."""
        inscripciones = self.repo_competencia.obtener_inscripciones_por_club(boxscore.idClub)
        inscripcion = next(
            (i for i in inscripciones if i.idCompetencia == id_competencia and i.idCategoria == id_categoria),
            None,
        )
        if inscripcion is None:
            raise InscripcionNoEncontradaError(
                f"El equipo {rol_equipo} (idClub={boxscore.idClub}) no esta inscripto en la competencia "
                f"{id_competencia} y categoria {id_categoria}."
            )

        id_inscripcion = id_persistido(inscripcion.idInscripcion, "Inscripcion")
        lista = self.repo_competencia.obtener_lista_por_inscripcion(id_inscripcion)
        if lista is None:
            raise ListaBuenaFeNoEncontradaError(
                f"La inscripcion del equipo {rol_equipo} (idClub={boxscore.idClub}) no tiene lista de buena fe."
            )

        id_lista = id_persistido(lista.idListaBuenaFe, "ListaBuenaFe")
        habilitados = {j.idJugador for j in self.repo_competencia.obtener_jugadores_lista(id_lista)}

        vistos: set[int] = set()
        filas: list[JugadorPartido] = []
        for est in boxscore.estadisticas:
            if est.idJugador in vistos:
                raise DatoInvalidoError(
                    f"El jugador idJugador={est.idJugador} aparece repetido en el boxscore del equipo {rol_equipo}."
                )
            vistos.add(est.idJugador)

            if est.idJugador not in habilitados:
                raise JugadorNoEstaEnListaError(
                    f"El jugador idJugador={est.idJugador} del equipo {rol_equipo} (idClub={boxscore.idClub}) "
                    "no esta en la lista de buena fe de esa competencia y categoria."
                )

            filas.append(
                JugadorPartido(
                    idJugador=est.idJugador,
                    idPartido=0,
                    idClub=boxscore.idClub,
                    minutosJugados=est.minutosJugados,
                    puntos=est.puntos,
                    t2c=est.t2c,
                    t2l=est.t2l,
                    t3c=est.t3c,
                    t3l=est.t3l,
                    t1c=est.t1c,
                    t1l=est.t1l,
                    rebotesDef=est.rebotesDef,
                    rebotesOf=est.rebotesOf,
                    asistencias=est.asistencias,
                    recuperos=est.recuperos,
                    perdidas=est.perdidas,
                    taponesRecibidos=est.taponesRecibidos,
                    taponesRealizados=est.taponesRealizados,
                    faltasRecibidas=est.faltasRecibidas,
                    faltasCometidas=est.faltasCometidas,
                )
            )
        return filas

    def _validar_y_construir_cuartos(
        self,
        cuartos_dto: list[CuartoDTO],
        id_local: int,
        id_visitante: int,
        puntos_local: int,
        puntos_visitante: int,
    ) -> list[PartidoCuarto]:
        """Valida consistencia de puntos por cuarto entre ambos equipos y contra el total del boxscore (AC7)."""
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
    def _verificar_suma_cuartos(rol_equipo: str, id_club: int, suma_cuartos: int, puntos_boxscore: int) -> None:
        if suma_cuartos == puntos_boxscore:
            return
        diferencia = suma_cuartos - puntos_boxscore
        detalle = f"sobran {diferencia}" if diferencia > 0 else f"faltan {-diferencia}"
        raise CuartosInconsistentesError(
            f"La suma de cuartos del equipo {rol_equipo} (idClub={id_club}) es {suma_cuartos}, "
            f"pero su boxscore suma {puntos_boxscore} ({detalle} puntos)."
        )
