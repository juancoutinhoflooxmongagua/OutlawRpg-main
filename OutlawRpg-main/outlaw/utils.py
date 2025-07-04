import discord
import random
import asyncio
from datetime import datetime
from discord import Interaction, Embed, Color

from config import (
    ITEMS_DATA,
    CLASS_TRANSFORMATIONS,
    BOSSES_DATA,
    XP_PER_LEVEL_BASE,
    ATTRIBUTE_POINTS_PER_LEVEL,
    CRITICAL_CHANCE,
    CRITICAL_MULTIPLIER,
    MAX_ENERGY,
    STARTING_LOCATION,
    LEVEL_ROLES,
    TRANSFORM_COST,
    CLAN_KILL_CONTRIBUTION_PERCENTAGE_XP,  # NEW
    CLAN_KILL_CONTRIBUTION_PERCENTAGE_MONEY,  # NEW
)

from data_manager import (
    save_data,
    get_player_data,
    clan_database,
    save_clan_data,
)  # NEW


def calculate_effective_stats(raw_player_data: dict) -> dict:
    """Calculates a player's effective stats based on their base stats, transformation, and inventory items.
    Does NOT modify the original raw_player_data.
    """
    effective_data = raw_player_data.copy()

    # Default values for bonuses/multipliers
    effective_data["attack_bonus_passive_percent"] = 0.0
    effective_data["healing_multiplier"] = 1.0
    effective_data["evasion_chance_bonus"] = 0.0
    effective_data["cooldown_reduction_percent"] = 0.0
    effective_data["xp_multiplier_passive"] = 0.0
    effective_data["money_multiplier_passive"] = 0.0

    # Apply passive bonuses from "Habilidade Inata" source of power (if active)
    habilidade_inata_info = ITEMS_DATA.get("habilidade_inata", {})
    if effective_data.get("style") == "Habilidade Inata":
        effective_data["attack_bonus_passive_percent"] += habilidade_inata_info.get(
            "attack_bonus_passive_percent", 0.0
        )
        effective_data["xp_multiplier_passive"] += habilidade_inata_info.get(
            "xp_multiplier_passive", 0.0
        )

    # Initialize current attack/special_attack/max_hp with base values
    effective_data["attack"] = raw_player_data["base_attack"]
    effective_data["special_attack"] = raw_player_data["base_special_attack"]
    effective_data["max_hp"] = raw_player_data["max_hp"]

    # Apply class transformations
    if effective_data.get("current_transformation"):
        transform_name = effective_data["current_transformation"]
        class_name = effective_data["class"]
        transform_info = CLASS_TRANSFORMATIONS.get(class_name, {}).get(transform_name)
        if transform_info:
            effective_data["attack"] = int(
                effective_data["attack"] * transform_info.get("attack_multiplier", 1.0)
            )
            effective_data["special_attack"] = int(
                effective_data["special_attack"]
                * transform_info.get("special_attack_multiplier", 1.0)
            )
            effective_data["max_hp"] = int(
                effective_data["max_hp"] * transform_info.get("hp_multiplier", 1.0)
            )
            effective_data["healing_multiplier"] *= transform_info.get(
                "healing_multiplier", 1.0
            )
            effective_data["evasion_chance_bonus"] += transform_info.get(
                "evasion_chance_bonus", 0.0
            )
            effective_data["cooldown_reduction_percent"] += transform_info.get(
                "cooldown_reduction_percent", 0.0
            )

    # Apply Aura-specific blessing (King Henry's Blessing) if active
    king_henry_blessing_info = ITEMS_DATA.get("bencao_rei_henrique", {})
    if effective_data.get("aura_blessing_active"):
        effective_data["attack"] = int(
            effective_data["attack"]
            * king_henry_blessing_info.get("attack_multiplier", 1.0)
        )
        effective_data["special_attack"] = int(
            effective_data["special_attack"]
            * king_henry_blessing_info.get("special_attack_multiplier", 1.0)
        )
        effective_data["max_hp"] = int(
            effective_data["max_hp"]
            * king_henry_blessing_info.get("max_hp_multiplier", 1.0)
        )
        effective_data["healing_multiplier"] *= king_henry_blessing_info.get(
            "healing_multiplier", 1.0
        )
        effective_data["cooldown_reduction_percent"] += king_henry_blessing_info.get(
            "cooldown_reduction_percent", 0.0
        )

    if effective_data["class"] == "Domador":
        effective_data["attack"] = int(
            effective_data["attack"] * 1.20
        )  # Ajustado de 1.35
        effective_data["special_attack"] = int(
            effective_data["special_attack"] * 1.20
        )  # Ajustado de 1.35
        effective_data["max_hp"] = int(
            effective_data["max_hp"] * 1.15
        )  # Ajustado de 1.25
        effective_data["hp"] = min(raw_player_data["hp"], effective_data["max_hp"])
    elif effective_data["class"] == "Corpo Seco":
        effective_data["max_hp"] = int(effective_data["max_hp"] * 1.50)
        effective_data["hp"] = min(raw_player_data["hp"], effective_data["max_hp"])
        effective_data["attack"] = int(effective_data["attack"] * 1.05)
        effective_data["special_attack"] = int(effective_data["special_attack"] * 1.05)
        effective_data["evasion_chance_bonus"] += 0.10

    # Apply item bonuses based on inventory (after transformations for proper stacking)
    inventory = effective_data.get("inventory", {})


