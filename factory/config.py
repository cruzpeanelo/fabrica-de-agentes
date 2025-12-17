"""
Configuracoes da Fabrica de Agentes
Sistema generico para construcao de multiplas aplicacoes
"""
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, field
from enum import Enum

# =============================================================================
# PATHS
# =============================================================================

# Diretorio raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Diretorios principais
FACTORY_DIR = PROJECT_ROOT / "factory"
PROJECTS_DIR = PROJECT_ROOT / "projects"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Subdiretorios da fabrica
DATABASE_DIR = FACTORY_DIR / "database"
DASHBOARD_DIR = FACTORY_DIR / "dashboard"
SKILLS_DIR = FACTORY_DIR / "skills"
AGENTS_DIR = FACTORY_DIR / "agents"
CORE_DIR = FACTORY_DIR / "core"

# Arquivos importantes
FACTORY_DB = DATABASE_DIR / "factory.db"

# =============================================================================
# TIMING
# =============================================================================

CYCLE_INTERVAL = 60          # Intervalo entre ciclos (segundos)
WATCHER_INTERVAL = 5         # Monitor de arquivos (segundos)
AGENT_TIMEOUT = 300          # Timeout agente (5 minutos)
SNAPSHOT_INTERVAL = 600      # Snapshot automatico (10 minutos)

# =============================================================================
# CONTEXT & MEMORY
# =============================================================================

CONTEXT_TOKEN_LIMIT = 150000     # Limite de tokens (Claude ~200k)
AUTO_COMPACT_THRESHOLD = 0.80    # Compactacao em 80%
MAX_SNAPSHOTS = 10               # Maximo de snapshots
MAX_LOG_SIZE_MB = 10             # Log maximo antes de arquivar

# =============================================================================
# ERROR HANDLING
# =============================================================================

MAX_CONSECUTIVE_ERRORS = 3       # Erros antes de pausar
MAX_BLOCK_TIME = 3600            # Bloqueio maximo (1 hora)
ERROR_RETRY_DELAY = 30           # Delay apos erro

# =============================================================================
# AGENTS - Dominios e Configuracoes
# =============================================================================

class AgentDomain(Enum):
    """Dominios dos agentes"""
    MANAGEMENT = "management"      # Gestao e planejamento
    DEVELOPMENT = "development"    # Desenvolvimento de software
    DATA = "data"                  # Dados e analise
    DESIGN = "design"              # Design e UX
    QUALITY = "quality"            # Qualidade e testes
    INFRASTRUCTURE = "infrastructure"  # DevOps e infra
    DOCUMENTATION = "documentation"    # Documentacao
    INTEGRATION = "integration"    # Integracoes


@dataclass
class AgentConfig:
    """Configuracao de um agente"""
    id: str
    name: str
    domain: AgentDomain
    role: str = ""
    enabled: bool = True
    priority: int = 5
    can_run_parallel: bool = True
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)


# =============================================================================
# AGENTS - 19 Agentes Genericos
# =============================================================================

