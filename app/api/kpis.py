# app/api/kpis.py

from typing import Any, Dict, List, Set

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.kpi_service import KPIService

router = APIRouter()


# --- Modelos Pydantic ---

class KPI(BaseModel):
    project_id: str | None = None
    project_name: str | None = None
    kpi_id: str | None = None
    kpi_name: str | None = None
    methodology: str | None = None
    dimension: str | None = None
    value: float | None = None
    target: float | None = None
    unit: str | None = None
    status: str | None = None
    description: str | None = None
    last_update: str | None = None


class KPIsMeta(BaseModel):
    total_kpis: int
    total_projects: int
    generated_at: str
    source: str


class KPIsResponse(BaseModel):
    kpis: List[KPI]
    meta: KPIsMeta


class ProjectSummary(BaseModel):
    total_kpis: int
    by_status: dict


class ProjectKPIsResponse(BaseModel):
    project: dict
    kpis: List[KPI]
    summary: ProjectSummary
    meta: KPIsMeta


# --- Dependency ---

def get_kpi_service() -> KPIService:
    return KPIService()


# --- Endpoints ---

@router.get("/kpis_v2", response_model=KPIsResponse)
def get_kpis_v2(service: KPIService = Depends(get_kpi_service)):
    kpis_norm = service.get_all_normalized()
    project_ids: Set[str] = {k["project_id"] for k in kpis_norm if k.get("project_id")}
    meta = KPIsMeta(
        total_kpis=len(kpis_norm),
        total_projects=len(project_ids),
        generated_at="2026-04-11T09:30:00Z",
        source="infy-vision-backend",
    )
    return KPIsResponse(kpis=kpis_norm, meta=meta)


@router.get("/kpis_v2/{project_id}", response_model=ProjectKPIsResponse)
def get_kpis_by_project_v2(project_id: str, service: KPIService = Depends(get_kpi_service)):
    kpis_norm = service.get_all_normalized()
    kpis_project = [k for k in kpis_norm if k.get("project_id") == project_id]

    project_name = kpis_project[0].get("project_name") if kpis_project else None
    methodology = kpis_project[0].get("methodology") if kpis_project else None

    red = sum(1 for k in kpis_project if k.get("status") == "red")
    yellow = sum(1 for k in kpis_project if k.get("status") == "yellow")
    green = sum(1 for k in kpis_project if k.get("status") == "green")

    return ProjectKPIsResponse(
        project={"project_id": project_id, "project_name": project_name, "methodology": methodology},
        kpis=[KPI(**k) for k in kpis_project],
        summary=ProjectSummary(total_kpis=len(kpis_project), by_status={"red": red, "yellow": yellow, "green": green}),
        meta=KPIsMeta(total_kpis=len(kpis_project), total_projects=1, generated_at="2026-04-11T09:30:00Z", source="infy-vision-backend"),
    )


# --- Summary v2 ---

class GlobalStatus(BaseModel):
    total_projects: int
    total_kpis: int
    by_status: dict


class ProjectStatus(BaseModel):
    project_id: str
    project_name: str | None = None
    red: int
    yellow: int
    green: int
    total_kpis: int


class GlobalSummaryResponse(BaseModel):
    overall: GlobalStatus
    by_project: List[ProjectStatus]
    meta: dict


@router.get("/summary_v2", response_model=GlobalSummaryResponse)
def get_summary_v2(service: KPIService = Depends(get_kpi_service)):
    kpis_norm = service.get_all_normalized()

    red_g = sum(1 for k in kpis_norm if k.get("status") == "red")
    yellow_g = sum(1 for k in kpis_norm if k.get("status") == "yellow")
    green_g = sum(1 for k in kpis_norm if k.get("status") == "green")

    projects: Dict[str, Any] = {}
    for k in kpis_norm:
        pid = k.get("project_id")
        if not pid:
            continue
        if pid not in projects:
            projects[pid] = {"project_id": pid, "project_name": k.get("project_name"), "red": 0, "yellow": 0, "green": 0, "total_kpis": 0}
        projects[pid]["total_kpis"] += 1
        if k.get("status") in ("red", "yellow", "green"):
            projects[pid][k["status"]] += 1

    return GlobalSummaryResponse(
        overall=GlobalStatus(total_projects=len(projects), total_kpis=len(kpis_norm), by_status={"red": red_g, "yellow": yellow_g, "green": green_g}),
        by_project=[ProjectStatus(**p) for p in projects.values()],
        meta={"generated_at": "2026-04-11T09:30:00Z", "kpi_window": "last_snapshot"},
    )
