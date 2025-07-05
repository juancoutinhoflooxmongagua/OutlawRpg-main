# config.py

# --- CONFIGURAÇÕES DE GAME DESIGN ---
XP_PER_LEVEL_BASE = 150
XP_PER_MESSAGE_COOLDOWN_SECONDS = 60
ATTRIBUTE_POINTS_PER_LEVEL = 2
CRITICAL_CHANCE = 0.10
CRITICAL_MULTIPLIER = 1.5
INITIAL_MONEY = 100
INITIAL_HP = 100
INITIAL_ATTACK = 10
INITIAL_SPECIAL_ATTACK = 20
REVIVE_COST = 55
BOUNTY_PERCENTAGE = 0.20
TRANSFORM_COST = 2
MAX_ENERGY = 10
STARTING_LOCATION = "Abrigo dos Foras-da-Lei"


# NEW: Clan System Configuration
CLAN_RANK_REWARDS = {  # XP and Money rewards for top 3 clans
    1: {"xp": 5000, "money": 2500},
    2: {"xp": 3000, "money": 1500},
    3: {"xp": 1000, "money": 500},
}
CLAN_CREATION_COST = 2000  # Cost to create a new clan
DEFAULT_CLAN_XP = 0  # Initial XP for a new clan
MAX_CLAN_MEMBERS = 10  # Maximum number of members allowed in a clan
CLAN_RANKING_INTERVAL_DAYS = 7  # How often the clan ranking happens
CLAN_KILL_CONTRIBUTION_PERCENTAGE_XP = (
    0.10  # 10% of player's earned XP from kills goes to clan
)
CLAN_KILL_CONTRIBUTION_PERCENTAGE_MONEY = (
    0.05  # 5% of player's earned Money from kills goes to clan
)

CUSTOM_EMOJIS = {
    "espada_rpg": "<:espada_rpg:123456789012345678>",  # Substitua pelo ID real
    "moeda_ouro": "<:moeda_ouro:987654321098765432>",  # Substitua pelo ID real
    "hp_icon": "<a:heartbeat_anim:1391079654638489660>",  # Substitua pelo ID real
    "transform": "<a:aura:1389688598139371631>",  # Exemplo de gif/emoji animado
    "machado_guerreiro": "<:machado_guerreiro:123123123123123123>",
    "escudo_defesa": "<:escudo_defesa:456456456456456456>",
    "xp_estrela": "<a:Special:1391079516788756600>",
    "olho_secreto": "<:olho_secreto:123456789012345678>",
    "ferramentas_dev": "<:ferramentas_dev:987654321098765432>",
    "clan_icon": "🛡️",
    "leader_icon": "👑",
    "member_icon": "👥",
    "trophy_icon": "🏆",
    "money_icon": "💰",
    "xp_icon": "✨",
    # Emojis faltantes usados em profile_view.py
    "class_icon": "🎭",  # Placeholder
    "level_icon": "<:Stats:1391079676650328097>",  # Placeholder
    "location_icon": "📍",  # Placeholder
    "status_icon": "📊",  # Placeholder
    "attack_icon": "🗡️",  # Placeholder
    "special_attack_icon": "✨",  # Placeholder
    "energy_icon": "⚡",  # Placeholder
    "attribute_points_icon": "💎",  # Placeholder
    "kills_icon": "⚔️",  # Placeholder
    "deaths_icon": "☠️",  # Placeholder
    "bounty_icon": "🏴‍☠️",  # Placeholder
    "xp_boost_icon": "🚀",  # Placeholder
    "money_boost_icon": "💸",  # Placeholder
    "empty_bag_icon": "🎒",  #
    "status_online_icon": "<a:online:1391079468155670588>",  # Pode ser um emoji customizado
    "status_dead_icon": "💀",  # Pode ser um emoji customizado
    "status_afk_icon": "🌙",  # Pode ser um emoji customizado
    # NOVOS: Emojis para os botões de navegação
    "button_profile_icon": "👤",  # Para o botão "Perfil"
    "button_inventory_icon": "🎒",  # Para o botão "Inventário"
    "button_resources_icon": "⚡",  # Para o botão "Recursos"
    "button_record_boosts_icon": "🏆",  # Para o botão "Registro & Boosts"
    # NOVOS: Emojis para os cabeçalhos de campo nos embeds (opcional)
    "combat_header_icon": "⚔️",  # Para o título "Combate"
    "active_effects_header_icon": "✨",  # Para o título "Efeitos Ativos"
    "resources_header_icon": "⚙️",  # Para o título "Seus Recursos"
    "journey_header_icon": "🏆",  # Para o título "Sua Jornada"
}


