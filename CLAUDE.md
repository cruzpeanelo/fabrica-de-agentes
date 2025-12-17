# Fabrica de Agentes

## Sistema de Desenvolvimento Autonomo com Agentes IA

A **Fabrica de Agentes** e uma plataforma de desenvolvimento autonomo que combina:
- **Dashboard Agile v6.0**: Gestao de User Stories com Kanban, narrativa Agile, e assistente IA
- **Workers Claude**: Processamento autonomo de tarefas com loop de auto-correcao
- **Kanban Watcher**: Monitoramento automatico que executa tarefas quando movidas para "To Do"

### Dashboards Disponiveis

| Dashboard | Porta | Descricao |
|-----------|-------|-----------|
| **Agile v6** | 9001 | Sistema Agile completo com Stories, Tasks, Docs e Chat |
| **Kanban v5** | 9001 | Kanban simples de tarefas |
| **Workers v4** | 9000 | Fila de jobs e workers Claude |

## Arquitetura Agile v6.0

```
User Stories -> Kanban Board -> Tasks -> Autonomous Dev -> Documentation
      |              |            |            |              |
  Narrativa      Drag/Drop    Subtarefas   Claude AI    Como Testar
  Criterios      Colunas      Progresso    Codigo       Deploy
  DoD            Sprint       Output       Testes       Versao
```

## Estrutura do Projeto

```
Fabrica de Agentes/
├── factory/
│   ├── api/                    # API REST
│   │   ├── routes.py           # Endpoints
│   │   └── auth.py             # Autenticacao JWT
│   ├── core/                   # Core do sistema
│   │   ├── autonomous_loop.py  # Loop Generate->Lint->Test->Fix
│   │   ├── job_queue.py        # Redis job queue
│   │   └── story_generator.py  # Gerador de stories
│   ├── database/               # Banco de dados
│   │   ├── connection.py       # SQLite + SQLAlchemy
│   │   ├── models.py           # Modelos (Story, Task, etc)
│   │   └── repositories.py     # Data access layer
│   ├── dashboard/              # Dashboards web
│   │   ├── app_v6_agile.py     # Dashboard Agile (Stories)
│   │   ├── app_v5_kanban.py    # Dashboard Kanban (Tasks)
│   │   └── app.py              # Dashboard Workers
│   └── config.py               # Configuracoes
├── projects/                   # Projetos gerados
├── uploads/                    # Arquivos anexados
├── run_kanban_watcher.py       # Watcher automatico
├── run_kanban_dev.py           # Desenvolvimento manual
└── docker-compose.yml          # PostgreSQL + Redis
```

## Iniciando a Fabrica

### Dashboard Agile (Recomendado)
```bash
# Iniciar Dashboard Agile v6
python factory/dashboard/app_v6_agile.py

# Dashboard disponivel em: http://localhost:9001
```

### Desenvolvimento Autonomo
```bash
# Watcher automatico (monitora Kanban a cada 30s)
python run_kanban_watcher.py

# Desenvolvimento manual
python run_kanban_dev.py
```

## Sistema Agile v6.0

### Modelos de Dados

#### Story (User Story)
| Campo | Tipo | Descricao |
|-------|------|-----------|
| story_id | string | ID unico (STR-0001) |
| title | string | Titulo da story |
| persona | string | "Como um [usuario]" |
| action | string | "Eu quero [funcionalidade]" |
| benefit | string | "Para que [beneficio]" |
| acceptance_criteria | list | Criterios de aceite |
| definition_of_done | list | Definition of Done |
| story_points | int | Fibonacci (1,2,3,5,8,13,21) |
| complexity | enum | low/medium/high/very_high |
| status | enum | backlog/ready/in_progress/review/testing/done |
| priority | enum | low/medium/high/urgent |
| epic_id | string | Epic associado |
| sprint_id | string | Sprint associado |

#### StoryTask (Subtarefa)
| Campo | Tipo | Descricao |
|-------|------|-----------|
| task_id | string | ID unico (STSK-0001) |
| story_id | string | Story pai |
| title | string | Titulo da task |
| task_type | enum | development/review/test/documentation/design |
| status | enum | pending/in_progress/completed/blocked |
| progress | int | 0-100% |
| files_created | list | Arquivos criados |
| code_output | text | Codigo gerado |
| test_results | json | Resultados de testes |

#### StoryDocumentation
| Campo | Tipo | Descricao |
|-------|------|-----------|
| doc_id | string | ID unico (DOC-0001) |
| story_id | string | Story associada |
| doc_type | enum | technical/user/test/deployment/api |
| content | text | Conteudo Markdown |
| test_instructions | text | Como testar |
| test_cases | list | Casos de teste |

### API Endpoints - Stories

