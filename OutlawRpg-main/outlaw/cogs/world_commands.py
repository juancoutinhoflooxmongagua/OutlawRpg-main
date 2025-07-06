import discord # Added import for discord
from discord.ext import commands
from discord import app_commands, Embed, Color, Interaction
import random
from datetime import datetime, timedelta

from data_manager import ( # Changed from ..data_manager to data_manager
    get_player_data,
    save_data,
    player_database,
)
from config import ( # Changed from ..config to config
    WORLD_MAP,
    STARTING_LOCATION,
    CUSTOM_EMOJIS,
)
from custom_checks import ( # Changed from ..custom_checks to custom_checks
    check_player_exists,
    is_in_city,
    is_not_in_city,
) # Alterado para importação relativa
from utils import ( # Changed from ..utils to utils
    format_cooldown,
    get_remaining_cooldown,
    calculate_effective_stats,
) # Alterado para importação relativa


class WorldCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="viajar", description="Viaja para um local conectado ao seu local atual."
    )
    @app_commands.check(check_player_exists)
    @app_commands.check(is_in_city)
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)  # 1 minuto de cooldown
    async def viajar(self, i: Interaction, destino: str):
        player_data = get_player_data(i.user.id)
        current_location_name = player_data.get("location")
        current_location_info = WORLD_MAP.get(current_location_name)

        if player_data.get("status") == "dead":
            await i.response.send_message("Mortos não viajam.", ephemeral=True)
            return

        if not current_location_info:
            await i.response.send_message(
                "Sua localização atual não foi encontrada no mapa.", ephemeral=True
            )
            return

        if destino not in current_location_info["conecta"]:
            await i.response.send_message(
                f"Você não pode viajar para **{destino}** de **{current_location_name}**. Verifique os locais conectados.",
                ephemeral=True,
            )
            return

        destination_info = WORLD_MAP.get(destino)
        if not destination_info:
            await i.response.send_message(
                "O destino especificado não existe no mapa.", ephemeral=True
            )
            return

        # Verificar requisitos de nível
        required_level = destination_info.get("required_level")
        if required_level and player_data.get("level", 1) < required_level:
            await i.response.send_message(
                f"Você precisa ser pelo menos Nível **{required_level}** para viajar para **{destino}**.",
                ephemeral=True,
            )
            return

        # Verificar requisito de item
        required_item = destination_info.get("required_item")
        if required_item:
            item_info = ITEMS_DATA.get(required_item)
            if not item_info or player_data.get("inventory", {}).get(required_item, 0) == 0:
                await i.response.send_message(
                    f"Você precisa de {item_info.get('emoji', '')} **{item_info.get('name', required_item)}** para acessar **{destino}**.",
                    ephemeral=True,
                )
                return

        # Verificar requisito de boss derrotado
        required_boss = destination_info.get("required_previous_boss")
        if required_boss:
            # Assumindo que player_data["boss_data"]["defeated_bosses"] é uma lista de IDs de bosses derrotados
            if required_boss not in player_data.get("boss_data", {}).get("defeated_bosses", []):
                await i.response.send_message(
                    f"Você precisa derrotar o chefe anterior ('{required_boss}') para viajar para **{destino}**.",
                    ephemeral=True,
                )
                return

        player_data["location"] = destino
        player_data["hp"] = player_data["max_hp"]  # Cura completa ao viajar
        save_data()

        embed = Embed(
            title=f"🗺️ Viagem Concluída!",
            description=f"Você viajou de **{current_location_info['emoji']} {current_location_name}** para **{destination_info['emoji']} {destino}**.",
            color=Color.blue(),
        )
        embed.add_field(name="Sua Saúde", value=f"{player_data['hp']}/{player_data['max_hp']} HP")
        embed.add_field(name="Descrição do Local", value=destination_info['desc'], inline=False)
        embed.set_footer(text="Sua saúde foi totalmente restaurada ao chegar.")
        await i.response.send_message(embed=embed)

    @app_commands.command(
        name="local", description="Mostra sua localização atual e locais conectados."
    )
    @app_commands.check(check_player_exists)
    async def local(self, i: Interaction):
        player_data = get_player_data(i.user.id)
        current_location_name = player_data.get("location")
        current_location_info = WORLD_MAP.get(current_location_name)

        if not current_location_info:
            await i.response.send_message(
                "Sua localização não foi encontrada. Algo deu errado!", ephemeral=True
            )
            return

        connected_locations_info = []
        for connected_loc_name in current_location_info["conecta"]:
            loc_info = WORLD_MAP.get(connected_loc_name)
            if loc_info:
                # Verificar requisitos para cada local conectado
                requirements = []
                if loc_info.get("required_level") and player_data.get("level", 1) < loc_info["required_level"]:
                    requirements.append(f"Nível {loc_info['required_level']}")
                if loc_info.get("required_item"):
                    item_name = ITEMS_DATA.get(loc_info["required_item"], {}).get("name", loc_info["required_item"])
                    if player_data.get("inventory", {}).get(loc_info["required_item"], 0) == 0:
                        requirements.append(f"Item: {item_name}")
                if loc_info.get("required_previous_boss"):
                    if loc_info["required_previous_boss"] not in player_data.get("boss_data", {}).get("defeated_bosses", []):
                        requirements.append(f"Derrotar: {loc_info['required_previous_boss'].replace('_', ' ').title()}")

                req_str = f" (Requer: {', '.join(requirements)})" if requirements else ""
                connected_locations_info.append(
                    f"{loc_info['emoji']} **{loc_info['name']}** ({loc_info['type'].capitalize()}){req_str}"
                )
        
        connected_locations_text = "\n".join(connected_locations_info) if connected_locations_info else "Nenhum local conectado encontrado."


        embed = Embed(
            title=f"📍 Sua Localização Atual: {current_location_info['emoji']} {current_location_name}",
            description=f"*{current_location_info['desc']}*",
            color=Color.orange(),
        )
        embed.add_field(name="Tipo de Local", value=current_location_info["type"].capitalize())
        embed.add_field(name="Locais Conectados", value=connected_locations_text, inline=False)
        embed.set_footer(text="Use /viajar [destino] para mover-se.")

        await i.response.send_message(embed=embed)


    @app_commands.command(
        name="reviver",
        description="Renasça dos mortos na última cidade que você visitou ou no Abrigo dos Foras-da-Lei.",
    )
    @app_commands.check(check_player_exists)
    @app_commands.check(is_not_in_city)
    @app_commands.checks.cooldown(1, 300, key=lambda i: i.user.id) # 5 minutos de cooldown para reviver
    async def reviver(self, i: Interaction):
        player_data = get_player_data(i.user.id)

        if player_data.get("status") != "dead":
            await i.response.send_message("Você não está morto!", ephemeral=True)
            return

        player_data["hp"] = player_data["max_hp"] # Restaura HP
        player_data["status"] = "online" # Altera status para online
        player_data["location"] = STARTING_LOCATION # Retorna ao Abrigo dos Foras-da-Lei
        save_data()

        embed = Embed(
            title="✨ Você Renasceu!",
            description=f"Você foi trazido de volta à vida e agora está no **{WORLD_MAP[STARTING_LOCATION]['emoji']} {STARTING_LOCATION}** com HP completo!",
            color=Color.green(),
        )
        embed.add_field(name="Sua Saúde", value=f"{player_data['hp']}/{player_data['max_hp']} HP")
        embed.set_footer(text="Cuidado na próxima vez!")

        await i.response.send_message(embed=embed)


    @app_commands.command(name="mapa", description="Mostra o mapa do mundo.")
    @app_commands.check(check_player_exists)
    async def mapa(self, i: Interaction):
        player_data = get_player_data(i.user.id)

        # Crie um mapa visual ou textual do mundo
        map_display = ["**Mapa do Mundo:**"]
        for location_name, location_info in WORLD_MAP.items():
            current_marker = " 📍" if player_data.get("location") == location_name else ""
            
            # Adicionar informação de conexão para cada local (opcional, pode ser muito detalhado)
            # connected_names = [WORLD_MAP[conn_name]['emoji'] + WORLD_MAP[conn_name]['name'] for conn_name in location_info['conecta']]
            # connections_str = f" -> {', '.join(connected_names)}" if connected_names else ""
            
            map_display.append(
                f"{location_info['emoji']} **{location_name}** ({location_info['type'].capitalize()}){current_marker}"
            )

        embed = Embed(
            title="🌍 Mapa do Mundo de Outlaws",
            description="\n".join(map_display),
            color=Color.dark_purple(),
        )
        await i.response.send_message(embed=embed)