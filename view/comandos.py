import discord
from discord import app_commands
import yt_dlp
import asyncio
import aiohttp
import json
import config.ftp_config as ftp_config
import random
from config.bot_config import *
from config.chanel_config import verificar_canal_voz
import modules.player as player
from modules.ui import VistaMusica, VistaPaginacionPlaylist, VistaConfirmacionBorrar, VistaListaFTP
import modules.playlists as playlists_db
from modules.youtube import obtener_playlist, buscar_cancion, obtener_info_video, obtener_info_playlist, construir_ydl_opts
from config.logger import registrar_error

# Reutilizar una sola sesión HTTP para autocomplete y reducir overhead
aiohttp_session = None

async def get_aiohttp_session():
    global aiohttp_session
    if aiohttp_session is None or aiohttp_session.closed:
        aiohttp_session = aiohttp.ClientSession()
    return aiohttp_session

async def close_aiohttp_session():
    global aiohttp_session
    if aiohttp_session is not None and not aiohttp_session.closed:
        try:
            await aiohttp_session.close()
        except Exception:
            pass
        aiohttp_session = None

# ---------------- COMANDOS ----------------

@bot.tree.command(name="musica", description="Busca y reproduce una canción")
async def musica(interaction: discord.Interaction, nombre: str):
    if not await verificar_canal_voz(interaction, solo_verificar=True):
        return

    await interaction.response.defer()

    opciones_ydl = construir_ydl_opts({'default_search': 'ytsearch5'})

    try:
        loop = asyncio.get_event_loop()
        datos = await loop.run_in_executor(
            None,
            lambda: yt_dlp.YoutubeDL(opciones_ydl).extract_info(nombre, download=False)
        )

        entradas = [e for e in datos['entries'] if e]

        if not entradas:
            await interaction.followup.send("No encontré resultados")
            return

        vista = VistaMusica(entradas, interaction)
        await interaction.followup.send(f"Resultados para **{nombre}**:", view=vista)

    except Exception as e:
        registrar_error(f"Búsqueda fallida en /musica: {nombre}", exc=e)
        try:
            await interaction.followup.send("Error al buscar")
        except discord.HTTPException:
            pass

@musica.autocomplete('nombre')
async def musica_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """
    Usa la API de sugerencias de YouTube para que sea instantáneo.
    """
    if not current:
        return []

    try:
        # Consultamos el motor de sugerencias de YouTube (Firefox/Chrome style)
        url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={current}"
        session = await get_aiohttp_session()
        async with session.get(url) as resp:
            if resp.status == 200:
                texto = await resp.text()
                sugerencias = json.loads(texto)[1]
                return [app_commands.Choice(name=s, value=s) for s in sugerencias[:10]]
        return []
    except Exception:
        return []

# ---------------- SKIP ----------------

@bot.tree.command(name="skip", description="Saltar canción")
async def skip(interaction: discord.Interaction):

    vc = interaction.guild.voice_client

    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("Canción saltada")
    else:
        await interaction.response.send_message("No hay música")

# ---------------- STOP ----------------

@bot.tree.command(name="stop", description="Detener música")
async def stop(interaction: discord.Interaction):

    vc = interaction.guild.voice_client

    if vc:
        player.cola.clear()  # Vacía la cola de reproducción
        await vc.disconnect()
        await interaction.response.send_message("Música detenida")

# ---------------- LOOP ----------------

@bot.tree.command(name="loop", description="Activar o desactivar loop")
async def loop_cmd(interaction: discord.Interaction):
    player.loop_activo = not player.loop_activo
    estado = "activado" if player.loop_activo else "desactivado"

    await interaction.response.send_message(f"Loop {estado}")

# ---------------- playlist----------------

