import sys

import davey
import nacl
from cx_Freeze import Executable, setup

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
        "flet",
        "ftplib",
        "dotenv",
        "modules",
    ],
    "includes": ["view.comandos"],

    # Incluimos archivos externos esenciales
    "include_files": [
        "ffmpeg.exe",
        "qjs.exe",
        "smile.ico",
        "version.txt",
        ("assets", "assets"),
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
    version="1.6.2",
    description="Bot de Discord",

    options={
        "build_exe": build_exe_options
    },

    executables=[
        Executable(
            "view/gui_updater.py",
            base="Win32GUI",
            target_name="TerPENEitor.exe",
            icon="smile.ico"
        ),
        Executable(
            "main.py",
            base=base,
            target_name="verificador.exe",
            icon="smile.ico"
        )
    ]
)