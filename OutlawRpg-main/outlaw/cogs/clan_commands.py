import discord
from discord.ext import commands, tasks
from discord import app_commands, ui
import uuid
import time
from typing import Optional
from datetime import datetime, time as dt_time, timedelta

import data_manager
import config
from utils import (
    display_money,
)


# Constantes para o sistema de recompensa
REWARD_WEEKDAY = 2  # 0=Segunda, 1=Terça, 2=Quarta-feira
REWARD_TIME = dt_time(22, 20)  # 22:20
REWARD_COOLDOWN_DAYS = 6  # Garante que a recompensa seja dada apenas uma vez por semana


# --- Views para interações com botões ---
class DistributeMoneyConfirmView(discord.ui.View):
    def __init__(self, cog, clan_id: str):
        super().__init__(timeout=60)  # Botão expira após 60 segundos
        self.cog = cog
        self.clan_id = clan_id
        self.message = None  # Para armazenar a mensagem original e desabilitar o botão

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(
                content="A ação de distribuição de dinheiro expirou.", view=self
            )

    @discord.ui.button(
        label="Confirmar Distribuição", style=discord.ButtonStyle.green, emoji="💰"
    )
    async def confirm_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # Verifica se o usuário que clicou é o líder do clã
        player_id = str(interaction.user.id)
        clan_data = data_manager.clan_database.get(self.clan_id)

        # Verificação mais robusta para leader
        if not clan_data or clan_data.get("leader") != player_id:
            await interaction.response.send_message(
                "Você não é o líder deste clã para executar esta ação.", ephemeral=True
            )
            return

        # Desabilita o botão imediatamente para evitar múltiplos cliques
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            view=self
        )  # Atualiza a mensagem para desabilitar

        # Envia uma mensagem temporária de "processando" para melhor UX
        await interaction.followup.send("Processando distribuição...", ephemeral=True)

        # Chamada da nova função de distribuição
        await self.cog._distribute_clan_money(interaction, clan_data)

        # Remove a view da mensagem, se desejar que ela desapareça completamente após a ação
        if self.message:
            await self.message.edit(view=None)


