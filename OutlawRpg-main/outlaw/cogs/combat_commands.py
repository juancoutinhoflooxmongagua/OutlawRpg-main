import discord
from discord.ext import commands
from discord import app_commands, Embed, Color, Interaction
import random
from datetime import datetime

from data_manager import (
    get_player_data,
    save_data,
    player_database,
)
from config import (
    ENEMIES,
    WORLD_MAP,
    TRANSFORM_COST,
    ITEMS_DATA,
    CLASS_TRANSFORMATIONS,
    CRITICAL_CHANCE,
    CRITICAL_MULTIPLIER,
    BOUNTY_PERCENTAGE,
    INITIAL_ATTACK,
    INITIAL_SPECIAL_ATTACK,
)

from custom_checks import (
    check_player_exists,
    is_in_wilderness,
)
from utils import (
    calculate_effective_stats,
    run_turn_based_combat,
)


class CombatCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="cacar",
        description="Caça uma criatura na sua localização atual (combate por turnos).",
    )
    @app_commands.check(check_player_exists)
    @app_commands.check(is_in_wilderness)
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.user.id)
    async def cacar(self, i: Interaction):
        player_data = get_player_data(i.user.id)
        if player_data.get("status") == "dead":
            await i.response.send_message("Mortos não caçam.", ephemeral=True)
            return

        location_enemies = ENEMIES.get(player_data.get("location"))
        if not location_enemies:
            await i.response.send_message(
                f"Não há criaturas para caçar em {WORLD_MAP.get(player_data.get('location', {}), {}).get('name', 'sua localização atual')}.",
                ephemeral=True,
            )
            return

        await i.response.defer()

        enemy_template = random.choice(location_enemies)
        enemy = enemy_template.copy()
        await run_turn_based_combat(self.bot, i, player_data, enemy)

    @app_commands.command(
        name="batalhar",
        description="Enfrenta um Ex-Cavaleiro para testar sua força (combate por turnos).",
    )
    @app_commands.check(check_player_exists)
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.user.id)
    @app_commands.describe(
        primeiro_ataque="Escolha seu ataque inicial: Básico ou Especial."
    )
    @app_commands.choices(
        primeiro_ataque=[
            app_commands.Choice(name="Ataque Básico", value="basico"),
            app_commands.Choice(name="Ataque Especial", value="especial"),
        ]
    )
    async def batalhar(self, i: Interaction, primeiro_ataque: app_commands.Choice[str]):
        player_data = get_player_data(i.user.id)
        if player_data.get("status") == "dead":
            await i.response.send_message("Mortos não batalham.", ephemeral=True)
            return

        player_stats = calculate_effective_stats(player_data)

        if primeiro_ataque.value == "especial":
            cost_energy_special = TRANSFORM_COST
            cost_energy_special = max(
                1,
                int(
                    cost_energy_special
                    * (1 - player_stats.get("cooldown_reduction_percent", 0.0))
                ),
            )

            if player_data.get("energy", 0) < cost_energy_special:
                await i.response.send_message(
                    f"Você não tem energia suficiente ({cost_energy_special}) para um Ataque Especial inicial! Use Ataque Básico ou recupere energia.",
                    ephemeral=True,
                )
                return

        await i.response.defer()

        enemy = {
            "name": "Ex-Cavaleiro Renegado",
            "hp": 320,
            "attack": 95,
            "xp": 390,
            "money": 400,
            "thumb": "https://c.tenor.com/ebFt6wJWEu8AAAAC/tenor.gif",
        }
        await run_turn_based_combat(self.bot, i, player_data, enemy)

    @app_commands.command(name="atacar", description="Ataca outro jogador em um duelo.")
    @app_commands.check(check_player_exists)
    @app_commands.describe(
        alvo="O jogador que você quer atacar.", estilo="O tipo de ataque a ser usado."
    )
    @app_commands.choices(
        estilo=[
            app_commands.Choice(name="Ataque Básico", value="basico"),
            app_commands.Choice(name="Ataque Especial", value="especial"),
        ]
    )
    async def atacar(
        self, i: Interaction, alvo: discord.Member, estilo: app_commands.Choice[str]
    ):
        attacker_id, target_id = str(i.user.id), str(alvo.id)
        if attacker_id == target_id:
            await i.response.send_message(
                "Você não pode atacar a si mesmo!", ephemeral=True
            )