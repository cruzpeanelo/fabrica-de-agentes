"""
Autonomous Developer - Desenvolvedor Autonomo de Projetos
=========================================================

Este modulo contem o sistema que REALMENTE desenvolve projetos de forma autonoma.
Os agentes usam skills reais para criar codigo, arquivos e estruturas.

Fluxo:
1. Recebe um projeto com stories
2. Para cada story em TO_DO:
   - Analisa requisitos
   - Determina agentes necessarios
   - Executa skills para criar codigo REAL
   - Move story pelo pipeline
   - Registra aprendizado dos agentes

Diferencial:
- Usa RealSkills para criar arquivos de verdade
- Agentes aprendem com cada execucao (AgentMemory)
- Suporta multiplos projetos em paralelo
- Intervencao humana em pontos criticos
"""

import os
import json
import threading
import queue
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from factory.database.connection import SessionLocal
from factory.database.models import Project, Story, Agent, ActivityLog, Task
from factory.skills.real_skills import RealSkills, AgentMemory, get_real_skills


class DevelopmentStage(Enum):
    """Estagios do desenvolvimento"""
    ANALYSIS = "ANALYSIS"
    DESIGN = "DESIGN"
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"
    TESTING = "TESTING"
    REVIEW = "REVIEW"
    DONE = "DONE"


