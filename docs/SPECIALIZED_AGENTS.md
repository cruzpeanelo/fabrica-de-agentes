# Agentes Especializados

Sistema de 53 agentes especializados em tecnologias especificas.

---

## Visao Geral

| Dominio | Agentes | Foco |
|---------|---------|------|
| Frontend | 5 | React, Vue, Angular, UI/UX, TypeScript |
| Backend | 5 | Python, Node.js, Java, .NET, APIs |
| SAP ECC | 11 | FI, CO, MM, SD, PP, WM, QM, PM, HR, ABAP, Basis |
| SAP Migration | 5 | Migracao ECC para S/4 HANA |
| SAP S/4 HANA | 6 | Finance, Procurement, Manufacturing, Sales, Analytics, BTP |
| Salesforce | 5 | Admin, Dev, Sales Cloud, Service Cloud, Integration |
| Marketing Cloud | 4 | Email, Journey, Data, Development |
| Power BI | 3 | Reports, Data Engineering, Administration |
| Azure | 5 | Architecture, Data, DevOps, Security, AI |
| Databricks | 4 | Data Engineering, ML, SQL, Platform Admin |

**Total: 53 agentes especializados**

---

## Como Usar

### Criar Agente por ID

```python
from factory.agents.agent_factory import create_agent

# Criar agente SAP FI
agent = create_agent("SAP-ECC-FI")

# Ver capacidades
print(agent.get_capabilities_summary())
```

### Selecionar Agente Automaticamente

```python
from factory.agents.agent_factory import select_agent

# Sistema seleciona melhor agente para a tarefa
agent = select_agent("migrar dados do SAP ECC para S/4 HANA")
# Retorna: SAP-MIG-02 (Data Migration Expert)

agent = select_agent("criar componente React com TypeScript")
# Retorna: FE-01 (React Specialist) ou FE-05 (TypeScript Expert)
```

### Executar Tarefa com Analise Automatica

```python
from factory.agents.core import TaskContext

task = TaskContext(
    task_id="T001",
    description="Analisar planilha de custos em dados/custos.xlsx",
    metadata={"files": ["dados/custos.xlsx"]}
)

result = agent.execute_task(task)

# O agente automaticamente:
# 1. Detecta que precisa da skill "data_analysis"
# 2. Analisa o arquivo Excel
# 3. Adiciona insights na memoria de trabalho
# 4. Executa a tarefa com contexto enriquecido
```

### Buscar Agentes

```python
from factory.agents.specialized_agents import search_agents

# Buscar por tecnologia
results = search_agents("SAP")
for agent in results:
    print(f"{agent.agent_id}: {agent.name}")

# Buscar por skill
results = search_agents("migração")
```

---

## Agentes de Frontend

### FE-01: React Specialist
- **Tecnologias**: React, Next.js, Redux, React Query, Zustand
- **Skills**: Componentes, State management, SSR, Hooks, Performance
- **Nivel**: Senior

### FE-02: Vue.js Specialist
- **Tecnologias**: Vue 3, Nuxt 3, Pinia, Vuetify, Quasar
- **Skills**: Composition API, Vue Router, SSR com Nuxt
- **Nivel**: Senior

### FE-03: Angular Specialist
- **Tecnologias**: Angular, NgRx, RxJS, Angular Material, PrimeNG
- **Skills**: Modules, Lazy loading, Reactive programming
- **Nivel**: Senior

### FE-04: UI/UX Developer
- **Tecnologias**: TailwindCSS, CSS-in-JS, Styled Components, Storybook, Figma
- **Skills**: Design systems, Responsivo, Acessibilidade (WCAG)
- **Nivel**: Senior

### FE-05: TypeScript Frontend Expert
- **Tecnologias**: TypeScript, Zod, tRPC, GraphQL Codegen
- **Skills**: Generics, Type-safe APIs, Schema validation
- **Nivel**: Senior

