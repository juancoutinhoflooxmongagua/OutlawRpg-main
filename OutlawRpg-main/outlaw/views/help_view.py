import discord
from discord.ui import View, Button, Select
from config import ITEMS_DATA, CLASS_TRANSFORMATIONS, CUSTOM_EMOJIS # Changed from ..config to config

# Define as categorias de ajuda e seus comandos
HELP_CATEGORIES = {
    "Geral": {
        "desc": "Comandos básicos para interagir com o bot.",
        "commands": [
            {"name": "/criar_ficha", "desc": "Cria seu personagem no jogo."},
            {"name": "/perfil", "desc": "Visualiza os detalhes do seu personagem."},
            {"name": "/status", "desc": "Verifica seu HP, energia e status."},
            {"name": "/atribuir", "desc": "Gasta pontos de atributo em suas estatísticas."},
            {"name": "/descansar", "desc": "Recupera HP e energia na cidade."},
            {"name": "/ajuda", "desc": "Mostra este menu de ajuda."},
            {"name": "/inventario", "desc": "Gerencia seus itens."},
        ],
    },
    "Combate": {
        "desc": "Comandos para enfrentar inimigos e outros jogadores.",
        "commands": [
            {"name": "/cacar", "desc": "Enfrenta criaturas na natureza."},
            {"name": "/batalhar", "desc": "Desafia um inimigo poderoso (Ex-Cavaleiro Renegado)."},
            {"name": "/atacar", "desc": "Duela com outro jogador."},
            # Removido: {"name": "/atacar_boss", "desc": "Ataca o chefe global (se ativo)."},
        ],
    },
    "Mundo": {
        "desc": "Comandos para explorar o mundo do jogo.",
        "commands": [
            {"name": "/local", "desc": "Mostra sua localização atual e conexões."},
            {"name": "/viajar", "desc": "Move-se para outro local no mapa."},
            {"name": "/mapa", "desc": "Exibe o mapa completo do mundo."},
            {"name": "/reviver", "desc": "Renasce após ser derrotado."},
        ],
    },
    "Economia": {
        "desc": "Comandos relacionados a dinheiro e compras.",
        "commands": [
            {"name": "/loja", "desc": "Acessa a loja para comprar itens."},
            {"name": "/vender", "desc": "Vende itens do seu inventário."},
            {"name": "/saldo", "desc": "Verifica seu dinheiro atual."},
            {"name": "/doar", "desc": "Doa dinheiro para outro jogador."},
        ],
    },
    "Classes e Poderes": {
        "desc": "Informações sobre classes, estilos de poder e transformações.",
        "commands": [
            {"name": "/classe", "desc": "Mostra informações sobre sua classe."},
            {"name": "/estilo_poder", "desc": "Escolhe ou muda seu estilo de poder."},
            {"name": "/transformar", "desc": "Ativa sua transformação de classe."},
        ],
    },
    "Clãs": {
        "desc": "Comandos para interagir com o sistema de clãs.",
        "commands": [
            {"name": "/clan criar", "desc": "Cria um novo clã."},
            {"name": "/clan entrar", "desc": "Entra em um clã existente."},
            {"name": "/clan sair", "desc": "Sai do seu clã atual."},
            {"name": "/clan info", "desc": "Visualiza informações do seu clã ou de outro."},
            {"name": "/clan membros", "desc": "Lista os membros do seu clã."},
            {"name": "/clan convidar", "desc": "Convida um jogador para o seu clã."},
            {"name": "/clan chutar", "desc": "Remove um membro do seu clã."},
            {"name": "/clan depositar", "desc": "Deposita dinheiro no tesouro do clã."},
            {"name": "/clan sacar", "desc": "Saca dinheiro do tesouro do clã."},
            {"name": "/clan xp", "desc": "Doa XP para o clã."},
            {"name": "/clan ranking", "desc": "Mostra o ranking dos clãs."},
        ],
    },
    "Bênçãos": {
        "desc": "Comandos para gerenciar suas bênçãos.",
        "commands": [
            {"name": "/bencao ativar", "desc": "Ativa uma bênção que você possui."},
            {"name": "/bencao info", "desc": "Mostra detalhes sobre suas bênçãos."},
        ],
    },
    "Relíquias": {
        "desc": "Comandos para interagir com o sistema de relíquias.",
        "commands": [
            {"name": "/reliquia procurar", "desc": "Procura por câmaras de relíquias."},
            {"name": "/reliquia entrar", "desc": "Tenta entrar em uma câmara de relíquias."},
            {"name": "/reliquia usar", "desc": "Usa energia de relíquia."},
            {"name": "/reliquia status", "desc": "Verifica seu status de relíquias."},
        ],
    },
    "Administração": {
        "desc": "Comandos apenas para administradores do bot.",
        "commands": [
            {"name": "/admin add_item", "desc": "Adiciona itens a um jogador."},
            {"name": "/admin set_status", "desc": "Define o status de um jogador."},
            {"name": "/admin set_hp", "desc": "Define o HP de um jogador."},
            {"name": "/admin give_money", "desc": "Dá dinheiro a um jogador."},
            {"name": "/admin give_xp", "desc": "Dá XP a um jogador."},
            {"name": "/admin reset_player", "desc": "Reseta o perfil de um jogador."},
            {"name": "/admin debug_player", "desc": "Mostra todos os dados de um jogador."},
            {"name": "/admin sync_roles", "desc": "Força a sincronização de cargos."},
            {"name": "/admin spawn_boss", "desc": "Gera um boss global."},
            {"name": "/admin set_location", "desc": "Define a localização de um jogador."},
        ],
    },
}


