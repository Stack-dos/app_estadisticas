"""Reporte de benchmarks para el segundo comentario de la PR (benchmark.md).

Sale del bench.json de pytest-benchmark.

Cada benchmark corre en dos escalas ("temporada" y "x10", ver tests/benchmarks/ayudantes_bench.py) y trae en
extra_info sus filas, los conteos de la base y el EXPLAIN QUERY PLAN de cada SELECT que ejecutó. El reporte:
- compara la MEDIANA contra la última corrida de la rama base (la mediana no se mueve por una ronda rara);
- calcula el crecimiento: mediana en x10 / mediana en temporada (los datos crecen x10);
- marca las consultas que recorren una tabla completa (SCAN) y las que lo empiezan a hacer en esta PR.
Lo usa resumen_pr.py. Las funciones son puras (datos -> Markdown) para poder testearlas.
"""

from typing import Any

MARCA = "<!-- resumen-benchmark -->"
ESCALAS = ("temporada", "x10")
UMBRAL_LENTO = 20.0  # % de aumento de la mediana contra la base para marcar ⚠️
CRECIMIENTO_CONSTANTE = 2.0  # factor x10/temporada por debajo del cual el tiempo casi no depende de los datos
CRECIMIENTO_LINEAL = 15.0  # por encima: crece más rápido que los datos (con datos x10, lo lineal es ~x10)
TABLAS_RESUMEN = {"jugador": "jugadores", "partido": "partidos", "jugadorPartido": "filas de boxscore"}
ORDEN_GRUPOS = ["usuario", "club", "jugador", "competencia", "partido", "vistas", "escrituras"]  # los demás, al final
LIMITE_COMENTARIO = 60_000  # GitHub acepta hasta 65.536 caracteres por comentario


def formatear_tiempo(segundos: float) -> str:
    if segundos < 1e-9:  # pytest-benchmark deja restos de punto flotante (7e-12) donde el valor es 0
        return "0"
    if segundos < 1e-3:
        return f"{segundos * 1e6:.3g} µs"
    if segundos < 1:
        return f"{segundos * 1e3:.3g} ms"
    return f"{segundos:.3g} s"


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def scans(plan: list[dict[str, Any]]) -> list[str]:
    """Pasos 'SCAN tabla' de un plan, sin los SCAN de subconsultas (CO-ROUTINE/MATERIALIZE), que no son tablas."""
    pasos = [paso for consulta in plan for paso in consulta["plan"]]
    subconsultas = {p.split()[1] for p in pasos if p.startswith(("CO-ROUTINE", "MATERIALIZE"))}
    return [p for p in pasos if p.startswith("SCAN ") and p.split()[1] not in subconsultas]