# NEW: Initial data structure for a new clan (added 'money' field)
INITIAL_CLAN_DATA = {
    "name": "",
    "leader_id": None,
    "members": [],  # List of member user IDs (strings)
    "xp": DEFAULT_CLAN_XP,
    "money": 0,  # NEW: Initial money for a new clan
    "creation_timestamp": 0,
    "last_ranking_timestamp": 0,  # To track when the last ranking rewards were given
}


# --- DADOS GLOBAIS DO JOGO ---
ITEMS_DATA = {
    "pocao": {
        "name": "Poção de Vida",
        "heal": 50,
        "price": 75,
        "emoji": "🧪",
        "consumable": True,
        "type": "healing",
        "description": "Restaura uma pequena quantidade de HP.",
    },
    "super_pocao": {
        "name": "Super Poção",
        "heal": 120,
        "price": 150,
        "emoji": "🍶",
        "consumable": True,
        "type": "healing",
        "description": "Restaura uma grande quantidade de HP.",
    },
    # REMOVIDO: "invocador" genérico
    "amuleto_de_pedra": {
        "name": "Amuleto de Pedra",
        "effect": "second_chance",
        "emoji": "🪨",
        "price": None,
        "consumable": False,
        "type": "unique_passive",
        "description": "Concede uma segunda chance em combate uma vez por batalha. Item permanente.",
    },
    "cajado_curandeiro": {
        "name": "Cajado do Curandeiro",
        "price": 5000,
        "class_restriction": "Curandeiro",
        "effect_multiplier": 1.20,
        "emoji": "⚕️",
        "consumable": False,
        "type": "equipable",
        "description": "Aumenta a eficácia de todas as suas curas em 20%.",
    },
    "manopla_lutador": {
        "name": "Manopla do Lutador",
        "price": 5000,
        "class_restriction": "Lutador",
        "attack_bonus_percent": 0.05,
        "hp_bonus_flat": 20,
        "emoji": "🥊",
        "consumable": False,
        "type": "equipable",
        "description": "Aumenta seu ataque base em 5% e HP máximo em 20.",
    },
    "mira_semi_automatica": {
        "name": "Mira Semi-Automática",
        "price": 5000,
        "class_restriction": "Atirador",
        "cooldown_reduction_percent": 0.40,
        "emoji": "🎯",
        "consumable": False,
        "type": "equipable",
        "description": "Reduz o tempo de recarga do seu ataque especial em 40%.",
    },
    "espada_fantasma": {
        "name": "Espada Fantasma",
        "price": 5000,
        "class_restriction": "Espadachim",
        "attack_bonus_percent": 0.10,
        "hp_penalty_percent": 0.20,
        "emoji": "🗡️",
        "consumable": False,
        "type": "equipable",
        "description": "Aumenta seu ataque em 10%, mas reduz seu HP máximo em 20%.",
    },
    "habilidade_inata": {
        "name": "Habilidade Inata (Passiva)",
        "xp_multiplier_passive": 0.10,
        "attack_bonus_passive_percent": 0.05,
        "type": "passive_style_bonus",  # Isso não é um item de inventário, é um bônus de estilo
        "emoji": "💡",
        "price": None,
        "consumable": False,
        "description": "Concede bônus passivos para ataque e XP com base no seu estilo de poder. Não é um item, e sim uma recompensa especial.",
    },
    "bencao_dracula": {
        "name": "Bênção de Drácula",
        "price": 10000,
        "class_restriction": "Vampiro",
        "cost_energy": 3,
        "duration_seconds": 5 * 60,
        "evasion_chance": 0.15,
        "hp_steal_percent_on_evade": 0.25,
        "emoji": "🦇",
        "consumable": False,
        "type": "blessing_unlock",
        "description": "Bênção temporária que concede chance de desviar de ataques e roubar HP.",
    },
    "bencao_rei_henrique": {
        "name": "Benção do Rei Henrique",
        "price": 10000,
        "style_restriction": "Aura",
        "cost_energy": 5,
        "duration_seconds": 10 * 60,
        "attack_multiplier": 1.15,
        "special_attack_multiplier": 1.15,
        "max_hp_multiplier": 1.15,
        "cooldown_reduction_percent": 0.07,
        "emoji": "✨",
        "consumable": False,
        "type": "blessing_unlock",
        "description": "Bênção temporária que aprimora muito seus atributos e reduz cooldowns.",
    },
    # NOVOS ITENS INVOCADORES DE BOSS (adicionados para permitir compra na loja)
    "invocador_colosso_de_pedra": {
        "name": "Invocador do Colosso de Pedra",
        "price": 1000,
        "emoji": "🔮",
        "consumable": True,
        "type": "summon_boss",
        "boss_id_to_summon": "colosso_de_pedra",
        "description": "Invoca o Colosso de Pedra para um desafio pessoal.",
    },
    "invocador_devorador_abissal": {
        "name": "Invocador do Devorador Abissal",
        "price": 2500,
        "emoji": "🔮",
        "consumable": True,
        "type": "summon_boss",
        "boss_id_to_summon": "devorador_abissal",
        "description": "Invoca o Devorador Abissal para um desafio personal.",
    },
    "invocador_inferno_guardiao": {
        "name": "Invocador do Inferno Guardião",
        "price": 6000,
        "emoji": "🔮",
        "consumable": True,
        "type": "summon_boss",
        "boss_id_to_summon": "inferno_guardiao",
        "description": "Invoca o Inferno Guardião para um desafio personal.",
    },
    "invocador_tita_esquecido": {
        "name": "Invocador do Titã Esquecido",
        "price": 15000,
        "emoji": "🔮",
        "consumable": True,
        "type": "summon_boss",
        "boss_id_to_summon": "tita_esquecido",
        "description": "Invoca o Titã Esquecido para um desafio personal.",
    },
    "invocador_arauto_das_sombras": {
        "name": "Invocador do Arauto das Sombras",
        "price": 40000,
        "emoji": "🔮",
        "consumable": True,
        "type": "summon_boss",
        "boss_id_to_summon": "arauto_das_sombras",
        "description": "Invoca o Arauto das Sombras para um desafio personal.",
    },
    "invocador_anomalia_dimensional": {
        "name": "Invocador da Anomalia Dimensional",
        "price": 100000,
        "emoji": "🔮",
        "consumable": True,
        "type": "summon_boss",
        "boss_id_to_summon": "anomalia_dimensional",
        "description": "Invoca a Anomalia Dimensional para um desafio personal.",
    },
    "invocador_sentinela_celestial": {
        "name": "Invocador da Sentinela Celestial",
        "price": 250000,
        "emoji": "🔮",
        "consumable": True,
        "type": "summon_boss",
        "boss_id_to_summon": "sentinela_celestial",
        "description": "Invoca a Sentinela Celestial para um desafio personal.",
    },
    "coleira_do_lobo": {
        "name": "Coleira do Lobo Alfa",
        "price": 7500,
        "class_restriction": "Domador",
        "attack_bonus_percent": 0.08,
        "hp_bonus_flat": 30,
        "emoji": "🦴",
        "consumable": False,
        "type": "equipable",
        "description": "Fortalece seu companheiro lobo, aumentando seu ataque em 8% e HP em 30.",
    },
    "armadura_de_osso": {
        "name": "Armadura de Osso Antigo",
        "price": 7500,
        "class_restriction": "Corpo Seco",
        "hp_bonus_flat": 50,
        "cooldown_reduction_percent": 0.10,
        "emoji": "🛡️",
        "consumable": False,
        "type": "equipable",
        "description": "Uma armadura densa que aumenta seu HP em 50 e reduz o cooldown de habilidades em 10%.",
    },
    "coracao_do_universo": {
        "name": "Coração do Universo",
        "price": 500000,
        "emoji": "💖",
        "consumable": False,
        "type": "unique_passive",
        "description": "Um fragmento da criação. Concede +15% de ataque, +15% de HP, +50% de XP e Dinheiro, e reduz todos os cooldowns em 20%.",
        "attack_multiplier": 1.15,
        "max_hp_multiplier": 1.15,
        "xp_multiplier_passive": 0.50,
        "money_multiplier_passive": 0.50,
        "cooldown_reduction_percent": 0.20,
    },
}

