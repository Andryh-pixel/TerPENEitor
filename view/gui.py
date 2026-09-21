import ttkbootstrap as ttk
from ttkbootstrap.scrolled import ScrolledText
import config.bot_config as config
import view.comandos as comandos #Impotamos comandos
import os
import sys
import threading
import pystray
from PIL import Image
import config.ftp_config as ftp_config


#definimos el tema de la app
app = ttk.Window(themename="vapor")

# Tray icon global para no recrear el icono cada vez
icon = None
tray_thread = None

# Configuración de ruta para el icono 
# Usamos DIRECTORIO_BASE de bot_config para una ruta consistente a la raíz del proyecto
if getattr(sys, 'frozen', False):
    ruta_icono = os.path.join(os.path.dirname(sys.executable), "smile.ico")
else:
    ruta_icono = os.path.join(config.DIRECTORIO_BASE, "smile.ico")


try:
    if os.path.exists(ruta_icono):
        app.iconbitmap(ruta_icono)
except Exception:
    pass # Evita que la app muera si el icono no se encuentra

#tamaño de la ventana
ancho = 920
alto = 700

#obtenr el tamaño de la pantalla
pantalla_ancho = app.winfo_screenwidth()
pantalla_alto = app.winfo_screenheight()

#calcular posicion de la ventana
x = int((pantalla_ancho / 2) - (ancho / 2))
y = int((pantalla_alto / 2) - (alto / 2))

#renderizar la ventana
app.geometry(f"{ancho}x{alto}+{x}+{y}")
        

app.columnconfigure(0, weight=1)
app.columnconfigure(1, weight=0)

app.rowconfigure(0, weight=1)

#frame para las posiciones
frame = ttk.Frame(app, padding=20)
frame.place(relx=0.5, # lados
            rely=0.5, # altura
            anchor="center") # definir donde inician

frame.columnconfigure(0, weight=1)
frame.columnconfigure(1, weight=1)
frame.columnconfigure(2, weight=1)
frame.rowconfigure(1, weight=1)

# Funciones de ayuda para 
def escribir_log(texto):
    #configuracionde la text box
    def update():
        txt_logs.text.configure(state= "normal")
        txt_logs.insert("end", f"> {texto}\n")
        txt_logs.see("end")
        txt_logs.text.configure(state="disabled")
    app.after(0, update)

# El logger central muestra los mensajes en la GUI (logs, errores de hooks, yt-dlp, etc.)
from config.logger import set_gui_callback as _set_gui_logger
_set_gui_logger(escribir_log)

def restaurar_ventana(icon, item):
    # Vuelve a mostrar la ventana desde la bandeja sin detener el icono
    app.after(0, app.deiconify)

def salir_total(icon_item, item):
    # Cierra el bot y la aplicación completamente desde la bandeja
    global icon
    if icon:
        icon.stop()
        icon = None
    try:
        config.detener_bot()
    except:
        pass
    app.after(0, app.destroy)

def crear_tray():
    # Configura y ejecuta el icono en la bandeja de sistema
    global icon
    if icon:
        return

    try:
        image = Image.open(ruta_icono)
        menu = pystray.Menu(
            pystray.MenuItem("Abrir", restaurar_ventana),
            pystray.MenuItem("Salir", salir_total)
        )
        icon = pystray.Icon("BotDiscord", image, "TerPENEitor", menu)
        icon.run()
    except Exception as e:
        print(f"Error al crear el tray icon: {e}")

def cerrar_aplicacion():
    """Oculta la ventana y activa el icono en la bandeja al presionar la X."""
    global tray_thread
    app.withdraw()
    # Ejecutamos el tray en un hilo separado para no congelar la gui
    if not tray_thread or not tray_thread.is_alive():
        tray_thread = threading.Thread(target=crear_tray, daemon=True)
        tray_thread.start()

def salir_completamente():
    """Detiene el bot y cierra la aplicación completamente."""
    try:
        config.detener_bot()
    except Exception:
        pass
    app.after(0, app.destroy)

def boton_on():
    escribir_log("Estimulando a TerPENEitor...")
    config.iniciar_bot()

def boton_off():
    escribir_log("TerPENEitor fulmino...")
    config.detener_bot()

