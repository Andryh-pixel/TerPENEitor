import os
import sys
import threading
import traceback
from datetime import datetime

# Resolvemos la raíz con la misma lógica que bot_config para evitar
# una importación circular (el exe empaquetado usa la carpeta del .exe).
if getattr(sys, 'frozen', False):
    DIRECTORIO_BASE = os.path.dirname(sys.executable)
else:
    DIRECTORIO_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CARPETA_LOGS = os.path.join(DIRECTORIO_BASE, "logs")

_lock = threading.Lock()
_gui_callback = None


def set_gui_callback(callback):
    """Registra la función que muestra los mensajes en la GUI (si existe)."""
    global _gui_callback
    _gui_callback = callback


def _ruta_log_general():
    return os.path.join(CARPETA_LOGS, f"bot_{datetime.now():%Y-%m-%d}.txt")


def _ruta_log_errores():
    return os.path.join(CARPETA_LOGS, f"errores_{datetime.now():%Y-%m-%d}.txt")


def _escribir(ruta, contenido):
    try:
        os.makedirs(CARPETA_LOGS, exist_ok=True)
        with _lock:
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(contenido + "\n")
    except OSError:
        # Si no se puede escribir el log no debemos romper el bot por ello.
        pass


def _avisar_gui(texto):
    if _gui_callback is None:
        return
    try:
        _gui_callback(texto)
    except Exception:
        pass


def registrar(texto):
    """Escribe un mensaje informativo en el log general del día."""
    marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{marca}] {texto}"
    _escribir(_ruta_log_general(), linea)
    _avisar_gui(texto)


def registrar_error(titulo, exc=None):
    """Registra un error: línea resumida en el log general y traceback
    completo en errores_YYYY-MM-DD.txt. Devuelve la línea resumida."""
    marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if exc is not None:
        resumen = f"{type(exc).__name__}: {exc}"
        traza = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    elif sys.exc_info()[0] is not None:
        resumen = traceback.format_exc(limit=1).strip().splitlines()[-1]
        traza = traceback.format_exc()
    else:
        resumen = "(sin excepción activa)"
        traza = ""

    corta = f"[{marca}] ERROR | {titulo} | {resumen}"
    completa = (
        f"{'=' * 70}\n"
        f"[{marca}] {titulo}\n"
        + (traza if traza else f"{resumen}\n")
    )

    _escribir(_ruta_log_general(), corta)
    _escribir(_ruta_log_errores(), completa)
    _avisar_gui(corta)
    return corta


def instalar_hooks_globales():
    """Captura excepciones que de otro modo se perderían:
    - Errores no manejados en el hilo principal (sys.excepthook).
    - Errores no manejados en cualquier hilo secundario (threading.excepthook).
    """
    def _hook_principal(tipo, valor, traza):
        registrar_error("Excepción no controlada (hilo principal)",
                        exc=valor.with_traceback(traza))
        sys.__excepthook__(tipo, valor, traza)

    def _hook_hilos(args):
        registrar_error(
            f"Excepción no controlada en hilo '{args.thread.name if args.thread else '?'}`",
            exc=args.exc_value)
        threading.__excepthook__(args)

    sys.excepthook = _hook_principal
    threading.excepthook = _hook_hilos