def display_money(amount: int) -> str:
    """Formata um valor inteiro como uma string de moeda."""
    return f"${amount:,}"
    # Manopla do Lutador: Increases attack and HP
    manopla_lutador_info = ITEMS_DATA.get("manopla_lutador", {})
    if inventory.get("manopla_lutador", 0) > 0 and effective_data["class"] == "Lutador":
        effective_data["attack"] = int(
            effective_data["attack"]
            * (1 + manopla_lutador_info.get("attack_bonus_percent", 0.0))
        )
        effective_data["max_hp"] = int(
            effective_data["max_hp"] + manopla_lutador_info.get("hp_bonus_flat", 0)
        )

    # Espada Fantasma: Attack bonus and HP penalty
    espada_fantasma_info = ITEMS_DATA.get("espada_fantasma", {})
    if (
        inventory.get("espada_fantasma", 0) > 0
        and effective_data["class"] == "Espadachim"
    ):
        effective_data["attack"] = int(
            effective_data["attack"]
            * (1 + espada_fantasma_info.get("attack_bonus_percent", 0.0))
        )
        effective_data["max_hp"] = int(
            effective_data["max_hp"]
            * (1 - espada_fantasma_info.get("hp_penalty_percent", 0.0))
        )
        effective_data["hp"] = min(effective_data["hp"], effective_data["max_hp"])

    # Cajado do Curandeiro: Increases healing effectiveness
    cajado_curandeiro_info = ITEMS_DATA.get("cajado_curandeiro", {})
    if (
        inventory.get("cajado_curandeiro", 0) > 0
        and effective_data["class"] == "Curandeiro"
    ):
        effective_data["healing_multiplier"] *= cajado_curandeiro_info.get(
            "effect_multiplier", 1.0
        )

    # Mira Semi-Automática: Adds to total cooldown reduction for special attacks
    mira_semi_automatica_info = ITEMS_DATA.get("mira_semi_automatica", {})
    if (
        inventory.get("mira_semi_automatica", 0) > 0
        and effective_data["class"] == "Atirador"
    ):
        effective_data["cooldown_reduction_percent"] += mira_semi_automatica_info.get(
            "cooldown_reduction_percent", 0.0
        )

    # NOVO: Coleira do Lobo Alfa (Domador item)
    coleira_lobo_info = ITEMS_DATA.get("coleira_do_lobo", {})
    if inventory.get("coleira_do_lobo", 0) > 0 and effective_data["class"] == "Domador":
        effective_data["attack"] = int(
            effective_data["attack"]
            * (1 + coleira_lobo_info.get("attack_bonus_percent", 0.0))
        )
        effective_data["max_hp"] = int(
            effective_data["max_hp"] + coleira_lobo_info.get("hp_bonus_flat", 0)
        )

    # NOVO: Armadura de Osso Antigo (Corpo Seco item)
    armadura_osso_info = ITEMS_DATA.get("armadura_de_osso", {})
    if (
        inventory.get("armadura_de_osso", 0) > 0
        and effective_data["class"] == "Corpo Seco"
    ):
        effective_data["max_hp"] = int(
            effective_data["max_hp"] + armadura_osso_info.get("hp_bonus_flat", 0)
        )
        effective_data["cooldown_reduction_percent"] += armadura_osso_info.get(
            "cooldown_reduction_percent", 0.0
        )

    # NOVO: Coração do Universo (End-Game Item)
    coracao_universo_info = ITEMS_DATA.get("coracao_do_universo", {})
    if inventory.get("coracao_do_universo", 0) > 0:
        effective_data["attack"] = int(
            effective_data["attack"]
            * coracao_universo_info.get("attack_multiplier", 1.0)
        )
        effective_data["max_hp"] = int(
            effective_data["max_hp"]
            * coracao_universo_info.get("max_hp_multiplier", 1.0)
        )
        effective_data["xp_multiplier_passive"] += coracao_universo_info.get(
            "xp_multiplier_passive", 0.0
        )
        effective_data["money_multiplier_passive"] += coracao_universo_info.get(
            "money_multiplier_passive", 0.0
        )
        effective_data["cooldown_reduction_percent"] += coracao_universo_info.get(
            "cooldown_reduction_percent", 0.0
        )

    effective_data["attack"] = int(
        effective_data["attack"]
        * (1 + effective_data.get("attack_bonus_passive_percent", 0.0))
    )

    effective_data["hp"] = min(raw_player_data["hp"], effective_data["max_hp"])

    return effective_data


