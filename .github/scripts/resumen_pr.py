"""Arma el comentario de resumen de la PR (resumen.md) con los resultados que dejaron los jobs del CI.

Lo corre el job "resumen-pr" de MainAction, después de bajar:
- resultados/<artifact>/...  los de esta corrida (un subdirectorio por artifact)
- base/<artifact>/...        los de la última corrida de la rama base (para el delta; pueden no estar)
- diff-cover.json            la cobertura de las líneas cambiadas (lo genera diff-cover en el mismo job)

Variables de entorno: NEEDS (toJSON(needs)), REPO, PR, CUERPO, RAMA, BASE, RUN_URL, SHA, GITHUB_WORKSPACE.
Las funciones seccion_* son puras (datos -> Markdown) para poder testearlas sin GitHub.
"""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from vincular_hu import buscar_issue

MARCA = "<!-- resumen-ci -->"  # el job busca el comentario con esta marca para editarlo en vez de crear otro
VERSION_REPORTADA = "3.13"  # de la matriz de tests-linux, la que se reporta (cobertura, tests)
UMBRAL_BENCH = 20.0  # % de aumento de la media a partir del cual un benchmark se marca como más lento

JOBS = {
    "lint": "Estilo (ruff + actionlint)",
    "static": "Tipos (mypy)",
    "tests-linux": "Tests Linux (3.12 · 3.13 · 3.14)",
    "tests-windows": "Tests Windows",
    "tests-docker": "Tests Docker",
    "check_dep": "Vulnerabilidades conocidas (pip-audit)",
    "dependency-review": "Dependencias nuevas (dependency review)",
    "benchmark": "Benchmarks (informativo)",
}
ICONOS = {"success": "✅", "failure": "❌", "cancelled": "⏹️", "skipped": "⏭️"}


# ---------------------------------------------------------------- lectura (IO)


def leer_json(ruta: Path) -> Any:
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else None


def leer_lineas(ruta: Path) -> list[str] | None:
    return ruta.read_text(encoding="utf-8").splitlines() if ruta.is_file() else None


def leer_junit(ruta: Path) -> dict[str, Any] | None:
    """Totales, fallidos y duración de cada test del junit.xml de pytest."""
    if not ruta.is_file():
        return None
    casos = []
    for caso in ET.parse(ruta).iter("testcase"):  # noqa: S314 - XML generado por pytest en el mismo CI
        problema = caso.find("failure")
        if problema is None:
            problema = caso.find("error")
        casos.append(
            {
                "nombre": f"{caso.get('classname', '')}::{caso.get('name', '')}",
                "tiempo": float(caso.get("time", 0)),
                "fallo": None if problema is None else (problema.get("message") or "").splitlines()[0][:200],
                "salteado": caso.find("skipped") is not None,
            }
        )
    return {"casos": casos}


def archivos_cambiados(base: str) -> list[str]:
    salida = subprocess.run(
        ["git", "diff", "--name-only", f"origin/{base}...HEAD"], capture_output=True, text=True, check=False
    ).stdout
    return salida.split()


# ---------------------------------------------------------------- secciones (puras)


def porcentaje_cobertura(cov: dict[str, Any] | None) -> float | None:
    return None if cov is None else float(cov["totals"]["percent_covered"])


def linea_cobertura(actual: float | None, base: float | None, base_nombre: str, diff: dict[str, Any] | None) -> str:
    if actual is None:
        return "**Cobertura:** sin datos (los tests de Linux no llegaron a generarla)"
    texto = f"**Cobertura:** {actual:.2f} %"
    if base is not None:
        delta = actual - base
        flecha = "🔺" if delta > 0.005 else "🔻" if delta < -0.005 else "="
        texto += f" ({flecha} {delta:+.2f} vs `{base_nombre}`)"
    else:
        texto += f" (sin corrida previa de `{base_nombre}` para comparar)"
    if diff is not None:
        total = diff.get("total_num_lines", 0)
        if total:
            cubiertas = total - diff.get("total_num_violations", 0)
            texto += f" · **Líneas cambiadas:** {diff['total_percent_covered']:.0f} % ({cubiertas}/{total})"
        else:
            texto += " · **Líneas cambiadas:** no hay código medible cambiado"
    return texto


