import discord
from discord.ui import View, Button
from discord import Interaction, Embed, Color
from data_manager import get_player_data, save_data, player_database, current_boss_data
from config import WORLD_MAP, BOSSES_DATA, ITEMS_DATA
from utils import calculate_effective_stats
import asyncio


class TravelButton(Button):
    def __init__(self, location_id: str, location_name: str, row: int):
        super().__init__(
            label=location_name,
            style=discord.ButtonStyle.secondary,
            custom_id=f"travel_to_{location_id}",
            row=row,
            disabled=False,  # Set to False initially, then disable if conditions aren't met
        )
        self.location_id = location_id
        self.location_name = location_name

    async def callback(self, i: Interaction):
        # SEMPRE busque os dados mais recentes do jogador aqui
        player_data = get_player_data(i.user.id)

        if not player_data:
            await i.response.send_message(
                "Você não tem uma ficha de personagem! Use `/criar_ficha` para começar.",
                ephemeral=True,
            )
            return

        if player_data.get("status") == "dead":
            await i.response.send_message(
                "Você não pode viajar enquanto estiver morto.", ephemeral=True
            )
            return

        location_info = WORLD_MAP.get(self.location_id)
        if not location_info:
            await i.response.send_message(
                "Erro: Localização desconhecida.", ephemeral=True
            )
            return

        # Verifica o requisito de boss
        required_boss_id = location_info.get("required_previous_boss")
        if required_boss_id:
            player_defeated_bosses = player_data.get("boss_data", {}).get(
                "defeated_bosses", []
            )
            if required_boss_id not in player_defeated_bosses:
                boss_name = BOSSES_DATA.get(required_boss_id, {}).get(
                    "name", "boss necessário"
                )
                await i.response.send_message(
                    f"Você não pode viajar para {self.location_name} ainda! Você precisa derrotar o {boss_name} primeiro.",
                    ephemeral=True,
                )
                return

        # Verifica o requisito de item
        required_item = location_info.get("required_item")
        if required_item:
            item_name = ITEMS_DATA.get(required_item, {}).get("name", "item necessário")
            if player_data.get("inventory", {}).get(required_item, 0) < 1:
                await i.response.send_message(
                    f"Você não pode viajar para {self.location_name} ainda! Você precisa de 1x {item_name}.",
                    ephemeral=True,
                )
                return

        # Verifica o requisito de nível
        required_level = location_info.get("required_level")
        if required_level and player_data.get("level", 1) < required_level:
            await i.response.send_message(
                f"Você não pode viajar para {self.location_name} ainda! Você precisa ser Nível {required_level}.",
                ephemeral=True,
            )
            return

        player_data["location"] = self.location_id
        save_data()

        embed = Embed(
            title="🗺️ Viagem Concluída!",
            description=f"Você viajou para **{self.location_name}**.",
            color=Color.blue(),
        )
        embed.set_thumbnail(
            url=location_info.get("thumb", "https://i.imgur.com/example.png")
        )

        # Atualiza a mensagem original para refletir a nova localização
        if i.message:
            await i.message.edit(embed=embed, view=None)  # Remove a view após a viagem
        else:
            await i.response.send_message(embed=embed)


class TravelView(View):
    def __init__(self, current_location_id: str, user_id: int):
        super().__init__(timeout=180)
        self.current_location_id = current_location_id
        self.user_id = user_id
        self.add_travel_buttons()

    def add_travel_buttons(self):
        # Busca os dados do jogador uma vez para o estado inicial dos botões
        # CORRIGIDO: Use self.user_id, não self.user.id
        player_data = get_player_data(self.user_id)

        row_counter = 0
        for loc_id, loc_info in WORLD_MAP.items():
            if loc_id == self.current_location_id:
                continue  # Não mostra o botão para viajar para a localização atual

            button = TravelButton(loc_id, loc_info["name"], row=row_counter // 2)
            row_counter += 1

            # Desabilita o botão se os requisitos não forem atendidos
            is_disabled = False

            # Verifica o requisito de boss
            required_boss_id = loc_info.get("required_previous_boss")
            if required_boss_id:
                player_defeated_bosses = player_data.get("boss_data", {}).get(
                    "defeated_bosses", []
                )
                if required_boss_id not in player_defeated_bosses:
                    is_disabled = True

            # Verifica o requisito de item
            required_item = loc_info.get("required_item")
            if required_item:
                if player_data.get("inventory", {}).get(required_item, 0) < 1:
                    is_disabled = True

            # Verifica o requisito de nível
            required_level = loc_info.get("required_level")
            if required_level and player_data.get("level", 1) < required_level:
                is_disabled = True

            button.disabled = is_disabled
            self.add_item(button)

    async def on_timeout(self):
        # Remove os botões quando a view expira
        if self.message:
            await self.message.edit(view=None)