```bash
# Stories
GET    /api/stories                     # Listar stories
POST   /api/stories                     # Criar story
GET    /api/stories/{id}                # Buscar story com tasks
PUT    /api/stories/{id}                # Atualizar story
DELETE /api/stories/{id}                # Deletar story
PATCH  /api/stories/{id}/move           # Mover no Kanban

# Story Tasks
GET    /api/stories/{id}/tasks          # Listar tasks
POST   /api/stories/{id}/tasks          # Criar task
PUT    /api/story-tasks/{id}            # Atualizar task
PATCH  /api/story-tasks/{id}/complete   # Completar task

# Documentation
GET    /api/stories/{id}/docs           # Listar docs
POST   /api/stories/{id}/docs           # Criar doc

# Chat (Assistente)
GET    /api/chat/history                # Historico
POST   /api/chat/message                # Enviar mensagem

# Upload
POST   /api/upload                      # Upload arquivo

# Epics & Sprints
GET    /api/projects/{id}/epics         # Listar epics
POST   /api/epics                       # Criar epic
GET    /api/projects/{id}/sprints       # Listar sprints
POST   /api/sprints                     # Criar sprint
```

### Kanban Board

```
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│  BACKLOG   │  │   READY    │  │ IN PROGRESS│  │   REVIEW   │  │  TESTING   │  │    DONE    │
├────────────┤  ├────────────┤  ├────────────┤  ├────────────┤  ├────────────┤  ├────────────┤
│ ┌────────┐ │  │ ┌────────┐ │  │ ┌────────┐ │  │            │  │            │  │            │
│ │ STR-01 │ │  │ │ STR-02 │ │  │ │ STR-03 │ │  │            │  │            │  │            │
│ │ 5 pts  │ │  │ │ 8 pts  │ │  │ │ 13 pts │ │  │            │  │            │  │            │
│ │ [████] │ │  │ │ [██──] │ │  │ │ [█───] │ │  │            │  │            │  │            │
│ └────────┘ │  │ └────────┘ │  │ └────────┘ │  │            │  │            │  │            │
└────────────┘  └────────────┘  └────────────┘  └────────────┘  └────────────┘  └────────────┘
```

### Story Card
```
┌─────────────────────────┐
│ EPIC-01      5 pts  [!] │  <- Epic + Points + Priority
│ Titulo da Story         │
│ ────────────────────    │
│ [████████░░] 80%        │  <- Progresso das tasks
│ 4/5 tasks | @joao       │  <- Tasks + Assignee
└─────────────────────────┘
```

## Exemplo: Criando Story via API

```bash
# Criar Story
curl -X POST http://localhost:9001/api/stories \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "BELGO-BPM-001",
    "title": "Implementar login com email",
    "persona": "usuario do sistema",
    "action": "fazer login com meu email",
    "benefit": "acesse minhas informacoes de forma segura",
    "acceptance_criteria": [
      "Usuario pode fazer login com email valido",
      "Senha deve ter minimo 8 caracteres",
      "Mensagem de erro clara para credenciais invalidas"
    ],
    "definition_of_done": [
      "Codigo revisado",
      "Testes unitarios passando",
      "Documentacao atualizada"
    ],
    "story_points": 5,
    "priority": "high"
  }'

# Criar Task na Story
curl -X POST http://localhost:9001/api/stories/STR-0001/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Criar endpoint de autenticacao",
    "task_type": "development",
    "estimated_hours": 4
  }'

# Mover Story para In Progress
curl -X PATCH http://localhost:9001/api/stories/STR-0001/move \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

## Watcher Automatico

O `run_kanban_watcher.py` monitora o Kanban a cada 30 segundos e processa automaticamente stories/tasks movidas para "To Do":

```bash
python run_kanban_watcher.py
```

**Fluxo:**
1. Story movida para "ready" ou "in_progress"
2. Watcher detecta a mudanca
3. Claude AI processa cada task da story
4. Arquivos sao gerados em `projects/{project_id}/`
5. Documentacao tecnica e criada automaticamente
6. Story avanca pelo pipeline: in_progress -> testing -> done

## Variaveis de Ambiente

```bash
# Claude API (obrigatorio)
ANTHROPIC_API_KEY=sk-ant-...

# Database (opcional - usa SQLite por padrao)
DATABASE_URL=sqlite:///factory/database/factory.db

# Dashboard
DASHBOARD_PORT=9001
```

## Identidade Visual - Belgo Arames

| Cor | Hex | Uso |
|-----|-----|-----|
| Azul Belgo | #003B4A | Header, botoes primarios |
| Laranja Belgo | #FF6C00 | Acoes, CTAs |
| Cinza Claro | #F3F4F6 | Background |
| Branco | #FFFFFF | Cards, paineis |

---

*Fabrica de Agentes v6.0 - Sistema Agile de Desenvolvimento Autonomo*
