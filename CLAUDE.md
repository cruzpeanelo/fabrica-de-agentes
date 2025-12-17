# Fabrica de Agentes

## Sistema de Agentes Autonomos para Construcao de Aplicacoes

A **Fabrica de Agentes** eh uma plataforma que utiliza 19 agentes autonomos trabalhando em paralelo para construir qualquer tipo de aplicacao, realizar analises de dados, gerar documentos e muito mais.

### Dashboard de Monitoramento

O dashboard esta disponivel em **http://localhost:9000** e mostra em tempo real:
- Projetos ativos e seu progresso
- Status dos agentes (EXECUTANDO, STANDBY, ERRO)
- Skills disponiveis (Core, MCP, Vessel)
- Logs de atividades

## Estrutura do Projeto

```
Fabrica de Agentes/
├── factory/                    # Core da fabrica
│   ├── database/               # SQLite + SQLAlchemy
│   │   ├── factory.db          # Banco de dados principal
│   │   ├── models.py           # Modelos de dados
│   │   ├── repositories.py     # Repositorios
│   │   └── seed.py             # Dados iniciais
│   ├── dashboard/              # Dashboard web (porta 9000)
│   │   └── app.py              # FastAPI + Vue.js
│   ├── core/                   # Componentes centrais
│   │   └── project_manager.py  # Gerenciador de projetos
│   ├── skills/                 # Sistema de skills
│   │   └── skill_manager.py    # Gerenciador de skills
│   ├── config.py               # Configuracoes
│   └── log_activity.py         # CLI para registrar atividades
├── projects/                   # Projetos construidos (cada um em pasta separada)
├── templates/                  # Templates de projetos
│   ├── web-app/
│   ├── api-service/
│   ├── data-analysis/
│   └── document/
└── .claude/                    # Configuracao Claude Code
```

## Iniciando a Fabrica

```bash
# 1. Inicializar banco de dados e dados iniciais
python factory/database/seed.py

# 2. Iniciar dashboard
python factory/dashboard/app.py

# Dashboard disponivel em: http://localhost:9000
```

## Registro de Atividades

**TODAS as atividades dos agentes DEVEM ser registradas no banco de dados** para aparecerem no dashboard.

### Como Registrar Atividades

Use o script `factory/log_activity.py`:

```bash
# Ao INICIAR uma tarefa:
python factory/log_activity.py -a 08 -t task_start -m "Criando API" -p PRJ-001 -s US-001

# Durante execucao:
python factory/log_activity.py -a 08 -t info -m "Processando dados..."

# Ao CONCLUIR uma tarefa:
python factory/log_activity.py -a 08 -t task_complete -m "Tarefa finalizada" -r "5 endpoints criados"

# Em caso de ERRO:
python factory/log_activity.py -a 08 -t error -m "Erro ao processar arquivo"
```

### Acoes Disponiveis

| Acao | Descricao | Efeito |
|------|-----------|--------|
| `task_start` | Inicio de tarefa | Marca agente como EXECUTING |
| `task_complete` | Tarefa concluida | Marca agente como STANDBY |
| `task_fail` | Tarefa falhou | Marca agente como ERROR |
| `info` | Log informativo | Registra mensagem INFO |
| `warning` | Aviso | Registra mensagem WARNING |
| `error` | Erro | Registra mensagem ERROR |
| `project_start` | Iniciar projeto | Registra inicio de projeto |
| `project_complete` | Projeto concluido | Registra conclusao de projeto |
| `story_start` | Iniciar story | Registra inicio de story |
| `story_complete` | Story concluida | Registra conclusao de story |
| `code_gen` | Codigo gerado | Registra criacao de arquivo |
| `decision` | Decisao tecnica | Registra decisao tomada |
| `skill_exec` | Skill executada | Registra uso de skill |

## Agentes Disponiveis

### Management (01-04)
| ID | Nome | Role | Descricao |
|----|------|------|-----------|
| 01 | Gestao Estrategica | Orquestrador | Coordenacao geral, OKRs, decisoes |
| 02 | Product Manager | Gerente Produto | Roadmap, priorizacao, estrategia |
| 03 | Product Owner | Dono Produto | Backlog, user stories, criterios |
| 04 | Project Manager | Gerente Projeto | Sprints, riscos, tracking |

### Data (05-07)
| ID | Nome | Role | Descricao |
|----|------|------|-----------|
| 05 | Analista de Dados | Analista | SQL, KPIs, visualizacao |
| 06 | Engenheiro de Dados | Engenheiro | ETL, pipelines, qualidade |
| 07 | Especialista BD | DBA | Schema, indices, performance |

