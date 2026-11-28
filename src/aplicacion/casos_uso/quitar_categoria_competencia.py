from aplicacion.dtos.competencia_dto import CategoriaCompetenciaDTO
from dominio.exceptions import (
    CategoriaConInscripcionesError,
    CategoriaNoEncontradaError,
    CategoriaNoHabilitadaError,
    CompetenciaNoEncontradaError,
)
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio


class QuitarCategoriaDeCompetenciaUseCase:
    def __init__(self, repo: CompetenciaRepositorio):
        """
        Inicializa el caso de uso para quitar una categoria de una competencia.

        Args:
            repo (CompetenciaRepositorio): Repositorio de competencias y categorias.
        """
        self.repo = repo

    def ejecutar(self, dto: CategoriaCompetenciaDTO) -> CategoriaCompetenciaDTO | None:
        """
        Quita una categoria habilitada de una competencia, salvo que ya tenga clubes inscriptos.

        Args:
            dto (CategoriaCompetenciaDTO): Competencia y categoria a quitar.

        Raises:
            CompetenciaNoEncontradaError: Si la competencia no existe.
            CategoriaNoEncontradaError: Si la categoria no existe.
            CategoriaNoHabilitadaError: Si la categoria no estaba habilitada en la competencia.
            CategoriaConInscripcionesError: Si ya hay clubes inscriptos en esa competencia y categoria.

        Returns:
            CategoriaCompetenciaDTO | None: Confirmacion de la quita, o None si no se pudo borrar.
        """
        if self.repo.buscar_competencia_por_id(dto.idCompetencia) is None:
            raise CompetenciaNoEncontradaError(f"No existe una competencia con idCompetencia={dto.idCompetencia}")

        if not any(c.idCategoria == dto.idCategoria for c in self.repo.obtener_categorias()):
            raise CategoriaNoEncontradaError(f"No existe una categoria con idCategoria={dto.idCategoria}")

        if not any(
            c.idCategoria == dto.idCategoria for c in self.repo.obtener_categorias_de_competencia(dto.idCompetencia)
        ):
            raise CategoriaNoHabilitadaError(
                f"La categoria (idCategoria={dto.idCategoria}) no esta habilitada en la competencia "
                f"(idCompetencia={dto.idCompetencia})"
            )

        if self.repo.tiene_inscripciones(dto.idCompetencia, dto.idCategoria):
            raise CategoriaConInscripcionesError(
                f"No se puede quitar la categoria (idCategoria={dto.idCategoria}) de la competencia "
                f"(idCompetencia={dto.idCompetencia}) porque ya tiene clubes inscriptos"
            )

        if not self.repo.quitar_categoria(dto.idCompetencia, dto.idCategoria):
            return None
        return CategoriaCompetenciaDTO(idCompetencia=dto.idCompetencia, idCategoria=dto.idCategoria)
