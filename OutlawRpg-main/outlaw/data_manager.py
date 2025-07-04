# data_manager.py

import json
import os

# Correctly import the template for player boss data
from config import STARTING_LOCATION, BOSSES_DATA, DEFAULT_PLAYER_BOSS_DATA

# --- CONFIGURATION FOR DATA MANAGER ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_DATA_FILE = os.path.join(SCRIPT_DIR, "outlaws_data.json")
# This file is now optional/obsolete if you don't track a 'global' boss state separately
BOSS_STATE_FILE = os.path.join(SCRIPT_DIR, "boss_state.json")

# Global variable to hold the loaded player data
player_database = {}
# This variable no longer represents THE active global boss.
# It can be repurposed for global stats (e.g., global_defeated_bosses) if you wish.
current_boss_data = {}


def load_data():
    """Loads player data from the JSON file."""
    global player_database, current_boss_data

    # Load player data
    if not os.path.exists(PLAYER_DATA_FILE):
        player_database = {}
    try:
        with open(PLAYER_DATA_FILE, "r", encoding="utf-8") as f:
            player_database = json.load(f)
            # Ensure 'location' and 'boss_data' are set for existing players
            for user_id_str, data in player_database.items():
                if "location" not in data:
                    data["location"] = STARTING_LOCATION
                # NEW: Initialize boss_data for existing players if they don't have it
                if "boss_data" not in data:
                    data["boss_data"] = DEFAULT_PLAYER_BOSS_DATA.copy()
                    # Ensure the first boss to unlock is set
                    if (
                        data["boss_data"].get("boss_progression_level") is None
                    ):  # Use .get for safety
                        if BOSSES_DATA:
                            data["boss_data"]["boss_progression_level"] = list(
                                BOSSES_DATA.keys()
                            )[0]
                        else:
                            data["boss_data"][
                                "boss_progression_level"
                            ] = "No Bosses Defined"
                # Ensure defeated_bosses list exists within boss_data
                if "defeated_bosses" not in data["boss_data"]:
                    data["boss_data"]["defeated_bosses"] = []

        # Optional: Load/initialize a global boss state file if still needed for other purposes
        if os.path.exists(BOSS_STATE_FILE):
            try:
                with open(BOSS_STATE_FILE, "r", encoding="utf-8") as f_boss:
                    current_boss_data.update(
                        json.load(f_boss)
                    )  # Update global variable
            except (json.JSONDecodeError, IOError) as e:
                print(
                    f"AVISO: Não foi possível carregar o {BOSS_STATE_FILE} (pode estar vazio/corrompido ou obsoleto): {e}"
                )
                current_boss_data.clear()  # Clear if corrupted/empty

        # If still empty after loading, initialize its default structure (e.g., for global stats)
        if not current_boss_data:
            current_boss_data["global_defeated_bosses_count"] = (
                0  # Example: Track how many bosses globally defeated
            )

    except (json.JSONDecodeError, IOError) as e:
        print(f"ERRO: Não foi possível carregar dados do jogador: {e}")
        player_database = {}

    return player_database


def save_data():
    """Saves player data and boss state to JSON files."""
    try:
        with open(PLAYER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(player_database, f, indent=4)
    except IOError as e:
        print(f"CRITICAL ERROR: Não foi possível salvar dados do jogador: {e}")

    # Save the global current_boss_data if it has any purpose
    try:
        with open(BOSS_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(current_boss_data, f, indent=4)
    except IOError as e:
        print(
            f"ERRO CRÍTICO: Não foi possível salvar dados do boss global (se ainda usado): {e}"
        )


def get_player_data(user_id: int | str) -> dict | None:
    """
    Retrieves player data from the database.
    Ensures 'boss_data' is initialized if not present (for new players).
    """
    user_id_str = str(user_id)
    if user_id_str not in player_database:
        return None

    # Ensure boss_data is initialized even for existing players who might not have it yet
    if "boss_data" not in player_database[user_id_str]:
        player_database[user_id_str]["boss_data"] = DEFAULT_PLAYER_BOSS_DATA.copy()
        # Ensure the first boss to unlock is set for newly initialized boss_data
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
        # Ensure defeated_bosses list exists
        if "defeated_bosses" not in player_database[user_id_str]["boss_data"]:
            player_database[user_id_str]["boss_data"]["defeated_bosses"] = []
        save_data()  # Save immediately after updating player data structure

    return player_database.get(user_id_str)


# Load data when this module is imported
player_database = load_data()