LOCATION_KILL_GOALS = {
    "Floresta Sussurrante": {
        "kills_required": 60,
        "invoker_id": "invocador_colosso_de_pedra",
    },
    "Ruínas do Templo": {
        "kills_required": 60,
        "invoker_id": "invocador_colosso_de_pedra",
    },
    "Abismo Sombrio": {
        "kills_required": 60,
        "invoker_id": "invocador_devorador_abissal",
    },
    "Vale do Inferno": {
        "kills_required": 60,
        "invoker_id": "invocador_inferno_guardiao",
    },
    "Templo Esquecido": {
        "kills_required": 60,
        "invoker_id": "invocador_tita_esquecido",
    },
    "Portão das Sombras": {
        "kills_required": 60,
        "invoker_id": "invocador_arauto_das_sombras",
    },
    "Brecha das Terras": {
        "kills_required": 60,
        "invoker_id": "invocador_anomalia_dimensional",
    },
    "Paraíso": {"kills_required": 60, "invoker_id": "invocador_sentinela_celestial"},
}


CLASS_TRANSFORMATIONS = {
    "Espadachim": {
        "Lâmina Fantasma": {
            "emoji": "👻",
            "cost_energy": TRANSFORM_COST,
            "duration_seconds": 5 * 60,
            "attack_multiplier": 1.20,
            "special_attack_multiplier": 1.10,
            "hp_multiplier": 0.90,
            "healing_multiplier": 1.0,
            "cooldown_reduction_percent": 0.0,
            "evasion_chance_bonus": 0.0,
        },
        "Lâmina Abençoada": {
            "emoji": "🌟👻",
            "cost_energy": TRANSFORM_COST + 2,
            "duration_seconds": 7 * 60,
            "attack_multiplier": 1.30,
            "special_attack_multiplier": 1.20,
            "hp_multiplier": 0.95,
            "healing_multiplier": 1.05,
            "cooldown_reduction_percent": 0.05,
            "evasion_chance_bonus": 0.0,
            "required_blessing": "bencao_rei_henrique",
        },
    },
    "Lutador": {
        "Punho de Aço": {
            "emoji": "💪",
            "cost_energy": TRANSFORM_COST,
            "duration_seconds": 5 * 60,
            "attack_multiplier": 1.15,
            "hp_multiplier": 1.15,
            "healing_multiplier": 1.0,
            "cooldown_reduction_percent": 0.0,
            "evasion_chance_bonus": 0.0,
        },
        "Punho de Adamantium": {
            "emoji": "💎💪",
            "cost_energy": TRANSFORM_COST + 2,
            "duration_seconds": 7 * 60,
            "attack_multiplier": 1.25,
            "hp_multiplier": 1.25,
            "healing_multiplier": 1.05,
            "cooldown_reduction_percent": 0.05,
            "evasion_chance_bonus": 0.0,
            "required_blessing": "bencao_rei_henrique",
        },
    },
    "Atirador": {
        "Olho de Águia": {
            "emoji": "🦅",
            "cost_energy": TRANSFORM_COST,
            "duration_seconds": 5 * 60,
            "attack_multiplier": 1.05,
            "special_attack_multiplier": 1.25,
            "cooldown_reduction_percent": 0.20,
            "healing_multiplier": 1.0,
            "hp_multiplier": 1.0,
            "evasion_chance_bonus": 0.0,
        },
        "Visão Cósmica": {
            "emoji": "👁️‍🗨️🦅",
            "cost_energy": TRANSFORM_COST + 2,
            "duration_seconds": 7 * 60,
            "attack_multiplier": 1.10,
            "special_attack_multiplier": 1.35,
            "cooldown_reduction_percent": 0.30,
            "healing_multiplier": 1.0,
            "hp_multiplier": 1.0,
            "evasion_chance_bonus": 0.0,
            "required_blessing": "bencao_rei_henrique",
        },
    },
    "Curandeiro": {
        "Bênção Vital": {
            "emoji": "😇",
            "cost_energy": TRANSFORM_COST,
            "duration_seconds": 5 * 60,
            "healing_multiplier": 1.25,
            "hp_multiplier": 1.10,
            "attack_multiplier": 1.0,
            "special_attack_multiplier": 1.0,
            "cooldown_reduction_percent": 0.0,
            "evasion_chance_bonus": 0.0,
        },
        "Toque Divino": {
            "emoji": "✨😇",
            "cost_energy": TRANSFORM_COST + 2,
            "duration_seconds": 7 * 60,
            "attack_multiplier": 1.0,
            "special_attack_multiplier": 1.05,
            "hp_multiplier": 1.20,
            "healing_multiplier": 1.35,
            "cooldown_reduction_percent": 0.05,
            "evasion_chance_bonus": 0.0,
            "required_blessing": "bencao_rei_henrique",
        },
    },
    "Vampiro": {
        "Lorde Sanguinário": {
            "emoji": "🧛",
            "cost_energy": TRANSFORM_COST,
            "duration_seconds": 5 * 60,
            "attack_multiplier": 1.80,  # Revertido para original
            "special_attack_multiplier": 2.00,  # Revertido para original
            "hp_multiplier": 1.05,
            "healing_multiplier": 1.0,
            "cooldown_reduction_percent": 0.0,
            "evasion_chance_bonus": 0.0,
        },
        "Rei da Noite": {
            "emoji": CUSTOM_EMOJIS.get("transform", "✨"),
            "cost_energy": TRANSFORM_COST + 2,
            "duration_seconds": 7 * 60,
            "attack_multiplier": 1.90,  # Revertido para original
            "special_attack_multiplier": 2.20,  # Revertido para original
            "evasion_chance_bonus": 0.05,
            "required_blessing": "bencao_dracula",
        },
    },
    "Corpo Seco": {
        "Fúria Imortal": {
            "emoji": "💀",
            "cost_energy": 1,
            "duration_seconds": 1 * 60,
            "attack_multiplier": 2.5,
            "special_attack_multiplier": 2.5,
            "hp_multiplier": 0.7,
            "healing_multiplier": 1.0,
            "cooldown_reduction_percent": 0.0,
            "evasion_chance_bonus": 0.0,
            "note": "A mecânica exata de 'transformar 50% da vida em ataque' requer lógica adicional na função calculate_effective_stats em utils.py ou no comando 'transformar' em world_commands.py, para manipular dinamicamente o HP e o Ataque. Atualmente, o hp_multiplier reduz o HP, e o attack_multiplier fornece um grande bônus de ataque.",
        },
    },
    "Domador": {
        "Lobo Descontrolado": {
            "emoji": "🐺",
            "cost_energy": TRANSFORM_COST,
            "duration_seconds": 4 * 60,
            "attack_multiplier": 1.25,
            "special_attack_multiplier": 1.25,
            "hp_multiplier": 1.0,
            "healing_multiplier": 1.0,
            "cooldown_reduction_percent": 0.0,
            "evasion_chance_bonus": 0.0,
        },
    },
}


