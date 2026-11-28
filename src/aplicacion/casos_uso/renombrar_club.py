import logging

from aplicacion.dtos.club_dto import ClubDTO, RenombrarClubDTO
from dominio.entidades.club import Club
from dominio.exceptions import ClubEnUsoError, ClubNoEncontradoError, ClubYaExisteError
from dominio.repositorios.club_repositorio import ClubRepositorio
from utils import id_persistido, normalizar_texto

# logging de la biblioteca estandar: el correlation_id lo agrega el handler (US-110).
logger = logging.getLogger(__name__)


class RenombrarClubUseCase:
    """Corrige el nombre de un club rival (US-114): por ejemplo "Pezca" escrito por error al cargar un partido.

    Solo para clubes sin usuario: el nombre de un club propio no se cambia desde la lista de rivales.
    """

    def __init__(self, repo: ClubRepositorio):
        """
        Args:
            repo (ClubRepositorio): Repositorio de clubes.
        """
        self.repo = repo

    def ejecutar(self, dto: RenombrarClubDTO) -> ClubDTO | None:
        """
        Args:
            dto (RenombrarClubDTO): El club y su nombre nuevo.

        Raises:
            DatoInvalidoError: Si el nombre esta vacio.
            ClubNoEncontradoError: Si el club no existe.
            ClubEnUsoError: Si es el club propio de algun usuario.
            ClubYaExisteError: Si otro club ya se llama asi (sin tildes ni mayusculas).

        Returns:
            ClubDTO | None: El club con el nombre nuevo, o None si fallo la base.
        """
        club = Club(nombre=dto.nombre.strip(), idClub=dto.idClub)
        if self.repo.buscar_por_id(dto.idClub) is None:
            raise ClubNoEncontradoError(f"No existe el club con id {dto.idClub}.")
        if self.repo.tiene_usuarios(dto.idClub):
            raise ClubEnUsoError("Ese club es propio de un entrenador: no se renombra desde la lista de rivales.")
        buscado = normalizar_texto(club.nombre)
        if any(normalizar_texto(c.nombre) == buscado and c.idClub != dto.idClub for c in self.repo.listar_todos()):
            raise ClubYaExisteError(f"Ya existe un club llamado '{club.nombre}'.")
        resultado = self.repo.actualizar(club)
        if resultado is None:
            return None
        logger.info("Club renombrado", extra={"evento": "club_actualizado", "id_club": resultado.idClub})
        return ClubDTO(idClub=id_persistido(resultado.idClub, "Club"), nombre=resultado.nombre)
