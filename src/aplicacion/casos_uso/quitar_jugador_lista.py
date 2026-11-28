from aplicacion.dtos.lista_buena_fe_dto import JugadorEnListaDTO, QuitarJugadorListaDTO
from dominio.exceptions import InscripcionNoEncontradaError, JugadorNoEstaEnListaError, ListaBuenaFeNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from utils import id_persistido


class QuitarJugadorDeListaBuenaFeUseCase:
    def __init__(self, repo_competencia: CompetenciaRepositorio):
        """
        Funcion que permite inicializar el caso de uso de quitar un jugador de una lista de buena fe
        Args:
            repo_competencia (CompetenciaRepositorio): Repositorio de inscripciones y listas de buena fe
        """
        self.repo_competencia = repo_competencia

    def ejecutar(self, dto: QuitarJugadorListaDTO) -> JugadorEnListaDTO | None:
        """
        Funcion que permite quitar a un jugador de la lista de buena fe de una inscripcion (por ejemplo, para
        deshacer una habilitacion hecha por error). Quitarlo de la lista no lo desvincula de su club.

        Args:
            dto (QuitarJugadorListaDTO): DTO con la inscripcion y el jugador a quitar

        Raises:
            InscripcionNoEncontradaError: Si la inscripcion no existe.
            ListaBuenaFeNoEncontradaError: Si la inscripcion no tiene lista (no deberia pasar, es 1:1).
            JugadorNoEstaEnListaError: Si el jugador no esta en la lista.

        Returns:
            JugadorEnListaDTO | None: DTO con el jugador que se quito (y de que lista), o None si no se pudo borrar
        """
        if self.repo_competencia.buscar_inscripcion_por_id(dto.idInscripcion) is None:
            raise InscripcionNoEncontradaError(f"No existe una inscripcion con idInscripcion={dto.idInscripcion}")

        lista = self.repo_competencia.obtener_lista_por_inscripcion(dto.idInscripcion)
        if lista is None:
            raise ListaBuenaFeNoEncontradaError(
                f"La inscripcion (idInscripcion={dto.idInscripcion}) no tiene lista de buena fe"
            )
        id_lista = id_persistido(lista.idListaBuenaFe, "ListaBuenaFe")

        if not any(j.idJugador == dto.idJugador for j in self.repo_competencia.obtener_jugadores_lista(id_lista)):
            raise JugadorNoEstaEnListaError(
                f"El jugador (idJugador={dto.idJugador}) no esta en la lista de buena fe (idListaBuenaFe={id_lista})"
            )

        if not self.repo_competencia.quitar_jugador_lista(dto.idJugador, id_lista):
            return None
        return JugadorEnListaDTO(idListaBuenaFe=id_lista, idInscripcion=dto.idInscripcion, idJugador=dto.idJugador)
