from aplicacion.dtos.lista_buena_fe_dto import AgregarJugadorListaDTO, JugadorEnListaDTO
from dominio.exceptions import (
    InscripcionNoEncontradaError,
    JugadorNoEncontradoError,
    JugadorNoPerteneceAlClubError,
    JugadorYaEnListaError,
    ListaBuenaFeNoEncontradaError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from utils import id_persistido


class AgregarJugadorAListaBuenaFeUseCase:
    def __init__(self, repo_competencia: CompetenciaRepositorio, repo_jugador: JugadorRepositorio):
        """
        Funcion que permite inicializar el caso de uso de habilitar un jugador en una lista de buena fe
        Args:
            repo_competencia (CompetenciaRepositorio): Repositorio de inscripciones y listas de buena fe
            repo_jugador (JugadorRepositorio): Repositorio de jugadores, para verificar que exista y su club activo
        """
        self.repo_competencia = repo_competencia
        self.repo_jugador = repo_jugador

    def ejecutar(self, dto: AgregarJugadorListaDTO) -> JugadorEnListaDTO | None:
        """
        Funcion que permite habilitar a un jugador en la lista de buena fe de una inscripcion. Solo los
        jugadores habilitados en la lista pueden figurar en la carga oficial de un partido.

        Args:
            dto (AgregarJugadorListaDTO): DTO con la inscripcion y el jugador a habilitar

        Raises:
            InscripcionNoEncontradaError: Si la inscripcion no existe.
            ListaBuenaFeNoEncontradaError: Si la inscripcion no tiene lista (no deberia pasar, es 1:1).
            JugadorNoEncontradoError: Si el jugador no existe.
            JugadorNoPerteneceAlClubError: Si el jugador no tiene un vinculo vigente con el club de la inscripcion.
            JugadorYaEnListaError: Si el jugador ya esta en la lista.

        Returns:
            JugadorEnListaDTO | None: DTO que confirma la habilitacion, o None si no se pudo guardar
        """
        inscripcion = self.repo_competencia.buscar_inscripcion_por_id(dto.idInscripcion)
        if inscripcion is None:
            raise InscripcionNoEncontradaError(f"No existe una inscripcion con idInscripcion={dto.idInscripcion}")

        lista = self.repo_competencia.obtener_lista_por_inscripcion(dto.idInscripcion)
        if lista is None:
            raise ListaBuenaFeNoEncontradaError(
                f"La inscripcion (idInscripcion={dto.idInscripcion}) no tiene lista de buena fe"
            )
        id_lista = id_persistido(lista.idListaBuenaFe, "ListaBuenaFe")

        if self.repo_jugador.buscar_por_id(dto.idJugador) is None:
            raise JugadorNoEncontradoError(f"No existe un jugador con idJugador={dto.idJugador}")

        club_actual = self.repo_jugador.club_activo(dto.idJugador)
        if club_actual is None or club_actual.idClub != inscripcion.idClub:
            raise JugadorNoPerteneceAlClubError(
                f"El jugador (idJugador={dto.idJugador}) no tiene un vinculo vigente con el club de la inscripcion "
                f"(idClub={inscripcion.idClub})"
            )

        if any(j.idJugador == dto.idJugador for j in self.repo_competencia.obtener_jugadores_lista(id_lista)):
            raise JugadorYaEnListaError(
                f"El jugador (idJugador={dto.idJugador}) ya esta en la lista de buena fe (idListaBuenaFe={id_lista})"
            )

        resultado = self.repo_competencia.agregar_jugador_lista(dto.idJugador, id_lista)
        if resultado is None:
            return None
        return JugadorEnListaDTO(
            idListaBuenaFe=resultado.idListaBuenaFe, idInscripcion=dto.idInscripcion, idJugador=resultado.idJugador
        )
