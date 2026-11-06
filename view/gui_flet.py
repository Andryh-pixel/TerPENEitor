import sys
from pathlib import Path

import flet as ft

import config.bot_config as config
from config.logger import set_gui_callback
from modules.acrilico_win32 import activar_acrilico, reaplicar_acrilico
from modules.componets import Encabezado, Taskbar, colors
from view.config_view import config as config_view
from view.ftp_view import ftp
from view.home_view import home

#verifica si el archivo es exe o no, si es exe toma la ruta del exe, si no, toma la ruta del archivo actual
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent


async def app(page: ft.Page):
    page.bgcolor = colors.TRANSPARENT
    page.window.bgcolor = colors.TRANSPARENT
    page.padding = 0
    page.spacing = 0

    page.title = "TerPENEitor"#turulo para toda la app
    page.window.icon = str(BASE_DIR / "smile.ico")#icono para toda la app
    page.window.width = 1050
    page.window.height = 650
    page.window.min_width = 800
    page.window.min_height = 550
    page.window.frameless = True
    page.window.title_bar_hidden = True
    page.window.title_bar_buttons_hidden = True
    page.window.resizable = True
    page.window.on_event = lambda e: reaplicar_acrilico()

    async def btn_min(e):
        page.window.minimized = True
        page.update()

    async def btn_max(e):
        page.window.maximized = not page.window.maximized
        page.update()

    async def btn_close(e):
        await page.window.close()

    taskbar = Taskbar()

    async def mostrar_log(texto):
        actual = taskbar.textbox.value or ""
        taskbar.textbox.value = f"{actual.rstrip()}\n> {texto}".lstrip()
        taskbar.textbox.update()

    def escribir_log(texto):
        if texto.startswith("[acrilico]"):
            return
        page.run_task(mostrar_log, texto)

    set_gui_callback(escribir_log)

    def boton_on(e):
        escribir_log("Estimulando a TerPENEitor...")
        config.iniciar_bot()

    def boton_off(e):
        escribir_log("TerPENEitor fulmino...")
        config.detener_bot()

    def cambiar_vista(vista):
        contenido.content = vista
        contenido.update()

    async def boton_salir(e):
        try:
            config.detener_bot()
        finally:
            await page.window.close()

    async def boton_ftp(e):
        cambiar_vista(ftp())

    async def boton_home(e):
        cambiar_vista(home())

    async def boton_config(e):
        cambiar_vista(config_view())

    taskbar.boton_on.on_click = boton_on
    taskbar.boton_off.on_click = boton_off
    taskbar.boton_salir.on_click = boton_salir
    taskbar.boton_ftp.on_click = boton_ftp
    taskbar.boton_home.on_click = boton_home
    taskbar.boton_config.on_click = boton_config

    encabezado = Encabezado(on_min=btn_min,
                            on_max=btn_max,
                            on_close=btn_close,)
    
    contenido = ft.Container(
    expand=True,)
    contenido.content = home()

    ventana = ft.Container(
        content=ft.Column(
            controls=[
                encabezado,
                ft.Row(
                    controls=[
                        taskbar,
                        contenido,
                    ],
                    spacing=0,
                    expand=True,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,     
                ),
            ],
            spacing=0,
            expand=True,
            
        ),
        padding=0,
        expand=True,
    )

    page.add(ventana)
    page.update()
    activar_acrilico()