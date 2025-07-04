# File: outlawrpg-main/OutlawRpg-main-a2057ca2c01b601c3efdbcc8a9106c5a638e3b6b/OutlawRpg-main/outlaw/combat_commands.py
# Reason: Fix for "Coração do Universo not working" (applying passive XP/money multipliers correctly)
# ----------------------------------------------------------------------------------------------------
import discord
from discord.ext import commands
from discord import app_commands, Embed, Color, Interaction
import random
from datetime import datetime

from data_manager import get_player_data, save_data, player_database
from config import (
    ENEMIES,
    WORLD_MAP,
    TRANSFORM_COST,  # <--- ADICIONE ESTA LINHA
    ITEMS_DATA,
    CLASS_TRANSFORMATIONS,
    CRITICAL_CHANCE,
    CRITICAL_MULTIPLIER,
    BOSSES_DATA,
    BOUNTY_PERCENTAGE,
    INITIAL_ATTACK,
    INITIAL_SPECIAL_ATTACK,
)

from custom_checks import check_player_exists, is_in_wilderness
from utils import calculate_effective_stats, run_turn_based_combat


class CombatCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="cacar",
        description="Caça uma criatura na sua localização atual (combate por turnos).",
    )
    @app_commands.check(check_player_exists)
    @app_commands.check(is_in_wilderness)
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.user.id)
    async def cacar(self, i: Interaction):
        player_data = get_player_data(i.user.id)
        if player_data["status"] == "dead":
            await i.response.send_message("Mortos não caçam.", ephemeral=True)
            return

        location_enemies = ENEMIES.get(player_data.get("location"))
        if not location_enemies:
            await i.response.send_message(
                f"Não há criaturas para caçar em {WORLD_MAP.get(player_data['location'], {}).get('name', 'sua localização atual')}.",
                ephemeral=True,
            )
            return

        await i.response.defer()

        enemy_template = random.choice(location_enemies)
        enemy = enemy_template.copy()
        await run_turn_based_combat(self.bot, i, player_data, enemy)

    @app_commands.command(
        name="batalhar",
        description="Enfrenta um Ex-Cavaleiro para testar sua força (combate por turnos).",
    )
    @app_commands.check(check_player_exists)
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.user.id)
    @app_commands.describe(
        primeiro_ataque="Escolha seu ataque inicial: Básico ou Especial."
    )
    @app_commands.choices(
        primeiro_ataque=[
            app_commands.Choice(name="Ataque Básico", value="basico"),
            app_commands.Choice(name="Ataque Especial", value="especial"),
        ]
    )
    async def batalhar(self, i: Interaction, primeiro_ataque: app_commands.Choice[str]):
        player_data = get_player_data(i.user.id)
        if player_data["status"] == "dead":
            await i.response.send_message("Mortos não batalham.", ephemeral=True)
            return

        player_stats = calculate_effective_stats(player_data)

        if primeiro_ataque.value == "especial":
            cost_energy_special = TRANSFORM_COST
            cost_energy_special = max(
                1,
                int(
                    cost_energy_special
                    * (1 - player_stats.get("cooldown_reduction_percent", 0.0))
                ),
            )

            if player_data.get("energy", 0) < cost_energy_special:
                await i.response.send_message(
                    f"Você não tem energia suficiente ({cost_energy_special}) para um Ataque Especial inicial! Use Ataque Básico ou recupere energia.",
                    ephemeral=True,
                )
                return

        await i.response.defer()

        enemy = {
            "name": "Ex-Cavaleiro Renegado",
            "hp": 320,
            "attack": 95,
            "xp": 390,
            "money": 400,
            "thumb": "https://c.tenor.com/ebFt6wJWEu8AAAAC/tenor.gif",
        }
        await run_turn_based_combat(self.bot, i, player_data, enemy)

    @app_commands.command(name="atacar", description="Ataca outro jogador em um duelo.")
    @app_commands.check(check_player_exists)
    @app_commands.describe(
        alvo="O jogador que você quer atacar.", estilo="O tipo de ataque a ser usado."
    )
    @app_commands.choices(
        estilo=[
            app_commands.Choice(name="Ataque Básico", value="basico"),
            app_commands.Choice(name="Ataque Especial", value="especial"),
        ]
    )
    async def atacar(
        self, i: Interaction, alvo: discord.Member, estilo: app_commands.Choice[str]
    ):
        attacker_id, target_id = str(i.user.id), str(alvo.id)
        if attacker_id == target_id:
            await i.response.send_message(
                "Você não pode atacar a si mesmo!", ephemeral=True
            )
            return

        raw_attacker_data = get_player_data(attacker_id)
        raw_target_data = get_player_data(target_id)

        if not raw_target_data:
            await i.response.send_message(
                "Este jogador não tem uma ficha!", ephemeral=True
            )
            return
        if raw_attacker_data["status"] == "dead" or raw_target_data["status"] == "dead":
            await i.response.send_message(
                "Um dos jogadores está morto.", ephemeral=True
            )
            return

        if raw_target_data.get("status") == "afk":
            await i.response.send_message(
                f"{alvo.display_name} está em modo AFK e não pode ser atacado.",
                ephemeral=True,
            )
            return

        if raw_attacker_data.get("location") != raw_target_data.get("location"):
            await i.response.send_message(
                "Você precisa estar na mesma localização para atacar outro jogador!",
                ephemeral=True,
            )
            return

        attacker_stats = calculate_effective_stats(raw_attacker_data)
        target_stats = calculate_effective_stats(raw_target_data)

        now = datetime.now().timestamp()
        cooldown_key = f"{estilo.value}_attack_cooldown"
        cooldown_duration = 10 if estilo.value == "basico" else 30

        cooldown_duration = int(
            cooldown_duration
            * (1 - attacker_stats.get("cooldown_reduction_percent", 0.0))
        )
        cooldown_duration = max(1, cooldown_duration)

        if (
            now - raw_attacker_data["cooldowns"].get(cooldown_key, 0)
            < cooldown_duration
        ):
            await i.response.send_message(
                f"Seu {estilo.name} está em cooldown! Tente novamente em **{cooldown_duration - (now - raw_attacker_data['cooldowns'].get(cooldown_key, 0)):.1f}s**.",
                ephemeral=True,
            )
            return

        damage = (
            random.randint(
                attacker_stats["attack"] // 2, int(attacker_stats["attack"] * 1.2)
            )
            if estilo.value == "basico"
            else random.randint(
                int(attacker_stats["special_attack"] * 0.8),
                int(attacker_stats["special_attack"] * 1.5),
            )
        )
        crit_msg = ""
        if random.random() < CRITICAL_CHANCE:
            damage = int(damage * CRITICAL_MULTIPLIER)
            crit_msg = "💥 **CRÍTICO!** "

        heal_info_msg = ""
        if raw_attacker_data["class"] == "Vampiro":
            if estilo.value == "basico":
                heal_amount = int(damage * 0.5)
                raw_attacker_data["hp"] = min(
                    raw_attacker_data["max_hp"],
                    raw_attacker_data["hp"] + heal_amount,
                )
                heal_info_msg = (
                    f" (🩸 Você sugou `{heal_amount}` HP de {alvo.display_name}!)"
                )
            elif estilo.value == "especial":
                heal_amount = int(damage * 0.75)
                raw_attacker_data["hp"] = min(
                    raw_attacker_data["max_hp"],
                    raw_attacker_data["hp"] + heal_amount,
                )
                heal_info_msg = f" (🧛 Você sugou `{heal_amount}` HP de {alvo.display_name} com seu ataque especial!)"

        initial_target_hp = raw_target_data["hp"]
        raw_target_data["hp"] -= damage

        embed = Embed(color=Color.red())

        target_effective_stats = calculate_effective_stats(raw_target_data)
        total_evasion_chance_target = target_effective_stats.get(
            "evasion_chance_bonus", 0.0
        )

        if raw_target_data.get("bencao_dracula_active", False):
            dracula_info = ITEMS_DATA.get("bencao_dracula", {})
            total_evasion_chance_target += dracula_info.get("evasion_chance", 0.0)

        if raw_target_data["hp"] <= 0:
            if (
                raw_target_data["class"] == "Vampiro"
                and random.random() < total_evasion_chance_target
            ):
                hp_steal_percent_on_evade = ITEMS_DATA.get("bencao_dracula", {}).get(
                    "hp_steal_percent_on_evade", 0.0
                )
                hp_stolen_on_evade = int(damage * hp_steal_percent_on_evade)
                raw_target_data["hp"] = min(
                    target_stats["max_hp"], initial_target_hp + hp_stolen_on_evade
                )

                embed.title = f"⚔️ Duelo de Fora-da-Lei ⚔️"
                embed.description = (
                    f"{crit_msg}{i.user.display_name} usou **{estilo.name}** em {alvo.display_name} e causou **{damage}** de dano!{heal_info_msg}\n"
                    f"👻 **DESVIADO!** {alvo.display_name} (Vampiro) ativou a Bênção de Drácula e sugou `{hp_stolen_on_evade}` HP!\n"
                    f"{alvo.display_name} agora tem **{raw_target_data['hp']}/{target_stats['max_hp']}** HP."
                )
            elif raw_target_data["inventory"].get(
                "amuleto_de_pedra", 0
            ) > 0 and not raw_target_data.get("amulet_used_since_revive", False):
                raw_target_data["hp"] = 1
                raw_target_data["amulet_used_since_revive"] = True
                embed.title = f"⚔️ Duelo de Fora-da-Lei ⚔️"
                embed.description = (
                    f"{crit_msg}{i.user.display_name} usou **{estilo.name}** em {alvo.display_name} e causou **{damage}** de dano!{heal_info_msg}\n"
                    f"✨ **Amuleto de Pedra ativado!** {alvo.display_name} sobreviveu com 1 HP!\n"
                    f"{alvo.display_name} agora tem **{raw_target_data['hp']}/{target_stats['max_hp']}** HP."
                )
            else:
                raw_target_data["hp"] = 0
                raw_target_data["status"] = "dead"
                raw_target_data["deaths"] += 1
                bounty_claimed = raw_target_data.get("bounty", 0)
                raw_target_data["bounty"] = 0

                money_stolen = int(raw_target_data["money"] * BOUNTY_PERCENTAGE)
                raw_attacker_data["money"] += money_stolen + bounty_claimed
                raw_attacker_data["kills"] += 1
                raw_attacker_data["bounty"] += 100

                embed.title = (
                    f"☠️ ABATE! {i.user.display_name} derrotou {alvo.display_name}!"
                )
                embed.description = f"{crit_msg}{i.user.display_name} usou **{estilo.name}** e causou **{damage}** de dano, finalizando o oponente.{heal_info_msg}\n\n"
                if bounty_claimed > 0:
                    embed.description += (
                        f"Uma recompensa de **${bounty_claimed}** foi clamada!\n"
                    )
                embed.description += f"**${money_stolen}** (20%) foram roubados.\n"
                embed.description += f"{i.user.display_name} agora tem uma recompensa de **${raw_attacker_data['bounty']}** por sua cabeça."
        else:
            embed.title = f"⚔️ Duelo de Fora-da-Lei ⚔️"
            embed.description = f"{crit_msg}{i.user.display_name} usou **{estilo.name}** em {alvo.display_name} e causou **{damage}** de dano!{heal_info_msg}\n{alvo.display_name} agora tem **{raw_target_data['hp']}/{target_stats['max_hp']}** HP."

        raw_attacker_data["cooldowns"][cooldown_key] = now
        save_data()
        await i.response.send_message(embed=embed)

    @app_commands.command(
        name="atacar_boss", description="Ataca o boss global quando ele estiver ativo."
    )
    @app_commands.check(check_player_exists)
    @app_commands.checks.cooldown(1, 5, key=lambda i: i.user.id)
    @app_commands.choices(
        estilo=[
            app_commands.Choice(name="Ataque Básico", value="basico"),
            app_commands.Choice(name="Ataque Especial", value="especial"),
        ]
    )
    async def atacar_boss(self, i: Interaction, estilo: app_commands.Choice[str]):
        if not current_boss_data.get("active_boss_id"):
            await i.response.send_message(
                "Não há nenhum boss ativo no momento.", ephemeral=True
            )
            return

        active_boss_info = BOSSES_DATA.get(current_boss_data["active_boss_id"])
        if not active_boss_info:
            await i.response.send_message(
                "Erro: Dados do boss ativo não encontrados no config.py.",
                ephemeral=True,
            )
            current_boss_data["active_boss_id"] = None
            save_data()
            return

        player_id = str(i.user.id)
        raw_player_data = get_player_data(player_id)

        if raw_player_data["status"] == "dead":
            await i.response.send_message(
                "Você não pode atacar o boss enquanto estiver morto.", ephemeral=True
            )
            return

        if player_id not in current_boss_data["participants"]:
            current_boss_data["participants"].append(player_id)

        now = datetime.now().timestamp()
        cooldown_key = f"boss_{estilo.value}_cooldown"
        cooldown_duration = 5 if estilo.value == "basico" else 15

        player_stats = calculate_effective_stats(raw_player_data)
        cooldown_duration = int(
            cooldown_duration
            * (1 - player_stats.get("cooldown_reduction_percent", 0.0))
        )
        cooldown_duration = max(1, cooldown_duration)

        last_attack = raw_player_data["cooldowns"].get(cooldown_key, 0)

        if now - last_attack < cooldown_duration:
            await i.response.send_message(
                f"Seu {estilo.name} contra o boss está em cooldown! Tente novamente em **{cooldown_duration - (now - last_attack):.1f}s**.",
                ephemeral=True,
            )
            return

        damage = (
            random.randint(player_stats["attack"], int(player_stats["attack"] * 1.5))
            if estilo.value == "basico"
            else random.randint(
                player_stats["special_attack"],
                int(player_stats["special_attack"] * 1.8),
            )
        )
        crit_msg = ""
        if random.random() < CRITICAL_CHANCE:
            damage = int(damage * CRITICAL_MULTIPLIER)
            crit_msg = "💥 **CRÍTICO!** "

        current_boss_data["hp"] -= damage
        raw_player_data["cooldowns"][cooldown_key] = now
        save_data()

        await i.response.send_message(
            f"{crit_msg}Você atacou o {active_boss_info['name']} e causou `{damage}` de dano! Vida restante: `{max(0, current_boss_data['hp'])}/{active_boss_info['max_hp']}`."
        )

        if current_boss_data["hp"] <= 0:
            embed = Embed(
                title=f"🎉 O {active_boss_info['name']} FOI DERROTADO! 🎉",
                description="Recompensas foram distribuídas!",
                color=Color.green(),
            )
            if current_boss_data["channel_id"]:
                boss_channel = self.bot.get_channel(current_boss_data["channel_id"])
                if boss_channel:
                    await boss_channel.send(embed=embed)
            else:
                await i.channel.send(embed=embed)

            for p_id_str in current_boss_data["participants"]:
                if p_data := get_player_data(p_id_str):
                    player_stats_for_rewards = calculate_effective_stats(
                        p_data
                    )  # Ensure stats are fresh for rewards

                    money_gain_raw = active_boss_info.get("money_reward", 0)
                    final_money_message_suffix = ""

                    # Apply passive Money bonus
                    if (
                        player_stats_for_rewards.get("money_multiplier_passive", 0.0)
                        > 0
                    ):
                        money_gain_raw = int(
                            money_gain_raw
                            * (
                                1
                                + player_stats_for_rewards.get(
                                    "money_multiplier_passive", 0.0
                                )
                            )
                        )
                        final_money_message_suffix += f" (Bônus Passivo: +{int(player_stats_for_rewards.get('money_multiplier_passive', 0.0)*100)}%!)"

                    if p_data.get("money_double") is True:
                        money_gain = money_gain_raw * 2
                        final_money_message_suffix = (
                            "(duplicado!" + final_money_message_suffix + ")"
                        )
                    else:
                        money_gain = money_gain_raw

                    money_message = f"💰 +${money_gain}{final_money_message_suffix}"
                    p_data["money"] += money_gain

                    xp_gain_raw = active_boss_info.get("xp_reward", 0)
                    final_xp_message_suffix = ""

                    # Apply passive XP bonus
                    if player_stats_for_rewards.get("xp_multiplier_passive", 0.0) > 0:
                        xp_gain_raw = int(
                            xp_gain_raw
                            * (
                                1
                                + player_stats_for_rewards.get(
                                    "xp_multiplier_passive", 0.0
                                )
                            )
                        )
                        final_xp_message_suffix += f" (Bônus Passivo: +{int(player_stats_for_rewards.get('xp_multiplier_passive', 0.0)*100)}%!)"

                    if p_data.get("xptriple") is True:
                        xp_gain = xp_gain_raw * 3
                        final_xp_message_suffix = (
                            "(triplicado!" + final_xp_message_suffix + ")"
                        )
                    else:
                        xp_gain = xp_gain_raw

                    xp_message = f"✨ +{xp_gain} XP{final_xp_message_suffix}"
                    p_data["xp"] += xp_gain

                    for item_drop_id, quantity_drop in active_boss_info.get(
                        "drops", {}
                    ).items():
                        if item_drop_id == "amuleto_de_pedra":
                            if p_data["inventory"].get("amuleto_de_pedra", 0) == 0:
                                p_data["inventory"]["amuleto_de_pedra"] = 1
                            else:
                                p_data["money"] += 500
                                member_for_compensation = self.bot.get_user(
                                    int(p_id_str)
                                )
                                if member_for_compensation:
                                    try:
                                        await member_for_compensation.send(
                                            f"Você derrotou o {active_boss_info['name']} e encontraria um {ITEMS_DATA.get('amuleto_de_pedra', {}).get('name', 'Amuleto de Pedra')}, mas já o possui! Você recebeu $500 como compensação."
                                        )
                                    except discord.Forbidden:
                                        pass

                        elif (
                            ITEMS_DATA.get(item_drop_id, {}).get("type")
                            == "blessing_unlock"
                        ):
                            if p_data["inventory"].get(item_drop_id, 0) == 0:
                                p_data["inventory"][item_drop_id] = 1
                            else:
                                p_data["money"] += 1000
                                member_for_compensation = self.bot.get_user(
                                    int(p_id_str)
                                )
                                if member_for_compensation:
                                    try:
                                        await member_for_compensation.send(
                                            f"Você derrotou o {active_boss_info['name']} e encontraria a {ITEMS_DATA.get(item_drop_id, {}).get('name', 'Bênção')}, mas já a possui! Você recebeu $1000 como compensação."
                                        )
                                    except discord.Forbidden:
                                        pass
                        else:
                            p_data["inventory"][item_drop_id] = (
                                p_data["inventory"].get(item_drop_id, 0) + quantity_drop
                            )

                    member_for_levelup = self.bot.get_user(int(p_id_str))
                    if member_for_levelup:
                        await self.bot.check_and_process_levelup(
                            member_for_levelup,
                            p_data,
                            i.channel,
                        )
            final_embed.add_field(
                name="Recompensas", value=f"{money_message}\n{xp_message}"
            )

            next_boss_id = active_boss_info.get("next_boss")
            if next_boss_id and next_boss_id in BOSSES_DATA:
                next_boss_info = BOSSES_DATA[next_boss_id]
                current_boss_data["active_boss_id"] = next_boss_id
                current_boss_data["hp"] = next_boss_info["max_hp"]
                current_boss_data["participants"] = []
                await i.channel.send(
                    f"📢 **PREPAREM-SE!** O próximo desafio é: **{next_boss_info['name']}**!"
                )
            else:
                current_boss_data["active_boss_id"] = None
                current_boss_data["hp"] = 0
                current_boss_data["participants"] = []
                current_boss_data["channel_id"] = None
                await i.channel.send(
                    "🎉 Todos os chefes foram derrotados! Um novo ciclo começará em breve."
                )

            save_data()


