from dominio.entidades.club import Club, UsuarioClub
from infraestructura.repositorios.sqlite_club_repositorio import (
    SqliteClubRepositorio,
)


def test_buscar_id(db_conexion):
    club_rep = SqliteClubRepositorio(db_conexion)

    club_aux = club_rep.buscar_por_id(1)
    assert club_aux.nombre == "Atenas"

    club_aux = club_rep.buscar_por_id(2)
    assert club_aux.nombre == "Universitario"

    club_aux = club_rep.buscar_por_id(14)
    assert club_aux is None


def test_buscar_id_usuario(db_conexion):
    cursor = db_conexion.cursor()
    query = """
    INSERT INTO usuarioClub (idUsuario,idClub,rolEntrenador)
    VALUES (1,1,'asistente');
    """
    cursor.execute(query)

    club_rep = SqliteClubRepositorio(db_conexion)
    club_aux_list = club_rep.buscar_por_id_usuario(1)
    assert len(club_aux_list) == 1
    assert club_aux_list[0].nombre == "Atenas"

    club_aux_list = club_rep.buscar_por_id_usuario(302)
    assert club_aux_list is None


def test_buscar_por_nombre(db_conexion):
    club_rep = SqliteClubRepositorio(db_conexion)

    club_aux = club_rep.buscar_por_nombre("Atenas")
    assert club_aux[0].nombre == "Atenas"
    assert len(club_aux) == 1

    club_aux = club_rep.buscar_por_nombre("Corazon")
    assert club_aux is None


def test_guardar(db_conexion):
    club_rep = SqliteClubRepositorio(db_conexion)

    club_a_guardar = Club(nombre="Juniors")
    club_guardado = club_rep.guardar(club_a_guardar)

    assert club_a_guardar.nombre == club_guardado.nombre
    assert club_guardado.idClub is not None

    # La validacion de tipos de Club(nombre=None) es de la entidad: se prueba en tests/unit/test_entidades.py


def test_guardar_con_entrenador_crea_el_club_y_lo_vincula_al_usuario(db_conexion):
    club_rep = SqliteClubRepositorio(db_conexion)

    club = club_rep.guardar_con_entrenador(Club(nombre="Juniors"), id_usuario=1, rol="principal")

    assert club.idClub is not None
    assert [c.nombre for c in club_rep.buscar_por_id_usuario(1)] == ["Juniors"]


def test_guardar_con_entrenador_inexistente_no_deja_el_club_huerfano(db_conexion):
    """Si falla el vinculo (la clave foranea rechaza el usuario 302), el ROLLBACK deshace tambien el club."""
    club_rep = SqliteClubRepositorio(db_conexion)

    assert club_rep.guardar_con_entrenador(Club(nombre="Juniors"), id_usuario=302, rol="principal") is None

    assert club_rep.buscar_por_nombre("Juniors") is None


def test_link_user_club(db_conexion):
    us_aux = UsuarioClub(rol="Asistente", idUsuario=1, idClub=2)
    club_rep = SqliteClubRepositorio(db_conexion)
    us_aux_2 = club_rep.link_user_to_club(us_club=us_aux)
    assert us_aux_2.idUsuario == us_aux.idUsuario
    assert us_aux_2.idClub == us_aux.idClub
    assert us_aux_2.rol == us_aux.rol

    us_aux = UsuarioClub(rol="Asistente", idUsuario=302, idClub=1)
    us_aux_2 = club_rep.link_user_to_club(us_club=us_aux)
    assert us_aux_2 is None

    us_aux = UsuarioClub(rol="Asistente", idUsuario=1, idClub=302)
    us_aux_2 = club_rep.link_user_to_club(us_club=us_aux)
    assert us_aux_2 is None


def test_listar_todos_devuelve_todos_los_clubes_ordenados(db_conexion):
    club_rep = SqliteClubRepositorio(db_conexion)
    club_rep.guardar(Club(nombre="Belgrano"))

    clubes = club_rep.listar_todos()

    assert [c.nombre for c in clubes] == ["Atenas", "Belgrano", "Universitario"]


# ----------------------------------------------------------------------------- clubes rivales (US-114)


def test_listar_sin_usuario_trae_solo_los_rivales(db_conexion):
    repo = SqliteClubRepositorio(db_conexion)
    propio = repo.guardar_con_entrenador(Club("Hindú"), id_usuario=1, rol="principal")
    assert propio is not None

    nombres = [c.nombre for c in repo.listar_sin_usuario()]

    assert "Hindú" not in nombres
    assert {"Atenas", "Universitario"} <= set(nombres)
    assert repo.tiene_usuarios(propio.idClub)
    assert not repo.tiene_usuarios(1)


def test_actualizar_cambia_el_nombre(db_conexion):
    repo = SqliteClubRepositorio(db_conexion)

    assert repo.actualizar(Club("Atenas de Córdoba", idClub=1)) == Club("Atenas de Córdoba", idClub=1)
    assert repo.buscar_por_id(1).nombre == "Atenas de Córdoba"
    assert repo.actualizar(Club("Nadie", idClub=999999)) is None


def test_eliminar_solo_un_club_sin_partidos(db_conexion):
    repo = SqliteClubRepositorio(db_conexion)
    pezca = repo.guardar(Club("Pezca"))
    assert pezca is not None
    assert repo.tiene_partidos(1)  # Atenas juega en el seed
    assert not repo.tiene_partidos(pezca.idClub)

    assert repo.eliminar(pezca.idClub)

    assert repo.buscar_por_id(pezca.idClub) is None
    assert not repo.eliminar(pezca.idClub)
