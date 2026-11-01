import ctypes
import os
import sys
import threading
import time
from ctypes import wintypes

_CLASE_VENTANA = "FLUTTER_RUNNER_WIN32_WINDOW"
_TITULOS_VENTANA = ("TerPENEitor", "Flet")

_DWMWA_WINDOW_CORNER_PREFERENCE = 33
_DWMWCP_ROUND = 2
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_SYSTEMBACKDROP_TYPE = 38
_DWMWA_BORDER_COLOR = 34
_DWMWA_COLOR_NONE = 0xFFFFFFFE
_DWMSBT_TRANSIENTWINDOW = 3
_WCA_ACCENT_POLICY = 19
_ACCENT_DISABLED = 0
_ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
_TINTE_ACRILICO = 0x992F1321

_GWL_EXSTYLE = -20
_GWL_STYLE = -16
_WS_CAPTION = 0x00C00000
_WS_EX_LAYERED = 0x00080000
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_SWP_FRAMECHANGED = 0x0020

class _MonitorInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


_user32 = None
_dwmapi = None
_kernel32 = None

if sys.platform == "win32":
    _user32 = ctypes.windll.user32
    _dwmapi = ctypes.windll.dwmapi
    _kernel32 = ctypes.windll.kernel32

    _WNDENUMPROC = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    _user32.EnumWindows.argtypes = [_WNDENUMPROC, wintypes.LPARAM]
    _user32.EnumWindows.restype = wintypes.BOOL
    _user32.GetClassNameW.argtypes = [
        wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetClassNameW.restype = ctypes.c_int
    _user32.GetWindowTextW.argtypes = [
        wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    _user32.GetWindowTextW.restype = ctypes.c_int
    _user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    _user32.IsWindowVisible.argtypes = [wintypes.HWND]
    _user32.IsWindowVisible.restype = wintypes.BOOL
    _user32.IsZoomed.argtypes = [wintypes.HWND]
    _user32.IsZoomed.restype = wintypes.BOOL
    _user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    _user32.SetWindowLongPtrW.argtypes = [
        wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    _user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    _user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    _user32.SetWindowPos.restype = wintypes.BOOL
    _user32.GetWindowRect.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    _user32.GetWindowRect.restype = wintypes.BOOL
    _user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    _user32.MonitorFromWindow.restype = wintypes.HANDLE
    _user32.GetMonitorInfoW.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(_MonitorInfo)]
    _user32.GetMonitorInfoW.restype = wintypes.BOOL
    _user32.SetWindowCompositionAttribute.argtypes = [
        wintypes.HWND, ctypes.c_void_p]
    _user32.SetWindowCompositionAttribute.restype = wintypes.BOOL
    _dwmapi.DwmSetWindowAttribute.argtypes = [
        wintypes.HWND, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
    _dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long
    _dwmapi.DwmGetWindowAttribute.argtypes = [
        wintypes.HWND, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
    _dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long
    _dwmapi.DwmExtendFrameIntoClientArea.argtypes = [
        wintypes.HWND, ctypes.c_void_p]
    _dwmapi.DwmExtendFrameIntoClientArea.restype = ctypes.c_long
    _kernel32.CreateToolhelp32Snapshot.argtypes = [
        wintypes.DWORD, wintypes.DWORD]
    _kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _kernel32.Process32FirstW.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p]
    _kernel32.Process32FirstW.restype = wintypes.BOOL
    _kernel32.Process32NextW.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p]
    _kernel32.Process32NextW.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.CloseHandle.restype = wintypes.BOOL
else:
    _WNDENUMPROC = None


class _ProcesoEntrada32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


class _AccentPolicy(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int),
    ]


class _WindowCompositionAttributeData(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]


class _Margenes(ctypes.Structure):
    _fields_ = [
        ("izquierda", ctypes.c_int),
        ("derecha", ctypes.c_int),
        ("arriba", ctypes.c_int),
        ("abajo", ctypes.c_int),
    ]


_reaplicar_evento = threading.Event()
_hilo_reaplicar = None
_hilo_lock = threading.Lock()


def _registrar(mensaje):
    try:
        from config.logger import registrar
        registrar(f"[acrilico] {mensaje}")
    except Exception:
        pass


def _pids_hijos():
    TH32CS_SNAPPROCESS = 2
    snapshot = _kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        return set()
    entrada = _ProcesoEntrada32()
    entrada.dwSize = ctypes.sizeof(_ProcesoEntrada32)
    pids = set()
    try:
        hay = _kernel32.Process32FirstW(snapshot, ctypes.byref(entrada))
        while hay:
            if entrada.th32ParentProcessID == os.getpid():
                pids.add(entrada.th32ProcessID)
            hay = _kernel32.Process32NextW(snapshot, ctypes.byref(entrada))
    finally:
        _kernel32.CloseHandle(snapshot)
    return pids


def _buscar_hwnd():
    candidatas = []

    @_WNDENUMPROC
    def _enum(hwnd, _):
        clase = ctypes.create_unicode_buffer(256)
        _user32.GetClassNameW(hwnd, clase, 256)
        if (clase.value == _CLASE_VENTANA
                and _user32.IsWindowVisible(hwnd)):
            titulo = ctypes.create_unicode_buffer(256)
            _user32.GetWindowTextW(hwnd, titulo, 256)
            pid = wintypes.DWORD(0)
            _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            candidatas.append((hwnd, pid.value, titulo.value))
        return True

    _user32.EnumWindows(_enum, 0)
    if not candidatas:
        return None
    hijos = _pids_hijos()
    for hwnd, pid, _ in candidatas:
        if pid in hijos:
            return hwnd
    for hwnd, _, titulo in candidatas:
        if titulo in _TITULOS_VENTANA:
            return hwnd
    if len(candidatas) == 1:
        return candidatas[0][0]
    return None


def _quitar_layered(hwnd):
    estilo = _user32.GetWindowLongPtrW(hwnd, _GWL_EXSTYLE)
    if not estilo & _WS_EX_LAYERED:
        return
    _user32.SetWindowLongPtrW(hwnd, _GWL_EXSTYLE, estilo & ~_WS_EX_LAYERED)
    _user32.SetWindowPos(
        hwnd, 0, 0, 0, 0, 0,
        _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOZORDER
        | _SWP_NOACTIVATE | _SWP_FRAMECHANGED)


def _quitar_caption(hwnd):
    estilo = _user32.GetWindowLongPtrW(hwnd, _GWL_STYLE)
    if not estilo & _WS_CAPTION:
        return
    _user32.SetWindowLongPtrW(hwnd, _GWL_STYLE, estilo & ~_WS_CAPTION)
    _user32.SetWindowPos(
        hwnd, 0, 0, 0, 0, 0,
        _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOZORDER
        | _SWP_NOACTIVATE | _SWP_FRAMECHANGED)


def _desactivar_acento(hwnd):
    acento = _AccentPolicy(_ACCENT_DISABLED, 2, 0, 0)
    datos = _WindowCompositionAttributeData(
        _WCA_ACCENT_POLICY, ctypes.addressof(acento), ctypes.sizeof(acento))
    _user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(datos))