class ClanCommands(commands.Cog):
    """Uma cog para lidar com todos os comandos e lógicas de clã."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Initialize _last_reward_check_date to None
        self._last_reward_check_date = None
        self.distribute_weekly_rewards.start()

    def cog_unload(self):
        self.distribute_weekly_rewards.cancel()

    # Define o grupo de comandos para clãs
    clan = app_commands.Group(name="clan", description="Comandos relacionados a clãs.")

    # --- MÉTODOS AUXILIARES ---

    async def _find_clan_by_name(self, name: str) -> Optional[dict]:
        """Encontra um clã pelo seu nome (sem diferenciar maiúsculas/minúsculas)."""
        name_lower = name.lower()
        for clan_data in data_manager.clan_database.values():
            if clan_data["name"].lower() == name_lower:
                return clan_data
        return None

    async def _get_user_display_name(self, user_id: int) -> str:
        """Busca com segurança o nome de exibição de um usuário, tratando possíveis erros."""
        try:
            # Tenta pegar da cache primeiro para eficiência
            user = self.bot.get_user(user_id)
            if user:
                return user.display_name

            # Se não estiver na cache, tenta buscar via API
            user = await self.bot.fetch_user(user_id)
            return user.display_name
        except discord.NotFound:
            return "Usuário Desconhecido"
        except discord.HTTPException:
            return "Erro ao Buscar Usuário"
        except Exception as e:
            print(f"Erro inesperado em _get_user_display_name para {user_id}: {e}")
            return "Erro Interno"

    # --- TAREFA DE RECOMPENSA SEMANAL ---

    async def _process_clan_rewards(self):
        """Lógica central para processar e distribuir as recompensas dos clãs."""
        rewarded_clans = []
        channel_id = config.CLAN_REWARD_ANNOUNCEMENT_CHANNEL_ID
        announcement_channel = self.bot.get_channel(channel_id)

        if not announcement_channel:
            print(
                f"ERRO: Canal de anúncios de recompensa (ID: {channel_id}) não encontrado."
            )
            return

        for clan_id, clan_data in data_manager.clan_database.items():
            # Pula clãs sem membros ou com XP 0, para não processar clãs inativos para ranking semanal
            if not clan_data.get("members") or clan_data.get("xp", 0) == 0:
                continue

            now_ts = int(time.time())
            last_reward_ts = clan_data.get("last_ranking_timestamp", 0)

            # Garante que a recompensa seja dada apenas uma vez por semana
            if (now_ts - last_reward_ts) < timedelta(
                days=REWARD_COOLDOWN_DAYS
            ).total_seconds():
                continue

            # --- LÓGICA DE RECOMPENSA (CUSTOMIZE AQUI!) ---
            # Ensure 'members' is a list before using len()
            num_members = len(clan_data.get("members", []))
            money_reward = num_members * 1000
            xp_reward = num_members * 50

            clan_data["money"] = clan_data.get("money", 0) + money_reward
            clan_data["xp"] = (
                clan_data.get("xp", 0) + xp_reward
            )  # Incrementa XP antes de resetar

            # --- Importante: Reinicia o XP e o last_ranking_timestamp para o próximo ciclo
            clan_data["last_ranking_timestamp"] = now_ts
            clan_data["xp"] = (
                config.DEFAULT_CLAN_XP
            )  # Reseta o XP do clã para o próximo ranking
            # O dinheiro do clã NÃO é resetado aqui porque ele é gerenciado pela distribuição manual ou pelo líder.

            rewarded_clans.append(
                {"name": clan_data["name"], "money": money_reward, "xp": xp_reward}
            )

        if rewarded_clans:
            data_manager.save_clan_data()

            embed = discord.Embed(
                title="🏆 Recompensas Semanais de Clãs Distribuídas!",
                description="Os clãs foram recompensados por sua atividade na última semana!",
                color=discord.Color.gold(),
            )
            for clan_info in rewarded_clans:
                embed.add_field(
                    name=f"🛡️ {clan_info['name']}",
                    value=f"💰 **Recebeu:** {display_money(clan_info['money'])}\n✨ **Ganhou:** {clan_info['xp']:,} XP",
                    inline=False,
                )
            embed.set_footer(text="A próxima recompensa será na próxima quarta-feira!")
            await announcement_channel.send(embed=embed)
        else:
            print(
                "Verificação de recompensas semanais concluída. Nenhum clã elegível no momento."
            )

    @tasks.loop(hours=1)
    async def distribute_weekly_rewards(self):
        await self.bot.wait_until_ready()

        now = datetime.now()

        # Condição para executar apenas no dia e hora específicos, e uma vez por semana
        if now.weekday() == REWARD_WEEKDAY and now.time() >= REWARD_TIME:
            # Verifica se já foi processado hoje para evitar múltiplos envios no mesmo dia
            # Isso é uma redundância se REWARD_COOLDOWN_DAYS for > 0, mas garante
            # que não haja envios duplicados no mesmo minuto da hora alvo.
            last_check_date = getattr(self, "_last_reward_check_date", None)
            if last_check_date is None or last_check_date < now.date():
                print("Condições de recompensa semanal atendidas. Processando clãs...")
                await self._process_clan_rewards()
                self._last_reward_check_date = now.date()

    # --- FUNÇÃO AUXILIAR PARA DISTRIBUIR O DINHEIRO MANUALMENTE ---
    async def _distribute_clan_money(
        self, interaction: discord.Interaction, clan_data: dict
    ):
        clan_money = clan_data.get("money", 0)  # Usa .get() para segurança

        # Filtra membros válidos (não AFK, não mortos, e que existam)
        eligible_members = []
        for member_id_str in clan_data.get("members", []):  # Usa .get() para segurança
            player_data = data_manager.get_player_data(member_id_str)
            # Verifica se o jogador existe e não está "afk" ou "dead"
            if player_data and player_data.get("status") not in ["afk", "dead"]:
                eligible_members.append((member_id_str, player_data))

        if not eligible_members:
            await interaction.followup.send(
                f"Nenhum membro elegível no clã **{clan_data['name']}** para receber dinheiro. A distribuição foi cancelada.",
                ephemeral=True,
            )
            return

        if clan_money <= 0:
            await interaction.followup.send(
                f"A tesouraria do clã **{clan_data['name']}** está vazia. Não há dinheiro para distribuir.",
                ephemeral=True,
            )
            return

        money_per_member = clan_money // len(eligible_members)
        remainder_money = clan_money % len(
            eligible_members
        )  # Caso o dinheiro não seja divisível igualmente

        distributed_amounts = {}
        for member_id_str, player_data in eligible_members:
            amount_to_give = money_per_member
            if remainder_money > 0:  # Distribui o restante para os primeiros membros
                amount_to_give += 1
                remainder_money -= 1

            player_data["money"] = player_data.get("money", 0) + amount_to_give
            distributed_amounts[member_id_str] = amount_to_give

        clan_data["money"] = 0  # Zera a tesouraria do clã após a distribuição
        data_manager.save_clan_data()
        data_manager.save_data()  # Salva o progresso dos jogadores

        # Embed final de sucesso para a distribuição
        embed = discord.Embed(
            title=f"💰 Dinheiro do Clã '{clan_data['name']}' Distribuído!",
            description=f"A tesouraria de **{display_money(clan_money)}** foi dividida entre {len(eligible_members)} membros elegíveis.",
            color=discord.Color.green(),
        )

        # Adiciona campos para os valores distribuídos, limitando para não exceder o limite de campos do embed
        sorted_distributed_amounts = sorted(
            distributed_amounts.items(), key=lambda item: item[1], reverse=True
        )
        count = 0
        for member_id_str, amount in sorted_distributed_amounts:
            if count >= 25:  # Limite do Discord para fields em um embed
                embed.add_field(
                    name="...", value="E mais membros receberam dinheiro.", inline=False
                )
                break
            member_name = await self._get_user_display_name(int(member_id_str))
            embed.add_field(name=member_name, value=display_money(amount), inline=True)
            count += 1

        embed.set_footer(text="Tesouraria do clã zerada para a próxima arrecadação.")
        await interaction.followup.send(embed=embed)

    # --- COMANDOS (agora como subcomandos do grupo 'clan') ---

    @clan.command(name="criar", description="Cria um novo clã.")
    @app_commands.describe(nome="O nome do clã que você deseja criar.")
    async def create(self, interaction: discord.Interaction, nome: str):
        await interaction.response.defer(ephemeral=True)

        player_id = str(interaction.user.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data:
            await interaction.followup.send(
                "Você precisa criar seu personagem primeiro! Use `/personagem criar`.",
                ephemeral=True,
            )
            return

        if player_data.get("clan_id"):
            clan_id_of_player = player_data["clan_id"]
            existing_clan_data = data_manager.clan_database.get(clan_id_of_player)
            if existing_clan_data:
                clan_name = existing_clan_data["name"]
                await interaction.followup.send(
                    f"Você já faz parte do clã **{clan_name}**.", ephemeral=True
                )
                return
            else:
                # Caso o player_data tenha um clan_id, mas o clã não exista mais no banco de dados.
                # Isso limpa o dado inconsistente do jogador.
                player_data["clan_id"] = None
                data_manager.save_data()
                await interaction.followup.send(
                    "Seu registro de clã estava inconsistente e foi corrigido. Por favor, tente criar novamente.",
                    ephemeral=True,
                )
                return

        if await self._find_clan_by_name(nome):
            await interaction.followup.send(
                f"Já existe um clã com o nome '{nome}'. Escolha outro nome.",
                ephemeral=True,
            )
            return

        if len(nome) < 3 or len(nome) > 20:
            await interaction.followup.send(
                "O nome do clã deve ter entre 3 e 20 caracteres.", ephemeral=True
            )
            return

        if not nome.replace(" ", "").isalnum():
            await interaction.followup.send(
                "O nome do clã pode conter espaços, mas apenas letras e números. Caracteres especiais não são permitidos.",
                ephemeral=True,
            )
            return

        cost = config.CLAN_CREATION_COST
        if player_data["money"] < cost:
            await interaction.followup.send(
                f"Você não tem dinheiro suficiente para criar um clã. Você precisa de {display_money(cost)}.",
                ephemeral=True,
            )
            return

        clan_id = str(uuid.uuid4())
        new_clan = {
            "id": clan_id,
            "name": nome,
            "leader": player_id,
            "members": [player_id],
            "money": 0,
            "xp": config.DEFAULT_CLAN_XP,
            "created_at": int(time.time()),
            "last_ranking_timestamp": 0,
        }

        data_manager.clan_database[clan_id] = new_clan
        player_data["clan_id"] = clan_id
        data_manager.save_clan_data()
        data_manager.save_data()

        embed = discord.Embed(
            title=f"🛡️ Clã '{nome}' Criado!",
            description=f"Parabéns, {interaction.user.display_name}! Você é o líder do novo clã **{nome}**.",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Custo", value=f"-{display_money(cost)}", inline=True)
        embed.set_footer(text="Use /clan info para ver os detalhes do seu clã.")
        await interaction.followup.send(embed=embed)

    @clan.command(name="entrar", description="Entra em um clã existente.")
    @app_commands.describe(nome="O nome do clã ao qual você deseja se juntar.")
    async def join(self, interaction: discord.Interaction, nome: str):
        await interaction.response.defer(ephemeral=True)

        player_id = str(interaction.user.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data:
            await interaction.followup.send(
                "Você precisa criar seu personagem primeiro! Use `/personagem criar`.",
                ephemeral=True,
            )
            return

        if player_data.get("clan_id"):
            clan_id_of_player = player_data["clan_id"]
            existing_clan_data = data_manager.clan_database.get(clan_id_of_player)
            if existing_clan_data:
                clan_name = existing_clan_data["name"]
                await interaction.followup.send(
                    f"Você já faz parte do clã **{clan_name}**.", ephemeral=True
                )
                return
            else:
                # Limpa o clan_id inconsistente do jogador
                player_data["clan_id"] = None
                data_manager.save_data()
                await interaction.followup.send(
                    "Seu registro de clã estava inconsistente e foi corrigido. Por favor, tente entrar novamente.",
                    ephemeral=True,
                )
                return

        clan_data = await self._find_clan_by_name(nome)
        if not clan_data:
            await interaction.followup.send(
                f"Clã '{nome}' não encontrado.", ephemeral=True
            )
            return

        # Melhoria de segurança: Garante que 'members' é uma lista
        if not isinstance(clan_data.get("members"), list):
            clan_data["members"] = []  # Reseta para uma lista vazia se for inválido
            data_manager.save_clan_data()  # Salva a correção
            await interaction.followup.send(
                "Houve um erro com os dados do clã. Tente novamente em breve.",
                ephemeral=True,
            )
            return

        if len(clan_data["members"]) >= config.MAX_CLAN_MEMBERS:
            await interaction.followup.send(
                f"O clã **{clan_data['name']}** está cheio. Ele já atingiu o limite de {config.MAX_CLAN_MEMBERS} membros.",
                ephemeral=True,
            )
            return

        clan_data["members"].append(player_id)
        player_data["clan_id"] = clan_data["id"]
        data_manager.save_clan_data()
        data_manager.save_data()

        embed = discord.Embed(
            title=f"🎉 Entrou no Clã '{clan_data['name']}'!",
            description=f"Bem-vindo(a) ao clã **{clan_data['name']}**, {interaction.user.display_name}!",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Use /clan info para ver os detalhes do seu clã.")
        await interaction.followup.send(embed=embed)

        # Notifica o líder
        leader_id = clan_data.get("leader")  # Usa .get() aqui também
        if leader_id:
            leader = self.bot.get_user(int(leader_id))
            if leader:
                try:
                    await leader.send(
                        f"👥 {interaction.user.display_name} se juntou ao seu clã, **{clan_data['name']}**!"
                    )
                except discord.Forbidden:
                    pass  # Não pode enviar DM, ignora

    @clan.command(name="sair", description="Sai do seu clã atual.")
    async def leave(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        player_id = str(interaction.user.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data or not player_data.get("clan_id"):
            await interaction.followup.send(
                "Você não faz parte de nenhum clã.", ephemeral=True
            )
            return

        clan_id = player_data["clan_id"]
        clan_data = data_manager.clan_database.get(clan_id)

        if not clan_data:
            player_data["clan_id"] = None
            data_manager.save_data()
            await interaction.followup.send(
                "Erro: O clã ao qual você estava vinculado não existe mais. Seu registro foi atualizado.",
                ephemeral=True,
            )
            return

        leader_id = clan_data.get("leader")  # Usa .get()
        if leader_id == player_id:
            if len(clan_data.get("members", [])) == 1:  # Usa .get() para 'members'
                del data_manager.clan_database[clan_id]
                player_data["clan_id"] = None
                data_manager.save_clan_data()
                data_manager.save_data()
                await interaction.followup.send(
                    f"Você saiu do clã **{clan_data['name']}** e, como era o último membro, o clã foi dissolvido. 💔",
                    ephemeral=True,
                )
                return
            else:
                await interaction.followup.send(
                    "Como líder, você não pode simplesmente sair do clã. Por favor, transfira a liderança para outro membro usando `/clan transferir` antes de sair.",
                    ephemeral=True,
                )
                return

        # Garante que 'members' é uma lista e que o player_id está nela antes de tentar remover
        if (
            not isinstance(clan_data.get("members"), list)
            or player_id not in clan_data["members"]
        ):
            player_data["clan_id"] = None  # Remove o vínculo inconsistente do jogador
            data_manager.save_data()
            await interaction.followup.send(
                "Você não parece ser um membro válido deste clã. Seu registro foi corrigido.",
                ephemeral=True,
            )
            return

        clan_data["members"].remove(player_id)
        player_data["clan_id"] = None
        data_manager.save_clan_data()
        data_manager.save_data()

        embed = discord.Embed(
            title=f"🚶 Saiu do Clã '{clan_data['name']}'",
            description=f"Você saiu do clã **{clan_data['name']}**.",
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed)

        # Notificar o líder
        if leader_id and leader_id != player_id:
            leader = self.bot.get_user(int(leader_id))
            if leader:
                try:
                    await leader.send(
                        f"💔 {interaction.user.display_name} saiu do seu clã, **{clan_data['name']}**."
                    )
                except discord.Forbidden:
                    pass

    @clan.command(
        name="info", description="Exibe informações sobre o seu clã ou outro clã."
    )
    @app_commands.describe(nome="Opcional: O nome do clã para ver as informações.")
    async def info(self, interaction: discord.Interaction, nome: Optional[str] = None):
        await interaction.response.defer(ephemeral=False)

        player_id = str(interaction.user.id)
        player_data = data_manager.get_player_data(player_id)

        clan_data = None
        if nome:
            clan_data = await self._find_clan_by_name(nome)
            if not clan_data:
                await interaction.followup.send(
                    f"Clã '{nome}' não encontrado.", ephemeral=True
                )
                return
        elif player_data and player_data.get("clan_id"):
            clan_data = data_manager.clan_database.get(player_data["clan_id"])
            if not clan_data:
                # Dados inconsistentes, limpa o clan_id do jogador
                player_data["clan_id"] = None
                data_manager.save_data()
                await interaction.followup.send(
                    "Erro: O clã ao qual você estava vinculado não existe mais. Seu registro foi atualizado.",
                    ephemeral=True,
                )
                return
        else:
            await interaction.followup.send(
                "Você não faz parte de nenhum clã. Use `/clan entrar <nome_do_cla>` ou `/clan criar <nome_do_cla>`.",
                ephemeral=True,
            )
            return

        # TRATAMENTO PARA KeyError: 'leader', 'members', 'money', 'xp', 'created_at'
        leader_id = clan_data.get("leader")
        if not leader_id:
            leader_name = "Líder Desconhecido (Dados Corrompidos)"
            # Tenta encontrar um líder entre os membros se não houver um 'leader' explícito
            if clan_data.get("members"):
                leader_name = (
                    await self._get_user_display_name(int(clan_data["members"][0]))
                    + " (Líder Padrão)"
                )
        else:
            leader_name = await self._get_user_display_name(int(leader_id))

        member_ids = clan_data.get(
            "members", []
        )  # Garante que é uma lista vazia se 'members' não existir
        member_names = []
        for member_id in member_ids:
            member_names.append(await self._get_user_display_name(int(member_id)))

        # Ordenar membros e líderes para exibição
        # Evita adicionar "Líder Desconhecido" na lista de membros normais se for um fallback
        display_members = [
            name
            for name in member_names
            if name != leader_name
            and name
            != (await self._get_user_display_name(int(leader_id)) if leader_id else "")
        ]
        display_members_sorted = sorted(display_members)

        members_list_str = f"👑 {leader_name} (Líder)\n" + "\n".join(
            [f"👤 {m}" for m in display_members_sorted]
        )
        if (
            not members_list_str.strip()
        ):  # Se a string ainda estiver vazia ou só com o líder
            members_list_str = "Nenhum membro."
        elif len(member_ids) == 0:
            members_list_str = "Nenhum membro."

        embed = discord.Embed(
            title=f"🛡️ Informações do Clã: {clan_data.get('name', 'Clã Desconhecido')}",  # Usa .get() para 'name'
            color=discord.Color.blue(),
            timestamp=datetime.fromtimestamp(
                clan_data.get("created_at", time.time())
            ),  # Usa .get() para 'created_at'
        )
        embed.add_field(
            name="ID do Clã", value=clan_data.get("id", "N/A"), inline=False
        )
        embed.add_field(
            name="💰 Tesouraria do Clã",
            value=display_money(clan_data.get("money", 0)),
            inline=True,
        )
        embed.add_field(
            name="✨ XP do Clã", value=f"{clan_data.get('xp', 0):,}", inline=True
        )
        embed.add_field(
            name="👥 Membros",
            value=f"{len(member_ids)}/{config.MAX_CLAN_MEMBERS}",
            inline=True,
        )
        embed.add_field(
            name="Membros Atuais",
            value=members_list_str,
            inline=False,
        )

        embed.set_footer(text="Criado em")
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="ranking_clans", description="Exibe o ranking dos clãs mais fortes."
    )
    async def ranking_clans(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        if not data_manager.clan_database:
            await interaction.followup.send(
                "Não há clãs para exibir no ranking ainda.", ephemeral=True
            )
            return

        sorted_clans = sorted(
            data_manager.clan_database.values(),
            key=lambda x: x.get("xp", 0),  # Usa .get() para XP
            reverse=True,
        )

        embed = discord.Embed(
            title="🏆 Ranking dos Clãs Mais Fortes 🏆",
            description="Os clãs são rankeados por XP! Veja os 10 melhores:",
            color=discord.Color.gold(),
        )

        if not sorted_clans:
            embed.description = "Nenhum clã para ranquear."
        else:
            for i, clan_data in enumerate(sorted_clans[:10]):
                leader_id = clan_data.get("leader")
                leader_name = "Líder Desconhecido"  # Default value

                if leader_id:
                    leader_name = await self._get_user_display_name(int(leader_id))
                elif clan_data.get("members"):
                    # Fallback: if 'leader' is missing, try to use the first member
                    # Ensure 'members' is a list and not empty before trying to access index 0
                    if (
                        isinstance(clan_data.get("members"), list)
                        and clan_data["members"]
                    ):
                        first_member_id = clan_data["members"][0]
                        leader_name = (
                            await self._get_user_display_name(int(first_member_id))
                            + " (Líder Padrão)"
                        )
                # else, it remains "Líder Desconhecido" if no leader_id and no members

                embed.add_field(
                    name=f"#{i + 1} - {clan_data.get('name', 'Clã Desconhecido')}",
                    value=(
                        f"Líder: {leader_name}\n"
                        f"Membros: {len(clan_data.get('members', []))}\n"
                        f"XP: {clan_data.get('xp', 0):,}\n"
                        f"Dinheiro: {display_money(clan_data.get('money', 0))}"
                    ),
                    inline=False,
                )
        await interaction.followup.send(embed=embed)

    @clan.command(
        name="expulsar",
        description="[LÍDER DO CLÃ] Expulsa um membro do seu clã.",
    )
    @app_commands.describe(membro="O membro a ser expulso do clã.")
    async def kick(self, interaction: discord.Interaction, membro: discord.Member):
        await interaction.response.defer(ephemeral=True)

        player_id = str(interaction.user.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data or not player_data.get("clan_id"):
            await interaction.followup.send(
                "Você não faz parte de nenhum clã.", ephemeral=True
            )
            return

        clan_id = player_data["clan_id"]
        clan_data = data_manager.clan_database.get(clan_id)

        if not clan_data or clan_data.get("leader") != player_id:  # Usa .get()
            await interaction.followup.send(
                "Você não é o líder deste clã.", ephemeral=True
            )
            return

        target_id = str(membro.id)
        if target_id == player_id:
            await interaction.followup.send(
                "Você não pode expulsar a si mesmo!", ephemeral=True
            )
            return

        # Garante que 'members' é uma lista e que o target_id está nela
        if (
            not isinstance(clan_data.get("members"), list)
            or target_id not in clan_data["members"]
        ):
            await interaction.followup.send(
                f"**{membro.display_name}** não é um membro do seu clã.",
                ephemeral=True,
            )
            return

        clan_data["members"].remove(target_id)

        target_player_data = data_manager.get_player_data(target_id)
        if target_player_data:
            target_player_data["clan_id"] = None

        data_manager.save_clan_data()
        data_manager.save_data()

        embed = discord.Embed(
            title="🚫 Membro Expulso",
            description=f"**{membro.display_name}** foi expulso do clã **{clan_data['name']}**.",
            color=discord.Color.red(),
        )
        await interaction.followup.send(embed=embed)

        try:
            await membro.send(
                f"Você foi expulso do clã **{clan_data['name']}** pelo líder {interaction.user.display_name}."
            )
        except discord.Forbidden:
            pass

    @clan.command(
        name="transferir",
        description="[LÍDER DO CLÃ] Transfere a liderança do clã para outro membro.",
    )
    @app_commands.describe(
        novo_lider="O membro para quem você deseja transferir a liderança."
    )
    async def transfer_leadership(
        self, interaction: discord.Interaction, novo_lider: discord.Member
    ):
        await interaction.response.defer(ephemeral=True)

        player_id = str(interaction.user.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data or not player_data.get("clan_id"):
            await interaction.followup.send(
                "Você não faz parte de nenhum clã.", ephemeral=True
            )
            return

        clan_id = player_data["clan_id"]
        clan_data = data_manager.clan_database.get(clan_id)

        if not clan_data or clan_data.get("leader") != player_id:  # Usa .get()
            await interaction.followup.send(
                "Você não é o líder deste clã.", ephemeral=True
            )
            return

        new_leader_id = str(novo_lider.id)
        if new_leader_id == player_id:
            await interaction.followup.send("Você já é o líder!", ephemeral=True)
            return

        # Garante que 'members' é uma lista e que o novo_lider_id está nela
        if (
            not isinstance(clan_data.get("members"), list)
            or new_leader_id not in clan_data["members"]
        ):
            await interaction.followup.send(
                f"**{novo_lider.display_name}** não é um membro do seu clã.",
                ephemeral=True,
            )
            return

        old_leader_name = interaction.user.display_name
        new_leader_name = novo_lider.display_name

        clan_data["leader"] = new_leader_id
        data_manager.save_clan_data()

        embed = discord.Embed(
            title="👑 Liderança Transferida!",
            description=(
                f"**{new_leader_name}** é o novo líder do clã **{clan_data['name']}**.\n"
                f"Obrigado, {old_leader_name}, por sua liderança!"
            ),
            color=discord.Color.gold(),
        )
        await interaction.followup.send(embed=embed)

        try:
            await novo_lider.send(
                f"Parabéns! Você é o novo líder do clã **{clan_data['name']}**!"
            )
        except discord.Forbidden:
            pass

    @app_commands.command(
        name="forcar_recompensa",
        description="[DONO] Força a distribuição de recompensas semanais.",
    )
    @commands.is_owner()
    async def forcar_recompensa(self, ctx: discord.Interaction):
        await ctx.response.defer(ephemeral=True)
        try:
            # Força o _last_reward_check_date para None para garantir a execução
            self._last_reward_check_date = None
            await self._process_clan_rewards()
            await ctx.followup.send(
                "Distribuição de recompensas forçada com sucesso!", ephemeral=True
            )
        except Exception as e:
            print(f"Erro ao forçar recompensa: {e}")
            await ctx.followup.send(f"Ocorreu um erro: {e}", ephemeral=True)

    # --- COMANDO: DISTRIBUIR DINHEIRO DO CLÃ ---
    @clan.command(
        name="distribuir",
        description="[LÍDER DO CLÃ] Distribui o dinheiro da tesouraria do clã entre os membros.",
    )
    async def distribute_money(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        player_id = str(interaction.user.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data or not player_data.get("clan_id"):
            await interaction.followup.send(
                "Você não faz parte de nenhum clã.", ephemeral=True
            )
            return

        clan_id = player_data["clan_id"]
        clan_data = data_manager.clan_database.get(clan_id)

        if not clan_data or clan_data.get("leader") != player_id:  # Usa .get()
            await interaction.followup.send(
                "Você não é o líder deste clã para usar este comando.", ephemeral=True
            )
            return

        if clan_data.get("money", 0) <= 0:  # Usa .get()
            await interaction.followup.send(
                f"A tesouraria do clã **{clan_data['name']}** está vazia. Não há dinheiro para distribuir.",
                ephemeral=True,
            )
            return

        # Cria a view com o botão
        view = DistributeMoneyConfirmView(self, clan_id)

        # Envia a mensagem com o botão
        message = await interaction.followup.send(
            f"💰 Líder, você tem **{display_money(clan_data.get('money', 0))}** na tesouraria do clã **{clan_data['name']}**.\n"
            "Clique no botão abaixo para distribuir este dinheiro igualmente entre os membros elegíveis.",
            view=view,
            ephemeral=True,
        )
        view.message = message


async def setup(bot: commands.Bot):
    """Adiciona a ClanCommands cog ao bot."""
    await bot.add_cog(ClanCommands(bot))