BOSSES_DATA = {
    "Colosso de Pedra": {
        "id": "colosso_de_pedra",
        "name": "Colosso de Pedra",
        "max_hp": 5000,
        "attack": 150,
        "xp_reward": 1000,
        "money_reward": 5000,
        "drops": {"amuleto_de_pedra": 1, "pocao": 10},
        "spawn_locations": [
            "Floresta Sussurrante",
            "Ruínas do Templo",
        ],
        "thumbnail": "https://c.tenor.com/NLQ2AoVfEQUAAAAd/tenor.gif",
        "next_boss_unlock": "Devorador Abissal",
        "required_level": 1,
        "price_invoker": 1000,
    },
    "Devorador Abissal": {
        "id": "devorador_abissal",
        "name": "Devorador Abissal",
        "max_hp": 12500,
        "attack": 375,
        "xp_reward": 2500,
        "money_reward": 12500,
        "drops": {
            "super_pocao": 2,
            "invocador_colosso_de_pedra": 1,
        },
        "spawn_locations": ["Abismo Sombrio"],
        "thumbnail": "https://c.tenor.com/f2S9_G2tEwAAAAAd/abyssal-devourer.gif",
        "next_boss_unlock": "Inferno Guardião",
        "required_level": 5,
        "price_invoker": 2500,
    },
    "Inferno Guardião": {
        "id": "inferno_guardiao",
        "name": "Inferno Guardião",
        "max_hp": 31250,
        "attack": 937,
        "xp_reward": 6250,
        "money_reward": 31250,
        "drops": {
            "cajado_curandeiro": 1,
            "manopla_lutador": 1,
            "invocador_devorador_abissal": 1,
        },
        "spawn_locations": ["Vale do Inferno"],
        "thumbnail": "https://c.tenor.com/7b9011A43IAAAAd/inferno-guardian.gif",
        "next_boss_unlock": "Titã Esquecido",
        "required_level": 10,
        "price_invoker": 6000,
    },
    "Titã Esquecido": {
        "id": "tita_esquecido",
        "name": "Titã Esquecido",
        "max_hp": 78125,
        "attack": 2342,
        "xp_reward": 15625,
        "money_reward": 78125,
        "drops": {
            "mira_semi_automatica": 1,
            "espada_fantasma": 1,
            "invocador_inferno_guardiao": 1,
        },
        "spawn_locations": ["Templo Esquecido"],
        "thumbnail": "https://c.tenor.com/A6j5QjE2vVAAAAAd/forgotten-titan.gif",
        "next_boss_unlock": "Arauto das Sombras",
        "required_level": 15,
        "price_invoker": 15000,
    },
    "Arauto das Sombras": {
        "id": "arauto_das_sombras",
        "name": "Arauto das Sombras",
        "max_hp": 195312,
        "attack": 5855,
        "xp_reward": 39062,
        "money_reward": 195312,
        "drops": {
            "bencao_dracula": 1,
            "bencao_rei_henrique": 1,
            "invocador_tita_esquecido": 1,
        },
        "spawn_locations": ["Portão das Sombras"],
        "thumbnail": "https://c.tenor.com/y8m0v_eF2AAAAAd/shadow-herald.gif",
        "next_boss_unlock": "Anomalia Dimensional",
        "required_level": 20,
        "price_invoker": 40000,
    },
    "Anomalia Dimensional": {
        "id": "anomalia_dimensional",
        "name": "Anomalia Dimensional",
        "max_hp": 488280,
        "attack": 14638,
        "xp_reward": 97656,
        "money_reward": 488280,
        "drops": {
            "invocador_arauto_das_sombras": 1,
            "amuleto_de_pedra": 1,
            "habilidade_inata": 1,
        },
        "spawn_locations": ["Brecha das Terras"],
        "thumbnail": "https://c.tenor.com/gK9x2C34z4kAAAAd/dimensional-anomaly.gif",
        "next_boss_unlock": "Sentinela Celestial",
        "required_level": 30,
        "price_invoker": 100000,
    },
    "Sentinela Celestial": {
        "id": "sentinela_celestial",
        "name": "Sentinela Celestial",
        "max_hp": 1220700,
        "attack": 36595,
        "xp_reward": 244140,
        "money_reward": 1220700,
        "drops": {
            "invocador_anomalia_dimensional": 1,
            "amuleto_de_pedra": 1,
            "habilidade_inata": 2,
            "bencao_rei_henrique": 1,
        },
        "spawn_locations": ["Paraíso"],
        "thumbnail": "https://c.tenor.com/f3k2b_9m0AAAAAd/celestial-sentinel.gif",
        "next_boss_unlock": None,
        "required_level": 50,
        "price_invoker": 250000,
    },
}

