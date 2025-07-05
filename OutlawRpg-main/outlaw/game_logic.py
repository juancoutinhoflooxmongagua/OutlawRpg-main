# File: OutlawRpg-main/outlaw/game_logic/relic_mechanics.py
# Crie esta nova pasta 'game_logic' dentro de 'outlaw' e este arquivo 'relic_mechanics.py'.

import random

# Importa a lista de relíquias do seu novo arquivo de dados
from ..game_data.relics_data import relics


def get_random_relic():
    """
    Sorteia uma relíquia com base nas chances de obtenção definidas na lista 'relics'.
    Garante um sorteio preciso mesmo com porcentagens muito pequenas.
    """
    if not relics:
        return None  # Retorna None se a lista de relíquias estiver vazia

    # Criar uma lista de pesos onde cada peso é a 'chance_obter_percentual'
    weights = [relic["chance_obter_percentual"] for relic in relics]

    # random.choices fará o sorteio com base nesses pesos.
    # Ele pode lidar com floats pequenos, mas se você encontrar problemas de precisão
    # para números *extremamente* pequenos ou uma quantidade *muito grande* de itens,
    # uma alternativa é escalar os pesos para inteiros grandes:
    # Por exemplo:
    # max_decimal_places = 8 # A maior quantidade de casas decimais em suas chances (0.00000001 tem 8)
    # scale_factor = 10**max_decimal_places
    # scaled_weights = [int(w * scale_factor) for w in weights]
    # chosen_relic = random.choices(relics, weights=scaled_weights, k=1)[0]

    # Para o seu conjunto atual de dados, usar os floats diretamente deve funcionar bem:
    chosen_relic = random.choices(relics, weights=weights, k=1)[0]
    return chosen_relic
