# Instalamos los capturadores globales de errores ANTES de importar nada más,
# para registrar en archivos cualquier fallo durante el arranque.
from config.logger import instalar_hooks_globales
instalar_hooks_globales()

from view.gui import app

if __name__ == "__main__":
    # Iniciamos la interfaz gráfica, la cual permite controlar el bot
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("Aplicación cerrada desde la terminal.")
