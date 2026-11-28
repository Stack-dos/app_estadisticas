from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Contrato para hashear y verificar contraseñas.

    Vive en el dominio (igual que las interfaces de los repositorios) para que los casos de uso dependan
    de esta abstraccion y no de una libreria concreta: la implementacion real esta en
    `infraestructura/security/`.
    """

    @abstractmethod
    def hash(self, password: str) -> str:
        "Devuelve el texto a guardar en la base en lugar de la contraseña (nunca la contraseña misma)"
        pass

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        "Indica si la contraseña ingresada corresponde al hash guardado"
        pass
