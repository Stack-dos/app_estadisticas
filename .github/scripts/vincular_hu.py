"""Encuentra la historia de usuario (issue) de una PR y le copia a la PR su épica, su US y su hito.

Lo usa el workflow PRMeta. resumen_pr.py reusa buscar_issue() para nombrar la HU en el comentario.

Cómo se encuentra la issue, en orden:
1. Una palabra de cierre en el cuerpo de la PR: "Closes #57", "Fixes #57", "Resolves #57".
2. El número de US en la rama: feature/us107-gestion -> la issue cuyo título empieza con "[US-107]".

Variables de entorno: REPO (owner/nombre), PR (número), CUERPO (cuerpo de la PR), RAMA, GH_TOKEN.
"""

import json
import os
import re
import subprocess
from typing import Any

RE_CIERRE = re.compile(r"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")
RE_US_RAMA = re.compile(r"(?i)\bus-?(\d{3})")
RE_EPICA = re.compile(r"H\d-E\d")


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def numero_desde_cuerpo(cuerpo: str) -> int | None:
    m = RE_CIERRE.search(cuerpo or "")
    return int(m.group(1)) if m else None


def us_desde_rama(rama: str) -> str | None:
    m = RE_US_RAMA.search(rama or "")
    return f"US-{m.group(1)}" if m else None


def buscar_issue(repo: str, cuerpo: str, rama: str) -> dict[str, Any] | None:
    """Devuelve la issue de la HU ({number, title, url, labels, milestone}) o None si no se encuentra."""
    campos = "number,title,url,labels,milestone"
    numero = numero_desde_cuerpo(cuerpo)
    if numero is None:
        us = us_desde_rama(rama)
        if us is None:
            return None
        # La búsqueda de GitHub es aproximada: se filtra por el prefijo exacto del título
        candidatas = json.loads(
            gh("issue", "list", "-R", repo, "--state", "all", "--json", campos, "--search", f'"[{us}]" in:title')
        )
        return next((i for i in candidatas if i["title"].startswith(f"[{us}]")), None)
    try:
        return json.loads(gh("issue", "view", str(numero), "-R", repo, "--json", campos))
    except subprocess.CalledProcessError:
        return None  # "Closes #N" a algo que no es una issue (por ejemplo, otra PR)


def labels_para_pr(issue: dict[str, Any]) -> list[str]:
    """La épica de la issue (H1-E2) y su US (US-107, sacada del título)."""
    labels = [label["name"] for label in issue["labels"] if RE_EPICA.fullmatch(label["name"])]
    if m := re.match(r"\[(US-\d{3})\]", issue["title"]):
        labels.append(m.group(1))
    return labels


def vincular() -> None:
    repo, pr = os.environ["REPO"], os.environ["PR"]
    issue = buscar_issue(repo, os.environ.get("CUERPO", ""), os.environ.get("RAMA", ""))
    if issue is None:
        print("::notice::No se encontró la HU de esta PR (ni 'Closes #N' en el cuerpo ni 'usNNN' en la rama)")
        return
    labels = labels_para_pr(issue)
    for label in labels:
        if label.startswith("US-"):  # los labels de US se crean a medida que aparecen
            subprocess.run(
                [
                    "gh",
                    "label",
                    "create",
                    label,
                    "-R",
                    repo,
                    "--color",
                    "c2e0c6",
                    "--description",
                    "Historia de usuario",
                ],
                capture_output=True,
            )
    if labels:
        gh(
            "api",
            "-X",
            "POST",
            f"repos/{repo}/issues/{pr}/labels",
            *(a for x in labels for a in ("-f", f"labels[]={x}")),
        )
    if issue.get("milestone"):
        gh("api", "-X", "PATCH", f"repos/{repo}/issues/{pr}", "-F", f"milestone={issue['milestone']['number']}")
    print(f"PR #{pr} vinculada a #{issue['number']} {issue['title']}: labels={labels}")


if __name__ == "__main__":
    vincular()
