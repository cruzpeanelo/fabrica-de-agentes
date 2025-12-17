"""
Corporate Hierarchy Agents - Hierarquia Corporativa Completa
=============================================================

Sistema completo de agentes que simula a hierarquia de uma multinacional.
Inclui todas as areas de Negocio e TI com sistema de aprovacao hierarquica.

ESTRUTURA ORGANIZACIONAL:

NEGOCIO (Business):
- Executivo (CEO, CFO, COO, CMO, CHRO)
- Financeiro (Controladoria, Tesouraria, Contabilidade)
- Comercial (Vendas, Pre-vendas, Pos-vendas)
- Marketing (Digital, Branding, Comunicacao)
- RH (Recrutamento, T&D, DP)
- Operacoes (Logistica, Supply Chain, Qualidade)
- Juridico (Contratos, Compliance)

TI (Technology):
- Gestao de TI (CIO, VP, Diretores)
- Desenvolvimento (Frontend, Backend, Mobile, Full-stack)
- Dados (Analytics, BI, Data Engineering, Data Science)
- Infraestrutura (Cloud, Network, Datacenter)
- Seguranca (AppSec, InfraSec, SOC)
- Qualidade (QA, Automacao, Performance)
- DevOps/SRE (CI/CD, Monitoring, Platform)
- Arquitetura (Solutions, Enterprise, Cloud)

NIVEIS HIERARQUICOS (10 niveis):
1. CEO
2. C-Level (CFO, CIO, COO, CMO, CHRO)
3. Vice-Presidentes
4. Diretores
5. Gerentes Senior
6. Gerentes
7. Coordenadores
8. Especialistas Senior / Tech Leads
9. Analistas / Desenvolvedores
10. Assistentes / Trainees / Estagiarios

SISTEMA DE APROVACAO:
- Cada nivel tem autoridade para aprovar decisoes ate seu limite
- Decisoes acima do limite sao escaladas automaticamente
- Superior pode aprovar, rejeitar, modificar ou delegar
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum, auto
from datetime import datetime
import json
import uuid


# =============================================================================
# ENUMS
# =============================================================================

class HierarchyLevel(Enum):
    """Niveis hierarquicos corporativos"""
    CEO = (1, "Chief Executive Officer", 1000000)
    C_LEVEL = (2, "C-Level Executive", 500000)
    VP = (3, "Vice President", 250000)
    DIRECTOR = (4, "Director", 100000)
    SENIOR_MANAGER = (5, "Senior Manager", 50000)
    MANAGER = (6, "Manager", 25000)
    COORDINATOR = (7, "Coordinator", 10000)
    SENIOR_SPECIALIST = (8, "Senior Specialist / Tech Lead", 5000)
    ANALYST = (9, "Analyst / Developer", 2000)
    ASSISTANT = (10, "Assistant / Trainee / Intern", 500)

    def __init__(self, level_num: int, title: str, budget_authority: int):
        self.level_num = level_num
        self.title = title
        self.budget_authority = budget_authority

    def is_superior_to(self, other: "HierarchyLevel") -> bool:
        return self.level_num < other.level_num


class Department(Enum):
    """Departamentos da empresa"""
    # EXECUTIVO
    EXECUTIVE = ("executive", "Executivo", "business")

    # NEGOCIO
    FINANCE = ("finance", "Financeiro", "business")
    SALES = ("sales", "Comercial/Vendas", "business")
    MARKETING = ("marketing", "Marketing", "business")
    HR = ("human_resources", "Recursos Humanos", "business")
    OPERATIONS = ("operations", "Operacoes", "business")
    LEGAL = ("legal", "Juridico", "business")
    PROCUREMENT = ("procurement", "Compras/Suprimentos", "business")
    SUPPLY_CHAIN = ("supply_chain", "Supply Chain", "business")
    CUSTOMER_SERVICE = ("customer_service", "Atendimento ao Cliente", "business")
    QUALITY_BUSINESS = ("quality_business", "Qualidade (Negocios)", "business")

    # TI
    IT_MANAGEMENT = ("it_management", "Gestao de TI", "technology")
    DEVELOPMENT = ("development", "Desenvolvimento", "technology")
    DATA = ("data", "Dados e Analytics", "technology")
    INFRASTRUCTURE = ("infrastructure", "Infraestrutura", "technology")
    SECURITY = ("security", "Seguranca da Informacao", "technology")
    QA = ("qa", "Quality Assurance", "technology")
    DEVOPS = ("devops", "DevOps/SRE", "technology")
    ARCHITECTURE = ("architecture", "Arquitetura", "technology")
    IT_SUPPORT = ("it_support", "Suporte de TI", "technology")
    PMO = ("pmo", "PMO/Projetos", "technology")

    def __init__(self, dept_id: str, display_name: str, area: str):
        self.dept_id = dept_id
        self.display_name = display_name
        self.area = area  # "business" ou "technology"


class DecisionType(Enum):
    """Tipos de decisao"""
    BUDGET_ALLOCATION = ("budget", "Alocacao Orcamentaria")
    HIRING = ("hiring", "Contratacao")
    FIRING = ("firing", "Desligamento")
    PROJECT_APPROVAL = ("project", "Aprovacao de Projeto")
    VENDOR_SELECTION = ("vendor", "Selecao de Fornecedor")
    PROCESS_CHANGE = ("process", "Mudanca de Processo")
    POLICY_CHANGE = ("policy", "Mudanca de Politica")
    TECHNICAL_DECISION = ("technical", "Decisao Tecnica")
    STRATEGIC_DECISION = ("strategic", "Decisao Estrategica")
    EMERGENCY_ACTION = ("emergency", "Acao de Emergencia")
    RESOURCE_ALLOCATION = ("resource", "Alocacao de Recursos")
    PROMOTION = ("promotion", "Promocao")
    TRAINING = ("training", "Treinamento")
    VACATION = ("vacation", "Ferias")

    def __init__(self, type_id: str, display_name: str):
        self.type_id = type_id
        self.display_name = display_name


class ApprovalStatus(Enum):
    """Status de aprovacao"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    MODIFIED = "modified"
    DELEGATED = "delegated"
    CANCELLED = "cancelled"


class AgentStatus(Enum):
    """Status do agente"""
    STANDBY = "STANDBY"
    WORKING = "WORKING"
    IN_MEETING = "IN_MEETING"
    ON_BREAK = "ON_BREAK"
    OFFLINE = "OFFLINE"
    BLOCKED = "BLOCKED"


# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class ApprovalRequest:
    """Solicitacao de aprovacao"""
    request_id: str
    requester_id: str
    approver_id: str
    decision_type: DecisionType
    title: str
    description: str
    estimated_cost: float = 0
    priority: int = 5
    deadline: Optional[datetime] = None
    attachments: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    response: Optional[str] = None
    conditions: List[str] = field(default_factory=list)
    delegated_to: Optional[str] = None
    escalation_chain: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "requester_id": self.requester_id,
            "approver_id": self.approver_id,
            "decision_type": self.decision_type.display_name,
            "title": self.title,
            "description": self.description,
            "estimated_cost": self.estimated_cost,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "response": self.response,
            "escalation_chain": self.escalation_chain
        }


