"""Integracion US-110: un clic de la GUI deja todos sus logs (pantalla, caso de uso, repositorio) con un
mismo correlation_id, y otro clic usa otro. Base SQLite real en memoria, sin ventana."""

from aplicacion.casos_uso.crear_club import CrearClubUseCase
from aplicacion.dtos.club_dto import CrearClubDTO
from infraestructura.repositorios.sqlite_club_repositorio import SqliteClubRepositorio
from infraestructura.ui.flet.errores import crear_etiqueta_error, ejecutar_mostrando_errores


def _crear(uc: CrearClubUseCase, nombre: str) -> None:
    ejecutar_mostrando_errores(
        lambda: uc.ejecutar(CrearClubDTO(nombre=nombre)), crear_etiqueta_error(), nombre="clubes.crear"
    )


def test_crear_un_club_deja_todos_sus_eventos_con_el_mismo_correlation_id(db_conexion, registros_log):
    uc = CrearClubUseCase(SqliteClubRepositorio(db_conexion))

    _crear(uc, "Club Observado")

    eventos = [(r.name, r.evento) for r in registros_log if hasattr(r, "evento")]
    assert eventos == [
        ("infraestructura.ui.flet.errores", "accion_inicio"),
        ("infraestructura.repositorios.sqlite_club_repositorio", "db_insert"),
        ("aplicacion.casos_uso.crear_club", "club_creado"),
        ("infraestructura.ui.flet.errores", "accion_fin"),
    ]
    ids = {r.correlation_id for r in registros_log}
    assert len(ids) == 1
    assert None not in ids


def test_otra_accion_tiene_otro_correlation_id(db_conexion, registros_log):
    uc = CrearClubUseCase(SqliteClubRepositorio(db_conexion))

    _crear(uc, "Primero")
    primera = {r.correlation_id for r in registros_log}
    registros_log.clear()
    _crear(uc, "Segundo")
    segunda = {r.correlation_id for r in registros_log}

    assert len(primera) == len(segunda) == 1
    assert primera != segunda