# File: outlawrpg-main/OutlawRpg-main-a2057ca2c01b601c3efdbcc8a9106c5a638e3b6b/OutlawRpg-main/outlaw/world_commands.py
# Reason: Fix for "no command to summon boss" (correcting item type and boss ID retrieval)
# Reason: Fix for "Coração do Universo not working" (applying passive XP/money multipliers correctly)
# ----------------------------------------------------------------------------------------------------
import discord
from discord.ext import commands
from discord import app_commands, Embed, Color, Interaction
import random
from datetime import datetime

from data_manager import get_player_data, save_data, player_database, current_boss_data
from config import (
    WORLD_MAP,
    STARTING_LOCATION,
    ITEMS_DATA,
    TRANSFORM_COST,
    CLASS_TRANSFORMATIONS,
    MAX_ENERGY,
    BOSSES_DATA,
    INITIAL_ATTACK,
    INITIAL_SPECIAL_ATTACK,
)
from custom_checks import check_player_exists, is_in_city, is_in_wilderness
from utils import calculate_effective_stats
from views.travel_view import TravelView
from views.shop_view import ShopView


class WorldCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="viajar",
        description="Viaja para uma nova localização no mundo de OUTLAWS.",
    )
    @app_commands.check(check_player_exists)
    async def viajar(self, i: Interaction):
        player_data = get_player_data(i.user.id)
        current_location_id = player_data.get("location", STARTING_LOCATION)

        current_location_name = WORLD_MAP.get(current_location_id, {}).get(
            "name", current_location_id.replace("_", " ").title()
        )

        view = TravelView(current_location_id, i.user.id)
        if not view.children:
            await i.response.send_message(
                f"Você está em **{current_location_name}**. Não há para onde viajar a partir daqui.",
                ephemeral=True,
            )
            return
        embed = Embed(
            title=f"✈️ Para Onde Vamos?",
            description=f"Você está em **{current_location_name}**. Escolha seu próximo destino.",
            color=Color.blue(),
        )
        await i.response.send_message(embed=embed, view=view)

    @app_commands.command(
        name="trabalhar",
        description="Faça um trabalho na cidade para ganhar dinheiro e XP.",
    )
    @app_commands.check(check_player_exists)
    @app_commands.check(is_in_city)
    async def trabalhar(self, i: Interaction):
        player_data = get_player_data(i.user.id)
        player_stats = calculate_effective_stats(
            player_data
        )  # Calculate player stats for passive bonuses
        now, cooldown_key, last_work = (
            datetime.now().timestamp(),
            "work_cooldown",
            player_data["cooldowns"].get("work_cooldown", 0),
        )
        if now - last_work < 30:
            await i.response.send_message(
                f"Você já trabalhou recentemente. Tente novamente em **{30 - (now - last_work):.1f} segundos**.",
                ephemeral=True,
            )
            return

        job = random.choice(
            [
                {"name": "Contrabando", "money": random.randint(40, 60), "xp": 20},
                {"name": "Punga", "money": random.randint(20, 80), "xp": 30},
                {
                    "name": "Segurança Particular",
                    "money": random.randint(50, 55),
                    "xp": 25,
                },
            ]
        )

        money_gain_raw = job["money"]
        xp_gain_raw = job["xp"]

        final_money_message_suffix = ""
        if player_stats.get("money_multiplier_passive", 0.0) > 0:
            money_gain_raw = int(
                money_gain_raw * (1 + player_stats.get("money_multiplier_passive", 0.0))
            )
            final_money_message_suffix += f" (Bônus Passivo: +{int(player_stats.get('money_multiplier_passive', 0.0)*100)}%!)"

        if player_data.get("money_double") is True:
            money_gain = money_gain_raw * 2
            final_money_message_suffix = (
                "(duplicado!" + final_money_message_suffix + ")"
            )
        else:
            money_gain = money_gain_raw

        money_message = f"**${money_gain}**{final_money_message_suffix}"

        final_xp_message_suffix = ""
        if player_stats.get("xp_multiplier_passive", 0.0) > 0:
            xp_gain_raw = int(
                xp_gain_raw * (1 + player_stats.get("xp_multiplier_passive", 0.0))
            )
            final_xp_message_suffix += f" (Bônus Passivo: +{int(player_stats.get('xp_multiplier_passive', 0.0)*100)}%!)"

        if player_data.get("xptriple") is True:
            xp_gain = xp_gain_raw * 3
            final_xp_message_suffix = "(triplicado!" + final_xp_message_suffix + ")"
        else:
            xp_gain = xp_gain_raw

        xp_message = f"e **{xp_gain}** XP{final_xp_message_suffix}"

        player_data["money"] += money_gain
        player_data["xp"] += xp_gain
        player_data["cooldowns"][cooldown_key] = now

        embed = Embed(
            title="💰 Bico Concluído!",
            description=f"Você realizou um trabalho de **{job['name']}**.",
            color=Color.dark_gold(),
        )
        embed.add_field(
            name="Recompensa", value=f"Você ganhou {money_message} {xp_message}."
        )
        save_data()
        await self.bot.check_and_process_levelup(i.user, player_data, i)
        await i.response.send_message(embed=embed)

    @app_commands.command(
        name="loja", description="Mostra os itens disponíveis para compra na cidade."
    )
    @app_commands.check(check_player_exists)
    @app_commands.check(is_in_city)
    async def loja(self, i: Interaction):
        embed = Embed(
            title="🛒 Loja OUTLAWS 🛒",
            description="Itens para te ajudar em sua jornada.",
            color=Color.dark_teal(),
        )

        for item_id, item_info in ITEMS_DATA.items():
            if item_info.get("price") is not None:
                name = item_info.get("name", item_id.replace("_", " ").title())
                emoji = item_info.get("emoji", "❔")
                price = item_info.get("price", 0)
                description = item_info.get("description", "Sem descrição.")

                if item_info.get("type") == "healing":
                    description = f"Restaura {item_info['heal']} HP."
                elif item_info.get("type") == "summon":
                    description = "Invoca o terrível boss atual (se não estiver ativo)."
                elif item_info.get("type") == "unique_passive":
                    description = (
                        f"{item_info.get('description', 'Item passivo único.')}"
                    )
                elif item_info.get("type") == "equipable":
                    class_bonus_details = []
                    if "attack_bonus_percent" in item_info:
                        class_bonus_details.append(
                            f"ATK +{int(item_info['attack_bonus_percent'] * 100)}%"
                        )
                    if "hp_bonus_flat" in item_info:
                        class_bonus_details.append(f"HP +{item_info['hp_bonus_flat']}")
                    if "effect_multiplier" in item_info:
                        class_bonus_details.append(
                            f"Cura +{int(item_info['effect_multiplier'] * 100 - 100)}%"
                        )
                    if "cooldown_reduction_percent" in item_info:
                        class_bonus_details.append(
                            f"CD Esp. -{int(item_info['cooldown_reduction_percent'] * 100)}%"
                        )
                    if "hp_penalty_percent" in item_info:
                        class_bonus_details.append(
                            f"HP -{int(item_info['hp_penalty_percent'] * 100)}% (penalidade)"
                        )

                    description = f"[{item_info['class_restriction']}] Bônus: {', '.join(class_bonus_details) or 'Nenhum'}"
                elif item_info.get("type") == "blessing_unlock":
                    description = f"Desbloqueia uma bênção poderosa para sua classe/estilo. Dura: {item_info.get('duration_seconds', 0) // 60}m, Custo Energia Ativ.: {item_info.get('cost_energy', 0)}."
                    if "class_restriction" in item_info:
                        description = (
                            f"[{item_info['class_restriction']}] {description}"
                        )
                    elif "style_restriction" in item_info:
                        description = (
                            f"[{item_info['style_restriction']}] {description}"
                        )

                embed.add_field(
                    name=f"{emoji} {name} (ID: `{item_id}`)",
                    value=f"{description} Custa **${price}**.",
                    inline=False,
                )

        await i.response.send_message(embed=embed, view=ShopView())

    @app_commands.command(
        name="aprimorar",
        description="Gaste dinheiro para fortalecer seus ataques na cidade.",
    )
    @app_commands.check(check_player_exists)
    @app_commands.check(is_in_city)
    @app_commands.choices(
        atributo=[
            app_commands.Choice(name="💪 Força (Ataque)", value="attack"),
            app_commands.Choice(
                name="✨ Agilidade (Atq. Especial)", value="special_attack"
            ),
        ]
    )
    async def aprimorar(self, i: Interaction, atributo: app_commands.Choice[str]):
        player_data = get_player_data(i.user.id)
        attr_key = f"base_{atributo.value}"

        base_stat_current = player_data[attr_key]

        cost_per_point = 20
        initial_base_value = (
            INITIAL_ATTACK if atributo.value == "attack" else INITIAL_SPECIAL_ATTACK
        )

        cost = 100 + (base_stat_current - initial_base_value) * cost_per_point

        if player_data["money"] < cost:
            await i.response.send_message(
                f"Você precisa de ${cost} para aprimorar.", ephemeral=True
            )
            return

        player_data["money"] -= cost
        player_data[attr_key] += 2
        save_data()

        next_cost = 100 + (
            (player_data[attr_key] - initial_base_value) * cost_per_point
        )

        await i.response.send_message(
            f"✨ Aprimoramento concluído! Seu {atributo.name} base aumentou para `{player_data[attr_key]}`. Próximo aprimoramento custará **${next_cost}**."
        )

    @app_commands.command(name="usar", description="Usa um item do seu inventário.")
    @app_commands.check(check_player_exists)
    async def usar(self, i: Interaction, item_id: str):
        item_id = item_id.lower()
        raw_player_data = get_player_data(i.user.id)

        if (
            item_id not in raw_player_data["inventory"]
            or raw_player_data["inventory"].get(item_id, 0) < 1
        ):
            await i.response.send_message("Você não possui este item!", ephemeral=True)
            return

        item_info = ITEMS_DATA.get(item_id)
        if not item_info:
            await i.response.send_message(
                "Este item não é reconhecido.", ephemeral=True
            )
            return

        if (
            item_info.get("type") == "equipable"
            or item_info.get("type") == "blessing_unlock"
            or item_info.get("type") == "passive_style_bonus"
        ):
            await i.response.send_message(
                f"Você tem o(a) **{item_info['name']}** no seu inventário! Seus efeitos são aplicados automaticamente, ou ative-o com `/transformar` ou `/ativar_bencao_aura`.",
                ephemeral=True,
            )
            return

        if item_info.get("type") == "healing":
            raw_player_data["hp"] = min(
                raw_player_data["max_hp"], raw_player_data["hp"] + item_info["heal"]
            )
            raw_player_data["inventory"][item_id] -= 1
            await i.response.send_message(
                f"{item_info['emoji']} Você usou uma {item_info['name']} e recuperou {item_info['heal']} HP! Vida atual: `{raw_player_data['hp']}/{raw_player_data['max_hp']}`."
            )
        elif (
            item_info.get("type") == "summon_boss"
        ):  # Changed from "summon" to "summon_boss"
            if current_boss_data.get("active_boss_id"):
                await i.response.send_message(
                    f"O {BOSSES_DATA[current_boss_data['active_boss_id']]['name']} já está ativo!",
                    ephemeral=True,
                )
                return

            boss_to_summon_name = item_info.get(
                "boss_id_to_summon"
            )  # Get specific boss ID from item
            if not boss_to_summon_name or boss_to_summon_name not in BOSSES_DATA:
                await i.response.send_message(
                    "Erro: O item invocador não especifica um boss válido para invocar.",
                    ephemeral=True,
                )
                return

            summoned_boss_info = BOSSES_DATA[boss_to_summon_name]

            current_boss_data["active_boss_id"] = summoned_boss_info["name"]
            current_boss_data["hp"] = summoned_boss_info["max_hp"]
            current_boss_data["participants"] = [str(i.user.id)]
            current_boss_data["channel_id"] = i.channel.id

            raw_player_data["inventory"][item_id] -= 1

            embed = Embed(
                title=f"{item_info['emoji']} O {summoned_boss_info['name']} APARECEU! {item_info['emoji']}",
                description=f"Invocado por **{i.user.display_name}**! Usem `/atacar_boss`!",
                color=Color.dark_red(),
            )
            embed.add_field(
                name="Vida do Boss",
                value=f"`{current_boss_data['hp']}/{summoned_boss_info['max_hp']}`",
            ).set_thumbnail(
                url=summoned_boss_info.get(
                    "thumbnail", "https://i.imgur.com/example_boss_default.png"
                )
            )
            await i.response.send_message(embed=embed)
        else:
            await i.response.send_message(
                "Este item não possui uma ação de 'usar' definida.", ephemeral=True
            )
            save_data()
            return

        if item_info.get("consumable", False):
            if raw_player_data["inventory"].get(item_id) <= 0:
                del raw_player_data["inventory"][item_id]
        save_data()

    @app_commands.command(
        name="curar",
        description="[Curandeiro] Usa seus poderes para restaurar a vida de um alvo.",
    )
    @app_commands.check(check_player_exists)
    async def curar(self, i: Interaction, alvo: discord.Member):
        raw_player_data = get_player_data(i.user.id)
        player_stats = calculate_effective_stats(raw_player_data)

        if raw_player_data["class"] != "Curandeiro":
            await i.response.send_message(
                "Apenas Curandeiros podem usar este comando.", ephemeral=True
            )
            return

        raw_target_data = get_player_data(alvo.id)
        if not raw_target_data:
            await i.response.send_message(
                f"{alvo.display_name} não possui uma ficha.", ephemeral=True
            )
            return

        target_stats = calculate_effective_stats(raw_target_data)

        now, cooldown_key, last_heal = (
            datetime.now().timestamp(),
            "heal_cooldown",
            raw_player_data["cooldowns"].get("heal_cooldown", 0),
        )

        cooldown_healing = 45
        cooldown_healing = int(
            cooldown_healing * (1 - player_stats.get("cooldown_reduction_percent", 0.0))
        )
        cooldown_healing = max(1, cooldown_healing)

        if now - last_heal < cooldown_healing:
            await i.response.send_message(
                f"Sua cura está em cooldown! Tente novamente em **{cooldown_healing - (now - last_heal):.1f}s**.",
                ephemeral=True,
            )
            return

        heal_amount = random.randint(
            int(player_stats["special_attack"] * 1.5),
            int(player_stats["special_attack"] * 2.5),
        )

        if player_stats.get("healing_multiplier", 1.0) > 1.0:
            heal_amount = int(heal_amount * player_stats["healing_multiplier"])

        original_hp = raw_target_data["hp"]
        raw_target_data["hp"] = min(
            raw_target_data["max_hp"], raw_target_data["hp"] + heal_amount
        )
        healed_for = raw_target_data["hp"] - original_hp

        raw_player_data["cooldowns"][cooldown_key] = now

        embed = Embed(title="✨ Bênção Vital ✨", color=Color.from_rgb(139, 212, 181))
        if i.user.id == alvo.id:
            embed.description = (
                f"Você se concentrou e curou a si mesmo em **{healed_for}** HP."
            )
        else:
            embed.description = f"Você usou seus poderes para curar {alvo.mention} em **{healed_for}** HP."
        embed.set_footer(
            text=f"Vida de {alvo.display_name}: {raw_target_data['hp']}/{target_stats['max_hp']}"
        )
        save_data()
        await i.response.send_message(embed=embed)

    @app_commands.command(
        name="transformar",
        description="Usa sua energia para entrar em um estado mais poderoso ou na Benção da Aura.",
    )
    @app_commands.choices(
        forma=[
            app_commands.Choice(
                name="Lâmina Fantasma (Espadachim)", value="Lâmina Fantasma"
            ),
            app_commands.Choice(name="Punho de Aço (Lutador)", value="Punho de Aço"),
            app_commands.Choice(name="Olho de Águia (Atirador)", value="Olho de Águia"),
            app_commands.Choice(name="Bênção Vital (Curandeiro)", value="Bênção Vital"),
            app_commands.Choice(
                name="Lorde Sanguinário (Vampiro)", value="Lorde Sanguinário"
            ),
            app_commands.Choice(
                name="Lâmina Abençoada (Espadachim - Aura)", value="Lâmina Abençoada"
            ),
            app_commands.Choice(
                name="Punho de Adamantium (Lutador - Aura)", value="Punho de Adamantium"
            ),
            app_commands.Choice(
                name="Visão Cósmica (Atirador - Aura)", value="Visão Cósmica"
            ),
            app_commands.Choice(
                name="Toque Divino (Curandeiro - Aura)", value="Toque Divino"
            ),
            app_commands.Choice(
                name="Rei da Noite (Vampiro - Aura)", value="Rei da Noite"
            ),
            app_commands.Choice(
                name="Bênção de Drácula (Vampiro)", value="Bênção de Drácula"
            ),
        ]
    )
    @app_commands.check(check_player_exists)
    async def transformar(self, i: Interaction, forma: app_commands.Choice[str]):
        raw_player_data = get_player_data(i.user.id)
        player_class = raw_player_data["class"]
        player_style = raw_player_data["style"]

        if forma.value == ITEMS_DATA["bencao_dracula"]["name"]:
            blessing_item_id = "bencao_dracula"
            blessing_info = ITEMS_DATA.get(blessing_item_id)

            if player_class != blessing_info["class_restriction"]:
                await i.response.send_message(
                    f"Somente {blessing_info['class_restriction']}s podem ativar a {blessing_info['name']}.",
                    ephemeral=True,
                )
                return
            if raw_player_data["inventory"].get(blessing_item_id, 0) == 0:
                await i.response.send_message(
                    f"Você não desbloqueou a {blessing_info['name']}! Compre-a na loja primeiro.",
                    ephemeral=True,
                )
                return
            if raw_player_data.get("bencao_dracula_active"):
                await i.response.send_message(
                    f"A {blessing_info['name']} já está ativa!", ephemeral=True
                )
                return

            if raw_player_data["energy"] < blessing_info["cost_energy"]:
                await i.response.send_message(
                    f"Energia insuficiente para a {blessing_info['name']} ({blessing_info['cost_energy']} energia)!",
                    ephemeral=True,
                )
                return

            raw_player_data["bencao_dracula_active"] = True
            raw_player_data["energy"] -= blessing_info["cost_energy"]
            raw_player_data["bencao_dracula_end_time"] = (
                datetime.now().timestamp() + blessing_info["duration_seconds"]
            )

            embed = Embed(
                title=f"{blessing_info['emoji']} {blessing_info['name']}! {blessing_info['emoji']}",
                description=f"{i.user.display_name} invocou a bênção sombria de Drácula!\n"
                f"Você agora tem uma chance de desviar e sugar vida por {blessing_info['duration_seconds'] // 60} minutos!",
                color=Color.dark_purple(),
            )
            embed.set_thumbnail(url="https://c.tenor.com/A6j4yvK8J-oAAAAC/tenor.gif")
            await i.response.send_message(embed=embed)
            save_data()
            return

        transform_info_found = None
        for t_name, t_data in CLASS_TRANSFORMATIONS.get(player_class, {}).items():
            if t_name == forma.value:
                transform_info_found = t_data
                break

        if transform_info_found:
            if raw_player_data.get("current_transformation"):
                await i.response.send_message(
                    f"Você já está na forma {raw_player_data.get('current_transformation', 'transformada')}! Use `/destransformar` para retornar ao normal.",
                    ephemeral=True,
                )
                return

            if transform_info_found.get("required_blessing"):
                required_blessing_id = transform_info_found["required_blessing"]
                if not raw_player_data.get(f"{required_blessing_id}_active"):
                    blessing_name = ITEMS_DATA.get(required_blessing_id, {}).get(
                        "name", "Bênção Desconhecida"
                    )
                    await i.response.send_message(
                        f"Você precisa ter a **{blessing_name}** ativa para usar a transformação **{forma.value}**.",
                        ephemeral=True,
                    )
                    return

            if raw_player_data["energy"] < transform_info_found["cost_energy"]:
                await i.response.send_message(
                    f"Energia insuficiente para se transformar em {forma.value} ({transform_info_found['cost_energy']} energia)!",
                    ephemeral=True,
                )
                return

            raw_player_data["current_transformation"] = forma.value
            raw_player_data["transform_end_time"] = (
                datetime.now().timestamp() + transform_info_found["duration_seconds"]
            )
            raw_player_data["energy"] -= transform_info_found["cost_energy"]

            embed = Embed(
                title=f"{transform_info_found['emoji']} TRANSFORMAÇÃO: {forma.value} {transform_info_found['emoji']}",
                description=f"{i.user.display_name} liberou seu poder oculto e se tornou um(a) {forma.value} por {transform_info_found['duration_seconds'] // 60} minutos!",
                color=Color.dark_red() if player_class == "Vampiro" else Color.gold(),
            )
            await i.response.send_message(embed=embed)
            save_data()
            return

        await i.response.send_message(
            "Forma de transformação não reconhecida ou não disponível para sua classe/estilo.",
            ephemeral=True,
        )

    @app_commands.command(
        name="destransformar",
        description="Retorna à sua forma normal e recupera energia.",
    )
    @app_commands.choices(
        forma=[
            app_commands.Choice(
                name="Lâmina Fantasma (Espadachim)", value="Lâmina Fantasma"
            ),
            app_commands.Choice(name="Punho de Aço (Lutador)", value="Punho de Aço"),
            app_commands.Choice(name="Olho de Águia (Atirador)", value="Olho de Águia"),
            app_commands.Choice(name="Bênção Vital (Curandeiro)", value="Bênção Vital"),
            app_commands.Choice(
                name="Lorde Sanguinário (Vampiro)", value="Lorde Sanguinário"
            ),
            app_commands.Choice(
                name="Lâmina Abençoada (Espadachim - Aura)", value="Lâmina Abençoada"
            ),
            app_commands.Choice(
                name="Punho de Adamantium (Lutador - Aura)", value="Punho de Adamantium"
            ),
            app_commands.Choice(
                name="Visão Cósmica (Atirador - Aura)", value="Visão Cósmica"
            ),
            app_commands.Choice(
                name="Toque Divino (Curandeiro - Aura)", value="Toque Divino"
            ),
            app_commands.Choice(
                name="Rei da Noite (Vampiro - Aura)", value="Rei da Noite"
            ),
            app_commands.Choice(
                name="Benção do Rei Henrique (Aura)", value="bencao_rei_henrique"
            ),
            app_commands.Choice(
                name="Bênção de Drácula (Vampiro)", value="bencao_dracula"
            ),
            app_commands.Choice(name="Todas as Transformações", value="all"),
        ]
    )
    @app_commands.check(check_player_exists)
    async def destransformar(self, i: Interaction, forma: app_commands.Choice[str]):
        raw_player_data = get_player_data(i.user.id)
        deactivated_any = False
        messages = []

        if forma.value == "all":
            if raw_player_data.get("current_transformation"):
                transform_name = raw_player_data["current_transformation"]
                raw_player_data["current_transformation"] = None
                raw_player_data["transform_end_time"] = 0
                deactivated_any = True
                messages.append(
                    f"Você retornou da forma **{transform_name}** para sua forma normal de {raw_player_data['class']}."
                )
            if raw_player_data.get("aura_blessing_active"):
                raw_player_data["aura_blessing_active"] = False
                raw_player_data["aura_blessing_end_time"] = 0
                deactivated_any = True
                messages.append(
                    f"A {ITEMS_DATA.get('bencao_rei_henrique',{}).get('name', 'Bênção da Aura')} foi desativada."
                )
            if raw_player_data.get("bencao_dracula_active"):
                raw_player_data["bencao_dracula_active"] = False
                raw_player_data["bencao_dracula_end_time"] = 0
                deactivated_any = True
                messages.append(
                    f"A {ITEMS_DATA.get('bencao_dracula',{}).get('name', 'Bênção de Drácula')} foi desativada."
                )

            if deactivated_any:
                raw_player_data["energy"] = min(
                    MAX_ENERGY, raw_player_data["energy"] + 1
                )
                save_data()
                messages.append("Você recuperou 1 de energia.")
                await i.response.send_message("\n".join(messages))
            else:
                await i.response.send_message(
                    "Você não tem nenhuma transformação ativa para desativar.",
                    ephemeral=True,
                )
            return

        class_transforms_for_player = CLASS_TRANSFORMATIONS.get(
            raw_player_data["class"], {}
        )
        if (
            raw_player_data.get("current_transformation") == forma.value
            and forma.value in class_transforms_for_player
        ):
            raw_player_data["current_transformation"] = None
            raw_player_data["transform_end_time"] = 0
            deactivated_any = True
            messages.append(
                f"Você retornou à sua forma normal ({raw_player_data['class']}) de **{forma.value}**."
            )
        elif forma.value == "bencao_rei_henrique":
            if not raw_player_data.get("aura_blessing_active"):
                await i.response.send_message(
                    "A Benção do Rei Henrique não está ativa.", ephemeral=True
                )
                return
            raw_player_data["aura_blessing_active"] = False
            raw_player_data["aura_blessing_end_time"] = 0
            deactivated_any = True
            messages.append(
                f"A {ITEMS_DATA.get('bencao_rei_henrique',{}).get('name', 'Bênção da Aura')} foi desativada."
            )
        elif forma.value == "bencao_dracula":
            if not raw_player_data.get("bencao_dracula_active"):
                await i.response.send_message(
                    "A Bênção de Drácula não está ativa.", ephemeral=True
                )
                return
            raw_player_data["bencao_dracula_active"] = False
            raw_player_data["bencao_dracula_end_time"] = 0
            deactivated_any = True
            messages.append(
                f"A {ITEMS_DATA.get('bencao_dracula',{}).get('name', 'Bênção de Drácula')} foi desativada."
            )
        else:
            await i.response.send_message(
                "A transformação solicitada não está ativa ou não é sua.",
                ephemeral=True,
            )
            return

        if deactivated_any:
            raw_player_data["energy"] = min(MAX_ENERGY, raw_player_data["energy"] + 1)
            save_data()
            messages.append("Você recuperou 1 de energia.")
            await i.response.send_message("\n".join(messages))
        else:
            await i.response.send_message(
                "Não foi possível desativar a transformação solicitada.", ephemeral=True
            )

    @app_commands.command(
        name="ativar_bencao_aura",
        description="[Aura] Ativa a Benção do Rei Henrique, concedendo bônus temporários.",
    )
    @app_commands.check(check_player_exists)
    async def ativar_bencao_aura(self, i: Interaction):
        raw_player_data = get_player_data(i.user.id)
        blessing_info = ITEMS_DATA.get("bencao_rei_henrique")

        if raw_player_data["style"] != blessing_info.get("style_restriction"):
            await i.response.send_message(
                f"Somente usuários de {blessing_info.get('style_restriction')} podem invocar a {blessing_info['name']}.",
                ephemeral=True,
            )
            return
        if raw_player_data["inventory"].get("bencao_rei_henrique", 0) == 0:
            await i.response.send_message(
                f"Você não desbloqueou a {blessing_info['name']}! Compre-a na loja primeiro.",
                ephemeral=True,
            )
            return

        if raw_player_data.get("aura_blessing_active"):
            await i.response.send_message(
                f"A {blessing_info['name']} já está ativa!", ephemeral=True
            )
            return

        if not blessing_info:
            await i.response.send_message(
                "Dados da Benção do Rei Henrique não encontrados.", ephemeral=True
            )
            return

        if raw_player_data["energy"] < blessing_info["cost_energy"]:
            await i.response.send_message(
                f"Você precisa de {blessing_info['cost_energy']} de energia para invocar a {blessing_info['name']}!",
                ephemeral=True,
            )
            return

        raw_player_data["energy"] -= blessing_info["cost_energy"]
        raw_player_data["aura_blessing_active"] = True
        raw_player_data["aura_blessing_end_time"] = (
            datetime.now().timestamp() + blessing_info["duration_seconds"]
        )

        embed = Embed(
            title=f"{blessing_info['emoji']} {blessing_info['name']}! {blessing_info['emoji']}",
            description=f"O Rei Henrique da Luz concedeu sua benção a {i.user.display_name}!\n"
            f"Seus atributos e cooldowns foram aprimorados por {blessing_info['duration_seconds'] // 60} minutos!",
            color=Color.gold(),
        )
        embed.set_thumbnail(url="https://c.tenor.com/2U54k92V-i4AAAAC/tenor.gif")
        await i.response.send_message(embed=embed)
        save_data()
