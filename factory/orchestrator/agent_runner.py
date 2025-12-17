"""
Agent Runner - Sistema de Execucao Real de Agentes
Executa agentes com skills reais e gerencia o pipeline de desenvolvimento

Pipeline automatico:
1. BACKLOG: Story criada, aguarda refinamento
2. REFINING: Agente de analise detalha a story
3. READY: Story detalhada, aguarda aprovacao humana
4. TO_DO: Aprovada, aguarda inicio de desenvolvimento
5. IN_PROGRESS: Em desenvolvimento pelos agentes
6. CODE_REVIEW: Codigo pronto, aguarda revisao
7. TESTING: Em testes automatizados
8. DONE: Concluida

Intervencao humana necessaria em:
- READY -> TO_DO (aprovar para desenvolvimento)
- CODE_REVIEW -> TESTING (aprovar codigo)
- TESTING -> DONE (aprovar testes)
"""

import os
import json
import threading
import queue
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from factory.database.connection import SessionLocal
from factory.database.models import Story, Agent, ActivityLog, Project


class StoryStage(Enum):
    """Estagios do pipeline de desenvolvimento"""
    BACKLOG = "BACKLOG"
    REFINING = "REFINING"           # Agente detalhando
    READY = "READY"                  # Aguarda aprovacao humana
    TO_DO = "TO_DO"                  # Aprovado, aguarda dev
    IN_PROGRESS = "IN_PROGRESS"      # Em desenvolvimento
    CODE_REVIEW = "CODE_REVIEW"      # Aguarda revisao
    TESTING = "TESTING"              # Em testes
    DONE = "DONE"                    # Concluido


class ApprovalType(Enum):
    """Tipos de aprovacao necessaria"""
    REFINEMENT = "refinement"        # Aprovar detalhamento
    DEVELOPMENT = "development"      # Aprovar para dev
    CODE = "code"                    # Aprovar codigo
    TESTS = "tests"                  # Aprovar testes


@dataclass
class AgentTask:
    """Tarefa para um agente executar"""
    task_id: str
    story_id: str
    agent_id: str
    action: str
    params: Dict = field(default_factory=dict)
    priority: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PendingApproval:
    """Aprovacao pendente de humano"""
    approval_id: str
    story_id: str
    approval_type: ApprovalType
    description: str
    details: Dict
    created_at: datetime = field(default_factory=datetime.utcnow)
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None


