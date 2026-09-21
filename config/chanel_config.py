import discord
import asyncio


async def verificar_canal_voz(interaction: discord.Interaction, solo_verificar: bool = False):
    """
    Verifica que el usuario esté en un canal de voz. 
    Si solo_verificar es False, también conecta o mueve al bot al canal.
    """
    if not interaction.user.voice or not interaction.user.voice.channel:
        msg = "No estás en un canal de voz"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return None

    if solo_verificar:
        return True

    canal = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    if not vc:
        try:
            vc = await canal.connect(timeout=30.0, self_deaf=True)
        except asyncio.TimeoutError:
            msg = "No se pudo conectar al canal de voz (Tiempo agotado). Inténtalo de nuevo."
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)
            return None
    elif vc.channel != canal:
        await vc.move_to(canal)
    
    return vc