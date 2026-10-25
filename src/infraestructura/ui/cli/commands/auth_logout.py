import argparse


def ejecutar(args: argparse.Namespace) -> None:
    """Comando `auth logout`: informa que no hay sesion que cerrar (US-104).

    Args:
        args (argparse.Namespace): Argumentos parseados.
    """
    print("No hay sesión que cerrar.")