WORLD_MAP = {
    "Abrigo dos Foras-da-Lei": {
        "name": "Abrigo dos Foras-da-Lei",
        "type": "cidade",
        "emoji": "⛺",
        "conecta": ["Floresta Sussurrante"],
        "desc": "Um acampamento improvisado que serve de refúgio para os renegados.",
        "required_previous_boss": None,
        "required_item": None,
        "required_level": None,
    },
    "Floresta Sussurrante": {
        "name": "Floresta Sussurrante",
        "type": "selvagem",
        "emoji": "🌳",
        "conecta": ["Abrigo dos Foras-da-Lei", "Ruínas do Templo"],
        "desc": "Uma mata densa e perigosa, onde criaturas espreitam nas sombras.",
        "required_previous_boss": None,
        "required_item": None,
        "required_level": None,
    },
    "Ruínas do Templo": {
        "name": "Ruínas do Templo",
        "type": "selvagem",
        "emoji": "🏛️",
        "conecta": ["Floresta Sussurrante", "Abismo Sombrio"],
        "desc": "Os restos de um antigo local de poder, agora habitado por guardiões de pedra.",
        "required_previous_boss": None,
        "required_item": None,
        "required_level": None,
    },
    "Abismo Sombrio": {
        "name": "Abismo Sombrio",
        "type": "selvagem",
        "emoji": "🕳️",
        "conecta": ["Ruínas do Templo", "Vale do Inferno"],
        "desc": "Um abismo sem fim, onde as sombras se tornam presas fáceis para predadores famintos.",
        "required_previous_boss": "colosso_de_pedra",  # CORRIGIDO: minúscula
        "required_item": None,
        "required_level": None,
    },
    "Vale do Inferno": {
        "name": "Vale do Inferno",
        "type": "selvagem",
        "emoji": "🔥",
        "conecta": ["Abismo Sombrio", "Templo Esquecido"],
        "desc": "Um vale escaldante cheio de fogo e criaturas que sobrevivem ao calor infernal.",
        "required_previous_boss": "devorador_abissal",  # CORRIGIDO: minúscula
        "required_item": None,
        "required_level": None,
    },
    "Templo Esquecido": {
        "name": "Templo Esquecido",
        "type": "selvagem",
        "emoji": "🏯",
        "conecta": ["Vale do Inferno", "Portão das Sombras"],
        "desc": "Ruínas antigas de um templo perdido no tempo, protegido por entidades místicas.",
        "required_previous_boss": "inferno_guardiao",  # CORRIGIDO: minúscula
        "required_item": None,
        "required_level": None,
    },
    "Portão das Sombras": {
        "name": "Portão das Sombras",
        "type": "selvagem",
        "emoji": "🚪",
        "conecta": ["Templo Esquecido", "Brecha das Terras"],
        "desc": "Um portal sombrio que conecta os mundos, guardado por forças obscuras.",
        "required_previous_boss": "tita_esquecido",  # CORRIGIDO: minúscula
        "required_item": None,
        "required_level": None,
    },
    "Brecha das Terras": {
        "name": "Brecha das Terras",
        "type": "selvagem",
        "emoji": "🌌",
        "conecta": ["Portão das Sombras", "Paraíso"],
        "desc": "O ponto onde múltiplas realidades se encontram e o destino do mundo será decidido.",
        "required_previous_boss": "arauto_das_sombras",  # CORRIGIDO: minúscula
        "required_item": None,
        "required_level": None,
    },
    "Paraíso": {
        "name": "Paraíso",
        "type": "cidade",
        "emoji": "🌟",
        "conecta": ["Brecha das Terras"],
        "desc": "O santuário sagrado onde a paz e a luz reinam supremos, mas guardado por seres celestiais poderosos.",
        "required_previous_boss": "anomalia_dimensional",  # CORRIGIDO: minúscula
        "required_item": None,
        "required_level": None,
    },
}

