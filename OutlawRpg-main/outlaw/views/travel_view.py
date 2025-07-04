import discord
from discord import ui, ButtonStyle, Interaction, Embed, Color

from data_manager import get_player_data, save_data
from config import WORLD_MAP


class TravelView(ui.View):
    def __init__(self, current_location_id: str, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        current_location_info = WORLD_MAP.get(current_location_id, {})
        connected_locations_ids = current_location_info.get("conecta", [])

        # Populate buttons for connected locations
        for dest_id in connected_locations_ids:
            dest_info = WORLD_MAP.get(dest_id, {})
            if dest_info:  # Ensure the destination actually exists in WORLD_MAP
                label = dest_info.get("name", dest_id.replace("_", " ").title())
                emoji = dest_info.get("emoji", "❓")
                self.add_item(
                    TravelButton(
                        label=label,
                        emoji=emoji,
                        destination_id=dest_id,  # Pass the actual internal ID to the button
                    )
                )


class TravelButton(ui.Button):
    def __init__(self, label: str, emoji: str, destination_id: str):
        super().__init__(label=label, style=ButtonStyle.secondary, emoji=emoji)
        self.destination_id = destination_id

    async def callback(self, i: Interaction):
        # Sempre adie a interação primeiro. Use ephemeral=True se a resposta for apenas para o usuário que clicou.
        await i.response.defer(ephemeral=True)  # <--- ALTERAÇÃO AQUI: Adiciona defer

        player_data = get_player_data(self.view.user_id)
        if not player_data:
            # Use followup.send após deferir, para enviar uma nova mensagem.
            await i.followup.send(  # <--- ALTERAÇÃO AQUI: Usa followup.send
                "Erro ao encontrar sua ficha.", ephemeral=True
            )
            return

        # Double check if the destination is valid (should be caught by button creation, but good for safety)
        if self.destination_id not in WORLD_MAP:
            # Use followup.send após deferir.
            await i.followup.send(  # <--- ALTERAÇÃO AQUI: Usa followup.send
                f"Destino '{self.label}' inválido ou não existe no mapa.",
                ephemeral=True,
            )
            return

        destination_info = WORLD_MAP.get(self.destination_id, {})
        required_boss_id = destination_info.get("required_previous_boss")

        if required_boss_id:
            player_boss_data = player_data.get("boss_data", {})
            defeated_bosses = player_boss_data.get("defeated_bosses", [])
            if required_boss_id not in defeated_bosses:
                # Use followup.send após deferir.
                await i.followup.send(  # <--- ALTERAÇÃO AQUI: Usa followup.send
                    f"Você não pode viajar para **{self.label}** ainda! Você precisa derrotar o **{required_boss_id}** primeiro.",
                    ephemeral=True,
                )
                return

        player_data["location"] = self.destination_id
        save_data()

        # Use edit_original_response para editar a mensagem que continha o botão.
        await i.edit_original_response(  # <--- ALTERAÇÃO AQUI: Usa edit_original_response
            embed=Embed(
                title=f"✈️ Viagem Concluída",
                description=f"Você viajou e chegou em **{self.label}**.",
                color=Color.blue(),
            ),
            view=None,  # Remove buttons after travel
        )
        self.view.stop()  # Stop the view to disable other buttons
