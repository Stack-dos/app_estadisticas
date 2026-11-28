"""Planilla de boxscore tipo Excel (US-113): una fila por jugador, columnas cortas y la fila "Equipo" sola.

Reemplaza a las filas sueltas de la US-108 (cada celda repetia el nombre del jugador y cada fila tenia
su propio scroll). Ahora es una grilla: encabezado arriba, una fila por jugador, Tab avanza de celda en
celda y abajo la fila "Equipo" se recalcula con cada tecla. Toda la planilla comparte un solo scroll
horizontal.

Dos componentes:

- `PlanillaBoxscore`: boxscore por jugador. Sirve para el equipo propio (nombres fijos, salen de la lista
  de buena fe) y para el rival (ademas se pueden agregar filas con nombre y apellido a mano).
- `FilaTotalesEquipo`: una sola fila con los totales de un equipo (la fila "Equipo Rival" de la planilla
  de Excel). Si se dejan los tiros vacios, los puntos se cargan a mano: es el caso "solo el resultado".

Una fila con todas las celdas vacias (o en 0) es un jugador que no jugo: no se manda.
"""

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from aplicacion.dtos.jugador_dto import JugadorDTO
from aplicacion.dtos.partido_dto import EstadisticaInputDTO, TotalesEquipoDTO
from dominio.entidades.partido import EstadisticaEquipo, JugadorPartido
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.estilo import ESPACIO_CHICO

# (atributo del DTO, encabezado, admite decimales). El orden es el de la planilla de Excel del club.
COLUMNAS_PLANILLA: tuple[tuple[str, str, bool], ...] = (
    ("minutosJugados", "Min", True),
    ("t2c", "T2C", False),
    ("t2l", "T2L", False),
    ("t3c", "T3C", False),
    ("t3l", "T3L", False),
    ("t1c", "T1C", False),
    ("t1l", "T1L", False),
    ("rebotesDef", "RD", False),
    ("rebotesOf", "RO", False),
    ("asistencias", "AST", False),
    ("recuperos", "REC", False),
    ("perdidas", "PER", False),
    ("taponesRealizados", "TAP+", False),
    ("taponesRecibidos", "TAP-", False),
    ("faltasRecibidas", "FR", False),
    ("faltasCometidas", "FC", False),
)
COLUMNAS_TOTALES = tuple(c for c in COLUMNAS_PLANILLA if c[0] != "minutosJugados")
DESCRIPCION_COLUMNAS = {
    "Min": "Minutos jugados",
    "PTS": "Puntos (se calculan solos: 2*T2C + 3*T3C + T1C)",
    "T2C": "Dobles convertidos",
    "T2L": "Dobles lanzados",
    "T3C": "Triples convertidos",
    "T3L": "Triples lanzados",
    "T1C": "Libres convertidos",
    "T1L": "Libres lanzados",
    "RD": "Rebotes defensivos",
    "RO": "Rebotes ofensivos",
    "AST": "Asistencias",
    "REC": "Recuperos",
    "PER": "Pérdidas",
    "TAP+": "Tapones realizados",
    "TAP-": "Tapones recibidos",
    "FR": "Faltas recibidas",
    "FC": "Faltas cometidas",
}

ANCHO_CELDA = 54
ANCHO_NOMBRE = 190
ANCHO_NOMBRE_EDITABLE = 94


def clave_celda(nombre_fila: str, etiqueta: str) -> str:
    """`key` de una celda, para encontrarla en los tests: "Pepe Argento · T2C"."""
    return f"{nombre_fila} · {etiqueta}"


def _puntos(valores: dict[str, float]) -> int:
    return int(valores.get("t2c", 0)) * 2 + int(valores.get("t3c", 0)) * 3 + int(valores.get("t1c", 0))


