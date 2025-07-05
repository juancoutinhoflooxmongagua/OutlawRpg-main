# File: outlawrpg-main/OutlawRpg-main-08db082cd4e4768d031dc16c0dd762b16b1328e6/OutlawRpg-main/outlaw/views/profile_view.py
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
    # PROFILE_IMAGES (Removido, pois não será mais usado para definir a imagem principal do perfil)
    CUSTOM_EMOJIS,
)


class ProfileView(ui.View):
    """
    A Discord View otimizada para exibir o perfil e inventário de um jogador
    com um design profissional e responsivo, inspirado no layout nativo do Discord.
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
        return f"[{bar}] **{current_xp}/{needed_xp} XP**"

    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 15) -> str:
        """Cria uma barra de progresso simples baseada em texto."""
        if total == 0:
            return "`" + "█" * length + "`"
        progress = min(current / total, 1.0)
        filled_length = int(length * progress)
        bar = "█" * filled_length + "░" * (length - filled_length)
        return f"[{bar}] **{current}/{total}**"

    def _get_base_profile_embed(self, player_data) -> Embed:
        """Helper para criar a estrutura base do embed, com foco em um design limpo."""
        if player_data is None:
            return Embed(
                title="❌ Erro",
                description="Dados do jogador não encontrados ao criar o embed base.",
                color=Color.red(),
            )

        embed_color = self.user.color
        # profile_image_url = PROFILE_IMAGES.get(player_data.get("class", "Unknown")) # REMOVIDO: Não usará imagens de classe/transformação

        if player_data.get("current_transformation"):
            transform_name = player_data["current_transformation"]
            transform_info_from_class = CLASS_TRANSFORMATIONS.get(
                player_data.get("class", "Unknown"), {}
            ).get(transform_name, {})
            # profile_image_url = PROFILE_IMAGES.get(transform_name, profile_image_url) # REMOVIDO
            embed_color = Color.orange()
        elif player_data.get("aura_blessing_active"):
            blessing_info = ITEMS_DATA.get("bencao_rei_henrique", {})
            blessing_name = blessing_info.get("name")
            # profile_image_url = PROFILE_IMAGES.get(blessing_name, profile_image_url) # REMOVIDO
            embed_color = Color.gold()

        # Título mais direto e claro
        embed = Embed(title=f"Perfil de {self.user.display_name}", color=embed_color)
        embed.set_thumbnail(
            url=self.user.display_avatar.url
        )  # Mantém o avatar do usuário
        # if profile_image_url: # REMOVIDO: Não usará imagem principal de perfil
        #     embed.set_image(url=profile_image_url) # REMOVIDO

        embed.set_footer(
            text=f"Outlaws RPG • {self.user.name}",
            icon_url=self.bot_user.display_avatar.url,
        )
        embed.timestamp = datetime.now()
        return embed

    def create_profile_embed(self) -> discord.Embed:
        """
        Cria o embed do perfil, com um design limpo e responsivo.
        As informações são agrupadas logicamente em campos separados.
        """
        player_data = get_player_data(self.user.id)
        if not player_data:
            return Embed(
                title="❌ Erro",
                description="Dados do jogador não encontrados.",
                color=Color.red(),
            )

        embed = self._get_base_profile_embed(player_data)
        if embed.title == "❌ Erro":
            return embed

        player_stats = calculate_effective_stats(player_data)

        # --- Descrição Principal (Resumo Essencial) ---
        xp_needed = int(XP_PER_LEVEL_BASE * (player_data.get("level", 1) ** 1.2))
        xp_bar = self.create_xp_bar(player_data.get("xp", 0), xp_needed)
        location_info = WORLD_MAP.get(
            player_data.get("location", STARTING_LOCATION), {}
        )
        status_map = {"online": "🟢 Online", "dead": "💀 Morto", "afk": "🌙 AFK"}

        # Descrição concisa com as informações mais relevantes no topo
        embed.description = (
            f"{CUSTOM_EMOJIS.get('class_icon', '🎭')} **Classe:** **{player_data.get('class', 'Desconhecida')}**\n"
            f"{CUSTOM_EMOJIS.get('level_icon', '⬆️')} **Nível:** **{player_data.get('level', 1)}** "
            f"({xp_bar})\n"
            f"{CUSTOM_EMOJIS.get('location_icon', '📍')} **Localização:** `{location_info.get('name', 'Desconhecida')}`\n"
            f"{CUSTOM_EMOJIS.get('status_icon', '📊')} **Status:** **{status_map.get(player_data.get('status', 'Indefinido'), 'Indefinido')}**\n"
        )

        # --- Campo de Combate (Separado) ---
        combat_value = (
            f"{CUSTOM_EMOJIS.get('hp_icon', '❤️')} **Vida:** {self.create_progress_bar(player_data.get('hp', 0), player_stats.get('max_hp', 1))}\n"
            f"{CUSTOM_EMOJIS.get('attack_icon', '🗡️')} **Ataque:** **{player_stats.get('attack', 0)}**\n"
            f"{CUSTOM_EMOJIS.get('special_attack_icon', '✨')} **Atq. Especial:** **{player_stats.get('special_attack', 0)}**\n"
        )
        embed.add_field(name="⚔️ Combate", value=combat_value, inline=False)

        # --- Campo de Efeitos Ativos (Se houver) ---
        active_effects = []
        if player_data.get("current_transformation"):
            transform_name = player_data["current_transformation"]
            transform_info_from_class = CLASS_TRANSFORMATIONS.get(
                player_data.get("class", "Unknown"), {}
            ).get(transform_name, {})
            active_effects.append(
                f"{transform_info_from_class.get('emoji', '🔥')} **{transform_name}**"
            )
        if player_data.get("aura_blessing_active"):
            blessing_info = ITEMS_DATA.get("bencao_rei_henrique", {})
            active_effects.append(
                f"{blessing_info.get('emoji', '✨')} **{blessing_info.get('name')}**"
            )
        if player_data.get("bencao_dracula_active"):
            dracula_info = ITEMS_DATA.get("bencao_dracula", {})
            active_effects.append(
                f"{dracula_info.get('emoji', '🦇')} **{dracula_info.get('name')}**"
            )

        if active_effects:
            embed.add_field(
                name="✨ Efeitos Ativos", value="\n".join(active_effects), inline=False
            )
        return embed

    def create_resources_embed(self) -> discord.Embed:
        """
        Cria o embed de recursos do jogador, com design responsivo.
        """
        player_data = get_player_data(self.user.id)
        if not player_data:
            return Embed(
                title="❌ Erro",
                description="Dados do jogador não encontrados.",
                color=Color.red(),
            )

        embed = self._get_base_profile_embed(player_data)
        if embed.title == "❌ Erro":
            return embed
        embed.title = f"Recursos de {self.user.display_name}"

        energy_bar = self.create_progress_bar(player_data.get("energy", 0), MAX_ENERGY)

        resources_value = (
            f"{CUSTOM_EMOJIS.get('energy_icon', '⚡')} **Energia:** {energy_bar}\n"
            f"{CUSTOM_EMOJIS.get('money_icon', '💰')} **Dinheiro:** **${player_data.get('money', 0):,}**\n"
            f"{CUSTOM_EMOJIS.get('attribute_points_icon', '💎')} **Pontos de Atributo:** **{player_data.get('attribute_points', 0)}**\n"
        )
        embed.add_field(name="⚙️ Seus Recursos", value=resources_value, inline=False)
        return embed

    def create_record_boosts_embed(self) -> discord.Embed:
        """
        Cria o embed de registro e boosts do jogador, com design responsivo.
        """
        player_data = get_player_data(self.user.id)
        if not player_data:
            return Embed(
                title="❌ Erro",
                description="Dados do jogador não encontrados.",
                color=Color.red(),
            )

        embed = self._get_base_profile_embed(player_data)
        if embed.title == "❌ Erro":
            return embed
        embed.title = f"Registro e Boosts de {self.user.display_name}"

        record_boosts_value = (
            f"{CUSTOM_EMOJIS.get('kills_icon', '⚔️')} **Abates:** **{player_data.get('kills', 0)}**\n"
            f"{CUSTOM_EMOJIS.get('deaths_icon', '☠️')} **Mortes:** **{player_data.get('deaths', 0)}**\n"
            f"{CUSTOM_EMOJIS.get('bounty_icon', '🏴‍☠️')} **Recompensa:** **${player_data.get('bounty', 0):,}**\n"
            f"\n**__Aprimoramentos Ativos__**\n"
            f"{CUSTOM_EMOJIS.get('xp_boost_icon', '🚀')} **XP Triplo:** `{'✅ Ativo' if player_data.get('xptriple') else '❌ Inativo'}`\n"
            f"{CUSTOM_EMOJIS.get('money_boost_icon', '💸')} **Dinheiro Duplo:** `{'✅ Ativo' if player_data.get('money_double') else '❌ Inativo'}`"
        )
        embed.add_field(name="🏆 Sua Jornada", value=record_boosts_value, inline=False)
        return embed

    def create_inventory_embed(self) -> discord.Embed:
        """
        Cria o embed do inventário do jogador, com design responsivo e espaçamento.
        """
        player_data = get_player_data(self.user.id)
        if not player_data:
            return Embed(
                title="❌ Erro",
                description="Dados do jogador não encontrados.",
                color=Color.red(),
            )

        embed = self._get_base_profile_embed(player_data)
        if embed.title == "❌ Erro":
            return embed
        embed.title = f"Inventário de {self.user.display_name}"

        inventory_items = player_data.get("inventory", {})
        if not inventory_items:
            embed.description = (
                f"{CUSTOM_EMOJIS.get('empty_bag_icon', '🎒')} *Parece que sua mochila está vazia, Fora-da-Lei! "
                f"Aventure-se e encontre novos tesouros!*"
            )
        else:
            item_list = []
            for item_id, amount in inventory_items.items():
                item_data = ITEMS_DATA.get(item_id, {})
                emoji = item_data.get("emoji", "❔")
                name = item_data.get("name", item_id.replace("_", " ").title())
                if amount > 0:
                    item_list.append(f"{emoji} **{name}** `x{amount}`")

            if not item_list:
                embed.description = (
                    f"{CUSTOM_EMOJIS.get('empty_bag_icon', '🎒')} *Parece que sua mochila está vazia, Fora-da-Lei! "
                    f"Aventure-se e encontre novos tesouros!*"
                )
            else:
                embed.description = "\n\n".join(item_list)

        return embed

    # --- Botões ---

    @ui.button(label="Perfil", style=ButtonStyle.primary, emoji="👤", disabled=True)
    async def profile_button(self, interaction: Interaction, button: ui.Button):
        self._disable_all_buttons_except(button)
        await self.original_interaction.edit_original_response(
            embed=self.create_profile_embed(), view=self
        )
        await interaction.response.defer()

    @ui.button(label="Inventário", style=ButtonStyle.secondary, emoji="🎒")
    async def inventory_button(self, interaction: Interaction, button: ui.Button):
        self._disable_all_buttons_except(button)
        await self.original_interaction.edit_original_response(
            embed=self.create_inventory_embed(), view=self
        )
        await interaction.response.defer()

    @ui.button(label="Recursos", style=ButtonStyle.secondary, emoji="⚡")
    async def resources_button(self, interaction: Interaction, button: ui.Button):
        self._disable_all_buttons_except(button)
        await self.original_interaction.edit_original_response(
            embed=self.create_resources_embed(), view=self
        )
        await interaction.response.defer()

    @ui.button(label="Registro & Boosts", style=ButtonStyle.secondary, emoji="🏆")
    async def record_boosts_button(self, interaction: Interaction, button: ui.Button):
        self._disable_all_buttons_except(button)
        await self.original_interaction.edit_original_response(
            embed=self.create_record_boosts_embed(), view=self
        )
        await interaction.response.defer()

    def _disable_all_buttons_except(self, current_button: ui.Button):
        """Ajuda a desativar todos os botões na view, exceto o clicado."""
        for item in self.children:
            if isinstance(item, ui.Button):
                item.disabled = item == current_button
