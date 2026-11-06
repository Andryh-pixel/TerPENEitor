# Instalamos los capturadores globales de errores ANTES de importar nada más,
# para registrar en archivos cualquier fallo durante el arranque.
from config.logger import instalar_hooks_globales

instalar_hooks_globales()

import sys
from pathlib import Path

import flet as ft

from view.gui_flet import app

#verifica si el archivo es exe o no, si es exe toma la ruta del exe, si no, toma la ruta del archivo actual
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    # Iniciamos la interfaz gráfica, la cual permite controlar el bot
    try:
        ft.run(app, assets_dir=str(BASE_DIR / "assets"))
    except KeyboardInterrupt:
        print("Aplicación cerrada desde la terminal.")