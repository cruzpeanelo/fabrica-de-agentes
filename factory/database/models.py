"""
Modelos SQLAlchemy para a Fabrica de Agentes v4.0
Arquitetura Worker-based (Single Claude + Tools per Worker)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

# Import Base
try:
    from .connection import Base
except ImportError:
    from connection import Base


# =============================================================================
# ENUMS
# =============================================================================

class ProjectStatus(str, Enum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class JobStatus(str, Enum):
    """Status do Job"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStep(str, Enum):
    """Passos do Autonomous Loop"""
    QUEUED = "queued"
    PARSING = "parsing"
    GENERATING = "generating"
    LINTING = "linting"
    TYPE_CHECKING = "type_checking"
    TESTING = "testing"
    SECURITY_SCAN = "security_scan"
    COMMITTING = "committing"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkerStatus(str, Enum):
    """Status do Worker"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


# =============================================================================
# PROJECT - Projetos construidos pela fabrica
# =============================================================================

class Project(Base):
    """Modelo para Projetos - cada aplicacao construida pela fabrica"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Tipo e template
    project_type = Column(String(50), nullable=False)
    template_used = Column(String(100), nullable=True)

    # Status e progresso
    status = Column(String(50), default=ProjectStatus.PLANNING.value)
    progress = Column(Float, default=0.0)

    # Diretorio do projeto
    folder_path = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)

    # Configuracoes do projeto
    config = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)
    tags = Column(JSON, default=list)

    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), default="system")

    # Relacionamentos
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "project_type": self.project_type,
            "template_used": self.template_used,
            "status": self.status,
            "progress": self.progress,
            "folder_path": self.folder_path,
            "github_url": self.github_url,
            "config": self.config or {},
            "settings": self.settings or {},
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "jobs_count": len(self.jobs) if self.jobs else 0
        }

    def __repr__(self):
        return f"<Project {self.project_id}: {self.name} [{self.status}]>"


# =============================================================================
# JOB - Jobs Assincronos (Unidade de trabalho principal)
# =============================================================================