ENEMIES = {
    "Floresta Sussurrante": [
        {
            "name": "Lobo Faminto",
            "hp": 60,
            "attack": 12,
            "xp": 25,
            "money": 15,
            "thumb": "https://c.tenor.com/v5Ik3wkrjlwAAAAC/tenor.gif",
        },
        {
            "name": "Aranha Gigante",
            "hp": 50,
            "attack": 15,
            "xp": 30,
            "money": 20,
            "thumb": "https://c.tenor.com/cBKUDbUVHSAAAAAC/tenor.gif",
        },
        {
            "name": "Dragão de Komodo",
            "hp": 70,
            "attack": 10,
            "xp": 28,
            "money": 18,
            "thumb": "https://c.tenor.com/gIzmfcS1-rcAAAAC/tenor.gif",
        },
    ],
    "Ruínas do Templo": [
        {
            "name": "Guardião de Pedra",
            "hp": 800,  # 400 * 2
            "attack": 76,  # 38 * 2
            "xp": 520,  # 260 * 2
            "money": 400,  # 200 * 2
            "thumb": "https://c.tenor.com/NLQ2AoVfEQUAAAAd/tenor.gif",
        },
        {
            "name": "Espectro Antigo",
            "hp": 180,  # 90 * 2
            "attack": 204,  # 102 * 2
            "xp": 160,  # 80 * 2
            "money": 320,  # 160 * 2
            "thumb": "https://c.tenor.com/tTXMqhKPCFwAAAAd/tenor.gif",
        },
        {
            "name": "Gárgula Vingativa",
            "hp": 440,  # 220 * 2
            "attack": 100,  # 50 * 2
            "xp": 130,  # 65 * 2
            "money": 330,  # 165 * 2
            "thumb": "https://c.tenor.com/Ub7Nd2q36RYAAAAd/tenor.gif",
        },
    ],
    "Abismo Sombrio": [
        {
            "name": "Aranha das Sombras",
            "hp": 720,  # 180 * 4
            "attack": 72,  # 18 * 4
            "xp": 140,  # 35 * 4
            "money": 1008,  # 252 * 4
            "thumb": "https://c.tenor.com/Q1UgRkPJzMAAAAAC/spider-shadow.gif",
        },
        {
            "name": "Serpente Abissal",
            "hp": 760,  # 190 * 4
            "attack": 88,  # 22 * 4
            "xp": 160,  # 40 * 4
            "money": 1216,  # 304 * 4
            "thumb": "https://c.tenor.com/n9Zyr_d-5O0AAAAC/sea-serpent.gif",
        },
    ],
    "Vale do Inferno": [
        {
            "name": "Demônio Flamejante",
            "hp": 800,  # 100 * 8
            "attack": 224,  # 28 * 8
            "xp": 400,  # 50 * 8
            "money": 320,  # 40 * 8
            "thumb": "https://c.tenor.com/vA1zDKkpFfIAAAAC/fire-demon.gif",
        },
        {
            "name": "Cão Infernal",
            "hp": 960,  # 120 * 8
            "attack": 240,  # 30 * 8
            "xp": 440,  # 55 * 8
            "money": 360,  # 45 * 8
            "thumb": "https://c.tenor.com/z8mELvPmsN8AAAAC/hellhound.gif",
        },
    ],
    "Templo Esquecido": [
        {
            "name": "Guardião Espectral",
            "hp": 2400,  # 150 * 16
            "attack": 560,  # 35 * 16
            "xp": 1120,  # 70 * 16
            "money": 960,  # 60 * 16
            "thumb": "https://c.tenor.com/Dq52zpNYdJ4AAAAC/ghost-guardian.gif",
        },
        {
            "name": "Mago Ancião",
            "hp": 2080,  # 130 * 16
            "attack": 640,  # 40 * 16
            "xp": 1200,  # 75 * 16
            "money": 1040,  # 65 * 16
            "thumb": "https://c.tenor.com/ysXUvq-wT5MAAAAAC/old-mage.gif",
        },
    ],
    "Portão das Sombras": [
        {
            "name": "Sombra Errante",
            "hp": 5120,  # 160 * 32
            "attack": 1440,  # 45 * 32
            "xp": 2560,  # 80 * 32
            "money": 2240,  # 70 * 32
            "thumb": "https://c.tenor.com/53EpyO-t1aIAAAAC/shadow-figure.gif",
        },
        {
            "name": "Guardião das Trevas",
            "hp": 5760,  # 180 * 32
            "attack": 1600,  # 50 * 32
            "xp": 2880,  # 90 * 32
            "money": 2400,  # 75 * 32
            "thumb": "https://c.tenor.com/EOhB81CS_2wAAAAC/dark-guardian.gif",
        },
    ],
    "Brecha das Terras": [
        {
            "name": "Caótico Dimensional",
            "hp": 19200,  # 300 * 64
            "attack": 5120,  # 80 * 64
            "xp": 9600,  # 150 * 64
            "money": 7680,  # 120 * 64
            "thumb": "https://c.tenor.com/GV31bRfFNy8AAAAC/dimensional-chaos.gif",
        },
        {
            "name": "Guardião da Brecha",
            "hp": 22400,  # 350 * 64
            "attack": 5760,  # 90 * 64
            "xp": 11520,  # 180 * 64
            "money": 9600,  # 150 * 64
            "thumb": "https://c.tenor.com/VuE-xM7RjTwAAAAC/gatekeeper.gif",
        },
    ],
    "Paraíso": [
        {
            "name": "Arcanjo Guardião",
            "hp": 64000,  # 500 * 128
            "attack": 15360,  # 120 * 128
            "xp": 38400,  # 300 * 128
            "money": 32000,  # 250 * 128
            "thumb": "https://c.tenor.com/89zGuwH3Ys8AAAAC/angelic.gif",
        },
        {
            "name": "Serafim de Luz",
            "hp": 70400,  # 550 * 128
            "attack": 16640,  # 130 * 128
            "xp": 44800,  # 350 * 128
            "money": 38400,  # 300 * 128
            "thumb": "https://c.tenor.com/I7CKPqu5XJMAAAAAC/seraphim.gif",
        },
    ],
}

