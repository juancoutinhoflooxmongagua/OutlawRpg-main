import discord
from discord import ui, ButtonStyle, Interaction, Embed, Color
from datetime import datetime

from data_manager import get_player_data
from utils import calculate_effective_stats
from config import (
    XP_PER_LEVEL_BASE,
    MAX_ENERGY,
    WORLD_MAP,
    STARTING_LOCATION,
    ITEMS_DATA,
    CLASS_TRANSFORMATIONS,
    PROFILE_IMAGES,
    CUSTOM_EMOJIS,
)


class ProfileView(ui.View):
    """
    A Discord View optimized to display a player's profile and inventory
    with a clean, modern UI/UX inspired by the native Discord interface.
    """

    def __init__(
        self,
        user: discord.Member,
        bot_user: discord.ClientUser,
        original_interaction: Interaction,
    ):
        super().__init__(timeout=180)
        self.user = user
        self.bot_user = bot_user
        self.original_interaction = original_interaction

    @staticmethod
    def create_xp_bar(current_xp: int, needed_xp: int, length: int = 15) -> str:
        if needed_xp == 0:
            return "`" + "█" * length + "`"
        progress = min(current_xp / needed_xp, 1.0)
        filled_length = int(length * progress)
        bar = "█" * filled_length + "░" * (length - filled_length)
        return f"`{bar}`"

    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 15) -> str:
        """Creates a simple text-based progress bar."""
        if total == 0:
            return "`" + "█" * length + "`"
        progress = min(current / total, 1.0)
        filled_length = int(length * progress)
        bar = "█" * filled_length + "░" * (length - filled_length)
        return f"`{bar}`"

    def create_profile_embed(self) -> discord.Embed:
        """
        Creates the profile embed with a responsive layout (all stats in a single field).
        """
        player_data = get_player_data(self.user.id)
        if not player_data:
            return Embed(
                title="❌ Erro",
                description="Dados do jogador não encontrados.",
                color=Color.red(),
            )

        player_stats = calculate_effective_stats(player_data)

        # --- Logic for Effects and Embed Color ---
        active_effects = []
        embed_color = self.user.color
        profile_image_url = PROFILE_IMAGES.get(player_data["class"])

        if player_data.get("current_transformation"):
            transform_name = player_data["current_transformation"]
            transform_info_from_class = CLASS_TRANSFORMATIONS.get(
                player_data["class"], {}
            ).get(transform_name, {})

            active_effects.append(
                f"{transform_info_from_class.get('emoji', '🔥')} **{transform_name}**"
            )
            profile_image_url = PROFILE_IMAGES.get(transform_name, profile_image_url)
            embed_color = Color.orange()

        if player_data.get("aura_blessing_active"):
            blessing_info = ITEMS_DATA.get("bencao_rei_henrique", {})
            blessing_name = blessing_info.get("name")
            active_effects.append(
                f"{blessing_info.get('emoji', '✨')} **{blessing_name}**"
            )
            if not player_data.get("current_transformation"):
                profile_image_url = PROFILE_IMAGES.get(blessing_name, profile_image_url)
                embed_color = Color.gold()

        if player_data.get("bencao_dracula_active"):
            dracula_info = ITEMS_DATA.get("bencao_dracula", {})
            active_effects.append(
                f"{dracula_info.get('emoji', '🦇')} **{dracula_info.get('name')}**"
            )

        # --- Embed Creation ---
        embed = Embed(title=f"Perfil de {self.user.display_name}", color=embed_color)
        embed.set_thumbnail(url=self.user.display_avatar.url)
        if profile_image_url:
            embed.set_image(url=profile_image_url)

        # --- Progress Bars ---
        hp_bar = self.create_progress_bar(player_data["hp"], player_stats["max_hp"])
        energy_bar = self.create_progress_bar(player_data["energy"], MAX_ENERGY)
        xp_needed = int(XP_PER_LEVEL_BASE * (player_data["level"] ** 1.2))
        xp_bar = self.create_xp_bar(player_data["xp"], xp_needed)

        # --- Main Description (Character Summary) ---
        location_info = WORLD_MAP.get(
            player_data.get("location", STARTING_LOCATION), {}
        )
        status_map = {"online": "🟢 Online", "dead": "💀 Morto", "afk": "🌙 AFK"}

        embed.description = (
            f"**{player_data['class']}** | Nível **{player_data['level']}**\n"
            f"{xp_bar} `({player_data['xp']}/{xp_needed} XP)`\n"
            f"📍 **Localização:** `{location_info.get('name', 'Desconhecida')}`\n"
            f"Status: *{status_map.get(player_data['status'], 'Indefinido')}*\n"
        )

        # --- Detailed Stats (all in one inline=False field for maximum responsiveness and readability) ---
        stats_value = (
            f"**__⚔️ Combate__**\n"
            f"❤️ **Vida:** `{player_data['hp']}/{player_stats['max_hp']}` {hp_bar}\n"
            f"🗡️ **Ataque:** `{player_stats['attack']}`\n"
            f"✨ **Atq. Especial:** `{player_stats['special_attack']}`\n"
            f"\n"
            f"**__⚙️ Recursos__**\n"
            f"⚡ **Energia:** `{player_data['energy']}/{MAX_ENERGY}` {energy_bar}\n"
            f"💰 **Dinheiro:** `${player_data['money']}`\n"
            f"🌟 **Pontos de Atributo:** `{player_data.get('attribute_points', 0)}`\n"
            f"\n"
            f"**__🏆 Registro & Boosts__**\n"
            f"⚔️ **Abates:** `{player_data['kills']}`\n"
            f"☠️ **Mortes:** `{player_data['deaths']}`\n"
            f"🏴‍☠️ **Recompensa:** `${player_data.get('bounty', 0)}`\n"
            f"🚀 **XP Triplo:** `{'✅ Ativo' if player_data.get('xptriple') else '❌ Inativo'}`\n"
            f"💸 **Dinheiro Duplo:** `{'✅ Ativo' if player_data.get('money_double') else '❌ Inativo'}`"
        )
        embed.add_field(name="Detalhes do Fora-da-Lei", value=stats_value, inline=False)

        # --- Active Effects Field (if any) ---
        if active_effects:
            embed.add_field(
                name="✨ Efeitos Ativos", value="\n".join(active_effects), inline=False
            )

        embed.set_footer(
            text=f"Outlaws RPG • {self.user.name}",
            icon_url=self.bot_user.display_avatar.url,
        )
        embed.timestamp = datetime.now()
        return embed

    def create_inventory_embed(self) -> discord.Embed:
        """
        Creates the player's inventory embed.
        """
        player_data = get_player_data(self.user.id)
        if not player_data:
            return Embed(
                title="❌ Erro",
                description="Dados do jogador não encontrados.",
                color=Color.red(),
            )

        embed = Embed(
            title=f"Inventário de {self.user.display_name}", color=self.user.color
        )
        embed.set_thumbnail(url=self.user.display_avatar.url)

        inventory_items = player_data.get("inventory", {})
        if not inventory_items:
            embed.description = "🎒 *O inventário está vazio.*"
        else:
            item_list = []
            for item_id, amount in inventory_items.items():
                item_data = ITEMS_DATA.get(item_id, {})
                emoji = item_data.get("emoji", "❔")
                name = item_data.get("name", item_id.replace("_", " ").title())
                if amount > 0:
                    item_list.append(f"{emoji} **{name}** `x{amount}`")
            if not item_list:
                embed.description = "🎒 *O inventário está vazio.*"
            else:
                embed.description = "\n".join(item_list)

        embed.set_footer(
            text=f"Outlaws RPG • {self.user.name}",
            icon_url=self.bot_user.display_avatar.url,
        )
        embed.timestamp = datetime.now()
        return embed

    @ui.button(label="Perfil", style=ButtonStyle.primary, emoji="👤", disabled=True)
    async def profile_button(self, interaction: Interaction, button: ui.Button):
        self.profile_button.disabled = True
        self.inventory_button.disabled = False
        await self.original_interaction.edit_original_response(
            embed=self.create_profile_embed(), view=self
        )
        await interaction.response.defer()

    @ui.button(label="Inventário", style=ButtonStyle.secondary, emoji="🎒")
    async def inventory_button(self, interaction: Interaction, button: ui.Button):
        self.inventory_button.disabled = True
        self.profile_button.disabled = False
        await self.original_interaction.edit_original_response(
            embed=self.create_inventory_embed(), view=self
        )
        await interaction.response.defer()