async def check_and_process_levelup_internal(
    bot_instance,
    member: discord.Member,
    player_data: dict,
    send_target: Interaction | discord.TextChannel,
):
    level = player_data.get("level", 1)
    xp_needed = int(XP_PER_LEVEL_BASE * (level**1.2))

    while player_data["xp"] >= xp_needed:
        player_data["level"] += 1
        player_data["xp"] -= xp_needed
        player_data["attribute_points"] = (
            player_data.get("attribute_points", 0) + ATTRIBUTE_POINTS_PER_LEVEL
        )
        player_data["max_hp"] += 10
        player_data["hp"] = player_data["max_hp"]

        embed = Embed(
            title="🌟 LEVEL UP! 🌟",
            description=f"Parabéns, {member.mention}! Você alcançou o **Nível {player_data['level']}**!",
            color=Color.gold(),
        )
        embed.set_thumbnail(
            url="https://media.tenor.com/drx1lO9cfEAAAAi/dark-souls-bonfire.gif"
        )
        embed.add_field(
            name="Recompensas",
            value=f"🔹 **{ATTRIBUTE_POINTS_PER_LEVEL}** Pontos de Atributo\n🔹 Vida totalmente restaurada!",
            inline=False,
        )
        embed.set_footer(text="Use /distribuir_pontos para ficar mais forte!")

        if isinstance(LEVEL_ROLES, dict):
            sorted_level_roles_keys = sorted(LEVEL_ROLES.keys(), reverse=True)

            current_role_to_assign = None
            for required_level in sorted_level_roles_keys:
                if player_data["level"] >= required_level:
                    current_role_to_assign = LEVEL_ROLES[required_level]
                    break

            guild_id_from_context = (
                send_target.guild_id
                if isinstance(send_target, Interaction)
                else send_target.guild.id
            )
            guild = bot_instance.get_guild(guild_id_from_context)

            if guild:
                member_obj = guild.get_member(member.id)
                if member_obj:
                    roles_to_remove = []
                    for level_key, role_id in LEVEL_ROLES.items():
                        role_to_remove = guild.get_role(role_id)
                        if role_to_remove and role_to_remove in member_obj.roles:
                            roles_to_remove.append(role_to_remove)

                    if roles_to_remove:
                        try:
                            await member_obj.remove_roles(
                                *roles_to_remove,
                                reason="Level up - updating level roles",
                            )
                        except discord.Forbidden:
                            print(
                                f"Erro: Bot sem permissão para remover cargos de nível para {member.display_name}."
                            )
                        except discord.HTTPException as e:
                            print(
                                f"Erro ao remover cargos de nível para {member.display_name}: {e}"
                            )

                    if current_role_to_assign:
                        role = guild.get_role(current_role_to_assign)
                        if role and role not in member_obj.roles:
                            try:
                                await member_obj.add_roles(
                                    role,
                                    reason=f"Reached Level {player_data['level']}",
                                )
                                embed.add_field(
                                    name="🎉 Novo Cargo Desbloqueado!",
                                    value=f"Você recebeu o cargo `{role.name}`!",
                                    inline=False,
                                )
                            except discord.Forbidden:
                                print(
                                    f"Erro: Bot não tem permissão para adicionar o cargo {role.name} ao usuário {member.display_name}. Verifique as permissões do bot e a hierarquia de cargos."
                                )
                            except discord.HTTPException as e:
                                print(
                                    f"Erro ao adicionar cargo para {member.display_name}: {e}"
                                )
                        elif not role:
                            print(
                                f"Aviso: Cargo com ID {current_role_to_assign} não encontrado na guilda {guild.name}."
                            )
                else:
                    print(
                        f"Aviso: Membro {member.display_name} não encontrado na guilda para atualizar cargos."
                    )
            else:
                print(
                    f"Aviso: Guilda com ID {guild_id_from_context} não encontrada para conceder cargo de nível."
                )

        if isinstance(send_target, Interaction):
            try:
                if send_target.response.is_done():
                    await send_target.followup.send(embed=embed)
                else:
                    await send_target.response.send_message(embed=embed)
            except discord.InteractionResponded:
                await send_target.channel.send(embed=embed)
            except Exception as e:
                print(f"Erro ao enviar embed de level up na interação: {e}")
        else:
            await send_target.send(embed=embed)

        xp_needed = int(XP_PER_LEVEL_BASE * (player_data["level"] ** 1.2))


