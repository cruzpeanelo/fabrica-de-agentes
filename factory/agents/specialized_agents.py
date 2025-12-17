"""
Agentes Especializados
======================

Configuracao de agentes especializados em tecnologias especificas:
- Frontend (React, Vue, Angular, etc.)
- Backend (Python, Node.js, Java, etc.)
- SAP ECC (por modulos)
- Migracao SAP ECC para S/4 HANA
- SAP S/4 HANA
- Salesforce
- Marketing Cloud
- Power BI
- Azure
- Databricks
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class TechnologyDomain(str, Enum):
    """Dominios de tecnologia"""
    # Desenvolvimento
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"
    MOBILE = "mobile"

    # SAP
    SAP_ECC = "sap_ecc"
    SAP_S4 = "sap_s4"
    SAP_MIGRATION = "sap_migration"

    # CRM & Marketing
    SALESFORCE = "salesforce"
    MARKETING_CLOUD = "marketing_cloud"

    # Data & Analytics
    POWER_BI = "power_bi"
    DATABRICKS = "databricks"
    DATA_ENGINEERING = "data_engineering"

    # Cloud
    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"


@dataclass
class AgentSpecialization:
    """Especializacao de um agente"""
    agent_id: str
    name: str
    domain: TechnologyDomain
    description: str
    technologies: List[str]
    skills: List[str]
    knowledge_areas: List[str]
    certifications: List[str] = field(default_factory=list)
    experience_level: str = "senior"  # junior, mid, senior, expert


# ============================================================
# AGENTES DE FRONTEND
# ============================================================

FRONTEND_AGENTS = [
    AgentSpecialization(
        agent_id="FE-01",
        name="React Specialist",
        domain=TechnologyDomain.FRONTEND,
        description="Especialista em desenvolvimento React e ecossistema",
        technologies=["React", "Next.js", "Redux", "React Query", "Zustand"],
        skills=[
            "Desenvolvimento de componentes React",
            "State management (Redux, Context, Zustand)",
            "Server-side rendering com Next.js",
            "React Hooks avancados",
            "Performance optimization",
            "Testing com Jest e React Testing Library"
        ],
        knowledge_areas=[
            "React 18+ features (Suspense, Concurrent)",
            "Server Components",
            "Static Site Generation (SSG)",
            "Incremental Static Regeneration (ISR)",
            "API Routes",
            "Middleware Next.js"
        ]
    ),
    AgentSpecialization(
        agent_id="FE-02",
        name="Vue.js Specialist",
        domain=TechnologyDomain.FRONTEND,
        description="Especialista em Vue.js e Nuxt",
        technologies=["Vue 3", "Nuxt 3", "Pinia", "Vuetify", "Quasar"],
        skills=[
            "Composition API",
            "Vue Router avancado",
            "State management com Pinia",
            "Server-side rendering com Nuxt",
            "Vue DevTools mastery"
        ],
        knowledge_areas=[
            "Vue 3 Composition API",
            "Nuxt 3 modules",
            "Auto-imports",
            "Hybrid rendering",
            "Vue ecosystem"
        ]
    ),
    AgentSpecialization(
        agent_id="FE-03",
        name="Angular Specialist",
        domain=TechnologyDomain.FRONTEND,
        description="Especialista em Angular e enterprise frontend",
        technologies=["Angular", "NgRx", "RxJS", "Angular Material", "PrimeNG"],
        skills=[
            "Angular modules e lazy loading",
            "Reactive programming com RxJS",
            "State management com NgRx",
            "Angular CLI mastery",
            "Enterprise patterns"
        ],
        knowledge_areas=[
            "Standalone components",
            "Signals",
            "Angular Universal (SSR)",
            "Dependency injection avancado",
            "Change detection strategies"
        ]
    ),
    AgentSpecialization(
        agent_id="FE-04",
        name="UI/UX Developer",
        domain=TechnologyDomain.FRONTEND,
        description="Especialista em CSS, design systems e acessibilidade",
        technologies=["TailwindCSS", "CSS-in-JS", "Styled Components", "Storybook", "Figma"],
        skills=[
            "Design systems implementation",
            "CSS Grid e Flexbox avancado",
            "Animations e transitions",
            "Responsive design",
            "Acessibilidade (WCAG)",
            "Component documentation"
        ],
        knowledge_areas=[
            "Design tokens",
            "Atomic design",
            "Motion design",
            "Color theory",
            "Typography",
            "ARIA patterns"
        ]
    ),
    AgentSpecialization(
        agent_id="FE-05",
        name="TypeScript Frontend Expert",
        domain=TechnologyDomain.FRONTEND,
        description="Especialista em TypeScript para aplicacoes frontend",
        technologies=["TypeScript", "Zod", "tRPC", "GraphQL Codegen"],
        skills=[
            "TypeScript avancado (generics, utility types)",
            "Type-safe API communication",
            "Schema validation",
            "Code generation",
            "Monorepo management"
        ],
        knowledge_areas=[
            "Advanced type patterns",
            "Type inference",
            "Branded types",
            "Type guards",
            "Declaration files"
        ]
    ),
]

# ============================================================
# AGENTES DE BACKEND
# ============================================================

BACKEND_AGENTS = [
    AgentSpecialization(
        agent_id="BE-01",
        name="Python Backend Expert",
        domain=TechnologyDomain.BACKEND,
        description="Especialista em desenvolvimento backend Python",
        technologies=["Python", "FastAPI", "Django", "SQLAlchemy", "Celery", "Redis"],
        skills=[
            "API REST design",
            "Async programming",
            "ORM e database design",
            "Background tasks",
            "Caching strategies",
            "Testing (pytest)"
        ],
        knowledge_areas=[
            "FastAPI avancado",
            "Django ORM optimization",
            "Async SQLAlchemy",
            "Pydantic v2",
            "Dependency injection",
            "OpenAPI/Swagger"
        ]
    ),
    AgentSpecialization(
        agent_id="BE-02",
        name="Node.js Backend Expert",
        domain=TechnologyDomain.BACKEND,
        description="Especialista em Node.js e ecossistema JavaScript/TypeScript",
        technologies=["Node.js", "Express", "NestJS", "Prisma", "TypeORM", "GraphQL"],
        skills=[
            "RESTful API design",
            "GraphQL APIs",
            "Microservices",
            "Event-driven architecture",
            "Database integration"
        ],
        knowledge_areas=[
            "NestJS modules e providers",
            "Prisma schema design",
            "GraphQL resolvers",
            "WebSockets",
            "Job queues (Bull)"
        ]
    ),
    AgentSpecialization(
        agent_id="BE-03",
        name="Java/Spring Expert",
        domain=TechnologyDomain.BACKEND,
        description="Especialista em Java enterprise e Spring ecosystem",
        technologies=["Java", "Spring Boot", "Spring Cloud", "Hibernate", "Maven/Gradle"],
        skills=[
            "Spring Boot applications",
            "Microservices com Spring Cloud",
            "JPA/Hibernate",
            "Security (Spring Security, OAuth2)",
            "Testing (JUnit, Mockito)"
        ],
        knowledge_areas=[
            "Spring Boot 3.x",
            "Virtual threads",
            "Native images (GraalVM)",
            "Reactive programming (WebFlux)",
            "Event sourcing"
        ],
        certifications=["Spring Professional"]
    ),
    AgentSpecialization(
        agent_id="BE-04",
        name=".NET Backend Expert",
        domain=TechnologyDomain.BACKEND,
        description="Especialista em .NET e C# enterprise",
        technologies=[".NET", "C#", "ASP.NET Core", "Entity Framework", "Azure Functions"],
        skills=[
            "ASP.NET Core APIs",
            "Entity Framework Core",
            "Blazor",
            "SignalR",
            "Azure integration"
        ],
        knowledge_areas=[
            ".NET 8+",
            "Minimal APIs",
            "Source generators",
            "MAUI",
            "Microservices patterns"
        ],
        certifications=["Azure Developer Associate"]
    ),
    AgentSpecialization(
        agent_id="BE-05",
        name="API & Integration Expert",
        domain=TechnologyDomain.BACKEND,
        description="Especialista em APIs, integracoes e messaging",
        technologies=["REST", "GraphQL", "gRPC", "Kafka", "RabbitMQ", "API Gateway"],
        skills=[
            "API design (REST, GraphQL, gRPC)",
            "Message brokers",
            "Event-driven architecture",
            "API versioning",
            "Rate limiting"
        ],
        knowledge_areas=[
            "OpenAPI 3.1",
            "AsyncAPI",
            "Schema registry",
            "Event sourcing",
            "CQRS pattern"
        ]
    ),
]

# ============================================================
# AGENTES SAP ECC (POR MODULO)
# ============================================================

SAP_ECC_AGENTS = [
    AgentSpecialization(
        agent_id="SAP-ECC-FI",
        name="SAP ECC FI Expert",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em SAP ECC - Modulo FI (Financial Accounting)",
        technologies=["SAP ECC", "ABAP", "SAP GUI", "LSMW", "BDC"],
        skills=[
            "Contabilidade Geral (GL)",
            "Contas a Pagar (AP)",
            "Contas a Receber (AR)",
            "Gestao de Ativos (AA)",
            "Fechamento contabil",
            "Relatorios financeiros"
        ],
        knowledge_areas=[
            "Plano de contas",
            "Centros de custo",
            "Centros de lucro",
            "Ledgers paralelos",
            "Impostos (IVA, ICMS, PIS, COFINS)",
            "Integracao FI-CO"
        ],
        certifications=["SAP Certified Application Associate - SAP S/4HANA for Financial Accounting"]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-CO",
        name="SAP ECC CO Expert",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em SAP ECC - Modulo CO (Controlling)",
        technologies=["SAP ECC", "ABAP", "Report Painter", "Report Writer"],
        skills=[
            "Contabilidade de centros de custo",
            "Ordens internas",
            "Product costing",
            "Profitability Analysis (CO-PA)",
            "Activity-Based Costing"
        ],
        knowledge_areas=[
            "Ciclos de rateio",
            "Custeio por atividade",
            "Analise de variancia",
            "Planejamento de custos",
            "Integracao CO-FI-PP"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-MM",
        name="SAP ECC MM Expert",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em SAP ECC - Modulo MM (Materials Management)",
        technologies=["SAP ECC", "ABAP", "EDI", "LSMW"],
        skills=[
            "Gestao de materiais",
            "Compras (Procurement)",
            "Contratos e scheduling agreements",
            "Gestao de estoque",
            "Avaliacao de fornecedores",
            "Invoice verification"
        ],
        knowledge_areas=[
            "Tipos de material",
            "MRP (Material Requirements Planning)",
            "Estrategias de sourcing",
            "Gestao de lotes",
            "Consignacao",
            "Integracao MM-FI-PP-SD"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-SD",
        name="SAP ECC SD Expert",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em SAP ECC - Modulo SD (Sales & Distribution)",
        technologies=["SAP ECC", "ABAP", "EDI", "IDoc"],
        skills=[
            "Gestao de vendas",
            "Pricing e condicoes",
            "Determinacao de impostos",
            "Shipping e transportation",
            "Billing e faturamento",
            "Credit management"
        ],
        knowledge_areas=[
            "Estrutura organizacional de vendas",
            "Tipos de documento de vendas",
            "Routines de pricing",
            "ATP (Available to Promise)",
            "Integracao SD-FI-MM"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-PP",
        name="SAP ECC PP Expert",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em SAP ECC - Modulo PP (Production Planning)",
        technologies=["SAP ECC", "ABAP", "MRP", "SOP"],
        skills=[
            "Planejamento de producao",
            "MRP e MPS",
            "Ordens de producao",
            "Confirmacoes de producao",
            "Capacity planning",
            "Shop floor control"
        ],
        knowledge_areas=[
            "BOM (Bill of Materials)",
            "Roteiros de producao",
            "Work centers",
            "Tipos de producao (discreta, repetitiva, processo)",
            "Integracao PP-MM-CO-QM"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-WM",
        name="SAP ECC WM/EWM Expert",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em SAP ECC - Modulo WM (Warehouse Management)",
        technologies=["SAP ECC", "SAP EWM", "RF", "ABAP"],
        skills=[
            "Gestao de armazem",
            "Estrategias de putaway",
            "Estrategias de picking",
            "Inventario",
            "RF transactions",
            "Wave management"
        ],
        knowledge_areas=[
            "Estrutura de warehouse",
            "Storage types e bins",
            "Transfer orders",
            "Slotting",
            "Integracao WM-MM-PP-SD"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-QM",
        name="SAP ECC QM Expert",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em SAP ECC - Modulo QM (Quality Management)",
        technologies=["SAP ECC", "ABAP", "SAP QM"],
        skills=[
            "Planejamento de qualidade",
            "Inspecao de qualidade",
            "Controle de qualidade",
            "Quality notifications",
            "Certificados de qualidade",
            "Audit management"
        ],
        knowledge_areas=[
            "Inspection lots",
            "Sampling procedures",
            "Usage decisions",
            "Quality certificates",
            "Integracao QM-MM-PP-SD"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-PM",
        name="SAP ECC PM Expert",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em SAP ECC - Modulo PM (Plant Maintenance)",
        technologies=["SAP ECC", "ABAP", "SAP PM"],
        skills=[
            "Gestao de equipamentos",
            "Manutencao preventiva",
            "Manutencao corretiva",
            "Ordens de manutencao",
            "Planejamento de manutencao",
            "Gestao de defeitos"
        ],
        knowledge_areas=[
            "Functional locations",
            "Equipment master",
            "Maintenance plans",
            "Task lists",
            "Integracao PM-MM-CO-HR"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-HR",
        name="SAP ECC HR/HCM Expert",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em SAP ECC - Modulo HR (Human Resources)",
        technologies=["SAP ECC", "SAP HCM", "ABAP", "ESS/MSS"],
        skills=[
            "Personnel Administration (PA)",
            "Organizational Management (OM)",
            "Time Management (PT)",
            "Payroll (PY)",
            "Benefits",
            "Recruitment"
        ],
        knowledge_areas=[
            "Infotypes",
            "Personnel actions",
            "Time evaluation",
            "Payroll schemas",
            "Integracao HR-FI-CO"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-ABAP",
        name="SAP ABAP Developer",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em desenvolvimento ABAP",
        technologies=["ABAP", "ABAP OO", "SAP NetWeaver", "Web Dynpro", "Fiori/UI5"],
        skills=[
            "ABAP Programming",
            "ABAP Objects",
            "ALV Reports",
            "BAPIs e RFCs",
            "Enhancement Framework",
            "ABAP Unit Testing"
        ],
        knowledge_areas=[
            "Core Data Services (CDS)",
            "AMDP",
            "OData services",
            "RAP (ABAP RESTful Programming)",
            "Clean ABAP"
        ],
        certifications=["SAP Certified Development Associate - ABAP"]
    ),
    AgentSpecialization(
        agent_id="SAP-ECC-BASIS",
        name="SAP Basis Administrator",
        domain=TechnologyDomain.SAP_ECC,
        description="Especialista em administracao SAP Basis",
        technologies=["SAP NetWeaver", "SAP HANA", "Solution Manager", "SAP Router"],
        skills=[
            "Instalacao e configuracao SAP",
            "Transport management",
            "User administration",
            "Performance tuning",
            "Backup e recovery",
            "System monitoring"
        ],
        knowledge_areas=[
            "SAP HANA administration",
            "System landscape",
            "RFC connections",
            "Background jobs",
            "Security e autorizacoes"
        ],
        certifications=["SAP Certified Technology Associate - SAP NetWeaver"]
    ),
]

# ============================================================
# AGENTES MIGRACAO SAP ECC -> S/4 HANA
# ============================================================

SAP_MIGRATION_AGENTS = [
    AgentSpecialization(
        agent_id="SAP-MIG-01",
        name="SAP S/4HANA Migration Lead",
        domain=TechnologyDomain.SAP_MIGRATION,
        description="Lider de migracao SAP ECC para S/4 HANA",
        technologies=["SAP S/4HANA", "SAP ECC", "DMO", "SUM", "SPRO"],
        skills=[
            "Estrategias de migracao (Greenfield, Brownfield, Bluefield)",
            "Assessment e planning",
            "Data migration",
            "Custom code adaptation",
            "Cutover planning",
            "Go-live management"
        ],
        knowledge_areas=[
            "SAP Readiness Check",
            "Simplification List",
            "Business Process Master List",
            "SAP Activate Methodology",
            "SAP Best Practices"
        ],
        experience_level="expert"
    ),
    AgentSpecialization(
        agent_id="SAP-MIG-02",
        name="SAP Data Migration Expert",
        domain=TechnologyDomain.SAP_MIGRATION,
        description="Especialista em migracao de dados SAP",
        technologies=["SAP Migration Cockpit", "LTMC", "LSMW", "SAP DS", "BODS"],
        skills=[
            "Data profiling e cleansing",
            "Data mapping",
            "ETL processes",
            "Data validation",
            "Legacy data archiving"
        ],
        knowledge_areas=[
            "Migration Object Modeler",
            "SAP Migration Cockpit",
            "Data aging",
            "Data tiering",
            "GDPR compliance"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-MIG-03",
        name="SAP Custom Code Migration Expert",
        domain=TechnologyDomain.SAP_MIGRATION,
        description="Especialista em adaptacao de codigo customizado",
        technologies=["ABAP", "ATC", "SCMON", "SAP Custom Code Migration"],
        skills=[
            "Custom code analysis",
            "Code remediation",
            "ABAP for HANA optimization",
            "CDS views migration",
            "Fiori app adaptation"
        ],
        knowledge_areas=[
            "ABAP Test Cockpit",
            "Custom Code Migration Worklist",
            "HANA-specific optimizations",
            "S/4HANA Compatibility"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-MIG-04",
        name="SAP Integration Migration Expert",
        domain=TechnologyDomain.SAP_MIGRATION,
        description="Especialista em migracao de integracoes",
        technologies=["SAP PI/PO", "SAP CPI", "AIF", "IDoc", "RFC"],
        skills=[
            "Integration assessment",
            "PI/PO to CPI migration",
            "API management",
            "IDoc remediation",
            "Third-party integration update"
        ],
        knowledge_areas=[
            "SAP Integration Suite",
            "API Business Hub",
            "SAP Event Mesh",
            "Integration patterns"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-MIG-05",
        name="SAP Testing & Validation Expert",
        domain=TechnologyDomain.SAP_MIGRATION,
        description="Especialista em testes de migracao SAP",
        technologies=["SAP Solution Manager", "CBTA", "Tricentis", "SAP Fiori Test"],
        skills=[
            "Test strategy definition",
            "Automated testing",
            "Regression testing",
            "Performance testing",
            "UAT coordination"
        ],
        knowledge_areas=[
            "Test automation frameworks",
            "Data-driven testing",
            "Business process testing",
            "Cutover testing"
        ]
    ),
]

# ============================================================
# AGENTES SAP S/4 HANA
# ============================================================

SAP_S4_AGENTS = [
    AgentSpecialization(
        agent_id="SAP-S4-01",
        name="SAP S/4HANA Finance Expert",
        domain=TechnologyDomain.SAP_S4,
        description="Especialista em SAP S/4HANA Finance",
        technologies=["SAP S/4HANA", "SAP Fiori", "Universal Journal", "CDS"],
        skills=[
            "Universal Journal",
            "Central Finance",
            "Group Reporting",
            "Cash Management",
            "Financial Planning",
            "Real-time analytics"
        ],
        knowledge_areas=[
            "ACDOCA (Universal Journal)",
            "Margin Analysis",
            "Embedded analytics",
            "Financial Close",
            "Intercompany processes"
        ],
        certifications=["SAP Certified Application Associate - SAP S/4HANA Finance"]
    ),
    AgentSpecialization(
        agent_id="SAP-S4-02",
        name="SAP S/4HANA Sourcing & Procurement Expert",
        domain=TechnologyDomain.SAP_S4,
        description="Especialista em SAP S/4HANA Sourcing and Procurement",
        technologies=["SAP S/4HANA", "SAP Ariba", "SAP Fiori", "CDS"],
        skills=[
            "Central Procurement",
            "Contract Management",
            "Supplier Management",
            "Ariba integration",
            "Intelligent automation"
        ],
        knowledge_areas=[
            "SAP S/4HANA Sourcing and Procurement",
            "SAP Ariba Network",
            "Predictive MRP",
            "Material Ledger"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-S4-03",
        name="SAP S/4HANA Manufacturing Expert",
        domain=TechnologyDomain.SAP_S4,
        description="Especialista em SAP S/4HANA Manufacturing",
        technologies=["SAP S/4HANA", "SAP MES", "SAP DMC", "SAP Fiori"],
        skills=[
            "Extended MRP",
            "Production Engineering",
            "Shop Floor Control",
            "Quality Management",
            "Manufacturing analytics"
        ],
        knowledge_areas=[
            "SAP Digital Manufacturing Cloud",
            "Production Planning & Detailed Scheduling",
            "Manufacturing Insights",
            "IoT integration"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-S4-04",
        name="SAP S/4HANA Sales Expert",
        domain=TechnologyDomain.SAP_S4,
        description="Especialista em SAP S/4HANA Sales",
        technologies=["SAP S/4HANA", "SAP CX", "SAP Fiori", "SAP CPQ"],
        skills=[
            "Order-to-Cash",
            "Advanced ATP",
            "Billing & Invoicing",
            "Sales analytics",
            "CX integration"
        ],
        knowledge_areas=[
            "Advanced Available-to-Promise",
            "Credit Management",
            "Output Management",
            "Sales Force Automation integration"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-S4-05",
        name="SAP S/4HANA Embedded Analytics Expert",
        domain=TechnologyDomain.SAP_S4,
        description="Especialista em SAP S/4HANA Embedded Analytics",
        technologies=["SAP S/4HANA", "CDS Views", "SAP Fiori", "SAP Analytics Cloud"],
        skills=[
            "CDS View development",
            "Fiori analytical apps",
            "KPI modeling",
            "Real-time reporting",
            "SAC integration"
        ],
        knowledge_areas=[
            "Virtual Data Model (VDM)",
            "Analytical queries",
            "Smart Business KPIs",
            "Live data connections"
        ]
    ),
    AgentSpecialization(
        agent_id="SAP-S4-06",
        name="SAP BTP Developer",
        domain=TechnologyDomain.SAP_S4,
        description="Especialista em SAP Business Technology Platform",
        technologies=["SAP BTP", "CAP", "SAP Fiori", "HANA Cloud", "SAP Build"],
        skills=[
            "CAP (Cloud Application Programming)",
            "Fiori Elements",
            "HANA Cloud development",
            "SAP Build Apps",
            "Extension development"
        ],
        knowledge_areas=[
            "Side-by-side extensions",
            "In-app extensions",
            "SAP Build Process Automation",
            "SAP Integration Suite"
        ]
    ),
]

# ============================================================
# AGENTES SALESFORCE
# ============================================================

SALESFORCE_AGENTS = [
    AgentSpecialization(
        agent_id="SF-01",
        name="Salesforce Administrator",
        domain=TechnologyDomain.SALESFORCE,
        description="Especialista em administracao Salesforce",
        technologies=["Salesforce", "Lightning", "Flow Builder", "Reports & Dashboards"],
        skills=[
            "User management",
            "Security e permissions",
            "Automation (Flow, Process Builder)",
            "Data management",
            "Reports e dashboards",
            "AppExchange"
        ],
        knowledge_areas=[
            "Org setup e configuration",
            "Profiles e Permission Sets",
            "Flow Builder avancado",
            "Data loader",
            "Sandbox management"
        ],
        certifications=["Salesforce Certified Administrator"]
    ),
    AgentSpecialization(
        agent_id="SF-02",
        name="Salesforce Developer",
        domain=TechnologyDomain.SALESFORCE,
        description="Especialista em desenvolvimento Salesforce",
        technologies=["Apex", "LWC", "Visualforce", "SOQL", "SFDX"],
        skills=[
            "Apex programming",
            "Lightning Web Components",
            "Triggers e batch processing",
            "API integrations",
            "Testing e deployment"
        ],
        knowledge_areas=[
            "Governor limits",
            "Asynchronous Apex",
            "Platform Events",
            "Salesforce DX",
            "CI/CD for Salesforce"
        ],
        certifications=["Salesforce Certified Platform Developer I/II"]
    ),
    AgentSpecialization(
        agent_id="SF-03",
        name="Salesforce Sales Cloud Expert",
        domain=TechnologyDomain.SALESFORCE,
        description="Especialista em Salesforce Sales Cloud",
        technologies=["Sales Cloud", "CPQ", "Territory Management", "Einstein"],
        skills=[
            "Lead-to-Cash process",
            "Opportunity management",
            "CPQ configuration",
            "Sales forecasting",
            "Einstein Analytics for Sales"
        ],
        knowledge_areas=[
            "Sales processes",
            "Pipeline management",
            "Quote-to-Cash",
            "Partner management"
        ],
        certifications=["Salesforce Certified Sales Cloud Consultant"]
    ),
    AgentSpecialization(
        agent_id="SF-04",
        name="Salesforce Service Cloud Expert",
        domain=TechnologyDomain.SALESFORCE,
        description="Especialista em Salesforce Service Cloud",
        technologies=["Service Cloud", "Omni-Channel", "Knowledge Base", "Einstein Bots"],
        skills=[
            "Case management",
            "Omni-channel routing",
            "Knowledge management",
            "Service analytics",
            "Field Service"
        ],
        knowledge_areas=[
            "Service Console",
            "Entitlements e SLAs",
            "Live Agent",
            "Service Cloud Voice"
        ],
        certifications=["Salesforce Certified Service Cloud Consultant"]
    ),
    AgentSpecialization(
        agent_id="SF-05",
        name="Salesforce Integration Expert",
        domain=TechnologyDomain.SALESFORCE,
        description="Especialista em integracoes Salesforce",
        technologies=["MuleSoft", "Salesforce Connect", "REST/SOAP APIs", "Platform Events"],
        skills=[
            "API design e implementation",
            "MuleSoft Anypoint",
            "External Objects",
            "Change Data Capture",
            "Heroku Connect"
        ],
        knowledge_areas=[
            "Integration patterns",
            "Composite APIs",
            "Event-driven architecture",
            "Data synchronization"
        ],
        certifications=["MuleSoft Certified Developer"]
    ),
]

# ============================================================
# AGENTES MARKETING CLOUD
# ============================================================

MARKETING_CLOUD_AGENTS = [
    AgentSpecialization(
        agent_id="MC-01",
        name="Marketing Cloud Email Expert",
        domain=TechnologyDomain.MARKETING_CLOUD,
        description="Especialista em Salesforce Marketing Cloud Email Studio",
        technologies=["Marketing Cloud", "Email Studio", "Content Builder", "AMPscript"],
        skills=[
            "Email design e templates",
            "AMPscript programming",
            "Personalization",
            "A/B testing",
            "Deliverability optimization"
        ],
        knowledge_areas=[
            "Email best practices",
            "Dynamic content",
            "Sender authentication",
            "Email compliance (CAN-SPAM, GDPR)"
        ],
        certifications=["Salesforce Marketing Cloud Email Specialist"]
    ),
    AgentSpecialization(
        agent_id="MC-02",
        name="Marketing Cloud Journey Expert",
        domain=TechnologyDomain.MARKETING_CLOUD,
        description="Especialista em Journey Builder e automacao",
        technologies=["Journey Builder", "Automation Studio", "SSJS", "SQL"],
        skills=[
            "Customer journey design",
            "Multi-channel orchestration",
            "Automation workflows",
            "Data extensions",
            "Journey analytics"
        ],
        knowledge_areas=[
            "Journey canvas",
            "Decision splits",
            "Einstein engagement scoring",
            "Journey optimization"
        ],
        certifications=["Salesforce Marketing Cloud Consultant"]
    ),
    AgentSpecialization(
        agent_id="MC-03",
        name="Marketing Cloud Data Expert",
        domain=TechnologyDomain.MARKETING_CLOUD,
        description="Especialista em dados e segmentacao Marketing Cloud",
        technologies=["Contact Builder", "Data Extensions", "SQL", "Data Views"],
        skills=[
            "Data modeling",
            "SQL queries",
            "Segmentation",
            "Data import/export",
            "Subscriber management"
        ],
        knowledge_areas=[
            "Data architecture",
            "Relational data extensions",
            "System data views",
            "Data hygiene"
        ]
    ),
    AgentSpecialization(
        agent_id="MC-04",
        name="Marketing Cloud Developer",
        domain=TechnologyDomain.MARKETING_CLOUD,
        description="Especialista em desenvolvimento Marketing Cloud",
        technologies=["AMPscript", "SSJS", "REST API", "Cloud Pages"],
        skills=[
            "AMPscript avancado",
            "Server-Side JavaScript",
            "API integrations",
            "Cloud Pages development",
            "Custom applications"
        ],
        knowledge_areas=[
            "Platform APIs",
            "Web SDK",
            "Microsite development",
            "Mobile SDK"
        ],
        certifications=["Salesforce Marketing Cloud Developer"]
    ),
]

# ============================================================
# AGENTES POWER BI
# ============================================================

POWER_BI_AGENTS = [
    AgentSpecialization(
        agent_id="PBI-01",
        name="Power BI Report Developer",
        domain=TechnologyDomain.POWER_BI,
        description="Especialista em desenvolvimento de relatorios Power BI",
        technologies=["Power BI Desktop", "DAX", "Power Query", "M Language"],
        skills=[
            "Report design",
            "DAX formulas",
            "Power Query transformations",
            "Data modeling",
            "Visualizations"
        ],
        knowledge_areas=[
            "Star schema modeling",
            "Time intelligence",
            "Row-level security",
            "Performance optimization"
        ],
        certifications=["PL-300: Microsoft Power BI Data Analyst"]
    ),
    AgentSpecialization(
        agent_id="PBI-02",
        name="Power BI Data Engineer",
        domain=TechnologyDomain.POWER_BI,
        description="Especialista em engenharia de dados Power BI",
        technologies=["Power BI", "Dataflows", "Azure Data Factory", "Synapse"],
        skills=[
            "Dataflows development",
            "Incremental refresh",
            "Composite models",
            "DirectQuery optimization",
            "Gateway management"
        ],
        knowledge_areas=[
            "Enterprise data architecture",
            "Dataflow best practices",
            "Premium features",
            "Hybrid scenarios"
        ]
    ),
    AgentSpecialization(
        agent_id="PBI-03",
        name="Power BI Administrator",
        domain=TechnologyDomain.POWER_BI,
        description="Especialista em administracao Power BI Service",
        technologies=["Power BI Service", "Power BI Admin Portal", "Azure AD"],
        skills=[
            "Workspace management",
            "Capacity planning",
            "Security configuration",
            "Usage monitoring",
            "Deployment pipelines"
        ],
        knowledge_areas=[
            "Tenant settings",
            "Premium capacity",
            "Embedded analytics",
            "Governance framework"
        ]
    ),
]

# ============================================================
# AGENTES AZURE
# ============================================================

AZURE_AGENTS = [
    AgentSpecialization(
        agent_id="AZ-01",
        name="Azure Solutions Architect",
        domain=TechnologyDomain.AZURE,
        description="Arquiteto de solucoes Azure",
        technologies=["Azure", "ARM Templates", "Bicep", "Azure DevOps"],
        skills=[
            "Architecture design",
            "Cost optimization",
            "Security design",
            "High availability",
            "Disaster recovery"
        ],
        knowledge_areas=[
            "Well-Architected Framework",
            "Landing zones",
            "Hub-spoke topology",
            "Cloud adoption"
        ],
        certifications=["AZ-305: Azure Solutions Architect Expert"],
        experience_level="expert"
    ),
    AgentSpecialization(
        agent_id="AZ-02",
        name="Azure Data Engineer",
        domain=TechnologyDomain.AZURE,
        description="Engenheiro de dados Azure",
        technologies=["Azure Data Factory", "Synapse Analytics", "Data Lake", "Stream Analytics"],
        skills=[
            "ETL/ELT pipelines",
            "Data Lake design",
            "Synapse development",
            "Real-time analytics",
            "Data governance"
        ],
        knowledge_areas=[
            "Medallion architecture",
            "Delta Lake",
            "Serverless SQL",
            "Spark pools"
        ],
        certifications=["DP-203: Azure Data Engineer Associate"]
    ),
    AgentSpecialization(
        agent_id="AZ-03",
        name="Azure DevOps Engineer",
        domain=TechnologyDomain.AZURE,
        description="Especialista em Azure DevOps",
        technologies=["Azure DevOps", "GitHub Actions", "Terraform", "Kubernetes"],
        skills=[
            "CI/CD pipelines",
            "Infrastructure as Code",
            "Container orchestration",
            "Release management",
            "Monitoring e alerting"
        ],
        knowledge_areas=[
            "YAML pipelines",
            "AKS deployment",
            "GitOps",
            "SRE practices"
        ],
        certifications=["AZ-400: Azure DevOps Engineer Expert"]
    ),
    AgentSpecialization(
        agent_id="AZ-04",
        name="Azure Security Engineer",
        domain=TechnologyDomain.AZURE,
        description="Especialista em seguranca Azure",
        technologies=["Azure Security Center", "Sentinel", "Key Vault", "Azure AD"],
        skills=[
            "Identity management",
            "Network security",
            "Data protection",
            "Threat detection",
            "Compliance"
        ],
        knowledge_areas=[
            "Zero Trust architecture",
            "RBAC e Conditional Access",
            "Security baselines",
            "SIEM/SOAR"
        ],
        certifications=["AZ-500: Azure Security Engineer Associate"]
    ),
    AgentSpecialization(
        agent_id="AZ-05",
        name="Azure AI Engineer",
        domain=TechnologyDomain.AZURE,
        description="Especialista em Azure AI e Cognitive Services",
        technologies=["Azure OpenAI", "Cognitive Services", "Azure ML", "Bot Framework"],
        skills=[
            "Azure OpenAI integration",
            "Custom models",
            "Cognitive Services APIs",
            "Bot development",
            "ML pipelines"
        ],
        knowledge_areas=[
            "Prompt engineering",
            "RAG architecture",
            "Responsible AI",
            "MLOps"
        ],
        certifications=["AI-102: Azure AI Engineer Associate"]
    ),
]

# ============================================================
# AGENTES DATABRICKS
# ============================================================

DATABRICKS_AGENTS = [
    AgentSpecialization(
        agent_id="DBR-01",
        name="Databricks Data Engineer",
        domain=TechnologyDomain.DATABRICKS,
        description="Engenheiro de dados Databricks",
        technologies=["Databricks", "Apache Spark", "Delta Lake", "Python/Scala"],
        skills=[
            "Spark programming",
            "Delta Lake operations",
            "ETL development",
            "Data quality",
            "Performance tuning"
        ],
        knowledge_areas=[
            "Lakehouse architecture",
            "Unity Catalog",
            "Structured Streaming",
            "Databricks SQL"
        ],
        certifications=["Databricks Certified Data Engineer Associate/Professional"]
    ),
    AgentSpecialization(
        agent_id="DBR-02",
        name="Databricks ML Engineer",
        domain=TechnologyDomain.DATABRICKS,
        description="Especialista em Machine Learning com Databricks",
        technologies=["MLflow", "Feature Store", "AutoML", "Model Serving"],
        skills=[
            "ML model development",
            "MLflow tracking",
            "Feature engineering",
            "Model deployment",
            "A/B testing"
        ],
        knowledge_areas=[
            "MLOps with Databricks",
            "Distributed ML",
            "Model registry",
            "Real-time inference"
        ],
        certifications=["Databricks Certified Machine Learning Associate/Professional"]
    ),
    AgentSpecialization(
        agent_id="DBR-03",
        name="Databricks SQL Analyst",
        domain=TechnologyDomain.DATABRICKS,
        description="Especialista em Databricks SQL e analytics",
        technologies=["Databricks SQL", "SQL", "BI Tools", "Dashboards"],
        skills=[
            "SQL optimization",
            "Dashboard development",
            "Query federation",
            "Warehouse management",
            "BI integration"
        ],
        knowledge_areas=[
            "SQL Warehouse tuning",
            "Query history analysis",
            "Cost monitoring",
            "Alerting"
        ],
        certifications=["Databricks Certified Data Analyst Associate"]
    ),
    AgentSpecialization(
        agent_id="DBR-04",
        name="Databricks Platform Administrator",
        domain=TechnologyDomain.DATABRICKS,
        description="Administrador de plataforma Databricks",
        technologies=["Databricks", "Unity Catalog", "Terraform", "Azure/AWS/GCP"],
        skills=[
            "Workspace administration",
            "Unity Catalog setup",
            "Access management",
            "Cost management",
            "Cluster policies"
        ],
        knowledge_areas=[
            "Account-level administration",
            "Identity federation",
            "Network configuration",
            "Audit logging"
        ]
    ),
]


# ============================================================
# REGISTRO COMPLETO DE AGENTES
# ============================================================

ALL_SPECIALIZED_AGENTS = (
    FRONTEND_AGENTS +
    BACKEND_AGENTS +
    SAP_ECC_AGENTS +
    SAP_MIGRATION_AGENTS +
    SAP_S4_AGENTS +
    SALESFORCE_AGENTS +
    MARKETING_CLOUD_AGENTS +
    POWER_BI_AGENTS +
    AZURE_AGENTS +
    DATABRICKS_AGENTS
)


def get_agents_by_domain(domain: TechnologyDomain) -> List[AgentSpecialization]:
    """Retorna agentes de um dominio especifico"""
    return [a for a in ALL_SPECIALIZED_AGENTS if a.domain == domain]


def get_agent_by_id(agent_id: str) -> Optional[AgentSpecialization]:
    """Busca agente por ID"""
    for agent in ALL_SPECIALIZED_AGENTS:
        if agent.agent_id == agent_id:
            return agent
    return None


def search_agents(keyword: str) -> List[AgentSpecialization]:
    """Busca agentes por palavra-chave"""
    keyword = keyword.lower()
    results = []

    for agent in ALL_SPECIALIZED_AGENTS:
        if (keyword in agent.name.lower() or
            keyword in agent.description.lower() or
            any(keyword in tech.lower() for tech in agent.technologies) or
            any(keyword in skill.lower() for skill in agent.skills)):
            results.append(agent)

    return results


def get_all_agents() -> List[AgentSpecialization]:
    """Retorna todos os agentes especializados"""
    return list(ALL_SPECIALIZED_AGENTS)


def get_statistics() -> Dict:
    """Retorna estatisticas dos agentes"""
    by_domain = {}
    for agent in ALL_SPECIALIZED_AGENTS:
        domain = agent.domain.value
        by_domain[domain] = by_domain.get(domain, 0) + 1

    return {
        "total_agents": len(ALL_SPECIALIZED_AGENTS),
        "by_domain": by_domain,
        "domains": list(by_domain.keys()),
        "technologies": list(set(
            tech
            for agent in ALL_SPECIALIZED_AGENTS
            for tech in agent.technologies
        ))
    }


# Resumo dos agentes
AGENTS_SUMMARY = """
AGENTES ESPECIALIZADOS
======================

