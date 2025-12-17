"""
Modelos SQLAlchemy para a Fabrica de Agentes
Sistema generico para construcao de multiplas aplicacoes
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


class AgentStatus(str, Enum):
    STANDBY = "STANDBY"
    READY = "READY"
    EXECUTING = "EXECUTING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SkillType(str, Enum):
    CORE = "core"           # Skills basicas (file, web, data)
    MCP = "mcp"             # Model Context Protocol
    VESSEL = "vessel"       # Vessel skills
    CUSTOM = "custom"       # Skills customizadas


# =============================================================================
# PROJECT - Projetos construidos pela fabrica
# =============================================================================

class Project(Base):
    """Modelo para Projetos - cada aplicacao construida pela fabrica"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(50), unique=True, nullable=False, index=True)  # PRJ-001, PRJ-002
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Tipo e template
    project_type = Column(String(50), nullable=False)  # web-app, data-analysis, document, api-service
    template_used = Column(String(100), nullable=True)

    # Status e progresso
    status = Column(String(50), default=ProjectStatus.PLANNING.value)
    progress = Column(Float, default=0.0)  # 0.0 a 100.0

    # Diretorio do projeto
    folder_path = Column(String(500), nullable=True)  # projects/nome-projeto/
    github_url = Column(String(500), nullable=True)  # URL do repositorio GitHub

    # Configuracoes do projeto
    config = Column(JSON, default=dict)  # Stack, dependencias, etc
    settings = Column(JSON, default=dict)  # Configuracoes especificas

    # Metadados
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), default="system")

    # Relacionamentos
    stories = relationship("Story", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    sprints = relationship("Sprint", back_populates="project", cascade="all, delete-orphan")

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
            "stories_count": len(self.stories) if self.stories else 0,
            "tasks_count": len(self.tasks) if self.tasks else 0,
            "sprints_count": len(self.sprints) if self.sprints else 0
        }

    def __repr__(self):
        return f"<Project {self.project_id}: {self.name} [{self.status}]>"


# =============================================================================
# STORY - User Stories (associadas a projetos)
# =============================================================================