def probar_ftp_hilo():
    """
    Realiza la prueba de conexión en un hilo secundario para evitar 
    que la interfaz se congele durante el tiempo de espera (timeout).
    """
    escribir_log("\nVerificando conexión con el cerebro de terPENE...")
    try:
        # La conversión a int se hace aquí para que si falla no congele la GUI
        puerto_validado = int(ftp_config.FTP_PORT) if ftp_config.FTP_PORT else 21
        ftp_config.probar_conexion_ftp(
            ftp_config.FTP_HOST,
            puerto_validado,
            ftp_config.FTP_USER,
            ftp_config.FTP_PASS
        )
        escribir_log("Se le conecto el cerebro a terPENEitor exitosamente")
    except ValueError:
        escribir_log("Error: El puerto ingresado debe ser un número válido.")
    except Exception as e:
        escribir_log(f"Error al conectar: {e}")

def procesar_entrada(event):
    # Esta función se activa al presionar Enter
    if txt_logs.text.cget("state") == "normal":
        # Obtenemos el texto de la línea donde está el cursor
        linea = txt_logs.text.get("insert linestart", "insert lineend")
        
        # Simulamos el comportamiento de input() buscando la etiqueta
        if "HOST: " in linea:
            ip_ingresada = linea.split("HOST: ")[-1].strip()
            if ip_ingresada:
                ftp_config.FTP_HOST = ip_ingresada
                txt_logs.insert("end", "\nPORT: ")
                txt_logs.see("end")
                return "break"

        elif "PORT: " in linea:
            puerto = linea.split("PORT: ")[-1].strip()
            if puerto:
                ftp_config.FTP_PORT = puerto
                txt_logs.insert("end", "\nUSER: ")
                txt_logs.see("end")
                return "break"

        elif "USER: " in linea:
            usuario = linea.split("USER: ")[-1].strip()
            if usuario:
                ftp_config.FTP_USER = usuario
                txt_logs.insert("end", "\nPASS: ")
                txt_logs.see("end")
                return "break"

        elif "PASS: " in linea:
            password = linea.split("PASS: ")[-1].strip()
            if password:
                ftp_config.FTP_PASS = password
                threading.Thread(target=probar_ftp_hilo, daemon=True).start()
                return "break"

    return None # Permite que el Enter siga creando una línea nueva si lo deseas

def boton_ftp():
    txt_logs.text.configure(state="normal")
    txt_logs.text.focus_set()# Pone el cursor automáticamente en el texto
    txt_logs.insert("end", "\nHOST: ") 
    txt_logs.see("end")


#botones
#definir parametros
ttk.Button(frame, 
           text="On",
           bootstyle="success",#estilo
           #tamaño del boton
           padding=(25, 15),
           width=12,
           command=boton_on
           ).grid(row=0, column=0, padx=10)
            
ttk.Button(frame, 
           text="Off", 
           bootstyle="warning",
           padding=(25, 15),
           width=12,
           command=boton_off
           ).grid(row=0, column=2, padx=10)

ttk.Button(frame, 
           text="FTP", 
           bootstyle="info",
           padding=(25, 15),
           width=12,
           command=boton_ftp
           ).grid(row=0, column=1, padx=10)

# Botón Salir completo ubicado al final de la ventana
ttk.Button(frame, 
           text="Salir", 
           bootstyle="danger",
           padding=(25, 15),
           width=12,
           command=salir_completamente
           ).grid(row=3, column=1, pady=(15, 0))

# añadir diseño a la text box
txt_logs = ScrolledText(frame, 
                        height=12, 
                        width=62, 
                        autohide=True, 
                        state="disabled",
                        font= 18)


# La ubicamos en la fila 1 (debajo de los botones) y que ocupe las 3 columnas
txt_logs.grid(row=2, column=0, columnspan=3, pady=20, sticky="nsew")

# Vinculamos el evento de la tecla Enter al widget de texto
txt_logs.text.bind("<Return>", procesar_entrada)

app.title("Bot Discord")

# Capturar el evento de cierre (X) para enviarlo a la bandeja
app.protocol("WM_DELETE_WINDOW", cerrar_aplicacion)
