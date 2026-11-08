"""Test de integracion de punta a punta de la US-106: sesion recordada y club activo, sin ventana.

Arma la app con `construir_dependencias` (SQLite `:memory:` sin seed, repositorios reales y el archivo
de sesion en `tmp_path`) y llama a los casos de uso como lo hacen las pantallas. Cada `abrir_app()`
simula cerrar y volver a abrir la app: objetos nuevos sobre la misma base y el mismo archivo.
"""

import pytest

from aplicacion.dtos.auth_dto import LoginDTO, RegistrarDTO
from aplicacion.dtos.club_dto import CrearClubDTO
from infraestructura.persistencia.json_sesion_almacen import JsonSesionAlmacen
from infraestructura.security.password_hasher import Pbkdf2PasswordHasher
from infraestructura.ui.flet.app import Dependencias, construir_dependencias


@pytest.fixture
def archivo_sesion(tmp_path):
    return tmp_path / ".statspro" / "session.json"


@pytest.fixture
def abrir_app(db_conexion_sin_seed, archivo_sesion):
    return lambda: construir_dependencias(
        db_conexion_sin_seed, Pbkdf2PasswordHasher(iteraciones=1_000), JsonSesionAlmacen(archivo_sesion)
    )


def _entrar_con_club(app: Dependencias, recordar: bool = True) -> int:
    """Registro -> login -> crear "Atenas" -> elegirlo, como en las pantallas. Devuelve el idClub."""
    app.registrar_uc.ejecutar(RegistrarDTO(nombre="Profesor", email="profe@test.com", password="secreta123"))
    usuario = app.login_uc.ejecutar(LoginDTO(email="profe@test.com", password="secreta123"))
    app.sesion.iniciar_sesion(usuario, recordar=recordar)
    club = app.crear_club_uc.ejecutar(CrearClubDTO(nombre="Atenas"), usuario.idUsuario)
    assert club is not None
    app.sesion.set_active_club(app.cambiar_club_uc.ejecutar(usuario.idUsuario, club.idClub))
    return club.idClub


def test_con_recordarme_al_reabrir_vuelven_el_usuario_y_el_club(abrir_app):
    """AC1, AC2 y AC3: el flujo completo del PRD."""
    id_club = _entrar_con_club(abrir_app())

    reabierta = abrir_app()

    usuario = reabierta.sesion.usuario_actual()
    assert usuario.email == "profe@test.com"
    assert reabierta.sesion.club_activo().idClub == id_club
    assert [c.nombre for c in reabierta.listar_clubes_uc.ejecutar(usuario.idUsuario)] == ["Atenas"]


def test_sin_recordarme_al_reabrir_hay_que_loguearse(abrir_app, archivo_sesion):
    _entrar_con_club(abrir_app(), recordar=False)

    assert abrir_app().sesion.is_authenticated() is False
    assert not archivo_sesion.exists()


def test_cerrar_sesion_borra_el_archivo_y_al_reabrir_pide_login(abrir_app, archivo_sesion):
    """AC1: "Cerrar sesión" borra el archivo."""
    app = abrir_app()
    _entrar_con_club(app)

    app.sesion.cerrar_sesion()

    assert not archivo_sesion.exists()
    assert abrir_app().sesion.is_authenticated() is False


def test_archivo_danado_se_ignora_y_pide_login(abrir_app, archivo_sesion):
    """AC4: un session.json ilegible no rompe el arranque."""
    _entrar_con_club(abrir_app())
    archivo_sesion.write_text("{esto no es json", encoding="utf-8")

    assert abrir_app().sesion.is_authenticated() is False


def test_usuario_borrado_de_la_base_se_ignora_y_borra_el_archivo(abrir_app, archivo_sesion, db_conexion_sin_seed):
    """AC4: un session.json con un usuario que ya no existe se ignora y se pide login."""
    _entrar_con_club(abrir_app())
    db_conexion_sin_seed.execute("DELETE FROM usuario")  # ON DELETE CASCADE borra tambien su usuarioClub
    db_conexion_sin_seed.commit()

    assert abrir_app().sesion.is_authenticated() is False
    assert not archivo_sesion.exists()


def test_club_desvinculado_al_reabrir_queda_la_sesion_sin_club(abrir_app, db_conexion_sin_seed):
    """El club recordado se revalida: si ya no es del usuario, la sesion abre igual pero sin club."""
    _entrar_con_club(abrir_app())
    db_conexion_sin_seed.execute("DELETE FROM usuarioClub")
    db_conexion_sin_seed.commit()

    reabierta = abrir_app()

    assert reabierta.sesion.is_authenticated() is True
    assert reabierta.sesion.club_activo() is None
    assert abrir_app().sesion.club_activo() is None  # y el archivo quedo reescrito sin el club
