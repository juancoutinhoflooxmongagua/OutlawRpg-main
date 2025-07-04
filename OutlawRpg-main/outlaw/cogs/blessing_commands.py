import discord
from discord.ext import commands
from discord import app_commands, Embed, Color, Interaction
from datetime import datetime

from data_manager import get_player_data, save_data
from config import ITEMS_DATA, MAX_ENERGY
from custom_checks import check_player_exists


class BlessingCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="ativar_bencao",
        description="Ativa uma bênção desbloqueada para sua classe/estilo.",
    )
    @app_commands.choices(
        bencao_id=[
            app_commands.Choice(
                name="Bênção de Drácula (Vampiro)", value="bencao_dracula"
            ),
            app_commands.Choice(
                name="Benção do Rei Henrique (Aura)", value="bencao_rei_henrique"
            ),
        ]
    )
    @app_commands.check(check_player_exists)
    async def ativar_bencao(self, i: Interaction, bencao_id: app_commands.Choice[str]):
        raw_player_data = get_player_data(i.user.id)
        blessing_info = ITEMS_DATA.get(bencao_id.value)

        if not blessing_info or blessing_info.get("type") != "blessing_unlock":
            await i.response.send_message(
                "Bênção não reconhecida ou inválida.", ephemeral=True
            )
            return

        # Check if player owns the blessing (it's an unlockable item)
        if raw_player_data["inventory"].get(bencao_id.value, 0) == 0:
            await i.response.send_message(
                f"Você não desbloqueou a **{blessing_info['name']}**! Compre-a na loja primeiro.",
                ephemeral=True,
            )
            return

        # Check class/style restriction
        if (
            "class_restriction" in blessing_info
            and raw_player_data["class"] != blessing_info["class_restriction"]
        ):
            await i.response.send_message(
                f"Somente {blessing_info['class_restriction']}s podem ativar a {blessing_info['name']}.",
                ephemeral=True,
            )
            return
        if (
            "style_restriction" in blessing_info
            and raw_player_data["style"] != blessing_info["style_restriction"]
        ):
            await i.response.send_message(
                f"Somente usuários de **{blessing_info['style_restriction']}** podem invocar a {blessing_info['name']}.",
                ephemeral=True,
            )
            return

        # Check if blessing is already active
        active_key = f"{bencao_id.value}_active"
        if raw_player_data.get(active_key):
            await i.response.send_message(
                f"A **{blessing_info['name']}** já está ativa!", ephemeral=True
            )
            return

        # Check energy cost
        if raw_player_data["energy"] < blessing_info["cost_energy"]:
            await i.response.send_message(
                f"Energia insuficiente para ativar a **{blessing_info['name']}** ({blessing_info['cost_energy']} energia)!",
                ephemeral=True,
            )
            return

        # Activate blessing
        raw_player_data["energy"] -= blessing_info["cost_energy"]
        raw_player_data[active_key] = True
        raw_player_data[f"{bencao_id.value}_end_time"] = (
            datetime.now().timestamp() + blessing_info["duration_seconds"]
        )

        embed = Embed(
            title=f"{blessing_info['emoji']} {blessing_info['name']}! {blessing_info['emoji']}",
            description=f"{i.user.display_name} ativou a **{blessing_info['name']}**!\n"
            f"Seus atributos foram aprimorados por {blessing_info['duration_seconds'] // 60} minutos!",
            color=(
                Color.gold()
                if "rei_henrique" in bencao_id.value
                else Color.dark_purple()
            ),
        )
        if "rei_henrique" in bencao_id.value:
            embed.set_thumbnail(url="https://c.tenor.com/2U54k92V-i4AAAAC/tenor.gif")
        elif "dracula" in bencao_id.value:
            embed.set_thumbnail(url="https://c.tenor.com/A6j4yvK8J-oAAAAC/tenor.gif")

        await i.response.send_message(embed=embed)
        save_data()

    @app_commands.command(
        name="desativar_bencao",
        description="Desativa uma bênção ativa e recupera energia.",
    )
    @app_commands.choices(
        bencao_id=[
            app_commands.Choice(name="Bênção de Drácula", value="bencao_dracula"),
            app_commands.Choice(
                name="Benção do Rei Henrique", value="bencao_rei_henrique"
            ),
            app_commands.Choice(name="Todas as Bênçãos", value="all_blessings"),
        ]
    )
    @app_commands.check(check_player_exists)
    async def desativar_bencao(
        self, i: Interaction, bencao_id: app_commands.Choice[str]
    ):
        raw_player_data = get_player_data(i.user.id)
        deactivated_any = False
        messages = []

        blessings_to_check = []
        if bencao_id.value == "all_blessings":
            blessings_to_check = ["bencao_dracula", "bencao_rei_henrique"]
        else:
            blessings_to_check = [bencao_id.value]

        for b_id in blessings_to_check:
            active_key = f"{b_id}_active"
            end_time_key = f"{b_id}_end_time"
            blessing_info = ITEMS_DATA.get(b_id, {})
            blessing_name = blessing_info.get("name", "Bênção Desconhecida")

            if raw_player_data.get(active_key):
                raw_player_data[active_key] = False
                raw_player_data[end_time_key] = 0
                deactivated_any = True
                messages.append(f"A **{blessing_name}** foi desativada.")
            elif (
                bencao_id.value != "all_blessings"
            ):  # Only show message if user tried to deactivate a specific non-active blessing
                await i.response.send_message(
                    f"A **{blessing_name}** não está ativa.", ephemeral=True
                )
                return

        if deactivated_any:
            raw_player_data["energy"] = min(MAX_ENERGY, raw_player_data["energy"] + 1)
            save_data()
            messages.append("Você recuperou 1 de energia.")
            await i.response.send_message("\n".join(messages))
        elif bencao_id.value == "all_blessings":
            await i.response.send_message(
                "Você não tem nenhuma bênção ativa para desativar.",
                ephemeral=True,
            )
        # If a specific blessing was requested but not active, message was already sent above.