# Antiguo /playlist (reproducía playlists de YouTube por URL).
# Renombrado a /ytplaylist para dejar libre el nombre "playlist" y usarlo
# como grupo de playlists personales. La funcionalidad es idéntica.
@bot.tree.command(name="ytplaylist", description="Reproduce una playlist completa de YouTube")
async def ytplaylist(interaction: discord.Interaction, url: str):
    if not await verificar_canal_voz(interaction, solo_verificar=True):
        return

    await interaction.response.defer()

    try:
        loop = asyncio.get_event_loop()
        # Ejecutamos la extracción en un executor para no bloquear el bot
        canciones = await loop.run_in_executor(None, lambda: obtener_playlist(url))

        if not canciones:
            await interaction.followup.send("No se encontraron canciones en el enlace proporcionado.")
            return

        for cancion in canciones:
            player.cola.append(cancion)

        vc = await verificar_canal_voz(interaction)
        if not vc:
            return

        await interaction.followup.send(f"Se han añadido **{len(canciones)}** canciones a la cola.")

        await player.intentar_reproducir(vc, interaction)

    except Exception as e:
        registrar_error(f"Error al cargar playlist de YouTube: {url}", exc=e)
        await interaction.followup.send("Ocurrió un error al cargar la playlist.")

# ---------------- FTP ----------------

# /ftp: sin nombre muestra toda la lista del dispositivo para elegir;
# con nombre filtra por búsqueda rápida. cancion es opcional.
@bot.tree.command(name="ftp", description="Reproduce una canción desde tu teléfono vía FTP. Sin nombre muestra toda la lista")
async def ftp(interaction: discord.Interaction, cancion: str = None):
    if not await verificar_canal_voz(interaction, solo_verificar=True):
        return

    await interaction.response.defer()

    if cancion:
        enviar_a_log(f"Buscando {cancion} en el dispositivo...")
    else:
        enviar_a_log("Obteniendo la lista de canciones del dispositivo...")

    # Obtenemos la lista en un hilo separado para no congelar el bot
    loop = asyncio.get_event_loop()
    canciones = await loop.run_in_executor(None, ftp_config.obtener_musica_ftp)

    if not canciones:
        await interaction.followup.send("No se pudieron obtener canciones. Verifica que el servidor FTP en tu teléfono esté activo.")
        return

    # Si se indicó un nombre, filtramos por búsqueda parcial insensible a mayúsculas
    if cancion:
        busqueda = cancion.lower()
        canciones = [c for c in canciones if busqueda in c['title'].lower()]

        if not canciones:
            await interaction.followup.send(f"No se encontró ninguna canción que coincida con '{cancion}'.")
            return

        # Con una sola coincidencia se reproduce directamente, sin menú
        if len(canciones) == 1:
            cancion_elegida = canciones[0]
            player.cola.append(cancion_elegida)

            vc = await verificar_canal_voz(interaction)
            if not vc:
                return

            await interaction.followup.send(f"Se ha añadido **{cancion_elegida['title']}** a la cola.")
            await player.intentar_reproducir(vc, interaction)
            return

    # Muestra la lista (completa o filtrada) en un menú desplegable con paginación
    vista = VistaListaFTP(canciones, interaction.user.id)
    await interaction.followup.send(f"Selecciona una canción del dispositivo (**{len(canciones)}**):", view=vista)

@bot.tree.command(name="ftpall", description="Reproduce toda la música de la carpeta FTP")
async def ftpall(interaction: discord.Interaction):
    if not await verificar_canal_voz(interaction, solo_verificar=True):
        return

    await interaction.response.defer()
    
    enviar_a_log("Obteniendo toda la música del servidor FTP...")
    
    # Obtenemos la lista completa en un hilo separado para no bloquear el bot
    loop = asyncio.get_event_loop()
    canciones = await loop.run_in_executor(None, ftp_config.obtener_musica_ftp)
    
    if not canciones:
        await interaction.followup.send("No se encontraron canciones o hubo un error al conectar al FTP.")
        return

    # Añadimos todos los elementos encontrados a la cola global
    for cancion in canciones:
        player.cola.append(cancion)
        
    vc = await verificar_canal_voz(interaction)
    if not vc:
        return
    
    await interaction.followup.send(f"Se han añadido **{len(canciones)}** canciones del FTP a la cola.")
    
    await player.intentar_reproducir(vc, interaction)

