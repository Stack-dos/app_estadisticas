from dominio.exceptions import InscripcionNoEncontradaError, ListaBuenaFeNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from utils import id_persistido


class VaciarListaBuenaFeUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Inicializa el caso de uso para quitar todos los jugadores de una lista de buena fe.

        Args:
            repo (CompetenciaRepositorio): Repositorio de inscripciones y listas de buena fe.
        """
        self.repo = repo

    def ejecutar(self, idInscripcion: int) -> int | None:
        """
        Quita todos los jugadores habilitados en la lista de buena fe de una inscripcion, sin dar de baja
        la inscripcion ni desvincular a los jugadores de su club.

        Args:
            idInscripcion (int): ID de la inscripcion cuya lista se vacia.

        Raises:
            InscripcionNoEncontradaError: Si la inscripcion no existe.
            ListaBuenaFeNoEncontradaError: Si la inscripcion no tiene lista (no deberia pasar, es 1:1).

        Returns:
            int | None: Cantidad de jugadores quitados (0 si ya estaba vacia), o None si fallo al borrar.
        """
        if self.repo.buscar_inscripcion_por_id(idInscripcion) is None:
            raise InscripcionNoEncontradaError(f"No existe una inscripcion con idInscripcion={idInscripcion}")

        lista = self.repo.obtener_lista_por_inscripcion(idInscripcion)
        if lista is None:
            raise ListaBuenaFeNoEncontradaError(
                f"La inscripcion (idInscripcion={idInscripcion}) no tiene lista de buena fe"
            )

        id_lista = id_persistido(lista.idListaBuenaFe, "ListaBuenaFe")
        cantidad = len(self.repo.obtener_jugadores_lista(id_lista))
        if cantidad == 0:
            return 0
        if not self.repo.vaciar_lista_buena_fe(id_lista):
            return None
        return cantidad
