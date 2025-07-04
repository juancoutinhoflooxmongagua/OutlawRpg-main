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
        player_data = get_player_data(self.view.user_id)
        if not player_data:
            await i.response.send_message(
                "Erro ao encontrar sua ficha.", ephemeral=True
            )
            return

        # Double check if the destination is valid (should be caught by button creation, but good for safety)
        if self.destination_id not in WORLD_MAP:
            await i.response.send_message(
                f"Destino '{self.label}' inválido ou não existe no mapa.",
                ephemeral=True,
            )
            return

        player_data["location"] = self.destination_id
        save_data()
        await i.response.edit_message(
            embed=Embed(
                title=f"✈️ Viagem Concluída",
                description=f"Você viajou e chegou em **{self.label}**.",
                color=Color.blue(),
            ),
            view=None,  # Remove buttons after travel
        )
        self.view.stop()  # Stop the view to disable other buttons
