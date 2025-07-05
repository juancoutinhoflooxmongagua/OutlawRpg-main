import discord
from discord.ext import commands
from discord import app_commands, Embed, Color, Interaction
import random
from datetime import datetime

from data_manager import get_player_data, save_data, player_database, current_boss_data
from config import (
    ENEMIES,
    WORLD_MAP,
    TRANSFORM_COST,
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
        if player_data.get("status") == "dead":
            await i.response.send_message("Mortos não caçam.", ephemeral=True)
            return

        location_enemies = ENEMIES.get(player_data.get("location"))
        if not location_enemies:
            await i.response.send_message(
                f"Não há criaturas para caçar em {WORLD_MAP.get(player_data.get('location', {}), {}).get('name', 'sua localização atual')}.",
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
        if player_data.get("status") == "dead":
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
        if (
            raw_attacker_data.get("status") == "dead"
            or raw_target_data.get("status") == "dead"
        ):
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
            now - raw_attacker_data.get("cooldowns", {}).get(cooldown_key, 0)
            < cooldown_duration
        ):
            await i.response.send_message(
                f"Seu {estilo.name} está em cooldown! Tente novamente em **{cooldown_duration - (now - raw_attacker_data.get('cooldowns', {}).get(cooldown_key, 0)):.1f}s**.",
                ephemeral=True,
            )
            return

        damage = (
            random.randint(
                attacker_stats.get("attack", 0) // 2,
                int(attacker_stats.get("attack", 0) * 1.2),
            )
            if estilo.value == "basico"
            else random.randint(
                int(attacker_stats.get("special_attack", 0) * 0.8),
                int(attacker_stats.get("special_attack", 0) * 1.5),
            )
        )
        crit_msg = ""
        if random.random() < CRITICAL_CHANCE:
            damage = int(damage * CRITICAL_MULTIPLIER)
            crit_msg = "💥 **CRÍTICO!** "

        heal_info_msg = ""
        if raw_attacker_data.get("class") == "Vampiro":
            if estilo.value == "basico":
                heal_amount = int(damage * 0.5)
                raw_attacker_data["hp"] = min(
                    raw_attacker_data.get("max_hp", 1),
                    raw_attacker_data.get("hp", 0) + heal_amount,
                )
                heal_info_msg = (
                    f" (🩸 Você sugou `{heal_amount}` HP de {alvo.display_name}!)"
                )
            elif estilo.value == "especial":
                heal_amount = int(damage * 0.75)
                raw_attacker_data["hp"] = min(
                    raw_attacker_data.get("max_hp", 1),
                    raw_attacker_data.get("hp", 0) + heal_amount,
                )
                heal_info_msg = f" (🧛 Você sugou `{heal_amount}` HP de {alvo.display_name} com seu ataque especial!)"

        initial_target_hp = raw_target_data.get("hp", 0)
        raw_target_data["hp"] = raw_target_data.get("hp", 0) - damage

        embed = Embed(color=Color.red())

        target_effective_stats = calculate_effective_stats(raw_target_data)
        total_evasion_chance_target = target_effective_stats.get(
            "evasion_chance_bonus", 0.0
        )

        if raw_target_data.get("bencao_dracula_active"):
            dracula_info = ITEMS_DATA.get("bencao_dracula", {})
            total_evasion_chance_target += dracula_info.get("evasion_chance", 0.0)

        if raw_target_data.get("hp", 0) <= 0:
            if (
                raw_target_data.get("class") == "Vampiro"
                and random.random() < total_evasion_chance_target
            ):
                hp_steal_percent_on_evade = ITEMS_DATA.get("bencao_dracula", {}).get(
                    "hp_steal_percent_on_evade", 0.0
                )
                hp_stolen_on_evade = int(damage * hp_steal_percent_on_evade)
                raw_target_data["hp"] = min(
                    target_stats.get("max_hp", 1),
                    initial_target_hp + hp_stolen_on_evade,
                )

                embed.title = f"⚔️ Duelo de Fora-da-Lei ⚔️"
                embed.description = (
                    f"{crit_msg}{i.user.display_name} usou **{estilo.name}** em {alvo.display_name} e causou **{damage}** de dano!{heal_info_msg}\n"
                    f"👻 **DESVIADO!** {alvo.display_name} (Vampiro) ativou a Bênção de Drácula e sugou `{hp_stolen_on_evade}` HP!\n"
                    f"{alvo.display_name} agora tem **{raw_target_data.get('hp',0)}/{target_stats.get('max_hp',1)}** HP."
                )
            elif raw_target_data.get("inventory", {}).get(
                "amuleto_de_pedra", 0
            ) > 0 and not raw_target_data.get("amulet_used_since_revive", False):
                raw_target_data["hp"] = 1
                raw_target_data["amulet_used_since_revive"] = True
                embed.title = f"⚔️ Duelo de Fora-da-Lei ⚔️"
                embed.description = (
                    f"{crit_msg}{i.user.display_name} usou **{estilo.name}** em {alvo.display_name} e causou **{damage}** de dano!{heal_info_msg}\n"
                    f"✨ **Amuleto de Pedra ativado!** {alvo.display_name} sobreviveu com 1 HP!\n"
                    f"{alvo.display_name} agora tem **{raw_target_data.get('hp',0)}/{target_stats.get('max_hp',1)}** HP."
                )
            else:
                raw_target_data["hp"] = 0
                raw_target_data["status"] = "dead"
                raw_target_data["deaths"] = raw_target_data.get("deaths", 0) + 1
                bounty_claimed = raw_target_data.get("bounty", 0)
                raw_target_data["bounty"] = 0

                money_stolen = int(raw_target_data.get("money", 0) * BOUNTY_PERCENTAGE)
                raw_attacker_data["money"] = (
                    raw_attacker_data.get("money", 0) + money_stolen + bounty_claimed
                )
                raw_attacker_data["kills"] = raw_attacker_data.get("kills", 0) + 1
                raw_attacker_data["bounty"] = raw_attacker_data.get("bounty", 0) + 100

                embed.title = (
                    f"☠️ ABATE! {i.user.display_name} derrotou {alvo.display_name}!"
                )
                embed.description = f"{crit_msg}{i.user.display_name} usou **{estilo.name}** e causou **{damage}** de dano, finalizando o oponente.{heal_info_msg}\n\n"
                if bounty_claimed > 0:
                    embed.description += (
                        f"Uma recompensa de **${bounty_claimed}** foi clamada!\n"
                    )
                embed.description += f"**${money_stolen}** (20%) foram roubados.\n"
                embed.description += f"{i.user.display_name} agora tem uma recompensa de **${raw_attacker_data.get('bounty',0)}** por sua cabeça."
        else:
            embed.title = f"⚔️ Duelo de Fora-da-Lei ⚔️"
            embed.description = f"{crit_msg}{i.user.display_name} usou **{estilo.name}** em {alvo.display_name} e causou **{damage}** de dano!{heal_info_msg}\n{alvo.display_name} agora tem **{raw_target_data.get('hp',0)}/{target_stats.get('max_hp',1)}** HP."

        raw_attacker_data.setdefault("cooldowns", {})[cooldown_key] = now
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

        if raw_player_data.get("status") == "dead":
            await i.response.send_message(
                "Você não pode atacar o boss enquanto estiver morto.", ephemeral=True
            )
            return

        if player_id not in current_boss_data.get("participants", []):
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

        last_attack = raw_player_data.get("cooldowns", {}).get(cooldown_key, 0)

        if now - last_attack < cooldown_duration:
            await i.response.send_message(
                f"Seu {estilo.name} contra o boss está em cooldown! Tente novamente em **{cooldown_duration - (now - last_attack):.1f}s**.",
                ephemeral=True,
            )
            return

        damage = (
            random.randint(
                player_stats.get("attack", 0), int(player_stats.get("attack", 0) * 1.5)
            )
            if estilo.value == "basico"
            else random.randint(
                player_stats.get("special_attack", 0),
                int(player_stats.get("special_attack", 0) * 1.8),
            )
        )
        crit_msg = ""
        if random.random() < CRITICAL_CHANCE:
            damage = int(damage * CRITICAL_MULTIPLIER)
            crit_msg = "💥 **CRÍTICO!** "

        current_boss_data["hp"] = current_boss_data.get("hp", 0) - damage
        raw_player_data.setdefault("cooldowns", {})[cooldown_key] = now
        save_data()

        await i.response.send_message(
            f"{crit_msg}Você atacou o {active_boss_info.get('name')} e causou `{damage}` de dano! Vida restante: `{max(0, current_boss_data.get('hp',0))}/{active_boss_info.get('max_hp',1)}`."
        )

        if current_boss_data.get("hp", 0) <= 0:
            embed = Embed(
                title=f"🎉 O {active_boss_info.get('name')} FOI DERROTADO! 🎉",
                description="Recompensas foram distribuídas!",
                color=Color.green(),
            )
            if current_boss_data.get("channel_id"):
                boss_channel = self.bot.get_channel(current_boss_data["channel_id"])
                if boss_channel:
                    await boss_channel.send(embed=embed)
            else:
                await i.channel.send(embed=embed)

            for p_id_str in current_boss_data.get("participants", []):
                if p_data := get_player_data(p_id_str):
                    player_stats_for_rewards = calculate_effective_stats(p_data)

                    # Construção da mensagem de ganho de dinheiro refatorada
                    money_gain_raw = active_boss_info.get("money_reward", 0)
                    money_bonus_sources = []

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
                        money_bonus_sources.append(
                            f"Bônus Passivo: +{int(player_stats_for_rewards.get('money_multiplier_passive', 0.0)*100)}%!"
                        )

                    if p_data.get("money_double") is True:
                        money_gain = money_gain_raw * 2
                        money_bonus_sources.append("duplicado!")
                    else:
                        money_gain = money_gain_raw

                    money_message = f"💰 +${money_gain}"
                    if money_bonus_sources:
                        money_message += f" ({', '.join(money_bonus_sources)})"

                    # Construção da mensagem de ganho de XP refatorada
                    xp_gain_raw = active_boss_info.get("xp_reward", 0)
                    xp_bonus_sources = []

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
                        xp_bonus_sources.append(
                            f"Bônus Passivo: +{int(player_stats_for_rewards.get('xp_multiplier_passive', 0.0)*100)}%!"
                        )

                    if p_data.get("xptriple") is True:
                        xp_gain = xp_gain_raw * 3
                        xp_bonus_sources.append("triplicado!")
                    else:
                        xp_gain = xp_gain_raw

                    xp_message = f"✨ +{xp_gain} XP"
                    if xp_bonus_sources:
                        xp_message += f" ({', '.join(xp_bonus_sources)})"

                    p_data["money"] = p_data.get("money", 0) + money_gain
                    p_data["xp"] = p_data.get("xp", 0) + xp_gain

                    for item_drop_id, quantity_drop in active_boss_info.get(
                        "drops", {}
                    ).items():
                        if item_drop_id == "amuleto_de_pedra":
                            if (
                                p_data.get("inventory", {}).get("amuleto_de_pedra", 0)
                                == 0
                            ):
                                p_data.setdefault("inventory", {})[
                                    "amuleto_de_pedra"
                                ] = 1
                            else:
                                p_data["money"] = p_data.get("money", 0) + 500
                                member_for_compensation = self.bot.get_user(
                                    int(p_id_str)
                                )
                                if member_for_compensation:
                                    try:
                                        await member_for_compensation.send(
                                            f"Você derrotou o {active_boss_info.get('name')} e encontraria um {ITEMS_DATA.get('amuleto_de_pedra', {}).get('name', 'Amuleto de Pedra')}, mas já o possui! Você recebeu $500 como compensação."
                                        )
                                    except discord.Forbidden:
                                        pass

                        elif (
                            ITEMS_DATA.get(item_drop_id, {}).get("type")
                            == "blessing_unlock"
                        ):
                            if p_data.get("inventory", {}).get(item_drop_id, 0) == 0:
                                p_data.setdefault("inventory", {})[item_drop_id] = 1
                            else:
                                p_data["money"] = p_data.get("money", 0) + 1000
                                member_for_compensation = self.bot.get_user(
                                    int(p_id_str)
                                )
                                if member_for_compensation:
                                    try:
                                        await member_for_compensation.send(
                                            f"Você derrotou o {active_boss_info.get('name')} e encontraria a {ITEMS_DATA.get(item_drop_id, {}).get('name', 'Bênção')}, mas já a possui! Você recebeu $1000 como compensação."
                                        )
                                    except discord.Forbidden:
                                        pass
                        else:
                            p_data.setdefault("inventory", {})[item_drop_id] = (
                                p_data.get("inventory", {}).get(item_drop_id, 0)
                                + quantity_drop
                            )

                    member_for_levelup = self.bot.get_user(int(p_id_str))
                    if member_for_levelup:
                        await self.bot.check_and_process_levelup(
                            member_for_levelup,
                            p_data,
                            i.channel,
                        )
            # The 'final_embed' variable is not defined in the original code,
            # so I'm assuming it should be the 'embed' object defined earlier.
            # If 'final_embed' is supposed to be a separate embed, you'll need
            # to define it before this point.
            embed.add_field(name="Recompensas", value=f"{money_message}\n{xp_message}")

            next_boss_id = active_boss_info.get("next_boss_unlock")
            if next_boss_id and next_boss_id in BOSSES_DATA:
                next_boss_info = BOSSES_DATA[next_boss_id]
                current_boss_data["active_boss_id"] = next_boss_id
                current_boss_data["hp"] = next_boss_info.get("max_hp", 1)
                current_boss_data["participants"] = []
                await i.channel.send(
                    f"📢 **PREPAREM-SE!** O próximo desafio é: **{next_boss_info.get('name')}**!"
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
