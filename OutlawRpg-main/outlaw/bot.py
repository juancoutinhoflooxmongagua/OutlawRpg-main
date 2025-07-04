import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed, Color, Interaction
import os
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import constants and data from config.py
from config import (
    XP_PER_LEVEL_BASE,
    ATTRIBUTE_POINTS_PER_LEVEL,
    MAX_ENERGY,
    STARTING_LOCATION,
    ITEMS_DATA,
    CLASS_TRANSFORMATIONS,
    BOSSES_DATA,
    WORLD_MAP,
    LEVEL_ROLES,
    NEW_CHARACTER_ROLE_ID,
    LOCATION_KILL_GOALS,
)

# Import data manager
from data_manager import (
    load_data,
    save_data,
    get_player_data,
    player_database,
)

# Import utilities
from utils import (
    calculate_effective_stats,
    run_turn_based_combat,
    check_and_process_levelup_internal,
)

# Import custom exceptions for error handling
from custom_checks import NotInCity, NotInWilderness


# Import Cogs (these classes MUST be imported before OutlawsBot class is defined)
from cogs.character_commands import CharacterCommands
from cogs.combat_commands import CombatCommands
from cogs.world_commands import WorldCommands
from cogs.admin_commands import AdminCommands
from cogs.utility_commands import UtilityCommands
from cogs.blessing_commands import BlessingCommands


# --- INITIAL CONFIGURATION AND CONSTANTS ---
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GUILD_ID = int(os.getenv("GUILD_ID", 0))


class OutlawsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Load Cogs. All actual slash commands should be defined INSIDE these Cogs.
        await self.add_cog(CharacterCommands(self))
        await self.add_cog(CombatCommands(self))
        await self.add_cog(WorldCommands(self))
        await self.add_cog(AdminCommands(self))
        await self.add_cog(UtilityCommands(self))
        await self.add_cog(BlessingCommands(self))

        # Start background tasks
        self.auto_save.start()
        self.energy_regeneration.start()
        self.boss_attack_loop.start()
        self.sync_roles_periodically.start()

        # Sync commands. This is the only place commands should be synced.
        if GUILD_ID:
            guild_obj = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            print(f"Comandos sincronizados para a guilda {GUILD_ID}!")
        else:
            await self.tree.sync()
            print("Comandos sincronizados globalmente!")

        # Set up global error handler
        self.tree.on_error = self.on_app_command_error

    async def on_app_command_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        """A global error handler for all slash commands."""

        # Importing custom exceptions locally here to avoid circular imports if checks are imported by Cogs
        # This is a common pattern for custom CheckFailure exceptions.
        # It's okay because these are only needed inside this error handler.
        from custom_checks import NotInCity, NotInWilderness

        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏳ Este comando está em cooldown! Tente novamente em **{error.retry_after:.1f} segundos**.",
                ephemeral=True,
            )
        elif isinstance(error, NotInWilderness):
            await interaction.response.send_message(
                f"🌲 **Ação Inválida!** {error}", ephemeral=True
            )
        elif isinstance(error, NotInCity):
            await interaction.response.send_message(
                f"🏙️ **Ação Inválida!** {error}", ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "🚫 Você não tem permissão para usar este comando.", ephemeral=True
            )
        elif isinstance(error, app_commands.NoPrivateMessage):  # Corrected check
            await interaction.response.send_message(
                "Este comando não pode ser usado em mensagens privadas.", ephemeral=True
            )
        elif isinstance(
            error, app_commands.CheckFailure
        ):  # Generic check failure for custom checks
            await interaction.response.send_message(
                f"🚫 Falha na verificação: {error}", ephemeral=True
            )
        else:
            print(f"Erro não tratado no comando '{interaction.command.name}': {error}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Ocorreu um erro inesperado ao executar este comando.",
                        ephemeral=True,
                    )
                else:
                    await interaction.followup.send(
                        "❌ Ocorreu um erro inesperado ao executar este comando.",
                        ephemeral=True,
                    )
            except Exception as e:
                print(f"Erro ao tentar enviar a mensagem de erro ao usuário: {e}")

    async def on_ready(self):
        print(f"Bot {self.user} está online!")
        # Ensure 'boss_data' structure and 'location_kill_tracker' for all loaded players
        # These are now handled by get_player_data and load_data with new initializations
        # No need for explicit checks here as data_manager ensures structure on load/access
        for user_id_str, player_data in player_database.items():
            pass  # Data manager handles initialization on load.
        save_data()  # Save any updates made during initialization
        print(
            f"Dados de {len(player_database)} jogadores carregados e estruturas de dados verificadas."
        )

    async def close(self):
        print("Desligando e salvando dados...")
        save_data()
        await super().close()

    async def check_and_process_levelup(
        self,
        member: discord.Member,
        player_data: dict,
        send_target: Interaction | discord.TextChannel,
    ):
        await check_and_process_levelup_internal(self, member, player_data, send_target)

    @tasks.loop(seconds=60)
    async def auto_save(self):
        save_data()
        # print("Dados salvos automaticamente.")

    @tasks.loop(seconds=60)
    async def energy_regeneration(self):
        now = datetime.now().timestamp()
        for user_id_str, player_data in player_database.items():
            user_id = int(user_id_str)
            if player_data.get("energy", 0) < MAX_ENERGY:
                player_data["energy"] = min(
                    MAX_ENERGY, player_data["energy"] + 1
                )  # Ensure energy does not exceed MAX_ENERGY

            # Iterate through all blessing types to check for expiration
            for item_id, item_info in ITEMS_DATA.items():
                if item_info.get("type") == "blessing_unlock":
                    active_key = f"{item_id}_active"
                    end_time_key = f"{item_id}_end_time"
                    if player_data.get(active_key) and now > player_data.get(
                        end_time_key, 0
                    ):
                        player_data[active_key] = False
                        player_data[end_time_key] = 0
                        user = self.get_user(user_id)
                        if user:
                            try:
                                await user.send(
                                    f"✨ A {item_info.get('name', 'Bênção')} em você expirou!"
                                )
                            except discord.Forbidden:
                                pass  # Bot cannot send DMs

            # Check for transformation expiration
            if player_data.get("current_transformation"):
                if now > player_data.get("transform_end_time", 0):
                    transform_name = player_data["current_transformation"]
                    player_data["current_transformation"] = None
                    player_data["transform_end_time"] = 0
                    user = self.get_user(user_id)
                    if user:
                        try:
                            await user.send(
                                f"🔄 Sua transformação de **{transform_name}** expirou!"
                            )
                        except discord.Forbidden:
                            pass
        save_data()

    @tasks.loop(seconds=15)  # Boss attacks every 15 seconds
    async def boss_attack_loop(self):
        for user_id_str, player_data in player_database.items():
            if player_data.get("status") in ["afk", "dead"]:
                continue

            player_boss_data = player_data.get("boss_data")
            if not player_boss_data or not player_boss_data.get("current_boss_id"):
                continue

            active_boss_info = BOSSES_DATA.get(player_boss_data["current_boss_id"])
            if not active_boss_info:
                # Boss info not found, clear player's current boss state
                player_boss_data["current_boss_id"] = None
                player_boss_data["current_boss_hp"] = 0
                player_boss_data["last_spawn_channel_id"] = None
                save_data()
                continue

            channel_id = player_boss_data.get("last_spawn_channel_id")
            if not channel_id:
                # No channel ID, clear player's current boss state
                player_boss_data["current_boss_id"] = None
                player_boss_data["current_boss_hp"] = 0
                player_boss_data["last_spawn_channel_id"] = None
                save_data()
                continue

            channel = self.get_channel(channel_id)
            if not channel:
                # Channel not found, clear player's current boss state
                player_boss_data["current_boss_id"] = None
                player_boss_data["current_boss_hp"] = 0
                player_boss_data["last_spawn_channel_id"] = None
                save_data()
                continue

            target_member = self.get_guild(GUILD_ID).get_member(int(user_id_str))
            if not target_member:
                # Member not found in guild, clear player's current boss state
                player_boss_data["current_boss_id"] = None
                player_boss_data["current_boss_hp"] = 0
                player_boss_data["last_spawn_channel_id"] = None
                save_data()
                continue

            damage_to_deal = random.randint(
                active_boss_info["attack"] // 2, active_boss_info["attack"]
            )

            player_effective_stats = calculate_effective_stats(player_data)
            total_evasion_chance = player_effective_stats.get(
                "evasion_chance_bonus", 0.0
            )

            # Check for all active blessings that provide evasion
            for item_id, item_info in ITEMS_DATA.items():
                if (
                    item_info.get("type") == "blessing_unlock"
                    and item_info.get("evasion_chance", 0.0) > 0
                ):
                    if player_data.get(f"{item_id}_active", False):
                        total_evasion_chance += item_info.get("evasion_chance", 0.0)

            log_message = f"👹 **Fúria do {active_boss_info['name']}** ataca **{target_member.display_name}**!"

            evaded = False
            hp_stolen_on_evade = 0
            # Apply evasion if player has enough total evasion chance and succeeds the roll
            if random.random() < total_evasion_chance:
                # Find the highest HP steal percentage from active blessings, if applicable
                max_hp_steal_percent = 0.0
                for item_id, item_info in ITEMS_DATA.items():
                    if (
                        item_info.get("type") == "blessing_unlock"
                        and item_info.get("evasion_chance", 0.0) > 0
                    ):
                        if player_data.get(f"{item_id}_active", False):
                            max_hp_steal_percent = max(
                                max_hp_steal_percent,
                                item_info.get("hp_steal_percent_on_evade", 0.0),
                            )

                hp_stolen_on_evade = int(damage_to_deal * max_hp_steal_percent)
                player_data["hp"] = min(
                    player_data["max_hp"], player_data["hp"] + hp_stolen_on_evade
                )
                log_message += f"\n👻 **DESVIADO!** Você evitou o ataque e sugou `{hp_stolen_on_evade}` HP!"
                evaded = True
            else:
                player_data["hp"] -= damage_to_deal
                log_message += f"\nVocê sofreu `{damage_to_deal}` de dano!"

            if player_data["hp"] <= 0:
                player_data["hp"] = 0
                player_data["status"] = "dead"
                player_data["deaths"] += 1
                log_message += "\n☠️ Você foi derrotado pelo Boss!"

            save_data()

            attack_embed = Embed(
                title="Ataque de Boss!",
                description=log_message,
                color=Color.dark_orange(),
            )
            attack_embed.set_footer(
                text=f"Sua vida: {max(0, player_data['hp'])}/{player_data['max_hp']}"
            )
            try:
                await channel.send(target_member.mention, embed=attack_embed)
            except Exception as e:
                print(
                    f"Erro ao enviar mensagem de ataque de boss para {target_member.display_name} no canal {channel_id}: {e}"
                )
                # If message sending fails, consider the boss encounter invalid for this player
                player_boss_data["current_boss_id"] = None
                player_boss_data["current_boss_hp"] = 0
                player_boss_data["last_spawn_channel_id"] = None
                save_data()

    @tasks.loop(minutes=5)
    async def sync_roles_periodically(self):
        if GUILD_ID == 0:
            print(
                "AVISO: GUILD_ID não está configurado. A sincronização de cargos não funcionará."
            )
            return

        guild = self.get_guild(GUILD_ID)
        if not guild:
            print(
                f"AVISO: Guilda com ID {GUILD_ID} não encontrada. A sincronização de cargos não pode prosseguir."
            )
            return

        print(f"Iniciando sincronização de cargos na guilda {guild.name}...")

        if not guild.chunked:
            try:
                await guild.chunk()
                print(f"Membros da guilda {guild.name} carregados no cache.")
            except discord.Forbidden:
                print(
                    f"Erro: Bot sem permissão para carregar membros na guilda {guild.name}. Verifique as permissões de `Intents de Membros` e `Ler Histórico de Mensagens`."
                )
                return
            except discord.HTTPException as e:
                print(f"Erro ao carregar membros da guilda {guild.name}: {e}")
                return

        total_synced = 0
        for member_id_str, player_data in player_database.items():
            member_id = int(member_id_str)
            member = guild.get_member(member_id)

            if not member:
                continue

            if player_data.get("status") == "afk":
                continue

            # 1. Handle NEW_CHARACTER_ROLE_ID
            if isinstance(NEW_CHARACTER_ROLE_ID, int) and NEW_CHARACTER_ROLE_ID > 0:
                new_char_role = guild.get_role(NEW_CHARACTER_ROLE_ID)
                if new_char_role:
                    if new_char_role not in member.roles:
                        try:
                            await member.add_roles(
                                new_char_role, reason="Sincronização de cargo inicial."
                            )
                            total_synced += 1
                        except discord.Forbidden:
                            print(
                                f"PERMISSÃO NEGADA: Não foi possível adicionar '{new_char_role.name}' a {member.display_name}."
                            )
                        except discord.HTTPException as e:
                            print(
                                f"ERRO HTTP ao adicionar '{new_char_role.name}' a {member.display_name}: {e}"
                            )
                else:
                    print(
                        f"Cargo inicial com ID {NEW_CHARACTER_ROLE_ID} não encontrado na guilda."
                    )
            else:
                print(
                    "NEW_CHARACTER_ROLE_ID não é um ID de cargo válido (deve ser um número inteiro positivo)."
                )

            # 2. Handle LEVEL_ROLES
            if isinstance(LEVEL_ROLES, dict):
                current_level = player_data.get("level", 1)
                highest_applicable_role_id = None

                for required_level in sorted(LEVEL_ROLES.keys(), reverse=True):
                    if current_level >= required_level:
                        highest_applicable_role_id = LEVEL_ROLES[required_level]
                        break

                all_level_role_ids = list(LEVEL_ROLES.values())

                roles_to_remove = []
                roles_to_add = []

                for existing_role in member.roles:
                    if (
                        existing_role.id in all_level_role_ids
                        and existing_role.id != highest_applicable_role_id
                    ):
                        roles_to_remove.append(existing_role)

                if highest_applicable_role_id:
                    role_to_add = guild.get_role(highest_applicable_role_id)
                    if role_to_add and role_to_add not in member.roles:
                        roles_to_add.append(role_to_add)

                if roles_to_remove:
                    try:
                        await member.remove_roles(
                            *roles_to_remove, reason="Sincronização de cargos de nível."
                        )
                        total_synced += len(roles_to_remove)
                    except discord.Forbidden:
                        print(
                            f"PERMISSÃO NEGADA: Não foi possível remover cargos de {member.display_name}."
                        )
                    except discord.HTTPException as e:
                        print(
                            f"ERRO HTTP ao remover cargos de {member.display_name}: {e}"
                        )

                if roles_to_add:
                    try:
                        await member.add_roles(
                            *roles_to_add, reason="Sincronização de cargos de nível."
                        )
                        total_synced += len(roles_to_add)
                    except discord.Forbidden:
                        print(
                            f"PERMISSÃO NEGADA: Não foi possível adicionar '{roles_to_add[0].name}' a {member.display_name}."
                        )
                    except discord.HTTPException as e:
                        print(
                            f"ERRO HTTP ao adicionar '{roles_to_add[0].name}' a {member.display_name}: {e}"
                        )

        if total_synced > 0:
            print(f"Sincronização de cargos concluída. Total de ações: {total_synced}.")
        else:
            print("Sincronização de cargos concluída. Nenhum cargo foi alterado.")

    @sync_roles_periodically.before_loop
    async def before_sync_roles_periodically(self):
        await self.wait_until_ready()


if __name__ == "__main__":
    bot = OutlawsBot()
    if TOKEN:
        try:
            bot.run(TOKEN)
        except KeyboardInterrupt:
            print("Desligando...")
        except discord.errors.LoginFailure as e:
            print(f"ERRO DE LOGIN: {e}\nVerifique seu DISCORD_TOKEN no arquivo .env.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado ao iniciar o bot: {e}")
    else:
        print("ERRO: O DISCORD_TOKEN não foi encontrado no arquivo .env!")
