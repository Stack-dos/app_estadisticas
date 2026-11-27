"""Componente reutilizable de puntos por cuarto/prorroga (US-108, reusado en US-201)."""

from collections.abc import Callable

import flet as ft

from aplicacion.dtos.partido_dto import CuartoDTO
from dominio.exceptions import DatoInvalidoError
from infraestructura.ui.flet.estilo import ESPACIO_CHICO

CUARTOS_INICIALES = 4
ANCHO_CASILLERO_CUARTO = 74
CLAVE_BLOQUE_CUARTOS = "bloque_puntos_por_cuarto"


def etiqueta_periodo(nro_cuarto: int) -> str:
    """Devuelve 'Q1'..'Q4' para los cuartos regulares y 'PR1', 'PR2'... para prorrogas."""
    if nro_cuarto <= CUARTOS_INICIALES:
        return f"Q{nro_cuarto}"
    return f"PR{nro_cuarto - CUARTOS_INICIALES}"


class BloquePuntosPorCuarto:
    """Bloque opcional con 4 casilleros por equipo y boton para agregar prorrogas."""

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

        self._lbl_local = ft.Text(nombre_local, weight=ft.FontWeight.W_600, width=140)
        self._lbl_visitante = ft.Text(nombre_visitante, weight=ft.FontWeight.W_600, width=140)
        self._fila_local = ft.Row(spacing=ESPACIO_CHICO, wrap=True)
        self._fila_visitante = ft.Row(spacing=ESPACIO_CHICO, wrap=True)

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
                self._fila_local,
                self._fila_visitante,
                self._boton_prorroga,
            ],
        )
        self._reconstruir_filas()

    def _agregar_campos_periodo(self, nro_cuarto: int) -> None:
        etiqueta = etiqueta_periodo(nro_cuarto)
        self._campos_local.append(
            ft.TextField(
                label=f"Local {etiqueta}",
                width=ANCHO_CASILLERO_CUARTO,
                keyboard_type=ft.KeyboardType.NUMBER,
                dense=True,
            )
        )
        self._campos_visitante.append(
            ft.TextField(
                label=f"Visitante {etiqueta}",
                width=ANCHO_CASILLERO_CUARTO,
                keyboard_type=ft.KeyboardType.NUMBER,
                dense=True,
            )
        )

    def _reconstruir_filas(self) -> None:
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
