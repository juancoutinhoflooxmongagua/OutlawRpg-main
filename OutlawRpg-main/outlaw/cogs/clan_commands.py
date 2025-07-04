# cogs/clan_commands.py
import discord
from discord.ext import commands
from discord import app_commands  # <- MUDANÇA 1: Importar app_commands
import uuid
import time
from typing import Optional

# Assumindo que esses módulos estão na raiz do projeto ou em um caminho acessível
import data_manager
import config
from utils import display_money


class ClanCommands(commands.Cog):
    """Uma cog para lidar com todos os comandos e lógicas de clã."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
            for guild in self.bot.guilds:
                member = guild.get_member(user_id)
                if member:
                    return member.display_name

            user = await self.bot.fetch_user(user_id)
            return user.display_name
        except discord.NotFound:
            return "Usuário Desconhecido"
        except discord.HTTPException:
            return "Erro ao Buscar Usuário"

    # --- COMANDOS ---

    # v MUDANÇA 2: Alterado de @commands.slash_command para @app_commands.command
    @app_commands.command(name="criar_cla", description="Cria um novo clã.")
    async def criar_cla(
        self, ctx: discord.Interaction, nome: str
    ):  # <- MUDANÇA 3: Alterado o tipo do ctx
        """Permite que um jogador crie um novo clã se atender aos requisitos."""
        player_id = str(ctx.user.id)  # Em discord.Interaction, o autor é ctx.user
        player_data = data_manager.get_player_data(player_id)

        if not player_data:
            return await ctx.response.send_message(
                "Você precisa criar um personagem primeiro! Use `/criar_personagem`.",
                ephemeral=True,
            )
        if player_data.get("clan_id"):
            return await ctx.response.send_message(
                "Você já faz parte de um clã. Saia do clã atual antes de criar um novo.",
                ephemeral=True,
            )
        if not (3 <= len(nome) <= 20):
            return await ctx.response.send_message(
                "O nome do clã deve ter entre 3 e 20 caracteres.", ephemeral=True
            )
        if player_data["money"] < config.CLAN_CREATION_COST:
            return await ctx.response.send_message(
                f"Você precisa de {display_money(config.CLAN_CREATION_COST)} para criar um clã. Você tem {display_money(player_data['money'])}.",
                ephemeral=True,
            )

        if await self._find_clan_by_name(nome):
            return await ctx.response.send_message(
                f"Já existe um clã com o nome '{nome}'. Por favor, escolha outro nome.",
                ephemeral=True,
            )

        clan_id = str(uuid.uuid4())
        timestamp = int(time.time())

        new_clan = {
            "id": clan_id,
            "name": nome,
            "leader_id": player_id,
            "members": [player_id],
            "xp": config.DEFAULT_CLAN_XP,
            "money": config.INITIAL_CLAN_DATA["money"],
            "creation_timestamp": timestamp,
            "last_ranking_timestamp": timestamp,
        }

        data_manager.clan_database[clan_id] = new_clan
        player_data.update({"clan_id": clan_id, "clan_role": "Líder"})
        player_data["money"] -= config.CLAN_CREATION_COST

        data_manager.save_data()
        data_manager.save_clan_data()

        embed = discord.Embed(
            title=f"{config.CUSTOM_EMOJIS.get('clan_icon', '🛡️')} Clã Criado!",
            description=f"O clã **{nome}** foi criado com sucesso por {ctx.user.mention}!",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Custo", value=display_money(config.CLAN_CREATION_COST), inline=True
        )
        embed.add_field(name="Líder", value=ctx.user.display_name, inline=True)
        embed.add_field(
            name="Membros", value=f"1/{config.MAX_CLAN_MEMBERS}", inline=True
        )
        embed.set_footer(text="Aventure-se com seu novo clã!")

        await ctx.response.send_message(
            embed=embed
        )  # Em discord.Interaction, a resposta é ctx.response.send_message

    @app_commands.command(name="entrar_cla", description="Entra em um clã existente.")
    async def entrar_cla(self, ctx: discord.Interaction, nome_do_cla: str):
        player_id = str(ctx.user.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data:
            return await ctx.response.send_message(
                "Você precisa criar um personagem primeiro! Use `/criar_personagem`.",
                ephemeral=True,
            )
        if player_data.get("clan_id"):
            return await ctx.response.send_message(
                "Você já faz parte de um clã.", ephemeral=True
            )

        clan_data = await self._find_clan_by_name(nome_do_cla)
        if not clan_data:
            return await ctx.response.send_message(
                f"Clã '{nome_do_cla}' não encontrado.", ephemeral=True
            )

        if len(clan_data["members"]) >= config.MAX_CLAN_MEMBERS:
            return await ctx.response.send_message(
                f"O clã **{clan_data['name']}** está cheio.", ephemeral=True
            )

        clan_data["members"].append(player_id)
        player_data["clan_id"] = clan_data["id"]
        player_data["clan_role"] = "Membro"

        data_manager.save_data()
        data_manager.save_clan_data()

        embed = discord.Embed(
            title=f"{config.CUSTOM_EMOJIS.get('clan_icon', '🛡️')} Entrou no Clã!",
            description=f"{ctx.user.mention} entrou para o clã **{clan_data['name']}**!",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Membros Atuais",
            value=f"{len(clan_data['members'])}/{config.MAX_CLAN_MEMBERS}",
        )
        await ctx.response.send_message(embed=embed)

    @app_commands.command(name="sair_cla", description="Sai do seu clã atual.")
    async def sair_cla(self, ctx: discord.Interaction):
        player_id = str(ctx.user.id)
        player_data = data_manager.get_player_data(player_id)
        clan_id = player_data.get("clan_id") if player_data else None

        if not clan_id:
            return await ctx.response.send_message(
                "Você não faz parte de nenhum clã.", ephemeral=True
            )

        clan_data = data_manager.clan_database.get(clan_id)
        if not clan_data:
            player_data.update({"clan_id": None, "clan_role": None})
            data_manager.save_data()
            return await ctx.response.send_message(
                "Erro: Seu clã não foi encontrado. Seus dados foram corrigidos.",
                ephemeral=True,
            )

        clan_name = clan_data["name"]
        player_data.update({"clan_id": None, "clan_role": None})
        clan_data["members"].remove(player_id)

        response_embed = None
        if clan_data["leader_id"] == player_id:
            if not clan_data["members"]:
                del data_manager.clan_database[clan_id]
                response_embed = discord.Embed(
                    title=f"🛡️ Clã Dissolvido!",
                    description=f"{ctx.user.mention} saiu do clã **{clan_name}** e, como era o último membro, o clã foi dissolvido.",
                    color=discord.Color.red(),
                )
            else:
                new_leader_id = clan_data["members"][0]
                clan_data["leader_id"] = new_leader_id
                new_leader_data = data_manager.get_player_data(new_leader_id)
                if new_leader_data:
                    new_leader_data["clan_role"] = "Líder"
                response_embed = discord.Embed(
                    title=f"👑 Liderança Transferida!",
                    description=f"{ctx.user.mention} saiu. A liderança foi transferida para <@{new_leader_id}>.",
                    color=discord.Color.orange(),
                )
        else:
            response_embed = discord.Embed(
                title=f"🛡️ Saiu do Clã!",
                description=f"{ctx.user.mention} saiu do clã **{clan_name}**.",
                color=discord.Color.blue(),
            )

        data_manager.save_data()
        data_manager.save_clan_data()
        await ctx.response.send_message(embed=response_embed)

    @app_commands.command(
        name="info_cla", description="Exibe informações sobre um clã."
    )
    async def info_cla(
        self, ctx: discord.Interaction, nome_do_cla: Optional[str] = None
    ):
        clan_data = None
        if nome_do_cla:
            clan_data = await self._find_clan_by_name(nome_do_cla)
        else:
            player_data = data_manager.get_player_data(str(ctx.user.id))
            if player_data and player_data.get("clan_id"):
                clan_data = data_manager.clan_database.get(player_data["clan_id"])
            else:
                return await ctx.response.send_message(
                    "Você não está em um clã. Especifique o nome de um.", ephemeral=True
                )

        if not clan_data:
            return await ctx.response.send_message(
                f"Clã '{nome_do_cla}' não encontrado.", ephemeral=True
            )

        leader_name = await self._get_user_display_name(int(clan_data["leader_id"]))
        member_names = [
            await self._get_user_display_name(int(mid)) for mid in clan_data["members"]
        ]
        members_list_str = (
            "\n".join(f"- {name}" for name in member_names) or "Nenhum membro."
        )

        embed = discord.Embed(
            title=f"🛡️ Informações do Clã: {clan_data['name']}",
            color=discord.Color.purple(),
        )
        embed.add_field(name="👑 Líder", value=leader_name, inline=False)
        embed.add_field(
            name=f"👥 Membros ({len(clan_data['members'])}/{config.MAX_CLAN_MEMBERS})",
            value=members_list_str[:1024],
            inline=False,
        )
        embed.add_field(name="✨ XP do Clã", value=f"{clan_data['xp']:,}", inline=True)
        embed.add_field(
            name="💰 Dinheiro do Clã",
            value=display_money(clan_data["money"]),
            inline=True,
        )
        embed.add_field(
            name="📅 Criado em",
            value=f"<t:{clan_data['creation_timestamp']}:D>",
            inline=True,
        )
        embed.set_footer(text=f"ID do Clã: {clan_data['id']}")

        await ctx.response.send_message(embed=embed)

    @app_commands.command(
        name="ranking_clans", description="Exibe o ranking dos clãs por XP."
    )
    async def ranking_clans(self, ctx: discord.Interaction):
        active_clans = [c for c in data_manager.clan_database.values() if c["members"]]
        if not active_clans:
            return await ctx.response.send_message(
                "Ainda não há clãs ativos para exibir no ranking.", ephemeral=True
            )

        sorted_clans = sorted(active_clans, key=lambda x: x["xp"], reverse=True)
        embed = discord.Embed(
            title=f"🏆 Ranking de Clãs",
            description="Os melhores clãs, ranqueados por XP.",
            color=discord.Color.gold(),
        )

        for i, clan in enumerate(sorted_clans[:10]):
            leader_name = await self._get_user_display_name(int(clan["leader_id"]))
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}.get(i, f"**{i+1}.**")
            embed.add_field(
                name=f"{rank_emoji} {clan['name']}",
                value=f"👑 **Líder:** {leader_name}\n✨ **XP:** {clan['xp']:,}\n💰 **Dinheiro:** {display_money(clan['money'])}\n👥 **Membros:** {len(clan['members'])}/{config.MAX_CLAN_MEMBERS}",
                inline=False,
            )
        await ctx.response.send_message(embed=embed)

    @app_commands.command(
        name="expulsar_membro", description="[Líder] Expulsa um membro do clã."
    )
    async def expulsar_membro(self, ctx: discord.Interaction, membro: discord.Member):
        player_id = str(ctx.user.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data or player_data.get("clan_role") != "Líder":
            return await ctx.response.send_message(
                "Apenas o líder do clã pode usar este comando.", ephemeral=True
            )

        clan_data = data_manager.clan_database.get(player_data["clan_id"])
        target_member_id = str(membro.id)

        if target_member_id == player_id:
            return await ctx.response.send_message(
                "Você não pode expulsar a si mesmo. Use `/sair_cla`.", ephemeral=True
            )
        if target_member_id not in clan_data["members"]:
            return await ctx.response.send_message(
                f"{membro.display_name} não é um membro do seu clã.", ephemeral=True
            )

        clan_data["members"].remove(target_member_id)
        target_member_data = data_manager.get_player_data(target_member_id)
        if target_member_data:
            target_member_data.update({"clan_id": None, "clan_role": None})
            data_manager.save_data()
        data_manager.save_clan_data()

        embed = discord.Embed(
            title=f"🛡️ Membro Expulso!",
            description=f"{membro.display_name} foi expulso do clã **{clan_data['name']}**.",
            color=discord.Color.orange(),
        )
        await ctx.response.send_message(embed=embed)

    @app_commands.command(
        name="transferir_lideranca", description="[Líder] Transfere a liderança do clã."
    )
    async def transferir_lideranca(
        self, ctx: discord.Interaction, novo_lider: discord.Member
    ):
        player_id = str(ctx.user.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data or player_data.get("clan_role") != "Líder":
            return await ctx.response.send_message(
                "Apenas o líder do clã pode transferir a liderança.", ephemeral=True
            )

        clan_data = data_manager.clan_database.get(player_data["clan_id"])
        new_leader_id = str(novo_lider.id)

        if new_leader_id == player_id:
            return await ctx.response.send_message(
                "Você já é o líder do clã.", ephemeral=True
            )
        if new_leader_id not in clan_data["members"]:
            return await ctx.response.send_message(
                f"{novo_lider.display_name} não é um membro do seu clã.", ephemeral=True
            )

        player_data["clan_role"] = "Membro"
        new_leader_data = data_manager.get_player_data(new_leader_id)
        if new_leader_data:
            new_leader_data["clan_role"] = "Líder"
        clan_data["leader_id"] = new_leader_id

        data_manager.save_data()
        data_manager.save_clan_data()

        embed = discord.Embed(
            title=f"👑 Liderança Transferida!",
            description=f"{ctx.user.mention} transferiu a liderança do clã para {novo_lider.mention}.",
            color=discord.Color.gold(),
        )
        await ctx.response.send_message(embed=embed)


# --- SETUP DA COG ---


# A função setup precisa ser assíncrona para adicionar cogs com comandos de barra
async def setup(bot: commands.Bot):
    """Adiciona a ClanCommands cog ao bot."""
    await bot.add_cog(ClanCommands(bot))
