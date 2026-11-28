from dominio.exceptions import CompetenciaEnUsoError, CompetenciaNoEncontradaError
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


class EliminarCompetenciaUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Inicializa el caso de uso para eliminar una competencia.

        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias.
        """
        self.repo = repo

    def ejecutar(self, idCompetencia: int) -> bool:
        """
        Elimina una competencia siempre que no tenga clubes inscriptos ni partidos cargados.

        Args:
            idCompetencia (int): ID de la competencia a eliminar.

        Raises:
            CompetenciaNoEncontradaError: Si la competencia no existe.
            CompetenciaEnUsoError: Si la competencia tiene inscripciones o partidos asociados.

        Returns:
            bool: True si se elimino correctamente, False si fallo al borrar en el repositorio.
        """
        if self.repo.buscar_competencia_por_id(idCompetencia) is None:
            raise CompetenciaNoEncontradaError(f"No existe una competencia con idCompetencia={idCompetencia}")

        if self.repo.competencia_tiene_inscripciones(idCompetencia):
            raise CompetenciaEnUsoError(
                f"No se puede eliminar la competencia (idCompetencia={idCompetencia}) porque tiene clubes inscriptos"
            )

        if self.repo.competencia_tiene_partidos(idCompetencia):
            raise CompetenciaEnUsoError(
                f"No se puede eliminar la competencia (idCompetencia={idCompetencia}) porque tiene partidos cargados"
            )

        return self.repo.eliminar_competencia(idCompetencia)
