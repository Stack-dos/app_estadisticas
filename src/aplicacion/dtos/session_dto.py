from dataclasses import dataclass


@dataclass
class SessionDTO:
    """Lo que se guarda de la sesion cuando el usuario marca "Recordarme" (US-106).

    Nunca lleva la contraseña ni su hash: con el id se vuelve a buscar el usuario en la base al reabrir la app.
    """

    usuario_id: int
    email: str
    club_activo_id: int | None = None
