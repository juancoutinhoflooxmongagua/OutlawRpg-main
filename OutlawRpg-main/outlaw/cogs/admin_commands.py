import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, Color
from data_manager import get_player_data, save_data
from views.embed_creator_views import EmbedCreatorView
from datetime import datetime


class AdminCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="set_xptriple",
        description="[ADMIN] Ativa/Desativa o XP Triplo para um jogador.",
    )
    @app_commands.describe(
        membro="O membro para ativar/desativar o XP Triplo.",
        status="True para ativar, False para desativar.",
    )
    @commands.has_permissions(administrator=True)
    async def set_xptriple(self, i: Interaction, membro: discord.Member, status: bool):
        player_data = get_player_data(membro.id)
        if not player_data:
            await i.response.send_message(
                "Este jogador não possui uma ficha.", ephemeral=True
            )
            return

        player_data["xptriple"] = status
        save_data()

        status_str = "ativado" if status else "desativado"
        await i.response.send_message(
            f"O XP Triplo para **{membro.display_name}** foi **{status_str}**."
        )

    @app_commands.command(
        name="set_money_double",
        description="[ADMIN] Ativa/Desativa o Dinheiro Duplo para um jogador.",
    )
    @app_commands.describe(
        membro="O membro para ativar/desativar o Dinheiro Duplo.",
        status="True para ativar, False para desativar.",
    )
    @commands.has_permissions(administrator=True)
    async def set_money_double(
        self, i: Interaction, membro: discord.Member, status: bool
    ):
        player_data = get_player_data(membro.id)
        if not player_data:
            await i.response.send_message(
                "Este jogador não possui uma ficha.", ephemeral=True
            )
            return

        player_data["money_double"] = status
        save_data()

        status_str = "ativado" if status else "desativado"
        await i.response.send_message(
            f"O Dinheiro Duplo para **{membro.display_name}** foi **{status_str}**."
        )

    @app_commands.command(
        name="criar_embed",
        description="[ADMIN] Crie um embed personalizado interativamente.",
    )
    @commands.has_permissions(administrator=True)
    async def criar_embed(self, i: Interaction):
        initial_embed = Embed(
            title="Novo Embed",
            description="Clique nos botões para editar.",
            color=Color.blue(),
        )
        initial_embed.set_footer(
            text="Criador de Embed", icon_url=self.bot.user.display_avatar.url
        )
        initial_embed.timestamp = datetime.now()

        view = EmbedCreatorView(initial_embed, i.user.id)

        await i.response.send_message(embed=initial_embed, view=view, ephemeral=True)
        view.message = await i.original_response()
