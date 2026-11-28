import base64
import hashlib
import hmac
import os

from dominio.servicios.password_hasher import PasswordHasher

ALGORITMO = "pbkdf2_sha256"
# Cantidad de repeticiones del hash: cuanto mas alta, mas caro es probar contraseñas por fuerza bruta
ITERACIONES_POR_DEFECTO = 600_000
BYTES_SALT = 16
SEPARADOR = "$"


class Pbkdf2PasswordHasher(PasswordHasher):
    def __init__(self, iteraciones: int = ITERACIONES_POR_DEFECTO):
        """
        Implementamos la interfaz PasswordHasher con PBKDF2-HMAC-SHA256.

        El texto que devuelve `hash` tiene todo lo necesario para verificar despues, separado por "$":
        algoritmo, iteraciones, salt y hash (los dos ultimos en base64). Por eso no hace falta una
        columna aparte para el salt.

        Args:
            iteraciones (int): Repeticiones del hash para las contraseñas nuevas. Los tests usan un
                valor bajo para ser rapidos; las ya guardadas se verifican con el valor de su propio texto.

        Raises:
            ValueError: Si las iteraciones no son un numero positivo.
        """
        if iteraciones < 1:
            raise ValueError(f"iteraciones debe ser mayor a 0, recibido {iteraciones}")
        self.iteraciones = iteraciones

    def hash(self, password: str) -> str:
        """
        Funcion que se encarga de hashear una contraseña con un salt nuevo (aleatorio, distinto en cada llamada).

        Args:
            password (str): Contraseña en texto plano.

        Returns:
            str: Texto a guardar, con formato `pbkdf2_sha256$<iteraciones>$<salt>$<hash>`.
        """
        salt = os.urandom(BYTES_SALT)
        derivado = self._derivar(password, salt, self.iteraciones)
        return SEPARADOR.join([ALGORITMO, str(self.iteraciones), self._a_texto(salt), self._a_texto(derivado)])

    def verify(self, password: str, password_hash: str) -> bool:
        """
        Funcion que se encarga de verificar una contraseña contra un hash guardado: repite la cuenta con el
        salt y las iteraciones del texto guardado y compara los resultados.

        Args:
            password (str): Contraseña en texto plano ingresada por el usuario.
            password_hash (str): Texto guardado, generado por `hash`.

        Returns:
            bool: True si la contraseña es la correcta. False si no lo es, o si el texto guardado no
                tiene el formato esperado (otro algoritmo, dato corrupto): nunca lanza una excepcion.
        """
        try:
            algoritmo, iteraciones_texto, salt_texto, hash_texto = password_hash.split(SEPARADOR)
            iteraciones = int(iteraciones_texto)
            salt = base64.b64decode(salt_texto, validate=True)
            esperado = base64.b64decode(hash_texto, validate=True)
        except ValueError:
            return False

        if algoritmo != ALGORITMO or iteraciones < 1 or not esperado:
            return False

        # compare_digest tarda lo mismo acierte o no: no deja medir cuantos caracteres coinciden
        return hmac.compare_digest(self._derivar(password, salt, iteraciones), esperado)

    @staticmethod
    def _derivar(password: str, salt: bytes, iteraciones: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iteraciones)

    @staticmethod
    def _a_texto(datos: bytes) -> str:
        return base64.b64encode(datos).decode("ascii")
