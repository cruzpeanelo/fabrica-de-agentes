"""
Runtime de Execucao de Agentes
==============================

Gerencia ciclo de vida de multiplos agentes:
- Inicializacao e shutdown
- Distribuicao de tarefas
- Monitoramento de estado
- Comunicacao entre agentes
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import threading

from .autonomous_agent import AutonomousAgent, AgentState, TaskContext, TaskResult
from factory.agents.knowledge.knowledge_base import KnowledgeBase


@dataclass
class AgentConfig:
    """Configuracao de um agente"""
    agent_id: str
    name: str
    domain: str
    description: str
    priority: int = 5
    max_concurrent_tasks: int = 1


class AgentRuntime:
    """
    Runtime para Execucao de Agentes

    Gerencia multiplos agentes de forma coordenada.
    """

    def __init__(self,
                 max_workers: int = 4,
                 shared_knowledge: Optional[KnowledgeBase] = None):
        """
        Args:
            max_workers: Numero maximo de workers para execucao paralela
            shared_knowledge: Base de conhecimento compartilhada
        """
        self.max_workers = max_workers
        self.shared_knowledge = shared_knowledge or KnowledgeBase()

        self._agents: Dict[str, AutonomousAgent] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = False
        self._lock = threading.Lock()

        # Callbacks
        self._on_agent_state_change: List[Callable] = []
        self._on_task_complete: List[Callable] = []

    def register_agent(self, config: AgentConfig) -> AutonomousAgent:
        """
        Registra um novo agente

        Args:
            config: Configuracao do agente

        Returns:
            Agente criado
        """
        agent = AutonomousAgent(
            agent_id=config.agent_id,
            name=config.name,
            domain=config.domain,
            description=config.description,
            knowledge_base=self.shared_knowledge
        )

        # Registra callbacks
        agent.on_state_change(self._handle_agent_state_change)
        agent.on_task_complete(self._handle_task_complete)

        with self._lock:
            self._agents[config.agent_id] = agent

        return agent

    def get_agent(self, agent_id: str) -> Optional[AutonomousAgent]:
        """Busca agente por ID"""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[Dict]:
        """Lista todos os agentes"""
        return [agent.get_status() for agent in self._agents.values()]

    def _handle_agent_state_change(self, agent_id: str, old_state: AgentState, new_state: AgentState):
        """Handler para mudanca de estado"""
        for callback in self._on_agent_state_change:
            try:
                callback(agent_id, old_state, new_state)
            except Exception:
                pass

    def _handle_task_complete(self, agent_id: str, task: TaskContext, result: TaskResult):
        """Handler para conclusao de tarefa"""
        for callback in self._on_task_complete:
            try:
                callback(agent_id, task, result)
            except Exception:
                pass

    def on_agent_state_change(self, callback: Callable):
        """Registra callback para mudanca de estado"""
        self._on_agent_state_change.append(callback)

    def on_task_complete(self, callback: Callable):
        """Registra callback para conclusao de tarefa"""
        self._on_task_complete.append(callback)

    async def submit_task(self,
                         agent_id: str,
                         task: TaskContext) -> TaskResult:
        """
        Submete tarefa para um agente

        Args:
            agent_id: ID do agente
            task: Tarefa a executar

        Returns:
            Resultado da tarefa
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                output=None,
                errors=[f"Agente {agent_id} nao encontrado"]
            )

        # Executa em thread separada
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            agent.execute_task,
            task
        )

        return result

    def submit_task_sync(self, agent_id: str, task: TaskContext) -> TaskResult:
        """Versao sincrona de submit_task"""
        agent = self.get_agent(agent_id)
        if not agent:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                output=None,
                errors=[f"Agente {agent_id} nao encontrado"]
            )

        return agent.execute_task(task)

    def select_agent(self, task_description: str, domain: Optional[str] = None) -> Optional[str]:
        """
        Seleciona melhor agente para uma tarefa

        Args:
            task_description: Descricao da tarefa
            domain: Dominio preferido (opcional)

        Returns:
            ID do agente selecionado ou None
        """
        candidates = []

        for agent_id, agent in self._agents.items():
            # Filtra por dominio se especificado
            if domain and agent.domain != domain:
                continue

            # Verifica se esta disponivel
            if agent.state not in [AgentState.READY, AgentState.IDLE]:
                continue

            # Calcula score baseado em:
            # - Performance historica
            # - Skills relevantes
            # - Conhecimento do dominio
            score = 0.0

            # Performance
            perf = agent.feedback.get_agent_performance(agent_id)
            score += perf.get("avg_score", 0.5) * 0.4

            # Skills
            skills = agent.skills.get_all_skills()
            skill_relevance = sum(
                s.proficiency for s in skills
                if any(kw in task_description.lower() for kw in s.name.lower().split())
            )
            score += min(skill_relevance, 1.0) * 0.3

            # Conhecimento
            knowledge_results = agent.retriever.retrieve(task_description, limit=5)
            if knowledge_results:
                avg_similarity = sum(r.similarity for r in knowledge_results) / len(knowledge_results)
                score += avg_similarity * 0.3

            candidates.append((agent_id, score))

        if not candidates:
            return None

        # Retorna agente com maior score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def broadcast_knowledge(self, topic: str, source_agent_id: str):
        """
        Compartilha conhecimento de um agente com todos os outros

        Args:
            topic: Topico a compartilhar
            source_agent_id: Agente origem
        """
        source = self.get_agent(source_agent_id)
        if not source:
            return

        for agent_id, agent in self._agents.items():
            if agent_id != source_agent_id:
                source.share_knowledge(agent, topic)

    def get_collective_wisdom(self) -> Dict:
        """
        Coleta sabedoria de todos os agentes

        Returns:
            Dict com sabedoria coletiva
        """
        wisdom = {
            "o_que_funciona": [],
            "o_que_evitar": [],
            "licoes": []
        }

        for agent in self._agents.values():
            agent_wisdom = agent.get_wisdom()
            wisdom["o_que_funciona"].extend(agent_wisdom.get("o_que_funciona", []))
            wisdom["o_que_evitar"].extend(agent_wisdom.get("o_que_evitar", []))
            wisdom["licoes"].extend(agent_wisdom.get("licoes_importantes", []))

        # Remove duplicatas
        for key in wisdom:
            wisdom[key] = list(set(wisdom[key]))[:20]

        return wisdom

    def get_runtime_stats(self) -> Dict:
        """Retorna estatisticas do runtime"""
        agent_states = {}
        for agent in self._agents.values():
            state = agent.state.value
            agent_states[state] = agent_states.get(state, 0) + 1

        return {
            "total_agents": len(self._agents),
            "agents_by_state": agent_states,
            "max_workers": self.max_workers,
            "running": self._running
        }

    def start(self):
        """Inicia o runtime"""
        self._running = True

    def stop(self):
        """Para o runtime"""
        self._running = False
        self._executor.shutdown(wait=True)


# Funcao helper para criar runtime com agentes padrao
def create_default_runtime() -> AgentRuntime:
    """
    Cria runtime com agentes padrao da fabrica

    Returns:
        AgentRuntime configurado
    """
    runtime = AgentRuntime(max_workers=4)

    # Agentes padrao
    agents_config = [
        AgentConfig("01", "Gestao Estrategica", "management", "Coordena decisoes estrategicas"),
        AgentConfig("02", "Product Manager", "management", "Define roadmap e prioridades"),
        AgentConfig("03", "Product Owner", "management", "Gerencia backlog e requisitos"),
        AgentConfig("08", "Backend Developer", "backend", "Desenvolve APIs e logica de negocio"),
        AgentConfig("09", "Frontend Developer", "frontend", "Desenvolve interfaces de usuario"),
        AgentConfig("07", "Database Specialist", "database", "Modela e otimiza banco de dados"),
        AgentConfig("12", "DevOps Engineer", "devops", "Gerencia infraestrutura e CI/CD"),
        AgentConfig("15", "QA Tester", "testing", "Garante qualidade com testes"),
    ]

    for config in agents_config:
        runtime.register_agent(config)

    return runtime
