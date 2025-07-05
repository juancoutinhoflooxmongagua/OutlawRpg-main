# File: OutlawRpg-main/outlaw/cogs/relic_commands.py
# Crie este novo arquivo dentro da pasta 'cogs'.

import discord
from discord.ext import commands, tasks
from discord import (
    app_commands,
)  # IMPORTANTE: Adicione esta linha para comandos de barra
from discord.ui import (
    Button,
    View,
)  # View e Button são usados agora

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
)  # Importa a lista de relíquias para o /inventory


# Dicionário de URLs de imagens de baús por Tier da Relíquia
# IMPORTANTE: Substitua estas URLs pelas suas próprias imagens de baús para cada tier!
TIER_CHEST_IMAGES = {
    "Básica": "https://i.imgur.com/YFS0E0O.png",  # Exemplo: Baú de madeira simples
    "Comum": "https://i.imgur.com/1C8QcA4.png",  # Exemplo: Baú de madeira com algumas ferragens
    "Incomum": "https://i.imgur.com/2ji2Ucq.png",  # Exemplo: Baú de metal enferrujado
    "Rara": "https://i.imgur.com/vQdnSCF.png",  # Exemplo: Baú de prata
    "Épica": "https://i.imgur.com/sTFdcbE.png",  # Exemplo: Baú de ouro ornamentado
    "Mítica": "https://i.imgur.com/mythic_chest.png",  # Exemplo: Baú mágico ou celestial
}


# Classe View para o botão de abrir baú
class OpenChestView(View):
    def __init__(self, gained_relic: dict, user_id: int, relic_commands_cog):
        super().__init__(timeout=60)  # O botão expira em 60 segundos
        self.gained_relic = gained_relic
        self.user_id = user_id
        self.relic_commands_cog = relic_commands_cog  # Referência ao cog para acessar métodos como _get_tier_color

    @discord.ui.button(label="Abrir Baú", style=discord.ButtonStyle.green, emoji="🔑")
    async def open_button_callback(
        self, interaction: discord.Interaction, button: Button
    ):
        # Garante que apenas o usuário que invocou o comando pode usar o botão
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "Este baú não é seu para abrir!", ephemeral=True
            )
            return

        await interaction.response.defer()  # Defer a resposta do botão

        user_data = get_player_data(str(self.user_id))
        keys_available = user_data.get("keys", 0)

        if keys_available <= 0:
            # Isso não deveria acontecer se a lógica inicial estiver correta, mas é uma salvaguarda
            await interaction.edit_original_response(
                content="Você não tem mais chaves para abrir este baú!",
                embed=None,  # Remove o embed anterior
                view=None,  # Remove o botão
            )
            self.stop()  # Para a view
            return

        # Consome uma chave
        user_data["keys"] = user_data.get("keys", 0) - 1
        save_data()  # Salva a alteração imediatamente

        # Adiciona a relíquia ao inventário e concede recompensas
        add_relic_to_inventory(str(self.user_id), self.gained_relic["nome"])
        add_user_money(str(self.user_id), self.gained_relic["valor_moedas"])
        add_user_energy(str(self.user_id), self.gained_relic["energia_concedida"])

        # Determina a imagem do baú com base no tier da relíquia GANHA
        relic_tier = self.gained_relic.get("tier", "Básica")
        chest_image_to_display = TIER_CHEST_IMAGES.get(
            relic_tier, "https://i.imgur.com/default_basic_chest.png"
        )

        # Cria o embed de recompensa - ESTE É ONDE O QUE A PESSOA GANHOU É MOSTRADO
        reward_embed = discord.Embed(
            title=f"Você Abriu o Baú e Ganhou!",
            description=(
                f"🎉 Parabéns! Você obteve a relíquia: **{self.gained_relic['nome']}**!\n\n"
                f"**Tier:** {self.gained_relic['tier']}\n"
                f"**Valor:** {self.gained_relic['valor_moedas']} moedas\n"
                f"**Energia:** {self.gained_relic['energia_concedida']} pontos\n"
                f"**Chance de Obtenção:** {self.gained_relic['chance_obter_percentual']}%"
            ),
            color=self.relic_commands_cog._get_tier_color(self.gained_relic["tier"]),
        )
        reward_embed.set_image(url=chest_image_to_display)

        # Adicionar o contador de chaves atualizado e tempo restante ao rodapé
        updated_keys_available = user_data.get("keys", 0)
        time_remaining_seconds_updated = get_time_until_next_key_claim(self.user_id)
        if time_remaining_seconds_updated > 0:
            td_updated = timedelta(seconds=int(time_remaining_seconds_updated))
            hours_updated, remainder_updated = divmod(td_updated.seconds, 3600)
            minutes_updated, seconds_updated = divmod(remainder_updated, 60)
            footer_text = f"Chaves restantes: {updated_keys_available} | Novas chaves em {hours_updated}h {minutes_updated}m {seconds_updated}s."
        else:
            footer_text = f"Chaves restantes: {updated_keys_available} | Você pode reivindicar novas chaves agora!"

        reward_embed.set_footer(
            text=f"{footer_text} Use /inventory para ver suas relíquias."
        )

        # Desabilita o botão após a abertura
        for item in self.children:
            item.disabled = True

        await interaction.edit_original_response(embed=reward_embed, view=self)
        self.stop()  # Para a view após a interação

    async def on_timeout(self):
        # Chamado quando a view expira (timeout)
        # Desabilita o botão para que não possa ser clicado após o tempo limite
        for item in self.children:
            item.disabled = True
        # Tenta editar a mensagem para remover o botão, se a mensagem ainda existir
        try:
            # interaction.message é a mensagem onde a view foi anexada
            await self.message.edit(view=self)
        except discord.NotFound:
            pass  # Mensagem já foi excluída ou não encontrada


class RelicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Inicia a tarefa de geração de chaves. Ela verificará a cada minuto.
        self.key_generation_task.start()

    def cog_unload(self):
        # Cancela a tarefa ao descarregar o cog para evitar que ela continue em background
        self.key_generation_task.cancel()

    @tasks.loop(minutes=1)  # Verifica a cada minuto para adicionar chaves
    async def key_generation_task(self):
        """
        Tarefa em loop que verifica e adiciona chaves para todos os usuários
        cujo cooldown de 1 hora expirou.
        """
        all_user_data = get_player_data(
            "all"
        )  # Retorna a referência ao dicionário global player_database

        # Cria uma lista de user_ids para iterar para evitar "dictionary changed size during iteration"
        # se o save_data for chamado dentro do loop (que ele é).
        user_ids_to_check = list(all_user_data.keys())

        for user_id_str in user_ids_to_check:
            user_id = int(user_id_str)
            keys_added = check_and_add_keys(user_id)  # Esta função já salva os dados

            if keys_added > 0:
                print(f"Adicionadas {keys_added} chaves para o usuário {user_id}")
                # Opcional: enviar DM ao usuário sobre novas chaves.
                # Cuidado com o rate limit do Discord para muitos usuários.
                user = self.bot.get_user(user_id)  # Tenta obter da cache primeiro
                if user is None:
                    try:
                        user = await self.bot.fetch_user(
                            user_id
                        )  # Se não estiver na cache, busca
                    except discord.NotFound:
                        user = None  # Usuário não existe mais

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
                        print(
                            f"Erro ao enviar DM para {user.id}): {e}"
                        )  # Corrigido para user.id

    @key_generation_task.before_loop
    async def before_key_generation(self):
        """Aguarda o bot estar pronto antes de iniciar a tarefa."""
        await self.bot.wait_until_ready()
        print("Tarefa de geração de chaves iniciada e aguardando bot pronto.")

    @app_commands.command(name="bau", description="Mostra o baú e permite abri-lo.")
    async def open_chest(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # Defer the response to allow time for processing
        await interaction.response.defer(
            ephemeral=False
        )  # ephemeral=True se você quiser que só o usuário veja

        # Garante que as chaves são atualizadas antes de exibir o status
        check_and_add_keys(interaction.user.id)
        user_data = get_player_data(
            user_id
        )  # Recarrega (ou obtém) para ter as chaves atualizadas

        keys_available = user_data.get("keys", 0)

        # --- Lógica de Abertura do Baú (Agora imediata) ---
        if keys_available <= 0:
            time_remaining_seconds = get_time_until_next_key_claim(interaction.user.id)
            if time_remaining_seconds > 0:
                td = timedelta(seconds=int(time_remaining_seconds))
                hours, remainder = divmod(td.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"Novas chaves em **{hours}h {minutes}m {seconds}s**."
            else:
                time_str = "Você pode reivindicar novas chaves agora!"

            # Imagem do baú para o caso de não ter chaves (geralmente um baú básico)
            chest_image_to_display = TIER_CHEST_IMAGES.get(
                "Básica", "https://i.imgur.com/default_basic_chest.png"
            )  # URL de um baú básico padrão

            no_keys_embed = discord.Embed(
                title="Um Baú Misterioso Aparece!",
                description=f"Você não tem chaves para abrir este baú! 😔\n\n{time_str}",
                color=discord.Color.red(),
            )
            no_keys_embed.set_image(url=chest_image_to_display)
            no_keys_embed.set_footer(text="Use /inventory para ver suas relíquias.")
            await interaction.edit_original_response(embed=no_keys_embed)
            return

        # Sorteia a relíquia ANTES de mostrar o baú para pegar o tier correto
        gained_relic = get_random_relic()
        relic_tier = gained_relic.get("tier", "Básica")
        chest_image_to_display = TIER_CHEST_IMAGES.get(
            relic_tier, "https://i.imgur.com/default_basic_chest.png"
        )

        # Cria o embed inicial com o baú e o botão
        initial_chest_embed = discord.Embed(
            title="Um Baú Misterioso Aparece!",
            description="Clique no botão abaixo para abrir o baú e revelar seu conteúdo!",
            color=self._get_tier_color(relic_tier),
        )
        initial_chest_embed.set_image(url=chest_image_to_display)
        initial_chest_embed.set_footer(text=f"Você tem {keys_available} chaves.")

        # Cria a view com o botão e passa a relíquia e o ID do usuário
        view = OpenChestView(gained_relic, interaction.user.id, self)

        # Envia a resposta inicial com o embed e o botão
        await interaction.edit_original_response(embed=initial_chest_embed, view=view)

        # Armazena a mensagem para que a view possa editá-la no timeout
        view.message = await interaction.original_response()

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

    @app_commands.command(  # Mudança de commands.command para app_commands.command
        name="inventory",
        description="Mostra suas relíquias obtidas.",  # help se torna description para slash commands
    )
    # Aliases (como 'inv', 'reliquias') não são suportados diretamente em app_commands.command
    # Se precisar deles, você teria que criar comandos slash separados para cada um
    # que chamem a mesma lógica (e registrar cada um).
    async def show_inventory(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
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

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(RelicCommands(bot))
