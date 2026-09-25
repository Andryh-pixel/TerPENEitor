import sys

from cx_Freeze import Executable, setup

import davey
import nacl

# Opciones de construcción
build_exe_options = {
    # Incluimos los paquetes necesarios para el bot
    "packages": [
        "discord",
        "yt_dlp",
        "yt_dlp_ejs",
        "aiohttp",
        "asyncio",
        "json",
        "os",
        "nacl",
        "_cffi_backend",
        "davey",
        "ttkbootstrap",
        "pystray",
        "PIL",
        "ftplib",
        "dotenv",
        "modules",
        "view"
    ],

    # Incluimos archivos externos esenciales
    "include_files": [
        "ffmpeg.exe",
        "qjs.exe",
        "smile.ico",
        "version.txt",
        ("config", "config"),
        ("config/.env", "config/.env"),

        # Forzar librerías por fallas detectadas
        (nacl.__path__[0], "nacl"),
        (davey.__path__[0], "davey")
    ],
}


base = None

if sys.platform == "win32":
    base = "Win32GUI"


setup(
    name="TerPENEitor",
    version="1.5.5",
    description="Bot de Discord",

    options={
        "build_exe": build_exe_options
    },

    executables=[
        # ESTE ES EL ACTUALIZADOR
        Executable(
            "view/gui_updater.py",
            base="Win32GUI",
            target_name="TerPENEitor.exe",
            icon="smile.ico"
        ),

        # ESTE ES EL BOT REAL
        Executable(
            "main.py",
            base=base,
            target_name="verificador.exe",
            icon="smile.ico"
        )
    ]
)