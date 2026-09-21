import os
import sys
import yt_dlp

from config.logger import registrar


class _LoggerYtdlp:
    """Puente para que los warnings/errores internos de yt-dlp queden
    registrados en los archivos de log y visibles en la GUI."""

    def debug(self, msg):
        pass  # Demasiado ruidoso para el log diario.

    def info(self, msg):
        pass

    def warning(self, msg):
        if isinstance(msg, bytes):
            try:
                msg = msg.decode()
            except Exception:
                return
        registrar(f"[yt-dlp] Aviso: {msg}")

    def error(self, msg, *_args, **_kwargs):
        if isinstance(msg, bytes):
            try:
                msg = msg.decode()
            except Exception:
                return
        registrar(f"[yt-dlp] Error: {msg}")


def _ruta_quickjs():
    """Devuelve la ruta del runtime qjs.exe si existe junto al programa.
    En el exe empaquetado vive al lado de TerPENEitor.exe; en desarrollo,
    en la raíz del proyecto. Así no se requiere Node.js ni Deno instalados."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(base, "qjs.exe")
    return ruta if os.path.exists(ruta) else None


def construir_ydl_opts(extras=None):
    """Opciones base de yt-dlp para todo el bot: formato de audio,
    runtime JS quickjs (empaquetado con el bot) y logger propio."""
    opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': False,
        'socket_timeout': 20,
        'logger': _LoggerYtdlp(),
    }
    qjs = _ruta_quickjs()
    if qjs:
        opts['js_runtimes'] = {'quickjs': {'path': qjs}}
    else:
        # Sin binario local: dejamos el default (deno si estuviera instalado)
        # y avisamos una vez por proceso que YouTube puede fallar sin runtime.
        if not getattr(construir_ydl_opts, '_aviso_sin_qjs', False):
            construir_ydl_opts._aviso_sin_qjs = True
            registrar("AVISO: no se encontró qjs.exe junto al programa. "
                      "La reproducción de YouTube puede fallar (403).")
    if extras:
        opts.update(extras)
    return opts


def _extraer(url):
    """
    Extrae información de una URL de YouTube sin descargar el audio.
    Usa extract_flat para ser rápido (solo metadatos) y noplaylist para
    que una URL de video individual no arrastre la playlist en la que esté.
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def buscar_cancion(query):
    """Busca en YouTube y devuelve el primer resultado como dict con video_id.
    Devuelve None si no hay resultados. El artista se toma del 'uploader'."""
    info = _extraer(f"ytsearch1:{query}")
    if not info or not info.get('entries'):
        return None
    entrada = info['entries'][0]
    if not entrada:
        return None
    return {
        'video_id': entrada.get('id'),
        'titulo': entrada.get('title', 'Sin título'),
        'artista': entrada.get('uploader'),
    }

def obtener_info_video(url):
    """Obtiene la info (id, título, artista) de un video individual de YouTube."""
    info = _extraer(url)
    return {
        'video_id': info.get('id'),
        'titulo': info.get('title', 'Sin título'),
        'artista': info.get('uploader'),
    }

def obtener_info_playlist(url):
    """Obtiene las canciones de una playlist de YouTube en su orden original.
    Devuelve una lista de dicts con video_id, titulo y artista (sin descargar nada)."""
    info = _extraer(url)
    canciones = []
    if 'entries' in info:
        for video in info['entries']:
            if video and video.get('id'):
                canciones.append({
                    'video_id': video['id'],
                    'titulo': video.get('title', 'Sin título'),
                    'artista': video.get('uploader'),
                })
    return canciones

def obtener_playlist(url):
    """[Funcion original] Extrae una playlist de YouTube como lista {'url', 'title'}.
    Se mantiene para el comando /ytplaylist, que reproduce directamente la URL."""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    canciones = []
    if 'entries' in info:
        for video in info['entries']:
            if video:
                video_url = video.get('url') or f"https://www.youtube.com/watch?v={video['id']}"
                canciones.append({'url': video_url, 'title': video.get('title', 'Sin título')})
    return canciones