@bot.tree.command(name="aleatorio", description="Mezcla la cola de reproducción (mínimo 3 canciones)")
async def aleatorio(interaction: discord.Interaction):
    if len(player.cola) < 3:
        await interaction.response.send_message("Necesitas al menos 3 canciones en la cola para poder mezclarlas.", ephemeral=True)
        return

    random.shuffle(player.cola)
    enviar_a_log("La cola de reproducción ha sido mezclada aleatoriamente.")
    await interaction.response.send_message("La cola de terPENEitor se mezclo aleatoriamente")

@bot.tree.command(name="video", description="Reproduce un video de YouTube mediante su URL")
async def video(interaction: discord.Interaction, url: str):
    if not await verificar_canal_voz(interaction, solo_verificar=True):
        return

    await interaction.response.defer()

    try:
        loop = asyncio.get_event_loop()
        # Extraemos solo la info básica (como el título) en un hilo aparte
        info = await loop.run_in_executor(
            None,
            lambda: yt_dlp.YoutubeDL(construir_ydl_opts()).extract_info(url, download=False)
        )

        titulo = info.get('title', 'Sin título')
        player.cola.append({'url': url, 'title': titulo})
        
        vc = await verificar_canal_voz(interaction)
        if not vc:
            return
        
        await interaction.followup.send(f"Agregado a la cola: **{titulo}**")
        
        await player.intentar_reproducir(vc, interaction)

    except Exception as e:
        registrar_error(f"URL inválida en /video: {url}", exc=e)
        await interaction.followup.send("No se pudo cargar el video. Verifica que la URL sea válida.")

# ---------------- PLAYLISTS PERSONALES ----------------
# Grupo de subcomandos /playlist. Cada playlist se guarda en SQLite asociada
# al Discord User ID de su dueño y usa el mismo sistema de reproducción del bot.

playlist_grupo = app_commands.Group(name="playlist", description="Playlists personales")

# /playlist crear nombre:...  -> crea una playlist vacía
@playlist_grupo.command(name="crear", description="Crea una playlist vacía")
async def playlist_crear(interaction: discord.Interaction, nombre: str):
    # crear_playlist devuelve False si el usuario ya tiene una con ese nombre.
    if playlists_db.crear_playlist(interaction.user.id, nombre):
        await interaction.response.send_message(f"Playlist **{nombre}** creada")
    else:
        await interaction.response.send_message(f"Ya tienes una playlist llamada **{nombre}**.")

