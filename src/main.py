"""Punto de entrada de StatsPro: abre la interfaz grafica (Flet).

Todo el armado (base de datos, repositorios, casos de uso, pantallas) vive en el composition root de la
GUI, `infraestructura/ui/flet/app.py`. Este archivo existe para que `python src/main.py` y el comando
`statspro` (`[project.scripts]` en pyproject.toml) sigan siendo la forma de abrir la app.
"""

from infraestructura.ui.flet.app import ejecutar


def main() -> None:
    """Abre la aplicacion y bloquea hasta que se cierra la ventana."""
    ejecutar()


if __name__ == "__main__":
    main()
