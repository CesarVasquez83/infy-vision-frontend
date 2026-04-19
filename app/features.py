#app/features.py
#KPI maps organizados por proyecto.
#Lite = KPIs intrínsecos del proyecto (KPI_DATA.xlsx) + contexto mínimo
#Elite = Lite + dimensiones completas de contexto organizacional (KPI_DATA2.xlsx)

from pathlib import Path
from typing import Optional
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"

#── Carga única al importar el módulo ─────────────────────────────────────────
_fact = pd.read_excel(DATA_DIR / "KPI_DATA.xlsx")
_fact.rename(columns={"PROYECTO": "Project", "MARCO": "Framework", "KPI": "KPI", "VALOR": "Value", "ESTADO": "Status"}, inplace=True)

_dim = pd.read_excel(DATA_DIR / "KPI_DATA2.xlsx", sheet_name="Sheet1")
_dim.rename(columns={"Proyecto": "Project", "Marco": "Framework", "Buy-in": "Buy_In", "Lectura rapida": "Quick_Reading"}, inplace=True)

#── Type helpers ───────────────────────────────────────────────────────────────
def _as_float(val, default: Optional[float] = None) -> Optional[float]:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _as_int(val, default: Optional[int] = None) -> Optional[int]:
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


#── Helper genérico ────────────────────────────────────────────────────────────
def _get_kpis(project_id: str, kpi_map: dict) -> dict:
    subset = (
        _fact[_fact["Project"] == project_id]
        .groupby("KPI")["Value"]
        .last()
    )
    return {
        feat: _as_float(subset.get(code))
        for feat, code in kpi_map.items()
    }


#── Suitability Classifier — PMBOK® Agile Practice Guide, Annex X3 ────────────
#
#  Escala visual del tablero: 1–10
#    Centro (1) = sweet spot Ágil
#    Borde  (10) = sweet spot Predictivo
#
#  Dirección por índice (como aparecen en el tablero):
#    ALTO = Predictivo : experience, access, buy_in, team_size, criticality, delivery
#    BAJO = Predictivo : trust, decision, changes
#      → estos tres se invierten para normalizar: score_pred = 11 - valor
#
#  Clasificación final:
#    suitability_score promedio ponderado (escala pred unificada)
#    1.0 – 4.0  → Agile
#    4.1 – 7.0  → Hybrid
#    7.1 – 10.0 → Predictive
#
#  Mismatch: diferencia ≥ 2 zonas entre framework declarado y score calculado.
# ─────────────────────────────────────────────────────────────────────────────

_AGILE_FRAMEWORKS = {
    "Scrum", "Kanban", "XP", "Lean", "FDD", "DSDM", "Crystal", "LeSS", "AUP"
}

_HYBRID_FRAMEWORKS = {
    "SAFe", "Disciplined Agile", "DA",
    "Agile+Waterfall", "Scrum+PMBOK",
    "Kanban+Predictivo", "Kanban+Predictive",
    "PRINCE2 Agile", "V+Agile", "Stage-Gate+Agile",
}

_PREDICTIVE_FRAMEWORKS = {
    "Predictivo", "Waterfall", "PMBOK"
}

# Pesos igualitarios por defecto (Annex X3 no especifica ponderación).
# Ajustables si el PM quiere dar más peso a criticality, changes, etc.
_WEIGHTS: dict[str, float] = {
    "experience":  1.0,
    "access":      1.0,
    "buy_in":      1.0,
    "team_size":   1.0,
    "criticality": 1.0,
    "delivery":    1.0,
    "trust":       1.0,
    "decision":    1.0,
    "changes":     1.0,
}


def _to_pred_scale(
    experience: float, access: float, buy_in: float,
    team_size: float, criticality: float, delivery: float,
    trust: float, decision: float, changes: float,
) -> dict[str, float]:
    """
    Normaliza todos los índices a escala 'predictivo':
    alto = más predictivo, bajo = más ágil.
    trust, decision y changes se invierten (11 - valor) porque en la
    escala original su dirección es la opuesta.
    """
    return {
        "experience":  experience,
        "access":      access,
        "buy_in":      buy_in,
        "team_size":   team_size,
        "criticality": criticality,
        "delivery":    delivery,
        "trust":       trust,
        "decision":    decision,
        "changes":     changes,
    }