---

## Agentes de Backend

### BE-01: Python Backend Expert
- **Tecnologias**: Python, FastAPI, Django, SQLAlchemy, Celery, Redis
- **Skills**: REST APIs, Async programming, ORM, Background tasks
- **Nivel**: Senior

### BE-02: Node.js Backend Expert
- **Tecnologias**: Node.js, Express, NestJS, Prisma, TypeORM, GraphQL
- **Skills**: REST/GraphQL APIs, Microservices, Event-driven
- **Nivel**: Senior

### BE-03: Java/Spring Expert
- **Tecnologias**: Java, Spring Boot, Spring Cloud, Hibernate
- **Skills**: Microservices, JPA, Security (OAuth2)
- **Certificacoes**: Spring Professional
- **Nivel**: Senior

### BE-04: .NET Backend Expert
- **Tecnologias**: .NET, C#, ASP.NET Core, Entity Framework, Azure Functions
- **Skills**: APIs, Blazor, SignalR
- **Certificacoes**: Azure Developer Associate
- **Nivel**: Senior

### BE-05: API & Integration Expert
- **Tecnologias**: REST, GraphQL, gRPC, Kafka, RabbitMQ, API Gateway
- **Skills**: API design, Message brokers, Event-driven architecture
- **Nivel**: Senior

---

## Agentes SAP ECC

### SAP-ECC-FI: Financial Accounting
- **Modulo**: FI (Financial Accounting)
- **Skills**: GL, AP, AR, AA, Fechamento contabil, Impostos
- **Certificacoes**: SAP S/4HANA for Financial Accounting

### SAP-ECC-CO: Controlling
- **Modulo**: CO (Controlling)
- **Skills**: Centro de custo, Ordens internas, Product costing, CO-PA

### SAP-ECC-MM: Materials Management
- **Modulo**: MM (Materials Management)
- **Skills**: Compras, Contratos, Estoque, MRP, Invoice verification

### SAP-ECC-SD: Sales & Distribution
- **Modulo**: SD (Sales & Distribution)
- **Skills**: Vendas, Pricing, Impostos, Shipping, Billing

### SAP-ECC-PP: Production Planning
- **Modulo**: PP (Production Planning)
- **Skills**: MRP/MPS, Ordens de producao, Capacity planning

### SAP-ECC-WM: Warehouse Management
- **Modulo**: WM/EWM
- **Skills**: Putaway, Picking, Inventario, RF, Wave management

### SAP-ECC-QM: Quality Management
- **Modulo**: QM (Quality Management)
- **Skills**: Inspecao, Controle de qualidade, Certificados

### SAP-ECC-PM: Plant Maintenance
- **Modulo**: PM (Plant Maintenance)
- **Skills**: Manutencao preventiva/corretiva, Ordens, Equipment

### SAP-ECC-HR: Human Resources
- **Modulo**: HR/HCM
- **Skills**: PA, OM, Time Management, Payroll, Benefits

### SAP-ECC-ABAP: ABAP Developer
- **Skills**: ABAP, ABAP OO, ALV, BAPIs/RFCs, CDS, RAP
- **Certificacoes**: SAP Certified ABAP Developer

### SAP-ECC-BASIS: Basis Administrator
- **Skills**: Instalacao, Transports, Users, Performance, Backup
- **Certificacoes**: SAP NetWeaver Technology Associate

---

## Agentes Migracao SAP

### SAP-MIG-01: Migration Lead
- **Foco**: Estrategia e planejamento de migracao
- **Skills**: Greenfield/Brownfield/Bluefield, Assessment, Cutover
- **Nivel**: Expert

### SAP-MIG-02: Data Migration Expert
- **Foco**: Migracao de dados
- **Tecnologias**: Migration Cockpit, LTMC, LSMW, BODS
- **Skills**: Data profiling, Cleansing, Mapping, Validation

