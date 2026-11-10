"""US-109, AC15: lo que la app escribe va en ~/.statspro/, nunca junto al codigo.

Instalada en `Program Files` o `/opt`, la carpeta del codigo es de solo lectura.
"""

from pathlib import Path

import config.rutas as r

DATOS = Path.home() / ".statspro"
CARPETA_DEL_CODIGO = Path(r.RUTA_SRC).parent


def test_la_carpeta_de_datos_es_statspro_en_la_carpeta_del_usuario():
    assert Path(r.DATOS_DIR) == DATOS


def test_base_logs_y_sesion_viven_en_la_carpeta_de_datos():
    assert Path(r.DB_FILE) == DATOS / "estadisticas.db"
    assert Path(r.LOG_DIR) == DATOS / "logs"
    assert Path(r.APP_LOG_FILE) == DATOS / "logs" / "app.log"
    assert Path(r.SESSION_FILE) == DATOS / "session.json"


def test_nada_de_lo_que_la_app_escribe_queda_junto_al_codigo():
    for ruta in (r.DB_FILE, r.LOG_DIR, r.SESSION_FILE):
        assert not Path(ruta).is_relative_to(CARPETA_DEL_CODIGO)
