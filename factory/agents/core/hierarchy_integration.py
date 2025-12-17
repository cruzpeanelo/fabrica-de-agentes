"""
Integracao de Hierarquia Corporativa com Agentes Autonomos
==========================================================

Garante que agentes respeitem a cadeia hierarquica ao tomar decisoes
e acionem skills de forma autonoma quando necessario.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
import sys
from pathlib import Path

try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

# Adiciona path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from factory.agents.corporate_hierarchy import (
        HierarchyApprovalSystem, ApprovalRequest, ApprovalStatus,
        DecisionType, CorporateAgent, ALL_CORPORATE_AGENTS,
        get_agent, get_superior, get_subordinates
    )
    HAS_HIERARCHY = True
except ImportError:
    HAS_HIERARCHY = False

try:
    from factory.agents.skills.skill_trigger import (
        SkillTrigger, SkillTriggerContext, SkillTriggerResult
    )
    HAS_SKILL_TRIGGER = True
except ImportError:
    HAS_SKILL_TRIGGER = False

if TYPE_CHECKING:
    from factory.agents.core.autonomous_agent import AutonomousAgent


class ApprovalRequirement(str, Enum):
    """Nivel de aprovacao necessario para diferentes acoes"""
    NONE = "none"           # Pode executar livremente
    NOTIFY = "notify"       # Notifica superior apos execucao
    REQUEST = "request"     # Precisa aprovacao previa
    ESCALATE = "escalate"   # Sempre escala para nivel superior


@dataclass
class WorkHoursConfig:
    """Configuracao de horario de trabalho"""
    timezone: str = "America/Sao_Paulo"     # Fuso horario Brasil
    start_hour: int = 8                     # Inicio expediente (08:00)
    end_hour: int = 18                      # Fim expediente (18:00)
    work_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])  # Segunda a Sexta


@dataclass
class HierarchyConfig:
    """Configuracao de hierarquia para um agente"""
    corporate_id: Optional[str] = None      # ID do agente corporativo
    budget_limit: float = 0.0               # Limite de orcamento autonomo
    can_approve_tasks: bool = False         # Pode aprovar tarefas de subordinados
    can_assign_tasks: bool = False          # Pode atribuir tarefas
    auto_escalate_on_error: bool = True     # Escala automaticamente em erro
    notify_superior_on_complete: bool = True # Notifica superior ao completar
    approval_timeout_hours: float = 1.0     # Timeout para aprovacao (1 hora)
    auto_approve_on_timeout: bool = True    # Aprova automaticamente apos timeout
    work_hours: WorkHoursConfig = field(default_factory=WorkHoursConfig)


@dataclass
class HierarchicalDecision:
    """Decisao que passou pelo sistema hierarquico"""
    decision_id: str
    agent_id: str
    decision_type: str
    description: str
    estimated_cost: float = 0.0
    approval_status: str = "pending"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    requested_at: Optional[datetime] = None  # Quando foi solicitada
    timeout_at: Optional[datetime] = None    # Quando expira
    auto_approved: bool = False              # Se foi aprovada automaticamente
    conditions: List[str] = field(default_factory=list)
    escalation_chain: List[str] = field(default_factory=list)


class HierarchyIntegration:
    """
    Integra agentes autonomos com sistema de hierarquia corporativa

    Responsabilidades:
    - Verificar permissoes antes de executar acoes
    - Solicitar aprovacao quando necessario
    - Notificar superiores de decisoes importantes
    - Escalar problemas automaticamente
    - Acionar skills de forma autonoma
    """

    # Limites de orcamento por acao (valores padrao em USD)
    ACTION_COST_ESTIMATES = {
        "create_file": 10,
        "modify_file": 5,
        "delete_file": 20,
        "create_database": 500,
        "modify_database": 100,
        "deploy": 1000,
        "install_dependency": 50,
        "external_api_call": 100,
        "send_notification": 10,
        "schedule_task": 25,
        "create_user": 200,
        "modify_permissions": 300,
    }

    # Acoes que requerem aprovacao por nivel
    APPROVAL_REQUIREMENTS = {
        # Acoes que qualquer um pode fazer
        "read_file": ApprovalRequirement.NONE,
        "search_code": ApprovalRequirement.NONE,
        "run_tests": ApprovalRequirement.NONE,
        "view_logs": ApprovalRequirement.NONE,

        # Acoes que notificam superior
        "create_file": ApprovalRequirement.NOTIFY,
        "modify_file": ApprovalRequirement.NOTIFY,
        "install_dependency": ApprovalRequirement.NOTIFY,

        # Acoes que requerem aprovacao
        "delete_file": ApprovalRequirement.REQUEST,
        "modify_database": ApprovalRequirement.REQUEST,
        "create_database": ApprovalRequirement.REQUEST,
        "modify_permissions": ApprovalRequirement.REQUEST,
        "create_user": ApprovalRequirement.REQUEST,

        # Acoes que sempre escalam
        "deploy": ApprovalRequirement.ESCALATE,
        "modify_infrastructure": ApprovalRequirement.ESCALATE,
        "access_production": ApprovalRequirement.ESCALATE,
    }

    def __init__(self, agent: "AutonomousAgent", config: Optional[HierarchyConfig] = None):
        """
        Inicializa integracao hierarquica

        Args:
            agent: Agente autonomo
            config: Configuracao de hierarquia
        """
        self.agent = agent
        self.config = config or HierarchyConfig()
        self.approval_system = HierarchyApprovalSystem() if HAS_HIERARCHY else None
        self.skill_trigger = SkillTrigger(agent_id=agent.agent_id) if HAS_SKILL_TRIGGER else None
        self.pending_approvals: Dict[str, HierarchicalDecision] = {}
        self.decision_history: List[HierarchicalDecision] = []
        self._decision_counter = 0

        # Vincula ao agente corporativo se existir
        self.corporate_agent: Optional[CorporateAgent] = None
        if HAS_HIERARCHY and self.config.corporate_id:
            self.corporate_agent = get_agent(self.config.corporate_id)
            if self.corporate_agent:
                self.config.budget_limit = self.corporate_agent.budget_authority
                self.config.can_approve_tasks = self.corporate_agent.can_approve_projects
                self.config.can_assign_tasks = len(self.corporate_agent.direct_reports) > 0

    def is_work_hours(self) -> bool:
        """
        Verifica se estamos dentro do horario de trabalho (Brasil)

        Returns:
            True se dentro do expediente (08:00-18:00 Brasilia, Seg-Sex)
        """
        try:
            now = self.get_brazil_time()

            # Verifica dia da semana (0=Segunda, 6=Domingo)
            if now.weekday() not in self.config.work_hours.work_days:
                return False

            # Verifica horario
            current_hour = now.hour
            if current_hour < self.config.work_hours.start_hour:
                return False
            if current_hour >= self.config.work_hours.end_hour:
                return False

            return True
        except Exception:
            # Em caso de erro, assume horario de trabalho
            return True

    def get_brazil_time(self) -> datetime:
        """Retorna a hora atual no fuso horario do Brasil (UTC-3)"""
        try:
            if HAS_PYTZ:
                tz = pytz.timezone(self.config.work_hours.timezone)
                return datetime.now(tz)
            else:
                # UTC-3 para Brasilia
                brazil_offset = timezone(timedelta(hours=-3))
                return datetime.now(brazil_offset)
        except Exception:
            return datetime.now()

    def _normalize_datetime(self, dt: datetime) -> datetime:
        """Remove timezone de datetime para permitir comparacao segura"""
        if dt is None:
            return None
        if dt.tzinfo is not None:
            # Remove timezone mantendo o horario local
            return dt.replace(tzinfo=None)
        return dt

    def _compare_datetime(self, dt1: datetime, dt2: datetime) -> int:
        """
        Compara dois datetimes de forma segura (normaliza timezone)
        Returns: -1 se dt1 < dt2, 0 se iguais, 1 se dt1 > dt2
        """
        norm1 = self._normalize_datetime(dt1)
        norm2 = self._normalize_datetime(dt2)
        if norm1 < norm2:
            return -1
        elif norm1 > norm2:
            return 1
        return 0

    def calculate_timeout(self) -> datetime:
        """
        Calcula quando a solicitacao expira, considerando horario de trabalho

        Se fora do expediente, o timeout so comeca a contar no proximo horario util.
        """
        timeout_hours = self.config.approval_timeout_hours
        now = self.get_brazil_time()

        # Se fora do expediente, ajusta para proximo dia util (max 72h adiante)
        max_iterations = 72
        iteration = 0
        while not self.is_work_hours() and iteration < max_iterations:
            now = now + timedelta(hours=1)
            iteration += 1

        # Adiciona timeout
        return now + timedelta(hours=timeout_hours)

    def check_pending_timeouts(self) -> List[HierarchicalDecision]:
        """
        Verifica aprovacoes pendentes que expiraram e auto-aprova

        Returns:
            Lista de decisoes auto-aprovadas
        """
        auto_approved = []
        now = self.get_brazil_time()

        for decision_id, decision in list(self.pending_approvals.items()):
            if decision.approval_status != "pending":
                continue

            if decision.timeout_at and self._compare_datetime(now, decision.timeout_at) >= 0:
                if self.config.auto_approve_on_timeout and self.is_work_hours():
                    # Auto-aprova
                    decision.approval_status = "auto_approved"
                    decision.approved_at = now
                    decision.approved_by = "SYSTEM_TIMEOUT"
                    decision.auto_approved = True
                    decision.conditions.append(
                        f"Auto-aprovado apos timeout de {self.config.approval_timeout_hours}h sem resposta do superior"
                    )
                    auto_approved.append(decision)

                    # Move para historico
                    self.decision_history.append(decision)
                    del self.pending_approvals[decision_id]

        return auto_approved

    def can_proceed_autonomously(self, decision_id: str) -> Dict:
        """
        Verifica se agente pode prosseguir autonomamente com uma decisao

        Args:
            decision_id: ID da decisao

        Returns:
            Dict com can_proceed, reason, decision
        """
        # Verifica timeouts pendentes
        self.check_pending_timeouts()

        if decision_id not in self.pending_approvals:
            # Procura no historico
            for decision in self.decision_history:
                if decision.decision_id == decision_id:
                    if decision.approval_status in ["approved", "auto_approved"]:
                        return {
                            "can_proceed": True,
                            "reason": "Decisao aprovada" + (" automaticamente" if decision.auto_approved else ""),
                            "decision": decision
                        }
                    else:
                        return {
                            "can_proceed": False,
                            "reason": f"Decisao {decision.approval_status}",
                            "decision": decision
                        }
            return {"can_proceed": False, "reason": "Decisao nao encontrada", "decision": None}

        decision = self.pending_approvals[decision_id]

        # Se expirou e auto-aprovacao esta habilitada
        now = self.get_brazil_time()
        if decision.timeout_at and self._compare_datetime(now, decision.timeout_at) >= 0:
            if self.config.auto_approve_on_timeout:
                return {
                    "can_proceed": True,
                    "reason": f"Timeout de {self.config.approval_timeout_hours}h expirado - agente tem autonomia para executar",
                    "decision": decision
                }

        # Calcula tempo restante
        if decision.timeout_at:
            now_norm = self._normalize_datetime(now)
            timeout_norm = self._normalize_datetime(decision.timeout_at)
            remaining = timeout_norm - now_norm
            remaining_minutes = remaining.total_seconds() / 60
            return {
                "can_proceed": False,
                "reason": f"Aguardando aprovacao ({remaining_minutes:.0f} minutos restantes)",
                "decision": decision
            }

        return {
            "can_proceed": False,
            "reason": "Aguardando aprovacao do superior",
            "decision": decision
        }

    def check_permission(self, action: str, estimated_cost: float = 0) -> Dict:
        """
        Verifica se agente tem permissao para executar acao

        Args:
            action: Tipo de acao a executar
            estimated_cost: Custo estimado da acao

        Returns:
            Dict com allowed, requirement, reason
        """
        # Determina custo se nao informado
        if estimated_cost == 0:
            estimated_cost = self.ACTION_COST_ESTIMATES.get(action, 50)

        # Determina requisito de aprovacao
        requirement = self.APPROVAL_REQUIREMENTS.get(action, ApprovalRequirement.NOTIFY)

        # Verifica limite de orcamento
        if estimated_cost > self.config.budget_limit:
            return {
                "allowed": False,
                "requirement": ApprovalRequirement.ESCALATE,
                "reason": f"Custo estimado ({estimated_cost}) excede limite de orcamento ({self.config.budget_limit})"
            }

        # Acoes livres
        if requirement == ApprovalRequirement.NONE:
            return {
                "allowed": True,
                "requirement": requirement,
                "reason": "Acao permitida sem restricoes"
            }

        # Acoes que notificam
        if requirement == ApprovalRequirement.NOTIFY:
            return {
                "allowed": True,
                "requirement": requirement,
                "reason": "Acao permitida, superior sera notificado"
            }

        # Acoes que requerem aprovacao
        if requirement == ApprovalRequirement.REQUEST:
            return {
                "allowed": False,
                "requirement": requirement,
                "reason": "Acao requer aprovacao do superior"
            }

        # Acoes que escalam
        return {
            "allowed": False,
            "requirement": ApprovalRequirement.ESCALATE,
            "reason": "Acao requer escalacao para nivel superior"
        }

    def request_approval(
        self,
        action: str,
        description: str,
        estimated_cost: float = 0,
        priority: int = 5
    ) -> HierarchicalDecision:
        """
        Solicita aprovacao para uma acao

        Args:
            action: Tipo de acao
            description: Descricao da acao
            estimated_cost: Custo estimado
            priority: Prioridade (1-10)

        Returns:
            HierarchicalDecision com status da solicitacao
        """
        if estimated_cost == 0:
            estimated_cost = self.ACTION_COST_ESTIMATES.get(action, 50)

        self._decision_counter += 1
        decision_id = f"DEC-{self.agent.agent_id}-{self._decision_counter:05d}"

        # Calcula timeout
        now = self.get_brazil_time()
        timeout_at = self.calculate_timeout()

        decision = HierarchicalDecision(
            decision_id=decision_id,
            agent_id=self.agent.agent_id,
            decision_type=action,
            description=description,
            estimated_cost=estimated_cost,
            requested_at=now,
            timeout_at=timeout_at,
            escalation_chain=[self.agent.agent_id]
        )

        # Se tem sistema de aprovacao, usa
        if self.approval_system and self.corporate_agent:
            try:
                decision_type = DecisionType.TECHNICAL_DECISION if "code" in action or "file" in action else DecisionType.BUDGET_ALLOCATION

                request = self.approval_system.create_request(
                    requester_id=self.config.corporate_id,
                    decision_type=decision_type,
                    title=f"{action}: {description[:50]}",
                    description=description,
                    estimated_cost=estimated_cost,
                    priority=priority
                )

                decision.approval_status = "pending"
                decision.escalation_chain.append(request.approver_id)
                decision.conditions.append(
                    f"Timeout em {timeout_at.strftime('%d/%m %H:%M')} - agente tera autonomia apos expirar"
                )

            except Exception as e:
                decision.approval_status = "error"
                decision.conditions.append(f"Erro ao solicitar aprovacao: {str(e)}")
        else:
            # Sem sistema hierarquico, aprova automaticamente se dentro do limite
            if estimated_cost <= self.config.budget_limit:
                decision.approval_status = "auto_approved"
                decision.approved_by = self.agent.agent_id
                decision.approved_at = datetime.now()
            else:
                decision.approval_status = "needs_manual_approval"

        self.pending_approvals[decision_id] = decision
        return decision

    def notify_superior(self, message: str, action: str, result: Any = None):
        """
        Notifica superior sobre acao executada

        Args:
            message: Mensagem de notificacao
            action: Acao executada
            result: Resultado da acao
        """
        if not self.corporate_agent:
            return

        superior = get_superior(self.config.corporate_id)
        if not superior:
            return

        # Em um sistema real, enviaria notificacao
        # Aqui apenas registramos no historico
        notification = HierarchicalDecision(
            decision_id=f"NOTIF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            agent_id=self.agent.agent_id,
            decision_type=action,
            description=message,
            approval_status="notified",
            approved_by=superior.agent_id,
            approved_at=datetime.now()
        )
        self.decision_history.append(notification)

    def escalate_issue(self, issue: str, severity: int = 5) -> str:
        """
        Escala problema para cadeia hierarquica

        Args:
            issue: Descricao do problema
            severity: Severidade (1-10)

        Returns:
            ID do escalacao
        """
        if not self.corporate_agent:
            return "NO_HIERARCHY"

        escalation_chain = []
        current = self.corporate_agent

        # Sobe na hierarquia baseado na severidade
        levels_to_escalate = max(1, severity // 3)

        for _ in range(levels_to_escalate):
            if current.reports_to:
                superior = get_agent(current.reports_to)
                if superior:
                    escalation_chain.append(superior.agent_id)
                    current = superior
                else:
                    break
            else:
                break

        # Registra escalacao
        decision = HierarchicalDecision(
            decision_id=f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            agent_id=self.agent.agent_id,
            decision_type="escalation",
            description=issue,
            approval_status="escalated",
            escalation_chain=escalation_chain
        )
        self.decision_history.append(decision)

        return decision.decision_id

    def trigger_skills_autonomously(
        self,
        task_description: str,
        files: Optional[List[str]] = None
    ) -> Optional[SkillTriggerResult]:
        """
        Aciona skills de forma autonoma baseado no contexto

        Args:
            task_description: Descricao da tarefa
            files: Arquivos envolvidos

        Returns:
            Resultado do acionamento de skills
        """
        if not self.skill_trigger:
            return None

        context = SkillTriggerContext(
            task_description=task_description,
            files_involved=files or [],
            domain=self.agent.domain
        )

        # Analisa contexto para determinar skills
        recommended_skills = self.skill_trigger.analyze_context(context)

        # Verifica permissao para usar skills
        for skill in recommended_skills:
            permission = self.check_permission(f"use_skill_{skill}")
            if not permission["allowed"]:
                # Remove skill que nao tem permissao
                recommended_skills.remove(skill)

        # Aciona skills permitidas
        if files:
            result = self.skill_trigger.trigger_skills(context)

            # Notifica superior sobre uso de skills
            if self.config.notify_superior_on_complete:
                self.notify_superior(
                    f"Skills acionadas: {', '.join(result.skills_triggered)}",
                    "skill_trigger",
                    result
                )

            return result

        return None

    def can_assign_to(self, subordinate_id: str, task_description: str) -> bool:
        """
        Verifica se pode atribuir tarefa a um subordinado

        Args:
            subordinate_id: ID do subordinado
            task_description: Descricao da tarefa

        Returns:
            True se pode atribuir
        """
        if not self.config.can_assign_tasks:
            return False

        if not self.corporate_agent:
            return False

        # Verifica se eh subordinado direto
        if subordinate_id not in self.corporate_agent.direct_reports:
            # Verifica se eh subordinado indireto
            all_subordinates = get_subordinates(self.config.corporate_id, recursive=True)
            if not any(s.agent_id == subordinate_id for s in all_subordinates):
                return False

        return True

    def get_approval_status(self, decision_id: str) -> Optional[str]:
        """Retorna status de uma aprovacao pendente"""
        if decision_id in self.pending_approvals:
            return self.pending_approvals[decision_id].approval_status

        for decision in self.decision_history:
            if decision.decision_id == decision_id:
                return decision.approval_status

        return None

    def get_hierarchy_info(self) -> Dict:
        """Retorna informacoes da hierarquia do agente"""
        if not self.corporate_agent:
            return {"has_hierarchy": False}

        superior = get_superior(self.config.corporate_id)
        subordinates = get_subordinates(self.config.corporate_id)

        return {
            "has_hierarchy": True,
            "agent_id": self.corporate_agent.agent_id,
            "name": self.corporate_agent.name,
            "title": self.corporate_agent.title,
            "level": self.corporate_agent.level.title,
            "department": self.corporate_agent.department.display_name,
            "budget_authority": self.corporate_agent.budget_authority,
            "superior": {
                "id": superior.agent_id,
                "name": superior.name,
                "title": superior.title
            } if superior else None,
            "subordinates": [
                {"id": s.agent_id, "name": s.name, "title": s.title}
                for s in subordinates
            ],
            "can_hire": self.corporate_agent.can_hire,
            "can_fire": self.corporate_agent.can_fire,
            "can_approve_projects": self.corporate_agent.can_approve_projects
        }


def integrate_hierarchy(agent: "AutonomousAgent", corporate_id: Optional[str] = None) -> HierarchyIntegration:
    """
    Integra agente com sistema de hierarquia

    Args:
        agent: Agente autonomo
        corporate_id: ID do agente corporativo correspondente

    Returns:
        HierarchyIntegration configurada
    """
    config = HierarchyConfig(corporate_id=corporate_id)
    return HierarchyIntegration(agent, config)


def with_hierarchy(corporate_id: str):
    """
    Decorator para adicionar integracao hierarquica a um agente

    Uso:
        @with_hierarchy("DEV-SR-BACK")
        class MyAgent(AutonomousAgent):
            pass
    """
    def decorator(agent_class):
        original_init = agent_class.__init__

        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.hierarchy = integrate_hierarchy(self, corporate_id)

        agent_class.__init__ = new_init
        return agent_class

    return decorator


__all__ = [
    "WorkHoursConfig",
    "HierarchyConfig",
    "HierarchyIntegration",
    "HierarchicalDecision",
    "ApprovalRequirement",
    "integrate_hierarchy",
    "with_hierarchy",
]
