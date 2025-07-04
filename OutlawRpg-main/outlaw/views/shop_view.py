import discord
from discord import ui, ButtonStyle, Interaction, Embed, Color

from data_manager import get_player_data, save_data
from config import ITEMS_DATA, BOSSES_DATA  # Import BOSSES_DATA for invoker info


class ShopView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)

        general_items_list = []
        invoker_items_list = []

        for item_id, item_info in ITEMS_DATA.items():
            if item_info.get("price") is not None:
                if item_info.get("type") == "summon_boss":
                    invoker_items_list.append((item_id, item_info))
                else:
                    general_items_list.append((item_id, item_info))

        # Add buttons for general items
        current_row = 0
        for item_id, item_info in general_items_list:
            label = item_info.get("name", item_id.replace("_", " ").title())
            emoji = item_info.get("emoji", "💰")

            # Special label for unlockable blessings
            if item_info.get("type") == "blessing_unlock":
                label = f"Desbloquear {label}"

            self.add_item(
                self.BuyButton(
                    item_id=item_id,
                    price=item_info["price"],
                    label=label,
                    emoji=emoji,
                    row=current_row,  # Keep on same row until it fills up
                )
            )
            # You might want to dynamically increase row here, but for simplicity, let discord handle wrapping

        # Add buttons for invoker items on a new row (or after general items)
        # Assuming we want invoker buttons on row 1, if general items were on row 0.
        # This assumes general_items_list does not fill more than 5 buttons on row 0
        # If it does, you'll need to dynamically manage row numbers.
        invoker_row_start = (
            len(general_items_list) // 5
        ) + 1  # Calculates starting row for invokers

        for item_id, item_info in invoker_items_list:
            label = item_info.get("name", item_id.replace("_", " ").title())
            emoji = item_info.get("emoji", "🔮")
            price = item_info["price"]  # Use price from ITEMS_DATA for display

            self.add_item(
                self.BuyButton(
                    item_id=item_id,
                    price=price,
                    label=label,
                    emoji=emoji,
                    row=invoker_row_start,
                )
            )
            # Again, assuming invoker_items_list does not fill more than 5 buttons per row
            # If it does, you'll need dynamic row management.

    class BuyButton(ui.Button):
        def __init__(self, item_id: str, price: int, label: str, emoji: str, row: int):
            super().__init__(
                label=f"{label} (${price})",
                style=ButtonStyle.primary,
                emoji=emoji,
                row=row,
            )
            self.item_id, self.price = item_id, price

        async def callback(self, i: Interaction):
            player_data = get_player_data(i.user.id)
            if not player_data:
                await i.response.send_message(
                    "Crie uma ficha primeiro!", ephemeral=True
                )
                return

            item_info = ITEMS_DATA.get(self.item_id)
            if not item_info:
                await i.response.send_message(
                    "Este item não é reconhecido.", ephemeral=True
                )
                return

            if (
                item_info.get("class_restriction")
                and player_data["class"] != item_info["class_restriction"]
            ):
                await i.response.send_message(
                    f"Este item é exclusivo para a classe **{item_info['class_restriction']}**!",
                    ephemeral=True,
                )
                return
            if (
                item_info.get("style_restriction")
                and player_data["style"] != item_info["style_restriction"]
            ):
                await i.response.send_message(
                    f"Este item é exclusivo para o estilo **{item_info['style_restriction']}**!",
                    ephemeral=True,
                )
                return

            if player_data["money"] < self.price:
                await i.response.send_message("Dinheiro insuficiente!", ephemeral=True)
                return

            # Check specific conditions for Summon Boss items
            if item_info.get("type") == "summon_boss":
                boss_id_to_summon = item_info.get("boss_id_to_summon")
                boss_info = BOSSES_DATA.get(boss_id_to_summon)

                if not boss_info:
                    await i.response.send_message(
                        "Erro: Dados do chefe para este invocador não encontrados.",
                        ephemeral=True,
                    )
                    return

                # Check player level requirement to BUY THE INVOKER
                if player_data["level"] < boss_info.get("required_level", 1):
                    await i.response.send_message(
                        f"Você precisa ser Nível {boss_info.get('required_level', 1)} para comprar este invocador.",
                        ephemeral=True,
                    )
                    return

                # Check progression: Player can only buy invoker for their current progression boss OR for bosses they already defeated
                player_progression_boss = player_data["boss_data"].get(
                    "boss_progression_level"
                )
                player_defeated_bosses = player_data["boss_data"].get(
                    "defeated_bosses", []
                )

                if (
                    boss_id_to_summon != player_progression_boss
                    and boss_id_to_summon not in player_defeated_bosses
                ):
                    await i.response.send_message(
                        f"Este invocador ainda não está disponível para você progredir. Você precisa derrotar o **{player_progression_boss}** para desbloquear o próximo, ou este é um boss que você ainda não derrotou.",
                        ephemeral=True,
                    )
                    return

            # Prevent buying multiple unique permanent items (e.g., amulets, equipables, blessings)
            if item_info.get("consumable") == False:  # Only applies to non-consumables
                if player_data["inventory"].get(self.item_id, 0) > 0:
                    await i.response.send_message(
                        f"Você já possui o(a) **{ITEMS_DATA[self.item_id]['name']}**!",
                        ephemeral=True,
                    )
                    return

            player_data["money"] -= self.price
            player_data["inventory"][self.item_id] = (
                player_data["inventory"].get(self.item_id, 0) + 1
            )

            # Apply HP bonuses/penalties on purchase (for equipable items)
            if item_info.get("type") == "equipable":
                if self.item_id == "manopla_lutador":
                    hp_gain_from_item = ITEMS_DATA["manopla_lutador"].get(
                        "hp_bonus_flat", 0
                    )
                    player_data["max_hp"] += hp_gain_from_item
                    player_data["hp"] = min(
                        player_data["hp"] + hp_gain_from_item, player_data["max_hp"]
                    )
                elif self.item_id == "espada_fantasma":
                    hp_penalty_percent = ITEMS_DATA["espada_fantasma"].get(
                        "hp_penalty_percent", 0.0
                    )
                    player_data["max_hp"] = max(
                        1, int(player_data["max_hp"] * (1 - hp_penalty_percent))
                    )
                    player_data["hp"] = min(player_data["hp"], player_data["max_hp"])

            save_data()
            await i.response.send_message(
                f"**{i.user.display_name}** comprou 1x {ITEMS_DATA[self.item_id]['name']}!"
            )
