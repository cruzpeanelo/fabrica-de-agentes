"""
Repositorios para acesso ao banco de dados - Fabrica de Agentes
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from .models import (
    Project, Story, Agent, Skill, Task, Sprint,
    ActivityLog, FactoryEvent, Template, User,
    ProjectStatus, AgentStatus, TaskStatus, SkillType
)


# =============================================================================
# PROJECT REPOSITORY
# =============================================================================

class ProjectRepository:
    """Repositorio para gerenciamento de Projetos"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, project_data: dict) -> Project:
        """Cria novo projeto"""
        project = Project(**project_data)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Busca projeto por ID"""
        return self.db.query(Project).filter(Project.project_id == project_id).first()

    def get_all(self, status: str = None, project_type: str = None) -> List[Project]:
        """Lista todos os projetos com filtros opcionais"""
        query = self.db.query(Project)
        if status:
            query = query.filter(Project.status == status)
        if project_type:
            query = query.filter(Project.project_type == project_type)
        return query.order_by(desc(Project.updated_at)).all()

    def update(self, project_id: str, data: dict) -> Optional[Project]:
        """Atualiza projeto"""
        project = self.get_by_id(project_id)
        if project:
            for key, value in data.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            project.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(project)
        return project

    def delete(self, project_id: str) -> bool:
        """Remove projeto"""
        project = self.get_by_id(project_id)
        if project:
            self.db.delete(project)
            self.db.commit()
            return True
        return False

    def count_by_status(self) -> Dict[str, int]:
        """Conta projetos por status"""
        result = {}
        for status in ProjectStatus:
            count = self.db.query(Project).filter(Project.status == status.value).count()
            result[status.value] = count
        return result


# =============================================================================
# STORY REPOSITORY
# =============================================================================

class StoryRepository:
    """Repositorio para gerenciamento de Stories"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, story_data: dict) -> Story:
        """Cria nova story"""
        story = Story(**story_data)
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)
        return story

    def get_by_id(self, story_id: str) -> Optional[Story]:
        """Busca story por ID"""
        return self.db.query(Story).filter(Story.story_id == story_id).first()

    def get_by_project(self, project_id: str) -> List[Story]:
        """Lista stories de um projeto"""
        return self.db.query(Story).filter(Story.project_id == project_id).all()

    def get_by_sprint(self, sprint: int, project_id: str = None) -> List[Story]:
        """Lista stories de um sprint"""
        query = self.db.query(Story).filter(Story.sprint == sprint)
        if project_id:
            query = query.filter(Story.project_id == project_id)
        return query.order_by(Story.priority.desc()).all()

    def update_status(self, story_id: str, status: str) -> Optional[Story]:
        """Atualiza status da story"""
        story = self.get_by_id(story_id)
        if story:
            story.status = status
            story.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(story)
        return story

    def get_all(self) -> List[Story]:
        """Lista todas as stories"""
        return self.db.query(Story).order_by(desc(Story.updated_at)).all()


# =============================================================================
# SPRINT REPOSITORY
# =============================================================================