AGENTS: Dict[str, AgentConfig] = {
    # MANAGEMENT (01-04)
    "01": AgentConfig(
        id="01",
        name="Gestao Estrategica",
        domain=AgentDomain.MANAGEMENT,
        role="Orquestrador Principal",
        priority=10,
        can_run_parallel=False,
        capabilities=["planning", "decision", "coordination", "okr"],
        skills=["project_management", "strategic_planning"]
    ),
    "02": AgentConfig(
        id="02",
        name="Product Manager",
        domain=AgentDomain.MANAGEMENT,
        role="Gerente de Produto",
        priority=9,
        dependencies=["01"],
        capabilities=["roadmap", "prioritization", "market_analysis"],
        skills=["product_strategy", "user_research"]
    ),
    "03": AgentConfig(
        id="03",
        name="Product Owner",
        domain=AgentDomain.MANAGEMENT,
        role="Dono do Produto",
        priority=9,
        dependencies=["01", "02"],
        capabilities=["backlog", "stories", "acceptance_criteria"],
        skills=["agile", "user_stories"]
    ),
    "04": AgentConfig(
        id="04",
        name="Project Manager",
        domain=AgentDomain.MANAGEMENT,
        role="Gerente de Projeto",
        priority=8,
        dependencies=["03"],
        capabilities=["sprint_planning", "risk_management", "tracking"],
        skills=["scrum", "kanban", "project_tracking"]
    ),

    # DATA (05-07)
    "05": AgentConfig(
        id="05",
        name="Analista de Dados",
        domain=AgentDomain.DATA,
        role="Analista de Dados",
        priority=7,
        dependencies=["03"],
        capabilities=["data_analysis", "sql", "visualization", "kpi"],
        skills=["sql", "pandas", "data_visualization"]
    ),
    "06": AgentConfig(
        id="06",
        name="Engenheiro de Dados",
        domain=AgentDomain.DATA,
        role="Engenheiro de Dados",
        priority=7,
        dependencies=["07"],
        capabilities=["etl", "pipeline", "data_validation"],
        skills=["etl", "data_pipeline", "data_quality"]
    ),
    "07": AgentConfig(
        id="07",
        name="Especialista BD",
        domain=AgentDomain.DATA,
        role="DBA",
        priority=8,
        capabilities=["schema_design", "optimization", "indexing"],
        skills=["sql", "database_design", "performance_tuning"]
    ),

    # DEVELOPMENT (08-10)
    "08": AgentConfig(
        id="08",
        name="Especialista Backend",
        domain=AgentDomain.DEVELOPMENT,
        role="Desenvolvedor Backend",
        priority=7,
        dependencies=["03", "07"],
        capabilities=["api", "services", "backend_logic"],
        skills=["python", "fastapi", "nodejs", "rest_api"]
    ),
    "09": AgentConfig(
        id="09",
        name="Desenvolvedor Frontend",
        domain=AgentDomain.DEVELOPMENT,
        role="Desenvolvedor Frontend",
        priority=7,
        dependencies=["03", "08", "12"],
        capabilities=["components", "pages", "ui_integration"],
        skills=["react", "typescript", "css", "html"]
    ),
    "10": AgentConfig(
        id="10",
        name="Especialista Seguranca",
        domain=AgentDomain.DEVELOPMENT,
        role="Security Engineer",
        priority=6,
        dependencies=["08"],
        capabilities=["security_audit", "auth", "vulnerability"],
        skills=["security", "authentication", "encryption"]
    ),

    # DESIGN (11-12)
    "11": AgentConfig(
        id="11",
        name="Especialista UX",
        domain=AgentDomain.DESIGN,
        role="UX Designer",
        priority=6,
        dependencies=["03"],
        capabilities=["wireframe", "user_flow", "ux_research"],
        skills=["ux_design", "user_research", "prototyping"]
    ),
    "12": AgentConfig(
        id="12",
        name="Especialista UI",
        domain=AgentDomain.DESIGN,
        role="UI Designer",
        priority=6,
        dependencies=["11"],
        capabilities=["design_system", "visual_design", "branding"],
        skills=["ui_design", "figma", "design_tokens"]
    ),

    # QUALITY (13, 15-16)
    "13": AgentConfig(
        id="13",
        name="Revisor de Codigo",
        domain=AgentDomain.QUALITY,
        role="Code Reviewer",
        priority=8,
        dependencies=["08", "09"],
        capabilities=["code_review", "best_practices", "refactoring"],
        skills=["code_review", "clean_code", "patterns"]
    ),
    "15": AgentConfig(
        id="15",
        name="Testador QA",
        domain=AgentDomain.QUALITY,
        role="QA Engineer",
        priority=8,
        dependencies=["08", "09"],
        capabilities=["testing", "test_automation", "quality"],
        skills=["pytest", "jest", "testing"]
    ),
    "16": AgentConfig(
        id="16",
        name="Testador E2E",
        domain=AgentDomain.QUALITY,
        role="E2E Test Engineer",
        priority=7,
        dependencies=["15"],
        capabilities=["e2e_testing", "browser_automation"],
        skills=["playwright", "cypress", "selenium"]
    ),

    # INFRASTRUCTURE (14)
    "14": AgentConfig(
        id="14",
        name="Engenheiro DevOps",
        domain=AgentDomain.INFRASTRUCTURE,
        role="DevOps Engineer",
        priority=6,
        dependencies=["08"],
        capabilities=["ci_cd", "deployment", "monitoring"],
        skills=["docker", "kubernetes", "github_actions"]
    ),

    # DOCUMENTATION (17)
    "17": AgentConfig(
        id="17",
        name="Documentador",
        domain=AgentDomain.DOCUMENTATION,
        role="Technical Writer",
        priority=5,
        dependencies=["08", "09"],
        capabilities=["documentation", "api_docs", "guides"],
        skills=["markdown", "openapi", "technical_writing"]
    ),

    # INTEGRATION (18-19)
    "18": AgentConfig(
        id="18",
        name="Arquiteto",
        domain=AgentDomain.INTEGRATION,
        role="Solution Architect",
        priority=9,
        dependencies=["01"],
        capabilities=["architecture", "design_patterns", "integration"],
        skills=["architecture", "system_design", "patterns"]
    ),
    "19": AgentConfig(
        id="19",
        name="Integrador",
        domain=AgentDomain.INTEGRATION,
        role="Integration Specialist",
        priority=6,
        dependencies=["08", "18"],
        capabilities=["api_integration", "data_sync", "connectors"],
        skills=["api_integration", "webhooks", "messaging"]
    ),
}