class Story(Base):
    """
    Modelo para User Stories - Estrutura padrao de mercado
    Baseado em boas praticas de Scrum/Agile
    """
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    story_id = Column(String(50), unique=True, nullable=False, index=True)  # US-001, US-002

    # Vinculo com projeto (OBRIGATORIO - projeto eh o primeiro nivel)
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=False, index=True)
    project = relationship("Project", back_populates="stories")

    # === IDENTIFICACAO ===
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    epic_id = Column(String(50), nullable=True, index=True)  # Agrupamento em Epics
    feature_id = Column(String(50), nullable=True)  # Feature pai

    # === STATUS E PLANEJAMENTO ===
    status = Column(String(50), default="BACKLOG", index=True)  # BACKLOG, TO_DO, IN_PROGRESS, TESTING, BLOCKED, DONE
    sprint = Column(Integer, default=1, index=True)
    points = Column(Integer, default=0)  # Story points (Fibonacci: 1,2,3,5,8,13,21)
    priority = Column(Integer, default=5)  # 1=Critica, 3=Alta, 5=Media, 7=Baixa, 9=Backlog
    business_value = Column(Integer, default=0)  # Valor de negocio (1-100)

    # === NARRATIVA (Formato padrao: Como/Quero/Para) ===
    narrative_persona = Column(String(200), nullable=True)  # Como [tipo de usuario]
    narrative_action = Column(String(500), nullable=True)   # Eu quero [acao]
    narrative_benefit = Column(String(500), nullable=True)  # Para que [beneficio]

    # === CRITERIOS E REGRAS (JSON Arrays) ===
    acceptance_criteria = Column(JSON, default=list)    # Lista de criterios de aceite
    business_rules = Column(JSON, default=list)         # Regras de negocio
    definition_of_done = Column(JSON, default=list)     # DoD especifico da story
    technical_notes = Column(JSON, default=list)        # Notas tecnicas para devs
    ui_requirements = Column(JSON, default=list)        # Requisitos de UI/UX

    # === DEPENDENCIAS E RELACIONAMENTOS ===
    dependencies = Column(JSON, default=list)           # IDs de stories que bloqueiam esta
    blocked_by = Column(String(50), nullable=True)      # Story que esta bloqueando
    blocked_reason = Column(Text, nullable=True)        # Motivo do bloqueio
    related_stories = Column(JSON, default=list)        # Stories relacionadas

    # === ATRIBUICAO E EXECUCAO ===
    assigned_to = Column(String(100), nullable=True)    # Agente principal responsavel
    agents = Column(JSON, default=list)                 # Lista de agentes trabalhando
    reviewer = Column(String(100), nullable=True)       # Agente revisor
    qa_agent = Column(String(100), nullable=True)       # Agente de QA

    # === ESTIMATIVAS E METRICAS ===
    estimated_hours = Column(Float, default=0)          # Horas estimadas
    actual_hours = Column(Float, default=0)             # Horas reais gastas
    complexity = Column(String(20), default="medium")   # low, medium, high, very_high
    risk_level = Column(String(20), default="low")      # low, medium, high, critical

    # === TAGS E CATEGORIAS ===
    tags = Column(JSON, default=list)                   # Tags/labels
    category = Column(String(50), nullable=True)        # feature, bugfix, refactor, docs, infra
    component = Column(String(100), nullable=True)      # Componente do sistema afetado

    # === TRACKING DE EXECUCAO ===
    started_at = Column(DateTime, nullable=True)        # Quando iniciou execucao
    completed_at = Column(DateTime, nullable=True)      # Quando foi concluida
    tested_at = Column(DateTime, nullable=True)         # Quando passou em teste

    # === ARTEFATOS GERADOS ===
    artifacts = Column(JSON, default=list)              # Arquivos gerados (codigo, docs, testes)
    pull_request_url = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)

    # === METADADOS ===
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    source = Column(String(50), default="manual")       # manual, auto_generated, imported

    def to_dict(self):
        return {
            "id": self.story_id,
            "story_id": self.story_id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description or "",
            "epic_id": self.epic_id,
            "feature_id": self.feature_id,
            # Status e planejamento
            "status": self.status,
            "sprint": self.sprint or 1,
            "points": self.points,
            "priority": self.priority,
            "business_value": self.business_value,
            # Narrativa
            "narrative": {
                "persona": self.narrative_persona or "",
                "action": self.narrative_action or "",
                "benefit": self.narrative_benefit or "",
                "full": f"Como {self.narrative_persona or '...'}, eu quero {self.narrative_action or '...'}, para que {self.narrative_benefit or '...'}"
            },
            # Criterios e regras
            "acceptance_criteria": self.acceptance_criteria or [],
            "business_rules": self.business_rules or [],
            "definition_of_done": self.definition_of_done or [],
            "technical_notes": self.technical_notes or [],
            "ui_requirements": self.ui_requirements or [],
            # Dependencias
            "dependencies": self.dependencies or [],
            "blocked_by": self.blocked_by,
            "blocked_reason": self.blocked_reason,
            "related_stories": self.related_stories or [],
            # Atribuicao
            "assigned_to": self.assigned_to,
            "agents": self.agents or [],
            "reviewer": self.reviewer,
            "qa_agent": self.qa_agent,
            # Metricas
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "complexity": self.complexity,
            "risk_level": self.risk_level,
            # Tags
            "tags": self.tags or [],
            "category": self.category,
            "component": self.component,
            # Tracking
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tested_at": self.tested_at.isoformat() if self.tested_at else None,
            # Artefatos
            "artifacts": self.artifacts or [],
            "pull_request_url": self.pull_request_url,
            "documentation_url": self.documentation_url,
            # Metadados
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "source": self.source
        }

    def __repr__(self):
        return f"<Story {self.story_id}: {self.title[:30]}...>"


# =============================================================================
# SPRINT - Sprints por Projeto
# =============================================================================