class HelpSelect(Select):
    def __init__(self, categories):
        options = []
        for category_name, category_data in categories.items():
            options.append(
                discord.SelectOption(
                    label=category_name,
                    description=category_data["desc"],
                    emoji="📚" if category_name == "Geral" else (
                        CUSTOM_EMOJIS.get('espada_rpg') if category_name == "Combate" else (
                            CUSTOM_EMOJIS.get('location_icon') if category_name == "Mundo" else (
                                CUSTOM_EMOJIS.get('money_icon') if category_name == "Economia" else (
                                    CUSTOM_EMOJIS.get('class_icon') if category_name == "Classes e Poderes" else (
                                        CUSTOM_EMOJIS.get('clan_icon') if category_name == "Clãs" else (
                                            "✨" if category_name == "Bênçãos" else (
                                                "💎" if category_name == "Relíquias" else (
                                                    "⚙️" if category_name == "Administração" else "❓"
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        super().__init__(
            placeholder="Escolha uma categoria de ajuda...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="help_category_select",
        )
        self.categories = categories

    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        category_data = self.categories.get(selected_category)

        if not category_data:
            await interaction.response.send_message(
                "Categoria de ajuda não encontrada.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📚 Ajuda: {selected_category} Comandos",
            description=category_data["desc"],
            color=discord.Color.blue(),
        )

        for command in category_data["commands"]:
            embed.add_field(
                name=command["name"], value=command["desc"], inline=False
            )
        embed.set_footer(text="Use o menu para navegar entre as categorias.")

        await interaction.response.edit_message(embed=embed)


class HelpView(View):
    def __init__(self, ephemeral: bool = False):
        super().__init__(timeout=180)
        self.add_item(HelpSelect(HELP_CATEGORIES))
        self.ephemeral = ephemeral

    async def on_timeout(self):
        # Desabilita todos os itens da view quando o tempo limite expira
        for item in self.children:
            item.disabled = True
        # Tenta editar a mensagem para refletir a view desabilitada
        try:
            # Verifica se a mensagem ainda existe e se é uma interação original ou uma resposta de acompanhamento
            # Não é possível editar interações que já responderam e não foram seguidas
            if self.message:
                await self.message.edit(view=self)
            elif hasattr(self, 'interaction') and not self.interaction.is_done():
                 await self.interaction.edit_original_response(view=self)
        except discord.NotFound:
            pass # A mensagem foi deletada, nada a fazer
        except Exception as e:
            print(f"Erro ao desabilitar view de ajuda no timeout: {e}")