### Development (08-10)
| ID | Nome | Role | Descricao |
|----|------|------|-----------|
| 08 | Especialista Backend | Backend Dev | APIs, servicos, logica |
| 09 | Desenvolvedor Frontend | Frontend Dev | React, componentes, UI |
| 10 | Especialista Seguranca | Security | Auth, auditoria, vulnerabilidades |

### Design (11-12)
| ID | Nome | Role | Descricao |
|----|------|------|-----------|
| 11 | Especialista UX | UX Designer | Wireframes, fluxos, pesquisa |
| 12 | Especialista UI | UI Designer | Design system, visual, tokens |

### Quality (13, 15-16)
| ID | Nome | Role | Descricao |
|----|------|------|-----------|
| 13 | Revisor de Codigo | Code Reviewer | Review, boas praticas, refactoring |
| 15 | Testador QA | QA Engineer | Testes, automacao, qualidade |
| 16 | Testador E2E | E2E Engineer | Playwright, browser tests |

### Infrastructure & Integration (14, 17-19)
| ID | Nome | Role | Descricao |
|----|------|------|-----------|
| 14 | Engenheiro DevOps | DevOps | CI/CD, deploy, monitoring |
| 17 | Documentador | Tech Writer | Documentacao, guias, API docs |
| 18 | Arquiteto | Solution Architect | Arquitetura, patterns, design |
| 19 | Integrador | Integration Specialist | APIs, webhooks, conectores |

## Tipos de Projetos Suportados

| Tipo | Descricao | Agentes Recomendados |
|------|-----------|----------------------|
| `web-app` | Aplicacao web fullstack | 01, 02, 03, 04, 08, 09, 11, 12, 15 |
| `api-service` | Servico de API REST/GraphQL | 01, 03, 04, 07, 08, 10, 15 |
| `data-analysis` | Analise e visualizacao de dados | 01, 03, 05, 06, 07 |
| `document` | Geracao de documentos/relatorios | 01, 03, 17 |
| `automation` | Scripts e automacoes | 01, 03, 08, 14, 19 |
| `integration` | Integracoes entre sistemas | 01, 03, 08, 18, 19 |

## Sistema de Skills

### Skills Core
- `file-read`, `file-write`, `file-search` - Operacoes de arquivo
- `web-fetch`, `web-search` - Operacoes web
- `bash-execute` - Execucao de comandos
- `sql-query`, `data-transform` - Dados

### Skills MCP (Model Context Protocol)
- `mcp-playwright` - Automacao de browser
- `mcp-filesystem` - Operacoes avancadas de arquivo
- `mcp-github` - Integracao GitHub
- `mcp-memory` - Memoria persistente

### Skills Vessel (futuro)
- `vessel-container` - Execucao isolada em container
- `vessel-sandbox` - Ambiente sandbox para testes

## API Endpoints

### Status
```bash
GET /api/status
```

### Projetos
```bash
GET  /api/projects           # Lista projetos
POST /api/projects           # Cria projeto
GET  /api/projects/{id}      # Busca projeto
PUT  /api/projects/{id}      # Atualiza projeto
DELETE /api/projects/{id}    # Remove projeto
```

### Stories
```bash
GET  /api/stories            # Lista stories
POST /api/stories            # Cria story
PUT  /api/stories/{id}       # Atualiza story
```

### Agentes
```bash
GET /api/agents              # Lista agentes
PUT /api/agents/{id}         # Atualiza agente
```

### Skills
```bash
GET /api/skills              # Lista skills
```

### Logs
```bash
GET /api/logs                # Lista logs (query: project_id, agent_id, level, limit)
```

## Exemplo: Criando um Novo Projeto

```bash
# Via API
curl -X POST http://localhost:9000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Meu App", "project_type": "web-app", "description": "Descricao do app"}'

# Via Python
from factory.core.project_manager import get_project_manager

pm = get_project_manager()
project = pm.create_project(
    name="Meu App",
    project_type="web-app",
    description="Descricao do app"
)
print(f"Projeto criado: {project['project_id']}")
```

## Workflow Tipico

1. **Criar Projeto** via dashboard ou API
2. **Atribuir Agentes** ao projeto
3. **Criar Stories** com tarefas
4. **Agentes Executam** as tarefas em paralelo
5. **Registrar Atividades** no banco de dados
6. **Monitorar Progresso** no dashboard
7. **Projeto Concluido** na pasta `projects/`

---

*Fabrica de Agentes v2.0 - Sistema de agentes autonomos para construcao de aplicacoes*
