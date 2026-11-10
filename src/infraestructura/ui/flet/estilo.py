"""Tema de la GUI (US-111): el unico lugar donde se escriben colores, letras, espaciados y anchos.

La combinacion se eligio en el muestrario el 2026-11-09 (propuesta "Pizarra", modificada): semilla
#4A5866 en variante tonal, menu lateral, densidad comoda, campos con relleno, boton principal de
ancho completo, esquinas suaves de 8 px e IBM Plex Sans. Las pantallas y los componentes importan
estas constantes; ninguna escribe un color ni un numero de espaciado propio (AC1).

Los colores no se eligen uno por uno: Material 3 arma toda la paleta (principal, superficies,
error...) a partir de la semilla, y las pantallas usan los roles (`ft.Colors.PRIMARY`,
`ft.Colors.ERROR`...), asi el modo oscuro sale de la misma semilla.
"""

import flet as ft

COLOR_SEMILLA = "#4A5866"

# Letra: va empaquetada en src/assets/ (la app funciona sin internet). Ruta relativa a assets_dir.
FUENTE = "IBM Plex Sans"
ARCHIVO_FUENTE = "fuentes/IBMPlexSans.ttf"

# Logo (US-111, AC6). Rutas relativas a assets_dir.
LOGO = "logo/statspro-isotipo.svg"
LOGO_BLANCO = "logo/statspro-isotipo-blanco.svg"
NOMBRE_APP = "StatsPro"
LEMA_APP = "Estadísticas de básquet para entrenadores"

# Espaciados (densidad comoda): entre controles de un grupo, entre grupos y margen de la pagina.
ESPACIO_CHICO = 8
ESPACIO = 16
ESPACIO_GRANDE = 24

# Tamaños de letra
TAMANIO_TITULO = 24
TAMANIO_MARCA = 32

# Esquinas suaves: botones, campos y tarjetas
RADIO = 8

# Anchos
ANCHO_FORMULARIO = 400  # formularios de una columna (login, registro, alta)
ANCHO_MAXIMO = 1100  # el contenido no se estira de borde a borde en una ventana maximizada
TAMANIO_LOGO_MENU = 44
TAMANIO_LOGO_MARCA = 120

# Ventana: arranca en un tamaño que entra en una notebook de 1366x768 y no se achica de mas
VENTANA_ANCHO = 1280
VENTANA_ALTO = 720
VENTANA_ANCHO_MINIMO = 960
VENTANA_ALTO_MINIMO = 600


def crear_tema() -> ft.Theme:
    """
    Arma el tema de Material 3 a partir de la semilla. Sirve para el modo claro y para el oscuro.

    Returns:
        ft.Theme: Paleta (variante tonal, la que Flet calcula por defecto), letra, campos con relleno
            y esquinas de `RADIO` en botones, campos y tarjetas.
    """
    esquinas = ft.RoundedRectangleBorder(radius=RADIO)
    estilo_boton = ft.ButtonStyle(shape=esquinas)
    return ft.Theme(
        color_scheme_seed=COLOR_SEMILLA,
        font_family=FUENTE,
        input_decoration_theme=ft.InputDecorationTheme(
            filled=True,
            # Campo con relleno: solo las esquinas de arriba van redondeadas, abajo queda la linea
            border=ft.UnderlineInputBorder(border_radius=ft.BorderRadius.only(top_left=RADIO, top_right=RADIO)),
        ),
        filled_button_theme=ft.FilledButtonTheme(style=estilo_boton),
        button_theme=ft.ButtonTheme(style=estilo_boton),
        text_button_theme=ft.TextButtonTheme(style=estilo_boton),
        card_theme=ft.CardTheme(shape=esquinas),
    )


def aplicar_tema(page: ft.Page) -> None:
    """
    Aplica a la ventana el tema, la letra y el tamaño. Lo llama `app.py` una sola vez, al arrancar.

    El modo oscuro usa el mismo tema: sin `dark_theme`, si Windows esta en oscuro Flet pondria su
    paleta azul por defecto. El resto del modo oscuro (elegirlo a mano, revisar cada pantalla) es de
    la US-401.

    Args:
        page (ft.Page): La ventana que entrega Flet.
    """
    page.title = NOMBRE_APP
    page.fonts = {FUENTE: ARCHIVO_FUENTE}
    page.theme = crear_tema()
    page.dark_theme = crear_tema()
    page.window.width = VENTANA_ANCHO
    page.window.height = VENTANA_ALTO
    page.window.min_width = VENTANA_ANCHO_MINIMO
    page.window.min_height = VENTANA_ALTO_MINIMO
