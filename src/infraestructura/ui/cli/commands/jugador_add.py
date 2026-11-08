import argparse

from aplicacion.casos_uso.registrar_jugador import RegistrarJugadorUseCase
from aplicacion.dtos.jugador_dto import CrearJugadorDTO
from dominio.repositorios.jugador_repositorio import JugadorRepositorio
from infraestructura.persistencia.database_manager import abrir_conexion
from infraestructura.repositorios.sqlite_jugador_repositorio import SqliteJugadorRepositorio
from utils import abortar


def ejecutar(args: argparse.Namespace, repo: JugadorRepositorio | None = None) -> None:
    """Comando `jugador add`: registra un jugador nuevo.

    Args:
        args (argparse.Namespace): Argumentos parseados (nombre, apellido, anio).
        repo (JugadorRepositorio | None): Repositorio a usar. En produccion no se pasa (se arma contra
            SQLite real); en los tests se inyecta uno falso.
    """
    if repo is None:
        repo = SqliteJugadorRepositorio(conexion=abrir_conexion())

    dto = CrearJugadorDTO(nombre=args.nombre, apellido=args.apellido, anioNacimiento=args.anio)

    jugador = RegistrarJugadorUseCase(repo).ejecutar(dto)
    if jugador is None:
        abortar("no se pudo guardar el jugador")
    print(f"Jugador creado: {jugador.nombre_completo} (id={jugador.id})")