def _aplicar_acento_acrilico(hwnd):
    acento = _AccentPolicy(
        _ACCENT_ENABLE_ACRYLICBLURBEHIND, 2, _TINTE_ACRILICO, 0)
    datos = _WindowCompositionAttributeData(
        _WCA_ACCENT_POLICY, ctypes.addressof(acento), ctypes.sizeof(acento))
    _user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(datos))


def _fondo_actual(hwnd):
    valor = ctypes.c_int(-1)
    resultado = _dwmapi.DwmGetWindowAttribute(
        hwnd, _DWMWA_SYSTEMBACKDROP_TYPE,
        ctypes.byref(valor), ctypes.sizeof(valor))
    if resultado != 0:
        return None
    return valor.value


def _centrar_ventana(hwnd):
    monitor = _user32.MonitorFromWindow(hwnd, 2)
    if not monitor:
        return
    info = _MonitorInfo()
    info.cbSize = ctypes.sizeof(_MonitorInfo)
    if not _user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return
    rect = wintypes.RECT()
    if not _user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return
    ancho = rect.right - rect.left
    alto = rect.bottom - rect.top
    x = info.rcWork.left + (info.rcWork.right - info.rcWork.left - ancho) // 2
    y = info.rcWork.top + (info.rcWork.bottom - info.rcWork.top - alto) // 2
    _user32.SetWindowPos(
        hwnd, 0, x, y, 0, 0,
        _SWP_NOSIZE | _SWP_NOZORDER | _SWP_NOACTIVATE)


