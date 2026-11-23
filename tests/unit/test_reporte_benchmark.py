"""Tests de .github/scripts/reporte_benchmark.py (segundo comentario de la PR), con un bench.json armado a mano."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".github" / "scripts"))

import reporte_benchmark as rb


def _bench(nombre, grupo, escala, mediana, plan=None):
    return {
        "name": f"test_bench_{nombre}[{escala}]",
        "fullname": f"tests/benchmarks/t.py::test_bench_{nombre}[{escala}]",
        "group": grupo,
        "param": escala,
        "stats": {
            "min": mediana,
            "median": mediana,
            "mean": mediana,
            "max": mediana,
            "stddev": 0.0,
            "iqr": 0.0,
            "ops": 1 / mediana,
            "rounds": 10,
        },
        "extra_info": {"filas": 3, "datos": {"partido": 240}, "plan": plan or []},
    }


SCAN_PARTIDO = [{"sql": "SELECT * FROM partido WHERE idClubLocal = 1", "plan": ["SCAN partido"]}]
CON_INDICE = [
    {"sql": "SELECT * FROM partido WHERE idPartido = 1", "plan": ["SEARCH partido USING INTEGER PRIMARY KEY"]}
]


def test_formatear_tiempo_elige_la_unidad():
    assert rb.formatear_tiempo(0.0000032) == "3.2 µs"
    assert rb.formatear_tiempo(0.0459) == "45.9 ms"
    assert rb.formatear_tiempo(2.5) == "2.5 s"


def test_scans_ignora_las_subconsultas():
    plan = [
        {
            "sql": "x",
            "plan": ["CO-ROUTINE v_totales", "SCAN jp", "SEARCH j USING INTEGER PRIMARY KEY", "SCAN v_totales"],
        }
    ]
    assert rb.scans(plan) == ["SCAN jp"]


def test_crecimiento_entre_escalas():
    consultas = rb.agrupar(
        {
            "benchmarks": [
                _bench("partido_por_club", "partido", "temporada", 0.001),
                _bench("partido_por_club", "partido", "x10", 0.010),
            ]
        },
        None,
    )
    assert len(consultas) == 1
    assert consultas[0]["nombre"] == "por_club"  # sin el prefijo del grupo
    assert rb.crecimiento(consultas[0]) == 10.0
    assert rb.describir_crecimiento(1.1) == "x1.1 constante"
    assert rb.describir_crecimiento(10.0) == "x10.0 lineal"
    assert rb.describir_crecimiento(40.0).startswith("⚠️")


def test_compara_la_mediana_contra_la_base_y_detecta_scans_nuevos():
    actual = {"benchmarks": [_bench("partido_por_club", "partido", "x10", 0.003, SCAN_PARTIDO)]}
    base = {"benchmarks": [_bench("partido_por_club", "partido", "x10", 0.002, CON_INDICE)]}
    c = rb.agrupar(actual, base)[0]
    assert rb.cambio_vs_base(rb.principal(c)) == 50.0
    assert rb.es_mas_lenta(c)
    assert rb.scans_nuevos(c) == ["SCAN partido"]
    assert rb.celda_plan(c) == "🆕 🔍 SCAN `partido`"


def test_sin_base_no_hay_comparacion():
    c = rb.agrupar({"benchmarks": [_bench("usuario_por_mail", "usuario", "x10", 0.001, CON_INDICE)]}, None)[0]
    assert rb.celda_vs_base(c) == "nuevo"
    assert not rb.es_mas_lenta(c)
    assert rb.scans_nuevos(c) == []
    assert rb.celda_plan(c) == "✅ con índice"


def test_armar_el_reporte_completo():
    actual = {
        "benchmarks": [
            _bench("partido_por_club", "partido", e, m, SCAN_PARTIDO) for e, m in (("temporada", 0.001), ("x10", 0.03))
        ]
    }
    texto = rb.armar(actual, None, "feature/epica2")
    assert texto.startswith(rb.MARCA)  # el workflow edita el comentario que empieza con esta marca
    assert "### partido" in texto
    assert "no hay corrida previa de `feature/epica2`" in texto
    assert "📈 1 crecen más que lineal" in texto
    assert "SELECT * FROM partido WHERE idClubLocal = 1" in texto  # el plan va en el desplegable
    assert rb.armar(None, None, "main") is None


def test_resumen_corto_para_el_semaforo():
    consultas = rb.agrupar({"benchmarks": [_bench("partido_por_club", "partido", "x10", 0.003, SCAN_PARTIDO)]}, None)
    assert rb.resumen_corto(consultas) == "1 consultas · 🔍 1 con SCAN · detalle en el comentario de benchmarks"
    assert rb.resumen_corto([]) == "sin resultados"


def test_tiempo_casi_cero_se_muestra_como_cero():
    assert rb.formatear_tiempo(7.28e-12) == "0"


def test_lecturas_antes_que_escrituras():
    actual = {
        "benchmarks": [
            _bench("guardar_algo", "escrituras", "x10", 0.001),
            _bench("usuario_por_mail", "usuario", "x10", 0.001),
        ]
    }
    texto = rb.armar(actual, None, "main")
    assert texto.index("### usuario") < texto.index("### escrituras")


def test_si_el_reporte_es_muy_largo_omite_los_planes(monkeypatch):
    actual = {"benchmarks": [_bench("partido_por_club", "partido", "x10", 0.001, SCAN_PARTIDO)]}
    completo = rb.armar(actual, None, "main")
    monkeypatch.setattr(rb, "LIMITE_COMENTARIO", len(completo) - 1)
    recortado = rb.armar(actual, None, "main")
    assert "SELECT * FROM partido" not in recortado
    assert "Omitidos" in recortado
