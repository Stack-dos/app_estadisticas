"""Tests unitarios de los casos de uso de clubes, con un repositorio falso (`unittest.mock`)."""

from unittest.mock import MagicMock

import pytest

from aplicacion.casos_uso.cambiar_club_activo import CambiarClubActivoUseCase
from aplicacion.casos_uso.crear_club import ROL_CREADOR, CrearClubUseCase
from aplicacion.casos_uso.eliminar_club import EliminarClubUseCase
from aplicacion.casos_uso.listar_clubes import ListarClubesUseCase
from aplicacion.casos_uso.listar_clubes_rivales import ListarClubesRivalesUseCase
from aplicacion.casos_uso.listar_clubes_usr import ListarClubesUsuarioUseCase
from aplicacion.casos_uso.renombrar_club import RenombrarClubUseCase
from aplicacion.dtos.club_dto import ClubDTO, CrearClubDTO, RenombrarClubDTO
from dominio.entidades.club import Club
from dominio.exceptions import ClubEnUsoError, ClubNoEncontradoError, ClubYaExisteError
from dominio.repositorios.club_repositorio import ClubRepositorio


@pytest.fixture
def repo_club():
    repo = MagicMock(spec=ClubRepositorio)
    repo.buscar_por_nombre.return_value = None  # por defecto no hay clubes con ese nombre
    return repo


# ----------------------------------------------------------------------------- CrearClub


def test_crear_club_vincula_al_usuario_como_entrenador_principal(repo_club):
    """Fix US-106: antes solo creaba el club, que nunca aparecia en "mis clubes" del usuario."""
    repo_club.guardar_con_entrenador.return_value = Club("Atenas", idClub=3)

    resultado = CrearClubUseCase(repo_club).ejecutar(CrearClubDTO(nombre="Atenas"), idUsuario=7)

    assert resultado == ClubDTO(idClub=3, nombre="Atenas")
    repo_club.guardar_con_entrenador.assert_called_once_with(club=Club("Atenas"), id_usuario=7, rol=ROL_CREADOR)
    repo_club.guardar.assert_not_called()  # el club sin vinculo es solo para rivales (US-108)


def test_crear_club_devuelve_none_si_el_repositorio_no_pudo_guardar(repo_club):
    repo_club.guardar_con_entrenador.return_value = None

    assert CrearClubUseCase(repo_club).ejecutar(CrearClubDTO(nombre="Atenas"), idUsuario=7) is None


def test_crear_club_con_nombre_de_tipo_invalido_no_llega_al_repositorio(repo_club):
    with pytest.raises(TypeError):
        CrearClubUseCase(repo_club).ejecutar(CrearClubDTO(nombre=None), idUsuario=7)

    repo_club.guardar_con_entrenador.assert_not_called()


@pytest.mark.parametrize("existente", ["Atenas", "atenas", "ATENAS"])
def test_crear_club_con_nombre_repetido_lanza_club_ya_existe(repo_club, existente):
    repo_club.buscar_por_nombre.return_value = [Club(existente, idClub=1)]

    with pytest.raises(ClubYaExisteError, match="Ya existe un club llamado 'Atenas'"):
        CrearClubUseCase(repo_club).ejecutar(CrearClubDTO(nombre="Atenas"), idUsuario=7)

    repo_club.guardar_con_entrenador.assert_not_called()


def test_crear_club_con_nombre_parecido_no_es_repetido(repo_club):
    """buscar_por_nombre es parcial (LIKE '%Atenas%'): "Atenas del Sur" no es el mismo club."""
    repo_club.buscar_por_nombre.return_value = [Club("Atenas del Sur", idClub=1)]
    repo_club.guardar_con_entrenador.return_value = Club("Atenas", idClub=2)

    assert CrearClubUseCase(repo_club).ejecutar(CrearClubDTO(nombre="Atenas"), idUsuario=7) == ClubDTO(2, "Atenas")


def test_crear_club_sin_usuario_no_vincula_entrenador(repo_club):
    """US-108: crear un club rival o de terceros sin idUsuario llama a guardar() sin vincularlo."""
    repo_club.guardar.return_value = Club("Instituto", idClub=4)

    resultado = CrearClubUseCase(repo_club).ejecutar(CrearClubDTO(nombre="Instituto"))

    assert resultado == ClubDTO(idClub=4, nombre="Instituto")
    repo_club.guardar.assert_called_once_with(club=Club("Instituto"))
    repo_club.guardar_con_entrenador.assert_not_called()


# ------------------------------------------------------------------ ListarClubes


def test_listar_clubes_devuelve_todos_los_clubes_como_dto(repo_club):
    repo_club.listar_todos.return_value = [Club("Atenas", idClub=1), Club("Instituto", idClub=2)]

    resultado = ListarClubesUseCase(repo_club).ejecutar()

    assert resultado == [ClubDTO(1, "Atenas"), ClubDTO(2, "Instituto")]
    repo_club.listar_todos.assert_called_once_with()


def test_listar_clubes_sin_clubes_devuelve_lista_vacia(repo_club):
    repo_club.listar_todos.return_value = []

    assert ListarClubesUseCase(repo_club).ejecutar() == []


# ------------------------------------------------------------------ ListarClubesUsuario


