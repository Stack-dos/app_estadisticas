from aplicacion.dtos.jugador_dto import JugadorDTO
from dominio.exceptions import InscripcionNoEncontradaError, JugadorNoEncontradoError, ListaBuenaFeNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from utils import id_persistido


class ListarListaBuenaFeUseCase:
    def __init__(self, repo_competencia: CompetenciaRepositorio, repo_jugador: JugadorRepositorio):
        """
        Funcion que permite inicializar el caso de uso de listar los jugadores de una lista de buena fe
        Args:
            repo_competencia (CompetenciaRepositorio): Repositorio de inscripciones y listas de buena fe
            repo_jugador (JugadorRepositorio): Repositorio de jugadores, para obtener sus nombres
        """
        self.repo_competencia = repo_competencia
        self.repo_jugador = repo_jugador

    def ejecutar(self, idInscripcion: int) -> list[JugadorDTO]:
        """
        Funcion que permite listar los jugadores habilitados en la lista de buena fe de una inscripcion

        Args:
            idInscripcion (int): ID de la inscripcion cuya lista se quiere ver

        Raises:
            InscripcionNoEncontradaError: Si la inscripcion no existe.
            ListaBuenaFeNoEncontradaError: Si la inscripcion no tiene lista (no deberia pasar, es 1:1).
            JugadorNoEncontradoError: Si un jugador de la lista no existe (inconsistencia de datos).

        Returns:
            list[JugadorDTO]: Jugadores habilitados. Lista vacia si todavia no se habilito a nadie.
        """
        if self.repo_competencia.buscar_inscripcion_por_id(idInscripcion) is None:
            raise InscripcionNoEncontradaError(f"No existe una inscripcion con idInscripcion={idInscripcion}")

        lista = self.repo_competencia.obtener_lista_por_inscripcion(idInscripcion)
        if lista is None:
            raise ListaBuenaFeNoEncontradaError(
                f"La inscripcion (idInscripcion={idInscripcion}) no tiene lista de buena fe"
            )

        resultado = []
        for habilitado in self.repo_competencia.obtener_jugadores_lista(
            id_persistido(lista.idListaBuenaFe, "ListaBuenaFe")
        ):
            jugador = self.repo_jugador.buscar_por_id(habilitado.idJugador)
            if jugador is None:
                raise JugadorNoEncontradoError(f"No existe un jugador con idJugador={habilitado.idJugador}")
            resultado.append(
                JugadorDTO(
                    nombre_completo=jugador.nombre_completo,
                    id=id_persistido(jugador.idJugador, "Jugador"),
                    anioNacimiento=jugador.anioNacimiento,
                )
            )
        return resultado
