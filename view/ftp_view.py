import asyncio

import flet as ft

import config.ftp_config as ftp_config
from modules.componets import btts, colors


def ftp():

    # formulario ftp
    ip = ft.TextField(
        label="Dirección IP",
        hint_text="192.168.1.100",
        width=250,
    )

    puerto = ft.TextField(
        label="Puerto",
        value="2221",
        width=100,
    )

    usuario = ft.TextField(
        label="Usuario",
        width=360,
    )

    contraseña = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        width=360,
    )

    # Este mensaje muestra validaciones y el resultado de la conexión FTP.
    estado_ip = ft.Text(color=colors.TEXT_LIGHT)

    def pasar_ftp(_e):
        # 1. Leer los campos y quitar espacios accidentales en sus extremos.
        ip_ingresada = (ip.value or "").strip()
        port_ingresado = (puerto.value or "").strip()
        usuario_ingresado = (usuario.value or "").strip()
        contraseña_ingresada = (contraseña.value or "").strip()

        # 2. Validar que se hayan ingresado todos los datos requeridos.
        if not ip_ingresada:
            estado_ip.value = "Ingresa la dirección IP."
            estado_ip.color = colors.RED
            estado_ip.update()
            return False
        if not port_ingresado:
            estado_ip.value = "Ingresa el puerto."
            estado_ip.color = colors.RED
            estado_ip.update()
            return False
        if not usuario_ingresado:
            estado_ip.value = "Ingresa el usuario."
            estado_ip.color = colors.RED
            estado_ip.update()
            return False
        if not contraseña_ingresada:
            estado_ip.value = "Ingresa la contraseña."
            estado_ip.color = colors.RED
            estado_ip.update()
            return False

        # 3. Comprobar que el puerto sea un número dentro del rango TCP válido.
        try:
            puerto_validado = int(port_ingresado)
            if not 1 <= puerto_validado <= 65535:
                raise ValueError
        except ValueError:
            estado_ip.value = "El puerto debe ser un número entre 1 y 65535."
            estado_ip.color = colors.RED
            estado_ip.update()
            return False

        # 4. Guardar los datos validados para que los use la conexión FTP.
        ftp_config.FTP_HOST = ip_ingresada
        ftp_config.FTP_PORT = str(puerto_validado)
        ftp_config.FTP_USER = usuario_ingresado
        ftp_config.FTP_PASS = contraseña_ingresada

        # 5. Indicar que los datos son válidos; aún falta probar la conexión.
        estado_ip.value = "Datos guardados. Conectando con el servidor FTP..."
        estado_ip.color = colors.TEXT_LIGHT
        estado_ip.update()
        return True

    async def conectar_ftp(_e):
        # 1. Validar y guardar en el hilo de la interfaz; no es una operación de red.
        if not pasar_ftp(_e):
            return

        try:
            # 2. Ejecutar el FTP síncrono en un hilo para no bloquear la interfaz.
            await asyncio.to_thread(
                ftp_config.probar_conexion_ftp,
                ftp_config.FTP_HOST,
                ftp_config.FTP_PORT,
                ftp_config.FTP_USER,
                ftp_config.FTP_PASS,
            )

            # 3. Obtener la lista también en un hilo, porque usa ftplib de forma síncrona.
            canciones = await asyncio.to_thread(
                ftp_config.obtener_musica_ftp,
                raise_errors=True,
            )

            # 4. Mostrar el resultado de la conexión y la cantidad de canciones halladas.
            estado_ip.value = (
                f"Conexión FTP exitosa. Canciones encontradas: {len(canciones)}."
            )
            estado_ip.color = colors.TEXT_LIGHT
        except Exception as ex:
            # 5. Informar el error de red o autenticación sin ocultarlo.
            estado_ip.value = f"Error de conexión FTP: {ex}"
            estado_ip.color = colors.RED

        # 6. Reflejar el estado final en la interfaz.
        estado_ip.update()

    # El botón guarda la IP; todavía no valida ni conecta los otros campos.
    boton_conectar = btts("", "Conectar", on_click=conectar_ftp)
    boton_conectar._imagen.visible = False
    boton_conectar._capa_hover.content.controls[0].visible = False
    boton_conectar.content.controls[0].spacing = 0
    boton_conectar._capa_hover.content.spacing = 0
    boton_conectar.width = 140
    # Desplaza el botón a la derecha
    boton_conectar.margin = ft.Margin(left=60, top=0, right=0, bottom=0)

    # Contenedor principal
    return ft.Container(
        expand=True,
        bgcolor=colors.BG_CONTENT,
        border=ft.Border.all(0.5, colors.BORDER),
        padding=20,
        alignment=ft.Alignment.CENTER,

        content=ft.Container(
            width=400,

            content=ft.Column(
                controls=[
                    ft.Text(
                        "Configuración FTP",
                        size=24,
                        color=colors.TEXT_LIGHT,
                        text_align=ft.TextAlign.CENTER,
                    ),

                    ft.Row(
                        controls=[ip, puerto],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),

                    usuario,
                    contraseña,

                    ft.Row(
                        controls=[boton_conectar],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    estado_ip,
                ],
                spacing=15,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ),
    )