class Job(Base):
    """
    Modelo para Jobs - Unidade de trabalho principal
    Processado por workers usando Claude Agent SDK
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(50), unique=True, nullable=False, index=True)

    # Relacionamento com projeto (opcional)
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=True, index=True)
    project = relationship("Project", back_populates="jobs")

    # Input do usuario
    description = Column(Text, nullable=False)
    tech_stack = Column(String(200), nullable=True)
    features = Column(JSON, default=list)

    # Status e progresso
    status = Column(String(20), default=JobStatus.PENDING.value, index=True)
    current_step = Column(String(30), default=JobStep.QUEUED.value)
    progress = Column(Float, default=0.0)

    # Controle do loop autonomo
    current_attempt = Column(Integer, default=0)
    max_attempts = Column(Integer, default=5)
    total_iterations = Column(Integer, default=0)

    # Worker que esta processando
    worker_id = Column(String(50), nullable=True, index=True)

    # Resultado
    result = Column(JSON, default=dict)
    output_path = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    artifacts = Column(JSON, default=list)

    # Erros e logs
    error_message = Column(Text, nullable=True)
    step_logs = Column(JSON, default=list)

    # Session (para Redis cache)
    session_data = Column(JSON, default=dict)

    # Timestamps
    queued_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Criado por
    created_by = Column(String(100), nullable=True)

    # Relacionamentos
    failures = relationship("FailureHistory", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "description": self.description,
            "tech_stack": self.tech_stack,
            "features": self.features or [],
            "status": self.status,
            "current_step": self.current_step,
            "progress": self.progress,
            "current_attempt": self.current_attempt,
            "max_attempts": self.max_attempts,
            "total_iterations": self.total_iterations,
            "worker_id": self.worker_id,
            "result": self.result or {},
            "output_path": self.output_path,
            "github_url": self.github_url,
            "artifacts": self.artifacts or [],
            "error_message": self.error_message,
            "step_logs": self.step_logs or [],
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by
        }

    def __repr__(self):
        return f"<Job {self.job_id}: {self.status} [{self.current_step}]>"


# =============================================================================
# WORKER - Workers do Pool (Claude Agent SDK instances)
# =============================================================================

class Worker(Base):
    """
    Modelo para Workers - Instancias do Claude Agent SDK
    Cada worker processa jobs da fila Redis
    """
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(String(50), unique=True, nullable=False, index=True)

    # Status
    status = Column(String(20), default=WorkerStatus.IDLE.value, index=True)
    current_job_id = Column(String(50), nullable=True)

    # Configuracao
    model = Column(String(50), default="claude-sonnet-4-20250514")
    mcp_tools = Column(JSON, default=list)

    # Metricas
    jobs_completed = Column(Integer, default=0)
    jobs_failed = Column(Integer, default=0)
    total_processing_time = Column(Integer, default=0)
    avg_job_duration = Column(Float, default=0.0)

    # Heartbeat
    last_heartbeat = Column(DateTime, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)

    # Metadados
    hostname = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)

    def to_dict(self):
        return {
            "worker_id": self.worker_id,
            "status": self.status,
            "current_job_id": self.current_job_id,
            "model": self.model,
            "mcp_tools": self.mcp_tools or [],
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "total_processing_time": self.total_processing_time,
            "avg_job_duration": self.avg_job_duration,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "hostname": self.hostname,
            "ip_address": self.ip_address
        }

    def __repr__(self):
        return f"<Worker {self.worker_id}: {self.status}>"


# =============================================================================
# FAILURE_HISTORY - Historico de Falhas
# =============================================================================

class FailureHistory(Base):
    """
    Modelo para Historico de Falhas
    Previne retry loops infinitos e permite analise de erros
    """
    __tablename__ = "failure_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Relacionamentos
    job_id = Column(String(50), ForeignKey("jobs.job_id"), nullable=False, index=True)
    job = relationship("Job", back_populates="failures")
    project_id = Column(String(50), nullable=True, index=True)

    # Detalhes da falha
    step = Column(String(30), nullable=False)
    attempt = Column(Integer, nullable=False)
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)

    # Contexto da falha
    input_data = Column(JSON, default=dict)
    step_output = Column(JSON, default=dict)

    # Resolucao
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "project_id": self.project_id,
            "step": self.step,
            "attempt": self.attempt,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "input_data": self.input_data or {},
            "step_output": self.step_output or {},
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<FailureHistory {self.job_id}:{self.step} attempt={self.attempt}>"


# =============================================================================
# USER - Usuarios do Sistema
# =============================================================================

class User(Base):
    """Modelo para Usuarios do Sistema"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default="VIEWER")
    active = Column(Boolean, default=True, nullable=False)

    # Quotas
    quotas = Column(JSON, default=lambda: {
        "max_jobs_per_day": 10,
        "max_concurrent_jobs": 2,
        "max_projects": 20,
        "api_tier": "free"
    })

    # Billing
    billing = Column(JSON, default=lambda: {
        "plan": "free",
        "tokens_used": 0,
        "tokens_limit": 100000,
        "cost_accumulated": 0.0,
        "budget_limit": 50.0
    })

    # Rate Limiting
    rate_limit_tokens = Column(Integer, default=0)
    rate_limit_reset = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "active": self.active,
            "quotas": self.quotas or {},
            "billing": self.billing or {},
            "rate_limit_tokens": self.rate_limit_tokens,
            "rate_limit_reset": self.rate_limit_reset.isoformat() if self.rate_limit_reset else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

    def check_quota(self, quota_name: str) -> bool:
        """Verifica se usuario tem quota disponivel"""
        if not self.quotas:
            return True
        return self.quotas.get(quota_name, 0) > 0

    def __repr__(self):
        return f"<User {self.username} [{self.role}]>"


# =============================================================================
# ACTIVITY_LOG - Logs de Atividades
# =============================================================================

class ActivityLog(Base):
    """Modelo para Logs de Atividades"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Origem
    source = Column(String(50), nullable=False, index=True)
    source_id = Column(String(50), nullable=True)

    # Contexto
    project_id = Column(String(50), nullable=True, index=True)
    job_id = Column(String(50), nullable=True, index=True)
    worker_id = Column(String(50), nullable=True, index=True)

    # Tipo e nivel
    level = Column(String(20), default="INFO", index=True)
    event_type = Column(String(50), nullable=False, index=True)

    # Dados
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source,
            "source_id": self.source_id,
            "project_id": self.project_id,
            "job_id": self.job_id,
            "worker_id": self.worker_id,
            "level": self.level,
            "event_type": self.event_type,
            "message": self.message,
            "details": self.details or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f"<ActivityLog [{self.level}] {self.source}: {self.message[:50]}...>"


# =============================================================================
# DEPRECATED MODELS (mantidos para compatibilidade durante migracao)
# =============================================================================

# Os modelos abaixo foram removidos na v4.0:
# - Agent: substituido por Worker
# - Skill: MCP tools gerenciados diretamente pelo Claude
# - Story: Jobs sao a unidade de trabalho principal
# - Sprint: nao mais necessario
# - Task: absorvido em Job
# - Template: simplificado (config no projeto)
# - FactoryEvent: merged com ActivityLog
