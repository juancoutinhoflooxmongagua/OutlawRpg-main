from discord import app_commands, Interaction
from data_manager import get_player_data
from config import WORLD_MAP, STARTING_LOCATION


class NotInCity(app_commands.CheckFailure):
    """Raised when a command is used outside of a city location."""

    pass


class NotInWilderness(app_commands.CheckFailure):
    """Raised when a command is used outside of a wilderness location."""

    pass


def check_player_exists(i: Interaction):
    """Checks if the interacting user has a character profile and is not AFK."""
    p = get_player_data(i.user.id)
    if not p:
        raise app_commands.CheckFailure(
            "Você não possui uma ficha de personagem. Crie uma com `/criar_ficha`!"
        )
    if p.get("status") == "afk":
        raise app_commands.CheckFailure(
            "Você está em modo AFK e não pode usar comandos. Use `/voltar` para sair do modo AFK."
        )
    return True


def is_in_city(i: Interaction):
    """Checks if the player's current location is a 'city' type."""
    player_data = get_player_data(i.user.id)
    if not player_data:
        raise app_commands.CheckFailure("Você não possui uma ficha de personagem.")

    current_location_id = player_data.get("location", STARTING_LOCATION)
    location_info = WORLD_MAP.get(current_location_id, {})

    if location_info.get("type") == "cidade":
        return True
    raise NotInCity(
        f"Você está em uma área selvagem. Este comando só pode ser usado em uma cidade. Sua localização atual: {location_info.get('name', 'Desconhecida')}."
    )


def is_in_wilderness(i: Interaction):
    """Checks if the player's current location is a 'wilderness' type."""
    player_data = get_player_data(i.user.id)
    if not player_data:
        raise app_commands.CheckFailure("Você não possui uma ficha de personagem.")

    current_location_id = player_data.get("location", STARTING_LOCATION)
    location_info = WORLD_MAP.get(current_location_id, {})

    if location_info.get("type") == "selvagem":
        return True
    raise NotInWilderness(
        f"Você está em uma cidade. Este comando só pode ser usado em áreas selvagens. Sua localização atual: {location_info.get('name', 'Desconhecida')}."
    )
