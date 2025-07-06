# File: OutlawRpg-main/outlaw/data_manager.py

import json
import os
import threading
import time

# Importar constantes do arquivo de configuração
from config import (
    INITIAL_MONEY,
    INITIAL_HP,
    INITIAL_ATTACK,
    INITIAL_SPECIAL_ATTACK,
    MAX_ENERGY,
    STARTING_LOCATION,
    NEW_CHARACTER_ROLE_ID,
    DEFAULT_CLAN_XP,
    INITIAL_CLAN_DATA,
    ATTRIBUTE_POINTS_PER_LEVEL, # Added this, as it's used in get_player_data
    HOURS_BETWEEN_KEY_CLAIMS, # Added for check_and_add_keys and get_time_until_next_key_claim
    MAX_RELIC_KEYS, # Added for check_and_add_keys
)


# Caminhos dos arquivos de dados
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_DATA_FILE = os.path.join(SCRIPT_DIR, "outlaws_data.json")
CLAN_DATA_FILE = os.path.join(SCRIPT_DIR, "clans_data.json")

# Bancos de dados em memória
player_database = {}
clan_database = {}
data_lock = threading.Lock()  # Para evitar condições de corrida ao salvar/carregar

# --- Funções de Carregamento e Salvamento de Dados ---


def load_data():
    """Carrega dados dos jogadores do arquivo JSON."""
    global player_database
    with data_lock:
        if os.path.exists(PLAYER_DATA_FILE):
            try:
                with open(PLAYER_DATA_FILE, "r", encoding="utf-8") as f:
                    player_database = json.load(f)
                print(f"Dados de {len(player_database)} jogadores carregados.")
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON de player_data.json: {e}")
                player_database = {}  # Resetar para evitar dados corrompidos
            except Exception as e:
                print(f"Erro ao carregar player_data.json: {e}")
                player_database = {}
        else:
            player_database = {}
            print("Arquivo outlaws_data.json não encontrado. Iniciando um novo.")


