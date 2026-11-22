"""Tests de los scripts del CI (.github/scripts/): las funciones puras que arman el resumen de la PR."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".github" / "scripts"))

import resumen_pr as r
import vincular_hu as v


def test_numero_desde_cuerpo_acepta_palabras_de_cierre():
    assert v.numero_desde_cuerpo("Bla\n- Closes #57\n- Related #3") == 57
    assert v.numero_desde_cuerpo("fixes #8") == 8
    assert v.numero_desde_cuerpo("- Closes #\n- Related #21") is None  # el template vacio no cuenta


def test_us_desde_rama():
    assert v.us_desde_rama("feature/us107-gestion") == "US-107"
    assert v.us_desde_rama("feature/US-204-migraciones") == "US-204"
    assert v.us_desde_rama("feature/mejora-ci") is None


def test_labels_para_pr_toma_epica_y_us():
    issue = {"title": "[US-107] Competencias", "labels": [{"name": "historia"}, {"name": "H1-E2"}]}
    assert v.labels_para_pr(issue) == ["H1-E2", "US-107"]


def test_linea_cobertura_con_delta_y_diff():
    diff = {"total_num_lines": 50, "total_num_violations": 4, "total_percent_covered": 92}
    texto = r.linea_cobertura(87.5, 86.0, "feature/epica2", diff)
    assert "87.50 %" in texto
    assert "🔺 +1.50 vs `feature/epica2`" in texto
    assert "92 % (46/50)" in texto


def test_linea_cobertura_sin_base_ni_datos():
    assert "sin corrida previa" in r.linea_cobertura(80.0, None, "main", None)
    assert "sin datos" in r.linea_cobertura(None, 80.0, "main", None)


def test_tests_cuenta_fallidos_y_ordena_lentos():
    junit = {
        "casos": [
            {"nombre": "a::rapido", "tiempo": 0.1, "fallo": None, "salteado": False},
            {"nombre": "a::lento", "tiempo": 2.0, "fallo": None, "salteado": False},
            {"nombre": "a::roto", "tiempo": 0.5, "fallo": "assert 1 == 2", "salteado": False},
            {"nombre": "a::skip", "tiempo": 0.0, "fallo": None, "salteado": True},
        ]
    }
    assert r.resumen_tests(junit) == "2 ✓ · 1 ✗ · 1 salteados"
    seccion = r.seccion_tests(junit, cuantos_lentos=2)
    assert "`a::roto`: assert 1 == 2" in seccion
    lentos = seccion.split("más lentos")[1]
    assert lentos.index("a::lento") < lentos.index("a::roto")  # ordenados de mayor a menor
    assert "a::rapido" not in lentos  # solo los 2 pedidos


def test_linea_docs_avisa_si_cambia_src_sin_docs():
    assert r.linea_docs(["src/dominio/club.py"]) is not None
    assert r.linea_docs(["src/dominio/club.py", "docs/plan_desarrollo_detallado.md"]) is None
    assert r.linea_docs([".github/workflows/x.yml"]) is None


def test_semaforo_solo_muestra_los_jobs_que_corrieron():
    tabla = r.semaforo({"lint": {"result": "failure"}, "static": {"result": "success"}}, {"lint": "3 errores"})
    assert "| ❌ | Estilo (ruff + actionlint) | 3 errores |" in tabla
    assert "Tests Windows" not in tabla
