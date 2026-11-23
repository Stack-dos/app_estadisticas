from aplicacion.dtos.competencia_dto import CategoriaCompetenciaDTO
from dominio.exceptions import (
    CategoriaNoEncontradaError,
    CategoriaYaHabilitadaError,
    CompetenciaNoEncontradaError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


class HabilitarCategoriaEnCompetenciaUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Inicializa el caso de uso para habilitar una categoria en una competencia.

        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias y categorias.
        """
        self.repo = repo

    def ejecutar(self, dto: CategoriaCompetenciaDTO) -> CategoriaCompetenciaDTO | None:
        """
        Habilita una categoria del catalogo para que pueda jugarse en la competencia.

        Args:
            dto (CategoriaCompetenciaDTO): Competencia y categoria a habilitar.

        Raises:
            CompetenciaNoEncontradaError: Si la competencia no existe.
            CategoriaNoEncontradaError: Si la categoria no existe.
            CategoriaYaHabilitadaError: Si la categoria ya esta habilitada en esa competencia.

        Returns:
            CategoriaCompetenciaDTO | None: Confirmacion de la habilitacion, o None si no se pudo guardar.
        """
        if self.repo.buscar_competencia_por_id(dto.idCompetencia) is None:
            raise CompetenciaNoEncontradaError(f"No existe una competencia con idCompetencia={dto.idCompetencia}")

        if not any(c.idCategoria == dto.idCategoria for c in self.repo.obtener_categorias()):
            raise CategoriaNoEncontradaError(f"No existe una categoria con idCategoria={dto.idCategoria}")

        if any(
            c.idCategoria == dto.idCategoria for c in self.repo.obtener_categorias_de_competencia(dto.idCompetencia)
        ):
            raise CategoriaYaHabilitadaError(
                f"La categoria (idCategoria={dto.idCategoria}) ya esta habilitada en la competencia "
                f"(idCompetencia={dto.idCompetencia})"
            )

        if not self.repo.habilitar_categoria(dto.idCompetencia, dto.idCategoria):
            return None
        return CategoriaCompetenciaDTO(idCompetencia=dto.idCompetencia, idCategoria=dto.idCategoria)
