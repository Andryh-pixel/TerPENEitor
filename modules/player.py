import discord
import asyncio
import os
import ftplib
import yt_dlp
import config.ftp_config as ftp_config
from config.bot_config import DIRECTORIO_BASE, RUTA_FFMPEG
from config.logger import registrar_error
from modules.youtube import construir_ydl_opts

cola = []
loop_activo = False

def _saltar_cancion(cola_local, cancion):
    """Elimina de la cola la canción que acaba de fallar para no reintentarla
    en bucle cuando loop_activo está encendido."""
    try:
        cola_local.remove(cancion)
    except ValueError:
        pass

class ContextoSlash:
    def __init__(self, interaccion):
        self.interaccion = interaccion
        self.bot = interaccion.client
        self.servidor = interaccion.guild
        self.canal = interaccion.channel
        self.autor = interaccion.user

    @property
    def voice_client(self):
        return self.servidor.voice_client

    async def send(self, contenido):
        await self.canal.send(contenido)

async def intentar_reproducir(vc, interaction):
    if not vc.is_playing():
        await reproducir_siguiente(ContextoSlash(interaction))
        return True
    return False

async def reproducir_siguiente(contexto):
    global loop_activo

    if len(cola) == 0:
        if contexto.voice_client:
            await contexto.voice_client.disconnect()
            await contexto.send("Cola vacía, desconectando del canal de voz.")
        return

    siguiente = cola[0] if loop_activo else cola.pop(0)
    url_original = siguiente['url']
    titulo = siguiente['title']

    stream_url = None
    headers = {}
    es_archivo_local = False

    if url_original.startswith("ftp://"):
        try:
            safe_title = "".join([c for c in titulo if c.isalnum() or c in (' ', '.', '_')]).strip()
            local_path = os.path.join(DIRECTORIO_BASE, f"temp_{safe_title}")
            
            def descargar():
                with ftplib.FTP() as ftp:
                    ftp.connect(ftp_config.FTP_HOST, int(ftp_config.FTP_PORT) if ftp_config.FTP_PORT else 21, timeout=10)
                    ftp.login(ftp_config.FTP_USER, ftp_config.FTP_PASS)
                    if ftp_config.FTP_DIR:
                        ftp.cwd(ftp_config.FTP_DIR)
                    with open(local_path, 'wb') as f:
                        ftp.retrbinary(f"RETR {titulo}", f.write)
            
            await contexto.bot.loop.run_in_executor(None, descargar)
            stream_url = local_path
            es_archivo_local = True
        except Exception as e:
            registrar_error(f"Descarga FTP fallida: {titulo}", exc=e)
            await contexto.send(f"No se pudo descargar **{titulo}**. Saltando.")
            _saltar_cancion(cola, siguiente)
            contexto.bot.loop.create_task(reproducir_siguiente(contexto))
            return

    elif any(x in url_original for x in ["youtube.com", "youtu.be", "soundcloud.com"]):
        try:
            info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: yt_dlp.YoutubeDL(construir_ydl_opts()).extract_info(url_original, download=False)
            )
            stream_url = info.get('url')
            headers = info.get('http_headers', {})
            if not stream_url and 'entries' in info:
                stream_url = info['entries'][0].get('url')
            
            if not stream_url:
                raise RuntimeError("yt-dlp no devolvió ninguna URL de stream")
        except Exception as e:
            registrar_error(f"Extracción de stream fallida: {titulo} ({url_original})", exc=e)
            await contexto.send(f"Error al extraer stream para **{titulo}**. Saltando.")
            _saltar_cancion(cola, siguiente)
            contexto.bot.loop.create_task(reproducir_siguiente(contexto))
            return
    else:
        stream_url = url_original

    vc = contexto.voice_client
    if not vc: return

    def after(error):
        if error:
            # Solo al fallar se retira de la cola; un final normal con loop
            # activo debe conservarla para repetirla.
            registrar_error(f"Reproducción interrumpida: {titulo}", exc=error)
            _saltar_cancion(cola, siguiente)
        if es_archivo_local and os.path.exists(stream_url):
            try: os.remove(stream_url)
            except: pass
        contexto.bot.loop.create_task(reproducir_siguiente(contexto))

    before_options = ""
    if stream_url.startswith("http"):
        # FFmpeg exige que CADA header termine con un salto CRLF real.
        # (Antes se pasaban como texto literal "\\r\\n" y el servidor
        # respondía 403 por headers malformados.)
        header_str = "".join([f"{k}: {v}\r\n" for k, v in headers.items()])
        before_options = f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -headers "{header_str}"'

    if not os.path.exists(RUTA_FFMPEG):
        registrar_error(f"CRÍTICO: FFmpeg no encontrado en {RUTA_FFMPEG}")
        await contexto.send("FFmpeg no está disponible. No se puede reproducir.")
        return

    try:
        vc.play(discord.FFmpegPCMAudio(stream_url, executable=RUTA_FFMPEG, before_options=before_options, options='-vn'), after=after)
        await contexto.send(f"Reproduciendo: **{titulo}**")
    except Exception as e:
        registrar_error(f"No se pudo iniciar FFmpeg para: {titulo}", exc=e)
        _saltar_cancion(cola, siguiente)
        contexto.bot.loop.create_task(reproducir_siguiente(contexto))