def seccion_diff_cover(diff: dict[str, Any] | None) -> str | None:
    if not diff:
        return None
    filas = [
        f"| `{archivo}` | {datos['percent_covered']:.0f} % | {', '.join(map(str, datos['violation_lines']))} |"
        for archivo, datos in sorted(diff.get("src_stats", {}).items())
        if datos.get("violation_lines")
    ]
    if not filas:
        return "Todas las líneas cambiadas están cubiertas por tests. 🎉"
    return "| Archivo | Cubierto | Líneas sin test |\n|---|---|---|\n" + "\n".join(filas)


def resumen_tests(junit: dict[str, Any] | None) -> str:
    if junit is None:
        return "sin resultados"
    casos = junit["casos"]
    fallidos = sum(1 for c in casos if c["fallo"])
    salteados = sum(1 for c in casos if c["salteado"])
    return f"{len(casos) - fallidos - salteados} ✓ · {fallidos} ✗ · {salteados} salteados"


def seccion_tests(junit: dict[str, Any] | None, cuantos_lentos: int = 5) -> str | None:
    if junit is None:
        return None
    partes = []
    fallidos = [c for c in junit["casos"] if c["fallo"]]
    if fallidos:
        partes.append("**Fallidos**\n\n" + "\n".join(f"- `{c['nombre']}`: {c['fallo']}" for c in fallidos))
    lentos = sorted(junit["casos"], key=lambda c: c["tiempo"], reverse=True)[:cuantos_lentos]
    partes.append(
        f"**Los {len(lentos)} más lentos**\n\n| Test | Segundos |\n|---|---|\n"
        + "\n".join(f"| `{c['nombre']}` | {c['tiempo']:.2f} |" for c in lentos)
    )
    return "\n\n".join(partes)


def seccion_ruff(errores: list[dict[str, Any]] | None, formato: list[str] | None, raiz: str) -> str | None:
    if errores is None and formato is None:
        return None
    lineas = []
    for e in (errores or [])[:20]:
        archivo = e["filename"].removeprefix(raiz).lstrip("/")
        lineas.append(f"- `{archivo}:{e['location']['row']}` **{e['code']}** {e['message']}")
    if errores and len(errores) > 20:
        lineas.append(f"- … y {len(errores) - 20} más")
    lineas += [f"- formato: `{x.removeprefix('Would reformat: ')}`" for x in (formato or []) if "Would reformat" in x]
    return "\n".join(lineas) or "Sin errores."


def errores_mypy(salida: list[str] | None) -> list[str] | None:
    return None if salida is None else [x for x in salida if ": error:" in x]


def seccion_mypy(errores: list[str] | None) -> str | None:
    if errores is None:
        return None
    if not errores:
        return "Sin errores."
    extra = [f"- … y {len(errores) - 20} más"] if len(errores) > 20 else []
    return "\n".join([f"- `{e}`" for e in errores[:20]] + extra)


