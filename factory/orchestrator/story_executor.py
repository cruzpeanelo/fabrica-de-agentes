"""
Story Executor - Sistema de Execucao Automatica de Stories
Monitora mudancas de status e aciona agentes automaticamente

Quando uma story vai para TO_DO:
1. Atribui agentes adequados baseado no tipo/tags
2. Move para IN_PROGRESS
3. Inicia execucao autonoma
4. Gera artefatos (codigo, testes, docs)
5. Move para TESTING quando pronto
6. Move para DONE apos aprovacao
"""

import threading
import time
import queue
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from factory.database.connection import SessionLocal
from factory.database.models import Story, Project, Agent, ActivityLog


class StoryStatus(Enum):
    BACKLOG = "BACKLOG"
    TO_DO = "TO_DO"
    IN_PROGRESS = "IN_PROGRESS"
    TESTING = "TESTING"
    BLOCKED = "BLOCKED"
    DONE = "DONE"


@dataclass
class ExecutionTask:
    """Tarefa de execucao para uma story"""
    story_id: str
    project_id: str
    action: str  # start, continue, review, complete
    assigned_agents: List[str]
    priority: int
    created_at: datetime


class StoryExecutor:
    """
    Executor automatico de stories
    Monitora mudancas de status e aciona agentes
    """

    # Mapeamento de categorias para agentes
    AGENT_MAPPING = {
        "backend": ["AGT-008", "AGT-007", "AGT-006"],  # Backend, BD, Dados
        "frontend": ["AGT-009", "AGT-018"],  # Frontend, UX
        "api": ["AGT-008", "AGT-013"],  # Backend, Arquiteto
        "database": ["AGT-007", "AGT-006"],  # BD, Dados
        "security": ["AGT-010"],  # Seguranca
        "testing": ["AGT-015", "AGT-016"],  # QA, E2E
        "docs": ["AGT-017"],  # Documentador
        "infra": ["AGT-012"],  # DevOps
        "integration": ["AGT-019"],  # Integrador
        "analysis": ["AGT-005"],  # Analista
        "architecture": ["AGT-013", "AGT-014"],  # Arquiteto, Tech Lead
        "default": ["AGT-014", "AGT-008"]  # Tech Lead, Backend
    }

    # Definition of Done padrao
    DEFAULT_DOD = [
        "Codigo implementado e funcionando",
        "Testes unitarios criados e passando",
        "Codigo revisado por outro agente",
        "Documentacao atualizada",
        "Sem erros de linting/build"
    ]

    def __init__(self):
        self.execution_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._running = False
        self._workers: List[threading.Thread] = []
        self._status_callbacks: List[Callable] = []
        self._last_check: Dict[str, str] = {}  # story_id -> last_status

    def start(self, num_workers: int = 2):
        """Inicia o executor com N workers"""
        if self._running:
            return

        self._running = True

        # Worker de monitoramento de status
        monitor = threading.Thread(target=self._status_monitor, daemon=True)
        monitor.start()
        self._workers.append(monitor)

        # Workers de execucao
        for i in range(num_workers):
            worker = threading.Thread(target=self._execution_worker, daemon=True, name=f"executor-{i}")
            worker.start()
            self._workers.append(worker)

        print(f"[StoryExecutor] Iniciado com {num_workers} workers")

    def stop(self):
        """Para o executor"""
        self._running = False
        for _ in self._workers:
            self.execution_queue.put((0, None))  # Sinal de parada
        self._workers.clear()
        print("[StoryExecutor] Parado")

    def _status_monitor(self):
        """Monitora mudancas de status nas stories"""
        while self._running:
            try:
                db = SessionLocal()
                try:
                    # Busca todas as stories em TO_DO que nao tem agente atribuido
                    stories = db.query(Story).filter(
                        Story.status == StoryStatus.TO_DO.value,
                        Story.assigned_to == None
                    ).all()

                    for story in stories:
                        # Verifica se ja processamos esta story
                        last_status = self._last_check.get(story.story_id)
                        if last_status != story.status:
                            self._on_status_change(story, last_status, story.status, db)
                            self._last_check[story.story_id] = story.status

                finally:
                    db.close()

            except Exception as e:
                print(f"[StoryExecutor] Erro no monitor: {e}")

            time.sleep(5)  # Verifica a cada 5 segundos

    def _on_status_change(self, story: Story, old_status: Optional[str], new_status: str, db):
        """Callback quando status de uma story muda"""
        print(f"[StoryExecutor] Story {story.story_id} mudou de {old_status} para {new_status}")

        if new_status == StoryStatus.TO_DO.value:
            self._start_story_execution(story, db)

    def _start_story_execution(self, story: Story, db):
        """Inicia execucao automatica de uma story"""
        print(f"[StoryExecutor] Iniciando execucao de {story.story_id}: {story.title}")

        # 1. Atribui agentes baseado na categoria/tags
        agents = self._select_agents(story)

        # 2. Atualiza a story
        story.assigned_to = agents[0] if agents else "AGT-014"
        story.agents = agents
        story.status = StoryStatus.IN_PROGRESS.value
        story.started_at = datetime.utcnow()

        # 3. Preenche DoD se vazio
        if not story.definition_of_done:
            story.definition_of_done = self.DEFAULT_DOD.copy()

        # 4. Gera criterios de aceite se vazio
        if not story.acceptance_criteria:
            story.acceptance_criteria = self._generate_acceptance_criteria(story)

        db.commit()

        # 5. Registra log
        self._log_activity(
            db=db,
            story_id=story.story_id,
            project_id=story.project_id,
            agent_id=story.assigned_to,
            action="story_started",
            message=f"Execucao iniciada por {story.assigned_to}. Agentes: {', '.join(agents)}"
        )

        # 6. Adiciona a fila de execucao
        task = ExecutionTask(
            story_id=story.story_id,
            project_id=story.project_id,
            action="start",
            assigned_agents=agents,
            priority=story.priority,
            created_at=datetime.utcnow()
        )
        self.execution_queue.put((story.priority, task))

        print(f"[StoryExecutor] Story {story.story_id} em execucao com agentes: {agents}")

    def _select_agents(self, story: Story) -> List[str]:
        """Seleciona agentes adequados para a story"""
        agents = []

        # Baseado na categoria
        category = story.category or "default"
        if category in self.AGENT_MAPPING:
            agents.extend(self.AGENT_MAPPING[category])
        else:
            agents.extend(self.AGENT_MAPPING["default"])

        # Baseado nas tags
        for tag in (story.tags or []):
            tag_lower = tag.lower()
            for key, agent_list in self.AGENT_MAPPING.items():
                if key in tag_lower:
                    for agent in agent_list:
                        if agent not in agents:
                            agents.append(agent)

        # Adiciona QA e revisor
        if "AGT-015" not in agents:
            agents.append("AGT-015")  # QA
        if "AGT-011" not in agents:
            agents.append("AGT-011")  # Code Reviewer

        return agents[:5]  # Maximo 5 agentes

    def _generate_acceptance_criteria(self, story: Story) -> List[str]:
        """Gera criterios de aceite baseados na story"""
        criteria = []

        # Criterios basicos
        criteria.append(f"Funcionalidade '{story.title}' implementada conforme descricao")

        if story.narrative_action:
            criteria.append(f"Usuario consegue {story.narrative_action}")

        if story.narrative_benefit:
            criteria.append(f"Beneficio alcancado: {story.narrative_benefit}")

        # Criterios por categoria
        category = story.category or ""
        if "backend" in category.lower() or "api" in category.lower():
            criteria.extend([
                "API endpoints funcionando corretamente",
                "Validacoes de entrada implementadas",
                "Erros tratados adequadamente"
            ])
        elif "frontend" in category.lower():
            criteria.extend([
                "Interface responsiva",
                "Feedback visual para acoes do usuario",
                "Acessibilidade basica implementada"
            ])
        elif "database" in category.lower():
            criteria.extend([
                "Migrations criadas",
                "Indices otimizados",
                "Dados consistentes"
            ])

        return criteria

    def _execution_worker(self):
        """Worker que processa tarefas de execucao"""
        while self._running:
            try:
                priority, task = self.execution_queue.get(timeout=5)
                if task is None:  # Sinal de parada
                    break

                self._execute_task(task)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[StoryExecutor] Erro no worker: {e}")

    def _execute_task(self, task: ExecutionTask):
        """Executa uma tarefa de story"""
        db = SessionLocal()
        try:
            story = db.query(Story).filter(Story.story_id == task.story_id).first()
            if not story:
                return

            print(f"[StoryExecutor] Executando tarefa {task.action} para {task.story_id}")

            if task.action == "start":
                # Simula execucao inicial
                self._simulate_development(story, db)

            elif task.action == "review":
                self._simulate_review(story, db)

            elif task.action == "complete":
                self._complete_story(story, db)

        except Exception as e:
            print(f"[StoryExecutor] Erro executando tarefa: {e}")
        finally:
            db.close()

    def _simulate_development(self, story: Story, db):
        """Simula desenvolvimento da story"""
        # Registra inicio
        self._log_activity(
            db=db,
            story_id=story.story_id,
            project_id=story.project_id,
            agent_id=story.assigned_to,
            action="development_started",
            message=f"Desenvolvimento iniciado para: {story.title}"
        )

        # Adiciona artefatos simulados
        artifacts = story.artifacts or []
        artifacts.append({
            "type": "code",
            "name": f"{story.story_id.lower().replace('-', '_')}_implementation.py",
            "created_at": datetime.utcnow().isoformat(),
            "agent": story.assigned_to
        })
        story.artifacts = artifacts
        story.actual_hours = story.estimated_hours * 0.5  # Metade das horas estimadas

        db.commit()

        # Agenda revisao
        review_task = ExecutionTask(
            story_id=story.story_id,
            project_id=story.project_id,
            action="review",
            assigned_agents=[story.reviewer or "AGT-011"],
            priority=story.priority,
            created_at=datetime.utcnow()
        )
        self.execution_queue.put((story.priority + 1, review_task))

    def _simulate_review(self, story: Story, db):
        """Simula revisao da story"""
        story.status = StoryStatus.TESTING.value
        story.tested_at = datetime.utcnow()

        self._log_activity(
            db=db,
            story_id=story.story_id,
            project_id=story.project_id,
            agent_id=story.reviewer or "AGT-011",
            action="review_completed",
            message="Revisao concluida, enviado para testes"
        )

        db.commit()

    def _complete_story(self, story: Story, db):
        """Completa uma story"""
        story.status = StoryStatus.DONE.value
        story.completed_at = datetime.utcnow()
        story.actual_hours = story.estimated_hours

        self._log_activity(
            db=db,
            story_id=story.story_id,
            project_id=story.project_id,
            agent_id=story.assigned_to,
            action="story_completed",
            message=f"Story {story.story_id} concluida com sucesso!"
        )

        db.commit()
        print(f"[StoryExecutor] Story {story.story_id} CONCLUIDA!")

    def _log_activity(self, db, story_id: str, project_id: str, agent_id: str,
                      action: str, message: str):
        """Registra atividade no log"""
        log = ActivityLog(
            source="story_executor",
            source_id="EXECUTOR",
            agent_id=agent_id,
            project_id=project_id,
            story_id=story_id,
            event_type=action,
            message=message,
            level="INFO"
        )
        db.add(log)
        db.commit()

    def trigger_story(self, story_id: str):
        """Dispara execucao manual de uma story"""
        db = SessionLocal()
        try:
            story = db.query(Story).filter(Story.story_id == story_id).first()
            if story and story.status in [StoryStatus.TO_DO.value, StoryStatus.BACKLOG.value]:
                story.status = StoryStatus.TO_DO.value
                db.commit()
                self._start_story_execution(story, db)
                return True
        finally:
            db.close()
        return False


# Instancia global
_executor: Optional[StoryExecutor] = None


def get_executor() -> StoryExecutor:
    """Retorna instancia global do executor"""
    global _executor
    if _executor is None:
        _executor = StoryExecutor()
    return _executor


def start_executor():
    """Inicia o executor global"""
    executor = get_executor()
    executor.start()
    return executor


def stop_executor():
    """Para o executor global"""
    global _executor
    if _executor:
        _executor.stop()
        _executor = None


if __name__ == "__main__":
    # Teste
    executor = start_executor()
    print("Executor rodando... Pressione Ctrl+C para parar")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_executor()
