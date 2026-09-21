import os
import sys
from dotenv import load_dotenv


def encontrar_ruta_env():
    """Busca .env en varias ubicaciones para que funcione en desarrollo y en el .exe."""
    posibles_rutas = []

    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
        posibles_rutas.extend([
            os.path.join(base, ".env"),
            os.path.join(base, "config", ".env"),
        ])
    else:
        base = os.path.dirname(os.path.abspath(__file__))
        posibles_rutas.extend([
            os.path.join(base, ".env"),
            os.path.join(base, "..", ".env"),
            os.path.join(base, "config", ".env"),
        ])

    posibles_rutas.extend([
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.getcwd(), "config", ".env"),
    ])

    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            return ruta

    return None


ruta_env = encontrar_ruta_env()
if ruta_env:
    load_dotenv(dotenv_path=ruta_env, override=False)
else:
    print("Advertencia: no se encontró ningún archivo .env para el bot.")

TOKEN = os.getenv("DISCORD_BOT")
if not TOKEN:
    print("Advertencia: no se encontró DISCORD_BOT en el archivo .env.")