""" 
PROFILE_IMAGES = {
    # Imagens das Classes Base
    "Espadachim": "https://i.imgur.com/RC3rJNc.png",
    "Lutador": "https://media.discordapp.net/attachments/1388860166648369184/1389495865567084605/Picsart_25-07-01_03-17-21-028.png?ex=6864d45d&is=686382dd&hm=73f2f3896118d1901ec30b0c8b7ef6739d400e6f06294d98891698e4f16622b6&=&format=webp&quality=lossless&width=608&height=608",
    "Atirador": "https://media.tenor.com/hYzJPjRmvWAAAAAM/clown.gif",
    "Curandeiro": "https://i.ibb.co/3Y1sqWcP/image.png",
    "Vampiro": "https://i.imgur.com/X0E6qQL.png",
    "Domador": "https://i.imgur.com/example_tamer.png",
    "Corpo Seco": "https://imgs.search.brave.com/0-7XXiyDokmhrgN9p6TBkHv_Ah2SxtWlTCsHsNasvjU/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9zdGF0/aWMud2l4c3RhdGlj/LmNvbS9tZWRpYS8z/NzFhMTNfMzI2Njkx/MGRiNGU0NDA4Mzlk/YWIwZmNkZTg4ZTM3/ZWF-bXYyLmpwZy92/MS9jcm9wL3hfMCx5/XzMwNSx3XzE5MjAs/aF8xMjIzL2ZpbGwv/d182MDAsaF8yOTAs/YWxfYyxxXzgwLHVz/Z21fMC42Nl8xLjAw/MC4wMSxlbmNfYXZp/Zi9jb3Jwby1zZWNv/LmpwZw",
    # Imagens das Transformações
    "Lâmina Fantasma": "https://i.imgur.com/CnDR7eP.png",
    "Punho de Aço": "https://i.imgur.com/mDsfNyi.png",
    "Olho de Águia": "https://media.tenor.com/hYzJPjRmvWAAAAAM/clown.gifI",
    "Bênção Vital": "https://i.ibb.co/5xScwp3Y/image.png",
    "Lorde Sanguinário": "https://i.imgur.com/eTaWLjx.png",
    "Benção do Rei Henrique": "https://media.tenor.com/hYzJPjRmvWAAAAAM/clown.gifI",
    "Lâmina Abençoada": "https://example.com/blade_blessed.png",
    "Punho de Adamantium": "https://example.com/adamantium_fist.png",
    "Visão Cósmica": "https://example.com/cosmic_sight.png",
    "Toque Divino": "https://i.ibb.co/VcK0Mzyr/image.png",
    "Rei da Noite": "https://example.com/night_king.png",
}

"""
LEVEL_ROLES = {
    2: 1389604381069938738,
    5: 1389604398103269376,
    10: 1389604405078134894,
    20: 1389604420702048417,
    35: 1389604431317827604,
    50: 1389604749233487923,
}

NEW_CHARACTER_ROLE_ID = 1388628499182518352

DEFAULT_PLAYER_BOSS_DATA = {
    "current_boss_id": None,
    "current_boss_hp": 0,
    "last_spawn_channel_id": None,
    "boss_progression_level": "colosso_de_pedra",  # CORRIGIDO: minúscula
    "defeated_bosses": [],
    "last_spawn_timestamp": 0,
}

CLAN_REWARD_ANNOUNCEMENT_CHANNEL_ID = 1387231221616087141
BOSS_ANNOUNCEMENT_CHANNEL_ID = 987654321098765432
