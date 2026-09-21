import sqlite3
import os
import threading
from config.bot_config import DIRECTORIO_BASE, enviar_a_log

# ---------------- Configuración de la base de datos ----------------

# Ruta de la base de datos dentro de la raíz del proyecto (data/playlists.db).
# DIRECTORIO_BASE apunta a la raíz tanto en modo script como en modo ejecutable.
DIRECTORIO_DB = os.path.join(DIRECTORIO_BASE, "data")
RUTA_DB = os.path.join(DIRECTORIO_DB, "playlists.db")

# Candado para proteger las operaciones de escritura en SQLite,
# ya que el bot usa hilos y no debe haber dos escrituras simultáneas.
_lock = threading.Lock()

def _conectar():
    """Crea la carpeta de la BD si falta y devuelve una conexión lista para usar."""
    os.makedirs(DIRECTORIO_DB, exist_ok=True)
    conexion = sqlite3.connect(RUTA_DB)
    # Devuelve las filas como diccionarios (acceso por nombre de columna).
    conexion.row_factory = sqlite3.Row
    # Activa las claves foráneas para que el borrado en cascada funcione.
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion

def inicializar_db():
    """Crea la carpeta, la base de datos y las tablas si no existen (uso automático)."""
    with _lock, _conectar() as conexion:
        conexion.executescript("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                UNIQUE(user_id, nombre)
            );

            CREATE TABLE IF NOT EXISTS canciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER NOT NULL,
                video_id TEXT NOT NULL,
                titulo TEXT NOT NULL,
                artista TEXT,
                posicion INTEGER NOT NULL,
                FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
            );
        """)

# ---------------- Operaciones con playlists ----------------

def crear_playlist(user_id, nombre):
    """
    Crea una playlist vacía para un usuario.
    Devuelve True si se creó y False si el usuario ya tiene una con ese nombre
    (la restricción UNIQUE(user_id, nombre) lanza IntegrityError en ese caso).
    """
    inicializar_db()
    with _lock, _conectar() as conexion:
        try:
            conexion.execute(
                "INSERT INTO playlists (user_id, nombre) VALUES (?, ?)",
                (str(user_id), nombre)
            )
            return True
        except sqlite3.IntegrityError:
            return False

def obtener_playlist(user_id, nombre):
    """Devuelve la playlist del usuario como dict, o None si no existe.
    Siempre se filtra por user_id para que nadie toque playlists ajenas."""
    inicializar_db()
    with _lock, _conectar() as conexion:
        fila = conexion.execute(
            "SELECT id, user_id, nombre FROM playlists WHERE user_id = ? AND nombre = ?",
            (str(user_id), nombre)
        ).fetchone()
    return dict(fila) if fila else None

def listar_playlists(user_id):
    """Devuelve las playlists del usuario con su número de canciones (COUNT)."""
    inicializar_db()
    with _lock, _conectar() as conexion:
        filas = conexion.execute(
            """SELECT p.id, p.nombre, COUNT(c.id) as total
               FROM playlists p
               LEFT JOIN canciones c ON c.playlist_id = p.id
               WHERE p.user_id = ?
               GROUP BY p.id
               ORDER BY p.nombre""",
            (str(user_id),)
        ).fetchall()
    return [dict(f) for f in filas]

# ---------------- Operaciones con canciones ----------------

def agregar_canciones(playlist_id, canciones):
    """Añade varias canciones en orden. canciones: lista de {'video_id','titulo','artista'}."""
    inicializar_db()
    with _lock, _conectar() as conexion:
        # Calcula la siguiente posición libre para encadenar las canciones nuevas.
        siguiente = conexion.execute(
            "SELECT COALESCE(MAX(posicion), 0) + 1 FROM canciones WHERE playlist_id = ?",
            (playlist_id,)
        ).fetchone()[0]
        # Inserta todas en una sola operación (executemany) con posiciones correlativas.
        conexion.executemany(
            "INSERT INTO canciones (playlist_id, video_id, titulo, artista, posicion) VALUES (?, ?, ?, ?, ?)",
            [(playlist_id, c['video_id'], c['titulo'], c.get('artista'), siguiente + i)
             for i, c in enumerate(canciones)]
        )

def agregar_cancion(playlist_id, video_id, titulo, artista=None):
    """Añade una sola canción (reutiliza agregar_canciones)."""
    agregar_canciones(playlist_id, [{'video_id': video_id, 'titulo': titulo, 'artista': artista}])

def contar_canciones(playlist_id):
    """Devuelve cuántas canciones tiene una playlist."""
    inicializar_db()
    with _lock, _conectar() as conexion:
        total = conexion.execute(
            "SELECT COUNT(*) FROM canciones WHERE playlist_id = ?",
            (playlist_id,)
        ).fetchone()[0]
    return total

def obtener_canciones(playlist_id):
    """Devuelve las canciones en su orden original (por posición)."""
    inicializar_db()
    with _lock, _conectar() as conexion:
        filas = conexion.execute(
            "SELECT id, video_id, titulo, artista, posicion FROM canciones WHERE playlist_id = ? ORDER BY posicion",
            (playlist_id,)
        ).fetchall()
    return [dict(f) for f in filas]

def quitar_cancion(playlist_id, posicion):
    """Elimina la canción en la posición indicada y renumera las restantes.
    Devuelve False si esa posición no existe."""
    inicializar_db()
    with _lock, _conectar() as conexion:
        cursor = conexion.execute(
            "SELECT id FROM canciones WHERE playlist_id = ? AND posicion = ?",
            (playlist_id, posicion)
        )
        fila = cursor.fetchone()
        if not fila:
            return False
        # Elimina la canción y baja en 1 la posición de todas las siguientes.
        conexion.execute("DELETE FROM canciones WHERE id = ?", (fila['id'],))
        conexion.execute(
            "UPDATE canciones SET posicion = posicion - 1 WHERE playlist_id = ? AND posicion > ?",
            (playlist_id, posicion)
        )
        return True

def borrar_playlist(user_id, nombre):
    """Elimina la playlist completa.
    Las canciones asociadas se borran solas gracias al ON DELETE CASCADE.
    Devuelve True si existía y se eliminó."""
    inicializar_db()
    with _lock, _conectar() as conexion:
        cursor = conexion.execute(
            "DELETE FROM playlists WHERE user_id = ? AND nombre = ?",
            (str(user_id), nombre)
        )
        return cursor.rowcount > 0