# /playlist agregar playlist:... [busqueda:...] [url:...]
# Acepta búsqueda de YouTube, URL de video individual o URL de playlist de YouTube.
@playlist_grupo.command(name="agregar", description="Agrega canciones a una playlist (búsqueda o URL)")
async def playlist_agregar(interaction: discord.Interaction, playlist: str, busqueda: str = None, url: str = None):
    # Comprueba que la playlist pertenezca al usuario que ejecuta el comando.
    pl = playlists_db.obtener_playlist(interaction.user.id, playlist)
    if not pl:
        await interaction.response.send_message(f"No tienes una playlist llamada **{playlist}**.", ephemeral=True)
        return

    if not busqueda and not url:
        await interaction.response.send_message("Debes indicar una **búsqueda** o una **URL**.", ephemeral=True)
        return

    # Diferimos la respuesta porque la extracción de YouTube puede tardar.
    await interaction.response.defer()

    try:
        loop = asyncio.get_event_loop()

        if url and "list=" in url:
            # Playlist de YouTube: se importan todas las canciones en orden,
            # mostrando progreso por lotes para que el usuario vea que el bot trabaja.
            await interaction.followup.send("Obteniendo canciones de la playlist...")
            canciones = await loop.run_in_executor(None, lambda: obtener_info_playlist(url))
            if not canciones:
                await interaction.followup.send("No se encontraron canciones. Verifica que la playlist no sea privada o que la URL sea válida.")
                return

            total = len(canciones)
            mensaje = await interaction.followup.send(f"Importando playlist... 0/{total} canciones")
            LOTE = 10
            for i in range(0, total, LOTE):
                playlists_db.agregar_canciones(pl['id'], canciones[i:i + LOTE])
                hecho = min(i + LOTE, total)
                # Actualiza el mensaje de progreso cada 10 canciones o al terminar.
                if hecho % 10 == 0 or hecho == total:
                    await mensaje.edit(content=f"Importando playlist... {hecho}/{total} canciones")
            await mensaje.edit(content=f" Se añadieron **{total}** canciones a **{playlist}**.")

        elif url:
            # Video individual de YouTube: se guarda su video_id, título y artista.
            info = await loop.run_in_executor(None, lambda: obtener_info_video(url))
            if not info or not info.get('video_id'):
                await interaction.followup.send("No se pudo obtener el video. Verifica la URL.")
                return
            playlists_db.agregar_cancion(pl['id'], info['video_id'], info['titulo'], info['artista'])
            await interaction.followup.send(f" Añadido a **{playlist}**: **{info['titulo']}**")

        else:
            # Búsqueda: se guarda el primer resultado que devuelve yt-dlp.
            info = await loop.run_in_executor(None, lambda: buscar_cancion(busqueda))
            if not info or not info.get('video_id'):
                await interaction.followup.send(f"No encontré resultados para **{busqueda}**.")
                return
            playlists_db.agregar_cancion(pl['id'], info['video_id'], info['titulo'], info['artista'])
            await interaction.followup.send(f" Añadido a **{playlist}**: **{info['titulo']}**")

    except Exception as e:
        # Error genérico: se registra y se avisa sin romper el bot.
        enviar_a_log(f"Error en /playlist agregar: {e}")
        await interaction.followup.send("Ocurrió un error al agregar la canción. Verifica la URL o inténtalo de nuevo.")

# /playlist listar  -> muestra las playlists del usuario (solo las suyas)
@playlist_grupo.command(name="listar", description="Muestra tus playlists")
async def playlist_listar(interaction: discord.Interaction):
    playlists = playlists_db.listar_playlists(interaction.user.id)
    if not playlists:
        await interaction.response.send_message("No tienes playlists todavía. Crea una con `/playlist crear`.")
        return

    lineas = [f"{i + 1}. 🎵 **{p['nombre']}** — {p['total']} canciones" for i, p in enumerate(playlists)]
    await interaction.response.send_message("**Tus playlists**\n\n" + "\n".join(lineas))

# /playlist ver nombre:...  -> muestra las canciones con paginación por botones
@playlist_grupo.command(name="ver", description="Muestra las canciones de una playlist")
async def playlist_ver(interaction: discord.Interaction, nombre: str):
    pl = playlists_db.obtener_playlist(interaction.user.id, nombre)
    if not pl:
        await interaction.response.send_message(f"No tienes una playlist llamada **{nombre}**.", ephemeral=True)
        return

    canciones = playlists_db.obtener_canciones(pl['id'])
    # La vista de paginación solo permite interactuar al dueño de la playlist.
    vista = VistaPaginacionPlaylist(nombre, canciones, interaction.user.id)
    await interaction.response.send_message(vista._contenido(), view=vista)

