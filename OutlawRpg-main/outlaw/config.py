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
    "espada_rpg": "<:EspadasDuplas:1391079572006637618>",  # Substitua pelo ID real
    "moeda_ouro": "<:moeda_ouro:9876543210998765432>",  # Substitua pelo ID real
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
    "trophy_icon": "<a:win:1389688665688768592> ",
    "money_icon": "💰",
    "xp_icon": "<a:Special:1391079516788756600> ",
    # Emojis faltantes usados em profile_view.py
    "class_icon": "🎭",  # Placeholder
    "level_icon": "<:Stats:1391079676650328097>",  # Placeholder
    "location_icon": "📍",  # Placeholder
    "status_icon": "📊",  # Placeholder
    "attack_icon": "🗡️",  # Placeholder
    "special_attack_icon": "<a:Special:1391079516788756600> ",  # Placeholder
    "energy_icon": "⚡",  # Placeholder
    "attribute_points_icon": "💎",  # Placeholder
    "kills_icon": "<:Saber:1391079549302734960>",  # Placeholder
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
    "combat_header_icon": "<:EspadasDuplas:1391079572006637618> ",  # Para o título "Combate"
    "active_effects_header_icon": "✨",  # Para o título "Efeitos Ativos"
    "resources_header_icon": "⚙️",  # Para o título "Seus Recursos"
    "journey_header_icon": "<a:win:1389688665688768592> ",  # Para o título "Sua Jornada"
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
        "price": 5000000,
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