class Sprint(Base):
    """Modelo para Sprints - vinculados a projetos especificos"""
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Vinculo com projeto
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=False, index=True)
    project = relationship("Project", back_populates="sprints")

    # Identificacao do sprint
    sprint_number = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)  # Ex: "Sprint 1 - MVP"

    # Datas
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Status
    status = Column(String(20), default="planned")  # planned, active, completed
    goal = Column(Text, nullable=True)  # Objetivo do sprint

    # Metricas
    planned_points = Column(Integer, default=0)
    completed_points = Column(Integer, default=0)
    velocity = Column(Float, default=0.0)

    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "sprint_number": self.sprint_number,
            "name": self.name or f"Sprint {self.sprint_number}",
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "goal": self.goal or "",
            "planned_points": self.planned_points,
            "completed_points": self.completed_points,
            "velocity": self.velocity,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Sprint {self.project_id}:{self.sprint_number} [{self.status}]>"


# =============================================================================
# AGENT - Agentes Autonomos
# =============================================================================

class Agent(Base):
    """Modelo para Agentes Autonomos - genericos para qualquer projeto"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    domain = Column(String(50), nullable=True)  # management, technology, design, business, custom

    # Status
    status = Column(String(50), default=AgentStatus.STANDBY.value)
    current_task_id = Column(String(50), nullable=True)
    current_project_id = Column(String(50), nullable=True)
    current_story_id = Column(String(50), nullable=True)

    # Configuracao
    priority = Column(Integer, default=5)
    capabilities = Column(JSON, default=list)
    skills = Column(JSON, default=list)  # Skills que o agente pode usar
    config = Column(JSON, default=dict)

    # Dependencias
    dependencies = Column(JSON, default=list)
    can_run_parallel = Column(Boolean, default=True)

    # Metricas
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    total_execution_time = Column(Integer, default=0)
    last_activity = Column(DateTime, nullable=True)

    # Metadados
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.agent_id,
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "domain": self.domain,
            "status": self.status,
            "current_task_id": self.current_task_id,
            "current_project_id": self.current_project_id,
            "current_story_id": self.current_story_id,
            "priority": self.priority,
            "capabilities": self.capabilities or [],
            "skills": self.skills or [],
            "config": self.config or {},
            "dependencies": self.dependencies or [],
            "can_run_parallel": self.can_run_parallel,
            "enabled": self.enabled,
            "metrics": {
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "total_execution_time": self.total_execution_time
            },
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }

    def __repr__(self):
        return f"<Agent {self.agent_id}: {self.name} [{self.status}]>"


# =============================================================================
# SKILL - Habilidades reutilizaveis
# =============================================================================

class Skill(Base):
    """Modelo para Skills - habilidades reutilizaveis pelos agentes"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Tipo de skill
    skill_type = Column(String(20), default=SkillType.CORE.value)  # core, mcp, vessel, custom
    category = Column(String(50), nullable=True)  # file, web, data, ai, integration

    # Configuracao
    config = Column(JSON, default=dict)  # Configuracoes da skill
    parameters = Column(JSON, default=dict)  # Parametros aceitos

    # MCP/Vessel especifico
    server_command = Column(String(500), nullable=True)  # Comando para iniciar servidor MCP
    server_args = Column(JSON, default=list)  # Argumentos do servidor

    # Dependencias
    requires = Column(JSON, default=list)  # Outras skills ou pacotes necessarios

    # Status
    enabled = Column(Boolean, default=True)
    version = Column(String(20), default="1.0.0")

    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "skill_type": self.skill_type,
            "category": self.category,
            "config": self.config or {},
            "parameters": self.parameters or {},
            "server_command": self.server_command,
            "server_args": self.server_args or [],
            "requires": self.requires or [],
            "enabled": self.enabled,
            "version": self.version
        }

    def __repr__(self):
        return f"<Skill {self.skill_id}: {self.name} [{self.skill_type}]>"


# =============================================================================
# TASK - Tarefas na Fila
# =============================================================================

