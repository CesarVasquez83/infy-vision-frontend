import os
import enum
import logging
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

logger = logging.getLogger(__name__)

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


# ── Lazy init — el engine se crea solo cuando se necesita ─────────────────────
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None and ENABLE_DB and DATABASE_URL:
        try:
            _engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,       # verifica conexión antes de usar
                connect_args={"sslmode": "require"} if "supabase" in (DATABASE_URL or "") else {},
            )
            logger.info("DB engine creado correctamente.")
        except Exception as e:
            logger.error(f"Error creando DB engine: {e}")
            _engine = None
    return _engine


def get_session_local():
    global _SessionLocal
    engine = get_engine()
    if _SessionLocal is None and engine is not None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def init_db():
    if not ENABLE_DB:
        return
    engine = get_engine()
    if engine is None:
        logger.warning("init_db: engine no disponible, se omite creación de tablas.")
        return
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas/verificadas correctamente.")
    except Exception as e:
        logger.error(f"Error en init_db: {e}")


def get_db_optional():
    if not ENABLE_DB:
        yield None
        return
    SessionLocal = get_session_local()
    if SessionLocal is None:
        logger.warning("get_db_optional: SessionLocal no disponible.")
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