LOCATION_KILL_GOALS = {}


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
            "attack_multiplier": 1.80,
            "special_attack_multiplier": 2.00,
            "hp_multiplier": 1.05,
            "healing_multiplier": 1.0,
            "cooldown_reduction_percent": 0.0,
            "evasion_chance_bonus": 0.0,
        },
        "Rei da Noite": {
            "emoji": CUSTOM_EMOJIS.get("transform", "✨"),
            "cost_energy": TRANSFORM_COST + 2,
            "duration_seconds": 7 * 60,
            "attack_multiplier": 1.90,
            "special_attack_multiplier": 2.20,
            "evasion_chance_bonus": 0.05,
            "required_blessing": "bencao_dracula",
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


BOSSES_DATA = {}  # Conteúdo removido e vazio


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
        "required_previous_boss": None,  # ALTERADO: Era "colosso_de_pedra"
        "required_item": None,
        "required_level": None,
    },
    "Vale do Inferno": {
        "name": "Vale do Inferno",
        "type": "selvagem",
        "emoji": "🔥",
        "conecta": ["Abismo Sombrio", "Templo Esquecido"],
        "desc": "Um vale escaldante cheio de fogo e criaturas que sobrevivem ao calor infernal.",
        "required_previous_boss": None,  # ALTERADO: Era "devorador_abissal"
        "required_item": None,
        "required_level": None,
    },
    "Templo Esquecido": {
        "name": "Templo Esquecido",
        "type": "selvagem",
        "emoji": "🏯",
        "conecta": ["Vale do Inferno", "Portão das Sombras"],
        "desc": "Ruínas antigas de um templo perdido no tempo, protegido por entidades místicas.",
        "required_previous_boss": None,  # ALTERADO: Era "inferno_guardiao"
        "required_item": None,
        "required_level": None,
    },
    "Portão das Sombras": {
        "name": "Portão das Sombras",
        "type": "selvagem",
        "emoji": "🚪",
        "conecta": ["Templo Esquecido", "Brecha das Terras"],
        "desc": "Um portal sombrio que conecta os mundos, guardado por forças obscuras.",
        "required_previous_boss": None,  # ALTERADO: Era "tita_esquecido"
        "required_item": None,
        "required_level": None,
    },
    "Brecha das Terras": {
        "name": "Brecha das Terras",
        "type": "selvagem",
        "emoji": "🌌",
        "conecta": ["Portão das Sombras", "Paraíso"],
        "desc": "O ponto onde múltiplas realidades se encontram e o destino do mundo será decidido.",
        "required_previous_boss": None,  # ALTERADO: Era "arauto_das_sombras"
        "required_item": None,
        "required_level": None,
    },
    "Paraíso": {
        "name": "Paraíso",
        "type": "cidade",
        "emoji": "🌟",
        "conecta": ["Brecha das Terras"],
        "desc": "O santuário sagrado onde a paz e a luz reinam supremos, mas guardado por seres celestiais poderosos.",
        "required_previous_boss": None,  # ALTERADO: Era "anomalia_dimensional"
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
            "hp": 800,
            "attack": 76,
            "xp": 520,
            "money": 400,
            "thumb": "https://c.tenor.com/NLQ2AoVfEQUAAAAd/tenor.gif",
        },
        {
            "name": "Espectro Antigo",
            "hp": 180,
            "attack": 204,
            "xp": 160,
            "money": 320,
            "thumb": "https://c.tenor.com/tTXMqhKPCFwAAAAd/tenor.gif",
        },
        {
            "name": "Gárgula Vingativa",
            "hp": 440,
            "attack": 100,
            "xp": 130,
            "money": 330,
            "thumb": "https://c.tenor.com/Ub7Nd2q36RYAAAAd/tenor.gif",
        },
    ],
    "Abismo Sombrio": [
        {
            "name": "Aranha das Sombras",
            "hp": 720,
            "attack": 72,
            "xp": 140,
            "money": 1008,
            "thumb": "https://c.tenor.com/Q1UgRkPJzMAAAAAC/spider-shadow.gif",
        },
        {
            "name": "Serpente Abissal",
            "hp": 760,
            "attack": 88,
            "xp": 160,
            "money": 1216,
            "thumb": "https://c.tenor.com/n9Zyr_d-5O0AAAAC/sea-serpent.gif",
        },
    ],
    "Vale do Inferno": [
        {
            "name": "Demônio Flamejante",
            "hp": 800,
            "attack": 224,
            "xp": 400,
            "money": 320,
            "thumb": "https://c.tenor.com/vA1zDKkpFfIAAAAC/fire-demon.gif",
        },
        {
            "name": "Cão Infernal",
            "hp": 960,
            "attack": 240,
            "xp": 440,
            "money": 360,
            "thumb": "https://c.tenor.com/z8mELvPmsN8AAAAC/hellhound.gif",
        },
    ],
    "Templo Esquecido": [
        {
            "name": "Guardião Espectral",
            "hp": 2400,
            "attack": 560,
            "xp": 1120,
            "money": 960,
            "thumb": "https://c.tenor.com/Dq52zpNYdJ4AAAAC/ghost-guardian.gif",
        },
        {
            "name": "Mago Ancião",
            "hp": 2080,
            "attack": 640,
            "xp": 1200,
            "money": 1040,
            "thumb": "https://c.tenor.com/ysXUvq-wT5MAAAAAC/old-mage.gif",
        },
    ],
    "Portão das Sombras": [
        {
            "name": "Sombra Errante",
            "hp": 5120,
            "attack": 1440,
            "xp": 2560,
            "money": 2240,
            "thumb": "https://c.tenor.com/53EpyO-t1aIAAAAC/shadow-figure.gif",
        },
        {
            "name": "Guardião das Trevas",
            "hp": 5760,
            "attack": 1600,
            "xp": 2880,
            "money": 2400,
            "thumb": "https://c.tenor.com/EOhB81CS_2wAAAAC/dark-guardian.gif",
        },
    ],
    "Brecha das Terras": [
        {
            "name": "Caótico Dimensional",
            "hp": 19200,
            "attack": 5120,
            "xp": 9600,
            "money": 7680,
            "thumb": "https://c.tenor.com/GV31bRfFNy8AAAAC/dimensional-chaos.gif",
        },
        {
            "name": "Guardião da Brecha",
            "hp": 22400,
            "attack": 5760,
            "xp": 11520,
            "money": 9600,
            "thumb": "https://c.tenor.com/VuE-xM7RjTwAAAAC/gatekeeper.gif",
        },
    ],
    "Paraíso": [
        {
            "name": "Arcanjo Guardião",
            "hp": 64000,
            "attack": 15360,
            "xp": 38400,
            "money": 32000,
            "thumb": "https://c.tenor.com/89zGuwH3Ys8AAAAC/angelic.gif",
        },
        {
            "name": "Serafim de Luz",
            "hp": 70400,
            "attack": 16640,
            "xp": 44800,
            "money": 38400,
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
    30: 1389604420702048417,
    100: 1389604431317827604,
    350: 1389604749233487923,
}

NEW_CHARACTER_ROLE_ID = 1388628499182518352

DEFAULT_PLAYER_BOSS_DATA = {}  # Conteúdo removido e vazio

BOSS_PROGRESSION_ORDER = []  # Conteúdo removido e vazio


CLAN_REWARD_ANNOUNCEMENT_CHANNEL_ID = 1387231221616087141
BOSS_ANNOUNCEMENT_CHANNEL_ID = 0  # Alterado para 0