def comparar_benchmarks(actual: dict[str, Any] | None, base: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Media de cada benchmark (en ms) y su cambio porcentual contra la base, si existe."""
    if not actual:
        return []
    medias_base = {b["fullname"]: b["stats"]["mean"] for b in (base or {}).get("benchmarks", [])}
    filas = []
    for b in actual.get("benchmarks", []):
        media, previa = b["stats"]["mean"], medias_base.get(b["fullname"])
        filas.append(
            {"nombre": b["name"], "ms": media * 1000, "cambio": None if not previa else (media - previa) / previa * 100}
        )
    return filas


def seccion_benchmarks(filas: list[dict[str, Any]]) -> str | None:
    if not filas:
        return None
    tabla = ["| Benchmark | Media | vs base |", "|---|---|---|"]
    for f in filas:
        if f["cambio"] is None:
            cambio = "nuevo"
        else:
            cambio = f"{f['cambio']:+.1f} %" + (" ⚠️" if f["cambio"] > UMBRAL_BENCH else "")
        tabla.append(f"| `{f['nombre']}` | {f['ms']:.3g} ms | {cambio} |")
    return "\n".join(tabla) + (f"\n\n_Informativo: los runners compartidos varían ±{UMBRAL_BENCH:.0f} %._")


def resumen_benchmarks(filas: list[dict[str, Any]]) -> str:
    if not filas:
        return "sin resultados"
    lentos = sum(1 for f in filas if f["cambio"] is not None and f["cambio"] > UMBRAL_BENCH)
    return contar(len(filas), "medido", "medidos") + (
        f", ⚠️ {contar(lentos, 'más lento', 'más lentos')}" if lentos else ""
    )


def linea_hu(issue: dict[str, Any] | None, cuerpo: str) -> str:
    if issue is None:
        return "⚠️ **HU:** no se encontró. Agregá `Closes #N` al cuerpo de la PR o usá una rama `feature/usNNN-...`"
    texto = f"🔗 **HU:** #{issue['number']} {issue['title']}"
    if f"#{issue['number']}" not in (cuerpo or ""):
        texto += f" · ⚠️ falta `Closes #{issue['number']}` en el cuerpo"
    return texto


def linea_docs(cambiados: list[str]) -> str | None:
    toca_src = any(a.startswith("src/") for a in cambiados)
    toca_docs = any(a.startswith("docs/") for a in cambiados)
    if toca_src and not toca_docs:
        return "⚠️ **Docs:** cambió `src/` pero no `docs/`. ¿Hay que actualizar el PRD o las guías?"
    return None


def semaforo(needs: dict[str, Any], detalles: dict[str, str]) -> str:
    filas = ["| | Chequeo | Detalle |", "|---|---|---|"]
    for job, nombre in JOBS.items():
        if job in needs:
            resultado = needs[job]["result"]
            filas.append(f"| {ICONOS.get(resultado, '❔')} | {nombre} | {detalles.get(job, '')} |")
    return "\n".join(filas)


def contar(n: int, singular: str, plural: str) -> str:
    return f"sin {plural}" if n == 0 else f"{n} {singular if n == 1 else plural}"


def desplegable(titulo: str, contenido: str | None) -> str:
    return "" if contenido is None else f"<details><summary>{titulo}</summary>\n\n{contenido}\n\n</details>\n"


# ---------------------------------------------------------------- armado


def armar() -> str:
    env = os.environ
    res, base = Path("resultados"), Path("base")
    tests_dir = f"resultados-linux-py{VERSION_REPORTADA}"

    cov = leer_json(res / tests_dir / "coverage.json")
    cov_base = leer_json(base / tests_dir / "coverage.json")
    diff = leer_json(Path("diff-cover.json"))
    junit = leer_junit(res / tests_dir / "junit.xml")
    ruff = leer_json(res / "resultados-ruff" / "ruff.json")
    ruff_formato = leer_lineas(res / "resultados-ruff" / "ruff-format.txt")
    mypy = errores_mypy(leer_lineas(res / "resultados-mypy" / "mypy.txt"))
    bench = comparar_benchmarks(
        leer_json(res / "resultados-benchmark" / "bench.json"), leer_json(base / "resultados-benchmark" / "bench.json")
    )
    try:
        issue = buscar_issue(env["REPO"], env.get("CUERPO", ""), env.get("RAMA", ""))
    except subprocess.CalledProcessError:
        issue = None

    detalles = {
        "tests-linux": f"py{VERSION_REPORTADA}: {resumen_tests(junit)}",
        "benchmark": resumen_benchmarks(bench),
    }
    if ruff is not None:
        detalles["lint"] = contar(len(ruff), "error", "errores")
    if mypy is not None:
        detalles["static"] = contar(len(mypy), "error", "errores")

    lineas_estado = [
        linea_cobertura(porcentaje_cobertura(cov), porcentaje_cobertura(cov_base), env["BASE"], diff),
        linea_hu(issue, env.get("CUERPO", "")),
        linea_docs(archivos_cambiados(env["BASE"])),
    ]
    return "\n".join(
        [
            MARCA,
            "## 📊 Resumen del CI",
            "",
            semaforo(json.loads(env["NEEDS"]), detalles),
            "",
            "  \n".join(x for x in lineas_estado if x),
            "",
            desplegable("🧪 Tests (Linux " + VERSION_REPORTADA + ")", seccion_tests(junit)),
            desplegable("📈 Cobertura de las líneas cambiadas", seccion_diff_cover(diff)),
            desplegable("🧹 Ruff", seccion_ruff(ruff, ruff_formato, env.get("GITHUB_WORKSPACE", ""))),
            desplegable("🔎 mypy", seccion_mypy(mypy)),
            desplegable("⏱️ Benchmarks", seccion_benchmarks(bench)),
            f"<sub>Commit {env.get('SHA', '')[:7]} · [ver la corrida completa]({env.get('RUN_URL', '')}) · "
            "las anotaciones de ruff y mypy aparecen en la pestaña *Files changed*</sub>",
        ]
    )


if __name__ == "__main__":
    texto = armar()
    Path(sys.argv[1] if len(sys.argv) > 1 else "resumen.md").write_text(texto, encoding="utf-8")
    print(texto)