class Task(Base):
    """Modelo para Tarefas - vinculadas a projetos"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True)
    task_type = Column(String(50), nullable=False)

    # Relacionamentos
    project_id = Column(String(50), ForeignKey("projects.project_id"), nullable=True, index=True)
    project = relationship("Project", back_populates="tasks")
    agent_id = Column(String(10), nullable=True, index=True)
    story_id = Column(String(50), nullable=True, index=True)

    # Dados da tarefa
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=5)
    payload = Column(JSON, default=dict)
    dependencies = Column(JSON, default=list)
    skills_required = Column(JSON, default=list)  # Skills necessarias

    # Status e execucao
    status = Column(String(50), default=TaskStatus.PENDING.value, index=True)
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Timestamps
    scheduled_time = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "project_id": self.project_id,
            "agent_id": self.agent_id,
            "story_id": self.story_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "payload": self.payload or {},
            "dependencies": self.dependencies or [],
            "skills_required": self.skills_required or [],
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "retries": self.retries,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Task {self.task_id}: {self.task_type} [{self.status}]>"


# =============================================================================
# ACTIVITY_LOG - Logs de Atividades
# =============================================================================

class ActivityLog(Base):
    """Modelo para Logs de Atividades"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Origem
    source = Column(String(50), nullable=False, index=True)
    source_id = Column(String(20), nullable=True)

    # Contexto
    project_id = Column(String(50), nullable=True, index=True)
    agent_id = Column(String(10), nullable=True, index=True)
    task_id = Column(String(50), nullable=True, index=True)
    story_id = Column(String(50), nullable=True, index=True)

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
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "story_id": self.story_id,
            "level": self.level,
            "event_type": self.event_type,
            "message": self.message,
            "details": self.details or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f"<ActivityLog [{self.level}] {self.source}: {self.message[:50]}...>"


# =============================================================================
# FACTORY_EVENT - Eventos da Fabrica
# =============================================================================

class FactoryEvent(Base):
    """Modelo para Eventos da Fabrica de Agentes"""
    __tablename__ = "factory_events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Tipo de evento
    event_type = Column(String(50), nullable=False, index=True)

    # Contexto
    project_id = Column(String(50), nullable=True)
    task_id = Column(String(50), nullable=True)
    story_id = Column(String(50), nullable=True)
    agent_id = Column(String(10), nullable=True)
    skill_id = Column(String(50), nullable=True)

    # Dados do evento
    description = Column(Text, nullable=True)
    before_state = Column(JSON, default=dict)
    after_state = Column(JSON, default=dict)
    event_data = Column(JSON, default=dict)

    # Resultado
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "project_id": self.project_id,
            "task_id": self.task_id,
            "story_id": self.story_id,
            "agent_id": self.agent_id,
            "skill_id": self.skill_id,
            "description": self.description,
            "before_state": self.before_state or {},
            "after_state": self.after_state or {},
            "event_data": self.event_data or {},
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

    def __repr__(self):
        return f"<FactoryEvent {self.event_type} at {self.timestamp}>"


# =============================================================================
# TEMPLATE - Templates de Projetos
# =============================================================================

class Template(Base):
    """Modelo para Templates de Projetos"""
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Tipo e categoria
    project_type = Column(String(50), nullable=False)  # web-app, data-analysis, document, api-service
    category = Column(String(50), nullable=True)  # fullstack, frontend, backend, etc

    # Estrutura do template
    structure = Column(JSON, default=dict)  # Estrutura de pastas/arquivos
    default_config = Column(JSON, default=dict)  # Configuracoes padrao
    required_skills = Column(JSON, default=list)  # Skills necessarias
    recommended_agents = Column(JSON, default=list)  # Agentes recomendados

    # Stack tecnologica
    stack = Column(JSON, default=dict)  # {frontend: "react", backend: "fastapi", db: "postgresql"}

    # Metadados
    version = Column(String(20), default="1.0.0")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "project_type": self.project_type,
            "category": self.category,
            "structure": self.structure or {},
            "default_config": self.default_config or {},
            "required_skills": self.required_skills or [],
            "recommended_agents": self.recommended_agents or [],
            "stack": self.stack or {},
            "version": self.version,
            "enabled": self.enabled
        }

    def __repr__(self):
        return f"<Template {self.template_id}: {self.name}>"


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
    role = Column(String(20), nullable=False, default="VIEWER")  # ADMIN, MANAGER, VIEWER
    active = Column(Boolean, default=True, nullable=False)

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self):
        return f"<User {self.username} [{self.role}]>"