def _suitability_score(normalized: dict[str, float]) -> float:
    """Promedio ponderado → score en escala 1–10."""
    total_w  = sum(_WEIGHTS[k] for k in normalized)
    weighted = sum(normalized[k] * _WEIGHTS[k] for k in normalized)
    return round(weighted / total_w, 2)


def _zone_from_score(score: float) -> str:
    if score <= 4.0:
        return "Agile"
    elif score <= 7.0:
        return "Hybrid"
    else:
        return "Predictive"


def _zone_from_framework(framework: str) -> str:
    f = (framework or "").strip()
    if f in _AGILE_FRAMEWORKS:
        return "Agile"
    elif f in _HYBRID_FRAMEWORKS:
        return "Hybrid"
    elif f in _PREDICTIVE_FRAMEWORKS:
        return "Predictive"
    return "Hybrid"  # desconocido → híbrido por defecto


_ZONE_ORDER = {"Agile": 0, "Hybrid": 1, "Predictive": 2}


def _classify_approach(
    framework: str,
    experience: float,
    access: float,
    delivery: float,
    criticality: float,
    changes: float,
    buy_in: float,
    trust: float,
    decision: float,
    team_size: float = 5.0,
    governance: float | None = None,
) -> dict:
    """
    Clasifica el enfoque de gestión según PMBOK® Annex X3.

    Retorna:
        approach_infy        : zona recomendada por el score (Agile/Hybrid/Predictive)
        suitability_score    : promedio ponderado normalizado (1.0–10.0)
        framework_zone       : zona del framework declarado
        suitability_mismatch : True si diferencia ≥ 2 zonas
        suitability_more_pred: True si el score empuja más hacia Predictivo que el fw
        suitability_less_pred: True si el score empuja más hacia Ágil que el fw
        suitability_note     : diagnóstico legible
        normalized_indexes   : índices ya en escala pred (útil para debug/trazabilidad)
    """

    # 1 — Normalizar
    normalized = _to_pred_scale(
        experience=experience, access=access, buy_in=buy_in,
        team_size=team_size, criticality=criticality, delivery=delivery,
        trust=trust, decision=decision, changes=changes,
    )

    # 2 — Score y zona calculada
    score      = _suitability_score(normalized)
    score_zone = _zone_from_score(score)
    fw_zone    = _zone_from_framework(framework)

    # 3 — Flags de dirección
    score_order = _ZONE_ORDER[score_zone]
    fw_order    = _ZONE_ORDER[fw_zone]
    delta       = score_order - fw_order   # + = más pred que fw; - = más ágil que fw

    more_pred = delta > 0
    less_pred = delta < 0
    mismatch  = abs(delta) >= 2

    # 4 — Nota diagnóstica
    if mismatch:
        note = (
            f"⚠️ mismatch fuerte: framework '{framework}' ({fw_zone}) "
            f"vs. contexto real ({score_zone}, score={score})"
        )
    elif more_pred:
        note = (
            f"contexto exige endurecer enfoque hacia {score_zone} "
            f"(score={score} | fw actual: {fw_zone})"
        )
    elif less_pred:
        note = (
            f"contexto permite flexibilizar hacia {score_zone} "
            f"(score={score} | fw actual: {fw_zone})"
        )
    else:
        note = f"marco y contexto alineados — {fw_zone} (score={score})"

    return {
        "approach_infy":         score_zone,
        "suitability_score":     score,
        "framework_zone":        fw_zone,
        "suitability_more_pred": more_pred,
        "suitability_less_pred": less_pred,
        "suitability_mismatch":  mismatch,
        "suitability_note":      note,
        "normalized_indexes":    normalized,
    }


