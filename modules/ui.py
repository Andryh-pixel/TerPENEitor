import discord
from discord.ui import Select, View
from config.chanel_config import verificar_canal_voz
import modules.player as player

class OpcionesMusica(Select):
    def __init__(self, resultados, interaccion_original):
        self.interaccion_original = interaccion_original
        self.resultados = resultados

        opciones = []
        for i, r in enumerate(resultados[:5]):
            titulo = r.get('title', 'Sin título')[:90]
            opciones.append(
                discord.SelectOption(
                    label=f"{i+1}. {titulo}",
                    value=str(i),
                    description=r.get('uploader', 'YouTube')[:50]
                )
            )

        super().__init__(
            placeholder="Selecciona la versión correcta...",
            min_values=1,
            max_values=1,
            options=opciones
        )

    async def callback(self, interaccion: discord.Interaction):
        await interaccion.response.defer()

        indice = int(self.values[0])
        seleccion = self.resultados[indice]
        url = seleccion.get('url')
        titulo = seleccion.get('title')

        vc = await verificar_canal_voz(interaccion)
        if not vc:
            return
            
        player.cola.append({'url': url, 'title': titulo})

        if not await player.intentar_reproducir(vc, interaccion):
            await interaccion.followup.send(f"Agregado a la cola: **{titulo}**")

class VistaMusica(View):
    def __init__(self, resultados, interaccion):
        super().__init__()
        self.add_item(OpcionesMusica(resultados, interaccion))