def agrupar(actual: dict[str, Any], base: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Una entrada por consulta, con sus dos escalas y lo que había en la base para cada una."""
    previos = {b["fullname"]: b for b in (base or {}).get("benchmarks", [])}
    consultas: dict[str, dict[str, Any]] = {}
    for b in actual.get("benchmarks", []):
        nombre = b["name"].split("[")[0].removeprefix("test_bench_")
        grupo = b.get("group") or "otros"
        c = consultas.setdefault(nombre, {"nombre": nombre.removeprefix(f"{grupo}_"), "grupo": grupo, "escalas": {}})
        previo = previos.get(b["fullname"])
        c["escalas"][b.get("param") or "unica"] = {
            "stats": b["stats"],
            "filas": b.get("extra_info", {}).get("filas"),
            "scans": scans(b.get("extra_info", {}).get("plan", [])),
            "plan": b.get("extra_info", {}).get("plan", []),
            "datos": b.get("extra_info", {}).get("datos", {}),
            "mediana_base": previo["stats"]["median"] if previo else None,
            "scans_base": scans(previo.get("extra_info", {}).get("plan", [])) if previo else None,
        }
    return list(consultas.values())


def crecimiento(c: dict[str, Any]) -> float | None:
    e = c["escalas"]
    if not all(x in e for x in ESCALAS) or not e["temporada"]["stats"]["median"]:
        return None
    return e["x10"]["stats"]["median"] / e["temporada"]["stats"]["median"]


def describir_crecimiento(factor: float | None) -> str:
    if factor is None:
        return "—"
    if factor < CRECIMIENTO_CONSTANTE:
        return f"x{factor:.1f} constante"
    if factor <= CRECIMIENTO_LINEAL:
        return f"x{factor:.1f} lineal"
    return f"⚠️ x{factor:.1f} más que lineal"


def cambio_vs_base(escala: dict[str, Any]) -> float | None:
    previa = escala["mediana_base"]
    return None if not previa else (escala["stats"]["median"] - previa) / previa * 100


def es_mas_lenta(c: dict[str, Any]) -> bool:
    cambio = cambio_vs_base(principal(c))
    return cambio is not None and cambio > UMBRAL_LENTO


def scans_nuevos(c: dict[str, Any]) -> list[str]:
    e = principal(c)
    return [] if e["scans_base"] is None else [s for s in e["scans"] if s not in e["scans_base"]]


def principal(c: dict[str, Any]) -> dict[str, Any]:
    """La escala con la que se compara contra la base y se muestra el plan: la más grande disponible."""
    return c["escalas"].get("x10") or next(iter(c["escalas"].values()))


def celda_plan(c: dict[str, Any]) -> str:
    e = principal(c)
    if not e["scans"]:
        return "✅ con índice"
    tablas = ", ".join(f"`{s.split()[1]}`" for s in e["scans"])
    return ("🆕 " if scans_nuevos(c) else "") + f"🔍 SCAN {tablas}"


def celda_vs_base(c: dict[str, Any]) -> str:
    cambio = cambio_vs_base(principal(c))
    if cambio is None:
        return "nuevo" if principal(c)["mediana_base"] is None else "—"
    return f"{cambio:+.1f} %" + (" ⚠️" if cambio > UMBRAL_LENTO else "")


def resumen_corto(consultas: list[dict[str, Any]]) -> str:
    """Una línea para el semáforo del comentario principal."""
    if not consultas:
        return "sin resultados"
    partes = [f"{len(consultas)} consultas", f"🔍 {sum(1 for c in consultas if principal(c)['scans'])} con SCAN"]
    lentas = sum(1 for c in consultas if es_mas_lenta(c))
    if lentas:
        partes.append(f"⚠️ {lentas} más lentas")
    return " · ".join(partes) + " · detalle en el comentario de benchmarks"


def linea_datos(consultas: list[dict[str, Any]]) -> str:
    partes = []
    for escala in ESCALAS:
        datos = next((c["escalas"][escala]["datos"] for c in consultas if escala in c["escalas"]), None)
        if datos:
            detalle = " · ".join(f"{miles(datos[t])} {n}" for t, n in TABLAS_RESUMEN.items() if t in datos)
            partes.append(f"`{escala}`: {detalle}")
    return "**Datos:** " + " — ".join(partes) if partes else ""


def tabla_grupo(consultas: list[dict[str, Any]]) -> str:
    filas = [
        "| Consulta | temporada | x10 | Crecimiento | vs base | Filas | Plan |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in consultas:
        tiempos = [formatear_tiempo(c["escalas"][e]["stats"]["median"]) if e in c["escalas"] else "—" for e in ESCALAS]
        filas.append(
            f"| `{c['nombre']}` | {tiempos[0]} | {tiempos[1]} | {describir_crecimiento(crecimiento(c))} | "
            f"{celda_vs_base(c)} | {principal(c)['filas']} | {celda_plan(c)} |"
        )
    return "\n".join(filas)


def seccion_planes(consultas: list[dict[str, Any]]) -> str:
    bloques = []
    for c in consultas:
        partes = [f"**`{c['grupo']}` · `{c['nombre']}`**"]
        for consulta in principal(c)["plan"]:
            pasos = "\n".join(consulta["plan"])
            partes.append(f"```sql\n{consulta['sql']}\n```\n```\n{pasos}\n```")
        bloques.append("\n".join(partes))
    return "\n\n".join(bloques)


def seccion_estadisticas(consultas: list[dict[str, Any]]) -> str:
    filas = [
        "| Benchmark | Escala | Mín | Mediana | Media | Máx | Desv. est. | IQR | OPS | Rondas |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for c in consultas:
        for escala, e in c["escalas"].items():
            s = e["stats"]
            tiempos = [formatear_tiempo(s[k]) for k in ("min", "median", "mean", "max", "stddev", "iqr")]
            filas.append(
                f"| `{c['grupo']}.{c['nombre']}` | {escala} | {' | '.join(tiempos)} | {s['ops']:,.0f} | {s['rounds']} |"
            )
    return "\n".join(filas)


COMO_LEER = "\n".join(
    [
        "- **Mediana:** el tiempo del medio de todas las rondas. Se compara con ella porque una ronda rara "
        "(el runner ocupado) no la mueve, a diferencia de la media.",
        f"- **Crecimiento:** mediana en `x10` / mediana en `temporada`. Los datos crecen x10: **constante** "
        f"(<x{CRECIMIENTO_CONSTANTE:.0f}) es una búsqueda por índice; **lineal** (~x10) recorre algo que crece con "
        f"los datos; **más que lineal** (>x{CRECIMIENTO_LINEAL:.0f}) merece mirarse.",
        f"- **vs base:** cambio de la mediana en `x10` contra la última corrida de la rama base. ⚠️ si sube más de "
        f"{UMBRAL_LENTO:.0f} %: los runners compartidos varían bastante, así que es una alerta para mirar, "
        "no un error.",
        "- **Plan:** `EXPLAIN QUERY PLAN` de cada SELECT que ejecutó la consulta (escala `x10`). "
        "`SEARCH ... USING INDEX` va directo a las filas; `SCAN tabla` recorre la tabla entera. Un SCAN sobre una "
        "tabla chica (club, categoría) no importa; sobre una que crece con los partidos, sí. 🆕 = SCAN que no estaba "
        "en la base. A diferencia del tiempo, el plan no tiene ruido.",
        "- **IQR:** rango entre el cuartil 1 y el 3; si es grande comparado con la mediana, la medición fue inestable.",
        "- **OPS:** operaciones por segundo (1 / media).",
    ]
)


def armar(actual: dict[str, Any] | None, base: dict[str, Any] | None, base_nombre: str) -> str | None:
    if not actual:
        return None
    consultas = agrupar(actual, base)
    consultas.sort(key=lambda c: ORDEN_GRUPOS.index(c["grupo"]) if c["grupo"] in ORDEN_GRUPOS else len(ORDEN_GRUPOS))
    grupos: dict[str, list[dict[str, Any]]] = {}
    for c in consultas:
        grupos.setdefault(c["grupo"], []).append(c)

    lentas = [c for c in consultas if es_mas_lenta(c)]
    nuevos = [c for c in consultas if scans_nuevos(c)]
    con_scan = [c for c in consultas if principal(c)["scans"]]
    mas_que_lineal = [c for c in consultas if (crecimiento(c) or 0) > CRECIMIENTO_LINEAL]
    destacados = [
        f"**{len(consultas)} consultas** medidas en {len(ESCALAS)} escalas",
        f"🔍 {len(con_scan)} recorren una tabla completa",
        f"📈 {len(mas_que_lineal)} crecen más que lineal",
        f"⚠️ {len(lentas)} más lentas que la base",
        f"🆕 {len(nuevos)} con un SCAN nuevo",
    ]
    if base is None:
        linea_base = f"**Base:** no hay corrida previa de `{base_nombre}`: se muestran solo los valores de esta PR."
    else:
        linea_base = (
            f"**Base:** última corrida de `{base_nombre}` "
            f"(se compara la mediana; ⚠️ si sube más de {UMBRAL_LENTO:.0f} %)."
        )

    partes = [MARCA, "## ⏱️ Benchmarks de consultas", "", linea_datos(consultas), linea_base, "", " · ".join(destacados)]
    if lentas or nuevos:
        partes += ["", "**Para mirar en esta PR:**"]
        partes += [f"- `{c['grupo']}.{c['nombre']}`: {celda_vs_base(c)}" for c in lentas]
        partes += [f"- `{c['grupo']}.{c['nombre']}`: SCAN nuevo ({', '.join(scans_nuevos(c))})" for c in nuevos]
    for grupo, lista in grupos.items():
        partes += ["", f"### {grupo}", "", tabla_grupo(lista)]
    planes = seccion_planes(consultas)
    pie = ["", "<sub>Informativo: no hace fallar el CI. Guía: `docs/info_modulo/14-benchmarks.md`.</sub>"]
    for intento_planes in (planes, "_Omitidos: el reporte superaba el tamaño máximo de un comentario de GitHub._"):
        texto = "\n".join(partes + desplegables(intento_planes, consultas) + pie)
        if len(texto) <= LIMITE_COMENTARIO:
            break
    return texto


def desplegables(planes: str, consultas: list[dict[str, Any]]) -> list[str]:
    secciones = (
        ("🔍 Planes de ejecución (EXPLAIN QUERY PLAN, escala x10)", planes),
        ("📊 Estadísticas completas", seccion_estadisticas(consultas)),
        ("📖 Cómo leer este reporte", COMO_LEER),
    )
    return [linea for t, c in secciones for linea in ("", f"<details><summary>{t}</summary>\n\n{c}\n\n</details>")]
