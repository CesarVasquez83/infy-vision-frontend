from typing import Dict

# Por defecto, trabajamos con escala 1–9
MAX_SCALE = 9
MIN_SCALE = 1

# Campos donde SÍ quieres invertir el valor para la lógica interna INFY
INVERTED_FIELDS = {
    "experience",   # ej: experiencia baja = riesgo alto
    "access",       # acceso difícil = riesgo alto
    "trust",        # confianza baja = riesgo alto
    "decision",     # decisión lenta = riesgo alto
    "buy_in",       # baja aceptación = riesgo alto
    # agrega/quita según tu criterio
}

def flip_value(value: int, max_scale: int = MAX_SCALE, min_scale: int = MIN_SCALE) -> int:
    """
    Aplica escala inversa. Ej: 2 -> 8 si escala 1–9.
    """
    if value is None:
        return None
    return max_scale + min_scale - value


def normalize_human_indexes(raw_indexes: Dict[str, int]) -> Dict[str, int]:
    """
    Devuelve los índices tal cual los ve el humano (sin flips).
    Esto es lo que se expone en STANDARD y en la parte descriptiva de ELITE.
    """
    # Aquí podrías clipear a rango [1,9], validar, etc.
    normalized: Dict[str, int] = {}
    for key, value in raw_indexes.items():
        if value is None:
            continue
        v = int(value)
        if v < MIN_SCALE:
            v = MIN_SCALE
        if v > MAX_SCALE:
            v = MAX_SCALE
        normalized[key] = v
    return normalized


def build_infy_suitability_indexes(raw_indexes: Dict[str, int]) -> Dict[str, int]:
    """
    Construye los índices para la LÓGICA INTERNA INFY (ELITE).
    - Para algunos campos (INVERTED_FIELDS) aplica flip.
    - Para el resto, usa el valor directo normalizado.
    """
    human = normalize_human_indexes(raw_indexes)
    infy: Dict[str, int] = {}

    for key, value in human.items():
        if key in INVERTED_FIELDS:
            infy[key] = flip_value(value)
        else:
            infy[key] = value

    return infy 