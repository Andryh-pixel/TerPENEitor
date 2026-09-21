import sys
from cx_Freeze import setup, Executable
import nacl
import davey

# Opciones de construcción
build_exe_options = {
    # Incluimos los paquetes necesarios para el bot
    "packages": ["discord", 
                 "yt_dlp", 
                 "yt_dlp_ejs", # Solver de retos JS de YouTube (requerido por yt-dlp nightly)
                 "aiohttp", 
                 "asyncio", 
                 "json", 
                 "os", 
                 "nacl", 
                 "_cffi_backend",
                 "davey",
                 "ttkbootstrap",
                 "pystray",
                 "PIL", # Pillow
                 "ftplib",
                 "dotenv" # Añadimos dotenv aquí
                ],
    # Incluimos archivos externos esenciales
    "include_files": [
        "ffmpeg.exe",
        "qjs.exe",   # Runtime JavaScript (quickjs-ng) para yt-dlp: evita el 403 de YouTube sin instalar Node/Deno en la PC destino
        "smile.ico",
        "version.txt",
        ("config", "config"),
        ("config/.env", "config/.env"),
        #forzar librerias por fallas detectadas
        (nacl.__path__[0], "nacl"),
        (davey.__path__[0], "davey") 
    ],
}


base = None
if sys.platform == "win32":
    base = "Win32GUI"  # Esto oculta la consola (CMD)
#definimos los atributos del exe
#nombre, version, descripcion, etc..
# indicamos que debe compilar

setup(
    name="TerPENEitor",
    version="1.5.2",
    description="Bot de Discord",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            target_name="TerPENEitor.exe",
            icon="smile.ico"
        )
    ]
)