@dataclass
class WorkMetrics:
    """Metricas de trabalho do agente"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_in_progress: int = 0
    total_hours_worked: float = 0
    projects_participated: List[str] = field(default_factory=list)
    approvals_granted: int = 0
    approvals_rejected: int = 0
    skills_used: Dict[str, int] = field(default_factory=dict)
    last_activity: Optional[datetime] = None
    average_task_duration: float = 0  # em horas

    def to_dict(self) -> Dict:
        return {
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_in_progress": self.tasks_in_progress,
            "total_hours_worked": self.total_hours_worked,
            "projects_participated": self.projects_participated,
            "approvals_granted": self.approvals_granted,
            "approvals_rejected": self.approvals_rejected,
            "skills_used": self.skills_used,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "productivity_score": self.get_productivity_score()
        }

    def get_productivity_score(self) -> float:
        """Calcula score de produtividade (0-100)"""
        if self.tasks_completed + self.tasks_failed == 0:
            return 0
        success_rate = self.tasks_completed / (self.tasks_completed + self.tasks_failed)
        return round(success_rate * 100, 1)


@dataclass
class CorporateAgent:
    """Agente com posicao na hierarquia corporativa"""
    agent_id: str
    name: str
    title: str
    level: HierarchyLevel
    department: Department

    # Hierarquia
    reports_to: Optional[str] = None
    direct_reports: List[str] = field(default_factory=list)

    # Competencias
    responsibilities: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

    # Autoridade
    budget_authority: float = 0
    can_hire: bool = False
    can_fire: bool = False
    can_approve_projects: bool = False
    decision_authority: List[DecisionType] = field(default_factory=list)

    # Status
    status: AgentStatus = AgentStatus.STANDBY
    current_task: Optional[str] = None
    current_project: Optional[str] = None

    # Metricas
    metrics: WorkMetrics = field(default_factory=WorkMetrics)

    # Metadados
    years_experience: int = 0
    email: str = ""

    def can_approve(self, request: ApprovalRequest) -> Tuple[bool, str]:
        """Verifica se pode aprovar uma solicitacao"""
        if request.estimated_cost > self.budget_authority:
            return False, f"Custo ({request.estimated_cost}) excede autoridade ({self.budget_authority})"
        if request.decision_type not in self.decision_authority:
            return False, f"Sem autoridade para {request.decision_type.display_name}"
        return True, "Autorizado"

    def get_hierarchy_path(self) -> List[str]:
        """Retorna caminho hierarquico ate o topo"""
        path = [self.agent_id]
        if self.reports_to:
            path.append(self.reports_to)
        return path

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "title": self.title,
            "level": self.level.title,
            "level_num": self.level.level_num,
            "department": self.department.display_name,
            "department_id": self.department.dept_id,
            "area": self.department.area,
            "reports_to": self.reports_to,
            "direct_reports": self.direct_reports,
            "direct_reports_count": len(self.direct_reports),
            "responsibilities": self.responsibilities,
            "skills": self.skills,
            "budget_authority": self.budget_authority,
            "can_hire": self.can_hire,
            "can_fire": self.can_fire,
            "status": self.status.value,
            "current_task": self.current_task,
            "current_project": self.current_project,
            "metrics": self.metrics.to_dict(),
            "years_experience": self.years_experience
        }


# =============================================================================
# DEFINICAO COMPLETA DOS AGENTES CORPORATIVOS
# =============================================================================

def create_agent(
    agent_id: str,
    name: str,
    title: str,
    level: HierarchyLevel,
    department: Department,
    reports_to: Optional[str] = None,
    responsibilities: List[str] = None,
    skills: List[str] = None,
    years_exp: int = 5
) -> CorporateAgent:
    """Factory function para criar agentes"""

    # Autoridades baseadas no nivel
    budget = level.budget_authority
    can_hire = level.level_num <= 6  # Gerente ou acima
    can_fire = level.level_num <= 5  # Gerente Senior ou acima
    can_approve = level.level_num <= 5

    # Decision authority baseada no nivel
    decision_auth = []
    if level.level_num <= 2:  # C-Level
        decision_auth = [dt for dt in DecisionType]
    elif level.level_num <= 4:  # VP/Director
        decision_auth = [
            DecisionType.BUDGET_ALLOCATION, DecisionType.HIRING,
            DecisionType.PROJECT_APPROVAL, DecisionType.VENDOR_SELECTION,
            DecisionType.TECHNICAL_DECISION, DecisionType.RESOURCE_ALLOCATION
        ]
    elif level.level_num <= 6:  # Sr Manager/Manager
        decision_auth = [
            DecisionType.HIRING, DecisionType.PROJECT_APPROVAL,
            DecisionType.TECHNICAL_DECISION, DecisionType.RESOURCE_ALLOCATION,
            DecisionType.TRAINING, DecisionType.VACATION
        ]
    elif level.level_num <= 8:  # Coordinator/Sr Specialist
        decision_auth = [
            DecisionType.TECHNICAL_DECISION, DecisionType.TRAINING
        ]

    return CorporateAgent(
        agent_id=agent_id,
        name=name,
        title=title,
        level=level,
        department=department,
        reports_to=reports_to,
        responsibilities=responsibilities or [],
        skills=skills or [],
        budget_authority=budget,
        can_hire=can_hire,
        can_fire=can_fire,
        can_approve_projects=can_approve,
        decision_authority=decision_auth,
        years_experience=years_exp,
        email=f"{agent_id.lower().replace('-', '.')}@empresa.com"
    )


# =============================================================================
# AGENTES - EXECUTIVO
# =============================================================================

EXECUTIVE_AGENTS = [
    create_agent("EXEC-CEO", "CEO", "Chief Executive Officer",
                 HierarchyLevel.CEO, Department.EXECUTIVE, None,
                 ["Visao estrategica", "Lideranca executiva", "Relacoes com stakeholders"],
                 ["leadership", "strategy", "communication"], 25),
]

# =============================================================================
# AGENTES - FINANCEIRO (NEGOCIO)
# =============================================================================

FINANCE_AGENTS = [
    create_agent("FIN-CFO", "CFO", "Chief Financial Officer",
                 HierarchyLevel.C_LEVEL, Department.FINANCE, "EXEC-CEO",
                 ["Gestao financeira", "Planejamento orcamentario", "Relacoes com investidores"],
                 ["finance", "accounting", "budgeting", "risk_management"], 20),

    create_agent("FIN-DIR-CTRL", "Diretor de Controladoria", "Controller Director",
                 HierarchyLevel.DIRECTOR, Department.FINANCE, "FIN-CFO",
                 ["Controladoria", "Fechamento contabil", "Auditoria interna"],
                 ["controlling", "accounting", "audit"], 15),

    create_agent("FIN-DIR-TES", "Diretor de Tesouraria", "Treasury Director",
                 HierarchyLevel.DIRECTOR, Department.FINANCE, "FIN-CFO",
                 ["Tesouraria", "Gestao de caixa", "Operacoes financeiras"],
                 ["treasury", "cash_management", "banking"], 15),

    create_agent("FIN-MGR-CONT", "Gerente de Contabilidade", "Accounting Manager",
                 HierarchyLevel.MANAGER, Department.FINANCE, "FIN-DIR-CTRL",
                 ["Contabilidade geral", "Fiscal", "Patrimonio"],
                 ["accounting", "tax", "gaap"], 10),

    create_agent("FIN-MGR-FP&A", "Gerente de FP&A", "FP&A Manager",
                 HierarchyLevel.MANAGER, Department.FINANCE, "FIN-CFO",
                 ["Planejamento financeiro", "Analise de resultados", "Orcamento"],
                 ["fp&a", "budgeting", "forecasting", "analysis"], 10),

    create_agent("FIN-COORD-CONT", "Coordenador Contabil", "Accounting Coordinator",
                 HierarchyLevel.COORDINATOR, Department.FINANCE, "FIN-MGR-CONT",
                 ["Lancamentos contabeis", "Conciliacoes", "Reports"],
                 ["accounting", "reconciliation", "reporting"], 7),

    create_agent("FIN-SR-AN", "Analista Financeiro Senior", "Senior Financial Analyst",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.FINANCE, "FIN-MGR-FP&A",
                 ["Analises financeiras", "Modelagem", "Projecoes"],
                 ["financial_analysis", "excel", "modeling"], 6),

    create_agent("FIN-AN", "Analista Financeiro", "Financial Analyst",
                 HierarchyLevel.ANALYST, Department.FINANCE, "FIN-SR-AN",
                 ["Suporte a analises", "Relatorios", "Dados"],
                 ["analysis", "excel", "reporting"], 3),

    create_agent("FIN-ASST", "Assistente Financeiro", "Financial Assistant",
                 HierarchyLevel.ASSISTANT, Department.FINANCE, "FIN-COORD-CONT",
                 ["Apoio administrativo", "Lancamentos", "Arquivo"],
                 ["administration", "data_entry"], 1),
]

# =============================================================================
# AGENTES - COMERCIAL/VENDAS (NEGOCIO)
# =============================================================================

SALES_AGENTS = [
    create_agent("SALES-VP", "VP de Vendas", "VP of Sales",
                 HierarchyLevel.VP, Department.SALES, "EXEC-CEO",
                 ["Estrategia comercial", "Metas de vendas", "Grandes contas"],
                 ["sales", "negotiation", "leadership", "strategy"], 18),

    create_agent("SALES-DIR-NAC", "Diretor Comercial Nacional", "National Sales Director",
                 HierarchyLevel.DIRECTOR, Department.SALES, "SALES-VP",
                 ["Vendas nacionais", "Expansao de mercado", "Parcerias"],
                 ["sales", "market_expansion", "partnerships"], 15),

    create_agent("SALES-DIR-INT", "Diretor Comercial Internacional", "International Sales Director",
                 HierarchyLevel.DIRECTOR, Department.SALES, "SALES-VP",
                 ["Vendas internacionais", "Exportacao", "Mercados externos"],
                 ["international_sales", "export", "foreign_markets"], 15),

    create_agent("SALES-MGR-KEY", "Gerente de Key Accounts", "Key Account Manager",
                 HierarchyLevel.MANAGER, Department.SALES, "SALES-DIR-NAC",
                 ["Grandes contas", "Relacionamento", "Contratos"],
                 ["key_accounts", "relationship", "contracts"], 10),

    create_agent("SALES-MGR-REG", "Gerente Regional de Vendas", "Regional Sales Manager",
                 HierarchyLevel.MANAGER, Department.SALES, "SALES-DIR-NAC",
                 ["Vendas regionais", "Equipe de campo", "Metas"],
                 ["regional_sales", "team_management", "targets"], 10),

    create_agent("SALES-COORD", "Coordenador de Vendas", "Sales Coordinator",
                 HierarchyLevel.COORDINATOR, Department.SALES, "SALES-MGR-REG",
                 ["Coordenacao de vendedores", "Pipeline", "CRM"],
                 ["sales_coordination", "crm", "pipeline"], 6),

    create_agent("SALES-SR-EXEC", "Executivo de Vendas Senior", "Senior Sales Executive",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.SALES, "SALES-COORD",
                 ["Vendas complexas", "Negociacao", "Fechamento"],
                 ["sales", "negotiation", "closing"], 5),

    create_agent("SALES-EXEC", "Executivo de Vendas", "Sales Executive",
                 HierarchyLevel.ANALYST, Department.SALES, "SALES-SR-EXEC",
                 ["Vendas", "Prospeccao", "Atendimento"],
                 ["sales", "prospecting", "customer_service"], 3),

    create_agent("SALES-SDR", "SDR/BDR", "Sales Development Representative",
                 HierarchyLevel.ASSISTANT, Department.SALES, "SALES-COORD",
                 ["Qualificacao de leads", "Agendamento", "Primeiro contato"],
                 ["lead_qualification", "outbound", "prospecting"], 1),
]

# =============================================================================
# AGENTES - MARKETING (NEGOCIO)
# =============================================================================

MARKETING_AGENTS = [
    create_agent("MKT-CMO", "CMO", "Chief Marketing Officer",
                 HierarchyLevel.C_LEVEL, Department.MARKETING, "EXEC-CEO",
                 ["Estrategia de marketing", "Marca", "Comunicacao"],
                 ["marketing", "branding", "communication", "strategy"], 18),

    create_agent("MKT-DIR-DIG", "Diretor de Marketing Digital", "Digital Marketing Director",
                 HierarchyLevel.DIRECTOR, Department.MARKETING, "MKT-CMO",
                 ["Marketing digital", "Performance", "E-commerce"],
                 ["digital_marketing", "performance", "ecommerce"], 12),

    create_agent("MKT-DIR-BRAND", "Diretor de Marca", "Brand Director",
                 HierarchyLevel.DIRECTOR, Department.MARKETING, "MKT-CMO",
                 ["Gestao de marca", "Branding", "Design"],
                 ["branding", "design", "brand_management"], 12),

    create_agent("MKT-MGR-CONT", "Gerente de Conteudo", "Content Manager",
                 HierarchyLevel.MANAGER, Department.MARKETING, "MKT-DIR-DIG",
                 ["Conteudo", "SEO", "Social media"],
                 ["content", "seo", "social_media"], 8),

    create_agent("MKT-MGR-PERF", "Gerente de Performance", "Performance Manager",
                 HierarchyLevel.MANAGER, Department.MARKETING, "MKT-DIR-DIG",
                 ["Media paga", "Analytics", "ROI"],
                 ["paid_media", "analytics", "roi"], 8),

    create_agent("MKT-COORD", "Coordenador de Marketing", "Marketing Coordinator",
                 HierarchyLevel.COORDINATOR, Department.MARKETING, "MKT-MGR-CONT",
                 ["Campanhas", "Eventos", "Materiais"],
                 ["campaigns", "events", "materials"], 5),

    create_agent("MKT-SR-AN", "Analista de Marketing Senior", "Senior Marketing Analyst",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.MARKETING, "MKT-MGR-PERF",
                 ["Analise de campanhas", "Dashboards", "Insights"],
                 ["analytics", "reporting", "insights"], 5),

    create_agent("MKT-AN", "Analista de Marketing", "Marketing Analyst",
                 HierarchyLevel.ANALYST, Department.MARKETING, "MKT-SR-AN",
                 ["Execucao de campanhas", "Social media", "Reports"],
                 ["campaigns", "social_media", "reporting"], 2),

    create_agent("MKT-ASST", "Assistente de Marketing", "Marketing Assistant",
                 HierarchyLevel.ASSISTANT, Department.MARKETING, "MKT-COORD",
                 ["Apoio operacional", "Materiais", "Eventos"],
                 ["support", "materials", "events"], 1),
]

# =============================================================================
# AGENTES - RH (NEGOCIO)
# =============================================================================

HR_AGENTS = [
    create_agent("HR-CHRO", "CHRO", "Chief Human Resources Officer",
                 HierarchyLevel.C_LEVEL, Department.HR, "EXEC-CEO",
                 ["Gestao de pessoas", "Cultura", "Desenvolvimento"],
                 ["hr", "culture", "talent_management", "leadership"], 18),

    create_agent("HR-DIR-TA", "Diretor de Talent Acquisition", "TA Director",
                 HierarchyLevel.DIRECTOR, Department.HR, "HR-CHRO",
                 ["Recrutamento", "Employer branding", "Selecao"],
                 ["recruitment", "employer_branding", "selection"], 12),

    create_agent("HR-DIR-TD", "Diretor de T&D", "L&D Director",
                 HierarchyLevel.DIRECTOR, Department.HR, "HR-CHRO",
                 ["Treinamento", "Desenvolvimento", "Academia corporativa"],
                 ["training", "development", "learning"], 12),

    create_agent("HR-MGR-BP", "Gerente de Business Partner", "HR BP Manager",
                 HierarchyLevel.MANAGER, Department.HR, "HR-CHRO",
                 ["Business partnering", "Consultoria interna", "Gestao de conflitos"],
                 ["hr_bp", "consulting", "conflict_management"], 10),

    create_agent("HR-MGR-DP", "Gerente de DP", "Payroll Manager",
                 HierarchyLevel.MANAGER, Department.HR, "HR-CHRO",
                 ["Folha de pagamento", "Beneficios", "Obrigacoes trabalhistas"],
                 ["payroll", "benefits", "labor_law"], 10),

    create_agent("HR-COORD-REC", "Coordenador de Recrutamento", "Recruitment Coordinator",
                 HierarchyLevel.COORDINATOR, Department.HR, "HR-DIR-TA",
                 ["Processo seletivo", "Entrevistas", "Onboarding"],
                 ["recruitment", "interviews", "onboarding"], 6),

    create_agent("HR-SR-AN", "Analista de RH Senior", "Senior HR Analyst",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.HR, "HR-MGR-BP",
                 ["Analise de RH", "Pesquisas", "Indicadores"],
                 ["hr_analytics", "surveys", "kpis"], 5),

    create_agent("HR-AN", "Analista de RH", "HR Analyst",
                 HierarchyLevel.ANALYST, Department.HR, "HR-SR-AN",
                 ["Processos de RH", "Atendimento", "Sistemas"],
                 ["hr_processes", "support", "systems"], 3),

    create_agent("HR-ASST", "Assistente de RH", "HR Assistant",
                 HierarchyLevel.ASSISTANT, Department.HR, "HR-COORD-REC",
                 ["Apoio administrativo", "Documentacao", "Agendamentos"],
                 ["administration", "documentation", "scheduling"], 1),
]

# =============================================================================
# AGENTES - OPERACOES (NEGOCIO)
# =============================================================================

OPERATIONS_AGENTS = [
    create_agent("OPS-COO", "COO", "Chief Operating Officer",
                 HierarchyLevel.C_LEVEL, Department.OPERATIONS, "EXEC-CEO",
                 ["Operacoes", "Eficiencia", "Processos"],
                 ["operations", "efficiency", "process_management"], 18),

    create_agent("OPS-DIR-LOG", "Diretor de Logistica", "Logistics Director",
                 HierarchyLevel.DIRECTOR, Department.SUPPLY_CHAIN, "OPS-COO",
                 ["Logistica", "Distribuicao", "Armazens"],
                 ["logistics", "distribution", "warehousing"], 15),

    create_agent("OPS-DIR-QUAL", "Diretor de Qualidade", "Quality Director",
                 HierarchyLevel.DIRECTOR, Department.QUALITY_BUSINESS, "OPS-COO",
                 ["Qualidade", "ISO", "Melhoria continua"],
                 ["quality", "iso", "continuous_improvement"], 15),

    create_agent("OPS-MGR-PROC", "Gerente de Processos", "Process Manager",
                 HierarchyLevel.MANAGER, Department.OPERATIONS, "OPS-COO",
                 ["Mapeamento de processos", "BPM", "Lean"],
                 ["bpm", "lean", "process_mapping"], 10),

    create_agent("OPS-MGR-SC", "Gerente de Supply Chain", "Supply Chain Manager",
                 HierarchyLevel.MANAGER, Department.SUPPLY_CHAIN, "OPS-DIR-LOG",
                 ["Supply chain", "Fornecedores", "Planejamento"],
                 ["supply_chain", "suppliers", "planning"], 10),

    create_agent("OPS-COORD", "Coordenador de Operacoes", "Operations Coordinator",
                 HierarchyLevel.COORDINATOR, Department.OPERATIONS, "OPS-MGR-PROC",
                 ["Coordenacao operacional", "KPIs", "Reports"],
                 ["operations", "kpis", "reporting"], 6),

    create_agent("OPS-SR-AN", "Analista de Operacoes Senior", "Senior Operations Analyst",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.OPERATIONS, "OPS-COORD",
                 ["Analise operacional", "Dashboards", "Otimizacao"],
                 ["analysis", "dashboards", "optimization"], 5),

    create_agent("OPS-AN", "Analista de Operacoes", "Operations Analyst",
                 HierarchyLevel.ANALYST, Department.OPERATIONS, "OPS-SR-AN",
                 ["Monitoramento", "Reports", "Suporte"],
                 ["monitoring", "reporting", "support"], 3),
]

# =============================================================================
# AGENTES - TI / GESTAO
# =============================================================================

IT_MANAGEMENT_AGENTS = [
    create_agent("IT-CIO", "CIO", "Chief Information Officer",
                 HierarchyLevel.C_LEVEL, Department.IT_MANAGEMENT, "EXEC-CEO",
                 ["Estrategia de TI", "Transformacao digital", "Governanca"],
                 ["it_strategy", "digital_transformation", "governance"], 20),

    create_agent("IT-VP-TECH", "VP de Tecnologia", "VP of Technology",
                 HierarchyLevel.VP, Department.IT_MANAGEMENT, "IT-CIO",
                 ["Lideranca tecnica", "Roadmap", "Inovacao"],
                 ["technology", "leadership", "innovation", "roadmap"], 16),

    create_agent("IT-VP-DATA", "VP de Dados", "VP of Data",
                 HierarchyLevel.VP, Department.DATA, "IT-CIO",
                 ["Estrategia de dados", "Analytics", "Governanca de dados"],
                 ["data_strategy", "analytics", "data_governance"], 16),
]

# =============================================================================
# AGENTES - TI / DESENVOLVIMENTO
# =============================================================================

DEV_AGENTS = [
    create_agent("DEV-DIR", "Diretor de Desenvolvimento", "Development Director",
                 HierarchyLevel.DIRECTOR, Department.DEVELOPMENT, "IT-VP-TECH",
                 ["Gestao de desenvolvimento", "Arquitetura", "Delivery"],
                 ["development", "architecture", "delivery", "agile"], 14),

    create_agent("DEV-SRMGR-BACK", "Gerente Senior de Backend", "Senior Backend Manager",
                 HierarchyLevel.SENIOR_MANAGER, Department.DEVELOPMENT, "DEV-DIR",
                 ["Backend", "APIs", "Microservices"],
                 ["backend", "api", "microservices", "leadership"], 12),

    create_agent("DEV-SRMGR-FRONT", "Gerente Senior de Frontend", "Senior Frontend Manager",
                 HierarchyLevel.SENIOR_MANAGER, Department.DEVELOPMENT, "DEV-DIR",
                 ["Frontend", "UX", "Performance"],
                 ["frontend", "ux", "performance", "leadership"], 12),

    create_agent("DEV-MGR-BACK", "Gerente de Backend", "Backend Manager",
                 HierarchyLevel.MANAGER, Department.DEVELOPMENT, "DEV-SRMGR-BACK",
                 ["Squad backend", "Sprints", "Code review"],
                 ["backend", "agile", "code_review"], 9),

    create_agent("DEV-MGR-FRONT", "Gerente de Frontend", "Frontend Manager",
                 HierarchyLevel.MANAGER, Department.DEVELOPMENT, "DEV-SRMGR-FRONT",
                 ["Squad frontend", "Components", "Design system"],
                 ["frontend", "components", "design_system"], 9),

    create_agent("DEV-MGR-MOBILE", "Gerente de Mobile", "Mobile Manager",
                 HierarchyLevel.MANAGER, Department.DEVELOPMENT, "DEV-DIR",
                 ["Apps mobile", "iOS", "Android"],
                 ["mobile", "ios", "android", "react_native"], 9),

    create_agent("DEV-COORD-BACK", "Coordenador Backend", "Backend Coordinator",
                 HierarchyLevel.COORDINATOR, Department.DEVELOPMENT, "DEV-MGR-BACK",
                 ["Coordenacao tecnica", "Mentoria", "Code standards"],
                 ["backend", "mentoring", "standards"], 7),

    create_agent("DEV-COORD-FRONT", "Coordenador Frontend", "Frontend Coordinator",
                 HierarchyLevel.COORDINATOR, Department.DEVELOPMENT, "DEV-MGR-FRONT",
                 ["Coordenacao tecnica", "Design system", "A11y"],
                 ["frontend", "design_system", "accessibility"], 7),

    create_agent("DEV-TL-BACK", "Tech Lead Backend", "Backend Tech Lead",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DEVELOPMENT, "DEV-COORD-BACK",
                 ["Lideranca tecnica", "Arquitetura", "Decisoes tecnicas"],
                 ["backend", "python", "nodejs", "architecture"], 8),

    create_agent("DEV-TL-FRONT", "Tech Lead Frontend", "Frontend Tech Lead",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DEVELOPMENT, "DEV-COORD-FRONT",
                 ["Lideranca tecnica", "React", "Performance"],
                 ["frontend", "react", "typescript", "performance"], 8),

    create_agent("DEV-SR-BACK", "Desenvolvedor Backend Senior", "Senior Backend Developer",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DEVELOPMENT, "DEV-TL-BACK",
                 ["Desenvolvimento backend", "APIs", "Banco de dados"],
                 ["python", "fastapi", "postgresql", "redis"], 6),

    create_agent("DEV-SR-FRONT", "Desenvolvedor Frontend Senior", "Senior Frontend Developer",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DEVELOPMENT, "DEV-TL-FRONT",
                 ["Desenvolvimento frontend", "React", "State management"],
                 ["react", "typescript", "redux", "testing"], 6),

    create_agent("DEV-PL-BACK", "Desenvolvedor Backend Pleno", "Backend Developer",
                 HierarchyLevel.ANALYST, Department.DEVELOPMENT, "DEV-SR-BACK",
                 ["Desenvolvimento", "Features", "Testes"],
                 ["python", "api", "testing", "git"], 3),

    create_agent("DEV-PL-FRONT", "Desenvolvedor Frontend Pleno", "Frontend Developer",
                 HierarchyLevel.ANALYST, Department.DEVELOPMENT, "DEV-SR-FRONT",
                 ["Desenvolvimento", "Componentes", "CSS"],
                 ["react", "javascript", "css", "testing"], 3),

    create_agent("DEV-JR-BACK", "Desenvolvedor Backend Junior", "Junior Backend Developer",
                 HierarchyLevel.ASSISTANT, Department.DEVELOPMENT, "DEV-PL-BACK",
                 ["Aprendizado", "Tarefas simples", "Suporte"],
                 ["python", "sql", "git"], 1),

    create_agent("DEV-JR-FRONT", "Desenvolvedor Frontend Junior", "Junior Frontend Developer",
                 HierarchyLevel.ASSISTANT, Department.DEVELOPMENT, "DEV-PL-FRONT",
                 ["Aprendizado", "Componentes simples", "CSS"],
                 ["html", "css", "javascript"], 1),

    create_agent("DEV-TRAINEE", "Trainee de Desenvolvimento", "Development Trainee",
                 HierarchyLevel.ASSISTANT, Department.DEVELOPMENT, "DEV-PL-BACK",
                 ["Programa trainee", "Rotacao", "Aprendizado"],
                 ["learning", "programming_basics"], 0),
]

# =============================================================================
# AGENTES - TI / DADOS
# =============================================================================

DATA_AGENTS = [
    create_agent("DATA-DIR", "Diretor de Dados", "Data Director",
                 HierarchyLevel.DIRECTOR, Department.DATA, "IT-VP-DATA",
                 ["Plataforma de dados", "Governanca", "Estrategia"],
                 ["data_platform", "governance", "strategy"], 14),

    create_agent("DATA-SRMGR-ENG", "Gerente Senior Data Engineering", "Senior Data Engineering Manager",
                 HierarchyLevel.SENIOR_MANAGER, Department.DATA, "DATA-DIR",
                 ["Data Engineering", "Pipelines", "Data Lake"],
                 ["data_engineering", "spark", "airflow"], 11),

    create_agent("DATA-SRMGR-BI", "Gerente Senior de BI", "Senior BI Manager",
                 HierarchyLevel.SENIOR_MANAGER, Department.DATA, "DATA-DIR",
                 ["BI", "Dashboards", "Self-service"],
                 ["bi", "power_bi", "tableau"], 11),

    create_agent("DATA-MGR-ENG", "Gerente de Data Engineering", "Data Engineering Manager",
                 HierarchyLevel.MANAGER, Department.DATA, "DATA-SRMGR-ENG",
                 ["Squad de dados", "ETL", "DW"],
                 ["data_engineering", "etl", "dw"], 9),

    create_agent("DATA-MGR-DS", "Gerente de Data Science", "Data Science Manager",
                 HierarchyLevel.MANAGER, Department.DATA, "DATA-DIR",
                 ["Data Science", "ML", "AI"],
                 ["data_science", "ml", "ai", "python"], 9),

    create_agent("DATA-MGR-BI", "Gerente de BI", "BI Manager",
                 HierarchyLevel.MANAGER, Department.DATA, "DATA-SRMGR-BI",
                 ["BI", "Reports", "Analytics"],
                 ["bi", "reporting", "analytics"], 9),

    create_agent("DATA-COORD", "Coordenador de Dados", "Data Coordinator",
                 HierarchyLevel.COORDINATOR, Department.DATA, "DATA-MGR-ENG",
                 ["Coordenacao de projetos", "Qualidade de dados"],
                 ["data_quality", "project_coordination"], 6),

    create_agent("DATA-TL-ENG", "Tech Lead Data Engineering", "Data Engineering Tech Lead",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DATA, "DATA-COORD",
                 ["Arquitetura de dados", "Best practices", "Mentoria"],
                 ["spark", "databricks", "aws", "architecture"], 7),

    create_agent("DATA-SR-ENG", "Data Engineer Senior", "Senior Data Engineer",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DATA, "DATA-TL-ENG",
                 ["Pipelines", "ETL", "Performance"],
                 ["python", "spark", "sql", "airflow"], 5),

    create_agent("DATA-SR-SCI", "Data Scientist Senior", "Senior Data Scientist",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DATA, "DATA-MGR-DS",
                 ["Modelos ML", "Analise avancada", "Experimentacao"],
                 ["python", "ml", "statistics", "deep_learning"], 5),

    create_agent("DATA-SR-AN", "Analista de BI Senior", "Senior BI Analyst",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DATA, "DATA-MGR-BI",
                 ["Dashboards avancados", "Self-service", "Governanca"],
                 ["power_bi", "sql", "dax", "data_modeling"], 5),

    create_agent("DATA-ENG", "Data Engineer", "Data Engineer",
                 HierarchyLevel.ANALYST, Department.DATA, "DATA-SR-ENG",
                 ["ETL", "Queries", "Pipelines"],
                 ["python", "sql", "etl"], 3),

    create_agent("DATA-SCI", "Data Scientist", "Data Scientist",
                 HierarchyLevel.ANALYST, Department.DATA, "DATA-SR-SCI",
                 ["Analise de dados", "ML", "Modelos"],
                 ["python", "ml", "pandas", "sklearn"], 3),

    create_agent("DATA-AN-BI", "Analista de BI", "BI Analyst",
                 HierarchyLevel.ANALYST, Department.DATA, "DATA-SR-AN",
                 ["Reports", "Dashboards", "Analises"],
                 ["power_bi", "sql", "excel"], 2),

    create_agent("DATA-JR", "Analista de Dados Junior", "Junior Data Analyst",
                 HierarchyLevel.ASSISTANT, Department.DATA, "DATA-ENG",
                 ["Suporte", "Queries basicas", "Reports"],
                 ["sql", "excel", "python_basics"], 1),
]

# =============================================================================
# AGENTES - TI / INFRAESTRUTURA
# =============================================================================

INFRA_AGENTS = [
    create_agent("INFRA-DIR", "Diretor de Infraestrutura", "Infrastructure Director",
                 HierarchyLevel.DIRECTOR, Department.INFRASTRUCTURE, "IT-VP-TECH",
                 ["Infraestrutura", "Cloud", "Datacenter"],
                 ["infrastructure", "cloud", "datacenter"], 14),

    create_agent("INFRA-SRMGR-CLOUD", "Gerente Senior de Cloud", "Senior Cloud Manager",
                 HierarchyLevel.SENIOR_MANAGER, Department.INFRASTRUCTURE, "INFRA-DIR",
                 ["Cloud computing", "AWS", "Azure", "GCP"],
                 ["aws", "azure", "gcp", "cloud_architecture"], 11),

    create_agent("INFRA-MGR-NET", "Gerente de Redes", "Network Manager",
                 HierarchyLevel.MANAGER, Department.INFRASTRUCTURE, "INFRA-DIR",
                 ["Redes", "Telecom", "Seguranca de rede"],
                 ["networking", "cisco", "firewall"], 9),

    create_agent("INFRA-MGR-DC", "Gerente de Datacenter", "Datacenter Manager",
                 HierarchyLevel.MANAGER, Department.INFRASTRUCTURE, "INFRA-DIR",
                 ["Datacenter", "Servidores", "Storage"],
                 ["datacenter", "servers", "storage", "vmware"], 9),

    create_agent("INFRA-COORD", "Coordenador de Infraestrutura", "Infrastructure Coordinator",
                 HierarchyLevel.COORDINATOR, Department.INFRASTRUCTURE, "INFRA-MGR-DC",
                 ["Coordenacao", "Projetos", "Capacidade"],
                 ["infrastructure", "capacity_planning"], 6),

    create_agent("INFRA-SR-CLOUD", "Especialista Cloud Senior", "Senior Cloud Specialist",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.INFRASTRUCTURE, "INFRA-SRMGR-CLOUD",
                 ["Arquitetura cloud", "Migracao", "FinOps"],
                 ["aws", "terraform", "kubernetes", "finops"], 6),

    create_agent("INFRA-SR-NET", "Especialista de Redes Senior", "Senior Network Specialist",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.INFRASTRUCTURE, "INFRA-MGR-NET",
                 ["Redes avancadas", "Security", "SD-WAN"],
                 ["networking", "security", "sdwan"], 6),

    create_agent("INFRA-AN-CLOUD", "Analista Cloud", "Cloud Analyst",
                 HierarchyLevel.ANALYST, Department.INFRASTRUCTURE, "INFRA-SR-CLOUD",
                 ["Cloud operations", "Monitoramento", "Custos"],
                 ["aws", "azure", "monitoring", "cost"], 3),

    create_agent("INFRA-AN-NET", "Analista de Redes", "Network Analyst",
                 HierarchyLevel.ANALYST, Department.INFRASTRUCTURE, "INFRA-SR-NET",
                 ["Suporte de redes", "Troubleshooting"],
                 ["networking", "troubleshooting"], 3),

    create_agent("INFRA-JR", "Analista de Infraestrutura Junior", "Junior Infrastructure Analyst",
                 HierarchyLevel.ASSISTANT, Department.INFRASTRUCTURE, "INFRA-AN-CLOUD",
                 ["Suporte", "Monitoramento basico"],
                 ["linux", "monitoring", "support"], 1),
]

# =============================================================================
# AGENTES - TI / SEGURANCA
# =============================================================================

SECURITY_AGENTS = [
    create_agent("SEC-CISO", "CISO", "Chief Information Security Officer",
                 HierarchyLevel.DIRECTOR, Department.SECURITY, "IT-CIO",
                 ["Seguranca da informacao", "Riscos", "Compliance"],
                 ["security", "risk_management", "compliance", "governance"], 15),

    create_agent("SEC-MGR-SOC", "Gerente de SOC", "SOC Manager",
                 HierarchyLevel.MANAGER, Department.SECURITY, "SEC-CISO",
                 ["Security Operations Center", "Incidentes", "SIEM"],
                 ["soc", "incident_response", "siem", "threat_hunting"], 10),

    create_agent("SEC-MGR-APPSEC", "Gerente de AppSec", "AppSec Manager",
                 HierarchyLevel.MANAGER, Department.SECURITY, "SEC-CISO",
                 ["Application Security", "SAST", "DAST", "DevSecOps"],
                 ["appsec", "devsecops", "sast", "dast"], 10),

    create_agent("SEC-COORD", "Coordenador de Seguranca", "Security Coordinator",
                 HierarchyLevel.COORDINATOR, Department.SECURITY, "SEC-MGR-SOC",
                 ["Coordenacao de seguranca", "Awareness", "Policies"],
                 ["security", "awareness", "policies"], 7),

    create_agent("SEC-SR-PENTEST", "Pentester Senior", "Senior Pentester",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.SECURITY, "SEC-MGR-APPSEC",
                 ["Penetration testing", "Vulnerability assessment"],
                 ["pentest", "vulnerability", "ethical_hacking"], 6),

    create_agent("SEC-SR-SOC", "Analista SOC Senior", "Senior SOC Analyst",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.SECURITY, "SEC-MGR-SOC",
                 ["Analise de ameacas", "Threat hunting", "Forensics"],
                 ["soc", "threat_hunting", "forensics", "siem"], 6),

    create_agent("SEC-AN-SOC", "Analista SOC", "SOC Analyst",
                 HierarchyLevel.ANALYST, Department.SECURITY, "SEC-SR-SOC",
                 ["Monitoramento", "Alertas", "Incidentes"],
                 ["soc", "monitoring", "incident_response"], 3),

    create_agent("SEC-AN-APPSEC", "Analista de AppSec", "AppSec Analyst",
                 HierarchyLevel.ANALYST, Department.SECURITY, "SEC-SR-PENTEST",
                 ["Code review", "Scan de vulnerabilidades"],
                 ["appsec", "code_review", "scanning"], 3),

    create_agent("SEC-JR", "Analista de Seguranca Junior", "Junior Security Analyst",
                 HierarchyLevel.ASSISTANT, Department.SECURITY, "SEC-AN-SOC",
                 ["Suporte", "Monitoramento basico"],
                 ["security", "monitoring"], 1),
]

# =============================================================================
# AGENTES - TI / QA
# =============================================================================

QA_AGENTS = [
    create_agent("QA-DIR", "Diretor de Qualidade", "QA Director",
                 HierarchyLevel.DIRECTOR, Department.QA, "IT-VP-TECH",
                 ["Estrategia de qualidade", "Automacao", "Processos"],
                 ["qa", "automation", "quality_strategy"], 14),

    create_agent("QA-MGR", "Gerente de QA", "QA Manager",
                 HierarchyLevel.MANAGER, Department.QA, "QA-DIR",
                 ["Gestao de QA", "Test planning", "Metricas"],
                 ["qa", "test_planning", "metrics"], 10),

    create_agent("QA-MGR-AUTO", "Gerente de Automacao", "Automation Manager",
                 HierarchyLevel.MANAGER, Department.QA, "QA-DIR",
                 ["Automacao de testes", "Frameworks", "CI/CD integration"],
                 ["automation", "selenium", "cypress", "ci_cd"], 10),

    create_agent("QA-COORD", "Coordenador de QA", "QA Coordinator",
                 HierarchyLevel.COORDINATOR, Department.QA, "QA-MGR",
                 ["Coordenacao de testes", "Releases", "Qualidade"],
                 ["qa", "test_coordination", "releases"], 6),

    create_agent("QA-TL", "Tech Lead de Automacao", "Automation Tech Lead",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.QA, "QA-MGR-AUTO",
                 ["Arquitetura de testes", "Frameworks", "Best practices"],
                 ["automation", "framework_design", "best_practices"], 7),

    create_agent("QA-SR", "QA Senior", "Senior QA",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.QA, "QA-COORD",
                 ["Testes avancados", "Performance", "Integracao"],
                 ["qa", "performance_testing", "integration"], 5),

    create_agent("QA-AN", "Analista de QA", "QA Analyst",
                 HierarchyLevel.ANALYST, Department.QA, "QA-SR",
                 ["Testes funcionais", "Regressao", "Bugs"],
                 ["qa", "functional_testing", "bug_tracking"], 3),

    create_agent("QA-AUTO", "Analista de Automacao", "Automation Analyst",
                 HierarchyLevel.ANALYST, Department.QA, "QA-TL",
                 ["Automacao de testes", "Scripts", "CI"],
                 ["automation", "selenium", "cypress"], 3),

    create_agent("QA-JR", "QA Junior", "Junior QA",
                 HierarchyLevel.ASSISTANT, Department.QA, "QA-AN",
                 ["Testes manuais", "Documentacao", "Suporte"],
                 ["qa", "manual_testing", "documentation"], 1),
]

# =============================================================================
# AGENTES - TI / DEVOPS
# =============================================================================

DEVOPS_AGENTS = [
    create_agent("DEVOPS-DIR", "Diretor de DevOps/SRE", "DevOps/SRE Director",
                 HierarchyLevel.DIRECTOR, Department.DEVOPS, "IT-VP-TECH",
                 ["DevOps", "SRE", "Platform Engineering"],
                 ["devops", "sre", "platform_engineering"], 14),

    create_agent("DEVOPS-SRMGR", "Gerente Senior de DevOps", "Senior DevOps Manager",
                 HierarchyLevel.SENIOR_MANAGER, Department.DEVOPS, "DEVOPS-DIR",
                 ["DevOps practices", "CI/CD", "Automacao"],
                 ["devops", "ci_cd", "automation", "kubernetes"], 11),

    create_agent("DEVOPS-MGR", "Gerente de DevOps", "DevOps Manager",
                 HierarchyLevel.MANAGER, Department.DEVOPS, "DEVOPS-SRMGR",
                 ["Squad DevOps", "Pipelines", "Releases"],
                 ["devops", "pipelines", "releases"], 9),

    create_agent("DEVOPS-MGR-SRE", "Gerente de SRE", "SRE Manager",
                 HierarchyLevel.MANAGER, Department.DEVOPS, "DEVOPS-SRMGR",
                 ["Site Reliability", "Observability", "Incident management"],
                 ["sre", "observability", "incident_management"], 9),

    create_agent("DEVOPS-COORD", "Coordenador de DevOps", "DevOps Coordinator",
                 HierarchyLevel.COORDINATOR, Department.DEVOPS, "DEVOPS-MGR",
                 ["Coordenacao", "Releases", "Change management"],
                 ["devops", "releases", "change_management"], 6),

    create_agent("DEVOPS-TL", "Tech Lead DevOps", "DevOps Tech Lead",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DEVOPS, "DEVOPS-COORD",
                 ["Arquitetura DevOps", "IaC", "K8s"],
                 ["kubernetes", "terraform", "helm", "argocd"], 7),

    create_agent("DEVOPS-SR-SRE", "SRE Senior", "Senior SRE",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.DEVOPS, "DEVOPS-MGR-SRE",
                 ["Reliability", "Monitoring", "On-call"],
                 ["sre", "prometheus", "grafana", "elk"], 6),

    create_agent("DEVOPS-ENG", "DevOps Engineer", "DevOps Engineer",
                 HierarchyLevel.ANALYST, Department.DEVOPS, "DEVOPS-TL",
                 ["CI/CD", "Containers", "Automacao"],
                 ["docker", "kubernetes", "jenkins", "github_actions"], 3),

    create_agent("DEVOPS-SRE", "SRE", "Site Reliability Engineer",
                 HierarchyLevel.ANALYST, Department.DEVOPS, "DEVOPS-SR-SRE",
                 ["Monitoramento", "Alertas", "Troubleshooting"],
                 ["monitoring", "alerting", "troubleshooting"], 3),

    create_agent("DEVOPS-JR", "DevOps Junior", "Junior DevOps",
                 HierarchyLevel.ASSISTANT, Department.DEVOPS, "DEVOPS-ENG",
                 ["Suporte", "Scripts", "Aprendizado"],
                 ["linux", "scripting", "docker"], 1),
]

# =============================================================================
# AGENTES - TI / ARQUITETURA
# =============================================================================

ARCHITECTURE_AGENTS = [
    create_agent("ARCH-DIR", "Diretor de Arquitetura", "Architecture Director",
                 HierarchyLevel.DIRECTOR, Department.ARCHITECTURE, "IT-VP-TECH",
                 ["Arquitetura enterprise", "Governanca", "Padroes"],
                 ["enterprise_architecture", "governance", "standards"], 15),

    create_agent("ARCH-MGR", "Gerente de Arquitetura", "Architecture Manager",
                 HierarchyLevel.MANAGER, Department.ARCHITECTURE, "ARCH-DIR",
                 ["Arquitetura de solucoes", "Design review"],
                 ["solution_architecture", "design_review"], 12),

    create_agent("ARCH-SR-SOL", "Arquiteto de Solucoes Senior", "Senior Solutions Architect",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.ARCHITECTURE, "ARCH-MGR",
                 ["Arquitetura de solucoes", "Integracao", "Cloud"],
                 ["solutions", "integration", "cloud", "microservices"], 10),

    create_agent("ARCH-SR-DATA", "Arquiteto de Dados Senior", "Senior Data Architect",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.ARCHITECTURE, "ARCH-MGR",
                 ["Arquitetura de dados", "Data modeling", "Governanca"],
                 ["data_architecture", "data_modeling", "governance"], 10),

    create_agent("ARCH-SOL", "Arquiteto de Solucoes", "Solutions Architect",
                 HierarchyLevel.ANALYST, Department.ARCHITECTURE, "ARCH-SR-SOL",
                 ["Design", "Documentacao", "POCs"],
                 ["design", "documentation", "pocs"], 5),

    create_agent("ARCH-DATA", "Arquiteto de Dados", "Data Architect",
                 HierarchyLevel.ANALYST, Department.ARCHITECTURE, "ARCH-SR-DATA",
                 ["Modelagem", "Documentacao", "Standards"],
                 ["data_modeling", "documentation", "standards"], 5),
]

# =============================================================================
# AGENTES - TI / SUPORTE
# =============================================================================

SUPPORT_AGENTS = [
    create_agent("SUP-MGR", "Gerente de Suporte", "Support Manager",
                 HierarchyLevel.MANAGER, Department.IT_SUPPORT, "INFRA-DIR",
                 ["Service Desk", "ITSM", "Atendimento"],
                 ["itsm", "service_desk", "itil"], 10),

    create_agent("SUP-COORD", "Coordenador de Suporte", "Support Coordinator",
                 HierarchyLevel.COORDINATOR, Department.IT_SUPPORT, "SUP-MGR",
                 ["Coordenacao de chamados", "Escalacao", "SLA"],
                 ["support", "ticketing", "sla"], 6),

    create_agent("SUP-SR", "Analista de Suporte Senior", "Senior Support Analyst",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.IT_SUPPORT, "SUP-COORD",
                 ["Suporte N2/N3", "Troubleshooting avancado"],
                 ["support", "troubleshooting", "systems"], 5),

    create_agent("SUP-AN", "Analista de Suporte", "Support Analyst",
                 HierarchyLevel.ANALYST, Department.IT_SUPPORT, "SUP-SR",
                 ["Suporte N1/N2", "Atendimento", "Resolucao"],
                 ["support", "helpdesk", "troubleshooting"], 3),

    create_agent("SUP-JR", "Analista de Suporte Junior", "Junior Support Analyst",
                 HierarchyLevel.ASSISTANT, Department.IT_SUPPORT, "SUP-AN",
                 ["Suporte N1", "Atendimento basico"],
                 ["support", "helpdesk"], 1),
]

# =============================================================================
# AGENTES - TI / PMO
# =============================================================================

PMO_AGENTS = [
    create_agent("PMO-DIR", "Diretor de PMO", "PMO Director",
                 HierarchyLevel.DIRECTOR, Department.PMO, "IT-CIO",
                 ["Portfolio", "Governanca de projetos", "PMO"],
                 ["pmo", "portfolio", "governance"], 14),

    create_agent("PMO-MGR", "Gerente de Projetos Senior", "Senior Project Manager",
                 HierarchyLevel.MANAGER, Department.PMO, "PMO-DIR",
                 ["Gestao de projetos", "PMO", "Metodologias"],
                 ["project_management", "pmo", "agile", "waterfall"], 10),

    create_agent("PMO-COORD", "Coordenador de Projetos", "Project Coordinator",
                 HierarchyLevel.COORDINATOR, Department.PMO, "PMO-MGR",
                 ["Coordenacao", "Planning", "Tracking"],
                 ["project_coordination", "planning", "tracking"], 6),

    create_agent("PMO-PM", "Gerente de Projetos", "Project Manager",
                 HierarchyLevel.SENIOR_SPECIALIST, Department.PMO, "PMO-MGR",
                 ["Gestao de projetos", "Stakeholders", "Riscos"],
                 ["project_management", "stakeholders", "risks"], 5),

    create_agent("PMO-AN", "Analista de PMO", "PMO Analyst",
                 HierarchyLevel.ANALYST, Department.PMO, "PMO-COORD",
                 ["Reports", "KPIs", "Documentacao"],
                 ["reporting", "kpis", "documentation"], 3),
]

# =============================================================================
# COLECAO DE TODOS OS AGENTES CORPORATIVOS
# =============================================================================

ALL_CORPORATE_AGENTS: Dict[str, CorporateAgent] = {}

# Adiciona todos os agentes
for agents_list in [
    EXECUTIVE_AGENTS, FINANCE_AGENTS, SALES_AGENTS, MARKETING_AGENTS,
    HR_AGENTS, OPERATIONS_AGENTS, IT_MANAGEMENT_AGENTS, DEV_AGENTS,
    DATA_AGENTS, INFRA_AGENTS, SECURITY_AGENTS, QA_AGENTS,
    DEVOPS_AGENTS, ARCHITECTURE_AGENTS, SUPPORT_AGENTS, PMO_AGENTS
]:
    for agent in agents_list:
        ALL_CORPORATE_AGENTS[agent.agent_id] = agent

# Preenche direct_reports baseado em reports_to
for agent_id, agent in ALL_CORPORATE_AGENTS.items():
    if agent.reports_to and agent.reports_to in ALL_CORPORATE_AGENTS:
        superior = ALL_CORPORATE_AGENTS[agent.reports_to]
        if agent_id not in superior.direct_reports:
            superior.direct_reports.append(agent_id)


# =============================================================================
# SISTEMA DE APROVACAO HIERARQUICA
# =============================================================================

class HierarchyApprovalSystem:
    """Sistema de aprovacao baseado em hierarquia corporativa"""

    def __init__(self):
        self.agents = ALL_CORPORATE_AGENTS
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []
        self._request_counter = 0

    def create_request(
        self,
        requester_id: str,
        decision_type: DecisionType,
        title: str,
        description: str,
        estimated_cost: float = 0,
        priority: int = 5,
        context: Dict = None
    ) -> ApprovalRequest:
        """Cria uma nova solicitacao de aprovacao"""
        if requester_id not in self.agents:
            raise ValueError(f"Agente {requester_id} nao encontrado")

        requester = self.agents[requester_id]
        approver_id = self._find_approver(requester, decision_type, estimated_cost)

        self._request_counter += 1
        request = ApprovalRequest(
            request_id=f"REQ-{self._request_counter:05d}",
            requester_id=requester_id,
            approver_id=approver_id,
            decision_type=decision_type,
            title=title,
            description=description,
            estimated_cost=estimated_cost,
            priority=priority,
            context=context or {},
            escalation_chain=[requester_id]
        )

        self.pending_requests[request.request_id] = request
        return request

    def _find_approver(
        self,
        requester: CorporateAgent,
        decision_type: DecisionType,
        estimated_cost: float
    ) -> str:
        """Encontra o aprovador apropriado"""
        current = requester

        while current.reports_to:
            superior = self.agents.get(current.reports_to)
            if not superior:
                break

            can_approve, _ = superior.can_approve(
                ApprovalRequest(
                    request_id="temp",
                    requester_id=requester.agent_id,
                    approver_id=superior.agent_id,
                    decision_type=decision_type,
                    title="",
                    description="",
                    estimated_cost=estimated_cost
                )
            )

            if can_approve:
                return superior.agent_id
            current = superior

        return "EXEC-CEO"

    def process_approval(
        self,
        request_id: str,
        approver_id: str,
        action: ApprovalStatus,
        response: str = "",
        conditions: List[str] = None
    ) -> bool:
        """Processa uma aprovacao"""
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests[request_id]
        if request.approver_id != approver_id:
            return False

        request.status = action
        request.response = response
        request.conditions = conditions or []
        request.resolved_at = datetime.now()

        del self.pending_requests[request_id]
        self.approval_history.append(request)

        return True

    def escalate(self, request_id: str) -> bool:
        """Escala para o proximo nivel"""
        if request_id not in self.pending_requests:
            return False

        request = self.pending_requests[request_id]
        current_approver = self.agents.get(request.approver_id)

        if not current_approver or not current_approver.reports_to:
            return False

        request.escalation_chain.append(request.approver_id)
        request.approver_id = current_approver.reports_to
        request.status = ApprovalStatus.ESCALATED

        return True

    def get_org_chart(self) -> Dict:
        """Retorna organograma completo"""
        def build_tree(agent_id: str) -> Dict:
            agent = self.agents.get(agent_id)
            if not agent:
                return {}

            return {
                "id": agent.agent_id,
                "name": agent.name,
                "title": agent.title,
                "level": agent.level.title,
                "department": agent.department.display_name,
                "area": agent.department.area,
                "status": agent.status.value,
                "metrics": agent.metrics.to_dict(),
                "direct_reports": [
                    build_tree(sub_id) for sub_id in agent.direct_reports
                ]
            }

        return build_tree("EXEC-CEO")

    def get_statistics(self) -> Dict:
        """Retorna estatisticas do sistema"""
        agents_by_level = {}
        agents_by_department = {}
        agents_by_area = {"business": 0, "technology": 0}
        agents_by_status = {}

        for agent in self.agents.values():
            level = agent.level.title
            dept = agent.department.display_name
            area = agent.department.area
            status = agent.status.value

            agents_by_level[level] = agents_by_level.get(level, 0) + 1
            agents_by_department[dept] = agents_by_department.get(dept, 0) + 1
            agents_by_area[area] = agents_by_area.get(area, 0) + 1
            agents_by_status[status] = agents_by_status.get(status, 0) + 1

        return {
            "total_agents": len(self.agents),
            "by_level": agents_by_level,
            "by_department": agents_by_department,
            "by_area": agents_by_area,
            "by_status": agents_by_status,
            "pending_requests": len(self.pending_requests),
            "total_processed": len(self.approval_history)
        }


# =============================================================================
# FUNCOES AUXILIARES
# =============================================================================

def get_agent(agent_id: str) -> Optional[CorporateAgent]:
    """Obtem um agente pelo ID"""
    return ALL_CORPORATE_AGENTS.get(agent_id)


def get_all_agents() -> List[CorporateAgent]:
    """Retorna lista de todos os agentes"""
    return list(ALL_CORPORATE_AGENTS.values())


def get_agents_by_department(department: Department) -> List[CorporateAgent]:
    """Obtem agentes de um departamento"""
    return [a for a in ALL_CORPORATE_AGENTS.values() if a.department == department]


def get_agents_by_level(level: HierarchyLevel) -> List[CorporateAgent]:
    """Obtem agentes de um nivel hierarquico"""
    return [a for a in ALL_CORPORATE_AGENTS.values() if a.level == level]


def get_agents_by_area(area: str) -> List[CorporateAgent]:
    """Obtem agentes por area (business ou technology)"""
    return [a for a in ALL_CORPORATE_AGENTS.values() if a.department.area == area]


def get_agents_by_status(status: AgentStatus) -> List[CorporateAgent]:
    """Obtem agentes por status"""
    return [a for a in ALL_CORPORATE_AGENTS.values() if a.status == status]


def get_superior(agent_id: str) -> Optional[CorporateAgent]:
    """Obtem o superior de um agente"""
    agent = ALL_CORPORATE_AGENTS.get(agent_id)
    if agent and agent.reports_to:
        return ALL_CORPORATE_AGENTS.get(agent.reports_to)
    return None


def get_subordinates(agent_id: str, recursive: bool = False) -> List[CorporateAgent]:
    """Retorna subordinados de um agente"""
    agent = ALL_CORPORATE_AGENTS.get(agent_id)
    if not agent:
        return []

    subordinates = [ALL_CORPORATE_AGENTS[sid] for sid in agent.direct_reports if sid in ALL_CORPORATE_AGENTS]

    if recursive:
        for sub in list(subordinates):
            subordinates.extend(get_subordinates(sub.agent_id, recursive=True))

    return subordinates


def search_agents(query: str) -> List[CorporateAgent]:
    """Busca agentes por nome, titulo ou skills"""
    query = query.lower()
    results = []

    for agent in ALL_CORPORATE_AGENTS.values():
        if (query in agent.name.lower() or
            query in agent.title.lower() or
            any(query in skill.lower() for skill in agent.skills) or
            any(query in resp.lower() for resp in agent.responsibilities)):
            results.append(agent)

    return results


def get_hierarchy_statistics() -> Dict:
    """Estatisticas completas da hierarquia"""
    system = HierarchyApprovalSystem()
    return system.get_statistics()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "HierarchyLevel",
    "Department",
    "DecisionType",
    "ApprovalStatus",
    "AgentStatus",
    "ApprovalRequest",
    "WorkMetrics",
    "CorporateAgent",
    "HierarchyApprovalSystem",
    "ALL_CORPORATE_AGENTS",
    "get_agent",
    "get_all_agents",
    "get_agents_by_department",
    "get_agents_by_level",
    "get_agents_by_area",
    "get_agents_by_status",
    "get_superior",
    "get_subordinates",
    "search_agents",
    "get_hierarchy_statistics",
]