### SAP-MIG-03: Custom Code Migration Expert
- **Foco**: Adaptacao de codigo customizado
- **Tecnologias**: ATC, SCMON, Custom Code Migration
- **Skills**: Code analysis, Remediation, HANA optimization

### SAP-MIG-04: Integration Migration Expert
- **Foco**: Migracao de integracoes
- **Tecnologias**: PI/PO, CPI, AIF, IDoc
- **Skills**: PI to CPI migration, API management

### SAP-MIG-05: Testing & Validation Expert
- **Foco**: Testes de migracao
- **Tecnologias**: Solution Manager, CBTA, Tricentis
- **Skills**: Test strategy, Automation, Regression, UAT

---

## Agentes SAP S/4 HANA

### SAP-S4-01: Finance Expert
- **Foco**: SAP S/4HANA Finance
- **Skills**: Universal Journal, Central Finance, Group Reporting
- **Certificacoes**: SAP S/4HANA Finance

### SAP-S4-02: Sourcing & Procurement Expert
- **Foco**: Compras e suprimentos
- **Tecnologias**: SAP Ariba, SAP Fiori
- **Skills**: Central Procurement, Supplier Management

### SAP-S4-03: Manufacturing Expert
- **Foco**: Manufatura
- **Tecnologias**: SAP MES, SAP DMC
- **Skills**: Extended MRP, Shop Floor Control

### SAP-S4-04: Sales Expert
- **Foco**: Vendas
- **Tecnologias**: SAP CX, SAP CPQ
- **Skills**: Order-to-Cash, Advanced ATP

### SAP-S4-05: Embedded Analytics Expert
- **Foco**: Analytics embarcado
- **Tecnologias**: CDS Views, SAP Analytics Cloud
- **Skills**: VDM, Fiori analytical apps, KPIs

### SAP-S4-06: BTP Developer
- **Foco**: SAP Business Technology Platform
- **Tecnologias**: CAP, Fiori, HANA Cloud, SAP Build
- **Skills**: Extensions, CAP development

---

## Agentes Salesforce

### SF-01: Administrator
- **Skills**: Users, Security, Automation (Flow), Reports
- **Certificacoes**: Salesforce Administrator

### SF-02: Developer
- **Tecnologias**: Apex, LWC, SOQL, SFDX
- **Skills**: Triggers, APIs, Testing
- **Certificacoes**: Platform Developer I/II

### SF-03: Sales Cloud Expert
- **Skills**: Lead-to-Cash, CPQ, Forecasting
- **Certificacoes**: Sales Cloud Consultant

### SF-04: Service Cloud Expert
- **Skills**: Cases, Omni-channel, Knowledge
- **Certificacoes**: Service Cloud Consultant

### SF-05: Integration Expert
- **Tecnologias**: MuleSoft, Salesforce Connect
- **Skills**: APIs, Change Data Capture
- **Certificacoes**: MuleSoft Certified Developer

---

## Agentes Marketing Cloud

### MC-01: Email Expert
- **Skills**: Templates, AMPscript, Personalization, A/B testing
- **Certificacoes**: Marketing Cloud Email Specialist

### MC-02: Journey Expert
- **Skills**: Customer journeys, Automation, Analytics
- **Certificacoes**: Marketing Cloud Consultant

### MC-03: Data Expert
- **Skills**: Data modeling, SQL, Segmentation

### MC-04: Developer
- **Tecnologias**: AMPscript, SSJS, REST API
- **Skills**: Cloud Pages, Custom apps
- **Certificacoes**: Marketing Cloud Developer

---

## Agentes Power BI

### PBI-01: Report Developer
- **Tecnologias**: Power BI Desktop, DAX, Power Query
- **Skills**: Reports, Data modeling, Visualizations
- **Certificacoes**: PL-300

### PBI-02: Data Engineer
- **Tecnologias**: Dataflows, Azure Data Factory, Synapse
- **Skills**: Incremental refresh, Composite models