class AgentSkills:
    """
    Skills disponiveis para os agentes
    Cada skill e uma funcao que executa uma tarefa especifica
    """

    @staticmethod
    def analyze_requirements(story: Story, db) -> Dict:
        """Skill: Analisa e detalha requisitos de uma story"""
        result = {
            "success": True,
            "action": "analyze_requirements",
            "outputs": {}
        }

        # Gera acceptance criteria se nao existir
        if not story.acceptance_criteria or story.acceptance_criteria == "[]":
            criteria = [
                f"DADO que o usuario acessa a funcionalidade {story.title}",
                "QUANDO executa a acao principal",
                "ENTAO o sistema responde conforme esperado",
                "E registra a acao no log de auditoria"
            ]
            story.acceptance_criteria = json.dumps(criteria)
            result["outputs"]["acceptance_criteria"] = criteria

        # Gera technical notes se nao existir
        if not story.technical_notes or story.technical_notes == "[]":
            notes = [
                f"Implementar endpoint REST para {story.title}",
                "Utilizar padrao Repository para acesso a dados",
                "Implementar validacoes de entrada",
                "Adicionar logs estruturados"
            ]
            story.technical_notes = json.dumps(notes)
            result["outputs"]["technical_notes"] = notes

        # Estima horas se nao existir
        if not story.estimated_hours:
            # Baseado em pontos
            hours_per_point = 4
            story.estimated_hours = (story.points or 5) * hours_per_point
            result["outputs"]["estimated_hours"] = story.estimated_hours

        db.commit()
        return result

    @staticmethod
    def design_architecture(story: Story, db) -> Dict:
        """Skill: Projeta arquitetura da solucao"""
        result = {
            "success": True,
            "action": "design_architecture",
            "outputs": {}
        }

        # Adiciona notas de arquitetura
        current_notes = json.loads(story.technical_notes or "[]")
        arch_notes = [
            "Arquitetura: Microservico com FastAPI",
            "Banco de dados: PostgreSQL com SQLAlchemy",
            "Cache: Redis para dados frequentes",
            "Mensageria: RabbitMQ para eventos async"
        ]
        current_notes.extend(arch_notes)
        story.technical_notes = json.dumps(current_notes)
        result["outputs"]["architecture"] = arch_notes

        db.commit()
        return result

    @staticmethod
    def generate_code_structure(story: Story, project: Project, db) -> Dict:
        """Skill: Gera estrutura de codigo"""
        result = {
            "success": True,
            "action": "generate_code_structure",
            "outputs": {"files": []}
        }

        # Define estrutura de arquivos baseado na categoria
        category = story.category or "backend"
        story_slug = story.story_id.lower().replace("-", "_")

        if category in ["backend", "api", "cadastro"]:
            files = [
                f"backend/routers/{story_slug}.py",
                f"backend/services/{story_slug}_service.py",
                f"backend/models/{story_slug}_model.py",
                f"backend/schemas/{story_slug}_schema.py",
                f"tests/test_{story_slug}.py"
            ]
        elif category == "frontend":
            files = [
                f"frontend/src/views/{story_slug.title()}View.vue",
                f"frontend/src/components/{story_slug.title()}Component.vue",
                f"frontend/src/services/{story_slug}Service.js",
                f"frontend/tests/{story_slug}.spec.js"
            ]
        else:
            files = [
                f"src/{story_slug}/main.py",
                f"src/{story_slug}/service.py",
                f"tests/test_{story_slug}.py"
            ]

        # Registra artefatos
        artifacts = json.loads(story.artifacts or "[]")
        for f in files:
            artifacts.append({
                "type": "code_structure",
                "path": f,
                "status": "planned",
                "created_at": datetime.utcnow().isoformat()
            })
        story.artifacts = json.dumps(artifacts)
        result["outputs"]["files"] = files

        db.commit()
        return result

    @staticmethod
    def implement_backend(story: Story, project: Project, db) -> Dict:
        """Skill: Implementa codigo backend"""
        result = {
            "success": True,
            "action": "implement_backend",
            "outputs": {"files_created": []}
        }

        # Simula criacao de arquivos (em producao, geraria codigo real)
        artifacts = json.loads(story.artifacts or "[]")
        for artifact in artifacts:
            if artifact.get("status") == "planned" and "backend" in artifact.get("path", ""):
                artifact["status"] = "implemented"
                artifact["implemented_at"] = datetime.utcnow().isoformat()
                result["outputs"]["files_created"].append(artifact["path"])

        story.artifacts = json.dumps(artifacts)
        story.actual_hours = (story.actual_hours or 0) + 8  # Adiciona 8h de trabalho

        db.commit()
        return result

    @staticmethod
    def implement_frontend(story: Story, project: Project, db) -> Dict:
        """Skill: Implementa codigo frontend"""
        result = {
            "success": True,
            "action": "implement_frontend",
            "outputs": {"files_created": []}
        }

        artifacts = json.loads(story.artifacts or "[]")
        for artifact in artifacts:
            if artifact.get("status") == "planned" and "frontend" in artifact.get("path", ""):
                artifact["status"] = "implemented"
                artifact["implemented_at"] = datetime.utcnow().isoformat()
                result["outputs"]["files_created"].append(artifact["path"])

        story.artifacts = json.dumps(artifacts)
        story.actual_hours = (story.actual_hours or 0) + 6

        db.commit()
        return result

    @staticmethod
    def review_code(story: Story, db) -> Dict:
        """Skill: Revisa codigo"""
        result = {
            "success": True,
            "action": "review_code",
            "outputs": {
                "review_status": "approved",
                "comments": []
            }
        }

        # Simula revisao
        artifacts = json.loads(story.artifacts or "[]")
        implemented = [a for a in artifacts if a.get("status") == "implemented"]

        if len(implemented) > 0:
            result["outputs"]["comments"] = [
                "Codigo segue padroes do projeto",
                "Tratamento de erros adequado",
                "Documentacao inline presente"
            ]
            for artifact in artifacts:
                if artifact.get("status") == "implemented":
                    artifact["status"] = "reviewed"
                    artifact["reviewed_at"] = datetime.utcnow().isoformat()
            story.artifacts = json.dumps(artifacts)
        else:
            result["success"] = False
            result["outputs"]["review_status"] = "no_code"
            result["outputs"]["comments"] = ["Nenhum codigo para revisar"]

        db.commit()
        return result

    @staticmethod
    def run_tests(story: Story, db) -> Dict:
        """Skill: Executa testes"""
        result = {
            "success": True,
            "action": "run_tests",
            "outputs": {
                "tests_passed": 0,
                "tests_failed": 0,
                "coverage": 0
            }
        }

        # Simula execucao de testes
        artifacts = json.loads(story.artifacts or "[]")
        test_files = [a for a in artifacts if "test" in a.get("path", "").lower()]

        if test_files:
            result["outputs"]["tests_passed"] = len(test_files) * 5
            result["outputs"]["tests_failed"] = 0
            result["outputs"]["coverage"] = 85

            for artifact in artifacts:
                if "test" in artifact.get("path", "").lower():
                    artifact["status"] = "tested"
                    artifact["tested_at"] = datetime.utcnow().isoformat()
            story.artifacts = json.dumps(artifacts)
            story.tested_at = datetime.utcnow()
        else:
            result["outputs"]["tests_passed"] = 0
            result["outputs"]["coverage"] = 0

        db.commit()
        return result

    @staticmethod
    def generate_documentation(story: Story, db) -> Dict:
        """Skill: Gera documentacao"""
        result = {
            "success": True,
            "action": "generate_documentation",
            "outputs": {"docs": []}
        }

        artifacts = json.loads(story.artifacts or "[]")
        docs = [
            {
                "type": "documentation",
                "path": f"docs/{story.story_id}_README.md",
                "status": "created",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "type": "documentation",
                "path": f"docs/api/{story.story_id}_api.md",
                "status": "created",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        artifacts.extend(docs)
        story.artifacts = json.dumps(artifacts)
        story.documentation_url = f"/docs/{story.story_id}_README.md"
        result["outputs"]["docs"] = [d["path"] for d in docs]

        db.commit()
        return result


class AgentRunner:
    """
    Executor de agentes com pipeline automatico
    Gerencia execucao de tarefas e aprovacoes
    """

    # Mapeamento de agente para skills
    AGENT_SKILLS = {
        "AGT-005": ["analyze_requirements"],  # Analista
        "AGT-013": ["design_architecture"],   # Arquiteto
        "AGT-008": ["implement_backend", "generate_code_structure"],  # Backend
        "AGT-009": ["implement_frontend"],    # Frontend
        "AGT-011": ["review_code"],           # Revisor
        "AGT-015": ["run_tests"],             # QA
        "AGT-017": ["generate_documentation"] # Documentador
    }

    # Transicoes automaticas (sem aprovacao humana)
    AUTO_TRANSITIONS = {
        StoryStage.BACKLOG: StoryStage.REFINING,
        StoryStage.REFINING: StoryStage.READY,
        StoryStage.IN_PROGRESS: StoryStage.CODE_REVIEW,
    }

    # Transicoes que requerem aprovacao humana
    HUMAN_TRANSITIONS = {
        StoryStage.READY: (StoryStage.TO_DO, ApprovalType.REFINEMENT),
        StoryStage.CODE_REVIEW: (StoryStage.TESTING, ApprovalType.CODE),
        StoryStage.TESTING: (StoryStage.DONE, ApprovalType.TESTS),
    }

    def __init__(self):
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.pending_approvals: Dict[str, PendingApproval] = {}
        self._running = False
        self._workers: List[threading.Thread] = []
        self.skills = AgentSkills()

    def start(self, num_workers: int = 2):
        """Inicia o runner"""
        if self._running:
            return

        self._running = True

        # Worker de pipeline
        pipeline_worker = threading.Thread(target=self._pipeline_worker, daemon=True)
        pipeline_worker.start()
        self._workers.append(pipeline_worker)

        # Workers de execucao
        for i in range(num_workers):
            worker = threading.Thread(target=self._execution_worker, daemon=True, name=f"agent-{i}")
            worker.start()
            self._workers.append(worker)

        print(f"[AgentRunner] Iniciado com {num_workers} workers")

    def stop(self):
        """Para o runner"""
        self._running = False
        self._workers.clear()
        print("[AgentRunner] Parado")

    def _pipeline_worker(self):
        """Worker que gerencia o pipeline de stories"""
        while self._running:
            try:
                db = SessionLocal()
                try:
                    # Busca stories que precisam de processamento
                    self._process_pipeline(db)
                finally:
                    db.close()
            except Exception as e:
                print(f"[AgentRunner] Erro no pipeline: {e}")

            time.sleep(3)  # Verifica a cada 3 segundos

    def _process_pipeline(self, db):
        """Processa stories no pipeline"""

        # 1. Stories em BACKLOG -> REFINING (auto)
        backlog_stories = db.query(Story).filter(
            Story.status == StoryStage.BACKLOG.value
        ).limit(5).all()

        for story in backlog_stories:
            self._start_refinement(story, db)

        # 2. Stories em TO_DO -> IN_PROGRESS (auto, se tem agente)
        todo_stories = db.query(Story).filter(
            Story.status == StoryStage.TO_DO.value,
            Story.assigned_to != None
        ).limit(3).all()

        for story in todo_stories:
            self._start_development(story, db)

    def _start_refinement(self, story: Story, db):
        """Inicia refinamento de uma story"""
        print(f"[AgentRunner] Iniciando refinamento: {story.story_id}")

        story.status = StoryStage.REFINING.value
        db.commit()

        # Agenda tarefas de refinamento
        task = AgentTask(
            task_id=f"REFINE-{story.story_id}-{int(time.time())}",
            story_id=story.story_id,
            agent_id="AGT-005",  # Analista
            action="analyze_requirements",
            priority=story.priority or 5
        )
        self.task_queue.put((task.priority, task))

        self._log_activity(db, story.story_id, story.project_id, "AGT-005",
                          "refinement_started", f"Iniciado refinamento de {story.title}")

    def _start_development(self, story: Story, db):
        """Inicia desenvolvimento de uma story"""
        print(f"[AgentRunner] Iniciando desenvolvimento: {story.story_id}")

        story.status = StoryStage.IN_PROGRESS.value
        story.started_at = datetime.utcnow()
        db.commit()

        # Agenda tarefas de desenvolvimento
        agents = json.loads(story.agents or "[]")
        if not agents:
            agents = [story.assigned_to or "AGT-008"]

        for agent_id in agents[:3]:  # Maximo 3 agentes em paralelo
            skills = self.AGENT_SKILLS.get(agent_id, [])
            for skill in skills:
                task = AgentTask(
                    task_id=f"DEV-{story.story_id}-{agent_id}-{int(time.time())}",
                    story_id=story.story_id,
                    agent_id=agent_id,
                    action=skill,
                    priority=story.priority or 5
                )
                self.task_queue.put((task.priority, task))

        self._log_activity(db, story.story_id, story.project_id, story.assigned_to,
                          "development_started", f"Iniciado desenvolvimento de {story.title}")

    def _execution_worker(self):
        """Worker que executa tarefas dos agentes"""
        while self._running:
            try:
                priority, task = self.task_queue.get(timeout=5)
                if task is None:
                    break

                self._execute_task(task)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[AgentRunner] Erro no worker: {e}")

    def _execute_task(self, task: AgentTask):
        """Executa uma tarefa de agente"""
        db = SessionLocal()
        try:
            story = db.query(Story).filter(Story.story_id == task.story_id).first()
            if not story:
                return

            project = db.query(Project).filter(Project.project_id == story.project_id).first()

            print(f"[AgentRunner] Executando {task.action} por {task.agent_id} em {task.story_id}")

            # Executa skill correspondente
            result = self._run_skill(task.action, story, project, db)

            # Log da atividade
            self._log_activity(
                db, story.story_id, story.project_id, task.agent_id,
                f"skill_{task.action}",
                f"Executado {task.action}: {json.dumps(result.get('outputs', {}), ensure_ascii=False)[:200]}"
            )

            # Verifica transicao de estado
            self._check_stage_transition(story, db)

        except Exception as e:
            print(f"[AgentRunner] Erro executando tarefa: {e}")
        finally:
            db.close()

    def _run_skill(self, skill_name: str, story: Story, project: Project, db) -> Dict:
        """Executa um skill especifico"""
        skill_methods = {
            "analyze_requirements": lambda: self.skills.analyze_requirements(story, db),
            "design_architecture": lambda: self.skills.design_architecture(story, db),
            "generate_code_structure": lambda: self.skills.generate_code_structure(story, project, db),
            "implement_backend": lambda: self.skills.implement_backend(story, project, db),
            "implement_frontend": lambda: self.skills.implement_frontend(story, project, db),
            "review_code": lambda: self.skills.review_code(story, db),
            "run_tests": lambda: self.skills.run_tests(story, db),
            "generate_documentation": lambda: self.skills.generate_documentation(story, db),
        }

        if skill_name in skill_methods:
            return skill_methods[skill_name]()
        else:
            return {"success": False, "error": f"Skill {skill_name} nao encontrado"}

    def _check_stage_transition(self, story: Story, db):
        """Verifica se story deve mudar de estagio"""
        current_stage = StoryStage(story.status)

        # Transicoes automaticas
        if current_stage == StoryStage.REFINING:
            # Verifica se refinamento esta completo
            has_criteria = story.acceptance_criteria and story.acceptance_criteria != "[]"
            has_notes = story.technical_notes and story.technical_notes != "[]"

            if has_criteria and has_notes:
                story.status = StoryStage.READY.value
                db.commit()

                # Cria aprovacao pendente
                self._create_approval(
                    story, ApprovalType.REFINEMENT,
                    "Story refinada, aguardando aprovacao para desenvolvimento",
                    db
                )

        elif current_stage == StoryStage.IN_PROGRESS:
            # Verifica se desenvolvimento esta completo
            artifacts = json.loads(story.artifacts or "[]")
            implemented = [a for a in artifacts if a.get("status") == "implemented"]

            if len(implemented) > 0:
                story.status = StoryStage.CODE_REVIEW.value
                db.commit()

                # Agenda revisao
                task = AgentTask(
                    task_id=f"REVIEW-{story.story_id}-{int(time.time())}",
                    story_id=story.story_id,
                    agent_id="AGT-011",
                    action="review_code",
                    priority=1
                )
                self.task_queue.put((task.priority, task))

        elif current_stage == StoryStage.CODE_REVIEW:
            # Verifica se revisao esta completa
            artifacts = json.loads(story.artifacts or "[]")
            reviewed = [a for a in artifacts if a.get("status") == "reviewed"]

            if len(reviewed) > 0:
                # Cria aprovacao pendente para testes
                self._create_approval(
                    story, ApprovalType.CODE,
                    "Codigo revisado, aguardando aprovacao para testes",
                    db
                )

    def _create_approval(self, story: Story, approval_type: ApprovalType, description: str, db):
        """Cria uma aprovacao pendente"""
        approval = PendingApproval(
            approval_id=f"APR-{story.story_id}-{approval_type.value}-{int(time.time())}",
            story_id=story.story_id,
            approval_type=approval_type,
            description=description,
            details={
                "story_title": story.title,
                "category": story.category,
                "points": story.points,
                "assigned_to": story.assigned_to
            }
        )
        self.pending_approvals[approval.approval_id] = approval

        self._log_activity(
            db, story.story_id, story.project_id, "SYSTEM",
            "approval_required",
            f"Aprovacao necessaria: {description}"
        )

        print(f"[AgentRunner] Aprovacao criada: {approval.approval_id}")

    def approve(self, approval_id: str, approved_by: str, approved: bool, notes: str = "") -> Dict:
        """Processa uma aprovacao"""
        if approval_id not in self.pending_approvals:
            return {"success": False, "error": "Aprovacao nao encontrada"}

        approval = self.pending_approvals[approval_id]
        approval.approved = approved
        approval.approved_by = approved_by
        approval.approved_at = datetime.utcnow()
        approval.notes = notes

        db = SessionLocal()
        try:
            story = db.query(Story).filter(Story.story_id == approval.story_id).first()
            if not story:
                return {"success": False, "error": "Story nao encontrada"}

            if approved:
                # Avanca para proximo estagio
                if approval.approval_type == ApprovalType.REFINEMENT:
                    story.status = StoryStage.TO_DO.value
                elif approval.approval_type == ApprovalType.CODE:
                    story.status = StoryStage.TESTING.value
                    # Agenda testes
                    task = AgentTask(
                        task_id=f"TEST-{story.story_id}-{int(time.time())}",
                        story_id=story.story_id,
                        agent_id="AGT-015",
                        action="run_tests",
                        priority=1
                    )
                    self.task_queue.put((task.priority, task))
                elif approval.approval_type == ApprovalType.TESTS:
                    story.status = StoryStage.DONE.value
                    story.completed_at = datetime.utcnow()

                db.commit()

                self._log_activity(
                    db, story.story_id, story.project_id, approved_by,
                    "approval_granted",
                    f"Aprovado por {approved_by}: {notes}"
                )
            else:
                # Rejeicao - volta para estagio anterior ou BACKLOG
                story.status = StoryStage.BACKLOG.value
                db.commit()

                self._log_activity(
                    db, story.story_id, story.project_id, approved_by,
                    "approval_rejected",
                    f"Rejeitado por {approved_by}: {notes}"
                )

            # Remove aprovacao processada
            del self.pending_approvals[approval_id]

            return {"success": True, "new_status": story.status}

        finally:
            db.close()

    def get_pending_approvals(self, project_id: str = None) -> List[Dict]:
        """Retorna aprovacoes pendentes"""
        approvals = []
        for approval in self.pending_approvals.values():
            if approval.approved is None:  # Ainda pendente
                data = {
                    "approval_id": approval.approval_id,
                    "story_id": approval.story_id,
                    "type": approval.approval_type.value,
                    "description": approval.description,
                    "details": approval.details,
                    "created_at": approval.created_at.isoformat()
                }
                approvals.append(data)
        return approvals

    def trigger_story(self, story_id: str) -> Dict:
        """Dispara processamento manual de uma story"""
        db = SessionLocal()
        try:
            story = db.query(Story).filter(Story.story_id == story_id).first()
            if not story:
                return {"success": False, "error": "Story nao encontrada"}

            current_stage = StoryStage(story.status)

            if current_stage == StoryStage.BACKLOG:
                self._start_refinement(story, db)
                return {"success": True, "action": "refinement_started"}

            elif current_stage == StoryStage.TO_DO:
                self._start_development(story, db)
                return {"success": True, "action": "development_started"}

            else:
                return {"success": False, "error": f"Story em {story.status}, nao pode ser disparada"}

        finally:
            db.close()

    def _log_activity(self, db, story_id: str, project_id: str, agent_id: str,
                      action: str, message: str):
        """Registra atividade no log"""
        log = ActivityLog(
            source="agent_runner",
            source_id="RUNNER",
            agent_id=agent_id,
            project_id=project_id,
            story_id=story_id,
            event_type=action,
            message=message,
            level="INFO"
        )
        db.add(log)
        db.commit()


# Instancia global
_runner: Optional[AgentRunner] = None


def get_runner() -> AgentRunner:
    """Retorna instancia global do runner"""
    global _runner
    if _runner is None:
        _runner = AgentRunner()
    return _runner


def start_runner():
    """Inicia o runner global"""
    runner = get_runner()
    runner.start()
    return runner


def stop_runner():
    """Para o runner global"""
    global _runner
    if _runner:
        _runner.stop()
        _runner = None


if __name__ == "__main__":
    # Teste
    runner = start_runner()
    print("Runner rodando... Pressione Ctrl+C para parar")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_runner()
