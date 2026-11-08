"""Utilidades compartidas por las distintas capas del proyecto.

Solo funciones puras y sin dependencias del proyecto: este modulo NO debe importar nada de
`infraestructura`, porque tambien lo usa `aplicacion` (una capa interna no puede depender de una
externa).
"""


def id_persistido(valor: int | None, entidad: str) -> int:
    """
    Devuelve el ID de una entidad que ya fue guardada por un repositorio.

    Las entidades declaran su ID como `int | None` porque antes de guardarse todavia no lo tienen. Una
    entidad que devuelve un repositorio siempre deberia traerlo, y los DTOs de salida exigen un `int`.
    Esta funcion deja explicita esa garantia en un solo lugar (y estrecha el tipo para mypy).

    Args:
        valor (int | None): ID de la entidad devuelta por el repositorio.
        entidad (str): Nombre de la entidad, solo para el mensaje de error.

    Raises:
        RuntimeError: Si el ID es None. Indica un bug en el repositorio, no un error del usuario.

    Returns:
        int: El ID de la entidad.
    """
    if valor is None:
        raise RuntimeError(f"El repositorio devolvio {entidad} sin ID asignado")
    return valor