### PBI-03: Administrator
- **Skills**: Workspaces, Capacity, Security, Governance

---

## Agentes Azure

### AZ-01: Solutions Architect
- **Skills**: Architecture, Cost optimization, HA/DR
- **Certificacoes**: AZ-305 (Expert)
- **Nivel**: Expert

### AZ-02: Data Engineer
- **Tecnologias**: Data Factory, Synapse, Data Lake
- **Skills**: ETL/ELT, Medallion architecture
- **Certificacoes**: DP-203

### AZ-03: DevOps Engineer
- **Tecnologias**: Azure DevOps, GitHub Actions, Terraform, K8s
- **Skills**: CI/CD, IaC, AKS
- **Certificacoes**: AZ-400

### AZ-04: Security Engineer
- **Tecnologias**: Security Center, Sentinel, Key Vault
- **Skills**: Identity, Network security, Compliance
- **Certificacoes**: AZ-500

### AZ-05: AI Engineer
- **Tecnologias**: Azure OpenAI, Cognitive Services, Azure ML
- **Skills**: RAG, Custom models, Bots
- **Certificacoes**: AI-102

---

## Agentes Databricks

### DBR-01: Data Engineer
- **Tecnologias**: Spark, Delta Lake, Python/Scala
- **Skills**: ETL, Data quality, Performance
- **Certificacoes**: Data Engineer Associate/Professional

### DBR-02: ML Engineer
- **Tecnologias**: MLflow, Feature Store, AutoML
- **Skills**: Model development, MLOps, Deployment
- **Certificacoes**: ML Associate/Professional

### DBR-03: SQL Analyst
- **Tecnologias**: Databricks SQL, Dashboards
- **Skills**: SQL optimization, BI integration
- **Certificacoes**: Data Analyst Associate

### DBR-04: Platform Administrator
- **Skills**: Workspace admin, Unity Catalog, Cost management

---

## Acionamento Autonomo de Skills

Cada agente pode acionar skills de analise multimidia automaticamente.

### Como Funciona

```python
# Ao executar uma tarefa, o agente:
# 1. Analisa a descricao da tarefa
# 2. Detecta arquivos mencionados
# 3. Aciona skills relevantes automaticamente
# 4. Enriquece o contexto com as analises

agent = create_agent("SAP-ECC-FI")

task = TaskContext(
    task_id="T001",
    description="Analisar relatorio financeiro em docs/relatorio.pdf",
    metadata={"files": ["docs/relatorio.pdf"]}
)

# O agente automaticamente usa pdf_analysis e data_analysis
result = agent.execute_task(task)
```

### Skills Disponiveis

| Skill | Formatos | Descricao |
|-------|----------|-----------|
| text_analysis | TXT, MD | Texto e Markdown |
| pdf_analysis | PDF | Documentos PDF |
| document_analysis | DOCX, HTML, XML | Documentos Office |
| code_analysis | PY, JS, TS, Java | Codigo fonte |
| data_analysis | JSON, CSV, XLSX | Dados estruturados |
| audio_analysis | MP3, WAV, FLAC | Arquivos de audio |
| video_analysis | MP4, AVI, MKV | Arquivos de video |

---

## Estatisticas

```python
from factory.agents.specialized_agents import get_statistics

stats = get_statistics()
print(f"Total: {stats['total_agents']} agentes")
print(f"Dominios: {stats['by_domain']}")
print(f"Tecnologias: {len(stats['technologies'])} unicas")
```

Saida:
```
Total: 53 agentes
Dominios: {
  'frontend': 5,
  'backend': 5,
  'sap_ecc': 11,
  'sap_migration': 5,
  'sap_s4': 6,
  'salesforce': 5,
  'marketing_cloud': 4,
  'power_bi': 3,
  'azure': 5,
  'databricks': 4
}
Tecnologias: 150+ unicas
```
