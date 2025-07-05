# File: OutlawRpg-main/outlaw/cogs/relic_commands.py
# Crie este novo arquivo dentro da pasta 'cogs'.

import discord
from discord.ext import commands, tasks
from discord import app_commands # IMPORTANTE: Adicione esta linha para comandos de barra
from discord.ui import Button, View
import asyncio
import time
from datetime import timedelta

# Importar de seus módulos de gerenciamento de dados e lógica
from data_manager import (  
    get_player_data,
    save_data,
    add_relic_to_inventory,
    add_user_money,
    add_user_energy,
    check_and_add_keys,
    get_time_until_next_key_claim,
)

from game_logic.relic_mechanics import get_random_relic  
from relics import (  
    relics,
)  # Importa a lista de relíquias para o /inventory


class RelicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Inicia a tarefa de geração de chaves. Ela verificará a cada minuto.
        self.key_generation_task.start()

    def cog_unload(self):
        # Cancela a tarefa ao descarregar o cog para evitar que ela continue em background
        self.key_generation_task.cancel()

    @tasks.loop(minutes=1)  # Verifica a cada minuto para adicionar chaves
    async def key_generation_task(self):
        """
        Tarefa em loop que verifica e adiciona chaves para todos os usuários
        cujo cooldown de 1 hora expirou.
        """
        all_user_data = get_player_data(
            "all"
        )  # Retorna a referência ao dicionário global player_database

        # Cria uma lista de user_ids para iterar para evitar "dictionary changed size during iteration"
        # se o save_data for chamado dentro do loop (que ele é).
        user_ids_to_check = list(all_user_data.keys())

        for user_id_str in user_ids_to_check:
            user_id = int(user_id_str)
            keys_added = check_and_add_keys(user_id)  # Esta função já salva os dados

            if keys_added > 0:
                print(f"Adicionadas {keys_added} chaves para o usuário {user_id}")
                # Opcional: enviar DM ao usuário sobre novas chaves.
                # Cuidado com o rate limit do Discord para muitos usuários.
                user = self.bot.get_user(user_id)  # Tenta obter da cache primeiro
                if user is None:
                    try:
                        user = await self.bot.fetch_user(
                            user_id
                        )  # Se não estiver na cache, busca
                    except discord.NotFound:
                        user = None  # Usuário não existe mais

                if user:
                    try:
                        # Para slash commands, o prefixo não é relevante aqui.
                        # Apenas mencionar o comando /bau
                        await user.send(
                            f"Você recebeu {keys_added} chaves de baú! Use-as com `/bau`."
                        )
                    except discord.Forbidden:
                        print(
                            f"Não foi possível enviar DM para {user.name} ({user.id})."
                        )
                    except Exception as e:
                        print(f"Erro ao enviar DM para {user.name} ({user.id}): {e}")

    @key_generation_task.before_loop
    async def before_key_generation(self):
        """Aguarda o bot estar pronto antes de iniciar a tarefa."""
        await self.bot.wait_until_ready()
        print("Tarefa de geração de chaves iniciada e aguardando bot pronto.")

    @app_commands.command(name="bau", description="Mostra o baú e permite abri-lo.")
    async def open_chest(self, interaction: discord.Interaction): # Mudança de ctx para interaction
        user_id = str(interaction.user.id) # Mudança de ctx.author.id para interaction.user.id

        # Garante que as chaves são atualizadas antes de exibir o status
        check_and_add_keys(interaction.user.id) # Mudança de ctx.author.id para interaction.user.id
        user_data = get_player_data(
            user_id
        )  # Recarrega (ou obtém) para ter as chaves atualizadas

        keys_available = user_data.get("keys", 0)
        time_remaining_seconds = get_time_until_next_key_claim(interaction.user.id) # Mudança de ctx.author.id para interaction.user.id

        # Formata o tempo restante
        if time_remaining_seconds > 0:
            td = timedelta(seconds=int(time_remaining_seconds))
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"Novas chaves em **{hours}h {minutes}m {seconds}s**."
        else:
            time_str = "Você pode reivindicar novas chaves agora!"

        embed = discord.Embed(
            title="Um Baú Misterioso Aparece!",
            description=f"Você tem **{keys_available}** chaves disponíveis.\n\n{time_str}",
            color=discord.Color.gold(),
        )
        # Substitua 'URL_DA_IMAGEM_DO_BAU' pela URL de uma imagem do baú
        embed.set_image(
            url="https://i.imgur.com/example_chest_image.png"
        )  # **IMPORTANTE: Mude para a sua imagem!**
        embed.set_footer(
            text=f"Use /inventory para ver suas relíquias." # Mudança de command_prefix para /inventory
        )

        # Classe interna para o botão de interação
        class ChestButton(Button):
            # O 'ctx' original não está mais disponível diretamente aqui,
            # então a verificação de autor é feita com interaction.user.id
            # O 'parent_cog_ref' ainda é necessário.
            def __init__(self, label, style, custom_id, parent_cog_ref, original_author_id):
                super().__init__(label=label, style=style, custom_id=custom_id)
                self.parent_cog = parent_cog_ref  # Referência ao cog para acessar métodos como _get_tier_color
                self.original_author_id = original_author_id # Guarda o ID do autor original

            async def callback(self, interaction: discord.Interaction):
                # Garante que apenas o usuário que invocou o comando pode usar o botão
                if interaction.user.id != self.original_author_id: # Usa o ID do autor original
                    await interaction.response.send_message(
                        "Este baú não é seu para abrir!", ephemeral=True
                    )
                    return

                user_id_btn = str(interaction.user.id)
                user_data_btn = get_player_data(user_id_btn)  # Obtém dados atualizados

                if user_data_btn.get("keys", 0) <= 0:
                    await interaction.response.send_message(
                        "Você não tem chaves para abrir este baú!", ephemeral=True
                    )
                    return

                # Consome uma chave
                user_data_btn["keys"] = user_data_btn.get("keys", 0) - 1
                save_data()  # Salva a alteração imediatamente

                # Sorteia a relíquia
                gained_relic = get_random_relic()
                add_relic_to_inventory(user_id_btn, gained_relic["nome"])
                add_user_money(user_id_btn, gained_relic["valor_moedas"])
                add_user_energy(user_id_btn, gained_relic["energia_concedida"])

                # Cria o embed de recompensa
                reward_embed = discord.Embed(
                    title=f"Você Abriu o Baú e Ganhou!",
                    description=f"🎉 Parabéns! Você obteve a relíquia: **{gained_relic['nome']}**!\n\n"
                    f"**Tier:** {gained_relic['tier']}\n"
                    f"**Valor:** {gained_relic['valor_moedas']} moedas\n"
                    f"**Energia:** {gained_relic['energia_concedida']} pontos\n"
                    f"**Chance de Obtenção:** {gained_relic['chance_obter_percentual']}%",
                    color=self.parent_cog._get_tier_color(
                        gained_relic["tier"]
                    ),  # Usa o método do cog
                )
                # Você pode adicionar uma imagem para a relíquia aqui se tiver URLs para cada uma
                # Exemplo: reward_embed.set_thumbnail(url=gained_relic.get("imagem_url", "URL_PADRAO_RELIQUIA"))

                # Atualiza a descrição do embed original do baú para refletir as chaves restantes
                # Primeiro, recarrega os dados do usuário para ter o estado mais recente (após uso da chave)
                user_data_updated = get_player_data(user_id_btn)
                keys_available_updated = user_data_updated.get("keys", 0)
                time_remaining_updated = get_time_until_next_key_claim(user_id_btn)

                if time_remaining_updated > 0:
                    td_updated = timedelta(seconds=int(time_remaining_updated))
                    hours_updated, remainder_updated = divmod(td_updated.seconds, 3600)
                    minutes_updated, seconds_updated = divmod(remainder_updated, 60)
                    time_str_updated = f"Novas chaves em **{hours_updated}h {minutes_updated}m {seconds_updated}s**."
                else:
                    time_str_updated = "Você pode reivindicar novas chaves agora!"

                # Acessa o embed da mensagem original através do interaction
                original_embed = interaction.message.embeds[0]
                original_embed.description = f"Você tem **{keys_available_updated}** chaves disponíveis.\n\n{time_str_updated}"

                # Edita a mensagem original do baú
                await interaction.message.edit(
                    embed=original_embed, view=self.view
                )  # view é a view que contém este botão
                await interaction.followup.send(
                    embed=reward_embed
                )  # Envia a recompensa como uma nova mensagem

        # Cria a view com o botão
        view = View(timeout=180)  # Timeout para o botão (ex: 3 minutos)
        # Passa a referência do cog e o ID do autor original para a classe do botão
        view.add_item(
            ChestButton(
                "Abrir Baú", discord.ButtonStyle.green, "open_chest_button", self, interaction.user.id
            )
        )

        # Envia a mensagem do baú
        await interaction.response.send_message(embed=embed, view=view) # Mudança de ctx.send para interaction.response.send_message

    def _get_tier_color(self, tier):
        """Retorna uma cor para o embed baseada no tier da relíquia."""
        colors = {
            "Básica": discord.Color.light_grey(),
            "Comum": discord.Color.dark_grey(),
            "Incomum": discord.Color.green(),
            "Rara": discord.Color.blue(),
            "Épica": discord.Color.purple(),
            "Mítica": discord.Color.red(),
        }
        return colors.get(tier, discord.Color.default())

    @app_commands.command( # Mudança de commands.command para app_commands.command
        name="inventory",
        description="Mostra suas relíquias obtidas.", # help se torna description para slash commands
    )
    # Aliases (como 'inv', 'reliquias') não são suportados diretamente em app_commands.command
    # Se precisar deles, você teria que criar comandos slash separados para cada um
    # que chamem a mesma lógica (e registrar cada um).
    async def show_inventory(self, interaction: discord.Interaction): # Mudança de ctx para interaction
        user_id = str(interaction.user.id) # Mudança de ctx.author.id para interaction.user.id
        user_data = get_player_data(user_id)
        inventory = user_data.get("relics_inventory", [])

        if not inventory:
            embed = discord.Embed(
                title="Seu Inventário de Relíquias",
                description="Você ainda não possui nenhuma relíquia. Use `/bau` para tentar a sorte!",
                color=discord.Color.blue(),
            )
        else:
            # Conta a ocorrência de cada relíquia para exibir de forma organizada
            relic_counts = {}
            for relic_name in inventory:
                relic_counts[relic_name] = relic_counts.get(relic_name, 0) + 1

            # Para ordenar e exibir o tier, precisamos da lista 'relics' completa aqui
            # Criar um dicionário para mapear nome da relíquia para o objeto completo (mais eficiente)
            relics_map = {relic["nome"]: relic for relic in relics}

            # Prepara a lista de itens para exibição, incluindo o tier
            display_items = []
            for item in relic_counts.items():
                relic_name = item[0]
                count = item[1]
                relic_info = relics_map.get(relic_name)
                if relic_info:
                    display_items.append(
                        {"name": relic_name, "count": count, "tier": relic_info["tier"]}
                    )

            # Opcional: Ordenar por tier (Mítica -> Épica -> Rara -> Incomum -> Comum -> Básica)
            tier_order = {
                "Mítica": 6,
                "Épica": 5,
                "Rara": 4,
                "Incomum": 3,
                "Comum": 2,
                "Básica": 1,
            }
            display_items.sort(key=lambda x: tier_order.get(x["tier"], 0), reverse=True)

            inventory_text = ""
            for item in display_items:
                inventory_text += (
                    f"- **{item['name']}** ({item['tier']}) x{item['count']}\n"
                )

            embed = discord.Embed(
                title="Seu Inventário de Relíquias",
                description=inventory_text,
                color=discord.Color.blue(),
            )

        await interaction.response.send_message(embed=embed) # Mudança de ctx.send para interaction.response.send_message


async def setup(bot):
    await bot.add_cog(RelicCommands(bot))