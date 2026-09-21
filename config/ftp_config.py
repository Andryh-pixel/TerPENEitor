import ftplib
from urllib.parse import quote

FTP_HOST = ""  # Reemplaza con la IP que te muestre la App de tu celular
FTP_PORT = ""  # Puerto típico (ej: 2221 o 2121)
FTP_USER = "" # Usuario configurado en la App
FTP_PASS = "" # Contraseña configurada en la App
FTP_DIR = "" #carpeta raiz

def probar_conexion_ftp(host, port, user, password):
    """
    Valida la conexión con los datos ingresados en la GUI.
    """
    ftp = ftplib.FTP()
    ftp.connect(host.strip(), int(port), timeout=5)
    ftp.login(user, password)
    ftp.quit()

#se conecta al server ftp y de vuelve la lista de canciones encontrada
def obtener_musica_ftp():
    try:
        ftp = ftplib.FTP()
        # Conexión al host y puerto configurados en py
        # Convertimos a int por seguridad en caso de que se use el valor inicial
        ftp.connect(FTP_HOST, int(FTP_PORT) if FTP_PORT else 21, timeout=10)
        ftp.login(FTP_USER, FTP_PASS)
            
        archivos = ftp.nlst()
        formatos_audio = ('.mp3', '.wav', '.m4a', '.flac', '.ogg')
        
        lista_reproduccion = []
        
        for nombre in archivos:
            if nombre.lower().endswith(formatos_audio):
                # Escapamos caracteres especiales para que la URL sea válida
                nombre_url = quote(nombre)
                ruta_base = f"{quote(FTP_DIR)}/" if FTP_DIR else ""
                user_quoted = quote(FTP_USER)
                pass_quoted = quote(FTP_PASS)
                
                # Construir URL con el formato: ftp://user:pass@host:port/path
                url_final = f"ftp://{user_quoted}:{pass_quoted}@{FTP_HOST}:{FTP_PORT}/{ruta_base}{nombre_url}"
                
                lista_reproduccion.append({
                    'url': url_final,
                    'title': nombre
                })
        
        ftp.quit()
        return lista_reproduccion
    except Exception as e:
        print(f"Error al obtener lista FTP: {e}")
        return []
