"""Módulo de configuración de rutas del proyecto.

Define las rutas absolutas a los archivos SQL, la base de datos y los logs,
derivándolas dinámicamente desde la ubicación de este archivo para que el
proyecto funcione independientemente del directorio de instalación.
"""

import os

RUTA_SRC = os.path.dirname(os.path.dirname(__file__))
SCHEMA_SQL = os.path.join(RUTA_SRC, "infraestructura", "persistencia", "sql", "schema.sql")
VISTA_SQL = os.path.join(RUTA_SRC, "infraestructura", "persistencia", "sql", "views.sql")
SEED_SQL = os.path.join(RUTA_SRC, "infraestructura", "persistencia", "sql", "seed.sql")
CLEAR_SQL = os.path.join(RUTA_SRC, "infraestructura", "persistencia", "sql", "limpieza.sql")
# Imagenes y letras de la GUI (US-111). `flet build` (US-404) tambien busca los assets en src/assets/
ASSETS_DIR = os.path.join(RUTA_SRC, "assets")
RUTA_RAIZ = os.path.dirname(RUTA_SRC)
DB_FILE = os.path.join(RUTA_RAIZ, "estadisticas.db")
LOG_DIR = os.path.join(RUTA_RAIZ, "logs")
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
# Sesion recordada ("Recordarme", US-106): fuera del proyecto, en la carpeta del usuario del sistema operativo
SESSION_FILE = os.path.join(os.path.expanduser("~"), ".statspro", "session.json")
