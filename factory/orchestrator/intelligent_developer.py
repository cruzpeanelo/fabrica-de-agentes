"""
Intelligent Developer - Desenvolvedor Inteligente com LLM
=========================================================

Este modulo extende o AutonomousDeveloper com inteligencia real
usando Claude (LLM) para tomar decisoes e gerar codigo.

Diferenciais:
- Agentes com "cerebro" (AgentBrain) que pensam e decidem
- Geracao de codigo contextualizada e adaptativa
- Aprendizado continuo com cada tarefa
- Hierarquia de aprovacoes respeitada
- Colaboracao inteligente entre agentes
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
from factory.ai.claude_integration import AgentBrain, ClaudeClient, get_claude_client, create_agent_brain
from factory.skills.intelligent_skills import IntelligentSkills, get_intelligent_skills
from factory.skills.real_skills import RealSkills, get_real_skills, SkillResult


class DevelopmentStage(Enum):
    """Estagios do desenvolvimento"""
    PLANNING = "PLANNING"
    ANALYSIS = "ANALYSIS"
    DESIGN = "DESIGN"
    BACKEND = "BACKEND"
    FRONTEND = "FRONTEND"
    TESTING = "TESTING"
    REVIEW = "REVIEW"
    DONE = "DONE"


@dataclass
class IntelligentTask:
    """Tarefa de desenvolvimento com inteligencia"""
    task_id: str
    project_id: str
    story_id: str
    agent_id: str
    stage: DevelopmentStage
    action: str
    params: Dict = field(default_factory=dict)
    priority: int = 5
    requires_approval: bool = False
    use_intelligence: bool = True  # Usar LLM ou template
    reasoning: Optional[str] = None  # Raciocinio do agente
    sequence: int = field(default_factory=lambda: int(datetime.utcnow().timestamp() * 1000))

    def __lt__(self, other):
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.sequence < other.sequence


@dataclass
class ProjectState:
    """Estado do desenvolvimento de um projeto"""
    project_id: str
    project_path: str
    project_name: str
    stories_total: int = 0
    stories_completed: int = 0
    current_stage: DevelopmentStage = DevelopmentStage.PLANNING
    active_agents: Dict[str, str] = field(default_factory=dict)  # agent_id -> current_task
    files_created: List[str] = field(default_factory=list)
    decisions_made: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    architecture: Optional[Dict] = None


class IntelligentDeveloper:
    """
    Desenvolvedor Inteligente - Usa LLM para desenvolvimento autonomo

    Cada agente tem seu proprio cerebro (AgentBrain) que:
    - Pensa sobre a tarefa antes de executar
    - Toma decisoes contextualizadas
    - Aprende com cada execucao
    - Pede aprovacao quando necessario
    """

    # Configuracao dos agentes
    AGENT_CONFIG = {
        "AGT-003": {
            "name": "Product Owner",
            "role": "Product Owner responsavel por definir e priorizar requisitos",
            "capabilities": ["analise de requisitos", "criacao de stories", "priorizacao"],
            "stage": DevelopmentStage.PLANNING,
            "requires_approval_from": None,  # Autoridade maxima para produto
            "can_approve": ["AGT-005"]
        },
        "AGT-005": {
            "name": "Analista de Sistemas",
            "role": "Analista que detalha requisitos tecnicos",
            "capabilities": ["analise tecnica", "documentacao", "especificacao"],
            "stage": DevelopmentStage.ANALYSIS,
            "requires_approval_from": "AGT-003",
            "can_approve": ["AGT-007", "AGT-008", "AGT-009"]
        },
        "AGT-007": {
            "name": "Especialista BD",
            "role": "Especialista em banco de dados e modelagem",
            "capabilities": ["SQLAlchemy", "PostgreSQL", "SQLite", "modelagem"],
            "stage": DevelopmentStage.BACKEND,
            "requires_approval_from": "AGT-013",
            "can_approve": []
        },
        "AGT-008": {
            "name": "Backend Dev",
            "role": "Desenvolvedor backend senior especialista em APIs",
            "capabilities": ["FastAPI", "Python", "REST", "autenticacao", "seguranca"],
            "stage": DevelopmentStage.BACKEND,
            "requires_approval_from": "AGT-013",
            "can_approve": []
        },
        "AGT-009": {
            "name": "Frontend Dev",
            "role": "Desenvolvedor frontend especialista em Vue.js",
            "capabilities": ["Vue.js", "JavaScript", "CSS", "UI/UX"],
            "stage": DevelopmentStage.FRONTEND,
            "requires_approval_from": "AGT-013",
            "can_approve": []
        },
        "AGT-011": {
            "name": "Revisor de Codigo",
            "role": "Revisor senior de codigo e seguranca",
            "capabilities": ["code review", "seguranca", "boas praticas", "OWASP"],
            "stage": DevelopmentStage.REVIEW,
            "requires_approval_from": None,
            "can_approve": ["AGT-007", "AGT-008", "AGT-009"]
        },
        "AGT-013": {
            "name": "Arquiteto",
            "role": "Arquiteto de software responsavel por decisoes tecnicas",
            "capabilities": ["arquitetura", "design patterns", "escalabilidade", "cloud"],
            "stage": DevelopmentStage.DESIGN,
            "requires_approval_from": "AGT-014",  # Tech Lead
            "can_approve": ["AGT-007", "AGT-008", "AGT-009", "AGT-015"]
        },
        "AGT-014": {
            "name": "Tech Lead",
            "role": "Lider tecnico com autoridade sobre decisoes de implementacao",
            "capabilities": ["lideranca tecnica", "decisoes arquiteturais", "mentoria"],
            "stage": DevelopmentStage.DESIGN,
            "requires_approval_from": None,
            "can_approve": ["AGT-013", "AGT-011"]
        },
        "AGT-015": {
            "name": "QA Engineer",
            "role": "Engenheiro de qualidade responsavel por testes",
            "capabilities": ["pytest", "testes unitarios", "integracao", "e2e"],
            "stage": DevelopmentStage.TESTING,
            "requires_approval_from": "AGT-013",
            "can_approve": []
        },
    }

    def __init__(self, max_parallel_projects: int = 3, max_workers: int = 5):
        # Skills
        self.intelligent_skills = get_intelligent_skills()
        self.template_skills = get_real_skills()

        # Claude client
        self.claude = get_claude_client()
        self.use_intelligence = self.claude.is_available()

        # Agent brains
        self.agent_brains: Dict[str, AgentBrain] = {}

        # Task management
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.active_projects: Dict[str, ProjectState] = {}
        self.pending_approvals: Dict[str, IntelligentTask] = {}

        # Config
        self.max_parallel_projects = max_parallel_projects
        self.max_workers = max_workers
        self._running = False
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._monitor_thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_file_created: Optional[Callable] = None
        self.on_decision_made: Optional[Callable] = None
        self.on_approval_needed: Optional[Callable] = None
        self.on_stage_complete: Optional[Callable] = None

        # Inicializa cerebros dos agentes
        self._init_agent_brains()

        print(f"[IntelligentDeveloper] Inicializado - Inteligencia: {'ATIVA' if self.use_intelligence else 'DESATIVADA (fallback para templates)'}")

    def _init_agent_brains(self):
        """Inicializa o cerebro de cada agente"""
        for agent_id, config in self.AGENT_CONFIG.items():
            self.agent_brains[agent_id] = create_agent_brain(
                agent_id=agent_id,
                agent_role=config["role"],
                capabilities=config["capabilities"]
            )
        print(f"[IntelligentDeveloper] {len(self.agent_brains)} cerebros de agentes inicializados")

    def start(self):
        """Inicia o desenvolvedor inteligente"""
        if self._running:
            return

        self._running = True
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        print(f"[IntelligentDeveloper] Iniciado com {self.max_workers} workers")

    def stop(self):
        """Para o desenvolvedor"""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=False)
        print("[IntelligentDeveloper] Parado")

    def develop_project(self, project_id: str) -> Dict:
        """
        Desenvolve um projeto de forma INTELIGENTE

        Fluxo:
        1. Arquiteto analisa requisitos e define arquitetura
        2. Para cada story, agentes colaboram para implementar
        3. Revisor valida codigo
        4. QA cria testes
        """
        db = SessionLocal()
        try:
            # Carrega projeto
            project = db.query(Project).filter(Project.project_id == project_id).first()
            if not project:
                return {"success": False, "error": "Projeto nao encontrado"}

            # Determina caminho
            config = project.config or {}
            project_path = config.get("output_path") or str(
                Path(__file__).parent.parent.parent / "projects" / project.name.lower().replace(" ", "-")
            )

            # Cria estrutura
            self._create_project_structure(project_path)

            # Registra projeto
            state = ProjectState(
                project_id=project_id,
                project_path=project_path,
                project_name=project.name
            )
            self.active_projects[project_id] = state

            # Carrega stories
            stories = db.query(Story).filter(
                Story.project_id == project_id,
                Story.status.in_(["TO_DO", "BACKLOG", "pending_review", "READY"])
            ).all()

            state.stories_total = len(stories)

            self._log_activity(db, project_id, "INTELLIGENT_DEV",
                              "intelligent_development_started",
                              f"Desenvolvimento inteligente iniciado para {project.name}")

            # Fase 1: Arquiteto define arquitetura
            self._schedule_architecture_definition(project, stories, project_path, db)

            # Fase 2: Desenvolvimento das stories
            self._schedule_intelligent_development(project, stories, project_path, db)

            return {
                "success": True,
                "project": project.name,
                "project_path": project_path,
                "stories_to_develop": len(stories),
                "intelligence_enabled": self.use_intelligence
            }

        finally:
            db.close()

    def _create_project_structure(self, project_path: str):
        """Cria estrutura de diretorios"""
        dirs = [
            "backend/routers", "backend/models", "backend/schemas",
            "backend/services", "backend/tests",
            "frontend/src/components", "frontend/src/views",
            "frontend/src/services", "frontend/public",
            "database", "docs"
        ]
        for d in dirs:
            Path(project_path, d).mkdir(parents=True, exist_ok=True)

    def _schedule_architecture_definition(self, project: Project, stories: List[Story],
                                         project_path: str, db):
        """Agenda definicao de arquitetura pelo Arquiteto"""
        # Coleta requisitos de todas as stories
        requirements_summary = "\n".join([
            f"- {s.title}: {s.description[:200] if s.description else 'Sem descricao'}"
            for s in stories[:10]  # Limita a 10 para nao exceder contexto
        ])

        self._queue_task(IntelligentTask(
            task_id=f"ARCH-{project.project_id}",
            project_id=project.project_id,
            story_id="ARCHITECTURE",
            agent_id="AGT-013",  # Arquiteto
            stage=DevelopmentStage.DESIGN,
            action="define_architecture",
            params={
                "project_path": project_path,
                "project_name": project.name,
                "requirements": requirements_summary,
                "stories_count": len(stories)
            },
            priority=0,  # Maior prioridade
            use_intelligence=True
        ))

    def _schedule_intelligent_development(self, project: Project, stories: List[Story],
                                         project_path: str, db):
        """Agenda desenvolvimento inteligente das stories"""

        # Setup do banco
        self._queue_task(IntelligentTask(
            task_id=f"SETUP-{project.project_id}",
            project_id=project.project_id,
            story_id="SETUP",
            agent_id="AGT-007",
            stage=DevelopmentStage.BACKEND,
            action="create_database_setup",
            params={"project_path": project_path},
            priority=1,
            use_intelligence=False  # Usa template para setup basico
        ))

        for i, story in enumerate(stories):
            resource_name = self._extract_resource_name(story)
            table_name = resource_name.lower().replace(" ", "_")
            fields = self._generate_fields_from_story(story)

            # Modelo - AGT-007
            self._queue_task(IntelligentTask(
                task_id=f"MODEL-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-007",
                stage=DevelopmentStage.BACKEND,
                action="create_model",
                params={
                    "project_path": project_path,
                    "name": resource_name,
                    "table_name": table_name,
                    "description": story.description or "",
                    "fields": fields
                },
                priority=3,
                use_intelligence=self.use_intelligence
            ))

            # Schemas Pydantic - AGT-008
            self._queue_task(IntelligentTask(
                task_id=f"SCHEMA-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-008",
                stage=DevelopmentStage.BACKEND,
                action="create_schemas",
                params={
                    "project_path": project_path,
                    "name": resource_name,
                    "fields": fields
                },
                priority=3,
                use_intelligence=self.use_intelligence
            ))

            # Router FastAPI - AGT-008
            self._queue_task(IntelligentTask(
                task_id=f"ROUTER-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-008",
                stage=DevelopmentStage.BACKEND,
                action="create_router",
                params={
                    "project_path": project_path,
                    "name": resource_name,
                    "model_name": table_name,
                    "description": story.description or "",
                    "fields": fields,
                    "business_rules": self._extract_business_rules(story)
                },
                priority=4,
                use_intelligence=self.use_intelligence
            ))

            # Componente Vue - AGT-009
            self._queue_task(IntelligentTask(
                task_id=f"VUE-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-009",
                stage=DevelopmentStage.FRONTEND,
                action="create_component",
                params={
                    "project_path": project_path,
                    "name": resource_name,
                    "description": story.description or "",
                    "api_endpoint": f"/api/{table_name}",
                    "fields": fields
                },
                priority=5,
                use_intelligence=self.use_intelligence
            ))

            # Testes - AGT-015
            self._queue_task(IntelligentTask(
                task_id=f"TEST-{story.story_id}",
                project_id=project.project_id,
                story_id=story.story_id,
                agent_id="AGT-015",
                stage=DevelopmentStage.TESTING,
                action="create_tests",
                params={
                    "project_path": project_path,
                    "name": resource_name,
                    "api_endpoint": f"/api/{table_name}"
                },
                priority=6,
                use_intelligence=self.use_intelligence
            ))

        # Main app - AGT-008
        routers = [self._extract_resource_name(s).lower().replace(" ", "_") for s in stories]
        self._queue_task(IntelligentTask(
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
            priority=10,
            use_intelligence=False  # Template para main.py
        ))

    def _queue_task(self, task: IntelligentTask):
        """Adiciona tarefa na fila"""
        self.task_queue.put(task)

    def _monitor_loop(self):
        """Loop de monitoramento"""
        while self._running:
            try:
                try:
                    task = self.task_queue.get(timeout=2)
                except queue.Empty:
                    continue

                if self._executor:
                    self._executor.submit(self._execute_intelligent_task, task)

            except Exception as e:
                print(f"[IntelligentDeveloper] Erro no monitor: {e}")

            time.sleep(0.5)

    def _execute_intelligent_task(self, task: IntelligentTask):
        """Executa tarefa de forma inteligente"""
        db = SessionLocal()
        try:
            agent_config = self.AGENT_CONFIG.get(task.agent_id, {})
            agent_name = agent_config.get("name", task.agent_id)
            brain = self.agent_brains.get(task.agent_id)

            print(f"[{agent_name}] Executando {task.action} para {task.story_id}")

            # Atualiza estado
            if task.project_id in self.active_projects:
                state = self.active_projects[task.project_id]
                state.active_agents[task.agent_id] = task.task_id

            # Agente pensa sobre a tarefa (se inteligencia ativa)
            reasoning = None
            if task.use_intelligence and brain and brain.claude.is_available():
                thinking = brain.think(
                    f"Vou executar: {task.action}. Params: {json.dumps(task.params, ensure_ascii=False)[:500]}",
                    {"stage": task.stage.value, "story": task.story_id}
                )
                if thinking.success:
                    reasoning = thinking.content
                    task.reasoning = reasoning
                    print(f"[{agent_name}] Pensamento: {reasoning[:200]}...")

            # Executa skill
            result = self._run_intelligent_skill(task, db)

            # Registra atividade
            self._log_activity(
                db, task.project_id, task.agent_id,
                f"intelligent_{task.action}",
                f"{'[INTELIGENTE] ' if task.use_intelligence else '[TEMPLATE] '}"
                f"{task.action}: {len(result.files_created)} arquivos"
                if result.success else f"Erro: {result.errors}",
                task.story_id
            )

            # Atualiza estado do projeto
            if task.project_id in self.active_projects:
                state = self.active_projects[task.project_id]
                state.files_created.extend(result.files_created)
                if result.errors:
                    state.errors.extend(result.errors)
                if hasattr(result, 'reasoning') and result.reasoning:
                    state.decisions_made.append({
                        "agent": task.agent_id,
                        "action": task.action,
                        "reasoning": result.reasoning,
                        "timestamp": datetime.utcnow().isoformat()
                    })

            # Agente aprende
            if brain:
                brain.learn({
                    "success": result.success,
                    "action": task.action,
                    "files_created": len(result.files_created),
                    "errors": result.errors
                })

            # Callback
            if result.success and result.files_created and self.on_file_created:
                for f in result.files_created:
                    self.on_file_created(task.project_id, task.agent_id, f)

        except Exception as e:
            print(f"[{task.agent_id}] Erro: {e}")
            import traceback
            traceback.print_exc()
            self._log_activity(
                db, task.project_id, task.agent_id,
                "error", f"Erro: {str(e)}", task.story_id
            )
        finally:
            # Remove da lista de ativos
            if task.project_id in self.active_projects:
                state = self.active_projects[task.project_id]
                if task.agent_id in state.active_agents:
                    del state.active_agents[task.agent_id]
            db.close()

    def _run_intelligent_skill(self, task: IntelligentTask, db) -> SkillResult:
        """Executa skill de forma inteligente ou com template"""
        action = task.action
        params = task.params
        agent_id = task.agent_id
        use_ai = task.use_intelligence and self.use_intelligence

        # Decide qual implementacao usar
        if action == "define_architecture":
            if use_ai:
                return self.intelligent_skills.decide_architecture_intelligent(
                    agent_id, params.get("requirements", ""),
                    [f"Projeto: {params.get('project_name')}", f"Stories: {params.get('stories_count')}"]
                )
            else:
                return SkillResult(success=True, skill_name=action, agent_id=agent_id,
                                  outputs={"architecture": "default"})

        elif action == "create_database_setup":
            return self.template_skills.create_database_setup(
                agent_id, params["project_path"]
            )

        elif action == "create_model":
            if use_ai:
                return self.intelligent_skills.generate_sqlalchemy_model_intelligent(
                    agent_id, params["project_path"], params["name"],
                    params.get("description", ""), params["fields"]
                )
            else:
                return self.template_skills.create_sqlalchemy_model(
                    agent_id, params["project_path"], params["name"],
                    params["table_name"], params["fields"], params.get("description", "")
                )

        elif action == "create_schemas":
            if use_ai:
                return self.intelligent_skills.generate_pydantic_schemas_intelligent(
                    agent_id, params["project_path"], params["name"], params["fields"]
                )
            else:
                # Fallback: usa template de schemas
                return self._create_schemas_template(agent_id, params)

        elif action == "create_router":
            if use_ai:
                return self.intelligent_skills.generate_fastapi_router_intelligent(
                    agent_id, params["project_path"], params["name"],
                    params.get("description", ""), params["fields"],
                    params.get("business_rules")
                )
            else:
                return self.template_skills.create_fastapi_router(
                    agent_id, params["project_path"], params["name"],
                    params["model_name"], params["fields"]
                )

        elif action == "create_component":
            if use_ai:
                return self.intelligent_skills.generate_vue_component_intelligent(
                    agent_id, params["project_path"], params["name"],
                    params.get("description", ""), params["fields"], params["api_endpoint"]
                )
            else:
                return self.template_skills.create_vue_component(
                    agent_id, params["project_path"], params["name"],
                    params["api_endpoint"], params["fields"]
                )

        elif action == "create_tests":
            if use_ai:
                return self.intelligent_skills.generate_tests_intelligent(
                    agent_id, params["project_path"], params["name"],
                    params["api_endpoint"]
                )
            else:
                return self.template_skills.create_test_file(
                    agent_id, params["project_path"], params["name"],
                    params["api_endpoint"].replace("/api/", "")
                )

        elif action == "create_main_app":
            return self.template_skills.create_main_app(
                agent_id, params["project_path"], params["app_name"], params["routers"]
            )

        else:
            return SkillResult(
                success=False,
                skill_name=action,
                agent_id=agent_id,
                errors=[f"Acao {action} nao implementada"]
            )

    def _create_schemas_template(self, agent_id: str, params: Dict) -> SkillResult:
        """Cria schemas Pydantic com template"""
        name = params["name"]
        file_name = name.lower().replace(" ", "_")
        fields = params.get("fields", [])

        # Gera campos do schema
        field_lines = []
        for f in fields:
            fname = f.get("name", "field")
            ftype = f.get("type", "str")
            nullable = f.get("nullable", True)

            py_type = {
                "str": "str", "text": "str", "int": "int",
                "float": "float", "bool": "bool", "datetime": "datetime"
            }.get(ftype, "str")

            if nullable:
                field_lines.append(f"    {fname}: Optional[{py_type}] = None")
            else:
                field_lines.append(f"    {fname}: {py_type}")

        fields_str = "\n".join(field_lines) if field_lines else "    pass"

        code = f'''"""