FRONTEND (5 agentes):
- FE-01: React Specialist
- FE-02: Vue.js Specialist
- FE-03: Angular Specialist
- FE-04: UI/UX Developer
- FE-05: TypeScript Frontend Expert

BACKEND (5 agentes):
- BE-01: Python Backend Expert
- BE-02: Node.js Backend Expert
- BE-03: Java/Spring Expert
- BE-04: .NET Backend Expert
- BE-05: API & Integration Expert

SAP ECC (11 agentes):
- SAP-ECC-FI: Financial Accounting
- SAP-ECC-CO: Controlling
- SAP-ECC-MM: Materials Management
- SAP-ECC-SD: Sales & Distribution
- SAP-ECC-PP: Production Planning
- SAP-ECC-WM: Warehouse Management
- SAP-ECC-QM: Quality Management
- SAP-ECC-PM: Plant Maintenance
- SAP-ECC-HR: Human Resources
- SAP-ECC-ABAP: ABAP Developer
- SAP-ECC-BASIS: Basis Administrator

SAP MIGRATION (5 agentes):
- SAP-MIG-01: Migration Lead
- SAP-MIG-02: Data Migration Expert
- SAP-MIG-03: Custom Code Migration Expert
- SAP-MIG-04: Integration Migration Expert
- SAP-MIG-05: Testing & Validation Expert