def test_listar_clubes_usuario_convierte_cada_club_en_dto(repo_club):
    repo_club.buscar_por_id_usuario.return_value = [Club("Atenas", idClub=1), Club("Instituto", idClub=2)]

    resultado = ListarClubesUsuarioUseCase(repo_club).ejecutar(10)

    assert resultado == [ClubDTO(1, "Atenas"), ClubDTO(2, "Instituto")]
    repo_club.buscar_por_id_usuario.assert_called_once_with(10)


@pytest.mark.parametrize("sin_resultados", [None, []], ids=["repo-devuelve-None", "repo-devuelve-lista-vacia"])
def test_listar_clubes_usuario_sin_resultados_devuelve_lista_vacia(repo_club, sin_resultados):
    repo_club.buscar_por_id_usuario.return_value = sin_resultados

    assert ListarClubesUsuarioUseCase(repo_club).ejecutar(10) == []


# ------------------------------------------------------------------ CambiarClubActivo


def test_cambiar_club_activo_devuelve_el_club_si_el_usuario_pertenece(repo_club):
    repo_club.buscar_por_id_usuario.return_value = [Club("Atenas", idClub=1), Club("Instituto", idClub=2)]

    resultado = CambiarClubActivoUseCase(repo_club).ejecutar(idUsuario=10, idClub=2)

    assert resultado == ClubDTO(idClub=2, nombre="Instituto")


@pytest.mark.parametrize(
    "clubes_del_usuario",
    [
        pytest.param([Club("Atenas", idClub=1)], id="el-club-es-de-otro-usuario"),
        pytest.param(None, id="el-usuario-no-tiene-clubes"),
    ],
)
def test_cambiar_club_activo_sin_acceso_lanza_club_no_encontrado(repo_club, clubes_del_usuario):
    repo_club.buscar_por_id_usuario.return_value = clubes_del_usuario

    with pytest.raises(ClubNoEncontradoError, match=r"idUsuario=10.*idClub=2"):
        CambiarClubActivoUseCase(repo_club).ejecutar(idUsuario=10, idClub=2)


# ----------------------------------------------------------------------------- clubes rivales (US-114)


def test_listar_rivales_traduce_los_clubes_sin_usuario(repo_club):
    repo_club.listar_sin_usuario.return_value = [Club("Pesca", idClub=20)]

    assert ListarClubesRivalesUseCase(repo_club).ejecutar() == [ClubDTO(idClub=20, nombre="Pesca")]


def test_renombrar_rival_corrige_el_nombre(repo_club):
    repo_club.buscar_por_id.return_value = Club("Pezca", idClub=20)
    repo_club.tiene_usuarios.return_value = False
    repo_club.listar_todos.return_value = [Club("Pezca", idClub=20), Club("Atenas", idClub=1)]
    repo_club.actualizar.return_value = Club("Pesca", idClub=20)

    resultado = RenombrarClubUseCase(repo_club).ejecutar(RenombrarClubDTO(idClub=20, nombre="  Pesca "))

    assert resultado == ClubDTO(idClub=20, nombre="Pesca")
    repo_club.actualizar.assert_called_once_with(Club("Pesca", idClub=20))


def test_renombrar_rival_se_puede_cambiar_solo_mayusculas_o_tildes(repo_club):
    """Comparar con el mismo club no es "ya existe": "pesca" -> "Pesca" es una correccion valida."""
    repo_club.buscar_por_id.return_value = Club("pesca", idClub=20)
    repo_club.tiene_usuarios.return_value = False
    repo_club.listar_todos.return_value = [Club("pesca", idClub=20)]
    repo_club.actualizar.return_value = Club("Pesca", idClub=20)

    assert RenombrarClubUseCase(repo_club).ejecutar(RenombrarClubDTO(idClub=20, nombre="Pesca")) is not None


@pytest.mark.parametrize(
    ("existe", "con_usuarios", "otros", "error"),
    [
        (False, False, [], ClubNoEncontradoError),
        (True, True, [], ClubEnUsoError),
        (True, False, [Club("Atenas", idClub=1)], ClubYaExisteError),
    ],
)
def test_renombrar_rechaza(repo_club, existe, con_usuarios, otros, error):
    repo_club.buscar_por_id.return_value = Club("Pezca", idClub=20) if existe else None
    repo_club.tiene_usuarios.return_value = con_usuarios
    repo_club.listar_todos.return_value = otros

    with pytest.raises(error):
        RenombrarClubUseCase(repo_club).ejecutar(RenombrarClubDTO(idClub=20, nombre="atenas"))
    repo_club.actualizar.assert_not_called()


def test_eliminar_rival_sin_partidos(repo_club):
    repo_club.tiene_usuarios.return_value = False
    repo_club.tiene_partidos.return_value = False
    repo_club.eliminar.return_value = True

    assert EliminarClubUseCase(repo_club).ejecutar(20)
    repo_club.eliminar.assert_called_once_with(20)


@pytest.mark.parametrize(("con_usuarios", "con_partidos"), [(True, False), (False, True)])
def test_eliminar_rival_en_uso_se_rechaza(repo_club, con_usuarios, con_partidos):
    repo_club.tiene_usuarios.return_value = con_usuarios
    repo_club.tiene_partidos.return_value = con_partidos

    with pytest.raises(ClubEnUsoError):
        EliminarClubUseCase(repo_club).ejecutar(20)
    repo_club.eliminar.assert_not_called()