def save_data():
    """Salva dados dos jogadores no arquivo JSON."""
    with data_lock:
        try:
            with open(PLAYER_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(player_database, f, indent=4)
            # print("Dados dos jogadores salvos.") # Desativado para reduzir spam no console
        except Exception as e:
            print(f"Erro ao salvar player_data.json: {e}")


def load_clan_data():
    """Carrega dados dos clãs do arquivo JSON."""
    global clan_database
    with data_lock:
        if os.path.exists(CLAN_DATA_FILE):
            try:
                with open(CLAN_DATA_FILE, "r", encoding="utf-8") as f:
                    clan_database = json.load(f)
                print(f"Dados de {len(clan_database)} clãs carregados.")
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON de clans_data.json: {e}")
                clan_database = {}  # Resetar para evitar dados corrompidos
            except Exception as e:
                print(f"Erro ao carregar clans_data.json: {e}")
                clan_database = {}
        else:
            clan_database = {}
            print("Arquivo clans_data.json não encontrado. Iniciando um novo.")


def save_clan_data():
    """Salva dados dos clãs no arquivo JSON."""
    with data_lock:
        try:
            with open(CLAN_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(clan_database, f, indent=4)
            # print("Dados dos clãs salvos.") # Desativado para reduzir spam no console
        except Exception as e:
            print(f"Erro ao salvar clans_data.json: {e}")


# --- Funções de Acesso e Inicialização de Dados do Jogador ---


def get_player_data(user_id: str) -> dict:
    """
    Retorna os dados de um jogador. Se o jogador não existir, inicializa com dados padrão.
    A inicialização agora inclui os novos campos de relíquias e chaves.
    """
    with data_lock:
        if user_id not in player_database:
            player_database[user_id] = {
                "id": user_id,
                "created_at": int(time.time()),
                "name": None,  # Será definido após a escolha da classe
                "level": 1,
                "xp": 0,
                "attribute_points": ATTRIBUTE_POINTS_PER_LEVEL,
                "hp": INITIAL_HP,
                "max_hp": INITIAL_HP,
                "attack": INITIAL_ATTACK,
                "special_attack": INITIAL_SPECIAL_ATTACK,
                "money": INITIAL_MONEY,
                "inventory": {},
                "location": STARTING_LOCATION,
                "energy": MAX_ENERGY,
                "kills": 0,
                "deaths": 0,
                "bounty": 0,
                "status": "online",  # online, afk, dead
                "last_attack_time": 0,
                "last_special_attack_time": 0,
                "last_message_xp_time": 0,
                "rebirths": 0,  # Contador de renascimentos
                "equipped_items": {},  # Itens equipados (ex: {"weapon": "espada_lendaria"})
                "current_transformation": None,  # Classe de transformação ativa
                "transform_end_time": 0,  # Quando a transformação termina (timestamp)
                "blessings": {},  # Ativação/expiração de bênçãos
                "relics": {},  # NOVO: Relíquias possuídas (id_reliquia: True/False)
                "relic_energy": 0,  # NOVO: Energia separada para relíquias
                "relic_keys": 0,  # NOVO: Chaves para abrir câmaras de relíquias
                "last_key_claim_time": 0, # NOVO: Timestamp da última reivindicação de chave
                "relics_inventory": [], # NOVO: Lista de IDs de relíquias obtidas, for /bau
                "active_relic_chamber": None, # NOVO: ID da câmara de relíquia ativa
                "relic_chamber_found_time": 0, # NOVO: Timestamp de quando a câmara foi encontrada
                "clan_id": None,  # ID do clã ao qual o jogador pertence
            }
            # Ensure 'blessings' is initialized correctly
            if "blessings" not in player_database[user_id]:
                player_database[user_id]["blessings"] = {}

            # Initialize all blessing-related fields from ITEMS_DATA as False
            # Note: INITIAL_CLAN_DATA is not the right place for blessing info.
            # You'll need to iterate over ITEMS_DATA or a dedicated BLESSINGS_DATA if you have one.
            # Assuming ITEMS_DATA is where blessing types are defined.
            # This part below is likely incorrect based on what INITIAL_CLAN_DATA implies.
            # It should likely be iterating over a list of actual blessing item IDs.
            # For now, I'm commenting out the problematic part to avoid error.
            # for item_id, item_info in INITIAL_CLAN_DATA.items():
            #     if item_info.get("type") == "blessing_unlock":
            #         player_database[user_id][f"{item_id}_active"] = False
            #         player_database[user_id][f"{item_id}_end_time"] = 0
            save_data()  # Salva o novo perfil
        return player_database[user_id]


def update_player_data(user_id: str, key: str, value):
    """Atualiza um campo específico nos dados do jogador."""
    with data_lock:
        if user_id in player_database:
            player_database[user_id][key] = value
            save_data()

def add_user_money(user_id: str, amount: int):
    """Adiciona dinheiro ao jogador."""
    with data_lock:
        player_data = get_player_data(user_id) # Ensures player data is initialized
        player_data["money"] = player_data.get("money", 0) + amount
        save_data()

def add_user_energy(user_id: str, amount: int):
    """Adiciona energia ao jogador, limitado ao MAX_ENERGY."""
    with data_lock:
        player_data = get_player_data(user_id) # Ensures player data is initialized
        player_data["energy"] = min(player_data.get("energy", 0) + amount, MAX_ENERGY)
        save_data()

def check_and_add_keys(user_id: int) -> int:
    """
    Verifica se o usuário pode reivindicar novas chaves e as adiciona,
    limitado a MAX_RELIC_KEYS.
    Retorna o número de chaves adicionadas.
    """
    user_id_str = str(user_id)
    with data_lock:
        player_data = get_player_data(user_id_str)
        
        last_claim_time = player_data.get("last_key_claim_time", 0)
        current_time = datetime.now().timestamp()
        
        # Calculate how many full claim periods have passed
        time_since_last_claim = current_time - last_claim_time
        
        # Convert HOURS_BETWEEN_KEY_CLAIMS to seconds
        claim_interval_seconds = HOURS_BETWEEN_KEY_CLAIMS * 3600
        
        keys_to_add = 0
        
        if claim_interval_seconds > 0: # Avoid division by zero
            # Check if it's the first time claiming or enough time has passed
            if last_claim_time == 0:
                # If first time, grant one key immediately and set last claim time
                keys_to_add = 1
                player_data["last_key_claim_time"] = current_time
            elif time_since_last_claim >= claim_interval_seconds:
                # Calculate how many keys should be added based on elapsed time
                # It grants one key per full interval passed since the last claim.
                num_intervals_passed = int(time_since_last_claim / claim_interval_seconds)
                keys_to_add = min(num_intervals_passed, MAX_RELIC_KEYS - player_data.get("relic_keys", 0))
                
                # Update last_key_claim_time based on how many intervals were claimed
                player_data["last_key_claim_time"] += keys_to_add * claim_interval_seconds

        # Add keys, but don't exceed MAX_RELIC_KEYS
        current_keys = player_data.get("relic_keys", 0)
        new_keys = min(current_keys + keys_to_add, MAX_RELIC_KEYS)
        
        keys_actually_added = new_keys - current_keys
        player_data["relic_keys"] = new_keys
        
        if keys_actually_added > 0 or last_claim_time == 0: # Save if keys were added or if it's a new player's first claim
            save_data()
        
        return keys_actually_added


def get_time_until_next_key_claim(user_id: int) -> int:
    """
    Retorna o tempo restante em segundos até que o usuário possa reivindicar a próxima chave.
    """
    user_id_str = str(user_id)
    with data_lock:
        player_data = get_player_data(user_id_str)
        last_claim_time = player_data.get("last_key_claim_time", 0)
        current_time = datetime.now().timestamp()
        
        claim_interval_seconds = HOURS_BETWEEN_KEY_CLAIMS * 3600
        
        if last_claim_time == 0:
            return 0 # Can claim immediately if never claimed before
        
        time_elapsed_since_last_claim = current_time - last_claim_time
        
        # If enough time has passed for a key, the remaining time for the *next* key
        if time_elapsed_since_last_claim >= claim_interval_seconds:
            # Calculate how many full intervals have passed
            num_intervals_passed = int(time_elapsed_since_last_claim / claim_interval_seconds)
            # The last claimable time would be last_claim_time + (num_intervals_passed * interval)
            # The time until the *next* claim is from that point.
            next_claim_due_time = last_claim_time + (num_intervals_passed * claim_interval_seconds) + claim_interval_seconds
            
            remaining = next_claim_due_time - current_time
            return max(0, int(remaining))
        else:
            remaining = claim_interval_seconds - time_elapsed_since_last_claim
            return max(0, int(remaining))


def add_item_to_inventory(user_id: str, item_id: str, quantity: int = 1):
    """Adiciona um item ao inventário do jogador. Se o item é uma relíquia, adiciona a relics_inventory."""
    with data_lock:
        player_data = get_player_data(user_id)
        
        # Check if the item is a relic based on ITEMS_DATA (if ITEMS_DATA has a 'type' for relics)
        item_info = ITEMS_DATA.get(item_id)
        if item_info and item_info.get("type") == "relic": # Assuming 'type': 'relic' in ITEMS_DATA
            if "relics_inventory" not in player_data:
                player_data["relics_inventory"] = []
            for _ in range(quantity): # Add quantity times
                player_data["relics_inventory"].append(item_id)
        else:
            # For non-relic items, use the existing inventory structure
            player_data["inventory"][item_id] = (
                player_data["inventory"].get(item_id, 0) + quantity
            )
        save_data()

# --- Funções de Acesso e Inicialização de Dados do Clã ---


def get_clan_data(clan_id: str) -> dict:
    """Retorna os dados de um clã. Se o clã não existir, retorna um dicionário vazio."""
    with data_lock:
        return clan_database.get(clan_id, {})


def create_clan(clan_id: str, clan_name: str, leader_id: str):
    """Cria um novo clã com os dados iniciais."""
    with data_lock:
        if clan_id not in clan_database:
            new_clan_data = INITIAL_CLAN_DATA.copy()
            new_clan_data["name"] = clan_name
            new_clan_data["leader_id"] = leader_id
            new_clan_data["members"].append(leader_id)
            clan_database[clan_id] = new_clan_data
            save_clan_data()
            return True
        return False


def add_member_to_clan(clan_id: str, user_id: str):
    """Adiciona um membro a um clã existente."""
    with data_lock:
        if clan_id in clan_database:
            if user_id not in clan_database[clan_id]["members"]:
                clan_database[clan_id]["members"].append(user_id)
                save_clan_data()
                return True
        return False


def remove_member_from_clan(clan_id: str, user_id: str):
    """Remove um membro de um clã."""
    with data_lock:
        if clan_id in clan_database:
            if user_id in clan_database[clan_id]["members"]:
                clan_database[clan_id]["members"].remove(user_id)
                # Se o líder for removido, e houver outros membros, transferir liderança
                if clan_database[clan_id]["leader_id"] == user_id:
                    if clan_database[clan_id]["members"]:
                        clan_database[clan_id]["leader_id"] = clan_database[clan_id][
                            "members"
                        ][0]
                    else:
                        del clan_database[clan_id]  # Apagar clã se não houver membros
                save_clan_data()
                return True
        return False


def delete_clan(clan_id: str):
    """Deleta um clã."""
    with data_lock:
        if clan_id in clan_database:
            del clan_database[clan_id]
            save_clan_data()
            return True
        return False


# Carregar dados ao iniciar o módulo
load_data()
load_clan_data()