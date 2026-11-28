from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class VersionPublicadaDTO:
    """El ultimo release estable publicado (spike de aviso de version nueva).

    `tag` es el nombre del tag tal cual (`"v1.0.1"`); `url` es la pagina del release, la que abre "Descargar".
    """

    tag: str
    url: str


@dataclass(frozen=True)
class EstadoAvisoDTO:
    """Lo que se recuerda entre arranques para no molestar (spike de aviso de version nueva, punto 4.4).

    `ultimo_chequeo`: el dia en que se consulto GitHub por ultima vez (se consulta una vez por dia como maximo).
    `tag_omitido`: la version que el usuario pidio no volver a avisar ("Omitir esta version").
    """

    ultimo_chequeo: date | None = None
    tag_omitido: str | None = None
