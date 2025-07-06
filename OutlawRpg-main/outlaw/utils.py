# utils.py
import math
import random
import time
from datetime import datetime, timedelta
import discord

from config import (
    CRITICAL_CHANCE,
    CRITICAL_MULTIPLIER,
    XP_PER_LEVEL_BASE,
    LEVEL_ROLES,
    ATTRIBUTE_POINTS_PER_LEVEL,
    NEW_CHARACTER_ROLE_ID,
    CLASS_TRANSFORMATIONS,
    ITEMS_DATA,
    CLAN_KILL_CONTRIBUTION_PERCENTAGE_XP,
    CLAN_KILL_CONTRIBUTION_PERCENTAGE_MONEY,
)
from data_manager import (
    player_database,
    get_player_data,
    save_data,
    clan_database,
    get_clan_data,
    save_clan_data,
)


def calculate_effective_stats(player_data: dict) -> dict:
    """Calcula os atributos efetivos de um jogador, incluindo bônus de itens e transformações."""
    effective_hp = player_data["max_hp"]
    effective_attack = player_data["attack"]
    effective_special_attack = player_data["special_attack"]
    xp_multiplier = 1.0
    money_multiplier = 1.0
    healing_multiplier = 1.0
    cooldown_reduction_percent = 0.0
    evasion_chance_bonus = 0.0

    # Bônus de atributos
    if player_data["class"] == "Lutador":
        effective_hp += player_data["strength"] * 1.5
        effective_attack += player_data["strength"] * 0.8
    elif player_data["class"] == "Espadachim":
        effective_attack += player_data["agility"] * 1.2
        effective_hp += player_data["agility"] * 0.5
    elif player_data["class"] == "Atirador":
        effective_special_attack += player_data["intelligence"] * 1.5
        effective_attack += player_data["intelligence"] * 0.5
    elif player_data["class"] == "Curandeiro":
        healing_multiplier += player_data["intelligence"] * 0.02
        effective_hp += player_data["constitution"] * 1.0
    elif player_data["class"] == "Vampiro":
        effective_attack += player_data["strength"] * 0.7
        effective_special_attack += player_data["intelligence"] * 1.0
        healing_multiplier += player_data["dexterity"] * 0.015  # Roubo de vida
    elif player_data["class"] == "Domador":
        effective_attack += player_data["strength"] * 0.6
        effective_hp += player_data["constitution"] * 0.7
        xp_multiplier += player_data["dexterity"] * 0.005  # Bônus de XP de caça
    elif player_data["class"] == "Corpo Seco":
        effective_hp += player_data["constitution"] * 1.8
        effective_attack += player_data["strength"] * 0.5

    # Bônus do item "Habilidade Inata (Passiva)" (bônus de estilo)
    if "habilidade_inata" in player_data.get("inventory", {}):
        if player_data.get("power_style") == "Força":
            effective_attack *= 1.05
            effective_hp *= 1.02
        elif player_data.get("power_style") == "Agilidade":
            effective_attack *= 1.03
            evasion_chance_bonus += 0.03
        elif player_data.get("power_style") == "Inteligência":
            effective_special_attack *= 1.07
            cooldown_reduction_percent += 0.03
        elif player_data.get("power_style") == "Constituição":
            effective_hp *= 1.07
        elif player_data.get("power_style") == "Destreza":
            xp_multiplier += 0.05
            money_multiplier += 0.05

    # Bônus de itens equipados
    for item_id in player_data.get("equipped_items", {}).values():
        item_info = ITEMS_DATA.get(item_id)
        if item_info and item_info.get("type") == "equipable":
            if item_info.get("class_restriction") and item_info["class_restriction"] != player_data["class"]:
                continue # Pular item se houver restrição de classe e não corresponder

            if "attack_bonus_percent" in item_info:
                effective_attack *= (1 + item_info["attack_bonus_percent"])
            if "hp_bonus_flat" in item_info:
                effective_hp += item_info["hp_bonus_flat"]
            if "special_attack_bonus_percent" in item_info:
                effective_special_attack *= (1 + item_info["special_attack_bonus_percent"])
            if "cooldown_reduction_percent" in item_info:
                cooldown_reduction_percent += item_info["cooldown_reduction_percent"]
            if "effect_multiplier" in item_info and item_info.get("description") == "Aumenta a eficácia de todas as suas curas em 20%.":
                healing_multiplier *= item_info["effect_multiplier"]
            if "hp_penalty_percent" in item_info:
                effective_hp *= (1 - item_info["hp_penalty_percent"])

    # Efeito do amuleto de pedra
    if "amuleto_de_pedra" in player_data.get("inventory", {}):
        # O amuleto de pedra é um item passivo, não afeta os atributos diretamente,
        # mas sim a lógica de combate (segunda chance), então não entra aqui.
        pass

    # Efeito do Coração do Universo
    if "coracao_do_universo" in player_data.get("inventory", {}):
        item_info = ITEMS_DATA.get("coracao_do_universo")
        if item_info:
            effective_attack *= (1 + item_info.get("attack_multiplier", 0) / 100)
            effective_hp *= (1 + item_info.get("max_hp_multiplier", 0) / 100)
            xp_multiplier += item_info.get("xp_multiplier_passive", 0)
            money_multiplier += item_info.get("money_multiplier_passive", 0)
            cooldown_reduction_percent += item_info.get("cooldown_reduction_percent", 0)

    # Bônus de Transformações/Bênçãos ativas
    if player_data.get("current_transformation"):
        transform_name = player_data["current_transformation"]
        player_class = player_data["class"]
        if player_class in CLASS_TRANSFORMATIONS and transform_name in CLASS_TRANSFORMATIONS[player_class]:
            transform_info = CLASS_TRANSFORMATIONS[player_class][transform_name]
            effective_attack *= transform_info.get("attack_multiplier", 1.0)
            effective_special_attack *= transform_info.get("special_attack_multiplier", 1.0)
            effective_hp *= transform_info.get("hp_multiplier", 1.0)
            healing_multiplier *= transform_info.get("healing_multiplier", 1.0)
            cooldown_reduction_percent += transform_info.get("cooldown_reduction_percent", 0.0)
            evasion_chance_bonus += transform_info.get("evasion_chance_bonus", 0.0)

    # Aplicar bênçãos que afetam atributos diretamente
    for item_id, item_info in ITEMS_DATA.items():
        if item_info.get("type") == "blessing_unlock" and player_data.get(f"{item_id}_active"):
            if "attack_multiplier" in item_info:
                effective_attack *= item_info["attack_multiplier"]
            if "special_attack_multiplier" in item_info:
                effective_special_attack *= item_info["special_attack_multiplier"]
            if "max_hp_multiplier" in item_info:
                effective_hp *= item_info["max_hp_multiplier"]
            if "cooldown_reduction_percent" in item_info:
                cooldown_reduction_percent += item_info["cooldown_reduction_percent"]
            if "evasion_chance" in item_info:
                evasion_chance_bonus += item_info["evasion_chance"]

    # Garantir que HP não seja negativo
    effective_hp = max(1, math.floor(effective_hp))
    effective_attack = max(1, math.floor(effective_attack))
    effective_special_attack = max(1, math.floor(effective_special_attack))

    return {
        "hp": effective_hp,
        "attack": effective_attack,
        "special_attack": effective_special_attack,
        "xp_multiplier": xp_multiplier,
        "money_multiplier": money_multiplier,
        "healing_multiplier": healing_multiplier,
        "cooldown_reduction_percent": min(0.95, cooldown_reduction_percent), # Limitar redução de cooldown
        "evasion_chance": min(0.75, evasion_chance_bonus), # Limitar chance de esquiva
    }