def _aplicar_acrilico(hwnd):
    _quitar_layered(hwnd)
    _quitar_caption(hwnd)

    esquinas = ctypes.c_int(_DWMWCP_ROUND)
    _dwmapi.DwmSetWindowAttribute(
        hwnd, _DWMWA_WINDOW_CORNER_PREFERENCE,
        ctypes.byref(esquinas), ctypes.sizeof(esquinas))

    oscuro = ctypes.c_int(1)
    _dwmapi.DwmSetWindowAttribute(
        hwnd, _DWMWA_USE_IMMERSIVE_DARK_MODE,
        ctypes.byref(oscuro), ctypes.sizeof(oscuro))

    sin_borde = ctypes.c_uint(_DWMWA_COLOR_NONE)
    _dwmapi.DwmSetWindowAttribute(
        hwnd, _DWMWA_BORDER_COLOR,
        ctypes.byref(sin_borde), ctypes.sizeof(sin_borde))

    _desactivar_acento(hwnd)

    maximizada = bool(_user32.IsZoomed(hwnd))
    if sys.getwindowsversion().build >= 22000 and not maximizada:
        margenes = _Margenes(-1, -1, -1, -1)
        _dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margenes))
        fondo = ctypes.c_int(_DWMSBT_TRANSIENTWINDOW)
        resultado = _dwmapi.DwmSetWindowAttribute(
            hwnd, _DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(fondo), ctypes.sizeof(fondo))
        if (resultado == 0
                and _fondo_actual(hwnd) == _DWMSBT_TRANSIENTWINDOW):
            return True

    margenes_sin_marco = _Margenes(0, 0, 0, 0)
    _dwmapi.DwmExtendFrameIntoClientArea(
        hwnd, ctypes.byref(margenes_sin_marco))

    _aplicar_acento_acrilico(hwnd)
    return False


def _bucle_reaplicar():
    while True:
        _reaplicar_evento.wait()
        _reaplicar_evento.clear()
        time.sleep(0.35)
        hwnd = _buscar_hwnd()
        if hwnd:
            _aplicar_acrilico(hwnd)


def _activar_acrilico():
    hwnd = None
    for _ in range(150):
        hwnd = _buscar_hwnd()
        if hwnd:
            break
        time.sleep(0.1)
    if not hwnd:
        _registrar("no se encontró la ventana de Flet; efecto no aplicado")
        return
    _registrar(f"ventana encontrada (hwnd={hwnd})")
    if not _user32.IsZoomed(hwnd):
        _centrar_ventana(hwnd)
    _aplicar_acrilico(hwnd)
    for espera in (0.8, 2.0):
        time.sleep(espera)
        actual = _buscar_hwnd() or hwnd
        _aplicar_acrilico(actual)


def activar_acrilico():
    if sys.platform != "win32":
        return
    threading.Thread(target=_activar_acrilico, daemon=True).start()


def reaplicar_acrilico():
    global _hilo_reaplicar
    if sys.platform != "win32":
        return
    with _hilo_lock:
        if _hilo_reaplicar is None or not _hilo_reaplicar.is_alive():
            _hilo_reaplicar = threading.Thread(
                target=_bucle_reaplicar, daemon=True)
            _hilo_reaplicar.start()
    _reaplicar_evento.set()
