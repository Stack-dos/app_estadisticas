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
