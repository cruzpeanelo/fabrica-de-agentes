"""
Agente Autonomo - Core do Sistema
=================================

Agente verdadeiramente autonomo que:
1. Possui conhecimento profundo do seu dominio
2. Aprende com experiencias passadas
3. Toma decisoes independentes
4. Compartilha conhecimento com outros agentes
5. Evolui continuamente

Ciclo de Vida:
1. INITIALIZING: Carrega conhecimento e memoria
2. READY: Pronto para receber tarefas
3. THINKING: Analisando tarefa e planejando
4. EXECUTING: Executando acoes
5. LEARNING: Processando resultados e aprendendo
6. IDLE: Aguardando proxima tarefa
"""

import json
import subprocess
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import sys

# Adiciona path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from factory.agents.knowledge.knowledge_base import KnowledgeBase, KnowledgeType
from factory.agents.knowledge.retriever import KnowledgeRetriever, RetrievalContext
from factory.agents.memory.agent_memory import AgentMemory, MemoryType
from factory.agents.memory.working_memory import WorkingMemory
from factory.agents.memory.episodic_memory import EpisodicMemory
from factory.agents.learning.feedback_system import FeedbackSystem, FeedbackType, FeedbackResult
from factory.agents.learning.learning_engine import LearningEngine
from factory.agents.learning.skill_acquisition import SkillAcquisition