async def run_turn_based_combat(bot, interaction, player_id, enemy_data):
    # from views.combat_views import CombatView # Importação local para evitar circular

    player_data = get_player_data(str(player_id))
    original_hp = player_data["hp"]
    player_stats = calculate_effective_stats(player_data)
    player_current_hp = player_data["hp"]
    enemy_current_hp = enemy_data["hp"]

    # Resetar 'second_chance_used' para cada nova batalha
    second_chance_used_in_combat = False
    if "amuleto_de_pedra" in player_data.get("inventory", {}):
        player_data["second_chance_used"] = False # Garantir que está Falso no início da batalha
        save_data()

    combat_log = [f"**--- Início do Combate contra {enemy_data['name']} ---**"]

    # Função auxiliar para adicionar ao log e garantir o limite
    def add_to_log(message):
        combat_log.append(message)
        # Manter o log em um tamanho razoável
        if len(combat_log) > 20:
            combat_log.pop(1) # Remove as entradas mais antigas, exceto o cabeçalho

    while player_current_hp > 0 and enemy_current_hp > 0:
        # Turno do Jogador
        player_hit_chance = random.random()
        is_player_critical = random.random() < CRITICAL_CHANCE
        player_damage = player_stats["attack"]
        if is_player_critical:
            player_damage = math.floor(player_damage * CRITICAL_MULTIPLIER)
            add_to_log(
                f"{interaction.user.mention} atacou {enemy_data['name']} e causou **{player_damage}** de dano! (Crítico!)"
            )
        else:
            add_to_log(
                f"{interaction.user.mention} atacou {enemy_data['name']} e causou **{player_damage}** de dano."
            )
        enemy_current_hp -= player_damage

        if enemy_current_hp <= 0:
            add_to_log(f"**{enemy_data['name']} foi derrotado!**")
            break

        # Turno do Inimigo
        enemy_hit_chance = random.random()
        if enemy_hit_chance > player_stats["evasion_chance"]: # Verifica se o jogador desviou
            enemy_damage = enemy_data["attack"]
            add_to_log(
                f"{enemy_data['name']} atacou {interaction.user.mention} e causou **{enemy_damage}** de dano."
            )
            player_current_hp -= enemy_damage

            # Lógica de roubo de HP se a Bênção de Drácula estiver ativa E o jogador desviou
            # Nota: O roubo de HP na Bênção de Drácula é condicional ao desvio
            if player_data.get("bencao_dracula_active") and player_hit_chance <= player_stats["evasion_chance"]:
                hp_steal_percent = ITEMS_DATA.get("bencao_dracula", {}).get("hp_steal_percent_on_evade", 0)
                if hp_steal_percent > 0:
                    hp_stolen = math.floor(enemy_damage * hp_steal_percent)
                    player_current_hp = min(player_stats["hp"], player_current_hp + hp_stolen)
                    add_to_log(f"✨ Você desviou e roubou **{hp_stolen} HP** de {enemy_data['name']}!")
        else:
            add_to_log(f"{interaction.user.mention} desviou do ataque de {enemy_data['name']}!")


        if player_current_hp <= 0:
            # Lógica da segunda chance do Amuleto de Pedra
            if (
                "amuleto_de_pedra" in player_data.get("inventory", {})
                and not player_data.get("second_chance_used")
            ):
                player_current_hp = math.floor(player_stats["hp"] * 0.30)  # Recupera 30% do HP máximo
                player_data["second_chance_used"] = True
                save_data() # Salva o uso da segunda chance
                add_to_log(
                    "🪨 Seu Amuleto de Pedra brilhou! Você recebeu uma segunda chance e recuperou 30% do seu HP!"
                )
            else:
                add_to_log(f"**{interaction.user.mention} foi derrotado!**")
                break

    # --- Fim do Combate ---
    if player_current_hp <= 0:
        player_data["hp"] = 1  # Deixa o HP em 1 para indicar derrota sem ser 0
        player_data["deaths"] = player_data.get("deaths", 0) + 1
        player_data["status"] = "dead"
        save_data()
        final_message = f"💀 **Você foi derrotado por {enemy_data['name']}!** Retorne à cidade para se curar."
        embed_color = discord.Color.red()
    else:
        xp_gain = enemy_data["xp"]
        money_gain = enemy_data["money"]

        # Aplicar multiplicadores de XP e Dinheiro
        effective_xp_gain = get_player_effective_xp_gain(player_data, xp_gain)
        effective_money_gain = math.floor(money_gain * player_stats["money_multiplier"])

        player_data["xp"] = player_data.get("xp", 0) + effective_xp_gain
        player_data["money"] = player_data.get("money", 0) + effective_money_gain
        player_data["kills"] = player_data.get("kills", 0) + 1
        player_data["hp"] = player_current_hp # Salvar HP restante

        # Contribuição para o clã
        if player_data.get("clan_id"):
            clan_id = player_data["clan_id"]
            clan_data = get_clan_data(clan_id)
            if clan_data:
                clan_xp_contribution = math.floor(xp_gain * CLAN_KILL_CONTRIBUTION_PERCENTAGE_XP)
                clan_money_contribution = math.floor(money_gain * CLAN_KILL_CONTRIBUTION_PERCENTAGE_MONEY)
                clan_data["xp"] = clan_data.get("xp", 0) + clan_xp_contribution
                clan_data["money"] = clan_data.get("money", 0) + clan_money_contribution
                save_clan_data()
                add_to_log(f"🛡️ Seu clã ganhou **{clan_xp_contribution} XP** e **${clan_money_contribution}** pela sua vitória!")


        # Chamar a função centralizada de level-up
        await check_and_process_levelup_internal(bot, interaction.user, player_data, interaction)

        save_data() # Salva todas as mudanças após o combate

        final_message = (
            f"🎉 **Você derrotou {enemy_data['name']}!**\n"
            f"Você ganhou **{effective_xp_gain} XP** e **${effective_money_gain}**."
        )
        embed_color = discord.Color.green()

    embed = discord.Embed(
        title="Relatório de Combate",
        description="\n".join(combat_log),
        color=embed_color,
    )
    embed.add_field(name="Seu HP Final", value=f"{max(0, player_current_hp)}/{player_stats['hp']}")
    embed.set_thumbnail(url=enemy_data["thumb"])
    embed.set_footer(text=f"Próximo ataque disponível em breve.")

    try:
        # Tenta editar a mensagem original da interação
        await interaction.edit_original_response(embed=embed, view=None)
    except Exception:
        # Se falhar (ex: interação expirou), tenta enviar uma nova mensagem
        await interaction.channel.send(embed=embed)