#── KPI maps por proyecto (Lite) ───────────────────────────────────────────────
PROJECT_KPI_MAPS = {

    "Alpha": {  # Predictivo
        "sv": "SV", "spi": "SPI", "cv": "CV", "cpi": "CPI",
        "bac": "BAC", "pv": "PV", "ev": "EV", "ac": "AC",
        "scope_del": "SCOPE_DEL", "cr_rate": "CR_RATE",
        "formal_del": "FORMAL_DEL", "unplanned_risk": "UNPLANNED_RISK",
        "rework_pct": "REWORK_PCT",
    },

    "Beta": {  # Scrum
        "velocity": "VELOCITY", "us_dev": "US_DEV", "sprint_count": "SPRINT_COUNT",
        "tech_debt_pct": "TECH_DEBT_PCT", "cfd_wip": "CFD_WIP",
        "risk_burndown": "RISK_BURNDOWN", "burn_rate": "BURN_RATE",
        "backlog_var": "BACKLOG_VAR", "sprint_del_pct": "SPRINT_DEL_PCT",
        "non_feat_pct": "NON_FEAT_PCT", "sp_commit_del": "SP_COMMIT_DEL",
    },

    "Chi": {  # V-Model + Agile
        "spi": "SPI", "test_coverage": "TEST_COVERAGE",
        "verif_valid_pct": "VERIF_VALID_PCT", "defect_pct": "DEFECT_PCT",
        "rework_pct": "REWORK_PCT", "agile_iter_pct": "AGILE_ITER_PCT",
        "ci_time": "CI_TIME", "risk_res_pct": "RISK_RES_PCT",
        "vmodel_agile_bal": "VMODEL_AGILE_BAL", "stakeh_sat": "STAKEH_SAT",
    },

    "Delta": {  # Kanban
        "lead_time": "LEAD_TIME", "cycle_time": "CYCLE_TIME",
        "throughput": "THROUGHPUT", "wip_col": "WIP_COL", "ageing": "AGEING",
        "cos_expedite": "COS_EXPEDITE", "cos_fixed_date": "COS_FIXED_DATE",
        "cos_standard": "COS_STANDARD", "cos_intangible": "COS_INTANGIBLE",
    },

    "Epsilon": {  # DSDM
        "musthave_pct": "MUSTHAVE_PCT", "nicetohave_def": "NICETOHAVE_DEF",
        "biz_sat": "BIZ_SAT", "user_involv": "USER_INVOLV",
        "meeting_delay": "MEETING_DELAY", "backlog_reprio": "BACKLOG_REPRIO",
        "budget_comply": "BUDGET_COMPLY", "unvalidated_req": "UNVALIDATED_REQ",
        "change_resp": "CHANGE_RESP", "ux_quality": "UX_QUALITY",
    },

    "Gamma": {  # Lean
        "lead_time": "LEAD_TIME", "cycle_time": "CYCLE_TIME",
        "throughput": "THROUGHPUT", "wip_avg": "WIP_AVG",
        "defect_rate": "DEFECT_RATE", "value_time_pct": "VALUE_TIME_PCT",
        "util_rate": "UTIL_RATE", "blocked_items": "BLOCKED_ITEMS",
        "csat_lean": "CSAT_LEAN", "rework_pct": "REWORK_PCT",
    },

    "Iota": {  # Agile + Waterfall
        "spi": "SPI", "cpi": "CPI", "phase_milestone": "PHASE_MILESTONE",
        "scope_freeze_pct": "SCOPE_FREEZE_PCT", "sprint_del_pct": "SPRINT_DEL_PCT",
        "gate_approval": "GATE_APPROVAL", "rework_pct": "REWORK_PCT",
        "risk_res_pct": "RISK_RES_PCT", "hybrid_balance": "HYBRID_BALANCE",
        "stakeh_sat": "STAKEH_SAT",
    },

    "Kappa": {  # FDD
        "feat_comp_pct": "FEAT_COMP_PCT", "feat_count": "FEAT_COUNT",
        "tech_debt_pct": "TECH_DEBT_PCT", "lead_time": "LEAD_TIME",
        "backlog_var": "BACKLOG_VAR", "sp_days_feat": "SP_DAYS_FEAT",
        "non_feat_pct": "NON_FEAT_PCT", "cfd_feat": "CFD_FEAT",
        "defect_pct": "DEFECT_PCT", "stakeh_sat": "STAKEH_SAT",
    },

    "Lambda": {  # AUP
        "risk_res_pct": "RISK_RES_PCT", "arch_stable_pct": "ARCH_STABLE_PCT",
        "backlog_refined": "BACKLOG_REFINED", "integr_iter_pct": "INTEGR_ITER_PCT",
        "phase_lead_time": "PHASE_LEAD_TIME", "test_exec_pct": "TEST_EXEC_PCT",
        "stakeh_sat": "STAKEH_SAT", "tech_debt_pct": "TECH_DEBT_PCT",
        "ambig_reqs": "AMBIG_REQS", "scope_var_pct": "SCOPE_VAR_PCT",
    },

    "Omega": {  # SAFe
        "pi_obj_pct": "PI_OBJ_PCT", "dep_resolved": "DEP_RESOLVED",
        "integr_pi_pct": "INTEGR_PI_PCT", "biz_sat_pi": "BIZ_SAT_PI",
        "backlog_reprio": "BACKLOG_REPRIO", "feat_vs_fire_pct": "FEAT_VS_FIRE_PCT",
        "lead_time_c2c": "LEAD_TIME_C2C", "innov_items": "INNOV_ITEMS",
        "lean_agile_mat": "LEAN_AGILE_MAT", "csi_pi": "CSI_PI",
    },

    "Omikron": {  # Crystal Orange
        "osmotic_comm": "OSMOTIC_COMM", "safe_env": "SAFE_ENV",
        "focus_disruption": "FOCUS_DISRUPTION", "user_access": "USER_ACCESS",
        "tech_debt_pct": "TECH_DEBT_PCT", "rework_pct": "REWORK_PCT",
        "integr_wkshop": "INTEGR_WKSHOP", "stakeh_sat": "STAKEH_SAT",
        "reflect_action": "REFLECT_ACTION", "release_freq": "RELEASE_FREQ",
    },

    "Phi": {  # PRINCE2 Agile
        "spi": "SPI", "cpi": "CPI", "stage_boundary": "STAGE_BOUNDARY",
        "formal_del": "FORMAL_DEL", "sprint_del_pct": "SPRINT_DEL_PCT",
        "velocity": "VELOCITY", "rework_pct": "REWORK_PCT",
        "risk_res_pct": "RISK_RES_PCT", "prince2_agile_bal": "PRINCE2_AGILE_BAL",
        "stakeh_sat": "STAKEH_SAT",
    },

    "Pi": {  # Scrum + PMBOK
        "spi": "SPI", "cpi": "CPI", "gate_approval": "GATE_APPROVAL",
        "velocity": "VELOCITY", "sprint_del_pct": "SPRINT_DEL_PCT",
        "formal_del": "FORMAL_DEL", "scope_change_pct": "SCOPE_CHANGE_PCT",
        "rework_pct": "REWORK_PCT", "pmo_agile_align": "PMO_AGILE_ALIGN",
        "stakeh_sat": "STAKEH_SAT",
    },

    "Psi": {  # Stage-Gate + Agile
        "cpi": "CPI", "gate_approval": "GATE_APPROVAL", "roi_gate": "ROI_GATE",
        "sprint_del_pct": "SPRINT_DEL_PCT", "velocity": "VELOCITY",
        "time_to_gate": "TIME_TO_GATE", "rework_pct": "REWORK_PCT",
        "risk_res_pct": "RISK_RES_PCT", "gate_agile_align": "GATE_AGILE_ALIGN",
        "stakeh_sat": "STAKEH_SAT",
    },

    "Rho": {  # Kanban + Predictivo
        "spi": "SPI", "cpi": "CPI", "lead_time": "LEAD_TIME",
        "throughput": "THROUGHPUT", "wip_col": "WIP_COL", "ageing": "AGEING",
        "scope_freeze_pct": "SCOPE_FREEZE_PCT", "rework_pct": "REWORK_PCT",
        "plan_flow_align": "PLAN_FLOW_ALIGN", "stakeh_sat": "STAKEH_SAT",
    },

    "Sigma": {  # LeSS
        "integr_sprint_pct": "INTEGR_SPRINT_PCT", "dep_resolved_pct": "DEP_RESOLVED_PCT",
        "multi_team_items": "MULTI_TEAM_ITEMS", "lead_time_xteam": "LEAD_TIME_XTEAM",
        "clear_reqs_pct": "CLEAR_REQS_PCT", "po_sat": "PO_SAT",
        "integr_incidents": "INTEGR_INCIDENTS", "refactor_coord_pct": "REFACTOR_COORD_PCT",
        "terminology_coh": "TERMINOLOGY_COH", "priority_conflict": "PRIORITY_CONFLICT",
    },

    "Tau": {  # XP
        "velocity": "VELOCITY", "test_coverage": "TEST_COVERAGE", "ci_time": "CI_TIME",
        "defect_pct": "DEFECT_PCT", "tech_debt_red": "TECH_DEBT_RED",
        "feat_comp_pct": "FEAT_COMP_PCT", "lead_time": "LEAD_TIME",
        "backlog_var": "BACKLOG_VAR", "non_feat_pct": "NON_FEAT_PCT",
        "stakeh_sat": "STAKEH_SAT",
    },

    "Upsilon": {  # Disciplined Agile
        "lifecycle_fit": "LIFECYCLE_FIT", "gci_adopt_pct": "GCI_ADOPT_PCT",
        "goal_driven_pct": "GOAL_DRIVEN_PCT", "value_stream_eff": "VALUE_STREAM_EFF",
        "context_adapt": "CONTEXT_ADAPT", "tech_debt_pct": "TECH_DEBT_PCT",
        "enterprise_align": "ENTERPRISE_ALIGN", "stakeh_sat": "STAKEH_SAT",
        "retro_action_pct": "RETRO_ACTION_PCT", "risk_res_pct": "RISK_RES_PCT",
    },
}


