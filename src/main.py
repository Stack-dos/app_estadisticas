import argparse

import config.rutas as r
from dominio.exceptions import ErrorDeDominio
from infraestructura.logger import get_logger
from infraestructura.persistencia.database_manager import SQLiteManager
from infraestructura.ui.cli.commands import (
    auth_login,
    auth_logout,
    auth_register,
    categoria_add,
    categoria_list,
    club_add,
    club_list,
    competencia_add,
    competencia_inscribir,
    competencia_list,
    game_list,
    inscripcion_list,
    jugador_add,
    jugador_link,
    jugador_list,
    jugador_unlink,
    lista_add,
    lista_list,
    lista_remove,
)
from utils import abortar, fecha_iso

logger = get_logger(__name__)


def construir_parser() -> argparse.ArgumentParser:
    """Arma el arbol completo de comandos de la CLI (Command Pattern con subparsers).

    Cada comando se registra con su propio bloque: agregar uno nuevo es sumar un bloque
    (nunca hay un if/elif gigante) y crear su archivo en `infraestructura/ui/cli/commands/`.
    """
    parser = argparse.ArgumentParser(prog="stats")
    subparser = parser.add_subparsers(dest="comando")

    # Rama "auth"
    parser_auth = subparser.add_parser("auth", help="Operaciones de autenticacion de usuarios")
    auth_subparsers = parser_auth.add_subparsers(dest="subcomando", required=True)

    parser_auth_register = auth_subparsers.add_parser("register", help="Registra un nuevo usuario entrenador")
    parser_auth_register.add_argument("--nombre", required=True, help="NOMBRE: nombre del usuario - OBLIGATORIO")
    parser_auth_register.add_argument("--email", required=True, help="EMAIL: email del usuario - OBLIGATORIO")
    parser_auth_register.add_argument(
        "--password", required=True, help="PASSWORD: contraseña del usuario - OBLIGATORIO"
    )
    parser_auth_register.set_defaults(func=auth_register.ejecutar)

    parser_auth_login = auth_subparsers.add_parser("login", help="Inicia sesion local con email y contraseña")
    parser_auth_login.add_argument("--email", required=True, help="EMAIL: email del usuario - OBLIGATORIO")
    parser_auth_login.add_argument("--password", required=True, help="PASSWORD: contraseña del usuario - OBLIGATORIO")
    parser_auth_login.set_defaults(func=auth_login.ejecutar)

    parser_auth_logout = auth_subparsers.add_parser("logout", help="Cierra la sesion actual")
    parser_auth_logout.set_defaults(func=auth_logout.ejecutar)

    # Rama "club"
    parser_club = subparser.add_parser("club", help="Operaciones sobre clubes")
    club_subparsers = parser_club.add_subparsers(dest="subcomando", required=True)

    parser_club_add = club_subparsers.add_parser("add", help="Crea un club nuevo")
    parser_club_add.add_argument("--nombre", required=True, help="NOMBRE: nombre del club - OBLIGATORIO")
    parser_club_add.set_defaults(func=club_add.ejecutar)

    parser_club_list = club_subparsers.add_parser("list", help="Lista los clubes de un usuario")
    parser_club_list.add_argument(
        "--id-usuario", type=int, required=True, help="ID-USUARIO: id del usuario dueño de los clubes - OBLIGATORIO"
    )
    parser_club_list.set_defaults(func=club_list.ejecutar)

    # Rama "jugador"
    parser_jugador = subparser.add_parser("jugador", help="Operaciones sobre jugadores")
    jugador_subparsers = parser_jugador.add_subparsers(dest="subcomando", required=True)

    parser_jugador_add = jugador_subparsers.add_parser("add", help="Registra un jugador nuevo")
    parser_jugador_add.add_argument("--nombre", required=True, help="NOMBRE: nombre del jugador - OBLIGATORIO")
    parser_jugador_add.add_argument("--apellido", required=True, help="APELLIDO: Apellido del jugador - OBLIGATORIO")
    parser_jugador_add.add_argument("--dni", type=int, required=True, help="DNI: DNI del jugador - OBLIGATORIO")
    parser_jugador_add.add_argument("--anio", type=int, required=True, help="AÑO: Año de nacimiento del jugador")
    parser_jugador_add.set_defaults(func=jugador_add.ejecutar)

    parser_jugador_link = jugador_subparsers.add_parser("link", help="Vincula un jugador a un club")
    parser_jugador_link.add_argument(
        "--id-jugador", type=int, required=True, help="ID-JUGADOR: id del jugador - OBLIGATORIO"
    )
    parser_jugador_link.add_argument("--id-club", type=int, required=True, help="ID-CLUB: id del club - OBLIGATORIO")
    parser_jugador_link.add_argument(
        "--fecha-desde",
        type=fecha_iso,
        required=True,
        help="FECHA-DESDE: fecha de inicio del vinculo, formato AAAA-MM-DD - OBLIGATORIO",
    )
    parser_jugador_link.set_defaults(func=jugador_link.ejecutar)

    parser_jugador_unlink = jugador_subparsers.add_parser("unlink", help="Da de baja a un jugador de su club actual")
    parser_jugador_unlink.add_argument(
        "--id-jugador", type=int, required=True, help="ID-JUGADOR: id del jugador - OBLIGATORIO"
    )
    parser_jugador_unlink.add_argument(
        "--fecha-hasta",
        type=fecha_iso,
        required=True,
        help="FECHA-HASTA: fecha de baja del vinculo, formato AAAA-MM-DD - OBLIGATORIO",
    )
    parser_jugador_unlink.set_defaults(func=jugador_unlink.ejecutar)

    parser_jugador_list = jugador_subparsers.add_parser("list", help="Lista los jugadores actuales de un club")
    parser_jugador_list.add_argument("--id-club", type=int, required=True, help="ID-CLUB: id del club - OBLIGATORIO")
    parser_jugador_list.set_defaults(func=jugador_list.ejecutar)

    # Rama "competencia"
    parser_competencia = subparser.add_parser("competencia", help="Operaciones sobre competencias")
    competencia_subparsers = parser_competencia.add_subparsers(dest="subcomando", required=True)

    parser_competencia_add = competencia_subparsers.add_parser("add", help="Crea una competencia nueva")
    parser_competencia_add.add_argument(
        "--nombre", required=True, help="NOMBRE: nombre de la competencia - OBLIGATORIO"
    )
    parser_competencia_add.add_argument(
        "--anio", type=int, required=True, help="AÑO: año de la competencia (mayor a 1900) - OBLIGATORIO"
    )
    parser_competencia_add.add_argument("--tipo", default=None, help="TIPO: tipo de competencia (ej. PROVINCIAL)")
    parser_competencia_add.set_defaults(func=competencia_add.ejecutar)

    parser_competencia_inscribir = competencia_subparsers.add_parser(
        "inscribir", help="Inscribe un club en una competencia y categoria (crea su lista de buena fe)"
    )
    parser_competencia_inscribir.add_argument(
        "--id-club", type=int, required=True, help="ID-CLUB: id del club - OBLIGATORIO"
    )
    parser_competencia_inscribir.add_argument(
        "--id-categoria", type=int, required=True, help="ID-CATEGORIA: id de la categoria - OBLIGATORIO"
    )
    parser_competencia_inscribir.add_argument(
        "--id-competencia", type=int, required=True, help="ID-COMPETENCIA: id de la competencia - OBLIGATORIO"
    )
    parser_competencia_inscribir.add_argument(
        "--fecha-presentacion",
        type=fecha_iso,
        required=True,
        help="FECHA-PRESENTACION: fecha de presentacion de la lista, formato AAAA-MM-DD - OBLIGATORIO",
    )
    parser_competencia_inscribir.set_defaults(func=competencia_inscribir.ejecutar)

    parser_competencia_list = competencia_subparsers.add_parser("list", help="Lista todas las competencias")
    parser_competencia_list.set_defaults(func=competencia_list.ejecutar)

    # Rama "categoria"
    parser_categoria = subparser.add_parser("categoria", help="Operaciones sobre categorias (ej. U21)")
    categoria_subparsers = parser_categoria.add_subparsers(dest="subcomando", required=True)

    parser_categoria_add = categoria_subparsers.add_parser("add", help="Crea una categoria nueva")
    parser_categoria_add.add_argument("--nombre", required=True, help="NOMBRE: nombre de la categoria - OBLIGATORIO")
    parser_categoria_add.set_defaults(func=categoria_add.ejecutar)

    parser_categoria_list = categoria_subparsers.add_parser("list", help="Lista todas las categorias")
    parser_categoria_list.set_defaults(func=categoria_list.ejecutar)

    # Rama "inscripcion"
    parser_inscripcion = subparser.add_parser("inscripcion", help="Consultas sobre inscripciones de clubes")
    inscripcion_subparsers = parser_inscripcion.add_subparsers(dest="subcomando", required=True)

    parser_inscripcion_list = inscripcion_subparsers.add_parser("list", help="Lista las inscripciones de un club")
    parser_inscripcion_list.add_argument(
        "--id-club", type=int, required=True, help="ID-CLUB: id del club - OBLIGATORIO"
    )
    parser_inscripcion_list.set_defaults(func=inscripcion_list.ejecutar)

    # Rama "lista" (lista de buena fe)
    parser_lista = subparser.add_parser("lista", help="Operaciones sobre la lista de buena fe de una inscripcion")
    lista_subparsers = parser_lista.add_subparsers(dest="subcomando", required=True)

    parser_lista_add = lista_subparsers.add_parser("add", help="Habilita a un jugador en la lista de buena fe")
    parser_lista_add.add_argument(
        "--id-inscripcion", type=int, required=True, help="ID-INSCRIPCION: id de la inscripcion - OBLIGATORIO"
    )
    parser_lista_add.add_argument(
        "--id-jugador", type=int, required=True, help="ID-JUGADOR: id del jugador a habilitar - OBLIGATORIO"
    )
    parser_lista_add.set_defaults(func=lista_add.ejecutar)

    parser_lista_list = lista_subparsers.add_parser("list", help="Lista los jugadores de la lista de buena fe")
    parser_lista_list.add_argument(
        "--id-inscripcion", type=int, required=True, help="ID-INSCRIPCION: id de la inscripcion - OBLIGATORIO"
    )
    parser_lista_list.set_defaults(func=lista_list.ejecutar)

    parser_lista_remove = lista_subparsers.add_parser("remove", help="Quita a un jugador de la lista de buena fe")
    parser_lista_remove.add_argument(
        "--id-inscripcion", type=int, required=True, help="ID-INSCRIPCION: id de la inscripcion - OBLIGATORIO"
    )
    parser_lista_remove.add_argument(
        "--id-jugador", type=int, required=True, help="ID-JUGADOR: id del jugador a quitar - OBLIGATORIO"
    )
    parser_lista_remove.set_defaults(func=lista_remove.ejecutar)

    # Rama "partido"
    parser_partido = subparser.add_parser("partido", help="Operaciones sobre partidos")
    partido_subparsers = parser_partido.add_subparsers(dest="subcomando", required=True)

    parser_partido_list = partido_subparsers.add_parser("list", help="Lista los partidos de un club")
    parser_partido_list.add_argument("--id-club", type=int, required=True, help="ID-CLUB: id del club - OBLIGATORIO")
    parser_partido_list.set_defaults(func=game_list.ejecutar)

    return parser


def inicializar_db() -> None:
    db = SQLiteManager(r.DB_FILE, r.SCHEMA_SQL, r.VISTA_SQL)
    db.connect()
    db.inicializar_schema()
    db.close_connection()


def main() -> None:
    """Orquesta el flujo principal de la aplicación.

    Inicializa la base de datos (esquema y vistas), parsea los argumentos de la CLI y ejecuta el
    comando elegido. Los errores de negocio (`ErrorDeDominio`) se atrapan acá, en un solo lugar: se
    muestran como un mensaje amigable y terminan el programa con codigo 1, sin traceback.

    Returns:
        None
    """
    logger.info("Ejecutando orquestador principal")
    inicializar_db()

    parser = construir_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except ErrorDeDominio as e:
            logger.warning(f"Error de dominio: {e}")
            abortar(str(e))
    else:
        parser.print_help()
    logger.info("Fin de programa")


if __name__ == "__main__":
    main()
