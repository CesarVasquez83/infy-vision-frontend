# app/services/kpi_service.py

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


STATUS_MAP: Dict[str, str] = {
    "Rojo": "red",
    "Amarillo": "yellow",
    "Verde": "green",
}

UNIT_MAP: Dict[str, str] = {
    "%": "percent",
    "USD": "currency",
    "USD  ": "currency",
    "n°": "count",
    "ratio": "ratio",
    # agrega aquí lo que veas en tu CSV
}


DEFAULT_CSV = Path(__file__).parent.parent / "data" / "alpha_kpis.csv"

class KPIService:
    def __init__(self, csv_path: Path = DEFAULT_CSV):
        self.csv_path = Path(csv_path)
        self.df = pd.read_csv(self.csv_path)

    # --- V1: datos crudos, lo que ya usas hoy ---

    def get_all_raw(self) -> List[Dict[str, Any]]:
        return self.df.to_dict(orient="records")

    # --- V2: datos normalizados para contrato limpio ---

    def _normalize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        raw_unit = row.get("UNIDAD")
        raw_status = row.get("ESTADO")

        unit_norm = None
        if isinstance(raw_unit, str):
            unit_norm = UNIT_MAP.get(raw_unit.strip(), raw_unit.strip())

        status_norm = None
        if isinstance(raw_status, str):
            status_norm = STATUS_MAP.get(raw_status.strip(), raw_status.strip()).lower()

        return {
            "project_id": row.get("PROYECTO"),
            "project_name": row.get("PROYECTO"),  # si no tienes nombre distinto
            "kpi_id": row.get("KPI"),
            "kpi_name": row.get("DENOMINACIÓN DE KPI"),
            "methodology": row.get("MARCO"),
            "dimension": row.get("DIMENSION"),
            "value": row.get("VALOR"),
            # por ahora usamos UMBRAL_VERDE como target; si luego decides otra lógica, se cambia aquí
            "target": row.get("UMBRAL_VERDE"),
            "unit": unit_norm,
            "status": status_norm,
            "description": row.get("QUE MIDE"),
            # de momento sin fuente real de fecha; se puede rellenar más adelante
            "last_update": None,
        }

    def get_all_normalized(self) -> List[Dict[str, Any]]:
        records = self.df.to_dict(orient="records")
        return [self._normalize_row(r) for r in records]