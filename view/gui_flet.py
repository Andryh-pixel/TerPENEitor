import flet as ft

import config.bot_config as config
from config.logger import set_gui_callback
from modules.acrilico_win32 import activar_acrilico, reaplicar_acrilico
from modules.componets import Encabezado, Taskbar, colors


async def app(page: ft.Page):
    page.bgcolor = colors.TRANSPARENT
    page.window.bgcolor = colors.TRANSPARENT
    page.padding = 0
    page.spacing = 0

    page.window.title = "TerPENEitor"
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

    async def boton_salir(e):
        try:
            config.detener_bot()
        finally:
            await page.window.close()

    taskbar.boton_on.on_click = boton_on
    taskbar.boton_off.on_click = boton_off
    taskbar.boton_salir.on_click = boton_salir

    encabezado = Encabezado(
        on_min=btn_min,
        on_max=btn_max,
        on_close=btn_close,
    )

    contenido = ft.Container(
        expand=True,
        bgcolor=colors.BG_CONTENT,
        border=ft.Border.all(0.5, colors.BORDER),
        padding=20,
        alignment=ft.Alignment.CENTER,
        content=ft.Text(
            "caratulas principal",
            color=colors.TEXT_LIGHT,
            size=20,
        ),
    )

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