@dataclass
class DevelopmentTask:
    """Tarefa de desenvolvimento para um agente"""
    task_id: str
    project_id: str
    story_id: str
    agent_id: str
    stage: DevelopmentStage
    action: str
    params: Dict = field(default_factory=dict)
    priority: int = 5
    requires_approval: bool = False
    sequence: int = field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))

    def __lt__(self, other):
        """Comparacao para PriorityQueue"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.sequence < other.sequence


@dataclass
class ProjectDevelopment:
    """Estado do desenvolvimento de um projeto"""
    project_id: str
    project_path: str
    stories_total: int = 0
    stories_completed: int = 0
    current_stage: DevelopmentStage = DevelopmentStage.ANALYSIS
    active_agents: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class AutonomousDeveloper:
    """
    Desenvolvedor Autonomo - Executa desenvolvimento real de projetos

    Capacidades:
    - Cria codigo backend (FastAPI, SQLAlchemy)
    - Cria codigo frontend (Vue.js)
    - Cria testes automatizados
    - Gerencia multiplos projetos em paralelo
    - Agentes aprendem com cada tarefa
    """

    # Mapeamento de agentes para suas responsabilidades
    AGENT_ROLES = {
        "AGT-005": {"name": "Analista", "stage": DevelopmentStage.ANALYSIS,
                   "skills": ["read_and_analyze_document", "extract_requirements"]},
        "AGT-007": {"name": "Especialista BD", "stage": DevelopmentStage.BACKEND,
                   "skills": ["create_sqlalchemy_model", "create_database_setup"]},
        "AGT-008": {"name": "Backend Dev", "stage": DevelopmentStage.BACKEND,
                   "skills": ["create_fastapi_router", "create_main_app"]},
        "AGT-009": {"name": "Frontend Dev", "stage": DevelopmentStage.FRONTEND,
                   "skills": ["create_vue_component", "create_vue_page"]},
        "AGT-011": {"name": "Revisor", "stage": DevelopmentStage.REVIEW,
                   "skills": ["review_code", "check_standards"]},
        "AGT-013": {"name": "Arquiteto", "stage": DevelopmentStage.DESIGN,
                   "skills": ["design_architecture", "define_structure"]},
        "AGT-015": {"name": "QA", "stage": DevelopmentStage.TESTING,
                   "skills": ["create_test_file", "run_tests"]},
    }

    def __init__(self, max_parallel_projects: int = 3, max_workers: int = 5):
        self.skills = get_real_skills()
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.active_projects: Dict[str, ProjectDevelopment] = {}
        self.max_parallel_projects = max_parallel_projects
        self.max_workers = max_workers
        self._running = False
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._monitor_thread: Optional[threading.Thread] = None

        # Callbacks para integracao
        self.on_file_created: Optional[Callable] = None
        self.on_stage_complete: Optional[Callable] = None
        self.on_approval_needed: Optional[Callable] = None

    def start(self):
        """Inicia o desenvolvedor autonomo"""
        if self._running:
            return

        self._running = True
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)

        # Thread de monitoramento
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        print(f"[AutonomousDeveloper] Iniciado com {self.max_workers} workers")

    def stop(self):
        """Para o desenvolvedor"""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=False)
        print("[AutonomousDeveloper] Parado")

    def develop_project(self, project_id: str) -> Dict:
        """
        Inicia o desenvolvimento completo de um projeto

        Este metodo:
        1. Carrega o projeto e suas stories
        2. Determina a estrutura a ser criada
        3. Agenda tarefas para os agentes
        4. Executa desenvolvimento em paralelo
        """
        db = SessionLocal()
        try:
            # Carrega projeto
            project = db.query(Project).filter(Project.project_id == project_id).first()
            if not project:
                return {"success": False, "error": "Projeto nao encontrado"}

            # Determina caminho do projeto
            config = project.config or {}
            project_path = config.get("output_path") or str(
                Path(__file__).parent.parent.parent / "projects" / project.name.lower().replace(" ", "-")
            )

            # Cria estrutura de diretorios
            self._create_project_structure(project_path)

            # Registra projeto ativo
            dev_state = ProjectDevelopment(
                project_id=project_id,
                project_path=project_path
            )
            self.active_projects[project_id] = dev_state

            # Carrega stories para desenvolver
            stories = db.query(Story).filter(
                Story.project_id == project_id,
                Story.status.in_(["TO_DO", "BACKLOG", "pending_review", "READY"])
            ).all()

            dev_state.stories_total = len(stories)

            self._log_activity(db, project_id, "DEVELOPER",
                              "development_started",
                              f"Iniciando desenvolvimento de {project.name} com {len(stories)} stories")

            # Agenda desenvolvimento
            self._schedule_development(project, stories, project_path, db)

            return {
                "success": True,
                "project": project.name,
                "project_path": project_path,
                "stories_to_develop": len(stories)
            }

        finally:
            db.close()

    def _create_project_structure(self, project_path: str):
        """Cria estrutura de diretorios do projeto"""
        dirs = [
            "backend",
            "backend/routers",
            "backend/models",
            "backend/schemas",
            "backend/services",
            "backend/tests",
            "frontend",
            "frontend/src",
            "frontend/src/components",
            "frontend/src/views",
            "frontend/src/services",
            "frontend/public",
            "database",
            "docs"
        ]

        for d in dirs:
            Path(project_path, d).mkdir(parents=True, exist_ok=True)

        print(f"[AutonomousDeveloper] Estrutura criada em {project_path}")

    def _schedule_development(self, project: Project, stories: List[Story],
                             project_path: str, db):
        """Agenda tarefas de desenvolvimento"""

        # 1. Primeiro: Setup do banco de dados
        self._queue_task(DevelopmentTask(
            task_id=f"SETUP-DB-{project.project_id}",
            project_id=project.project_id,
            story_id="SETUP",
            agent_id="AGT-007",
            stage=DevelopmentStage.BACKEND,
            action="create_database_setup",
            params={"project_path": project_path, "db_name": "app.db"},
            priority=1
        ))

        # 2. Para cada story, agenda desenvolvimento
        for i, story in enumerate(stories):
            # Analisa requisitos da story
            self._queue_task(DevelopmentTask(
                task_id=f"ANALYZE-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-005",
                stage=DevelopmentStage.ANALYSIS,
                action="analyze_story",
                params={"story": story.to_dict(), "project_path": project_path},
                priority=2
            ))

            # Extrai nome do recurso da story
            resource_name = self._extract_resource_name(story)
            table_name = resource_name.lower().replace(" ", "_")

            # Cria modelo
            self._queue_task(DevelopmentTask(
                task_id=f"MODEL-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-007",
                stage=DevelopmentStage.BACKEND,
                action="create_sqlalchemy_model",
                params={
                    "project_path": project_path,
                    "name": resource_name,
                    "table_name": table_name,
                    "fields": self._generate_fields_from_story(story),
                    "description": story.description[:200] if story.description else ""
                },
                priority=3
            ))

            # Cria router
            self._queue_task(DevelopmentTask(
                task_id=f"ROUTER-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-008",
                stage=DevelopmentStage.BACKEND,
                action="create_fastapi_router",
                params={
                    "project_path": project_path,
                    "name": resource_name,
                    "model_name": table_name,
                    "fields": self._generate_fields_from_story(story)
                },
                priority=4
            ))

            # Cria componente Vue
            self._queue_task(DevelopmentTask(
                task_id=f"VUE-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-009",
                stage=DevelopmentStage.FRONTEND,
                action="create_vue_component",
                params={
                    "project_path": project_path,
                    "name": resource_name,
                    "api_url": f"/api/{table_name}",
                    "fields": self._generate_fields_from_story(story)
                },
                priority=5
            ))

            # Cria testes
            self._queue_task(DevelopmentTask(
                task_id=f"TEST-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-015",
                stage=DevelopmentStage.TESTING,
                action="create_test_file",
                params={
                    "project_path": project_path,
                    "name": resource_name,
                    "route_prefix": table_name
                },
                priority=6
            ))

        # 3. Final: Cria main.py com todos os routers
        routers = [self._extract_resource_name(s).lower().replace(" ", "_") for s in stories]
        self._queue_task(DevelopmentTask(
            task_id=f"MAIN-{project.project_id}",
            project_id=project.project_id,
            story_id="SETUP",
            agent_id="AGT-008",
            stage=DevelopmentStage.BACKEND,
            action="create_main_app",
            params={
                "project_path": project_path,
                "app_name": project.name,
                "routers": routers
            },
            priority=10
        ))

    def _queue_task(self, task: DevelopmentTask):
        """Adiciona tarefa na fila"""
        self.task_queue.put(task)

    def _monitor_loop(self):
        """Loop de monitoramento e execucao de tarefas"""
        while self._running:
            try:
                # Pega proxima tarefa
                try:
                    task = self.task_queue.get(timeout=2)
                except queue.Empty:
                    continue

                # Executa tarefa em thread separada
                if self._executor:
                    self._executor.submit(self._execute_task, task)

            except Exception as e:
                print(f"[AutonomousDeveloper] Erro no monitor: {e}")

            time.sleep(0.5)

    def _execute_task(self, task: DevelopmentTask):
        """Executa uma tarefa de desenvolvimento"""
        db = SessionLocal()
        try:
            print(f"[{task.agent_id}] Executando {task.action} para {task.story_id}")

            # Atualiza projeto ativo
            if task.project_id in self.active_projects:
                dev_state = self.active_projects[task.project_id]
                if task.agent_id not in dev_state.active_agents:
                    dev_state.active_agents.append(task.agent_id)

            # Executa skill correspondente
            result = self._run_skill(task, db)

            # Registra atividade
            self._log_activity(
                db, task.project_id, task.agent_id,
                f"skill_{task.action}",
                f"Executado {task.action}: {len(result.files_created)} arquivos criados" if result.success else f"Erro: {result.errors}",
                task.story_id
            )

            # Atualiza estado do projeto
            if task.project_id in self.active_projects:
                dev_state = self.active_projects[task.project_id]
                dev_state.files_created.extend(result.files_created)
                if result.errors:
                    dev_state.errors.extend(result.errors)

            # Callback de arquivo criado
            if result.success and result.files_created and self.on_file_created:
                for f in result.files_created:
                    self.on_file_created(task.project_id, task.agent_id, f)

        except Exception as e:
            print(f"[{task.agent_id}] Erro executando {task.action}: {e}")
            self._log_activity(
                db, task.project_id, task.agent_id,
                "error", f"Erro: {str(e)}", task.story_id
            )
        finally:
            db.close()

    def _run_skill(self, task: DevelopmentTask, db) -> Any:
        """Executa a skill correspondente a tarefa"""
        action = task.action
        params = task.params
        agent_id = task.agent_id

        if action == "create_database_setup":
            return self.skills.create_database_setup(
                agent_id, params["project_path"], params.get("db_name", "app.db")
            )

        elif action == "create_sqlalchemy_model":
            return self.skills.create_sqlalchemy_model(
                agent_id, params["project_path"], params["name"],
                params["table_name"], params["fields"], params.get("description", "")
            )

        elif action == "create_fastapi_router":
            return self.skills.create_fastapi_router(
                agent_id, params["project_path"], params["name"],
                params["model_name"], params["fields"]
            )

        elif action == "create_vue_component":
            return self.skills.create_vue_component(
                agent_id, params["project_path"], params["name"],
                params["api_url"], params["fields"]
            )

        elif action == "create_test_file":
            return self.skills.create_test_file(
                agent_id, params["project_path"], params["name"],
                params["route_prefix"]
            )

        elif action == "create_main_app":
            return self.skills.create_main_app(
                agent_id, params["project_path"], params["app_name"],
                params["routers"]
            )

        elif action == "read_and_analyze_document":
            return self.skills.read_and_analyze_document(agent_id, params["file_path"])

        else:
            # Skill nao implementada - retorna resultado vazio
            from factory.skills.real_skills import SkillResult
            return SkillResult(
                success=False,
                skill_name=action,
                agent_id=agent_id,
                errors=[f"Skill {action} nao implementada"]
            )

    def _extract_resource_name(self, story: Story) -> str:
        """Extrai nome do recurso da story"""
        title = story.title or ""

        # Remove prefixos comuns
        prefixes = ["Cadastro de", "Gestao de", "Visualizacao de", "Edicao de",
                   "Lista de", "Criacao de", "Mapeamento", "API de"]

        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
                break

        # Remove sufixos
        suffixes = ["- Mapeamento AS-IS", "AS-IS", "TO-BE", "com", "por"]
        for suffix in suffixes:
            if suffix in title:
                title = title.split(suffix)[0].strip()

        # Limpa e retorna
        return title.strip() or "Resource"

    def _generate_fields_from_story(self, story: Story) -> List[Dict]:
        """Gera lista de campos baseado na story"""
        # Campos padrao
        fields = [
            {"name": "name", "type": "str", "nullable": False},
            {"name": "description", "type": "text", "nullable": True},
        ]

        # Analisa acceptance criteria para campos adicionais
        criteria = story.acceptance_criteria
        if criteria:
            if isinstance(criteria, str):
                try:
                    criteria = json.loads(criteria)
                except:
                    criteria = [criteria]

            criteria_text = " ".join(criteria).lower() if isinstance(criteria, list) else str(criteria).lower()

            # Detecta campos comuns
            if "status" in criteria_text:
                fields.append({"name": "status", "type": "str", "default": "ACTIVE"})
            if "valor" in criteria_text or "preco" in criteria_text or "custo" in criteria_text:
                fields.append({"name": "value", "type": "float", "nullable": True})
            if "data" in criteria_text or "prazo" in criteria_text:
                fields.append({"name": "due_date", "type": "datetime", "nullable": True})
            if "responsavel" in criteria_text or "usuario" in criteria_text:
                fields.append({"name": "owner", "type": "str", "nullable": True})
            if "categoria" in criteria_text or "tipo" in criteria_text:
                fields.append({"name": "category", "type": "str", "nullable": True})

        return fields

    def get_project_status(self, project_id: str) -> Dict:
        """Retorna status do desenvolvimento de um projeto"""
        if project_id not in self.active_projects:
            return {"status": "not_found"}

        dev_state = self.active_projects[project_id]
        return {
            "project_id": project_id,
            "project_path": dev_state.project_path,
            "stories_total": dev_state.stories_total,
            "stories_completed": dev_state.stories_completed,
            "current_stage": dev_state.current_stage.value,
            "active_agents": dev_state.active_agents,
            "files_created": len(dev_state.files_created),
            "errors": dev_state.errors,
            "tasks_pending": self.task_queue.qsize()
        }

    def get_agent_memory_summary(self, agent_id: str) -> Dict:
        """Retorna resumo da memoria de um agente"""
        memory = self.skills.get_memory(agent_id)
        return memory.get_summary()

    def _log_activity(self, db, project_id: str, agent_id: str,
                      event_type: str, message: str, story_id: str = None):
        """Registra atividade"""
        log = ActivityLog(
            source="autonomous_developer",
            source_id="DEVELOPER",
            agent_id=agent_id,
            project_id=project_id,
            story_id=story_id,
            event_type=event_type,
            message=message,
            level="INFO"
        )
        db.add(log)
        try:
            db.commit()
        except:
            db.rollback()


# Instancia global
_developer: Optional[AutonomousDeveloper] = None


def get_developer() -> AutonomousDeveloper:
    """Retorna instancia global do desenvolvedor"""
    global _developer
    if _developer is None:
        _developer = AutonomousDeveloper()
    return _developer


def start_developer():
    """Inicia o desenvolvedor global"""
    developer = get_developer()
    developer.start()
    return developer


def stop_developer():
    """Para o desenvolvedor global"""
    global _developer
    if _developer:
        _developer.stop()
        _developer = None


if __name__ == "__main__":
    # Teste
    print("Testando AutonomousDeveloper...")

    developer = start_developer()

    # Testa com projeto de exemplo
    result = developer.develop_project("PROJ-20251216221517")
    print(f"Resultado: {result}")

    # Aguarda execucao
    time.sleep(30)

    # Verifica status
    status = developer.get_project_status("PROJ-20251216221517")
    print(f"Status: {status}")

    stop_developer()
