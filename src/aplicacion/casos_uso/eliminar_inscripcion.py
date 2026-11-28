from dominio.exceptions import InscripcionEnUsoError, InscripcionNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


class EliminarInscripcionUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Inicializa el caso de uso para dar de baja una inscripcion (y su lista de buena fe 1:1).

        Args:
            repo (CompetenciaRepositorio): Repositorio de inscripciones y listas.
        """
        self.repo = repo

    def ejecutar(self, idInscripcion: int) -> bool:
        """
        Elimina una inscripcion (y en cascada su lista de buena fe) siempre que el club no tenga partidos
        cargados en esa competencia.

        Args:
            idInscripcion (int): ID de la inscripcion a dar de baja.

        Raises:
            InscripcionNoEncontradaError: Si la inscripcion no existe.
            InscripcionEnUsoError: Si el club ya tiene partidos cargados en esa competencia.

        Returns:
            bool: True si se dio de baja correctamente, False si fallo en el repositorio.
        """
        if self.repo.buscar_inscripcion_por_id(idInscripcion) is None:
            raise InscripcionNoEncontradaError(f"No existe una inscripcion con idInscripcion={idInscripcion}")

        if self.repo.inscripcion_tiene_partidos(idInscripcion):
            raise InscripcionEnUsoError(
                f"No se puede dar de baja la inscripcion (idInscripcion={idInscripcion}) porque el club "
                "ya tiene partidos cargados en esa competencia"
            )

        return self.repo.eliminar_inscripcion(idInscripcion)