def _celda(clave: str, al_cambiar: Callable[[], None]) -> ft.TextField:
    return ft.TextField(
        key=clave,
        width=ANCHO_CELDA,
        dense=True,
        text_align=ft.TextAlign.CENTER,
        keyboard_type=ft.KeyboardType.NUMBER,
        content_padding=ft.Padding.symmetric(horizontal=4, vertical=8),
        on_change=lambda: al_cambiar(),
    )


def _texto_celda(valor: str = "", *, negrita: bool = False, tooltip: str | None = None) -> ft.Text:
    return ft.Text(
        valor,
        width=ANCHO_CELDA,
        text_align=ft.TextAlign.CENTER,
        weight=ft.FontWeight.W_600 if negrita else None,
        tooltip=tooltip,
    )


def _encabezado(primera: str, columnas: tuple[tuple[str, str, bool], ...]) -> ft.Row:
    """Fila de encabezados; al pasar el mouse por una sigla se ve que significa."""
    celdas: list[ft.Control] = [
        ft.Text(primera, width=ANCHO_NOMBRE, weight=ft.FontWeight.W_600),
        _texto_celda("PTS", negrita=True, tooltip=DESCRIPCION_COLUMNAS["PTS"]),
    ]
    for _attr, etiqueta, _dec in columnas:
        celdas.append(_texto_celda(etiqueta, negrita=True, tooltip=DESCRIPCION_COLUMNAS[etiqueta]))
    return ft.Row(celdas, spacing=ESPACIO_CHICO // 2)


def _leer_numeros(
    celdas: dict[str, ft.TextField], columnas: tuple[tuple[str, str, bool], ...], nombre: str
) -> dict[str, float] | None:
    """Lee las celdas de una fila. Devuelve None si la fila esta vacia; marca la celda invalida si hay error."""
    valores: dict[str, float] = {}
    hay_dato = False
    for attr, etiqueta, admite_decimales in columnas:
        campo = celdas[attr]
        campo.error = None
        texto = (campo.value or "").strip().replace(",", ".")
        if not texto:
            valores[attr] = 0
            continue
        try:
            numero = float(texto) if admite_decimales else int(texto)
        except ValueError as err:
            campo.error = "!"
            raise DatoInvalidoError(f"{nombre}: '{etiqueta}' tiene que ser un número entero.") from err
        if numero < 0:
            campo.error = "!"
            raise DatoInvalidoError(f"{nombre}: '{etiqueta}' no puede ser negativo.")
        valores[attr] = numero
        hay_dato = hay_dato or numero != 0
    return valores if hay_dato else None


def _texto_valor(valor: float) -> str:
    """Valor guardado como texto de celda: los ceros quedan vacios, como al cargar."""
    return f"{valor:g}" if valor else ""


def _sumar_sin_error(celdas: dict[str, ft.TextField], attr: str) -> float:
    try:
        return float((celdas[attr].value or "0").strip().replace(",", ".") or 0)
    except ValueError:
        return 0


@dataclass
class _Fila:
    """Una fila de la planilla. `jugador` es None en las filas del rival cargadas a mano."""

    jugador: JugadorDTO | None
    celdas: dict[str, ft.TextField]
    pts: ft.Text
    control: ft.Row
    campo_nombre: ft.TextField | None = None
    campo_apellido: ft.TextField | None = None

    @property
    def nombre(self) -> str:
        """Lo escrito en Nombre (solo filas a mano; en las demas es "")."""
        return (self.campo_nombre.value or "").strip() if self.campo_nombre is not None else ""

    @property
    def apellido(self) -> str:
        return (self.campo_apellido.value or "").strip() if self.campo_apellido is not None else ""

    @property
    def nombre_visible(self) -> str:
        if self.jugador is not None:
            return self.jugador.nombre_completo
        return f"{self.nombre} {self.apellido}".strip() or "Jugador sin nombre"


class PlanillaBoxscore:
    """Boxscore por jugador de un equipo, con la fila "Equipo" calculada sola."""

    def __init__(self, titulo: str, al_cambiar: Callable[[], None] | None = None, *, permite_agregar: bool = False):
        """
        Args:
            titulo (str): Nombre del equipo, encabeza la primera columna.
            al_cambiar (Callable[[], None] | None): Se llama cuando cambia un valor (para redibujar la pagina).
            permite_agregar (bool): Si se pueden sumar filas con nombre y apellido a mano (planilla del rival).
        """
        self._al_cambiar_externo = al_cambiar
        self._filas: list[_Fila] = []
        self._contador_manual = 0
        self._encabezado = _encabezado(titulo, COLUMNAS_PLANILLA)
        self._cuerpo = ft.Column(spacing=2)
        self._fila_total_pts = _texto_celda("0", negrita=True)
        self._fila_total = {attr: _texto_celda("0", negrita=True) for attr, _e, _d in COLUMNAS_PLANILLA}
        fila_equipo = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Equipo", width=ANCHO_NOMBRE, weight=ft.FontWeight.W_600),
                    self._fila_total_pts,
                    *self._fila_total.values(),
                ],
                spacing=ESPACIO_CHICO // 2,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            padding=ft.Padding.symmetric(vertical=6),
        )
        controles: list[ft.Control] = [self._encabezado, self._cuerpo, fila_equipo]
        if permite_agregar:
            controles.append(ft.TextButton("Agregar jugador", icon=ft.Icons.PERSON_ADD, on_click=self.agregar_fila))
        self.error = ft.Text("", color=ft.Colors.ERROR, visible=False)
        # Un solo scroll horizontal para toda la planilla (antes cada fila tenia el suyo)
        self.control = ft.Column(
            [ft.Row([ft.Column(controles, spacing=ESPACIO_CHICO)], scroll=ft.ScrollMode.AUTO), self.error],
            spacing=ESPACIO_CHICO,
        )

    def actualizar_titulo(self, titulo: str) -> None:
        primera = self._encabezado.controls[0]
        if isinstance(primera, ft.Text):
            primera.value = titulo

    def cargar_jugadores(self, jugadores: list[JugadorDTO]) -> None:
        """Pone una fila por jugador (nombre fijo). Un jugador que ya tenia fila conserva lo cargado."""
        anteriores = {f.jugador.id: f for f in self._filas if f.jugador is not None}
        self._filas = [anteriores.get(j.id) or self._nueva_fila(j) for j in jugadores]
        self._redibujar()

    def poner_valores(self, id_jugador: int, valores: dict[str, float]) -> bool:
        """Llena la fila de un jugador con valores guardados (US-114, editar). False si no tiene fila."""
        for fila in self._filas:
            if fila.jugador is not None and fila.jugador.id == id_jugador:
                for attr, celda in fila.celdas.items():
                    celda.value = _texto_valor(valores.get(attr, 0))
                self._recalcular(avisar=False)
                return True
        return False

    def agregar_fila(self) -> None:
        """Suma una fila con nombre y apellido editables (jugador del rival que no esta en la base)."""
        self._contador_manual += 1
        self._filas.append(self._nueva_fila(None))
        self._redibujar()
        self._avisar()

    @property
    def filas_manuales(self) -> list[_Fila]:
        return [f for f in self._filas if f.jugador is None]

    @property
    def cantidad_filas(self) -> int:
        return len(self._filas)

    def _nueva_fila(self, jugador: JugadorDTO | None) -> _Fila:
        if jugador is not None:
            nombre_clave = jugador.nombre_completo
            primera: list[ft.Control] = [ft.Text(jugador.nombre_completo, width=ANCHO_NOMBRE)]
            campo_nombre = campo_apellido = None
        else:
            nombre_clave = f"Rival {self._contador_manual}"
            campo_nombre = ft.TextField(
                key=clave_celda(nombre_clave, "Nombre"), hint_text="Nombre", width=ANCHO_NOMBRE_EDITABLE, dense=True
            )
            campo_apellido = ft.TextField(
                key=clave_celda(nombre_clave, "Apellido"),
                hint_text="Apellido",
                width=ANCHO_NOMBRE_EDITABLE,
                dense=True,
            )
            primera = [ft.Row([campo_nombre, campo_apellido], spacing=2, width=ANCHO_NOMBRE)]
        celdas = {
            attr: _celda(clave_celda(nombre_clave, etiqueta), self._recalcular)
            for attr, etiqueta, _d in COLUMNAS_PLANILLA
        }
        pts = _texto_celda("")
        control = ft.Row([*primera, pts, *celdas.values()], spacing=ESPACIO_CHICO // 2)
        return _Fila(jugador, celdas, pts, control, campo_nombre, campo_apellido)

    def _redibujar(self) -> None:
        self._cuerpo.controls = [
            ft.Container(content=f.control, bgcolor=ft.Colors.SURFACE_CONTAINER_LOW if i % 2 else None)
            for i, f in enumerate(self._filas)
        ]
        self._recalcular(avisar=False)

    def _recalcular(self, avisar: bool = True) -> None:
        """Recalcula los PTS de cada fila y la fila Equipo. No valida: eso lo hace `leer` al guardar."""
        totales = dict.fromkeys(self._fila_total, 0.0)
        total_pts = 0
        for fila in self._filas:
            valores = {attr: _sumar_sin_error(fila.celdas, attr) for attr in fila.celdas}
            pts = _puntos(valores)
            fila.pts.value = str(pts) if any(valores.values()) else ""
            total_pts += pts
            for attr, valor in valores.items():
                totales[attr] += valor
        self._fila_total_pts.value = str(total_pts)
        for attr, texto in self._fila_total.items():
            texto.value = f"{totales[attr]:g}"
        if avisar:
            self._avisar()

    def _avisar(self) -> None:
        if self._al_cambiar_externo is not None:
            self._al_cambiar_externo()

    @property
    def puntos(self) -> int:
        """Puntos del equipo segun lo cargado (sin validar)."""
        return int(self._fila_total_pts.value or 0)

    def leer(self) -> list[EstadisticaInputDTO]:
        """
        Valida la planilla y devuelve una estadistica por jugador que jugo (las filas vacias se ignoran).

        Raises:
            DatoInvalidoError: Si una celda no es numerica, una fila rompe una regla del boxscore
                (por ejemplo T2C > T2L) o a una fila manual con datos le falta el nombre o el apellido.
        """
        self.error.value = ""
        self.error.visible = False
        resultado: list[EstadisticaInputDTO] = []
        try:
            for fila in self._filas:
                valores = _leer_numeros(fila.celdas, COLUMNAS_PLANILLA, fila.nombre_visible)
                if valores is None:
                    continue
                puntos = _puntos(valores)
                try:
                    JugadorPartido(
                        idJugador=0,
                        idPartido=0,
                        idClub=0,
                        puntos=puntos,
                        minutosJugados=float(valores["minutosJugados"]),
                        **{a: int(v) for a, v in valores.items() if a != "minutosJugados"},
                    )
                except DatoInvalidoError as err:
                    raise DatoInvalidoError(f"{fila.nombre_visible}: {err}") from err
                nombre, apellido = fila.nombre, fila.apellido
                if fila.jugador is None and not (nombre and apellido):
                    raise DatoInvalidoError("Completá nombre y apellido de cada jugador rival que cargaste.")
                resultado.append(
                    EstadisticaInputDTO(
                        idJugador=fila.jugador.id if fila.jugador is not None else None,
                        nombre=nombre,
                        apellido=apellido,
                        puntos=puntos,
                        minutosJugados=float(valores["minutosJugados"]),
                        **{a: int(v) for a, v in valores.items() if a != "minutosJugados"},
                    )
                )
        except DatoInvalidoError as err:
            self.error.value = str(err)
            self.error.visible = True
            raise
        return resultado


class FilaTotalesEquipo:
    """Totales de un equipo en una sola fila: la fila "Equipo Rival" de la planilla de Excel."""

    def __init__(self, titulo: str, al_cambiar: Callable[[], None] | None = None):
        self._titulo = titulo
        self._al_cambiar = al_cambiar
        self.campo_puntos = ft.TextField(
            key=clave_celda("Totales", "PTS"),
            width=ANCHO_CELDA,
            dense=True,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            content_padding=ft.Padding.symmetric(horizontal=4, vertical=8),
            on_change=lambda: self._recalcular(),
        )
        self.celdas = {
            attr: _celda(clave_celda("Totales", etiqueta), self._recalcular) for attr, etiqueta, _d in COLUMNAS_TOTALES
        }
        self._nombre = ft.Text(titulo, width=ANCHO_NOMBRE, weight=ft.FontWeight.W_600)
        self.error = ft.Text("", color=ft.Colors.ERROR, visible=False)
        self.control = ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                _encabezado("Equipo", COLUMNAS_TOTALES),
                                ft.Row(
                                    [self._nombre, self.campo_puntos, *self.celdas.values()], spacing=ESPACIO_CHICO // 2
                                ),
                            ],
                            spacing=ESPACIO_CHICO,
                        )
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                ft.Text(
                    "Si cargás los tiros, los puntos se calculan solos. Si solo sabés el resultado, "
                    "dejá los tiros vacíos y escribí los puntos.",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                self.error,
            ],
            spacing=ESPACIO_CHICO,
        )

    def actualizar_titulo(self, titulo: str) -> None:
        self._titulo = titulo
        self._nombre.value = titulo

    def poner_valores(self, puntos: int, valores: dict[str, float]) -> None:
        """Llena la fila con totales guardados (US-114, editar)."""
        for attr, celda in self.celdas.items():
            celda.value = _texto_valor(valores.get(attr, 0))
        self.campo_puntos.value = str(puntos)
        self.campo_puntos.read_only = self._hay_tiros()

    def _hay_tiros(self) -> bool:
        return any(_sumar_sin_error(self.celdas, a) for a in ("t2c", "t2l", "t3c", "t3l", "t1c", "t1l"))

    def _recalcular(self) -> None:
        # Con tiros cargados los puntos se calculan (y no se pueden escribir); sin tiros se escriben a mano
        if self._hay_tiros():
            self.campo_puntos.value = str(_puntos({a: _sumar_sin_error(self.celdas, a) for a in self.celdas}))
            self.campo_puntos.read_only = True
        else:
            self.campo_puntos.read_only = False
        if self._al_cambiar is not None:
            self._al_cambiar()

    @property
    def puntos(self) -> int:
        try:
            return int((self.campo_puntos.value or "0").strip() or 0)
        except ValueError:
            return 0

    def leer(self, id_club: int) -> TotalesEquipoDTO:
        """
        Valida la fila y devuelve los totales del equipo.

        Raises:
            DatoInvalidoError: Si falta el puntaje, una celda no es numerica o los totales son incoherentes.
        """
        self.error.value = ""
        self.error.visible = False
        self.campo_puntos.error = None
        try:
            valores = _leer_numeros(self.celdas, COLUMNAS_TOTALES, self._titulo) or dict.fromkeys(self.celdas, 0)
            texto_pts = (self.campo_puntos.value or "").strip()
            if not texto_pts:
                self.campo_puntos.error = "!"
                raise DatoInvalidoError(f"{self._titulo}: cargá al menos los puntos del equipo.")
            try:
                puntos = int(texto_pts)
            except ValueError as err:
                self.campo_puntos.error = "!"
                raise DatoInvalidoError(f"{self._titulo}: los puntos tienen que ser un número entero.") from err
            enteros = {a: int(v) for a, v in valores.items()}
            try:
                EstadisticaEquipo(idClub=id_club, puntos=puntos, **enteros)
            except DatoInvalidoError as err:
                raise DatoInvalidoError(f"{self._titulo}: {err}") from err
        except DatoInvalidoError as err:
            self.error.value = str(err)
            self.error.visible = True
            raise
        return TotalesEquipoDTO(idClub=id_club, puntos=puntos, **enteros)