# Lista de IDs de agentes habilitados
AGENTS_ENABLED = list(AGENTS.keys())

# =============================================================================
# PROJECT TYPES - Tipos de Projetos Suportados
# =============================================================================

PROJECT_TYPES = {
    "web-app": {
        "name": "Aplicacao Web",
        "description": "Aplicacao web fullstack com frontend e backend",
        "default_agents": ["01", "02", "03", "04", "08", "09", "11", "12", "15"],
        "default_stack": {"frontend": "react", "backend": "fastapi", "database": "sqlite"}
    },
    "api-service": {
        "name": "API Service",
        "description": "Servico de API REST ou GraphQL",
        "default_agents": ["01", "03", "04", "07", "08", "10", "15"],
        "default_stack": {"backend": "fastapi", "database": "postgresql"}
    },
    "data-analysis": {
        "name": "Analise de Dados",
        "description": "Projeto de analise e visualizacao de dados",
        "default_agents": ["01", "03", "05", "06", "07"],
        "default_stack": {"tools": "pandas", "database": "sqlite", "viz": "plotly"}
    },
    "document": {
        "name": "Documento",
        "description": "Geracao de documentos, relatorios ou manuais",
        "default_agents": ["01", "03", "17"],
        "default_stack": {"format": "markdown", "output": "pdf"}
    },
    "automation": {
        "name": "Automacao",
        "description": "Scripts e automacoes de tarefas",
        "default_agents": ["01", "03", "08", "14", "19"],
        "default_stack": {"language": "python", "scheduler": "cron"}
    },
    "integration": {
        "name": "Integracao",
        "description": "Integracoes entre sistemas e APIs",
        "default_agents": ["01", "03", "08", "18", "19"],
        "default_stack": {"protocol": "rest", "messaging": "rabbitmq"}
    }
}

# =============================================================================
# SKILLS - Categorias de Skills
# =============================================================================

SKILL_CATEGORIES = {
    "file": "Operacoes de arquivo (leitura, escrita, busca)",
    "web": "Operacoes web (fetch, scraping, API calls)",
    "data": "Processamento de dados (pandas, SQL, transformacao)",
    "ai": "Inteligencia artificial (LLM, embeddings, RAG)",
    "browser": "Automacao de browser (Playwright, Selenium)",
    "integration": "Integracoes (APIs, webhooks, messaging)",
    "development": "Desenvolvimento (git, npm, pip, build)",
    "documentation": "Documentacao (markdown, PDF, diagrams)"
}

# =============================================================================
# MCP SERVERS - Servidores MCP Disponiveis
# =============================================================================

MCP_SERVERS = {
    "playwright": {
        "name": "Playwright MCP",
        "description": "Automacao de browser com Playwright",
        "command": "npx",
        "args": ["@anthropic/mcp-server-playwright"],
        "category": "browser"
    },
    "filesystem": {
        "name": "Filesystem MCP",
        "description": "Operacoes avancadas de filesystem",
        "command": "npx",
        "args": ["@anthropic/mcp-server-filesystem"],
        "category": "file"
    },
    "github": {
        "name": "GitHub MCP",
        "description": "Integracao com GitHub",
        "command": "npx",
        "args": ["@anthropic/mcp-server-github"],
        "category": "integration"
    },
    "memory": {
        "name": "Memory MCP",
        "description": "Memoria persistente para agentes",
        "command": "npx",
        "args": ["@anthropic/mcp-server-memory"],
        "category": "ai"
    }
}

# =============================================================================
# HOOKS & INTEGRATIONS
# =============================================================================

# Claude CLI
CLAUDE_CLI_PATH = r"C:\Users\lcruz\AppData\Roaming\npm\claude.cmd"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# MCP
MCP_ENABLED = True

# Playwright
PLAYWRIGHT_ENABLED = True
PLAYWRIGHT_BROWSER = "chromium"
PLAYWRIGHT_HEADLESS = True

# =============================================================================
# LOGGING
# =============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
LOG_ROTATION = "10 MB"
LOG_RETENTION = "7 days"

# =============================================================================
# API (Dashboard)
# =============================================================================

DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 9000
DASHBOARD_TITLE = "Fabrica de Agentes"

# =============================================================================
# PAUSE CONDITIONS
# =============================================================================

class PauseCondition(Enum):
    """Condicoes que disparam pausa automatica"""
    CRITICAL_DECISION = "critical_decision"
    AGENT_BLOCKED = "agent_blocked"
    CONSECUTIVE_ERRORS = "consecutive_errors"
    FILE_CONFLICT = "file_conflict"
    CONTEXT_OVERFLOW = "context_overflow"
    MANUAL_PAUSE = "manual_pause"

PAUSE_FILE = FACTORY_DIR / ".pause"
STOP_FILE = FACTORY_DIR / ".stop"
