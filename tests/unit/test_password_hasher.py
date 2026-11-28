"""Tests unitarios de `Pbkdf2PasswordHasher` (`infraestructura/security/password_hasher.py`).

Usan pocas iteraciones para ser rapidos: lo que se prueba es el comportamiento, no la lentitud del hash.
"""

import pytest

from dominio.servicios.password_hasher import PasswordHasher
from infraestructura.security.password_hasher import ITERACIONES_POR_DEFECTO, Pbkdf2PasswordHasher

ITERACIONES_TEST = 1_000
PASSWORD = "secreta123"


@pytest.fixture
def hasher():
    return Pbkdf2PasswordHasher(iteraciones=ITERACIONES_TEST)


def test_implementa_la_interfaz_del_dominio(hasher):
    assert isinstance(hasher, PasswordHasher)


def test_por_defecto_usa_las_iteraciones_recomendadas():
    assert Pbkdf2PasswordHasher().iteraciones == ITERACIONES_POR_DEFECTO == 600_000


@pytest.mark.parametrize("iteraciones", [0, -1])
def test_iteraciones_no_positivas_lanzan_value_error(iteraciones):
    with pytest.raises(ValueError, match="iteraciones"):
        Pbkdf2PasswordHasher(iteraciones=iteraciones)


# ----------------------------------------------------------------------------- hash


def test_hash_no_contiene_la_password_en_texto_plano(hasher):
    assert PASSWORD not in hasher.hash(PASSWORD)


def test_hash_tiene_formato_algoritmo_iteraciones_salt_hash(hasher):
    algoritmo, iteraciones, salt, derivado = hasher.hash(PASSWORD).split("$")

    assert algoritmo == "pbkdf2_sha256"
    assert iteraciones == str(ITERACIONES_TEST)
    assert salt
    assert derivado


def test_dos_hashes_de_la_misma_password_son_distintos(hasher):
    # Salt dinamico: cada llamada genera uno nuevo, asi dos usuarios con la misma password no comparten hash
    assert hasher.hash(PASSWORD) != hasher.hash(PASSWORD)


# ----------------------------------------------------------------------------- verify


def test_verify_con_la_password_correcta_es_true(hasher):
    assert hasher.verify(PASSWORD, hasher.hash(PASSWORD)) is True


@pytest.mark.parametrize("ingresada", ["otra-password", "SECRETA123", "secreta123 ", ""])
def test_verify_con_otra_password_es_false(hasher, ingresada):
    assert hasher.verify(ingresada, hasher.hash(PASSWORD)) is False


def test_verify_acepta_passwords_con_acentos_y_simbolos(hasher):
    password = "contraseña-ñandú$123"

    assert hasher.verify(password, hasher.hash(password)) is True


def test_verify_usa_las_iteraciones_del_hash_guardado_y_no_las_del_hasher():
    # Si mañana se suben las iteraciones, las passwords ya guardadas tienen que seguir verificando
    guardado = Pbkdf2PasswordHasher(iteraciones=500).hash(PASSWORD)

    assert Pbkdf2PasswordHasher(iteraciones=ITERACIONES_TEST).verify(PASSWORD, guardado) is True


@pytest.mark.parametrize(
    "guardado",
    [
        pytest.param("", id="vacio"),
        pytest.param("123456", id="texto-plano"),
        pytest.param("pbkdf2_sha256$1000$c2FsdA==", id="faltan-partes"),
        pytest.param("pbkdf2_sha256$1000$c2FsdA==$aGFzaA==$extra", id="sobran-partes"),
        pytest.param("pbkdf2_sha256$mil$c2FsdA==$aGFzaA==", id="iteraciones-no-numericas"),
        pytest.param("pbkdf2_sha256$0$c2FsdA==$aGFzaA==", id="iteraciones-en-cero"),
        pytest.param("pbkdf2_sha256$1000$c2FsdA==$", id="hash-vacio"),
        pytest.param("pbkdf2_sha256$1000$no es base64$aGFzaA==", id="salt-no-es-base64"),
        pytest.param("md5$1000$c2FsdA==$aGFzaA==", id="otro-algoritmo"),
        pytest.param("$2b$10$CwTycUXWue0Thq9StjUM0uJ8s6mG1fK0O9Yx8uWb1x1o1t4bm/FKa", id="hash-bcrypt"),
    ],
)
def test_verify_con_un_hash_malformado_es_false_y_no_lanza(hasher, guardado):
    assert hasher.verify(PASSWORD, guardado) is False
