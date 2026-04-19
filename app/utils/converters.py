INDEX_CONFIG = {
    "experience": "inverse",
    "access": "inverse",
    "buy_in": "inverse",
    "trust": "inverse",
    "decision": "inverse",
    "delivery": "inverse",
    "changes": "inverse",
    "criticality": "direct",
    "team_size": "direct"
}


def clamp(value, min_val=0, max_val=10):
    return max(min_val, min(max_val, value))


def convert_index(value, index_name):
    """
    Convierte un valor RAW (radar) a escala INFY.
    """

    if value is None:
        return None

    value = clamp(value, 0, 10)

    mode = INDEX_CONFIG.get(index_name)

    if mode == "inverse":
        return 10 - value

    elif mode == "direct":
        return value

    else:
        return None


def convert_all_indexes(indexes: dict) -> dict:
    """
    Convierte todo el dict de índices a INFY.
    """

    converted = {}

    for k, v in indexes.items():
        converted[k] = convert_index(v, k)

    return converted