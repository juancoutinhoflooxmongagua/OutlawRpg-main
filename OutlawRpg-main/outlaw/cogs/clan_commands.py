# cogs/clan_commands.py
import discord
from discord.ext import commands
import uuid
import time

# Changed imports from 'from outlaw import ...' to direct imports as per project structure
import data_manager
import config  # Assuming config.py is directly importable
from utils import display_money  # Assuming utils.py is directly importable
from utils import display_money


class ClanCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="criar_cla", description="Cria um novo clã.")
    async def criar_cla(self, ctx, nome: str):
        player_id = str(ctx.author.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data:
            await ctx.respond(
                "Você precisa criar um personagem primeiro! Use `/criar_personagem`."
            )
            return

        if player_data.get("clan_id"):
            await ctx.respond(
                "Você já faz parte de um clã. Saia do clã atual antes de criar um novo."
            )
            return

        if len(nome) < 3 or len(nome) > 20:
            await ctx.respond("O nome do clã deve ter entre 3 e 20 caracteres.")
            return

        # Check if clan name already exists (case-insensitive)
        for clan_id, clan_info in data_manager.clan_database.items():
            if clan_info["name"].lower() == nome.lower():
                await ctx.respond(
                    f"Já existe um clã com o nome '{nome}'. Por favor, escolha outro nome."
                )
                return

        if (
            player_data["money"] < config.CLAN_CREATION_COST
        ):  # Access via config.CLAN_CREATION_COST
            await ctx.respond(
                f"Você precisa de {display_money(config.CLAN_CREATION_COST)} para criar um clã. Você tem {display_money(player_data['money'])}."
            )
            return

        clan_id = str(uuid.uuid4())
        timestamp = int(time.time())

        new_clan_data = {
            "id": clan_id,  # Store clan_id inside clan_data as well
            "name": nome,
            "leader_id": player_id,
            "members": [player_id],
            "xp": config.DEFAULT_CLAN_XP,  # Access via config.DEFAULT_CLAN_XP
            "money": config.INITIAL_CLAN_DATA[
                "money"
            ],  # Access via config.INITIAL_CLAN_DATA
            "creation_timestamp": timestamp,
            "last_ranking_timestamp": timestamp,  # Initialize with current time
        }

        data_manager.clan_database[clan_id] = new_clan_data
        player_data["clan_id"] = clan_id
        player_data["clan_role"] = "Líder"
        player_data[
            "money"
        ] -= config.CLAN_CREATION_COST  # Access via config.CLAN_CREATION_COST

        data_manager.save_data()  # save_player_data
        data_manager.save_clan_data()

        embed = discord.Embed(
            title=f"{config.CUSTOM_EMOJIS.get('clan_icon', '🛡️')} Clã Criado!",  # Access via config.CUSTOM_EMOJIS
            description=f"O clã **{nome}** foi criado com sucesso por {ctx.author.mention}!",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Custo", value=display_money(config.CLAN_CREATION_COST), inline=True
        )  # Access via config.CLAN_CREATION_COST
        embed.add_field(name="Líder", value=ctx.author.display_name, inline=True)
        embed.add_field(
            name="Membros", value=f"1/{config.MAX_CLAN_MEMBERS}", inline=True
        )  # Access via config.MAX_CLAN_MEMBERS
        embed.set_footer(text="Aventure-se com seu novo clã!")

        await ctx.respond(embed=embed)

    @commands.slash_command(name="entrar_cla", description="Entra em um clã existente.")
    async def entrar_cla(self, ctx, nome_do_cla: str):
        player_id = str(ctx.author.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data:
            await ctx.respond(
                "Você precisa criar um personagem primeiro! Use `/criar_personagem`."
            )
            return

        if player_data.get("clan_id"):
            await ctx.respond(
                "Você já faz parte de um clã. Saia do clã atual antes de entrar em outro."
            )
            return

        target_clan_id = None
        for clan_id, clan_info in data_manager.clan_database.items():
            if clan_info["name"].lower() == nome_do_cla.lower():
                target_clan_id = clan_id
                break

        if not target_clan_id:
            await ctx.respond(
                f"Clã '{nome_do_cla}' não encontrado. Verifique o nome e tente novamente."
            )
            return

        clan_data = data_manager.clan_database[target_clan_id]

        if (
            len(clan_data["members"]) >= config.MAX_CLAN_MEMBERS
        ):  # Access via config.MAX_CLAN_MEMBERS
            await ctx.respond(
                f"O clã **{clan_data['name']}** já atingiu o número máximo de membros ({config.MAX_CLAN_MEMBERS})."
            )  # Access via config.MAX_CLAN_MEMBERS
            return

        clan_data["members"].append(player_id)
        player_data["clan_id"] = target_clan_id
        player_data["clan_role"] = "Membro"

        data_manager.save_data()  # save_player_data
        data_manager.save_clan_data()

        embed = discord.Embed(
            title=f"{config.CUSTOM_EMOJIS.get('clan_icon', '🛡️')} Entrou no Clã!",  # Access via config.CUSTOM_EMOJIS
            description=f"{ctx.author.mention} entrou no clã **{clan_data['name']}**!",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Membros Atuais",
            value=f"{len(clan_data['members'])}/{config.MAX_CLAN_MEMBERS}",
            inline=True,
        )  # Access via config.MAX_CLAN_MEMBERS
        embed.set_footer(text="Bem-vindo(a) ao seu novo lar!")

        await ctx.respond(embed=embed)

    @commands.slash_command(name="sair_cla", description="Sai do seu clã atual.")
    async def sair_cla(self, ctx):
        player_id = str(ctx.author.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data or not player_data.get("clan_id"):
            await ctx.respond("Você não faz parte de nenhum clã.")
            return

        clan_id = player_data["clan_id"]
        clan_data = data_manager.clan_database.get(clan_id)

        if not clan_data:
            # Should not happen if clan_id exists in player_data, but for safety
            player_data["clan_id"] = None
            player_data["clan_role"] = None
            data_manager.save_data()  # save_player_data
            await ctx.respond(
                "Erro: Seu clã não foi encontrado no banco de dados. Seus dados foram corrigidos."
            )
            return

        clan_name = clan_data["name"]

        # Remove player from clan members list
        if player_id in clan_data["members"]:
            clan_data["members"].remove(player_id)

        # Handle leader leaving
        if clan_data["leader_id"] == player_id:
            if clan_data["members"]:
                new_leader_id = clan_data["members"][
                    0
                ]  # Assign first member as new leader
                clan_data["leader_id"] = new_leader_id

                # Update new leader's role
                new_leader_data = data_manager.get_player_data(new_leader_id)
                if new_leader_data:
                    new_leader_data["clan_role"] = "Líder"
                    data_manager.save_data()  # Save immediately for new leader

                embed = discord.Embed(
                    title=f"{config.CUSTOM_EMOJIS.get('leader_icon', '👑')} Liderança Transferida!",  # Access via config.CUSTOM_EMOJIS
                    description=f"{ctx.author.mention} saiu do clã **{clan_name}**. A liderança foi transferida para <@{new_leader_id}>.",
                    color=discord.Color.orange(),
                )
                await ctx.respond(embed=embed)
            else:
                # No more members, dissolve the clan
                del data_manager.clan_database[clan_id]
                embed = discord.Embed(
                    title=f"{config.CUSTOM_EMOJIS.get('clan_icon', '🛡️')} Clã Dissolvido!",  # Access via config.CUSTOM_EMOJIS
                    description=f"{ctx.author.mention} saiu do clã **{clan_name}**, e como não havia mais membros, o clã foi dissolvido.",
                    color=discord.Color.red(),
                )
                await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title=f"{config.CUSTOM_EMOJIS.get('clan_icon', '🛡️')} Saiu do Clã!",  # Access via config.CUSTOM_EMOJIS
                description=f"{ctx.author.mention} saiu do clã **{clan_name}**.",
                color=discord.Color.red(),
            )
            await ctx.respond(embed=embed)

        player_data["clan_id"] = None
        player_data["clan_role"] = None

        data_manager.save_data()  # save_player_data
        data_manager.save_clan_data()

    @commands.slash_command(
        name="expulsar_membro", description="[Líder do Clã] Expulsa um membro do clã."
    )
    async def expulsar_membro(self, ctx, membro: discord.Member):
        player_id = str(ctx.author.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data or player_data.get("clan_role") != "Líder":
            await ctx.respond(
                "Apenas o líder do clã pode usar este comando.", ephemeral=True
            )
            return

        clan_id = player_data["clan_id"]
        clan_data = data_manager.clan_database.get(clan_id)

        if not clan_data:
            await ctx.respond("Você não está em um clã válido.", ephemeral=True)
            return

        target_member_id = str(membro.id)
        if target_member_id == player_id:
            await ctx.respond(
                "Você não pode expulsar a si mesmo. Use `/sair_cla` para sair do clã.",
                ephemeral=True,
            )
            return

        if target_member_id not in clan_data["members"]:
            await ctx.respond(
                f"{membro.display_name} não é um membro do seu clã.", ephemeral=True
            )
            return

        clan_data["members"].remove(target_member_id)

        target_member_data = data_manager.get_player_data(target_member_id)
        if target_member_data:
            target_member_data["clan_id"] = None
            target_member_data["clan_role"] = None
            data_manager.save_data()  # save_player_data

        data_manager.save_clan_data()

        embed = discord.Embed(
            title=f"{config.CUSTOM_EMOJIS.get('clan_icon', '🛡️')} Membro Expulso!",  # Access via config.CUSTOM_EMOJIS
            description=f"{membro.display_name} foi expulso(a) do clã **{clan_data['name']}** por {ctx.author.mention}.",
            color=discord.Color.orange(),
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="transferir_lideranca",
        description="[Líder do Clã] Transfere a liderança do clã.",
    )
    async def transferir_lideranca(self, ctx, novo_lider: discord.Member):
        player_id = str(ctx.author.id)
        player_data = data_manager.get_player_data(player_id)

        if not player_data or player_data.get("clan_role") != "Líder":
            await ctx.respond(
                "Apenas o líder do clã pode transferir a liderança.", ephemeral=True
            )
            return

        clan_id = player_data["clan_id"]
        clan_data = data_manager.clan_database.get(clan_id)

        if not clan_data:
            await ctx.respond("Você não está em um clã válido.", ephemeral=True)
            return

        new_leader_id = str(novo_lider.id)
        if new_leader_id not in clan_data["members"]:
            await ctx.respond(
                f"{novo_lider.display_name} não é um membro do seu clã.", ephemeral=True
            )
            return

        if new_leader_id == player_id:
            await ctx.respond("Você já é o líder do clã.", ephemeral=True)
            return

        # Update old leader's role
        player_data["clan_role"] = "Membro"

        # Update clan leader
        clan_data["leader_id"] = new_leader_id

        # Update new leader's role
        new_leader_data = data_manager.get_player_data(new_leader_id)
        if new_leader_data:
            new_leader_data["clan_role"] = "Líder"

        data_manager.save_data()  # save_player_data
        data_manager.save_clan_data()

        embed = discord.Embed(
            title=f"{config.CUSTOM_EMOJIS.get('leader_icon', '👑')} Liderança Transferida!",  # Access via config.CUSTOM_EMOJIS
            description=f"{ctx.author.mention} transferiu a liderança do clã **{clan_data['name']}** para {novo_lider.mention}.",
            color=discord.Color.gold(),
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="info_cla", description="Exibe informações sobre um clã."
    )
    async def info_cla(self, ctx, nome_do_cla_ou_id: str = None):
        clan_data = None
        if nome_do_cla_ou_id:
            # Try to find by name first (case-insensitive)
            for cid, cdata in data_manager.clan_database.items():
                if cdata["name"].lower() == nome_do_cla_ou_id.lower():
                    clan_data = cdata
                    break
            # If not found by name, try by ID
            if not clan_data and nome_do_cla_ou_id in data_manager.clan_database:
                clan_data = data_manager.clan_database[nome_do_cla_ou_id]
        else:
            player_data = data_manager.get_player_data(str(ctx.author.id))
            if player_data and player_data.get("clan_id"):
                clan_data = data_manager.clan_database.get(player_data["clan_id"])
            else:
                await ctx.respond(
                    "Você não está em um clã. Use `/info_cla [nome_do_cla]` para ver informações de outro clã.",
                    ephemeral=True,
                )
                return

        if not clan_data:
            await ctx.respond(
                f"Clã '{nome_do_cla_ou_id}' não encontrado.", ephemeral=True
            )
            return

        leader_member = await self.bot.fetch_user(int(clan_data["leader_id"]))
        leader_name = leader_member.display_name if leader_member else "Desconhecido"

        member_names = []
        # Fetch members in chunks to avoid rate limits if many members
        # For simplicity, fetching one by one here, but for large clans, a more efficient method might be needed
        for member_id in clan_data["members"]:
            try:
                member = await self.bot.fetch_user(int(member_id))
                if member:
                    member_names.append(member.display_name)
                else:
                    member_names.append(f"ID: {member_id} (Usuário não encontrado)")
            except discord.NotFound:
                member_names.append(f"ID: {member_id} (Usuário não encontrado)")
            except Exception as e:
                member_names.append(f"ID: {member_id} (Erro: {e})")

        members_list = (
            "\n".join(member_names) if member_names else "Nenhum membro (clã vazio)"
        )
        if len(members_list) > 1024:  # Discord embed field value limit
            members_list = members_list[:1000] + "..."

        embed = discord.Embed(
            title=f"{config.CUSTOM_EMOJIS.get('clan_icon', '🛡️')} Informações do Clã: {clan_data['name']}",  # Access via config.CUSTOM_EMOJIS
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="Líder",
            value=f"{config.CUSTOM_EMOJIS.get('leader_icon', '👑')} {leader_name}",
            inline=False,
        )  # Access via config.CUSTOM_EMOJIS
        embed.add_field(
            name="Membros",
            value=f"{config.CUSTOM_EMOJIS.get('member_icon', '👥')} {len(clan_data['members'])}/{config.MAX_CLAN_MEMBERS}\n{members_list}",
            inline=False,
        )  # Access via config.CUSTOM_EMOJIS, config.MAX_CLAN_MEMBERS
        embed.add_field(
            name="XP do Clã",
            value=f"{config.CUSTOM_EMOJIS.get('xp_icon', '✨')} {clan_data['xp']:,}",
            inline=True,
        )  # Access via config.CUSTOM_EMOJIS
        embed.add_field(
            name="Dinheiro do Clã",
            value=f"{config.CUSTOM_EMOJIS.get('money_icon', '💰')} ${clan_data['money']:,}",
            inline=True,
        )  # NEW: Display clan money
        embed.add_field(
            name="Criado em",
            value=f"<t:{clan_data['creation_timestamp']}:D>",
            inline=True,
        )
        embed.set_footer(
            text=f"ID do Clã: {clan_data.get('id', 'N/A')}"
        )  # Display ID for debugging/reference

        await ctx.respond(embed=embed)

    @commands.slash_command(
        name="ranking_clans", description="Exibe o ranking dos clãs por XP."
    )
    async def ranking_clans(self, ctx):
        if not data_manager.clan_database:
            await ctx.respond(
                "Ainda não há clãs registrados para exibir o ranking.", ephemeral=True
            )
            return

        # Filter out clans with no members for ranking purposes
        active_clans = [
            clan for clan in data_manager.clan_database.values() if clan["members"]
        ]

        if not active_clans:
            await ctx.respond(
                "Ainda não há clãs ativos (com membros) para exibir o ranking.",
                ephemeral=True,
            )
            return

        sorted_clans = sorted(active_clans, key=lambda x: x["xp"], reverse=True)

        embed = discord.Embed(
            title=f"{config.CUSTOM_EMOJIS.get('trophy_icon', '🏆')} Ranking de Clãs",  # Access via config.CUSTOM_EMOJIS
            description="Os clãs são ranqueados pela XP acumulada.",
            color=discord.Color.gold(),
        )

        for i, clan in enumerate(sorted_clans[:10]):  # Show top 10 clans
            leader_member = await self.bot.fetch_user(int(clan["leader_id"]))
            leader_name = (
                leader_member.display_name if leader_member else "Desconhecido"
            )

            rank_emoji = ""
            if i == 0:
                rank_emoji = "🥇"
            elif i == 1:
                rank_emoji = "🥈"
            elif i == 2:
                rank_emoji = "🥉"
            else:
                rank_emoji = f"{i+1}."

            embed.add_field(
                name=f"{rank_emoji} {clan['name']}",
                value=f"Líder: {leader_name}\nXP: {clan['xp']:,}\nDinheiro: ${clan['money']:,}\nMembros: {len(clan['members'])}/{config.MAX_CLAN_MEMBERS}",  # Display clan money, access config.MAX_CLAN_MEMBERS
                inline=False,
            )

        embed.set_footer(text="O ranking é atualizado semanalmente com recompensas!")
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(ClanCommands(bot))
