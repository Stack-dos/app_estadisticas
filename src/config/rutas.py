"""Módulo de configuración de rutas del proyecto.

Dos grupos de rutas:

- Lo que viene con la app (scripts SQL, assets): se deriva de la ubicación de este archivo, así
  funciona desde el repo y desde la carpeta donde la instale el instalador.
- Lo que la app escribe (base, logs, sesión): va en `~/.statspro/`, la carpeta del usuario
  (US-109, AC15). Instalada en `Program Files` o `/opt` la app no puede escribir en su propia
  carpeta; y así una reinstalación o una actualización no pisan los datos.
"""

import os

RUTA_SRC = os.path.dirname(os.path.dirname(__file__))
SCHEMA_SQL = os.path.join(RUTA_SRC, "infraestructura", "persistencia", "sql", "schema.sql")
VISTA_SQL = os.path.join(RUTA_SRC, "infraestructura", "persistencia", "sql", "views.sql")
SEED_SQL = os.path.join(RUTA_SRC, "infraestructura", "persistencia", "sql", "seed.sql")
CLEAR_SQL = os.path.join(RUTA_SRC, "infraestructura", "persistencia", "sql", "limpieza.sql")
# Imagenes y letras de la GUI (US-111). `flet build` (US-109) tambien busca los assets en src/assets/
ASSETS_DIR = os.path.join(RUTA_SRC, "assets")

# Datos del usuario: en Windows, C:\Users\<usuario>\.statspro\; en Linux, /home/<usuario>/.statspro/
DATOS_DIR = os.path.join(os.path.expanduser("~"), ".statspro")
DB_FILE = os.path.join(DATOS_DIR, "estadisticas.db")
LOG_DIR = os.path.join(DATOS_DIR, "logs")
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")
# Sesion recordada ("Recordarme", US-106)
SESSION_FILE = os.path.join(DATOS_DIR, "session.json")
