import os
import enum
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ENABLE_DB = os.getenv("ENABLE_DB", "false").lower() == "true"

Base = declarative_base()

# Enum de tipos de evento de visión
class VisionEventType(str, enum.Enum):
    OK = "OK"
    INVALID_DASHBOARD = "INVALID_DASHBOARD"
    OPENAI_ERROR = "OPENAI_ERROR"
    JSON_DECODE_ERROR = "JSON_DECODE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AnalisisDashboard(Base):
    __tablename__ = "analisis_dashboard"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    analisis_pm = Column(JSONB, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    # relación con logs (opcional, pero útil)
    logs = relationship("VisionRequestsLog", back_populates="analisis")


class VisionRequestsLog(Base):
    __tablename__ = "vision_requests_log"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String, nullable=False)
    filename = Column(String, nullable=True)
    event_type = Column(Enum(VisionEventType), nullable=False)
    input_description = Column(Text, nullable=True)
    input_metadata = Column(JSONB, nullable=True)
    classifier_reason = Column(Text, nullable=True)
    analisis_pm = Column(JSONB, nullable=True)
    error_detail = Column(Text, nullable=True)
    analisis_id = Column(Integer, ForeignKey("analisis_dashboard.id"), nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    analisis = relationship("AnalisisDashboard", back_populates="logs")


# Solo se crea el engine si DB está habilitada
engine = create_engine(DATABASE_URL) if ENABLE_DB else None
SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine) if ENABLE_DB else None
)


def init_db():
    if not ENABLE_DB:
        return
    Base.metadata.create_all(bind=engine)


def get_db_optional():
    if not ENABLE_DB:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()