class AgentState(str, Enum):
    """Estados do agente"""
    INITIALIZING = "initializing"
    READY = "ready"
    THINKING = "thinking"
    EXECUTING = "executing"
    LEARNING = "learning"
    IDLE = "idle"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class AgentCapability:
    """Capacidade do agente"""
    name: str
    description: str
    required_skills: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class TaskContext:
    """Contexto de uma tarefa"""
    task_id: str
    description: str
    project_id: Optional[str] = None
    priority: int = 5
    deadline: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Resultado de uma tarefa"""
    task_id: str
    success: bool
    output: Any
    files_modified: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    actions_taken: List[str] = field(default_factory=list)


class AutonomousAgent:
    """
    Agente Autonomo com Capacidade de Aprendizado

    Um agente que:
    - Conhece profundamente seu dominio
    - Aprende com cada tarefa executada
    - Toma decisoes baseadas em experiencias
    - Melhora continuamente sua performance
    """

    def __init__(self,
                 agent_id: str,
                 name: str,
                 domain: str,
                 description: str,
                 capabilities: Optional[List[AgentCapability]] = None,
                 knowledge_base: Optional[KnowledgeBase] = None):
        """
        Inicializa agente autonomo

        Args:
            agent_id: ID unico do agente
            name: Nome do agente
            domain: Dominio de atuacao (backend, frontend, etc)
            description: Descricao do papel do agente
            capabilities: Lista de capacidades
            knowledge_base: Base de conhecimento compartilhada
        """
        self.agent_id = agent_id
        self.name = name
        self.domain = domain
        self.description = description
        self.capabilities = capabilities or []

        # Estado
        self._state = AgentState.INITIALIZING
        self._current_task: Optional[TaskContext] = None
        self._session_id: Optional[str] = None

        # Sistemas cognitivos
        self.knowledge = knowledge_base or KnowledgeBase()
        self.retriever = KnowledgeRetriever(self.knowledge)
        self.memory = AgentMemory(agent_id)
        self.working_memory = WorkingMemory()
        self.episodes = EpisodicMemory(agent_id)
        self.feedback = FeedbackSystem()
        self.learning = LearningEngine(
            agent_id,
            memory=self.memory,
            episodes=self.episodes,
            feedback=self.feedback
        )
        self.skills = SkillAcquisition(agent_id)

        # Callbacks
        self._on_state_change: List[Callable] = []
        self._on_task_complete: List[Callable] = []

        # Inicializa
        self._initialize()

    def _initialize(self):
        """Inicializa agente"""
        # Carrega conhecimento do dominio
        self._load_domain_knowledge()

        # Inicializa skills basicas
        self._init_base_skills()

        # Muda estado para pronto
        self._set_state(AgentState.READY)

    def _load_domain_knowledge(self):
        """Carrega conhecimento especifico do dominio"""
        # Adiciona conhecimento base do dominio
        domain_knowledge = {
            "backend": [
                "APIs REST seguem principios de recursos e verbos HTTP",
                "Validacao de entrada eh critica para seguranca",
                "Logs estruturados facilitam debugging",
                "Testes unitarios devem cobrir casos de borda"
            ],
            "frontend": [
                "Componentes devem ser reutilizaveis e desacoplados",
                "Performance percebida eh tao importante quanto real",
                "Acessibilidade nao eh opcional",
                "Estado deve ser gerenciado de forma previsivel"
            ],
            "database": [
                "Indices aceleram queries mas custam em escrita",
                "Normalizacao vs desnormalizacao depende do caso",
                "Transacoes garantem consistencia",
                "Backup e recovery sao criticos"
            ],
            "devops": [
                "Infraestrutura como codigo permite reproducibilidade",
                "CI/CD acelera entregas com qualidade",
                "Monitoring proativo previne incidentes",
                "Seguranca deve ser incorporada desde o inicio"
            ]
        }

        if self.domain in domain_knowledge:
            for knowledge in domain_knowledge[self.domain]:
                self.knowledge.add(
                    content=knowledge,
                    knowledge_type=KnowledgeType.DOMAIN,
                    source=f"domain_init_{self.domain}",
                    agent_id=self.agent_id,
                    tags=[self.domain, "fundamental"]
                )

    def _init_base_skills(self):
        """Inicializa skills basicas do dominio"""
        base_skills = {
            "backend": [
                ("Python", "Programacao em Python", "technical"),
                ("FastAPI", "Desenvolvimento de APIs com FastAPI", "technical"),
                ("SQL", "Queries e modelagem SQL", "technical"),
                ("REST Design", "Design de APIs RESTful", "technical"),
            ],
            "frontend": [
                ("JavaScript", "Programacao em JavaScript/TypeScript", "technical"),
                ("React", "Desenvolvimento com React", "technical"),
                ("CSS", "Estilizacao e layouts", "technical"),
                ("UI/UX", "Principios de design de interface", "domain"),
            ],
            "database": [
                ("SQL", "Queries e otimizacao SQL", "technical"),
                ("Data Modeling", "Modelagem de dados", "technical"),
                ("Performance Tuning", "Otimizacao de banco", "technical"),
            ]
        }

        if self.domain in base_skills:
            for name, desc, category in base_skills[self.domain]:
                self.skills.acquire_skill(
                    name=name,
                    description=desc,
                    category=category,
                    initial_proficiency=0.5  # Comeca com nivel intermediario
                )

    def _set_state(self, new_state: AgentState):
        """Muda estado do agente"""
        old_state = self._state
        self._state = new_state

        # Notifica listeners
        for callback in self._on_state_change:
            try:
                callback(self.agent_id, old_state, new_state)
            except Exception:
                pass

    @property
    def state(self) -> AgentState:
        """Estado atual do agente"""
        return self._state

    def on_state_change(self, callback: Callable):
        """Registra callback para mudanca de estado"""
        self._on_state_change.append(callback)

    def on_task_complete(self, callback: Callable):
        """Registra callback para conclusao de tarefa"""
        self._on_task_complete.append(callback)

    # ==================== EXECUCAO DE TAREFAS ====================

    def execute_task(self, task: TaskContext) -> TaskResult:
        """
        Executa uma tarefa de forma autonoma

        Args:
            task: Contexto da tarefa

        Returns:
            TaskResult com resultado
        """
        import time
        start_time = time.time()

        self._current_task = task
        self._set_state(AgentState.THINKING)

        # Inicia sessao de trabalho
        self._session_id = self.memory.start_session(
            project_id=task.project_id,
            task_id=task.task_id
        )

        # Configura memoria de trabalho
        self.working_memory.set_task(
            task.task_id,
            task.description,
            task.project_id
        )

        try:
            # 1. PENSAR: Analisa tarefa e busca conhecimento relevante
            context = self._think(task)

            # 2. PLANEJAR: Decide como executar
            plan = self._plan(task, context)

            # 3. EXECUTAR: Realiza acoes
            self._set_state(AgentState.EXECUTING)
            result = self._execute(task, plan)

            # 4. APRENDER: Processa resultado
            self._set_state(AgentState.LEARNING)
            self._learn(task, result)

            result.duration_seconds = time.time() - start_time

            # Notifica conclusao
            for callback in self._on_task_complete:
                try:
                    callback(self.agent_id, task, result)
                except Exception:
                    pass

            return result

        except Exception as e:
            self._set_state(AgentState.ERROR)

            result = TaskResult(
                task_id=task.task_id,
                success=False,
                output=None,
                errors=[str(e)],
                duration_seconds=time.time() - start_time
            )

            # Aprende com o erro
            self._learn_from_error(task, e)

            return result

        finally:
            # Finaliza sessao
            if self._session_id:
                self.memory.end_session(
                    session_id=self._session_id,
                    actions=self.working_memory.context.modified_files,
                    files=self.working_memory.context.modified_files,
                    errors=self.working_memory.context.errors_encountered,
                    lessons=self.working_memory.context.notes,
                    success=self._state != AgentState.ERROR
                )

            self._set_state(AgentState.IDLE)
            self._current_task = None

    def _think(self, task: TaskContext) -> Dict:
        """
        Fase de pensamento: analisa tarefa e busca conhecimento

        Returns:
            Dict com contexto para planejamento
        """
        context = {
            "task": task,
            "relevant_knowledge": [],
            "similar_experiences": [],
            "applicable_patterns": [],
            "recommendations": []
        }

        # Busca conhecimento relevante
        retrieval_ctx = RetrievalContext(
            agent_id=self.agent_id,
            project_id=task.project_id
        )

        knowledge_results = self.retriever.retrieve_for_task(
            task.description,
            self.agent_id,
            task.project_id
        )

        for category, results in knowledge_results.items():
            for result in results:
                context["relevant_knowledge"].append({
                    "category": category,
                    "content": result.item.content[:200],
                    "similarity": result.similarity
                })

        # Busca experiencias similares
        similar_episodes = self.episodes.recall_similar(task.description, limit=5)
        for ep in similar_episodes:
            context["similar_experiences"].append({
                "title": ep.title,
                "outcome": ep.outcome,
                "lessons": ep.lessons
            })

        # Busca padroes aplicaveis
        patterns = self.memory.get_applicable_patterns(task.description)
        for pattern in patterns:
            context["applicable_patterns"].append({
                "action": pattern.action,
                "confidence": pattern.confidence
            })

        # Gera recomendacoes
        recommendation = self.learning.get_recommendation(task.description)
        if recommendation:
            context["recommendations"].append(recommendation)

        # Registra na memoria de trabalho
        self.working_memory.note(f"Analisados {len(context['relevant_knowledge'])} conhecimentos relevantes")
        self.working_memory.note(f"Encontradas {len(context['similar_experiences'])} experiencias similares")

        return context

    def _plan(self, task: TaskContext, context: Dict) -> List[str]:
        """
        Fase de planejamento: decide acoes a tomar

        Returns:
            Lista de acoes planejadas
        """
        actions = []

        # Usa padroes de sucesso se disponiveis
        for pattern in context.get("applicable_patterns", []):
            if pattern["confidence"] >= 0.6:
                actions.append(pattern["action"])
                self.working_memory.note(f"Usando padrao: {pattern['action'][:50]}")

        # Usa recomendacoes
        for rec in context.get("recommendations", []):
            if rec not in actions:
                actions.append(rec)

        # Acoes default baseadas no tipo de tarefa
        if not actions:
            if "criar" in task.description.lower() or "implementar" in task.description.lower():
                actions = [
                    "Analisar requisitos",
                    "Criar estrutura de arquivos",
                    "Implementar funcionalidade",
                    "Adicionar testes",
                    "Documentar"
                ]
            elif "corrigir" in task.description.lower() or "fix" in task.description.lower():
                actions = [
                    "Identificar causa raiz",
                    "Desenvolver solucao",
                    "Testar correcao",
                    "Verificar regressao"
                ]
            else:
                actions = ["Analisar", "Implementar", "Verificar"]

        # Registra decisao
        self.memory.record_decision(
            context=task.description[:200],
            options=["Seguir padroes conhecidos", "Abordagem padrao"],
            decision="; ".join(actions[:3]),
            reasoning="Baseado em experiencias anteriores e conhecimento do dominio",
            task_id=task.task_id
        )

        return actions

    def _execute(self, task: TaskContext, plan: List[str]) -> TaskResult:
        """
        Fase de execucao: realiza as acoes planejadas

        Esta eh a fase onde o agente interage com o ambiente.
        A implementacao depende do tipo de tarefa.
        """
        actions_taken = []
        files_modified = []
        errors = []
        output = {}

        for action in plan:
            self.working_memory.add_pending_action(action)

            try:
                # Simula execucao da acao
                # Em producao, isso seria a chamada real ao Claude CLI ou outra ferramenta
                result = self._execute_action(action, task)

                if result.get("files"):
                    files_modified.extend(result["files"])
                    for f in result["files"]:
                        self.working_memory.record_file_change(f)

                actions_taken.append(action)
                self.working_memory.complete_action(action)

                # Pratica skill relacionada
                self._practice_related_skill(action, success=True)

            except Exception as e:
                errors.append(f"Erro em '{action}': {str(e)}")
                self.working_memory.record_error(str(e))
                self._practice_related_skill(action, success=False)

        success = len(errors) == 0

        return TaskResult(
            task_id=task.task_id,
            success=success,
            output=output,
            files_modified=files_modified,
            errors=errors,
            actions_taken=actions_taken
        )

    def _execute_action(self, action: str, task: TaskContext) -> Dict:
        """
        Executa uma acao especifica

        Em producao, isso chamaria o Claude CLI ou outra ferramenta.
        Por ora, retorna resultado simulado.
        """
        # Placeholder - em producao seria a execucao real
        return {
            "status": "completed",
            "files": []
        }

    def _practice_related_skill(self, action: str, success: bool):
        """Pratica skill relacionada a acao"""
        action_lower = action.lower()

        # Mapeia acoes para skills
        skill_map = {
            "api": "FastAPI",
            "endpoint": "REST Design",
            "query": "SQL",
            "component": "React",
            "style": "CSS",
            "test": "Testing"
        }

        for keyword, skill in skill_map.items():
            if keyword in action_lower:
                if self.skills.get_skill(skill):
                    self.skills.practice_skill(skill, success=success)
                break

    def _learn(self, task: TaskContext, result: TaskResult):
        """
        Fase de aprendizado: processa resultado e atualiza conhecimento
        """
        # Registra feedback automatico
        feedback = self.feedback.auto_evaluate(
            task_id=task.task_id,
            agent_id=self.agent_id,
            task_result={
                "success": result.success,
                "files_modified": result.files_modified,
                "errors": result.errors,
                "actions": result.actions_taken
            },
            context={"domain": self.domain}
        )

        # Aprende com a tarefa
        insights = self.learning.learn_from_task(
            task_id=task.task_id,
            task_description=task.description,
            actions_taken=result.actions_taken,
            result={"success": result.success, "errors": result.errors},
            success=result.success
        )

        # Atualiza resultado da decisao
        decisions = self.memory.get_similar_decisions(task.description, limit=1)
        if decisions:
            self.memory.record_decision_outcome(
                decisions[0].id,
                outcome="success" if result.success else "failure",
                success_rating=1.0 if result.success else 0.3
            )

        # Se bem sucedido, adiciona a base de conhecimento
        if result.success and result.actions_taken:
            self.knowledge.add(
                content=f"Tarefa: {task.description[:100]}. Solucao: {'; '.join(result.actions_taken[:3])}",
                knowledge_type=KnowledgeType.PATTERN,
                source=f"task_{task.task_id}",
                agent_id=self.agent_id,
                project_id=task.project_id,
                metadata={"success": True, "actions": result.actions_taken}
            )

    def _learn_from_error(self, task: TaskContext, error: Exception):
        """Aprende com erro"""
        # Registra erro na memoria
        self.memory.remember(
            content=f"Erro em tarefa '{task.description[:50]}': {str(error)}",
            memory_type=MemoryType.EPISODIC,
            context={"task_id": task.task_id, "error_type": type(error).__name__},
            importance=0.7,
            emotional_valence=-0.5
        )

        # Adiciona a base de conhecimento
        self.knowledge.add(
            content=f"Erro: {str(error)}. Contexto: {task.description[:100]}",
            knowledge_type=KnowledgeType.ERROR,
            source=f"error_{task.task_id}",
            agent_id=self.agent_id,
            tags=["error", type(error).__name__]
        )

    # ==================== CONSULTAS ====================

    def get_status(self) -> Dict:
        """Retorna status atual do agente"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "domain": self.domain,
            "state": self._state.value,
            "current_task": self._current_task.task_id if self._current_task else None,
            "skills": self.skills.get_skill_summary(),
            "performance": self.feedback.get_agent_performance(self.agent_id),
            "memory_stats": self.memory.get_stats()
        }

    def get_capabilities(self) -> List[Dict]:
        """Lista capacidades do agente"""
        return [
            {
                "name": cap.name,
                "description": cap.description,
                "enabled": cap.enabled,
                "required_skills": cap.required_skills
            }
            for cap in self.capabilities
        ]

    def get_learning_summary(self) -> Dict:
        """Retorna resumo do aprendizado"""
        return self.learning.get_learning_summary()

    def get_wisdom(self) -> Dict:
        """Retorna sabedoria acumulada"""
        return self.episodes.generate_wisdom()

    # ==================== INTERACAO COM OUTROS AGENTES ====================

    def share_knowledge(self, target_agent: 'AutonomousAgent', topic: str):
        """
        Compartilha conhecimento com outro agente

        Args:
            target_agent: Agente que recebera conhecimento
            topic: Topico a compartilhar
        """
        # Busca conhecimento relevante
        results = self.knowledge.search(
            query=topic,
            agent_id=self.agent_id,
            limit=5
        )

        for result in results:
            # Adiciona ao conhecimento do outro agente
            target_agent.knowledge.add(
                content=result.item.content,
                knowledge_type=result.item.knowledge_type,
                source=f"shared_from_{self.agent_id}",
                agent_id=target_agent.agent_id,
                tags=result.item.tags + ["shared"]
            )

    def teach_skill(self, target_agent: 'AutonomousAgent', skill_name: str) -> bool:
        """
        Ensina skill para outro agente

        Args:
            target_agent: Agente aluno
            skill_name: Nome da skill

        Returns:
            True se ensinou com sucesso
        """
        result = self.skills.teach_skill(skill_name, target_agent.agent_id)
        return result is not None

    def consult(self, question: str) -> Optional[str]:
        """
        Consulta o agente sobre um assunto

        Args:
            question: Pergunta

        Returns:
            Resposta baseada em conhecimento e experiencia
        """
        # Busca conhecimento relevante
        results = self.retriever.retrieve(
            question,
            RetrievalContext(agent_id=self.agent_id),
            limit=3
        )

        if results:
            # Retorna conhecimento mais relevante
            best = results[0]
            return f"[Confianca: {best.similarity:.0%}] {best.item.content[:500]}"

        # Busca em experiencias
        episodes = self.episodes.recall_similar(question, limit=1)
        if episodes:
            ep = episodes[0]
            return f"[Experiencia] {ep.narrative[:300]}. Licoes: {'; '.join(ep.lessons[:2])}"

        return None
