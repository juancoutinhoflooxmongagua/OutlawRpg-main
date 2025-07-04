# data_manager.py

import json
import os

# Correctly import the template for player boss data
from config import (
    STARTING_LOCATION,
    BOSSES_DATA,
    DEFAULT_PLAYER_BOSS_DATA,
    INITIAL_CLAN_DATA,
)  # Updated import

# --- CONFIGURATION FOR DATA MANAGER ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_DATA_FILE = os.path.join(SCRIPT_DIR, "outlaws_data.json")
CLAN_DATA_FILE = os.path.join(SCRIPT_DIR, "clans_data.json")  # NEW: Clan data file

# This global variable will no longer represent an active global boss.
# It can be repurposed for global stats (e.g., global_defeated_bosses_count) if needed).
# For now, it will be initialized empty and effectively unused for active boss tracking.
# The boss_state.json file will no longer be used for live boss data.
current_boss_data = {}


# Global variables for player and clan data
player_database = {}
clan_database = {}  # NEW: Global clan database


def load_data():
    """Loads player data from the JSON file and initializes new fields."""
    global player_database, current_boss_data

    # Load player data
    if not os.path.exists(PLAYER_DATA_FILE):
        player_database = {}
    try:
        with open(PLAYER_DATA_FILE, "r", encoding="utf-8") as f:
            player_database = json.load(f)
            # Ensure 'location', 'boss_data', 'location_kill_tracker', 'clan_id', 'clan_role' are set for existing players
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
                # NEW: Initialize clan data fields for players
                if "clan_id" not in data:
                    data["clan_id"] = None
                if "clan_role" not in data:
                    data["clan_role"] = None

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


def load_clan_data():  # NEW FUNCTION
    """Loads clan data from the JSON file."""
    global clan_database
    if not os.path.exists(CLAN_DATA_FILE):
        clan_database = {}
    try:
        with open(CLAN_DATA_FILE, "r", encoding="utf-8") as f:
            clan_database = json.load(f)
            # Ensure 'money' field is set for existing clans if not present
            for clan_id_str, data in clan_database.items():
                if "money" not in data:
                    data["money"] = INITIAL_CLAN_DATA[
                        "money"
                    ]  # Initialize using config's default
                if (
                    "id" not in data
                ):  # Ensure 'id' is stored within the clan data itself
                    data["id"] = clan_id_str
    except (json.JSONDecodeError, IOError) as e:
        print(f"ERRO: Não foi possível carregar dados do clã: {e}")
        clan_database = {}
    return clan_database


def save_clan_data():  # NEW FUNCTION
    """Saves clan data to the JSON file."""
    try:
        with open(CLAN_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(clan_database, f, indent=4)
    except IOError as e:
        print(f"CRITICAL ERROR: Não foi possível salvar dados do clã: {e}")


def get_player_data(user_id: int | str) -> dict | None:
    """
    Retrieves player data from the database.
    Ensures 'boss_data', 'location_kill_tracker', 'clan_id', and 'clan_role' are initialized if not present.
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

    # NEW: Ensure clan data fields are initialized for players
    if "clan_id" not in player_database[user_id_str]:
        player_database[user_id_str]["clan_id"] = None
    if "clan_role" not in player_database[user_id_str]:
        player_database[user_id_str]["clan_role"] = None

    return player_database.get(user_id_str)


# Load data when this module is imported
player_database = load_data()
clan_database = load_clan_data()  # NEW: Load clan data on import