def calculate_xp_for_next_level(current_level: int) -> int:
    """Calcula a XP necessária para o próximo nível."""
    return XP_PER_LEVEL_BASE * (current_level**2)


async def check_and_process_levelup_internal(
    bot, member: discord.Member, player_data: dict, send_target: any
):
    """
    Verifica e processa o level-up de um jogador.
    Pode ser chamado de on_message, comandos de combate, ou tarefas de ranking.
    `send_target` pode ser uma `Interaction` ou um `discord.TextChannel`.
    """
    old_level = player_data.get("level", 1)
    xp_needed_for_next_level = calculate_xp_for_next_level(old_level)

    level_up_occurred = False
    while player_data["xp"] >= xp_needed_for_next_level:
        player_data["level"] += 1
        player_data["attribute_points"] += ATTRIBUTE_POINTS_PER_LEVEL
        player_data["hp"] = player_data["max_hp"]  # Recupera HP ao subir de nível
        level_up_occurred = True
        xp_needed_for_next_level = calculate_xp_for_next_level(player_data["level"])

    if level_up_occurred:
        save_data()  # Salvar os novos dados de level/xp/atributos

        # Sincronizar cargos imediatamente após o level-up
        if bot.GUILD_ID:
            guild = bot.get_guild(bot.GUILD_ID)
            if guild:
                member_obj = guild.get_member(member.id)
                if member_obj:
                    # Remover cargo de 'novo personagem' se ainda tiver
                    if isinstance(NEW_CHARACTER_ROLE_ID, int) and NEW_CHARACTER_ROLE_ID > 0:
                        new_char_role = guild.get_role(NEW_CHARACTER_ROLE_ID)
                        if new_char_role and new_char_role in member_obj.roles:
                            try:
                                await member_obj.remove_roles(new_char_role, reason="Level Up")
                            except discord.Forbidden:
                                print(f"AVISO: Não foi possível remover cargo {new_char_role.name} de {member_obj.display_name} (permissão negada).")
                            except Exception as e:
                                print(f"Erro ao remover cargo de novo personagem: {e}")

                    # Atribuir o novo cargo de nível
                    current_level = player_data["level"]
                    highest_applicable_role_id = None
                    for required_level in sorted(LEVEL_ROLES.keys(), reverse=True):
                        if current_level >= required_level:
                            highest_applicable_role_id = LEVEL_ROLES[required_level]
                            break

                    if highest_applicable_role_id:
                        role_to_add = guild.get_role(highest_applicable_role_id)
                        if role_to_add and role_to_add not in member_obj.roles:
                            try:
                                # Remover cargos de níveis anteriores
                                roles_to_remove = [
                                    r for r in member_obj.roles
                                    if r.id in LEVEL_ROLES.values() and r.id != highest_applicable_role_id
                                ]
                                if roles_to_remove:
                                    await member_obj.remove_roles(*roles_to_remove, reason="Level Up")
                                await member_obj.add_roles(role_to_add, reason="Level Up")
                            except discord.Forbidden:
                                print(f"AVISO: Não foi possível atribuir/remover cargos de nível para {member_obj.display_name} (permissão negada).")
                            except Exception as e:
                                print(f"Erro ao atribuir/remover cargos de nível: {e}")

        # Enviar mensagem de level-up
        embed = discord.Embed(
            title="🎉 Parabéns! Você subiu de nível!",
            description=f"Você alcançou o **Nível {player_data['level']}**!",
            color=discord.Color.gold(),
        )
        embed.add_field(name="Atributos Livres", value=player_data["attribute_points"])
        embed.set_thumbnail(url=member.display_avatar.url)

        if isinstance(send_target, discord.Interaction):
            if not send_target.response.is_done():
                await send_target.response.send_message(embed=embed)
            else:
                await send_target.followup.send(embed=embed)
        elif isinstance(send_target, discord.TextChannel):
            await send_target.send(embed=embed)