class SprintRepository:
    """Repositorio para gerenciamento de Sprints por Projeto"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, sprint_data: dict) -> Sprint:
        """Cria novo sprint"""
        sprint = Sprint(**sprint_data)
        self.db.add(sprint)
        self.db.commit()
        self.db.refresh(sprint)
        return sprint

    def get_by_id(self, sprint_id: int) -> Optional[Sprint]:
        """Busca sprint por ID"""
        return self.db.query(Sprint).filter(Sprint.id == sprint_id).first()

    def get_by_project(self, project_id: str) -> List[Sprint]:
        """Lista sprints de um projeto"""
        return self.db.query(Sprint).filter(
            Sprint.project_id == project_id
        ).order_by(Sprint.sprint_number).all()

    def get_active_sprint(self, project_id: str) -> Optional[Sprint]:
        """Retorna sprint ativo do projeto"""
        return self.db.query(Sprint).filter(
            Sprint.project_id == project_id,
            Sprint.status == "active"
        ).first()

    def get_or_create(self, project_id: str, sprint_number: int) -> Sprint:
        """Busca sprint ou cria se nao existir"""
        sprint = self.db.query(Sprint).filter(
            Sprint.project_id == project_id,
            Sprint.sprint_number == sprint_number
        ).first()

        if not sprint:
            sprint = Sprint(
                project_id=project_id,
                sprint_number=sprint_number,
                name=f"Sprint {sprint_number}",
                status="planned"
            )
            self.db.add(sprint)
            self.db.commit()
            self.db.refresh(sprint)

        return sprint

    def update(self, sprint_id: int, data: dict) -> Optional[Sprint]:
        """Atualiza sprint"""
        sprint = self.get_by_id(sprint_id)
        if sprint:
            for key, value in data.items():
                if hasattr(sprint, key) and value is not None:
                    setattr(sprint, key, value)
            sprint.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(sprint)
        return sprint

    def activate_sprint(self, project_id: str, sprint_number: int) -> Optional[Sprint]:
        """Ativa um sprint e desativa os outros do projeto"""
        # Desativa todos os sprints do projeto
        self.db.query(Sprint).filter(
            Sprint.project_id == project_id
        ).update({"status": "planned"})

        # Ativa o sprint especificado
        sprint = self.db.query(Sprint).filter(
            Sprint.project_id == project_id,
            Sprint.sprint_number == sprint_number
        ).first()

        if sprint:
            sprint.status = "active"
            sprint.start_date = datetime.utcnow()
            self.db.commit()
            self.db.refresh(sprint)

        return sprint

    def complete_sprint(self, sprint_id: int) -> Optional[Sprint]:
        """Completa um sprint"""
        sprint = self.get_by_id(sprint_id)
        if sprint:
            sprint.status = "completed"
            sprint.end_date = datetime.utcnow()
            self.db.commit()
            self.db.refresh(sprint)
        return sprint

    def delete(self, sprint_id: int) -> bool:
        """Remove sprint"""
        sprint = self.get_by_id(sprint_id)
        if sprint:
            self.db.delete(sprint)
            self.db.commit()
            return True
        return False


# =============================================================================
# AGENT REPOSITORY
# =============================================================================

class AgentRepository:
    """Repositorio para gerenciamento de Agentes"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, agent_data: dict) -> Agent:
        """Cria novo agente"""
        agent = Agent(**agent_data)
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """Busca agente por ID"""
        return self.db.query(Agent).filter(Agent.agent_id == agent_id).first()

    def get_all(self, enabled_only: bool = True) -> List[Agent]:
        """Lista todos os agentes"""
        query = self.db.query(Agent)
        if enabled_only:
            query = query.filter(Agent.enabled == True)
        return query.order_by(Agent.priority.desc(), Agent.agent_id).all()

    def get_by_domain(self, domain: str) -> List[Agent]:
        """Lista agentes por dominio"""
        return self.db.query(Agent).filter(Agent.domain == domain).all()

    def get_by_status(self, status: str) -> List[Agent]:
        """Lista agentes por status"""
        return self.db.query(Agent).filter(Agent.status == status).all()

    def update_status(self, agent_id: str, status: str, task_id: str = None, project_id: str = None) -> Optional[Agent]:
        """Atualiza status do agente"""
        agent = self.get_by_id(agent_id)
        if agent:
            agent.status = status
            agent.current_task_id = task_id
            agent.current_project_id = project_id
            agent.last_activity = datetime.utcnow()
            self.db.commit()
            self.db.refresh(agent)
        return agent

    def increment_completed(self, agent_id: str) -> Optional[Agent]:
        """Incrementa contador de tarefas completadas"""
        agent = self.get_by_id(agent_id)
        if agent:
            agent.tasks_completed += 1
            agent.last_activity = datetime.utcnow()
            self.db.commit()
        return agent


# =============================================================================
# SKILL REPOSITORY
# =============================================================================

class SkillRepository:
    """Repositorio para gerenciamento de Skills"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, skill_data: dict) -> Skill:
        """Cria nova skill"""
        skill = Skill(**skill_data)
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def get_by_id(self, skill_id: str) -> Optional[Skill]:
        """Busca skill por ID"""
        return self.db.query(Skill).filter(Skill.skill_id == skill_id).first()

    def get_all(self, enabled_only: bool = True) -> List[Skill]:
        """Lista todas as skills"""
        query = self.db.query(Skill)
        if enabled_only:
            query = query.filter(Skill.enabled == True)
        return query.order_by(Skill.skill_type, Skill.name).all()

    def get_by_type(self, skill_type: str) -> List[Skill]:
        """Lista skills por tipo (core, mcp, vessel, custom)"""
        return self.db.query(Skill).filter(Skill.skill_type == skill_type).all()

    def get_by_category(self, category: str) -> List[Skill]:
        """Lista skills por categoria"""
        return self.db.query(Skill).filter(Skill.category == category).all()


# =============================================================================
# TASK REPOSITORY
# =============================================================================

class TaskRepository:
    """Repositorio para gerenciamento de Tasks"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, task_data: dict) -> Task:
        """Cria nova task"""
        task = Task(**task_data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: str) -> Optional[Task]:
        """Busca task por ID"""
        return self.db.query(Task).filter(Task.task_id == task_id).first()

    def get_pending(self, project_id: str = None) -> List[Task]:
        """Lista tasks pendentes"""
        query = self.db.query(Task).filter(Task.status == TaskStatus.PENDING.value)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        return query.order_by(Task.priority.desc(), Task.created_at).all()

    def get_by_project(self, project_id: str) -> List[Task]:
        """Lista tasks de um projeto"""
        return self.db.query(Task).filter(Task.project_id == project_id).all()

    def get_by_agent(self, agent_id: str) -> List[Task]:
        """Lista tasks de um agente"""
        return self.db.query(Task).filter(Task.agent_id == agent_id).all()

    def update_status(self, task_id: str, status: str, result: str = None, error: str = None) -> Optional[Task]:
        """Atualiza status da task"""
        task = self.get_by_id(task_id)
        if task:
            task.status = status
            if status == TaskStatus.IN_PROGRESS.value:
                task.started_at = datetime.utcnow()
            elif status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                task.completed_at = datetime.utcnow()
            if result:
                task.result = result
            if error:
                task.error = error
            self.db.commit()
            self.db.refresh(task)
        return task


