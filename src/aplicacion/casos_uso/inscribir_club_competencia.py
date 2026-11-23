from aplicacion.dtos.competencia_dto import InscribirClubDTO, InscripcionDTO
from dominio.entidades.competencia import Inscripcion
from dominio.exceptions import (
    CategoriaNoEncontradaError,
    CategoriaNoHabilitadaError,
    ClubNoEncontradoError,
    CompetenciaNoEncontradaError,
    InscripcionDuplicadaError,
)
from dominio.repositorios.club_repositorio import ClubRepositorio
from dominio.repositorios.competencia_repositorio import CompetenciaRepositorio
from utils import id_persistido


class InscribirClubEnCompetenciaUseCase:
    def __init__(self, repo_competencia: CompetenciaRepositorio, repo_club: ClubRepositorio):
        """
        Funcion que permite inicializar el caso de uso de inscribir un club en una competencia
        Args:
            repo_competencia (CompetenciaRepositorio): Repositorio de competencias, categorias e inscripciones
            repo_club (ClubRepositorio): Repositorio de clubes, para verificar que el club exista
        """
        self.repo_competencia = repo_competencia
        self.repo_club = repo_club

    def ejecutar(self, dto: InscribirClubDTO) -> InscripcionDTO | None:
        """
        Funcion que permite inscribir un club en una competencia, generando automaticamente su lista de
        buena fe vacia. Ambas cosas se guardan de forma atomica (o se guardan las dos, o ninguna).

        Args:
            dto (InscribirClubDTO): DTO con el club, la categoria, la competencia y la fecha de presentacion

        Raises:
            ClubNoEncontradoError: Si el club no existe.
            CompetenciaNoEncontradaError: Si la competencia no existe.
            CategoriaNoEncontradaError: Si la categoria no existe.
            CategoriaNoHabilitadaError: Si la categoria no esta habilitada en la competencia.
            InscripcionDuplicadaError: Si el club ya esta inscripto en esa competencia y categoria.

        Returns:
            InscripcionDTO | None: DTO con la inscripcion y el id de su lista de buena fe, o None si no se pudo guardar
        """
        if self.repo_club.buscar_por_id(dto.idClub) is None:
            raise ClubNoEncontradoError(f"No existe un club con idClub={dto.idClub}")

        if self.repo_competencia.buscar_competencia_por_id(dto.idCompetencia) is None:
            raise CompetenciaNoEncontradaError(f"No existe una competencia con idCompetencia={dto.idCompetencia}")

        categorias = self.repo_competencia.obtener_categorias()
        if not any(c.idCategoria == dto.idCategoria for c in categorias):
            raise CategoriaNoEncontradaError(f"No existe una categoria con idCategoria={dto.idCategoria}")

        habilitadas = self.repo_competencia.obtener_categorias_de_competencia(dto.idCompetencia)
        if not any(c.idCategoria == dto.idCategoria for c in habilitadas):
            raise CategoriaNoHabilitadaError(
                f"La categoria (idCategoria={dto.idCategoria}) no esta habilitada en la competencia "
                f"(idCompetencia={dto.idCompetencia})"
            )

        # La tabla inscripcion no tiene UNIQUE(club, categoria, competencia): la regla se valida acá.
        inscripciones = self.repo_competencia.obtener_inscripciones_por_club(dto.idClub)
        if any(i.idCompetencia == dto.idCompetencia and i.idCategoria == dto.idCategoria for i in inscripciones):
            raise InscripcionDuplicadaError(
                f"El club (idClub={dto.idClub}) ya esta inscripto en la competencia "
                f"(idCompetencia={dto.idCompetencia}) y categoria (idCategoria={dto.idCategoria})"
            )

        inscripcion = Inscripcion(idClub=dto.idClub, idCategoria=dto.idCategoria, idCompetencia=dto.idCompetencia)
        resultado = self.repo_competencia.inscribir_con_lista(inscripcion, dto.fechaPresentacion)
        if resultado is None:
            return None

        inscripcion_guardada, lista_buena_fe = resultado
        return InscripcionDTO(
            idInscripcion=id_persistido(inscripcion_guardada.idInscripcion, "Inscripcion"),
            idClub=inscripcion_guardada.idClub,
            idCategoria=inscripcion_guardada.idCategoria,
            idCompetencia=inscripcion_guardada.idCompetencia,
            idListaBuenaFe=id_persistido(lista_buena_fe.idListaBuenaFe, "ListaBuenaFe"),
        )