SAP S/4 HANA (6 agentes):
- SAP-S4-01: Finance Expert
- SAP-S4-02: Sourcing & Procurement Expert
- SAP-S4-03: Manufacturing Expert
- SAP-S4-04: Sales Expert
- SAP-S4-05: Embedded Analytics Expert
- SAP-S4-06: BTP Developer

SALESFORCE (5 agentes):
- SF-01: Administrator
- SF-02: Developer
- SF-03: Sales Cloud Expert
- SF-04: Service Cloud Expert
- SF-05: Integration Expert

MARKETING CLOUD (4 agentes):
- MC-01: Email Expert
- MC-02: Journey Expert
- MC-03: Data Expert
- MC-04: Developer

POWER BI (3 agentes):
- PBI-01: Report Developer
- PBI-02: Data Engineer
- PBI-03: Administrator

AZURE (5 agentes):
- AZ-01: Solutions Architect
- AZ-02: Data Engineer
- AZ-03: DevOps Engineer
- AZ-04: Security Engineer
- AZ-05: AI Engineer

DATABRICKS (4 agentes):
- DBR-01: Data Engineer
- DBR-02: ML Engineer
- DBR-03: SQL Analyst
- DBR-04: Platform Administrator

TOTAL: 53 agentes especializados
"""


if __name__ == "__main__":
    print(AGENTS_SUMMARY)
    stats = get_statistics()
    print(f"\nEstatisticas:")
    print(f"  Total: {stats['total_agents']} agentes")
    print(f"  Dominios: {len(stats['by_domain'])}")
    print(f"  Tecnologias unicas: {len(stats['technologies'])}")
