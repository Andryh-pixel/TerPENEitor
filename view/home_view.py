import flet as ft

from modules.componets import colors


def home():
    return ft.Container(
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