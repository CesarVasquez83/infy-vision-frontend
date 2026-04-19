# Estandariza la forma en que encuentra el término.

import unicodedata


def normalize_key(key: str) -> str:
    if not isinstance(key, str):
        return key

    key = key.lower()

    key = ''.join(
        c for c in unicodedata.normalize('NFD', key)
        if unicodedata.category(c) != 'Mn'
    )

    key = key.strip().replace(" ", "_")

    mapping = {
        "experiencia": "experience",
        "experience": "experience",
        "acceso": "access",
        "access": "access",
        "buy_in": "buy_in",
        "buy-in": "buy_in",
        "aceptacion": "buy_in",
        "acceptance": "buy_in",
        "confianza": "trust",
        "trust": "trust",
        "decision": "decision",
        "decisiones": "decision",
        "decision_making": "decision",
        "entrega": "delivery",
        "delivery": "delivery",
        "criticidad": "criticality",
        "criticality": "criticality",
        "cambios": "changes",
        "changes": "changes",
        "tamano_del_equipo": "team_size",
        "tamaño_del_equipo": "team_size",
        "team_size": "team_size"
    }

    return mapping.get(key, key)


def normalize_indexes_dict(data: dict) -> dict:
    normalized = {}

    for k, v in data.items():
        nk = normalize_key(k)
        normalized[nk] = v

    return normalized