class VistaPaginacionPlaylist(View):
    """Paginación para mostrar las canciones de una playlist. Solo la usa su dueño."""
    CANCIONES_POR_PAGINA = 10

    def __init__(self, nombre_playlist, canciones, user_id):
        super().__init__()
        self.nombre_playlist = nombre_playlist
        self.canciones = canciones
        self.user_id = user_id  # Discord User ID del dueño de la playlist
        self.pagina = 0
        # -(-x // y) es una división redondeada hacia arriba para calcular páginas.
        self.total_paginas = max(1, -(-len(canciones) // self.CANCIONES_POR_PAGINA))

        # Botón para ir a la página anterior.
        self.boton_atras = discord.ui.Button(label="⬅️", style=discord.ButtonStyle.secondary, row=0)
        self.boton_atras.callback = self.atras_callback
        self.add_item(self.boton_atras)

        # Etiqueta central que muestra la página actual (siempre deshabilitada).
        self.etiqueta_pagina = discord.ui.Button(
            label=f"[1/{self.total_paginas}]",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            row=0
        )
        self.add_item(self.etiqueta_pagina)

        # Botón para ir a la página siguiente.
        self.boton_adelante = discord.ui.Button(label="➡️", style=discord.ButtonStyle.secondary, row=0)
        self.boton_adelante.callback = self.adelante_callback
        self.add_item(self.boton_adelante)

        self._actualizar_botones()

    def _comprobar_dueno(self, interaccion):
        """Bloquea la interacción si el usuario no es el dueño de la playlist."""
        return interaccion.user.id == self.user_id

    def _actualizar_botones(self):
        """Deshabilita el botón atrás/adelante si estamos en el primer/último extremo."""
        self.boton_atras.disabled = self.pagina == 0
        self.boton_adelante.disabled = self.pagina >= self.total_paginas - 1

    def _contenido(self):
        """Construye el texto del mensaje con las canciones de la página actual."""
        inicio = self.pagina * self.CANCIONES_POR_PAGINA
        pagina_canciones = self.canciones[inicio:inicio + self.CANCIONES_POR_PAGINA]
        lineas = [f"{c['posicion']}. {c['titulo']}" for c in pagina_canciones]
        contenido = f"🎵 **{self.nombre_playlist}**\n"
        contenido += f"**{len(self.canciones)} canciones**\n\n"
        contenido += "\n".join(lineas) if lineas else "_La playlist está vacía_"
        return contenido

    async def atras_callback(self, interaccion):
        """Va a la página anterior y actualiza el mensaje."""
        if not self._comprobar_dueno(interaccion):
            await interaccion.response.send_message("No puedes interactuar con esta playlist.", ephemeral=True)
            return
        self.pagina = max(0, self.pagina - 1)
        self._actualizar_botones()
        self.etiqueta_pagina.label = f"[{self.pagina + 1}/{self.total_paginas}]"
        await interaccion.response.edit_message(content=self._contenido(), view=self)

    async def adelante_callback(self, interaccion):
        """Va a la página siguiente y actualiza el mensaje."""
        if not self._comprobar_dueno(interaccion):
            await interaccion.response.send_message("No puedes interactuar con esta playlist.", ephemeral=True)
            return
        self.pagina = min(self.total_paginas - 1, self.pagina + 1)
        self._actualizar_botones()
        self.etiqueta_pagina.label = f"[{self.pagina + 1}/{self.total_paginas}]"
        await interaccion.response.edit_message(content=self._contenido(), view=self)

class VistaConfirmacionBorrar(View):
    """Confirmación antes de eliminar una playlist. Solo la usa su dueño."""

    def __init__(self, nombre_playlist, user_id):
        super().__init__()
        self.nombre_playlist = nombre_playlist
        self.user_id = user_id
        self.confirmado = False  # El comando consulta esta bandera al esperar la vista.

        # Botón verde que confirma la eliminación.
        self.boton_confirmar = discord.ui.Button(label="✅ Confirmar", style=discord.ButtonStyle.success, row=0)
        self.boton_confirmar.callback = self.confirmar_callback
        self.add_item(self.boton_confirmar)

        # Botón gris que cancela la eliminación.
        self.boton_cancelar = discord.ui.Button(label="❌ Cancelar", style=discord.ButtonStyle.secondary, row=0)
        self.boton_cancelar.callback = self.cancelar_callback
        self.add_item(self.boton_cancelar)

    def _comprobar_dueno(self, interaccion):
        """Bloquea la interacción si el usuario no es el dueño de la playlist."""
        return interaccion.user.id == self.user_id

    async def confirmar_callback(self, interaccion):
        """Marca la confirmación, cierra la vista y avisa que se está eliminando."""
        if not self._comprobar_dueno(interaccion):
            await interaccion.response.send_message("No puedes interactuar con esta playlist.", ephemeral=True)
            return
        self.confirmado = True
        self.stop()
        await interaccion.response.edit_message(content="Eliminando playlist...", view=None)

    async def cancelar_callback(self, interaccion):
        """Cancela la eliminación sin marcar la confirmación."""
        if not self._comprobar_dueno(interaccion):
            await interaccion.response.send_message("No puedes interactuar con esta playlist.", ephemeral=True)
            return
        self.stop()
        await interaccion.response.edit_message(content="Eliminación cancelada.", view=None)

class OpcionesFTP(Select):
    """Menú desplegable para elegir una canción del dispositivo vía FTP."""

    def __init__(self, opciones, vista):
        # opciones: lista de discord.SelectOption de la página actual del listado.
        self.vista = vista
        super().__init__(
            placeholder="Elige una canción...",
            min_values=1,
            max_values=1,
            options=opciones
        )

    async def callback(self, interaccion: discord.Interaction):
        # Solo el usuario que lanzó el comando puede elegir una canción.
        if not self.vista._comprobar_dueno(interaccion):
            await interaccion.response.send_message("No puedes elegir aquí.", ephemeral=True)
            return

        await interaccion.response.defer()

        # El valor de la opción guarda el índice global dentro de la lista completa.
        indice = int(self.values[0])
        cancion = self.vista.canciones[indice]

        # Añade la canción a la cola actual del bot (mismo sistema de reproducción).
        player.cola.append({'url': cancion['url'], 'title': cancion['title']})

        # Conecta al canal de voz del usuario si aún no está conectado.
        vc = await verificar_canal_voz(interaccion)
        if not vc:
            return

        # Si ya hay música sonando solo se encola; si no, empieza a reproducir.
        if not await player.intentar_reproducir(vc, interaccion):
            await interaccion.followup.send(f"Agregado a la cola: **{cancion['title']}**")

class VistaListaFTP(View):
    """Lista paginada de canciones FTP con un menú desplegable para elegir.
    Solo el usuario que lanzó el comando puede interactuar."""
    CANCIONES_POR_PAGINA = 25

    def __init__(self, canciones, user_id):
        super().__init__()
        self.canciones = canciones
        self.user_id = user_id
        self.pagina = 0
        # -(-x // y) es una división redondeada hacia arriba para calcular páginas.
        self.total_paginas = max(1, -(-len(canciones) // self.CANCIONES_POR_PAGINA))

        # Select con las opciones de la primera página.
        self.select = OpcionesFTP(self._opciones_pagina(), self)
        self.add_item(self.select)

        # Botón para ir a la página anterior.
        self.boton_atras = discord.ui.Button(label="Anterior", style=discord.ButtonStyle.secondary, row=1)
        self.boton_atras.callback = self.atras_callback
        self.add_item(self.boton_atras)

        # Etiqueta que indica la página actual (siempre deshabilitada).
        self.etiqueta_pagina = discord.ui.Button(
            label=f"[1/{self.total_paginas}]",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            row=1
        )
        self.add_item(self.etiqueta_pagina)

        # Botón para ir a la página siguiente.
        self.boton_adelante = discord.ui.Button(label="Siguiente", style=discord.ButtonStyle.secondary, row=1)
        self.boton_adelante.callback = self.adelante_callback
        self.add_item(self.boton_adelante)

        self._actualizar_botones()

    def _comprobar_dueno(self, interaccion):
        """Bloquea la interacción si el usuario no lanzó el comando."""
        return interaccion.user.id == self.user_id

    def _actualizar_botones(self):
        """Deshabilita Anterior/Siguiente si estamos en el primer/último extremo."""
        self.boton_atras.disabled = self.pagina == 0
        self.boton_adelante.disabled = self.pagina >= self.total_paginas - 1

    def _opciones_pagina(self):
        """Construye hasta 25 opciones para la página actual de la lista."""
        inicio = self.pagina * self.CANCIONES_POR_PAGINA
        pagina = self.canciones[inicio:inicio + self.CANCIONES_POR_PAGINA]
        opciones = []
        for i, cancion in enumerate(pagina):
            titulo = cancion['title'][:90]  # Límite de 100 caracteres de Discord
            opciones.append(
                discord.SelectOption(
                    label=f"{inicio + i + 1}. {titulo}",
                    value=str(inicio + i)  # Índice global para recuperar la canción
                )
            )
        return opciones

    async def atras_callback(self, interaccion):
        """Va a la página anterior y actualiza el menú."""
        if not self._comprobar_dueno(interaccion):
            await interaccion.response.send_message("No puedes interactuar aquí.", ephemeral=True)
            return
        self.pagina = max(0, self.pagina - 1)
        await self._aplicar_pagina(interaccion)

    async def adelante_callback(self, interaccion):
        """Va a la página siguiente y actualiza el menú."""
        if not self._comprobar_dueno(interaccion):
            await interaccion.response.send_message("No puedes interactuar aquí.", ephemeral=True)
            return
        self.pagina = min(self.total_paginas - 1, self.pagina + 1)
        await self._aplicar_pagina(interaccion)

    async def _aplicar_pagina(self, interaccion):
        """Refresca botones, etiqueta de página y opciones del select."""
        self._actualizar_botones()
        self.etiqueta_pagina.label = f"[{self.pagina + 1}/{self.total_paginas}]"
        self.select.options = self._opciones_pagina()
        await interaccion.response.edit_message(view=self)