from aplicacion.dtos.club_dto import ClubDTO, CrearClubDTO
from dominio.entidades.club import Club
from dominio.exceptions import ClubYaExisteError
from dominio.repositorios.club_repositorio import ClubRepositorio
from utils import id_persistido

# Regla de negocio: quien crea un club es su entrenador principal.
ROL_CREADOR = "principal"


class CrearClubUseCase:
    def __init__(self, repo: ClubRepositorio):
        """
        Funcion que permite inicializar el caso de uso de crear un club
        Args:
            repo (ClubRepositorio): Repositorio de clubes
        """
        self.repo = repo

    def ejecutar(self, dto: CrearClubDTO, idUsuario: int | None = None) -> ClubDTO | None:
        """
        Crea un club y, si se indica `idUsuario`, lo vincula como entrenador principal (en `usuarioClub`).

        Si `idUsuario` es `None` (US-108), el club se crea sin vinculo en `usuarioClub`: sirve para dar
        de alta clubes rivales o de terceros que participan en la competencia.

        Args:
            dto (CrearClubDTO): DTO que contiene la informacion del club a crear
            idUsuario (int | None): ID del usuario con sesion iniciada, o None para clubes sin vinculo.

        Raises:
            TypeError: Si el nombre no es una cadena de caracteres.
            DatoInvalidoError: Si el nombre esta vacio.
            ClubYaExisteError: Si ya hay un club con ese nombre (la base lo exige unico en toda la app).

        Returns:
            ClubDTO | None: DTO con el club creado, o None si no se pudo guardar
        """
        club = Club(nombre=dto.nombre)
        # buscar_por_nombre es parcial (LIKE '%x%'): se filtra por igualdad, sin distinguir mayusculas
        # ("atenas" y "Atenas" son el mismo club para el usuario, aunque la base los aceptaria a los dos).
        existentes = self.repo.buscar_por_nombre(club.nombre) or []
        if any(c.nombre.casefold() == club.nombre.casefold() for c in existentes):
            raise ClubYaExisteError(f"Ya existe un club llamado '{club.nombre}'")
        if idUsuario is None:
            resultado = self.repo.guardar(club=club)
        else:
            resultado = self.repo.guardar_con_entrenador(club=club, id_usuario=idUsuario, rol=ROL_CREADOR)
        if resultado is None:
            return None
        return ClubDTO(idClub=id_persistido(resultado.idClub, "Club"), nombre=resultado.nombre)
