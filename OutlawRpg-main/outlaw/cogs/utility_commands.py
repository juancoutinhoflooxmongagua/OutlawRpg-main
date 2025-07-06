import discord
from discord.ext import commands
from discord import app_commands, Embed, Color, Interaction
from datetime import timedelta, datetime

from data_manager import get_player_data, save_data
from custom_checks import check_player_exists
from views.help_view import HelpView
from config import ITEMS_DATA, CLASS_TRANSFORMATIONS


class UtilityCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help", description="Mostra a wiki interativa do bot OUTLAWS."
    )
    async def help(self, i: Interaction):
        embed = Embed(
            title="📜 Bem-vindo à Wiki de OUTLAWS",
            description="Use o menu abaixo para navegar pelos tópicos.",
            color=Color.blurple(),
        )
        embed.set_thumbnail(url="https://i.imgur.com/Sce6RIJ.png")
        await i.response.send_message(embed=embed, view=HelpView())

    @app_commands.command(
        name="lore", description="Mostra a história do mundo de Outlaws."
    )
    async def lore(self, i: Interaction):
        lore_text = """
        No alvorecer dos tempos, a **Terra 1** era um santuário de serenidade, onde a vida florescia em harmonia e a paz reinava soberana. O seu líder, o **Rei da Luz, Luís Henrique III**, forjou essa união após incontáveis batalhas, consolidando um reino de prosperidade e tranquilidade. Naquele tempo, a magia era um conceito desconhecido, um poder adormecido que aguardava o seu despertar.

        Contudo, a inveja corroeu o coração do tio do Rei da Luz. Consumido pela ambição e seduzido pelas sombras, ele selou um pacto profano com o **Senhor da Morte**. Em troca de poder ilimitado, o ser inominável, conhecido apenas como "**o Inpronunciável**", prometeu ceifar almas e abrir caminho para a dominação multiversal, mergulhando a existência no caos.

        Após o desaparecimento do Senhor da Morte, o Inpronunciável desencadeou sua fúria em uma batalha épica contra as forças da Luz e o Rei Luís Henrique III. O confronto foi devastador, resultando na queda de ambos os líderes. Sem rei e sem proteção, a Terra 1 ficou à mercê do destino.

        Desse vácuo de poder, emergiram os **Outlaws (Foras da Lei)**. Sejam eles guiados pela virtude ou pela maldade, esses indivíduos se uniram com um único propósito: reconstruir a Terra 1. Renomeando-a para **Terra Outlaw**, eles juraram protegê-la... ou destruí-la. O futuro da Terra Outlaw agora repousa nas mãos desses enigmáticos forasteiros.
        """
        embed = Embed(
            title="📜 A Lenda da Terra Outlaw 📜",
            description=lore_text,
            color=Color.dark_purple(),
        )
        embed.set_thumbnail(url="https://i.imgur.com/Sce6RIJ.png")
        await i.response.send_message(embed=embed)

    @app_commands.command(
        name="afk",
        description="Entra no modo AFK. Você não pode ser alvo nem usar comandos.",
    )
    @app_commands.check(check_player_exists)
    async def afk(self, i: Interaction):
        player_data = get_player_data(i.user.id)
        now = datetime.now().timestamp()
        afk_cooldown_duration = 10800

        last_return_from_afk = player_data["cooldowns"].get("afk_cooldown", 0)
        if now - last_return_from_afk < afk_cooldown_duration:
            remaining_time_seconds = afk_cooldown_duration - (
                now - last_return_from_afk
            )
            remaining_time = str(timedelta(seconds=int(remaining_time_seconds)))
            await i.response.send_message(
                f"Você só pode entrar em modo AFK a cada {afk_cooldown_duration // 3600} horas. Tente novamente em **{remaining_time}**.",
                ephemeral=True,
            )
            return

        if player_data["status"] == "afk":
            await i.response.send_message("Você já está em modo AFK.", ephemeral=True)
            return

        player_data["status"] = "afk"
        save_data()
        await i.response.send_message(
            "🌙 Você entrou em modo AFK. Use `/voltar` para ficar online."
        )

    @app_commands.command(
        name="voltar", description="Sai do modo AFK e volta a ficar online."
    )
    async def voltar(self, i: Interaction):
        player_data = get_player_data(i.user.id)

        if not player_data:
            await i.response.send_message(
                "Você não tem uma ficha! Use `/criar_ficha`.", ephemeral=True
            )
            return

        if player_data["status"] != "afk":
            await i.response.send_message("Você não está em modo AFK.", ephemeral=True)
            return

        player_data["status"] = "online"
        player_data["cooldowns"]["afk_cooldown"] = datetime.now().timestamp()
        save_data()
        await i.response.send_message(
            "🟢 Você está online novamente! O cooldown para usar `/afk` outra vez começou."
        )
