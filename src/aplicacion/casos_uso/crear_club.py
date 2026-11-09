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

    def ejecutar(self, dto: CrearClubDTO, idUsuario: int) -> ClubDTO | None:
        """
        Crea un club y vincula como entrenador al usuario que lo crea (en `usuarioClub`).

        Fix de la US-106: antes solo creaba el club, que nunca aparecia en "mis clubes" ni se podia
        elegir como club activo. Los clubes rivales, sin vinculo, los crea la US-108 por otro camino.

        Args:
            dto (CrearClubDTO): DTO que contiene la informacion del club a crear
            idUsuario (int): ID del usuario con sesion iniciada (sale de la sesion, no del formulario)

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
        resultado = self.repo.guardar_con_entrenador(club=club, id_usuario=idUsuario, rol=ROL_CREADOR)
        if resultado is None:
            return None
        return ClubDTO(idClub=id_persistido(resultado.idClub, "Club"), nombre=resultado.nombre)