# NEW: Function to calculate XP needed for the next level
def calculate_xp_for_next_level(level: int) -> int:
    return int(XP_PER_LEVEL_BASE * (level**1.2))


# NEW: Function to get effective XP gain with passive multipliers
def get_player_effective_xp_gain(player_data: dict, base_xp_gain: int) -> int:
    player_stats = calculate_effective_stats(
        player_data
    )  # Ensure passive multipliers are applied
    xp_multiplier_passive = player_stats.get("xp_multiplier_passive", 0.0)
    effective_xp_gain = int(base_xp_gain * (1 + xp_multiplier_passive))

    # Check for xptriple
    if player_data.get("xptriple") is True:
        effective_xp_gain *= 3
    return effective_xp_gain


async def run_turn_based_combat(
    bot_instance,
    interaction: Interaction,
    raw_player_data: dict,
    enemy: dict,
    initial_attack_style: str = "basico",
):
    log = []
    player_hp = raw_player_data["hp"]
    enemy_hp = enemy["hp"]
    amulet_activated_this_combat = False

    player_stats = calculate_effective_stats(raw_player_data)

    owner_display_hp = player_hp
    wolf_display_hp = 0
    owner_display_max_hp = player_stats["max_hp"]
    wolf_display_max_hp = 0
    player_hp_display_text = ""

    if raw_player_data["class"] == "Domador":
        owner_base_for_ratio = raw_player_data["max_hp"]
        wolf_base_for_ratio = int(raw_player_data["max_hp"] * 0.50)

        total_ratio_base = owner_base_for_ratio + wolf_base_for_ratio

        if total_ratio_base > 0:
            owner_ratio = owner_base_for_ratio / total_ratio_base

            owner_display_hp = int(player_hp * owner_ratio)
            wolf_display_hp = player_hp - owner_display_hp

            owner_display_max_hp = int(player_stats["max_hp"] * owner_ratio)
            wolf_display_max_hp = player_stats["max_hp"] - owner_display_max_hp
        else:
            owner_display_hp = player_hp
            owner_display_max_hp = player_stats["max_hp"]
            wolf_display_hp = 0
            wolf_display_max_hp = 0

        player_hp_display_text = (
            f"❤️ Você: {max(0, owner_display_hp)}/{owner_display_max_hp}\n"
            f"🐺 Lobo: {max(0, wolf_display_hp)}/{wolf_display_max_hp}"
        )
    else:
        player_hp_display_text = f"❤️ {player_hp}/{player_stats['max_hp']}"

    embed = Embed(title=f"⚔️ Batalha Iniciada! ⚔️", color=Color.orange())
    embed.set_thumbnail(url=enemy.get("thumb"))
    embed.add_field(
        name=interaction.user.display_name,
        value=player_hp_display_text,
        inline=True,
    )
    embed.add_field(
        name=enemy["name"], value=f"❤️ {enemy_hp}/{enemy['hp']}", inline=True
    )

    if not interaction.response.is_done():
        await interaction.response.defer()

    battle_message = await interaction.edit_original_response(embed=embed)

    turn = 1
    while player_hp > 0 and enemy_hp > 0:
        await asyncio.sleep(2.5)

        player_dmg = 0
        attack_type_name = ""
        crit_msg = ""
        owner_dmg_display = 0
        wolf_dmg_display = 0
        is_domador_attack = False

        cost_energy_special = TRANSFORM_COST
        cost_energy_special = max(
            1,
            int(
                cost_energy_special
                * (1 - player_stats.get("cooldown_reduction_percent", 0.0))
            ),
        )

        if raw_player_data["class"] == "Domador":
            is_domador_attack = True
            base_owner_attack = raw_player_data["base_attack"]
            base_wolf_attack = int(raw_player_data["base_attack"] * 0.50)

            base_owner_special_attack = raw_player_data["base_special_attack"]
            base_wolf_special_attack = int(
                raw_player_data["base_special_attack"] * 0.50
            )

        if turn == 1:
            if initial_attack_style == "basico":
                player_dmg = random.randint(
                    player_stats["attack"] // 2, player_stats["attack"]
                )
                attack_type_name = "Ataque Básico"

                if is_domador_attack:
                    total_base_attack_for_display = base_owner_attack + base_wolf_attack
                    if total_base_attack_for_display > 0:
                        owner_dmg_display = int(
                            player_dmg
                            * (base_owner_attack / total_base_attack_for_display)
                        )
                        wolf_dmg_display = player_dmg - owner_dmg_display
                    else:
                        owner_dmg_display = player_dmg
                        wolf_dmg_display = 0

            elif initial_attack_style == "especial":
                if raw_player_data["energy"] < cost_energy_special:
                    player_dmg = random.randint(
                        player_stats["attack"] // 2, player_stats["attack"]
                    )
                    attack_type_name = (
                        "Ataque Básico (Energia Insuficiente para Especial)"
                    )
                    log.append(
                        "⚠️ Energia insuficiente para Ataque Especial. Usando Ataque Básico."
                    )

                    if is_domador_attack:
                        total_base_attack_for_display = (
                            base_owner_attack + base_wolf_attack
                        )
                        if total_base_attack_for_display > 0:
                            owner_dmg_display = int(
                                player_dmg
                                * (base_owner_attack / total_base_attack_for_display)
                            )
                            wolf_dmg_display = player_dmg - owner_dmg_display
                        else:
                            owner_dmg_display = player_dmg
                            wolf_dmg_display = 0

                else:
                    player_dmg = random.randint(
                        int(player_stats["special_attack"] * 0.8),
                        int(player_stats["special_attack"] * 1.5),
                    )
                    attack_type_name = "Ataque Especial"
                    raw_player_data["energy"] = max(
                        0, raw_player_data["energy"] - cost_energy_special
                    )

                    if is_domador_attack:
                        total_base_special_attack_for_display = (
                            base_owner_special_attack + base_wolf_special_attack
                        )
                        if total_base_special_attack_for_display > 0:
                            owner_dmg_display = int(
                                player_dmg
                                * (
                                    base_owner_special_attack
                                    / total_base_special_attack_for_display
                                )
                            )
                            wolf_dmg_display = player_dmg - owner_dmg_display
                        else:
                            owner_dmg_display = player_dmg
                            wolf_dmg_display = 0

        else:
            player_dmg = random.randint(
                player_stats["attack"] // 2, player_stats["attack"]
            )
            attack_type_name = "Ataque Básico"

            if is_domador_attack:
                total_base_attack_for_display = base_owner_attack + base_wolf_attack
                if total_base_attack_for_display > 0:
                    owner_dmg_display = int(
                        player_dmg * (base_owner_attack / total_base_attack_for_display)
                    )
                    wolf_dmg_display = player_dmg - owner_dmg_display
                else:
                    owner_dmg_display = player_dmg
                    wolf_dmg_display = 0

        if random.random() < CRITICAL_CHANCE:
            player_dmg = int(player_dmg * CRITICAL_MULTIPLIER)
            crit_msg = "💥 **CRÍTICO!** "
            if is_domador_attack:
                if initial_attack_style == "basico" or (
                    turn == 1
                    and initial_attack_style == "especial"
                    and raw_player_data["energy"] < cost_energy_special
                ):
                    total_base_attack_for_display = base_owner_attack + base_wolf_attack
                    if total_base_attack_for_display > 0:
                        owner_dmg_display = int(
                            player_dmg
                            * (base_owner_attack / total_base_attack_for_display)
                        )
                        wolf_dmg_display = player_dmg - owner_dmg_display
                elif initial_attack_style == "especial":
                    total_base_special_attack_for_display = (
                        base_owner_special_attack + base_wolf_special_attack
                    )
                    if total_base_special_attack_for_display > 0:
                        owner_dmg_display = int(
                            player_dmg
                            * (
                                base_owner_special_attack
                                / total_base_special_attack_for_display
                            )
                        )
                        wolf_dmg_display = player_dmg - owner_dmg_display

        if raw_player_data["class"] == "Vampiro":
            if attack_type_name == "Ataque Básico":
                heal_from_vampire_basic = int(player_dmg * 0.5)
                raw_player_data["hp"] = min(
                    raw_player_data["max_hp"],
                    raw_player_data["hp"] + heal_from_vampire_basic,
                )
                log.append(f"🩸 Você sugou `{heal_from_vampire_basic}` HP do inimigo!")
            elif attack_type_name == "Ataque Especial":
                heal_from_vampire_special = int(player_dmg * 0.75)
                raw_player_data["hp"] = min(
                    raw_player_data["max_hp"],
                    raw_player_data["hp"] + heal_from_vampire_special,
                )
                log.append(
                    f"🧛 Você sugou `{heal_from_vampire_special}` HP do inimigo com seu ataque especial!"
                )

        enemy_hp -= player_dmg

        if is_domador_attack:
            log.append(
                f"➡️ **Turno {turn}**: {crit_msg}Você e seu lobo usaram **{attack_type_name}** e causaram `{player_dmg}` de dano (Você: `{owner_dmg_display}`, Lobo: `{wolf_dmg_display}`)."
            )
        else:
            log.append(
                f"➡️ **Turno {turn}**: {crit_msg}Você usou **{attack_type_name}** e causou `{player_dmg}` de dano."
            )

        if len(log) > 5:
            log.pop(0)

        player_hp = raw_player_data["hp"]

        if raw_player_data["class"] == "Domador":
            owner_base_for_ratio = raw_player_data["max_hp"]
            wolf_base_for_ratio = int(raw_player_data["max_hp"] * 0.50)
            total_ratio_base = owner_base_for_ratio + wolf_base_for_ratio

            if total_ratio_base > 0:
                owner_ratio = owner_base_for_ratio / total_ratio_base

                owner_display_hp = int(player_hp * owner_ratio)
                wolf_display_hp = player_hp - owner_display_hp
            else:
                owner_display_hp = player_hp
                wolf_display_hp = 0
            player_hp_display_text = (
                f"❤️ Você: {max(0, owner_display_hp)}/{owner_display_max_hp}\n"
                f"🐺 Lobo: {max(0, wolf_display_hp)}/{wolf_display_max_hp}"
            )
        else:
            player_hp_display_text = f"❤️ {max(0, player_hp)}/{player_stats['max_hp']}"

        embed.description = "\n".join(log)
        embed.set_field_at(
            0,
            name=interaction.user.display_name,
            value=player_hp_display_text,
            inline=True,
        )
        embed.set_field_at(
            1,
            name=enemy["name"],
            value=f"❤️ {max(0, enemy_hp)}/{enemy['hp']}",
            inline=True,
        )
        await interaction.edit_original_response(embed=embed)

        if enemy_hp <= 0:
            break

        await asyncio.sleep(2.5)

        enemy_dmg = random.randint(enemy["attack"] // 2, enemy["attack"])

        total_evasion_chance = player_stats.get("evasion_chance_bonus", 0.0)

        if raw_player_data.get("bencao_dracula_active", False):
            dracula_info = ITEMS_DATA.get("bencao_dracula", {})
            total_evasion_chance += dracula_info.get("evasion_chance", 0.0)

        if (
            raw_player_data["class"] == "Vampiro"
            and random.random() < total_evasion_chance
        ):
            hp_steal_percent_on_evade = ITEMS_DATA.get("bencao_dracula", {}).get(
                "hp_steal_percent_on_evade", 0.0
            )
            hp_stolen_on_evade = int(enemy_dmg * hp_steal_percent_on_evade)
            raw_player_data["hp"] = min(
                raw_player_data["max_hp"], raw_player_data["hp"] + hp_stolen_on_evade
            )

            log.append(
                f"👻 **DESVIADO!** {enemy['name']} errou o ataque! Você sugou `{hp_stolen_on_evade}` HP!)"
            )
            if len(log) > 5:
                log.pop(0)
            player_hp = raw_player_data["hp"]

            if raw_player_data["class"] == "Domador":
                owner_base_for_ratio = raw_player_data["max_hp"]
                wolf_base_for_ratio = int(raw_player_data["max_hp"] * 0.50)
                total_ratio_base = owner_base_for_ratio + wolf_base_for_ratio
                if total_ratio_base > 0:
                    owner_ratio = owner_base_for_ratio / total_ratio_base
                    owner_display_hp = int(player_hp * owner_ratio)
                    wolf_display_hp = player_hp - owner_display_hp
                else:
                    owner_display_hp = player_hp
                    wolf_display_hp = 0
                player_hp_display_text = (
                    f"❤️ Você: {max(0, owner_display_hp)}/{owner_display_max_hp}\n"
                    f"🐺 Lobo: {max(0, wolf_display_hp)}/{wolf_display_max_hp}"
                )
            else:
                player_hp_display_text = (
                    f"❤️ {max(0, player_hp)}/{player_stats['max_hp']}"
                )

            embed.description = "\n".join(log)
            embed.set_field_at(
                0,
                name=interaction.user.display_name,
                value=player_hp_display_text,
                inline=True,
            )
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(1.5)
            continue

        player_hp -= enemy_dmg
        raw_player_data["hp"] = player_hp

        amulet_info = ITEMS_DATA.get("amuleto_de_pedra", {})
        if (
            player_hp <= 0
            and raw_player_data["inventory"].get("amuleto_de_pedra", 0) > 0
            and not amulet_activated_this_combat
            and not raw_player_data.get("amulet_used_since_revive", False)
        ):
            player_hp = 1
            raw_player_data["hp"] = 1
            amulet_activated_this_combat = True
            raw_player_data["amulet_used_since_revive"] = True
            log.append("✨ **Amuleto de Pedra ativado!** Você sobreviveu por um triz!")
            if len(log) > 5:
                log.pop(0)

            if raw_player_data["class"] == "Domador":
                owner_base_for_ratio = raw_player_data["max_hp"]
                wolf_base_for_ratio = int(raw_player_data["max_hp"] * 0.50)
                total_ratio_base = owner_base_for_ratio + wolf_base_for_ratio
                if total_ratio_base > 0:
                    owner_ratio = owner_base_for_ratio / total_ratio_base
                    owner_display_hp = int(player_hp * owner_ratio)
                    wolf_display_hp = player_hp - owner_display_hp
                else:
                    owner_display_hp = player_hp
                    wolf_display_hp = 0
                player_hp_display_text = (
                    f"❤️ Você: {max(0, owner_display_hp)}/{owner_display_max_hp}\n"
                    f"🐺 Lobo: {max(0, wolf_display_hp)}/{wolf_display_max_hp}"
                )
            else:
                player_hp_display_text = (
                    f"❤️ {max(0, player_hp)}/{player_stats['max_hp']}"
                )

            embed.description = "\n".join(log)
            embed.set_field_at(
                0,
                name=interaction.user.display_name,
                value=player_hp_display_text,
                inline=True,
            )
            await interaction.edit_original_response(embed=embed)
            await asyncio.sleep(1.5)
            continue

        log.append(f"⬅️ {enemy['name']} ataca e causa `{enemy_dmg}` de dano.")
        if len(log) > 5:
            log.pop(0)

        if raw_player_data["class"] == "Domador":
            owner_base_for_ratio = raw_player_data["max_hp"]
            wolf_base_for_ratio = int(raw_player_data["max_hp"] * 0.50)
            total_ratio_base = owner_base_for_ratio + wolf_base_for_ratio
            if total_ratio_base > 0:
                owner_ratio = owner_base_for_ratio / total_ratio_base
                # The problematic line 751 was here, now corrected:
                owner_display_hp = int(player_hp * owner_ratio)
                wolf_display_hp = player_hp - owner_display_hp
            else:
                owner_display_hp = player_hp
                wolf_display_hp = 0
            player_hp_display_text = (
                f"❤️ Você: {max(0, owner_display_hp)}/{owner_display_max_hp}\n"
                f"🐺 Lobo: {max(0, wolf_display_hp)}/{wolf_display_max_hp}"
            )
        else:
            player_hp_display_text = f"❤️ {max(0, player_hp)}/{player_stats['max_hp']}"

        embed.description = "\n".join(log)
        embed.set_field_at(
            0,
            name=interaction.user.display_name,
            value=player_hp_display_text,
            inline=True,
        )
        embed.set_field_at(
            1,
            name=enemy["name"],
            value=f"❤️ {max(0, enemy_hp)}/{enemy['hp']}",
            inline=True,
        )
        await interaction.edit_original_response(embed=embed)

        turn += 1

    final_embed = Embed()
    raw_player_data["hp"] = max(0, player_hp)

    if player_hp <= 0:
        final_embed.title = "☠️ Você Foi Derrotado!"
        final_embed.color = Color.dark_red()
        raw_player_data["status"] = "dead"
        raw_player_data["deaths"] += 1
        final_embed.description = f"O {enemy['name']} foi muito forte para você."
    else:
        final_embed.title = "🏆 Vitória! 🏆"
        final_embed.color = Color.green()
        final_embed.description = f"Você derrotou o {enemy['name']}!"

        xp_gain_raw = enemy["xp"]

        xp_gain_raw = int(
            xp_gain_raw * (1 + player_stats.get("xp_multiplier_passive", 0.0))
        )

        if raw_player_data.get("xptriple") is True:
            xp_gain = xp_gain_raw * 3
            xp_message = f"✨ +{xp_gain} XP (triplicado!)"
        else:
            xp_gain = xp_gain_raw
            xp_message = f"✨ +{xp_gain} XP"

        if player_stats.get(
            "xp_multiplier_passive", 0.0
        ) > 0 and not raw_player_data.get("xptriple"):
            xp_message += (
                f" (Bônus Passivo: +{int(player_stats['xp_multiplier_passive']*100)}%!)"
            )
        elif player_stats.get("xp_multiplier_passive", 0.0) > 0 and raw_player_data.get(
            "xptriple"
        ):
            xp_message = f"✨ +{xp_gain} XP (triplicado + Bônus Passivo: +{int(player_stats['xp_multiplier_passive']*100)}%!)"

        money_gain_raw = enemy["money"]
        money_gain_raw = int(
            money_gain_raw * (1 + player_stats.get("money_multiplier_passive", 0.0))
        )

        if raw_player_data.get("money_double") is True:
            money_gain = money_gain_raw * 2
            money_message = f"💰 +${money_gain} (duplicado!)"
        else:
            money_gain = money_gain_raw
            money_message = f"💰 +${money_gain}"

        if player_stats.get(
            "money_multiplier_passive", 0.0
        ) > 0 and not raw_player_data.get("money_double"):
            money_message += f" (Bônus Passivo: +{int(player_stats['money_multiplier_passive']*100)}%!)"
        elif player_stats.get(
            "money_multiplier_passive", 0.0
        ) > 0 and raw_player_data.get("money_double"):
            money_message = f"💰 +${money_gain} (duplicado + Bônus Passivo: +{int(player_stats['money_multiplier_passive']*100)}%!)"

        final_embed.add_field(
            name="Recompensas", value=f"{money_message}\n{xp_message}"
        )

        raw_player_data["money"] += money_gain
        raw_player_data["xp"] += xp_gain

        # NEW: Add XP and Money to clan if player is in one
        if raw_player_data.get("clan_id"):
            clan_id = raw_player_data["clan_id"]
            clan_data = clan_database.get(clan_id)
            if clan_data:
                clan_xp_contribution = int(
                    xp_gain * CLAN_KILL_CONTRIBUTION_PERCENTAGE_XP
                )
                clan_money_contribution = int(
                    money_gain * CLAN_KILL_CONTRIBUTION_PERCENTAGE_MONEY
                )
                clan_data["xp"] += clan_xp_contribution
                clan_data["money"] += clan_money_contribution
                save_clan_data()  # Save clan data after update
                final_embed.add_field(
                    name="Contribuição para o Clã",
                    value=f"✨ +{clan_xp_contribution} XP\n💰 +${clan_money_contribution}",
                    inline=False,
                )

        await bot_instance.check_and_process_levelup(
            interaction.user, raw_player_data, interaction
        )

    save_data()
    await interaction.edit_original_response(embed=final_embed)
