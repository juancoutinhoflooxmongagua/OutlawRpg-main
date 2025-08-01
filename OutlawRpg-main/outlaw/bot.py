# File: OutlawRpg-main/outlaw/bot.py
import discord
from discord.ext import commands, tasks
from discord import app_commands, Embed, Color, Interaction
import os
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Importar constantes e dados de config.py
from config import ( # Changed from .config to config
    XP_PER_LEVEL_BASE,
    ATTRIBUTE_POINTS_PER_LEVEL,
    MAX_ENERGY,
    STARTING_LOCATION,
    ITEMS_DATA,
    CLASS_TRANSFORMATIONS,
    WORLD_MAP,
    LEVEL_ROLES,
    NEW_CHARACTER_ROLE_ID,
    LOCATION_KILL_GOALS,
    CLAN_RANKING_INTERVAL_DAYS,
    CLAN_RANK_REWARDS,
    DEFAULT_CLAN_XP,
    CUSTOM_EMOJIS,
    XP_PER_MESSAGE_COOLDOWN_SECONDS,
)

# Importar data manager
from data_manager import ( # Changed from .data_manager to data_manager
    load_data,
    save_data,
    get_player_data,
    player_database,
    load_clan_data,
    save_clan_data,
    clan_database,
)

# Importar utilitários
from utils import ( # Changed from .utils to utils
    calculate_effective_stats,
    run_turn_based_combat,
    check_and_process_levelup_internal,
    get_player_effective_xp_gain,
    calculate_xp_for_next_level,
)

# Importar exceções personalizadas para tratamento de erros
from custom_checks import NotInCity, NotInWilderness # Changed from .custom_checks to custom_checks


# Importar Cogs
from cogs.character_commands import CharacterCommands # Changed from .cogs.character_commands to cogs.character_commands
from cogs.combat_commands import CombatCommands # Changed from .cogs.combat_commands to cogs.combat_commands
from cogs.world_commands import WorldCommands # Changed from .cogs.world_commands to cogs.world_commands
from cogs.admin_commands import AdminCommands # Changed from .cogs.admin_commands to cogs.admin_commands
from cogs.utility_commands import UtilityCommands # Changed from .cogs.utility_commands to cogs.utility_commands
from cogs.blessing_commands import BlessingCommands # Changed from .cogs.blessing_commands to cogs.blessing_commands
from cogs.clan_commands import ClanCommands # Changed from .cogs.clan_commands to cogs.clan_commands
from cogs.relic_commands import RelicCommands # Changed from .cogs.relic_commands to cogs.relic_commands


# --- CONFIGURAÇÃO INICIAL E CONSTANTES ---
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GUILD_ID = int(os.getenv("GUILD_ID", 0))
ANNOUNCEMENT_CHANNEL_ID = os.getenv("ANNOUNCEMENT_CHANNEL_ID")


class OutlawsBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.last_message_xp_time = {}

    async def setup_hook(self):
        # Carregar Cogs. Todos os comandos de barra reais devem ser definidos DENTRO desses Cogs.
        await self.add_cog(CharacterCommands(self))
        await self.add_cog(CombatCommands(self))
        await self.add_cog(WorldCommands(self))
        await self.add_cog(AdminCommands(self))
        await self.add_cog(UtilityCommands(self))
        await self.add_cog(BlessingCommands(self))
        await self.add_cog(ClanCommands(self))
        await self.add_cog(RelicCommands(self))

        # Iniciar tarefas em segundo plano
        self.auto_save.start()
        self.energy_regeneration.start()
        # Removido: self.boss_attack_loop.start()
        self.sync_roles_periodically.start()
        self.weekly_clan_ranking.start()

        # Sincronizar comandos. Este é o único lugar onde os comandos devem ser sincronizados.
        if GUILD_ID:
            guild_obj = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            print(f"Comandos sincronizados para a guilda {GUILD_ID}!")
        else:
            await self.tree.sync()
            print("Comandos sincronizados globalmente!")

        # Configurar manipulador de erros global
        self.tree.on_error = self.on_app_command_error

    async def on_app_command_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        """Um manipulador de erros global para todos os comandos de barra."""

        # Importando exceções personalizadas localmente aqui para evitar importações circulares se as verificações forem importadas por Cogs
        from custom_checks import NotInCity, NotInWilderness # Changed from .custom_checks to custom_checks

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
        elif isinstance(error, app_commands.NoPrivateMessage):
            await interaction.response.send_message(
                "Este comando não pode ser usado em mensagens privadas.", ephemeral=True
            )
        elif isinstance(error, app_commands.CheckFailure):
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
        # Percorre o player_database para garantir que os padrões estejam inicializados
        # Isso é importante para usuários existentes antes da adição dos novos campos de relíquias/chaves.
        # get_player_data já inicializa os padrões, então apenas acessá-los garante isso.
        for user_id_str in list(
            player_database.keys()
        ):  # Itera sobre uma cópia para evitar modificação durante a iteração
            if not user_id_str.isdigit(): #
                print(f"AVISO: Chave inválida encontrada no player_database: '{user_id_str}'. Ignorando.") #
                continue #
            get_player_data(user_id_str)
        save_data()  # Salva quaisquer inicializações feitas
        load_clan_data()
        print(f"Dados de {len(clan_database)} clãs carregados.")

    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        player_data = get_player_data(
            user_id
        )  # Usa a função atualizada para obter/inicializar dados

        if player_data:
            current_time = datetime.now().timestamp()
            if (
                user_id not in self.last_message_xp_time
                or (current_time - self.last_message_xp_time[user_id])
                >= XP_PER_MESSAGE_COOLDOWN_SECONDS
            ):
                xp_gain = 1
                effective_xp_gain = get_player_effective_xp_gain(player_data, xp_gain)
                player_data["xp"] = player_data.get("xp", 0) + effective_xp_gain
                self.last_message_xp_time[user_id] = current_time

                # Chamar a função centralizada de level-up
                await self.check_and_process_levelup(
                    message.author, player_data, message.channel
                )

                # Salvar dados após potencial aumento de nível (o check_and_process_levelup já deve salvar)
                save_data()  # Garante que as mudanças de XP e level-up sejam salvas

        await self.process_commands(message)

    async def close(self):
        print("Desligando e salvando dados...")
        save_data()
        save_clan_data()
        await super().close()

    async def check_and_process_levelup(
        self,
        member: discord.Member,
        player_data: dict,
        send_target: Interaction | discord.TextChannel,
    ):
        await check_and_process_levelup_internal(self, member, player_data, send_target)

    @tasks.loop(seconds=60)  # Auto-salvamento a cada minuto
    async def auto_save(self):
        save_data()
        save_clan_data()

    @tasks.loop(seconds=60)  # Regeneração de energia e expiração de buffs a cada minuto
    async def energy_regeneration(self):
        now = datetime.now().timestamp()
        # Iterate over a copy of keys to avoid RuntimeError: dictionary changed size during iteration if player_database is modified
        for user_id_str in list(player_database.keys()): #
            if not user_id_str.isdigit(): #
                print(f"AVISO: Chave inválida encontrada no player_database durante regeneração de energia: '{user_id_str}'. Ignorando.") #
                continue #
            user_id = int(user_id_str) #
            player_data = player_database[user_id_str] #

            # Regeneração de Energia
            if player_data.get("energy", 0) < MAX_ENERGY:
                player_data["energy"] = min(
                    MAX_ENERGY, player_data.get("energy", 0) + 1
                )

            # Verificação de Buffs/Transformações/Bênçãos que expiram
            # Iterar sobre ITEMS_DATA para bênçãos
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
                                pass  # Bot não pode enviar DM
                            except Exception as e:
                                print(
                                    f"Erro ao enviar DM sobre expiração de bênção para {user.name}: {e}"
                                )

            # Verificação de Transformações (campo current_transformation)
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
                            pass  # Bot não pode enviar DM
                        except Exception as e:
                            print(
                                f"Erro ao enviar DM sobre expiração de transformação para {user.name}: {e}"
                            )

        save_data()  # Salva as mudanças de energia e buffs para todos os jogadores

    @tasks.loop(minutes=5)  # Sincronização de cargos a cada 5 minutos
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
        # Iterate over a copy of keys to avoid RuntimeError: dictionary changed size during iteration if player_database is modified
        for member_id_str in list(player_database.keys()): #
            if not member_id_str.isdigit(): #
                print(f"AVISO: Chave inválida encontrada no player_database durante sincronização de cargos: '{member_id_str}'. Ignorando.") #
                continue #
            member_id = int(member_id_str) #
            player_data = player_database[member_id_str] #

            member = guild.get_member(member_id)

            if not member:
                continue

            if player_data.get("status") == "afk":
                continue

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

    @tasks.loop(hours=24 * CLAN_RANKING_INTERVAL_DAYS)  # Ranking de clãs
    async def weekly_clan_ranking(self):
        await self.wait_until_ready()
        print("Iniciando cálculo de ranking semanal de clãs...")

        if not clan_database:
            print("Nenhum clã para ranquear.")
            return

        active_clans = [
            clan
            for clan in clan_database.values()
            if clan["members"] and clan.get("xp", 0) > 0
        ]
        if not active_clans:
            print("Nenhum clã ativo para ranquear.")
            return

        sorted_clans = sorted(active_clans, key=lambda x: x.get("xp", 0), reverse=True)

        announcement_channel = None
        if ANNOUNCEMENT_CHANNEL_ID:
            announcement_channel = self.get_channel(int(ANNOUNCEMENT_CHANNEL_ID))

        if not announcement_channel:
            for guild in self.guilds:
                if guild.system_channel:
                    announcement_channel = guild.system_channel
                    break

        if not announcement_channel:
            print("Nenhum canal de anúncios encontrado para o ranking de clãs.")
            return

        embed = discord.Embed(
            title=f"{CUSTOM_EMOJIS.get('trophy_icon', '🏆')} Ranking Semanal de Clãs!",
            description="Parabéns aos clãs que se destacaram nesta semana!",
            color=discord.Color.gold(),
        )

        reward_messages = []

        for i, clan in enumerate(sorted_clans):
            if i >= 3:
                break

            rank = i + 1
            rewards = CLAN_RANK_REWARDS.get(rank, {"xp": 0, "money": 0})
            xp_reward = rewards["xp"]
            money_reward = rewards["money"]

            if xp_reward > 0 or money_reward > 0:
                embed.add_field(
                    name=f"#{rank} - {clan.get('name')}",
                    value=f"XP do Clã: {clan.get('xp',0):,}\nRecompensa para cada membro: {xp_reward:,} XP e ${money_reward:,}",
                    inline=False,
                )
                reward_messages.append(
                    f"O clã **{clan.get('name')}** ficou em #{rank} e seus membros receberão {xp_reward:,} XP e ${money_reward:,}!"
                )

                for member_id in clan["members"]:
                    player_data = get_player_data(member_id)
                    if player_data:
                        player_data["xp"] = player_data.get("xp", 0) + xp_reward
                        player_data["money"] = (
                            player_data.get("money", 0) + money_reward
                        )
                        # A lógica de level up agora é centralizada na função check_and_process_levelup_internal
                        try:
                            member_obj = await self.fetch_user(int(member_id))
                            if member_obj:
                                await self.check_and_process_levelup(
                                    member_obj,
                                    player_data,
                                    announcement_channel,
                                )
                            else:
                                print(
                                    f"Usuário {member_id} não encontrado para processar level up."
                                )
                        except discord.NotFound:
                            print(
                                f"Usuário {member_id} não encontrado para enviar mensagem de nível."
                            )
                        except Exception as e:
                            print(
                                f"Erro ao atualizar nível ou enviar mensagem para {member_id}: {e}"
                            )
                        save_data()  # Salva o progresso do jogador
                    else:
                        print(
                            f"Dados do jogador {member_id} não encontrados para recompensar."
                        )

            clan["xp"] = DEFAULT_CLAN_XP
            clan["money"] = 0
            clan["last_ranking_timestamp"] = int(datetime.now().timestamp())

        save_clan_data()

        if reward_messages:
            embed.set_footer(
                text="A XP e o dinheiro de todos os clãs foram resetados para o próximo ciclo de ranking."
            )
            await announcement_channel.send(embed=embed)
            for msg in reward_messages:
                await announcement_channel.send(msg)
        else:
            await announcement_channel.send(
                "Nenhum clã se qualificou para recompensas esta semana."
            )

        print("Cálculo de ranking semanal de clãs concluído.")

    @weekly_clan_ranking.before_loop
    async def before_weekly_clan_ranking(self):
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