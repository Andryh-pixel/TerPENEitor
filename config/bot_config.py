import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
import threading
import asyncio
import config.keys as keys
import importlib
from config.logger import registrar, registrar_error, instalar_hooks_globales, set_gui_callback

# Captura excepciones fuera de los manejadores (hilos, callbacks sueltos)
instalar_hooks_globales()

#configuracion de los permisos que tendra el bot
intenciones = discord.Intents.none()
intenciones.guilds = True
intenciones.voice_states = True

# Definimos la variable global pero no la inicializamos aquí permanentemente
bot = None

def configurar_bot():
    """Crea una nueva instancia del bot y define sus eventos."""
    global bot
    bot = commands.Bot(command_prefix="!", intents=intenciones)

    @bot.event
    async def on_ready():
        try:
            enviar_a_log("Sincronizando comandos...")
            sincro = await bot.tree.sync()
            enviar_a_log(f"{len(sincro)} comandos se sincronizaron correctamente.")
        except Exception as e:
            registrar_error("Error al sincronizar comandos", exc=e)

        enviar_a_log(f"{bot.user} se ha herectado correctamente.")

    @bot.event
    async def on_error(event_method, *args, **kwargs):
        # Errores dentro de eventos de discord.py que nadie capturó.
        registrar_error(f"Excepción en el evento '{event_method}'")

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        # Errores no capturados dentro de un comando slash.
        nombre = interaction.command.qualified_name if interaction.command else "desconocido"
        registrar_error(f"Error en el comando slash /{nombre}", exc=error)
        try:
            if interaction.response.is_done():
                await interaction.followup.send("Ocurrió un error interno. Revisa los logs.", ephemeral=True)
            else:
                await interaction.response.send_message("Ocurrió un error interno. Revisa los logs.", ephemeral=True)
        except Exception:
            pass

# Ejecutamos la configuración inicial
configurar_bot()

def enviar_a_log(texto):
    """Registra un mensaje: archivo de logs del día + consola + GUI si está abierta."""
    registrar(texto)
    print(texto)


def iniciar_bot():
    #Lanza el bot en un hilo separado para no bloquear la gui
    global bot

    if not keys.TOKEN:
        enviar_a_log("No se encontró el token de Discord. Revisa el archivo .env del proyecto o del ejecutable.")
        return

    # Si el bot ya existe y fue cerrado anteriormente, necesitamos una instancia nueva.
    # discord.py no permite re-utilizar una instancia que ya ejecutó close().
    if bot and bot.is_closed():
        enviar_a_log("Limpiando fluidos y reiniciando a TerPENEitor...")
        configurar_bot()
        # Recargamos el módulo de comandos para que se registren en la nueva instancia del bot
        try:
            import view.comandos
            importlib.reload(view.comandos)
        except Exception as e:
            enviar_a_log(f"Error al recargar comandos: {e}")

    if bot and bot.is_ready():
        enviar_a_log("El bot ya está encendido.")
        return

    def _run_bot():
        try:
            bot.run(keys.TOKEN)
        except Exception as e:
            enviar_a_log(f"Error al conectar con Discord: {e}")

    threading.Thread(target=_run_bot, daemon=True).start()


def detener_bot():
    # Cierra la conexión del bot de forma segura
    if not bot or bot.is_closed():
        return

    if bot.loop.is_closed():
        enviar_a_log("El loop del bot ya está cerrado.")
        return

    try:
        from view.comandos import close_aiohttp_session
        close_session_future = asyncio.run_coroutine_threadsafe(close_aiohttp_session(), bot.loop)
        try:
            close_session_future.result(timeout=5)
        except Exception:
            pass
    except Exception:
        pass

    try:
        asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
        enviar_a_log("💧 🩲 🥵")
    except RuntimeError:
        enviar_a_log("Error al cerrar el bot: el loop ya estaba cerrado.")

#verificacion de ffmpeg, para saber donde se ejecuta si en codigo o .exe
# Define DIRECTORIO_BASE para que siempre apunte a la raíz del proyecto
if getattr(sys, 'frozen', False):
    DIRECTORIO_BASE = os.path.dirname(sys.executable)
else:
    DIRECTORIO_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RUTA_FFMPEG = os.path.join(DIRECTORIO_BASE, "ffmpeg.exe")
