"""Componente reutilizable de puntos por cuarto/prorroga (US-108, reusado en US-201)."""

from collections.abc import Callable

import flet as ft

from aplicacion.dtos.partido_dto import CuartoDTO
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.estilo import ESPACIO_CHICO

CUARTOS_INICIALES = 4
ANCHO_CASILLERO_CUARTO = 56
ANCHO_NOMBRE_EQUIPO = 160
CLAVE_BLOQUE_CUARTOS = "bloque_puntos_por_cuarto"


def clave_casillero_cuarto(rol: str, nro_cuarto: int) -> str:
    """`key` del casillero de un periodo ("cuarto · local · Q1"): no lleva rotulo, la columna dice el periodo."""
    return f"cuarto · {rol} · {etiqueta_periodo(nro_cuarto)}"


def etiqueta_periodo(nro_cuarto: int) -> str:
    """Devuelve 'Q1'..'Q4' para los cuartos regulares y 'PR1', 'PR2'... para prorrogas."""
    if nro_cuarto <= CUARTOS_INICIALES:
        return f"Q{nro_cuarto}"
    return f"PR{nro_cuarto - CUARTOS_INICIALES}"


def filas_cuartos(
    cuartos: list[CuartoDTO], equipos: list[tuple[int, str]]
) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
    """
    Arma la tabla de puntos por cuarto: una columna por periodo y el total.

    Args:
        cuartos (list[CuartoDTO]): Los cuartos guardados (pueden faltar periodos de un equipo).
        equipos (list[tuple[int, str]]): `(idClub, nombre)` de local y visitante, en ese orden.

    Returns:
        tuple: Las columnas ("Equipo", "Q1".., "Total") y una fila por equipo ("—" si falta un periodo).
    """
    periodos = max((c.nroCuarto for c in cuartos), default=0)
    columnas = ("Equipo", *(etiqueta_periodo(nro) for nro in range(1, periodos + 1)), "Total")
    puntos = {(c.idClub, c.nroCuarto): c.puntos for c in cuartos}
    filas = []
    for id_club, nombre in equipos:
        valores = [puntos.get((id_club, nro)) for nro in range(1, periodos + 1)]
        total = sum(v for v in valores if v is not None)
        filas.append((nombre, *("—" if v is None else str(v) for v in valores), str(total)))
    return columnas, filas