# /playlist reproducir nombre:...  -> carga la playlist en la cola actual del bot
@playlist_grupo.command(name="reproducir", description="Reproduce una playlist completa")
async def playlist_reproducir(interaction: discord.Interaction, nombre: str):
    pl = playlists_db.obtener_playlist(interaction.user.id, nombre)
    if not pl:
        await interaction.response.send_message(f"No tienes una playlist llamada **{nombre}**.", ephemeral=True)
        return

    canciones = playlists_db.obtener_canciones(pl['id'])
    if not canciones:
        await interaction.response.send_message(f"La playlist **{nombre}** está vacía.")
        return

    # Verifica que el usuario esté en un canal de voz y conecta al bot si es necesario.
    vc = await verificar_canal_voz(interaction)
    if not vc:
        return

    # Usa la MISMA cola del bot: reconstruye la URL desde el video_id guardado.
    # El reproductor actual obtendrá el stream con yt-dlp en cada canción.
    for c in canciones:
        player.cola.append({'url': f"https://www.youtube.com/watch?v={c['video_id']}", 'title': c['titulo']})

    await interaction.response.send_message(f"Se añadieron **{len(canciones)}** canciones de **{nombre}** a la cola.")
    # Si no hay nada sonando, empieza a reproducir; si ya hay música, se encolan.
    await player.intentar_reproducir(vc, interaction)

# /playlist quitar nombre:... numero:...  -> elimina por posición (evita títulos repetidos)
@playlist_grupo.command(name="quitar", description="Quita una canción de una playlist por su número")
async def playlist_quitar(interaction: discord.Interaction, nombre: str, numero: int):
    pl = playlists_db.obtener_playlist(interaction.user.id, nombre)
    if not pl:
        await interaction.response.send_message(f"No tienes una playlist llamada **{nombre}**.", ephemeral=True)
        return

    # quitar_cancion renumera las posiciones restantes automáticamente.
    if playlists_db.quitar_cancion(pl['id'], numero):
        await interaction.response.send_message(f" Canción **{numero}** eliminada de **{nombre}**.")
    else:
        await interaction.response.send_message(f"No hay ninguna canción en la posición **{numero}** en **{nombre}**.")

# /playlist borrar nombre:...  -> elimina la playlist con confirmación previa
@playlist_grupo.command(name="borrar", description="Elimina una playlist completa")
async def playlist_borrar(interaction: discord.Interaction, nombre: str):
    pl = playlists_db.obtener_playlist(interaction.user.id, nombre)
    if not pl:
        await interaction.response.send_message(f"No tienes una playlist llamada **{nombre}**.", ephemeral=True)
        return

    # Muestra la vista de confirmación y espera a que el dueño pulse un botón.
    vista = VistaConfirmacionBorrar(nombre, interaction.user.id)
    await interaction.response.send_message(f"¿Seguro que quieres eliminar **{nombre}**?", view=vista)
    await vista.wait()
    if vista.confirmado:
        playlists_db.borrar_playlist(interaction.user.id, nombre)
        await interaction.edit_original_response(content=f"Playlist **{nombre}** eliminada.", view=None)

# Autocompletado del parámetro 'nombre': sugiere las playlists del usuario.
async def autocomplete_playlist(interaction: discord.Interaction, current: str):
    playlists = playlists_db.listar_playlists(interaction.user.id)
    return [
        app_commands.Choice(name=p['nombre'], value=p['nombre'])
        for p in playlists if current.lower() in p['nombre'].lower()
    ][:25]

# Registra el autocompletado en todos los subcomandos que usan el parámetro 'nombre'.
# /playlist agregar usa el parámetro 'playlist' para el mismo propósito.
for _comando in [playlist_ver, playlist_reproducir, playlist_quitar, playlist_borrar]:
    _comando.autocomplete('nombre')(autocomplete_playlist)
playlist_agregar.autocomplete('playlist')(autocomplete_playlist)

# Añade el grupo completo al árbol de comandos del bot.
bot.tree.add_command(playlist_grupo)

# -------------------- limpiar_cola --------------------

@bot.tree.command(name="limpiar_cola", description="Limpia la cola de TerPENEitor")
async def limpiar_cola(interaction: discord.Interaction):
    if not player.cola:
        await interaction.response.send_message("La cola ya está vacía.", ephemeral=True)
        return

    player.cola.clear()
    await interaction.response.send_message("La cola de TerPENEitor ha sido limpiada.")