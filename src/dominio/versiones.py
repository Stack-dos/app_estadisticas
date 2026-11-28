"""Comparacion de versiones para el aviso de version nueva (spike: docs/spike/spike_aviso_actualizaciones.md).

Solo se entienden versiones `X.Y.Z` (con o sin `v` adelante). Cualquier otra forma (`v1.0`, `latest`,
un pre-release `v1.0.0-rc.1`) se ignora: ante la duda, no se avisa.
"""

import re

# [0-9] y no \d: \d tambien acepta digitos de otros alfabetos (el "1" arabe, U+0661), que int() convierte sin quejarse
_VERSION = re.compile(r"v?([0-9]+)\.([0-9]+)\.([0-9]+)")


def parsear_version(texto: str) -> tuple[int, int, int] | None:
    """
    Convierte `"v1.10.0"` o `"1.10.0"` en `(1, 10, 0)`.

    Args:
        texto (str): Version o tag de GitHub.

    Returns:
        tuple[int, int, int] | None: La version como numeros, o None si no tiene la forma `X.Y.Z`.
    """
    coincidencia = _VERSION.fullmatch(texto.strip())
    if coincidencia is None:
        return None
    mayor, menor, parche = (int(parte) for parte in coincidencia.groups())
    return mayor, menor, parche


def hay_version_nueva(instalada: str, tag: str) -> bool:
    """
    Indica si el tag publicado es una version mayor que la instalada.

    Se comparan tuplas de enteros y no textos: como texto `"1.10.0" < "1.9.0"`, como version es al reves.

    Args:
        instalada (str): Version de la app que esta corriendo (por ejemplo `"1.0.0"`).
        tag (str): Tag del ultimo release estable (por ejemplo `"v1.0.1"`).

    Returns:
        bool: True solo si las dos versiones son validas y el tag es mayor.
    """
    actual = parsear_version(instalada)
    publicada = parsear_version(tag)
    if actual is None or publicada is None:
        return False
    return publicada > actual