# =============================================================================
# ACTIVITY LOG REPOSITORY
# =============================================================================

class ActivityLogRepository:
    """Repositorio para gerenciamento de Logs"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, log_data: dict) -> ActivityLog:
        """Cria novo log"""
        log = ActivityLog(**log_data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_recent(self, limit: int = 100, project_id: str = None) -> List[ActivityLog]:
        """Lista logs recentes"""
        query = self.db.query(ActivityLog)
        if project_id:
            query = query.filter(ActivityLog.project_id == project_id)
        return query.order_by(desc(ActivityLog.timestamp)).limit(limit).all()

    def get_by_agent(self, agent_id: str, limit: int = 50) -> List[ActivityLog]:
        """Lista logs de um agente"""
        return self.db.query(ActivityLog).filter(
            ActivityLog.agent_id == agent_id
        ).order_by(desc(ActivityLog.timestamp)).limit(limit).all()

    def get_by_level(self, level: str, limit: int = 100) -> List[ActivityLog]:
        """Lista logs por nivel"""
        return self.db.query(ActivityLog).filter(
            ActivityLog.level == level
        ).order_by(desc(ActivityLog.timestamp)).limit(limit).all()


# =============================================================================
# FACTORY EVENT REPOSITORY
# =============================================================================

class FactoryEventRepository:
    """Repositorio para gerenciamento de Eventos"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, event_data: dict) -> FactoryEvent:
        """Cria novo evento"""
        event = FactoryEvent(**event_data)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_recent(self, limit: int = 100) -> List[FactoryEvent]:
        """Lista eventos recentes"""
        return self.db.query(FactoryEvent).order_by(
            desc(FactoryEvent.timestamp)
        ).limit(limit).all()

    def get_by_project(self, project_id: str) -> List[FactoryEvent]:
        """Lista eventos de um projeto"""
        return self.db.query(FactoryEvent).filter(
            FactoryEvent.project_id == project_id
        ).order_by(desc(FactoryEvent.timestamp)).all()


# =============================================================================
# TEMPLATE REPOSITORY
# =============================================================================

class TemplateRepository:
    """Repositorio para gerenciamento de Templates"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, template_data: dict) -> Template:
        """Cria novo template"""
        template = Template(**template_data)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_by_id(self, template_id: str) -> Optional[Template]:
        """Busca template por ID"""
        return self.db.query(Template).filter(Template.template_id == template_id).first()

    def get_all(self, enabled_only: bool = True) -> List[Template]:
        """Lista todos os templates"""
        query = self.db.query(Template)
        if enabled_only:
            query = query.filter(Template.enabled == True)
        return query.order_by(Template.project_type, Template.name).all()

    def get_by_type(self, project_type: str) -> List[Template]:
        """Lista templates por tipo de projeto"""
        return self.db.query(Template).filter(Template.project_type == project_type).all()


# =============================================================================
# USER REPOSITORY
# =============================================================================

class UserRepository:
    """Repositorio para gerenciamento de Usuarios"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, user_data: dict) -> User:
        """Cria novo usuario"""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_username(self, username: str) -> Optional[User]:
        """Busca usuario por username"""
        return self.db.query(User).filter(User.username == username).first()

    def get_all(self, active_only: bool = True) -> List[User]:
        """Lista todos os usuarios"""
        query = self.db.query(User)
        if active_only:
            query = query.filter(User.active == True)
        return query.all()

    def update_last_login(self, username: str) -> Optional[User]:
        """Atualiza ultimo login"""
        user = self.get_by_username(username)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
        return user
