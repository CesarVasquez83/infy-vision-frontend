import json
import re
import logging

logger = logging.getLogger(__name__)

NUMBER_REGEX = re.compile(r"-?\d+(\.\d+)?")

VALID_INDEXES = {
    "experience",
    "access",
    "buy_in",
    "trust",
    "decision",
    "delivery",
    "criticality",
    "changes",
    "team_size"
}


# =============================================================================
# JSON
# =============================================================================
def parse_json_safe(message_content: str | None) -> dict:
    if not message_content:
        raise ValueError("LLM devolvió vacío")

    cleaned = re.sub(r"```[a-zA-Z]*", "", message_content).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido del LLM: {e}\nRAW: {message_content}")


# =============================================================================
# NUMÉRICOS
# =============================================================================
def safe_number(val, default=None):
    """
    Extrae número desde input sucio.
    """
    if val is None:
        return default

    if isinstance(val, (int, float)):
        return float(val)

    if isinstance(val, str):
        texto = val.replace(",", ".").lower()

        match = NUMBER_REGEX.search(texto)
        if not match:
            return default

        try:
            return float(match.group(0))
        except:
            return default

    return default


def clamp(val, min_val=0, max_val=10):
    if val is None:
        return None
    return max(min_val, min(max_val, val))


# =============================================================================
# VALIDACIÓN FINAL
# =============================================================================
def validate_indexes(data: dict) -> dict:
    """
    Limpia + valida suitability indexes.
    """
    cleaned = {}

    for k, v in data.items():

        if k not in VALID_INDEXES:
            continue

        num = safe_number(v, default=None)
        num = clamp(num, 0, 10)

        cleaned[k] = num

    return cleaned