Schemas Pydantic para {name}
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class {name}Base(BaseModel):
{fields_str}


class {name}Create({name}Base):
    pass


class {name}Update(BaseModel):
{fields_str.replace(": str", ": Optional[str] = None").replace(": int", ": Optional[int] = None")}


class {name}Response({name}Base):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
'''

        file_path = Path(params["project_path"]) / "backend" / "schemas" / f"{file_name}.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")

        result = SkillResult(
            success=True,
            skill_name="create_schemas",
            agent_id=agent_id,
            files_created=[str(file_path)]
        )

        # Registra na memoria
        memory = self.intelligent_skills.get_memory(agent_id)
        memory.record_skill_execution(result)

        return result

    def _extract_resource_name(self, story: Story) -> str:
        """Extrai nome do recurso"""
        title = story.title or ""
        prefixes = ["Cadastro de", "Gestao de", "Visualizacao de", "Edicao de",
                   "Lista de", "Criacao de", "Mapeamento", "API de"]
        for prefix in prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()
                break
        suffixes = ["- Mapeamento AS-IS", "AS-IS", "TO-BE", "com", "por"]
        for suffix in suffixes:
            if suffix in title:
                title = title.split(suffix)[0].strip()
        return title.strip() or "Resource"

    def _generate_fields_from_story(self, story: Story) -> List[Dict]:
        """Gera campos baseado na story"""
        fields = [
            {"name": "name", "type": "str", "nullable": False},
            {"name": "description", "type": "text", "nullable": True},
        ]

        criteria = story.acceptance_criteria
        if criteria:
            if isinstance(criteria, str):
                try:
                    criteria = json.loads(criteria)
                except:
                    criteria = [criteria]

            criteria_text = " ".join(criteria).lower() if isinstance(criteria, list) else str(criteria).lower()

            if "status" in criteria_text:
                fields.append({"name": "status", "type": "str", "default": "ACTIVE"})
            if any(w in criteria_text for w in ["valor", "preco", "custo"]):
                fields.append({"name": "value", "type": "float", "nullable": True})
            if any(w in criteria_text for w in ["data", "prazo"]):
                fields.append({"name": "due_date", "type": "datetime", "nullable": True})
            if any(w in criteria_text for w in ["responsavel", "usuario"]):
                fields.append({"name": "owner", "type": "str", "nullable": True})
            if any(w in criteria_text for w in ["categoria", "tipo"]):
                fields.append({"name": "category", "type": "str", "nullable": True})

        return fields

    def _extract_business_rules(self, story: Story) -> List[str]:
        """Extrai regras de negocio da story"""
        rules = []
        criteria = story.acceptance_criteria
        if criteria:
            if isinstance(criteria, str):
                try:
                    criteria = json.loads(criteria)
                except:
                    criteria = [criteria]
            if isinstance(criteria, list):
                rules = criteria[:5]  # Limita a 5 regras
        return rules

    def get_project_status(self, project_id: str) -> Dict:
        """Retorna status do projeto"""
        if project_id not in self.active_projects:
            return {"status": "not_found"}

        state = self.active_projects[project_id]
        return {
            "project_id": project_id,
            "project_name": state.project_name,
            "project_path": state.project_path,
            "stories_total": state.stories_total,
            "stories_completed": state.stories_completed,
            "current_stage": state.current_stage.value,
            "active_agents": state.active_agents,
            "files_created": len(state.files_created),
            "decisions_made": len(state.decisions_made),
            "errors": state.errors,
            "tasks_pending": self.task_queue.qsize(),
            "intelligence_enabled": self.use_intelligence
        }

    def get_agent_status(self, agent_id: str) -> Dict:
        """Retorna status de um agente"""
        brain = self.agent_brains.get(agent_id)
        config = self.AGENT_CONFIG.get(agent_id, {})

        return {
            "agent_id": agent_id,
            "name": config.get("name", agent_id),
            "role": config.get("role", ""),
            "capabilities": config.get("capabilities", []),
            "stage": config.get("stage", DevelopmentStage.BACKEND).value,
            "brain_available": brain is not None and brain.claude.is_available(),
            "memory_size": len(brain.memory) if brain else 0,
            "decisions_count": len(brain.decision_history) if brain else 0
        }

    def _log_activity(self, db, project_id: str, agent_id: str,
                      event_type: str, message: str, story_id: str = None):
        """Registra atividade"""
        log = ActivityLog(
            source="intelligent_developer",
            source_id="INTELLIGENT_DEV",
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
_intelligent_developer: Optional[IntelligentDeveloper] = None


def get_intelligent_developer() -> IntelligentDeveloper:
    """Retorna instancia global"""
    global _intelligent_developer
    if _intelligent_developer is None:
        _intelligent_developer = IntelligentDeveloper()
    return _intelligent_developer


def start_intelligent_developer() -> IntelligentDeveloper:
    """Inicia o desenvolvedor inteligente"""
    developer = get_intelligent_developer()
    developer.start()
    return developer


def stop_intelligent_developer():
    """Para o desenvolvedor inteligente"""
    global _intelligent_developer
    if _intelligent_developer:
        _intelligent_developer.stop()
        _intelligent_developer = None
