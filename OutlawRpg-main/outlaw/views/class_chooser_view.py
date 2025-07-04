import discord
from discord.ext import commands
from discord import ui, ButtonStyle, Interaction, Embed, Color

from data_manager import player_database, save_data
from config import (
    INITIAL_HP,
    INITIAL_ATTACK,
    INITIAL_SPECIAL_ATTACK,
    INITIAL_MONEY,
    MAX_ENERGY,
    STARTING_LOCATION,
    NEW_CHARACTER_ROLE_ID,
)


class ClassChooserView(ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=180)
        self.bot = bot
        self.chosen_class = None
        self.chosen_style = None

    @ui.select(
        placeholder="Escolha sua Classe...",
        options=[
            discord.SelectOption(label="Espadachim", emoji="⚔️"),
            discord.SelectOption(label="Lutador", emoji="🥊"),
            discord.SelectOption(label="Atirador", emoji="🏹"),
            discord.SelectOption(label="Curandeiro", emoji="🩹"),
            discord.SelectOption(label="Vampiro", emoji="🧛"),
            discord.SelectOption(
                label="Domador", emoji="🐺"
            ),  # <--- ADICIONE ESTA LINHA
            discord.SelectOption(
                label="Corpo Seco", emoji="💀"
            ),  # <--- ADICIONE ESTA LINHA
        ],
    )
    async def class_select(self, i: Interaction, s: ui.Select):
        self.chosen_class = s.values[0]
        await i.response.send_message(
            f"Classe: **{self.chosen_class}**. Agora, a fonte de poder.", ephemeral=True
        )

    @ui.select(
        placeholder="Escolha sua Fonte de Poder...",
        options=[
            discord.SelectOption(label="Habilidade Inata", emoji="💪"),
            discord.SelectOption(label="Aura", emoji="✨"),
        ],
    )
    async def style_select(self, i: Interaction, s: ui.Select):
        self.chosen_style = s.values[0]
        await i.response.send_message(
            f"Fonte de Poder: **{self.chosen_style}**.", ephemeral=True
        )

    @ui.button(label="Confirmar Criação", style=ButtonStyle.success, row=2)
    async def confirm_button(self, i: Interaction, b: ui.Button):
        if not self.chosen_class or not self.chosen_style:
            await i.response.send_message(
                "Escolha uma classe e um estilo!", ephemeral=True
            )
            return
        user_id = str(i.user.id)
        if user_id in player_database:
            await i.response.send_message("Você já possui uma ficha!", ephemeral=True)
            return

        base_stats = {
            "hp": INITIAL_HP,
            "attack": INITIAL_ATTACK,
            "special_attack": INITIAL_SPECIAL_ATTACK,
        }

        if self.chosen_class == "Lutador":
            base_stats["hp"] += 20
            base_stats["attack"] += 5
        elif self.chosen_class == "Espadachim":
            base_stats["attack"] += 10
            base_stats["special_attack"] -= 5
        elif self.chosen_class == "Atirador":
            base_stats["hp"] -= 10
            base_stats["special_attack"] += 10
        elif self.chosen_class == "Curandeiro":
            base_stats["special_attack"] += 5
        elif self.chosen_class == "Vampiro":
            base_stats["hp"] += 30
            base_stats["attack"] += 8
            base_stats["special_attack"] += 15
        elif self.chosen_class == "Domador":
            base_stats["hp"] += 15  # HP base um pouco maior para o dono
            base_stats["attack"] += 7
            base_stats["special_attack"] += 7
            # O dano e HP do lobo serão calculados em `calculate_effective_stats`
        elif self.chosen_class == "Corpo Seco":
            base_stats["hp"] += 60  # HP significativamente maior
            base_stats["attack"] -= 5  # Dano base menor
            base_stats["special_attack"] -= 5  # Dano especial menor
            player_database[user_id] = {
                "name": i.user.display_name,
                "class": self.chosen_class,
                "style": self.chosen_style,
                "xp": 0,
                "level": 1,
                "money": INITIAL_MONEY,
                "hp": base_stats["hp"],
                "max_hp": base_stats["hp"],
                "base_attack": base_stats["attack"],
                "base_special_attack": base_stats["special_attack"],
                "inventory": {},
                "cooldowns": {},
                "status": "online",
                "bounty": 0,
                "kills": 0,
                "deaths": 0,
                "energy": MAX_ENERGY,
                "current_transformation": None,
                "transform_end_time": 0,
                "aura_blessing_active": False,
                "aura_blessing_end_time": 0,
                "bencao_dracula_active": False,
                "bencao_dracula_end_time": 0,
                "amulet_used_since_revive": False,
                "attribute_points": 0,
                "location": STARTING_LOCATION,
                "xptriple": False,
                "money_double": False,
            }

        guild = i.guild
        if guild:
            if isinstance(NEW_CHARACTER_ROLE_ID, int) and NEW_CHARACTER_ROLE_ID > 0:
                new_char_role = guild.get_role(NEW_CHARACTER_ROLE_ID)
                if new_char_role:
                    try:
                        await i.user.add_roles(new_char_role)
                        print(
                            f"Added role '{new_char_role.name}' to {i.user.display_name}"
                        )
                    except discord.Forbidden:
                        print(
                            f"Error: Bot lacks permissions to add role '{new_char_role.name}' to user {i.user.display_name}. Check bot permissions and role hierarchy."
                        )
                    except discord.HTTPException as e:
                        print(f"Error adding initial role: {e}")
                else:
                    print(
                        f"Initial character role with ID {NEW_CHARACTER_ROLE_ID} not found in guild."
                    )
            else:
                print(
                    "NEW_CHARACTER_ROLE_ID is not a valid role ID (must be a positive integer)."
                )

        save_data()
        embed = Embed(
            title=f"Ficha de {i.user.display_name} Criada!",
            description=f"Bem-vindo ao mundo de OUTLAWS, **{self.chosen_class}** que usa **{self.chosen_style}**!",
            color=Color.green(),
        )
        embed.set_thumbnail(
            url=i.user.avatar.url if i.user.avatar else discord.Embed.Empty
        )
        embed.set_footer(text="Use /perfil para ver seus status.")
        await i.response.edit_message(content=None, embed=embed, view=None)
        self.stop()