class BloquePuntosPorCuarto:
    """Bloque opcional con 4 casilleros por equipo y boton para agregar prorrogas.

    Se ve como una grilla chica: una fila de encabezados (Q1..Q4, PR1...) y una fila por equipo.
    """

    def __init__(
        self,
        nombre_local: str = "Local",
        nombre_visitante: str = "Visitante",
        al_cambiar: Callable[[], None] | None = None,
    ) -> None:
        self._nombre_local = nombre_local
        self._nombre_visitante = nombre_visitante
        self._al_cambiar = al_cambiar
        self._cantidad_periodos = CUARTOS_INICIALES

        self._campos_local: list[ft.TextField] = []
        self._campos_visitante: list[ft.TextField] = []

        self._lbl_local = self._nombre_equipo(nombre_local)
        self._lbl_visitante = self._nombre_equipo(nombre_visitante)
        self._fila_encabezados = ft.Row(spacing=ESPACIO_CHICO)
        self._fila_local = ft.Row(spacing=ESPACIO_CHICO)
        self._fila_visitante = ft.Row(spacing=ESPACIO_CHICO)

        for nro in range(1, CUARTOS_INICIALES + 1):
            self._agregar_campos_periodo(nro)

        self._boton_prorroga = ft.TextButton("Agregar prórroga", on_click=self.agregar_prorroga)
        self.control = ft.Column(
            key=CLAVE_BLOQUE_CUARTOS,
            spacing=ESPACIO_CHICO,
            controls=[
                ft.Text("Puntos por cuarto (opcional)", weight=ft.FontWeight.W_600),
                ft.Text(
                    "Si dejás todos los casilleros vacíos, el partido se guarda sin parciales.",
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Row(
                    [
                        ft.Column(
                            [self._fila_encabezados, self._fila_local, self._fila_visitante],
                            spacing=ESPACIO_CHICO,
                        ),
                        self._boton_prorroga,
                    ],
                    wrap=True,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                ),
            ],
        )
        self._reconstruir_filas()

    @staticmethod
    def _nombre_equipo(nombre: str) -> ft.Text:
        return ft.Text(
            nombre,
            weight=ft.FontWeight.W_600,
            width=ANCHO_NOMBRE_EQUIPO,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

    @staticmethod
    def _casillero(rol: str, nro_cuarto: int) -> ft.TextField:
        return ft.TextField(
            key=clave_casillero_cuarto(rol, nro_cuarto),
            width=ANCHO_CASILLERO_CUARTO,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_align=ft.TextAlign.CENTER,
            dense=True,
        )

    def _agregar_campos_periodo(self, nro_cuarto: int) -> None:
        self._campos_local.append(self._casillero("local", nro_cuarto))
        self._campos_visitante.append(self._casillero("visitante", nro_cuarto))

    def _reconstruir_filas(self) -> None:
        self._fila_encabezados.controls = [
            ft.Container(width=ANCHO_NOMBRE_EQUIPO),
            *(
                ft.Text(
                    etiqueta_periodo(nro),
                    width=ANCHO_CASILLERO_CUARTO,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
                for nro in range(1, self._cantidad_periodos + 1)
            ),
        ]
        self._fila_local.controls = [self._lbl_local, *self._campos_local]
        self._fila_visitante.controls = [self._lbl_visitante, *self._campos_visitante]

    def actualizar_equipos(self, nombre_local: str, nombre_visitante: str) -> None:
        """Actualiza los nombres visibles de local y visitante sin borrar los valores cargados."""
        self._nombre_local = nombre_local
        self._nombre_visitante = nombre_visitante
        self._lbl_local.value = nombre_local
        self._lbl_visitante.value = nombre_visitante

    def agregar_prorroga(self) -> None:
        """Suma un nuevo periodo (PR1, PR2...) a ambos equipos."""
        self._cantidad_periodos += 1
        self._agregar_campos_periodo(self._cantidad_periodos)
        self._reconstruir_filas()
        if self._al_cambiar is not None:
            self._al_cambiar()

    def cargar_cuartos(self, cuartos: list[CuartoDTO], id_club_local: int, id_club_visitante: int) -> None:
        """Llena los casilleros con los cuartos de un partido guardado (US-114, editar), sumando prorrogas."""
        if not cuartos:
            return
        while self._cantidad_periodos < max(c.nroCuarto for c in cuartos):
            self._cantidad_periodos += 1
            self._agregar_campos_periodo(self._cantidad_periodos)
        self._reconstruir_filas()
        campos_por_club = {id_club_local: self._campos_local, id_club_visitante: self._campos_visitante}
        for cuarto in cuartos:
            campos = campos_por_club.get(cuarto.idClub)
            if campos is not None:
                campos[cuarto.nroCuarto - 1].value = str(cuarto.puntos)

    @property
    def cantidad_periodos(self) -> int:
        return self._cantidad_periodos

    def leer_cuartos(self, id_club_local: int, id_club_visitante: int) -> list[CuartoDTO]:
        """Lee los casilleros cargados y devuelve `list[CuartoDTO]` (vacia si no se cargo ninguno).

        Marca `field.error` en el casillero exacto si un valor no es un entero >= 0.
        """
        for campo in (*self._campos_local, *self._campos_visitante):
            campo.error = None

        todos_vacios = all(not (campo.value or "").strip() for campo in (*self._campos_local, *self._campos_visitante))
        if todos_vacios:
            return []

        cuartos: list[CuartoDTO] = []
        for id_club, rol, campos in (
            (id_club_local, "local", self._campos_local),
            (id_club_visitante, "visitante", self._campos_visitante),
        ):
            for nro, campo in enumerate(campos, start=1):
                texto = (campo.value or "").strip()
                if not texto:
                    continue
                try:
                    valor = int(texto)
                except ValueError as err:
                    campo.error = "Entero ≥ 0"
                    raise DatoInvalidoError(
                        f"El valor de {rol} {etiqueta_periodo(nro)} debe ser un número entero."
                    ) from err
                if valor < 0:
                    campo.error = "≥ 0"
                    raise DatoInvalidoError(f"Los puntos de {rol} {etiqueta_periodo(nro)} no pueden ser negativos.")
                cuartos.append(CuartoDTO(idClub=id_club, nroCuarto=nro, puntos=valor))

        return cuartos
