import flet as ft


class colors:
    TRANSPARENT = "transparent"

    WHITE = "#FFFFFF"
    RED = "#FF0000"

    BG_TASKBAR = "#99351C4D"
    BG_HEADER = "#99321B50"
    BG_CONTENT = "#9921132F"

    BORDER = "#CCCCCC"
    TEXT_LIGHT = "#F5EEFF"

    TEXT_BUTTON = "#78757B"


class btts (ft.Container):#clase que herada prpiedadees de container, 
                          #facilita la modificacion de los atributos

    def __init__(self, icono, texto, on_click=None):

        self.icono = icono
        self.texto = texto

        self._imagen = ft.Image(
            src=self.icono,
            width=22,
            height=22,
            color=colors.TEXT_BUTTON,
        )
        self._texto = ft.Text(
            value=self.texto,
            color=colors.TEXT_BUTTON,
        )

        self._capa_hover = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=self.icono,
                        width=22,
                        height=22,
                        color=colors.WHITE,
                    ),
                    ft.Text(
                        value=self.texto,
                        color=colors.WHITE,
                    ),
                ],
                spacing=12,
            ),
            opacity=0,
            animate_opacity=ft.Animation(
                250,
                ft.AnimationCurve.EASE_OUT,
            ),
        )

        super().__init__(
            content=ft.Stack(
                controls=[
                    ft.Row(
                        controls=[
                            self._imagen,
                            self._texto,
                        ],
                        spacing=12,
                    ),
                    self._capa_hover,
                ],
            ),

            padding=12,
            border_radius=10,

            animate_scale=ft.Animation(
                250,
                ft.AnimationCurve.EASE_OUT,
            ),

            on_hover=self.cambiar_escala,
            on_click=on_click,
        )

    def cambiar_escala(self, e):

        activo = str(e.data).lower() == "true"

        self.scale = 1.2 if activo else 1.0
        self._capa_hover.opacity = 1.0 if activo else 0.0

        self.update()

class Taskbar(ft.Container):

    def __init__(self):

        self.boton_home = btts("icons/house.svg", "Inico")
        self.boton_on = btts("icons/on.svg", "On")
        self.boton_ftp = btts("icons/ftp.svg", "FTP")
        self.boton_config = btts("icons/config.svg", "Configuración")
        self.boton_off = btts("icons/off.svg", "Off")
        self.boton_salir = btts("icons/exit.svg", "Salir")

        self.textbox = ft.TextField(
            label="Info",
            value=" ",
            read_only=True,
            expand=True,
            multiline=True,
            min_lines=6,
            max_lines=9,
            height=160,
            border=ft.InputBorder.OUTLINE,
            border_color=colors.BORDER,
            focused_border_color=colors.BORDER,
            border_width=0.5,
            border_radius=5,
            text_style=ft.TextStyle(
                color=colors.WHITE,
                size=12,
            ),
        )

        super().__init__(
            width=200,
            bgcolor=colors.BG_TASKBAR,
            border=ft.Border.all(0.5, colors.BORDER),
            border_radius=5,
            padding=10,
            content=ft.Stack(
                controls=[
                    ft.Container(self.boton_home, left=0, top=70),
                    ft.Container(self.boton_on, left=0, top=110),
                    ft.Container(self.boton_ftp, left=0, top=150),
                    ft.Container(self.boton_config, left=0.5, top=190),
                    ft.Container(self.boton_off, left=0, top=230),
                    ft.Container(self.boton_salir, left=0, top=270),
                    ft.Container(
                        content=self.textbox,
                        left=0,
                        right=0,
                        bottom=0,
                        height=160,
                    ),
                ],
                expand=True,
                fit=ft.StackFit.EXPAND,
            ),
        )


class Encabezado(ft.Container):

    def __init__(self, on_min=None, on_max=None, on_close=None):

        tamaño_bt = 16
        controles_ventana = ft.Row(
            controls=[
                ft.IconButton(ft.Icons.REMOVE,
                              on_click=on_min,
                              icon_size=tamaño_bt,
                              padding=4,
                              icon_color=colors.WHITE),
                ft.IconButton(ft.Icons.CROP_SQUARE,
                              on_click=on_max,
                              icon_size=tamaño_bt,
                              padding=4,
                              icon_color=colors.WHITE),
                ft.IconButton(ft.Icons.CLOSE,
                              on_click=on_close,
                              icon_size=tamaño_bt,
                              padding=4,
                              icon_color=colors.RED),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.END,
        )

        super().__init__(
            content=ft.WindowDragArea(
                content=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(
                                "TerPENEitor",
                                color=colors.WHITE,
                                size=15),
                            ft.Container(expand=True),
                            ft.Container(
                                content=controles_ventana,
                                margin=ft.Margin(0, -6, 0, 0),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=colors.BG_HEADER,
                    height=35,
                    padding=5,
                ),
                expand=False,
                maximizable=True,
            ),
        )