def get_player_effective_xp_gain(player_data: dict, base_xp_gain: int) -> int:
    """Calcula o ganho de XP efetivo de um jogador, aplicando multiplicadores."""
    effective_xp_gain = base_xp_gain
    player_stats = calculate_effective_stats(player_data) # Para pegar o xp_multiplier

    effective_xp_gain = math.floor(effective_xp_gain * player_stats["xp_multiplier"])

    # Adicionalmente, se o jogador tiver a Habilidade Inata e o estilo de poder for "Destreza"
    if "habilidade_inata" in player_data.get("inventory", {}) and player_data.get("power_style") == "Destreza":
        item_info = ITEMS_DATA.get("habilidade_inata", {})
        effective_xp_gain = math.floor(effective_xp_gain * (1 + item_info.get("xp_multiplier_passive", 0)))

    # Se o jogador tiver o Coração do Universo
    if "coracao_do_universo" in player_data.get("inventory", {}):
        item_info = ITEMS_DATA.get("coracao_do_universo", {})
        effective_xp_gain = math.floor(effective_xp_gain * (1 + item_info.get("xp_multiplier_passive", 0)))


    return max(1, effective_xp_gain) # Garantir que o ganho mínimo de XP seja 1


# Função auxiliar para formatar tempo de cooldown
def format_cooldown(seconds: int) -> str:
    if seconds <= 0:
        return "Disponível!"
    minutes, seconds = divmod(seconds, 60)
    if minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    return f"{int(seconds)}s"


def get_remaining_cooldown(last_use_time: int, cooldown_seconds: int, cooldown_reduction_percent: float = 0.0) -> int:
    """Calcula o tempo de cooldown restante para uma habilidade, aplicando redução."""
    effective_cooldown = cooldown_seconds * (1 - cooldown_reduction_percent)
    elapsed_time = datetime.now().timestamp() - last_use_time
    remaining_cooldown = math.ceil(effective_cooldown - elapsed_time)
    return max(0, remaining_cooldown)

def display_money(amount: int) -> str:
    """Formata um valor numérico para exibição como dinheiro."""
    return f"${amount:,}"