from aplicacion.dtos.club_dto import DesvincularJugadorDTO, VinculoDTO
from dominio.exceptions import DatoInvalidoError, JugadorNoEncontradoError, JugadorSinVinculoActivoError
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from utils import id_persistido


class DesvincularJugadorDeClubUseCase:
    def __init__(self, repo_jugador: JugadorRepositorio):
        """
        Funcion que permite inicializar el caso de uso de desvincular un jugador de su club actual
        Args:
            repo_jugador (JugadorRepositorio): Repositorio de jugadores
        """
        self.repo_jugador = repo_jugador

    def ejecutar(self, dto: DesvincularJugadorDTO) -> VinculoDTO | None:
        """
        Funcion que permite dar de baja a un jugador de su club actual (cierra el vinculo vigente cargando su
        fecha de fin). Es lo que permite que despues se lo vincule a otro club.

        Args:
            dto (DesvincularJugadorDTO): DTO con el jugador y la fecha de baja

        Raises:
            JugadorNoEncontradoError: Si el jugador no existe.
            JugadorSinVinculoActivoError: Si el jugador no tiene un club activo.
            DatoInvalidoError: Si la fecha de baja es anterior a la fecha de inicio del vinculo.

        Returns:
            VinculoDTO | None: El vinculo ya cerrado, o None si no se pudo guardar
        """
        if self.repo_jugador.buscar_por_id(dto.idJugador) is None:
            raise JugadorNoEncontradoError(f"No existe un jugador con idJugador={dto.idJugador}")

        vigente = next((v for v in self.repo_jugador.historial_vinculos(dto.idJugador) if v.fechaHasta is None), None)
        if vigente is None:
            raise JugadorSinVinculoActivoError(f"El jugador (idJugador={dto.idJugador}) no tiene un club activo")

        if dto.fechaHasta < vigente.fechaDesde:
            raise DatoInvalidoError(
                f"La fecha de baja ({dto.fechaHasta}) no puede ser anterior "
                f"al inicio del vinculo ({vigente.fechaDesde})"
            )

        cerrado = self.repo_jugador.cerrar_vinculo(dto.idJugador, dto.fechaHasta)
        if cerrado is None:
            return None
        return VinculoDTO(
            idJugador=dto.idJugador,
            idClub=id_persistido(vigente.idClub, "Club"),
            fechaDesde=cerrado.fechaDesde,
            fechaHasta=cerrado.fechaHasta,
        )
