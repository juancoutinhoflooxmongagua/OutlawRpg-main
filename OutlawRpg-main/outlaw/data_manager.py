# data_manager.py

import json
import os

# Correctly import the template for player boss data
from config import STARTING_LOCATION, BOSSES_DATA

# --- CONFIGURATION FOR DATA MANAGER ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_DATA_FILE = os.path.join(SCRIPT_DIR, "outlaws_data.json")

# This global variable will no longer represent an active global boss.
# It can be repurposed for global stats (e.g., global_defeated_bosses_count) if needed.
# For now, it will be initialized empty and effectively unused for active boss tracking.
# The boss_state.json file will no longer be used for live boss data.
current_boss_data = {}


# This is the TEMPLATE for the initial player boss data structure.
DEFAULT_PLAYER_BOSS_DATA = {
    "current_boss_id": None,
    "current_boss_hp": 0,
    "last_spawn_channel_id": None,
    "boss_progression_level": "Colosso de Pedra",
    "defeated_bosses": [],
    "last_spawn_timestamp": 0,  # Added for cooldown on boss spawn per player
}


def load_data():
    """Loads player data from the JSON file."""
    global player_database, current_boss_data

    # Load player data
    if not os.path.exists(PLAYER_DATA_FILE):
        player_database = {}
    try:
        with open(PLAYER_DATA_FILE, "r", encoding="utf-8") as f:
            player_database = json.load(f)
            # Ensure 'location', 'boss_data', and 'location_kill_tracker' are set for existing players
            for user_id_str, data in player_database.items():
                if "location" not in data:
                    data["location"] = STARTING_LOCATION
                if "boss_data" not in data:
                    data["boss_data"] = DEFAULT_PLAYER_BOSS_DATA.copy()
                    if data["boss_data"].get("boss_progression_level") is None:
                        if BOSSES_DATA:
                            data["boss_data"]["boss_progression_level"] = list(
                                BOSSES_DATA.keys()
                            )[0]
                        else:
                            data["boss_data"][
                                "boss_progression_level"
                            ] = "No Bosses Defined"
                if "defeated_bosses" not in data["boss_data"]:
                    data["boss_data"]["defeated_bosses"] = []
                # NEW: Initialize location_kill_tracker
                if "location_kill_tracker" not in data:
                    data["location_kill_tracker"] = {}

        # Reset current_boss_data (global) on load, as it's no longer used for active individual boss tracking.
        # This global variable might be used for other purposes later (e.g., global stats)
        # For now, ensure it's not holding stale active boss data.
        current_boss_data.clear()
        current_boss_data["global_stats_example"] = (
            "This is a placeholder for global stats if needed."
        )

    except (json.JSONDecodeError, IOError) as e:
        print(f"ERRO: Não foi possível carregar dados do jogador: {e}")
        player_database = {}

    return player_database


def save_data():
    """Saves player data to the JSON file."""
    try:
        with open(PLAYER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(player_database, f, indent=4)
    except IOError as e:
        print(f"CRITICAL ERROR: Não foi possível salvar dados do jogador: {e}")

    # The global boss_state.json is no longer actively managed for live boss state.
    # If `current_boss_data` is used for other global stats, it can still be saved.
    # For now, we'll remove saving it for active boss data.
    # If needed for other purposes, uncomment and adjust:
    # try:
    #     with open(BOSS_STATE_FILE, "w", encoding="utf-8") as f:
    #         json.dump(current_boss_data, f, indent=4)
    # except IOError as e:
    #     print(f"ERRO CRÍTICO: Não foi possível salvar dados do boss global (se ainda usado): {e}")


def get_player_data(user_id: int | str) -> dict | None:
    """
    Retrieves player data from the database.
    Ensures 'boss_data' and 'location_kill_tracker' are initialized if not present.
    """
    user_id_str = str(user_id)
    if user_id_str not in player_database:
        return None

    # Ensure boss_data is initialized
    if "boss_data" not in player_database[user_id_str]:
        player_database[user_id_str]["boss_data"] = DEFAULT_PLAYER_BOSS_DATA.copy()
        if (
            player_database[user_id_str]["boss_data"].get("boss_progression_level")
            is None
        ):
            if BOSSES_DATA:
                player_database[user_id_str]["boss_data"]["boss_progression_level"] = (
                    list(BOSSES_DATA.keys())[0]
                )
            else:
                player_database[user_id_str]["boss_data"][
                    "boss_progression_level"
                ] = "No Bosses Defined"
        if "defeated_bosses" not in player_database[user_id_str]["boss_data"]:
            player_database[user_id_str]["boss_data"]["defeated_bosses"] = []

    # NEW: Ensure location_kill_tracker is initialized
    if "location_kill_tracker" not in player_database[user_id_str]:
        player_database[user_id_str]["location_kill_tracker"] = {}

    return player_database.get(user_id_str)


# Load data when this module is imported
player_database = load_data()
