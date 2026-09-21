import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import urllib.request


URL_VERSION = (
    "https://raw.githubusercontent.com/"
    "Andryh-pixel/TerPENEitor/main/version.json"
)


def obtener_version_actual():
    carpeta_updater = os.path.dirname(
        os.path.abspath(sys.argv[0])
    )

    archivo_version = os.path.join(
        carpeta_updater,
        "version.txt"
    )

    try:
        with open(
            archivo_version,
            "r",
            encoding="utf-8"
        ) as archivo:
            return archivo.read().strip()

    except Exception as error:
        print("No se pudo leer version.txt.")
        print(error)
        return "0.0.0"


def obtener_actualizacion():
    try:
        with urllib.request.urlopen(URL_VERSION, timeout=10) as respuesta:
            datos = json.loads(
                respuesta.read().decode("utf-8")
            )

        return datos["version"], datos["download_url"]

    except Exception as error:
        print("No se pudo comprobar la actualización.")
        print(error)
        return None, None


def descargar_actualizacion(url, archivo):
    print("Descargando actualización...")

    urllib.request.urlretrieve(url, archivo)

    print("Descarga terminada.")


def instalar_actualizacion(archivo_zip):
    carpeta_bot = os.path.dirname(
        os.path.abspath(sys.argv[0])
    )

    carpeta_temporal = os.path.join(
        tempfile.gettempdir(),
        "TerPENEitor_update"
    )

    if os.path.exists(carpeta_temporal):
        shutil.rmtree(carpeta_temporal)

    os.makedirs(carpeta_temporal)

    print("Extrayendo actualización...")

    with zipfile.ZipFile(archivo_zip, "r") as archivo:
        archivo.extractall(carpeta_temporal)

    contenido = os.listdir(carpeta_temporal)

    if len(contenido) == 1:
        posible_carpeta = os.path.join(
            carpeta_temporal,
            contenido[0]
        )

        if os.path.isdir(posible_carpeta):
            carpeta_nueva = posible_carpeta
        else:
            carpeta_nueva = carpeta_temporal
    else:
        carpeta_nueva = carpeta_temporal

    print("Instalando archivos...")

    for nombre in os.listdir(carpeta_nueva):

        if nombre in ["config", "data", "logs"]:
            continue

        origen = os.path.join(carpeta_nueva, nombre)
        destino = os.path.join(carpeta_bot, nombre)

        if os.path.isdir(origen):

            if os.path.exists(destino):
                shutil.rmtree(destino)

            shutil.copytree(origen, destino)

        else:

            if os.path.exists(destino):
                os.remove(destino)

            shutil.copy2(origen, destino)

    shutil.rmtree(carpeta_temporal)

    if os.path.exists(archivo_zip):
        os.remove(archivo_zip)

    print("Actualización instalada.")


def iniciar_bot():
    carpeta_bot = os.path.dirname(
        os.path.abspath(sys.argv[0])
    )

    bot = os.path.join(
        carpeta_bot,
        "TerPENEitor.exe"
    )

    if os.path.exists(bot):
        subprocess.Popen([bot])


def main():
    print("Comprobando actualizaciones...")

    version_actual = obtener_version_actual()

    print("Versión instalada:", version_actual)

    version_nueva, url_descarga = obtener_actualizacion()

    if version_nueva is None:
        iniciar_bot()
        return

    if version_nueva == version_actual:
        print("TerPENEitor ya está actualizado.")
        iniciar_bot()
        return

    print("Nueva versión encontrada:", version_nueva)

    archivo_zip = os.path.join(
        tempfile.gettempdir(),
        "TerPENEitor_update.zip"
    )

    try:
        descargar_actualizacion(
            url_descarga,
            archivo_zip
        )

        instalar_actualizacion(archivo_zip)

        iniciar_bot()

    except Exception as error:
        print("Error al actualizar:")
        print(error)

        if os.path.exists(archivo_zip):
            os.remove(archivo_zip)

        iniciar_bot()


if __name__ == "__main__":
    main()
