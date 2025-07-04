# data_manager.py
import json
import os

# Importa as configurações necessárias
from config import (
    STARTING_LOCATION,
    BOSSES_DATA,
    DEFAULT_PLAYER_BOSS_DATA,  # Keep this for player-specific boss data initialization
    INITIAL_CLAN_DATA,
)

# --- Configuração dos Caminhos ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_DATA_FILE = os.path.join(SCRIPT_DIR, "outlaws_data.json")
CLAN_DATA_FILE = os.path.join(SCRIPT_DIR, "clans_data.json")

# --- Bancos de Dados em Memória ---
player_database = {}
clan_database = {}
current_boss_data = {}  # Declare global current_boss_data here

# --- Funções Auxiliares Privadas ---


def _initialize_player_defaults(player_data: dict):
    """Garante que um dicionário de dados de jogador contenha todos os campos padrão."""
    if "location" not in player_data:
        player_data["location"] = STARTING_LOCATION

    if "clan_id" not in player_data:
        player_data["clan_id"] = None
    if "clan_role" not in player_data:
        player_data["clan_role"] = None

    if "location_kill_tracker" not in player_data:
        player_data["location_kill_tracker"] = {}

    # Ensure player's specific boss_data is initialized
    if "boss_data" not in player_data:
        player_data["boss_data"] = DEFAULT_PLAYER_BOSS_DATA.copy()
    else:
        # Ensure all sub-fields of boss_data are present based on DEFAULT_PLAYER_BOSS_DATA
        for key, value in DEFAULT_PLAYER_BOSS_DATA.items():
            if key not in player_data["boss_data"]:
                player_data["boss_data"][key] = value

    if player_data["boss_data"].get("boss_progression_level") is None:
        if BOSSES_DATA:
            player_data["boss_data"]["boss_progression_level"] = list(
                BOSSES_DATA.keys()
            )[0]
        else:
            player_data["boss_data"]["boss_progression_level"] = "Nenhum Boss Definido"


def _initialize_clan_defaults(clan_data: dict, clan_id: str):
    """Garante que um dicionário de dados de clã contenha todos os campos padrão."""
    if "id" not in clan_data:
        clan_data["id"] = clan_id
    if "money" not in clan_data:
        clan_data["money"] = INITIAL_CLAN_DATA.get("money", 0)


# --- Funções de Carregamento ---


def load_data():
    """Carrega os dados dos jogadores e o estado global do boss do arquivo JSON e inicializa os padrões."""
    global player_database
    global current_boss_data  # Make sure to declare global
    try:
        with open(PLAYER_DATA_FILE, "r", encoding="utf-8") as f:
            full_data = json.load(f)  # Load the entire file content
            player_database.clear()  # Clear existing data
            player_database.update(
                full_data.get("player_data", {})
            )  # Load player data from 'player_data' key

            current_boss_data.clear()  # Clear existing data
            # Load global boss state from 'global_boss_state' key
            global_boss_state_loaded = full_data.get("global_boss_state", {})
            current_boss_data.update(global_boss_state_loaded)

        # Initialize player defaults for all loaded players
        for player_data_item in player_database.values():
            _initialize_player_defaults(player_data_item)

        # Initialize global current_boss_data if it was empty after loading
        if not current_boss_data or not current_boss_data.get("active_boss_id"):
            if BOSSES_DATA:
                # Default to the first boss in BOSSES_DATA
                first_boss_id = list(BOSSES_DATA.keys())[0]
                current_boss_data.update(
                    {
                        "active_boss_id": first_boss_id,
                        "hp": BOSSES_DATA[first_boss_id]["max_hp"],
                        "participants": [],
                        "channel_id": None,
                    }
                )
            else:
                current_boss_data.clear()  # Ensure it's empty if no bosses are defined

    except FileNotFoundError:
        print(
            "Arquivo de dados do jogador não encontrado. Um novo será criado ao salvar."
        )
        player_database.clear()
        current_boss_data.clear()
    except json.JSONDecodeError as e:
        print(
            f"ERRO: Não foi possível decodificar o JSON de dados do jogador: {e}. Um novo arquivo será usado."
        )
        player_database.clear()
        current_boss_data.clear()


def load_clan_data():
    """Carrega os dados dos clãs do arquivo JSON e inicializa os padrões."""
    global clan_database
    try:
        with open(CLAN_DATA_FILE, "r", encoding="utf-8") as f:
            clan_database.clear()
            clan_database.update(json.load(f))
        # Garante que todos os clãs carregados tenham os campos padrão
        for clan_id, clan_data_item in clan_database.items():
            _initialize_clan_defaults(clan_data_item, clan_id)
    except FileNotFoundError:
        print("Arquivo de dados do clã não encontrado. Um novo será criado ao salvar.")
        clan_database.clear()
    except json.JSONDecodeError as e:
        print(
            f"ERRO: Não foi possível decodificar o JSON de dados do clã: {e}. Um novo arquivo será usado."
        )
        clan_database.clear()


# --- Funções de Salvamento ---


def save_data():
    """Salva os dados dos jogadores e o estado global do boss no arquivo JSON."""
    try:
        data_to_save = {
            "player_data": player_database,
            "global_boss_state": current_boss_data,  # Save the global boss state
        }
        with open(PLAYER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)
    except IOError as e:
        print(f"ERRO CRÍTICO: Não foi possível salvar os dados do jogador: {e}")


def save_clan_data():
    """Salva os dados dos clãs no arquivo JSON."""
    try:
        with open(CLAN_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(clan_database, f, indent=4)
    except IOError as e:
        print(f"ERRO CRÍTICO: Não foi possível salvar os dados do clã: {e}")


# --- Funções de Acesso a Dados ---


def get_player_data(user_id: int | str) -> dict | None:
    """
    Recupera os dados de um jogador do banco de dados, garantindo que
    todos os campos padrão estejam inicializados.
    """
    user_id_str = str(user_id)
    player_data = player_database.get(user_id_str)

    if player_data:
        # Garante a consistência dos dados sempre que um jogador é acessado
        _initialize_player_defaults(player_data)

    return player_data


# --- Carregamento Inicial ---
# Carrega os dados dos arquivos para a memória quando o módulo é importado pela primeira vez.
load_data()
load_clan_data()
