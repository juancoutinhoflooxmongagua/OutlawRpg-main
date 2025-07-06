import discord
from discord import ui, Interaction, Embed, Color
from ..config import ITEMS_DATA, CLASS_TRANSFORMATIONS, CUSTOM_EMOJIS


class HelpView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @ui.select(
        placeholder="Escolha uma categoria da Wiki...",
        options=[
            discord.SelectOption(label="Introdução", emoji="📜", value="Introdução"),
            discord.SelectOption(
                label="Comandos Gerais", emoji="👤", value="Comandos Gerais"
            ),
            discord.SelectOption(
                label="Comandos de Ação", emoji="⚔️", value="Comandos de Ação"
            ),
            discord.SelectOption(
                label="Sistema de Classes", emoji="🛡️", value="Sistema de Classes"
            ),
            discord.SelectOption(
                label="Sistema de Combate", emoji="💥", value="Sistema de Combate"
            ),
            discord.SelectOption(
                label="Itens Especiais", emoji="💎", value="Itens Especiais"
            ),
        ],
    )
    async def select_callback(self, i: Interaction, s: ui.Select):
        topic = s.values[0]
        embed = Embed(title=f"📜 Wiki OUTLAWS - {topic}", color=Color.blurple())
        if topic == "Introdução":
            embed.description = "Bem-vindo a OUTLAWS, um mundo impiedoso onde apenas os mais fortes sobrevivem..."
        elif topic == "Comandos Gerais":
            embed.add_field(name="/perfil", value="Mostra seu perfil.", inline=False)
            embed.add_field(
                name="/distribuir_pontos", value="Melhora atributos.", inline=False
            )
            embed.add_field(name="/reviver", value="Volta à vida.", inline=False)
            embed.add_field(
                name="/ranking", value="Mostra os mais mortais.", inline=False
            )
            embed.add_field(
                name="/afk | /voltar", value="Entra/sai do modo Ausente.", inline=False
            )
        elif topic == "Comandos de Ação":
            embed.add_field(
                name="/cacar | /batalhar",
                value="Inicia um combate por turnos.",
                inline=False,
            )
            embed.add_field(name="/atacar", value="Ataca outro jogador.", inline=False)
            embed.add_field(
                name="/trabalhar", value="Ganha dinheiro e XP.", inline=False
            )
            embed.add_field(name="/viajar", value="Move-se pelo mundo.", inline=False)
            embed.add_field(
                name="/loja | /aprimorar", value="Disponíveis em cidades.", inline=False
            )
            embed.add_field(
                name="/usar [item]", value="Usa um item do inventário.", inline=False
            )
            embed.add_field(
                name="/curar [alvo]",
                value="[Curandeiro] Cura um aliado ou a si mesmo.",
                inline=False,
            )
            embed.add_field(
                name="/transformar [forma]",
                value="Ativa uma transformação de classe/estilo (ex: Lâmina Fantasma, Lorde Sanguinário, Bênção de Drácula, Lâmina Abençoada).",
                inline=False,
            )
            embed.add_field(
                name="/destransformar [forma]",
                value="Desativa uma transformação específica.",
                inline=False,
            )
            embed.add_field(
                name="/ativar_bencao_aura",
                value="[Aura] Ativa diretamente a Benção do Rei Henrique.",
                inline=False,
            )
        elif topic == "Sistema de Classes":
            class_descriptions = []
            for class_name, transforms in CLASS_TRANSFORMATIONS.items():
                transform_details = []
                for t_name, t_info in transforms.items():
                    transform_details.append(f"{t_info.get('emoji', '')} **{t_name}**")
                class_descriptions.append(
                    f"**{class_name}**: Pode se transformar em {', '.join(transform_details)}."
                )
            embed.description = (
                "Aqui estão as classes e suas transformações:\n"
                + "\n".join(class_descriptions)
            )
            # Specific note for Vampiro with Dracula Blessing (as it's often confused as a "transformation" of the class itself)
            if "Vampiro" in CLASS_TRANSFORMATIONS:
                embed.description += f"\n\nAlém disso, **Vampiros** podem ativar a {ITEMS_DATA.get('bencao_dracula', {}).get('emoji', '🦇')} **Bênção de Drácula** para desviar e sugar HP!"

        elif topic == "Sistema de Combate":
            # Removido: A menção a atacar_boss
            embed.description = "Batalhas são por turnos. Acertos Críticos (10% de chance) causam 50% a mais de dano!"
        elif topic == "Itens Especiais":
            potion_info = ITEMS_DATA.get("pocao", {})
            super_potion_info = ITEMS_DATA.get("super_pocao", {})
            amulet_info = ITEMS_DATA.get("amuleto_de_pedra", {})
            healer_staff_info = ITEMS_DATA.get("cajado_curandeiro", {})
            fighter_gauntlet_info = ITEMS_DATA.get("manopla_lutador", {})
            shooter_sight_info = ITEMS_DATA.get("mira_semi_automatica", {})
            ghost_sword_info = ITEMS_DATA.get("espada_fantasma", {})
            dracula_blessing_info = ITEMS_DATA.get("bencao_dracula", {})
            king_henry_blessing_info = ITEMS_DATA.get("bencao_rei_henrique", {})

            embed.add_field(
                name=f"{potion_info.get('emoji', '❔')} {potion_info.get('name', 'Poção de Vida')} & {super_potion_info.get('emoji', '❔')} {super_potion_info.get('name', 'Super Poção')}",
                value=f"Restaura HP. Poção: {potion_info.get('heal', 0)}HP, Super Poção: {super_potion_info.get('heal', 0)}HP.",
                inline=False,
            )
            embed.add_field(
                name=f"{amulet_info.get('emoji', '❔')} {amulet_info.get('name', 'Amuleto de Pedra')}",
                value="Item raro que concede uma segunda chance em combate, salvando-o da morte iminente uma vez por batalha. Este item é **permanente** e não é consumido.",
                inline=False,
            )
            embed.add_field(
                name="Equipamentos de Classe",
                value=(
                    f"Itens poderosos que fornecem bônus passivos para classes específicas quando no inventário. "
                    f"Ex: **{healer_staff_info.get('emoji', '❔')} {healer_staff_info.get('name', 'Cajado do Curandeiro')}** (Curandeiro) aumenta cura em {int(healer_staff_info.get('effect_multiplier', 1.0) * 100 - 100)}%, "
                    f"**{fighter_gauntlet_info.get('emoji', '❔')} {fighter_gauntlet_info.get('name', 'Manopla do Lutador')}** (Lutador) aumenta ataque base em {int(fighter_gauntlet_info.get('attack_bonus_percent', 0.0) * 100)}% e vida máxima em {fighter_gauntlet_info.get('hp_bonus_flat', 0)}, "
                    f"**{shooter_sight_info.get('emoji', '❔')} {shooter_sight_info.get('name', 'Mira Semi-Automática')}** (Atirador) reduz cooldown de ataque especial em {int(shooter_sight_info.get('cooldown_reduction_percent', 0.0) * 100)}%, "
                    f"**{ghost_sword_info.get('emoji', '❔')} {ghost_sword_info.get('name', 'Espada Fantasma')}** (Espadachim) concede +{int(ghost_sword_info.get('attack_bonus_percent', 0.0) * 100)}% de ataque, mas penaliza -{int(ghost_sword_info.get('hp_penalty_percent', 0.0) * 100)}% do HP total."
                ),
                inline=False,
            )
            embed.add_field(
                name=f"{dracula_blessing_info.get('emoji', '❔')} {dracula_blessing_info.get('name', 'Bênção de Drácula')}",
                value=(
                    f"[Vampiro] Ativa uma bênção que concede {int(dracula_blessing_info.get('evasion_chance', 0.0) * 100)}% de chance de desviar de ataques inimigos e roubar {int(dracula_blessing_info.get('hp_steal_percent_on_evade', 0.0) * 100)}% do HP que seria o dano. "
                    f"Custa {dracula_blessing_info.get('cost_energy', 0)} energia e dura {dracula_blessing_info.get('duration_seconds', 0) // 60} minutos. (Desbloqueável na loja)"
                ),
                inline=False,
            )
            embed.add_field(
                name=f"{king_henry_blessing_info.get('emoji', '❔')} {king_henry_blessing_info.get('name', 'Benção do Rei Henrique')}",
                value=(
                    f"[Aura] Ativa uma bênção poderosa com +{int(king_henry_blessing_info.get('attack_multiplier', 1.0) * 100 - 100)}% ATQ/ATQ Especial/HP e -{int(king_henry_blessing_info.get('cooldown_reduction_percent', 0.0) * 100)}% nos cooldowns. "
                    f"Custa {king_henry_blessing_info.get('cost_energy', 0)} energia e dura {king_henry_blessing_info.get('duration_seconds', 0) // 60} minutos. (Desbloqueável na loja)"
                ),
                inline=False,
            )
        await i.response.edit_message(embed=embed)
