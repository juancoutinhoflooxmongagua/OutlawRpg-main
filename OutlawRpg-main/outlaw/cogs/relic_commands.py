# File: OutlawRpg-main/outlaw/cogs/relic_commands.py

import discord
from discord.ext import commands, tasks
from discord import (
    app_commands,
    Embed,
    Color,
    Interaction,
)
from discord.ui import (
    Button,
    View,
)

import asyncio
from datetime import datetime, timedelta
import random # Needed for random selection in get_random_relic

# Import from your data management and game logic modules
from data_manager import (
    get_player_data,
    save_data,
    player_database,
    add_item_to_inventory,
    add_user_money,
    add_user_energy,
    check_and_add_keys,
    get_time_until_next_key_claim,
)
from config import (
    ITEMS_DATA, # Used to get relic info by ID in /inventory
)
from custom_checks import check_player_exists

from relics import relics # Assuming relics.py exports a list named 'relics'
from game_logic.relic_mechanics import get_random_relic # This function should pull from the 'relics' list

from utils import (
    format_cooldown, # Retained for displaying key cooldowns
)


# Dictionary of chest images by Relic Tier
# IMPORTANT: Replace these URLs with your own chest images for each tier!
TIER_CHEST_IMAGES = {
    "Básica": "https://i.imgur.com/YFS0E0O.png",
    "Comum": "https://i.imgur.com/1C8QcA4.png",
    "Incomum": "https://i.imgur.com/2ji2Ucq.png",
    "Rara": "https://i.imgur.com/vQdnSCF.png",
    "Épica": "https://i.imgur.com/sTFdcbE.png",
    "Mítica": "https://i.imgur.com/mythic_chest.png",
}


# Class View for the "Open Chest" button (used by /bau)
class OpenChestView(View):
    def __init__(self, gained_relic: dict, user_id: int, relic_commands_cog):
        super().__init__(timeout=60)
        self.gained_relic = gained_relic
        self.user_id = user_id
        self.relic_commands_cog = relic_commands_cog

    @discord.ui.button(label="Abrir Baú", style=discord.ButtonStyle.green, emoji="🔑")
    async def open_button_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Este baú não é seu para abrir!", ephemeral=True
            )
            return

        await interaction.response.defer()

        user_data = get_player_data(str(self.user_id))
        keys_available = user_data.get("relic_keys", 0)

        if keys_available <= 0:
            await interaction.edit_original_response(
                content="Você não tem mais chaves para abrir este baú!",
                embed=None,
                view=None,
            )
            self.stop()
            return

        user_data["relic_keys"] = user_data.get("relic_keys", 0) - 1
        save_data()

        # Add the relic to inventory and grant rewards
        # Assuming gained_relic has an 'id' field that matches ITEMS_DATA keys
        add_item_to_inventory(str(self.user_id), self.gained_relic["id"], 1)
        add_user_money(str(self.user_id), self.gained_relic.get("valor_moedas", 0))
        add_user_energy(str(self.user_id), self.gained_relic.get("energia_concedida", 0))

        relic_tier = self.gained_relic.get("tier", "Básica")
        chest_image_to_display = TIER_CHEST_IMAGES.get(
            relic_tier, "https://i.imgur.com/default_basic_chest.png"
        )

        reward_embed = Embed(
            title="Você Abriu o Baú e Ganhou!",
            description=(
                f"🎉 Parabéns! Você obteve a relíquia: **{self.gained_relic.get('name', 'Relíquia Desconhecida')}**!\n\n"
                f"**Tier:** {relic_tier}\n"
                f"**Valor:** {self.gained_relic.get('valor_moedas', 0)} moedas\n"
                f"**Energia:** {self.gained_relic.get('energia_concedida', 0)} pontos\n"
                f"**Chance de Obtenção:** {self.gained_relic.get('chance_obter_percentual', 'N/A')}%"
            ),
            color=self.relic_commands_cog._get_tier_color(relic_tier),
        )
        reward_embed.set_image(url=chest_image_to_display)

        updated_keys_available = user_data.get("relic_keys", 0)
        time_remaining_seconds_updated = get_time_until_next_key_claim(self.user_id)
        if time_remaining_seconds_updated > 0:
            td_updated = timedelta(seconds=int(time_remaining_seconds_updated))
            footer_text = f"Chaves restantes: {updated_keys_available} | Novas chaves em {format_cooldown(time_remaining_seconds_updated)}."
        else:
            footer_text = f"Chaves restantes: {updated_keys_available} | Você pode reivindicar novas chaves agora!"

        reward_embed.set_footer(
            text=f"{footer_text} Use /inventory para ver suas relíquias."
        )

        for item in self.children:
            item.disabled = True

        await interaction.edit_original_response(embed=reward_embed, view=self)
        self.stop()

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.NotFound:
            pass


class RelicCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.key_generation_task.start()

    def cog_unload(self):
        self.key_generation_task.cancel()

    @tasks.loop(minutes=1)
    async def key_generation_task(self):
        all_user_data = player_database

        user_ids_to_check = list(all_user_data.keys())

        for user_id_str in user_ids_to_check:
            user_id = int(user_id_str)
            keys_added = check_and_add_keys(user_id)

            if keys_added > 0:
                print(f"Adicionadas {keys_added} chaves para o usuário {user_id}")
                user = self.bot.get_user(user_id)
                if user is None:
                    try:
                        user = await self.bot.fetch_user(user_id)
                    except discord.NotFound:
                        user = None

                if user:
                    try:
                        await user.send(
                            f"Você recebeu {keys_added} chaves de baú! Use-as com `/bau`."
                        )
                    except discord.Forbidden:
                        print(f"Não foi possível enviar DM para {user.name} ({user.id}).")
                    except Exception as e:
                        print(f"Erro ao enviar DM para {user.id}): {e}")

    @key_generation_task.before_loop
    async def before_key_generation(self):
        await self.bot.wait_until_ready()
        print("Tarefa de geração de chaves iniciada e aguardando bot pronto.")

    def _get_tier_color(self, tier: str) -> Color:
        """Returns a color for the embed based on the relic's tier."""
        colors = {
            "Básica": Color.light_grey(),
            "Comum": Color.dark_grey(),
            "Incomum": Color.green(),
            "Rara": Color.blue(),
            "Épica": Color.purple(),
            "Mítica": Color.red(),
        }
        return colors.get(tier, Color.default())

## Chest Command

# This command allows players to open chests using relic keys.
    
    @app_commands.command(name="bau", description="Mostra o baú e permite abri-lo.")
    @app_commands.check(check_player_exists) # Added check for consistency
    async def open_chest(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        await interaction.response.defer(ephemeral=False)

        # Ensure keys are updated before checking
        check_and_add_keys(interaction.user.id)
        user_data = get_player_data(user_id)

        keys_available = user_data.get("relic_keys", 0)

        if keys_available <= 0:
            time_remaining_seconds = get_time_until_next_key_claim(interaction.user.id)
            time_str = f"Novas chaves em **{format_cooldown(time_remaining_seconds)}**." if time_remaining_seconds > 0 else "Você pode reivindicar novas chaves agora!"

            chest_image_to_display = TIER_CHEST_IMAGES.get(
                "Básica", "https://i.imgur.com/default_basic_chest.png"
            )

            no_keys_embed = Embed(
                title="Um Baú Misterioso Aparece!",
                description=f"Você não tem chaves para abrir este baú! 😔\n\n{time_str}",
                color=Color.red(),
            )
            no_keys_embed.set_image(url=chest_image_to_display)
            no_keys_embed.set_footer(text="Use /inventory para ver suas relíquias.")
            await interaction.edit_original_response(embed=no_keys_embed)
            return

        # Get a random relic from the 'relics' list (from relics.py)
        # Assuming get_random_relic correctly picks from `relics` and formats it
        gained_relic = get_random_relic(relics) # Pass the relics list to the function
        
        # Ensure gained_relic has expected keys, provide defaults if not
        relic_tier = gained_relic.get("tier", "Básica")
        chest_image_to_display = TIER_CHEST_IMAGES.get(
            relic_tier, "https://i.imgur.com/default_basic_chest.png"
        )

        initial_chest_embed = Embed(
            title="Um Baú Misterioso Aparece!",
            description="Clique no botão abaixo para abrir o baú e revelar seu conteúdo!",
            color=self._get_tier_color(relic_tier),
        )
        initial_chest_embed.set_image(url=chest_image_to_display)
        initial_chest_embed.set_footer(text=f"Você tem {keys_available} chaves.")

        view = OpenChestView(gained_relic, interaction.user.id, self)

        await interaction.edit_original_response(embed=initial_chest_embed, view=view)

        view.message = await interaction.original_response()

## Inventory Command

# This command displays the player's current relic inventory.

    @app_commands.command(
        name="inventory",
        description="Mostra suas relíquias obtidas.",
    )
    @app_commands.check(check_player_exists)
    async def show_inventory(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = get_player_data(user_id)
        
        # Now inventory should pull from 'relics_inventory'
        inventory_relic_ids = user_data.get("relics_inventory", []) 

        if not inventory_relic_ids:
            embed = Embed(
                title="Seu Inventário de Relíquias",
                description="Você ainda não possui nenhuma relíquia. Use `/bau` para tentar a sorte!",
                color=Color.blue(),
            )
        else:
            relic_counts = {}
            for relic_id in inventory_relic_ids:
                relic_counts[relic_id] = relic_counts.get(relic_id, 0) + 1

            display_items = []
            for relic_id, count in relic_counts.items():
                relic_info = ITEMS_DATA.get(relic_id) # Get relic info from ITEMS_DATA
                if relic_info:
                    display_items.append(
                        {"name": relic_info.get('name', relic_id), "count": count, "tier": relic_info.get('tier', 'Desconhecido')}
                    )

            tier_order = {
                "Mítica": 6, "Épica": 5, "Rara": 4, "Incomum": 3, "Comum": 2, "Básica": 1, "Desconhecido": 0
            }
            # Sort by tier (descending), then by name (ascending)
            display_items.sort(key=lambda x: (tier_order.get(x["tier"], 0), x["name"]), reverse=True)

            inventory_text = ""
            for item in display_items:
                inventory_text += (
                    f"- **{item['name']}** ({item['tier']}) x{item['count']}\n"
                )

            embed = Embed(
                title="Seu Inventário de Relíquias",
                description=inventory_text,
                color=Color.blue(),
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(RelicCommands(bot))