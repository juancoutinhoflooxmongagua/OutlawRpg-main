import discord
from discord.ext import commands
from discord import app_commands, Embed, Color, Interaction

from data_manager import get_player_data, save_data, player_database
from config import (
    INITIAL_HP,
    INITIAL_ATTACK,
    INITIAL_SPECIAL_ATTACK,
    INITIAL_MONEY,
    MAX_ENERGY,
    REVIVE_COST,
    XP_PER_LEVEL_BASE,
    ATTRIBUTE_POINTS_PER_LEVEL,
    NEW_CHARACTER_ROLE_ID,
    WORLD_MAP,
    STARTING_LOCATION,
)
from custom_checks import check_player_exists
from views.class_chooser_view import ClassChooserView
from views.profile_view import ProfileView
from utils import calculate_effective_stats


class CharacterCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="criar_ficha",
        description="Cria sua ficha de personagem no mundo de OUTLAWS.",
    )
    async def criar_ficha(self, i: Interaction):
        if get_player_data(i.user.id):
            await i.response.send_message("Você já possui uma ficha!", ephemeral=True)
            return

        view = ClassChooserView(self.bot)
        await i.response.send_message(
            embed=Embed(
                title="Criação de Personagem",
                description="Escolha os fundamentos do seu personagem.",
                color=Color.blurple(),
            ),
            view=view,
            ephemeral=True,
        )

    @app_commands.command(
        name="perfil",
        description="Mostra seu perfil de fora-da-lei com um layout profissional.",
    )
    @app_commands.check(check_player_exists)
    async def perfil(self, i: Interaction, membro: discord.Member = None):
        target_user = membro or i.user
        player_data = get_player_data(target_user.id)
        if not player_data:
            await i.response.send_message(
                "Essa pessoa ainda não é um fora-da-lei.", ephemeral=True
            )
            return

        await i.response.defer()

        view = ProfileView(target_user, self.bot.user, i)
        await i.edit_original_response(
            embed=view.create_profile_embed(),
            view=view,
        )

    @app_commands.command(
        name="reviver", description="Pague uma taxa para voltar à vida."
    )
    @app_commands.check(check_player_exists)
    async def reviver(self, i: Interaction):
        player_data = get_player_data(i.user.id)
        if player_data["status"] != "dead":
            await i.response.send_message("Você já está vivo!", ephemeral=True)
            return

        # Modificação para permitir que 'Corpo Seco' reviva sem custo
        if player_data["class"] == "Corpo Seco":
            revive_message = "Você, como um Corpo Seco, se ergueu novamente sem custo!"
            cost = 0
        elif player_data["money"] < REVIVE_COST:
            await i.response.send_message(
                f"Você precisa de ${REVIVE_COST} para reviver.", ephemeral=True
            )
            return
        else:
            cost = REVIVE_COST
            player_data["money"] -= cost
            revive_message = f"Você pagou ${REVIVE_COST} e trapaceou a morte."

        player_data["hp"] = player_data["max_hp"]
        player_data["status"] = "online"
        player_data["amulet_used_since_revive"] = False
        save_data()
        await i.response.send_message(
            embed=Embed(
                title="✨ De Volta à Vida",
                description=revive_message,
                color=Color.light_grey(),
            )
        )

    @app_commands.command(
        name="distribuir_pontos",
        description="Use seus pontos de atributo para fortalecer seu personagem.",
    )
    @app_commands.describe(
        atributo="Onde você quer investir seus pontos.",
        quantidade="Quantos pontos quer usar.",
    )
    @app_commands.choices(
        atributo=[
            app_commands.Choice(name="💪 Força (Ataque)", value="attack"),
            app_commands.Choice(
                name="✨ Agilidade (Atq. Especial)", value="special_attack"
            ),
            app_commands.Choice(name="❤️ Vitalidade (HP)", value="hp"),
        ]
    )
    @app_commands.check(check_player_exists)
    async def distribuir_pontos(
        self, i: Interaction, atributo: app_commands.Choice[str], quantidade: int
    ):
        player_data = get_player_data(i.user.id)
        available_points = player_data.get("attribute_points", 0)
        if quantidade <= 0:
            await i.response.send_message(
                "A quantidade deve ser positiva.", ephemeral=True
            )
            return
        if available_points < quantidade:
            await i.response.send_message(
                f"Você só tem {available_points} pontos.", ephemeral=True
            )
            return
        player_data["attribute_points"] -= quantidade
        if atributo.value == "attack":
            player_data["base_attack"] += quantidade * 2
        elif atributo.value == "special_attack":
            player_data["base_special_attack"] += quantidade * 3
        elif atributo.value == "hp":
            player_data["max_hp"] += quantidade * 5
            player_data["hp"] += quantidade * 5
        save_data()
        await i.response.send_message(
            embed=Embed(
                title="📈 Atributos Aprimorados",
                description=f"Você investiu **{quantidade}** pontos em **{atributo.name}**.",
                color=Color.green(),
            )
        )

    @app_commands.command(
        name="ranking",
        description="Mostra o ranking de MVPs (Mais Abates) do servidor.",
    )
    async def ranking(self, i: Interaction):
        if not player_database:
            await i.response.send_message(
                "Nenhum jogador no ranking ainda.", ephemeral=True
            )
            return

        await i.response.defer()

        guild_members = {}
        if i.guild:
            try:
                async for member in i.guild.fetch_members(limit=None):
                    guild_members[member.id] = member
            except discord.Forbidden:
                print(
                    f"Bot lacks 'Members Intent' or 'Read Members' permission in guild {i.guild.name}. Cannot fetch all members for ranking."
                )
            except Exception as e:
                print(f"Error fetching guild members for ranking: {e}")

        sorted_players = sorted(
            player_database.values(),
            key=lambda p: (p.get("kills", 0), p.get("level", 1), p.get("money", 0)),
            reverse=True,
        )

        embed = Embed(
            title="🏆 Ranking de MVPs - OUTLAWS 🏆",
            description="Os fora-da-lei mais temidos do servidor.",
            color=Color.gold(),
        )

        rank_entries = []
        for idx, player_data in enumerate(sorted_players[:10]):
            player_id_str = None
            for uid_str, data_val in player_database.items():
                if data_val == player_data:
                    player_id_str = uid_str
                    break

            if not player_id_str:
                continue

            player_id = int(player_id_str)
            member = guild_members.get(player_id)

            player_display_name = (
                member.display_name
                if member
                else player_data.get("name", "Desconhecido")
            )
            avatar_url = (
                member.display_avatar.url
                if member and member.display_avatar
                else "https://discord.com/assets/f9bb9c17af1b5c2a048a1d13f9c646f8.png"
            )

            rank_entries.append(
                f"**{idx+1}.** [{player_display_name}]({avatar_url})\n"
                f"  **Abates:** {player_data.get('kills', 0)} | "
                f"**Mortes:** {player_data.get('deaths', 0)} | "
                f"**Recompensa:** ${player_data.get('bounty', 0)}"
            )

        if rank_entries:
            embed.description = "\n\n".join(rank_entries)
        else:
            embed.description = "Nenhum jogador no ranking ainda."

        embed.set_footer(text="A glória aguarda os mais audazes!")
        await i.edit_original_response(embed=embed)
