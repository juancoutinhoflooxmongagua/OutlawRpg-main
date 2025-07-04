# data_manager.py
import json
import os

# Importa as configurações necessárias
from config import (
    STARTING_LOCATION,
    BOSSES_DATA,
    DEFAULT_PLAYER_BOSS_DATA,
    INITIAL_CLAN_DATA,
)

# --- Configuração dos Caminhos ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_DATA_FILE = os.path.join(SCRIPT_DIR, "outlaws_data.json")
CLAN_DATA_FILE = os.path.join(SCRIPT_DIR, "clans_data.json")

# --- Bancos de Dados em Memória ---
player_database = {}
clan_database = {}

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

    # Garante a inicialização completa de 'boss_data'
    if "boss_data" not in player_data:
        player_data["boss_data"] = DEFAULT_PLAYER_BOSS_DATA.copy()

    if "defeated_bosses" not in player_data["boss_data"]:
        player_data["boss_data"]["defeated_bosses"] = []

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
    """Carrega os dados dos jogadores do arquivo JSON e inicializa os padrões."""
    global player_database
    try:
        with open(PLAYER_DATA_FILE, "r", encoding="utf-8") as f:
            player_database = json.load(f)
        # Garante que todos os jogadores carregados tenham os campos padrão
        for player_data in player_database.values():
            _initialize_player_defaults(player_data)
    except FileNotFoundError:
        print(
            "Arquivo de dados do jogador não encontrado. Um novo será criado ao salvar."
        )
        player_database = {}
    except json.JSONDecodeError as e:
        print(
            f"ERRO: Não foi possível decodificar o JSON de dados do jogador: {e}. Um novo arquivo será usado."
        )
        player_database = {}


def load_clan_data():
    """Carrega os dados dos clãs do arquivo JSON e inicializa os padrões."""
    global clan_database
    try:
        with open(CLAN_DATA_FILE, "r", encoding="utf-8") as f:
            clan_database = json.load(f)
        # Garante que todos os clãs carregados tenham os campos padrão
        for clan_id, clan_data in clan_database.items():
            _initialize_clan_defaults(clan_data, clan_id)
    except FileNotFoundError:
        print("Arquivo de dados do clã não encontrado. Um novo será criado ao salvar.")
        clan_database = {}
    except json.JSONDecodeError as e:
        print(
            f"ERRO: Não foi possível decodificar o JSON de dados do clã: {e}. Um novo arquivo será usado."
        )
        clan_database = {}


# --- Funções de Salvamento ---


def save_data():
    """Salva os dados dos jogadores no arquivo JSON."""
    try:
        with open(PLAYER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(player_database, f, indent=4)
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
