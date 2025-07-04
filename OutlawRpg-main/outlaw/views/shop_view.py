import discord
from discord import ui, ButtonStyle, Interaction, Embed, Color

from data_manager import get_player_data, save_data
from config import ITEMS_DATA, BOSSES_DATA


class ShopView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.current_category = None  # To keep track of the active category

        # Categorize items
        self.potions_items = []
        self.general_items = []
        self.invoker_items = []

        for item_id, item_info in ITEMS_DATA.items():
            if item_info.get("price") is not None:  # Only show purchasable items
                item_type = item_info.get("type")
                item_subtype = item_info.get("subtype")  # Get the subtype

                if item_type == "consumable" and item_subtype == "potion":
                    self.potions_items.append((item_id, item_info))
                elif item_type == "summon_boss":
                    self.invoker_items.append((item_id, item_info))
                else:  # All other items: general consumables (non-potions), equipables, blessing unlocks, etc.
                    self.general_items.append((item_id, item_info))

        self._add_category_buttons()

    def _add_category_buttons(self):
        """Adds buttons for category selection."""
        self.clear_items()
        self.add_item(self.CategoryButton("Itens", "general", row=0))
        self.add_item(self.CategoryButton("Invocadores", "invokers", row=0))

    def _add_item_buttons(self, items_list):
        """Adds specific item buttons to the view, handling row placement."""
        self.clear_items()  # Clear previous buttons

        current_row = 0
        buttons_in_current_row = 0

        for item_id, item_info in items_list:
            label = item_info.get("name", item_id.replace("_", " ").title())
            emoji = item_info.get("emoji", "💰")

            if item_info.get("type") == "blessing_unlock":
                label = f"Desbloquear {label}"

            self.add_item(
                self.BuyButton(
                    item_id=item_id,
                    price=item_info["price"],
                    label=label,
                    emoji=emoji,
                    row=current_row,
                )
            )
            buttons_in_current_row += 1
            if buttons_in_current_row == 5:
                current_row += 1
                buttons_in_current_row = 0

        # Add a "Voltar" (Back) button at the end
        self.add_item(self.BackButton(row=current_row + 1))

    class CategoryButton(ui.Button):
        def __init__(self, label: str, category_key: str, row: int):
            super().__init__(label=label, style=ButtonStyle.secondary, row=row)
            self.category_key = category_key

        async def callback(self, i: Interaction):
            view: ShopView = self.view  # Get the parent view instance
            view.current_category = self.category_key

            if self.category_key == "potions":
                view._add_item_buttons(view.potions_items)
            elif self.category_key == "general":
                view._add_item_buttons(view.general_items)
            elif self.category_key == "invokers":
                view._add_item_buttons(view.invoker_items)

            await i.response.edit_message(view=view)

    class BackButton(ui.Button):
        def __init__(self, row: int):
            super().__init__(
                label="Voltar", style=ButtonStyle.danger, emoji="🔙", row=row
            )

        async def callback(self, i: Interaction):
            view: ShopView = self.view
            view._add_category_buttons()  # Go back to category selection
            view.current_category = None
            await i.response.edit_message(view=view)

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

            if item_info.get("type") == "summon_boss":
                boss_id_to_summon = item_info.get("boss_id_to_summon")
                boss_info = BOSSES_DATA.get(boss_id_to_summon)

                if not boss_info:
                    await i.response.send_message(
                        "Erro: Dados do chefe para este invocador não encontrados.",
                        ephemeral=True,
                    )
                    return

                if player_data["level"] < boss_info.get("required_level", 1):
                    await i.response.send_message(
                        f"Você precisa ser Nível {boss_info.get('required_level', 1)} para comprar este invocador.",
                        ephemeral=True,
                    )
                    return

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

            if item_info.get("consumable") == False:
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
            # After purchase, re-display the items in the current category
            view: ShopView = self.view
            if view.current_category == "potions":
                view._add_item_buttons(view.potions_items)
            elif view.current_category == "general":
                view._add_item_buttons(view.general_items)
            elif view.current_category == "invokers":
                view._add_item_buttons(view.invoker_items)
            await i.message.edit(view=view)