#── Builders ───────────────────────────────────────────────────────────────────
def build_lite_features(project_id: str) -> dict:
    """Servicio LITE: KPIs intrínsecos del proyecto + contexto mínimo."""

    if project_id not in PROJECT_KPI_MAPS:
        raise ValueError(
            f"Proyecto '{project_id}' no encontrado. "
            f"Disponibles: {list(PROJECT_KPI_MAPS)}"
        )

    dim_row = _dim[_dim["Project"] == project_id].iloc[0]

    return {
        "project":     project_id,
        "framework":   dim_row["Framework"],
        "criticality": _as_float(dim_row["Criticality"]),
        "team_size":   _as_int(dim_row["Team_Size"]),
        "governance":  _as_int(dim_row["Governance"]),
        **_get_kpis(project_id, PROJECT_KPI_MAPS[project_id]),
    }


def build_elite_features(project_id: str) -> dict:
    """Servicio ELITE: Lite + perfil organizacional completo + clasificación PMBOK Annex X3."""

    base    = build_lite_features(project_id)
    dim_row = _dim[_dim["Project"] == project_id].iloc[0]

    exp  = _as_float(dim_row["Experience"])
    acc  = _as_float(dim_row["Access"])
    delv = _as_float(dim_row["Delivery"])
    chg  = _as_float(dim_row["Changes"])
    bi   = _as_float(dim_row["Buy_In"])
    tr   = _as_float(dim_row["Trust"])
    dec  = _as_float(dim_row["Decision"])
    ts   = _as_float(dim_row.get("Team_Size")) or float(base.get("team_size") or 5)

    base.update({
        "experience":        exp,
        "access":            acc,
        "delivery":          delv,
        "changes":           chg,
        "buy_in":            bi,
        "trust":             tr,
        "decision":          dec,
        "headcount":         _as_int(dim_row["Personal"]),
        "suitability_model": dim_row["Suitability_Model"],
        "quick_reading":     dim_row["Quick_Reading"],
    })

    base.update(_classify_approach(
        framework   = base["framework"],
        experience  = exp  or 5.0,
        access      = acc  or 5.0,
        delivery    = delv or 5.0,
        criticality = base["criticality"] or 5.0,
        changes     = chg  or 5.0,
        buy_in      = bi   or 5.0,
        trust       = tr   or 5.0,
        decision    = dec  or 5.0,
        team_size   = ts,
        governance  = base["governance"],
    ))

    return base


def get_all_projects() -> list:
    return sorted(PROJECT_KPI_MAPS.keys())


def get_framework(project_id: str) -> str:
    return _dim[_dim["Project"] == project_id].iloc[0]["Framework"]


#── Smoke test — ejecutar con: python -m app.features ─────────────────────────
if __name__ == "__main__":
    import json

    print("Proyecto     Framework                  Score  Zona          Mismatch")
    print("-" * 72)

    for pid in get_all_projects():
        elite  = build_elite_features(pid)
        score  = elite.get("suitability_score", "?")
        zone   = elite.get("approach_infy", "?")
        fw_z   = elite.get("framework_zone", "?")
        flag   = "⚠️  MISMATCH" if elite.get("suitability_mismatch") else ""
        print(f"{pid:12} {elite['framework']:26} {str(score):6} {zone:14} {flag}")

    print()
    for pid in get_all_projects():
        print(f"\n=== ELITE {pid} ===")
        print(json.dumps(build_elite_features(pid), indent=2, default=str))
