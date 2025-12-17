# Fabrica de Workers

## Sistema de Desenvolvimento Autonomo com Workers Claude

A **Fabrica de Workers** e uma plataforma que utiliza workers Claude para construir software de forma automatizada. Cada worker executa um loop autonomo de geracao, validacao e correcao.

### Dashboard de Monitoramento

O dashboard esta disponivel em **http://localhost:9000** e mostra em tempo real:
- Fila de jobs (pendentes, processando, completos)
- Status dos workers (ativo, idle, erro)
- Progresso de cada job (etapa atual, iteracoes)
- Estatisticas da fila

## Arquitetura v4.0

```
User Request -> FastAPI (JWT/Rate Limit) -> Redis Queue -> Worker Pool (2-5)
                                                              |
                                                       Claude API
                                                              |
                                          Loop: Generate -> Lint -> Test -> Fix (max 5x)
                                                              |
                                                       projects/ folder
```

## Estrutura do Projeto

```
Fabrica de Workers/
├── factory/
│   ├── api/                    # API REST
│   │   ├── routes.py           # Endpoints de jobs/workers/queue
│   │   ├── auth.py             # JWT authentication
│   │   └── rate_limit.py       # Redis rate limiting
│   ├── core/                   # Core do sistema
│   │   ├── job_queue.py        # Redis job queue (FIFO)
│   │   ├── worker.py           # Claude workers + WorkerPool
│   │   └── autonomous_loop.py  # Loop Generate->Lint->Test->Fix
│   ├── database/               # Banco de dados
│   │   ├── connection.py       # PostgreSQL + Redis + SQLite fallback
│   │   ├── models.py           # SQLAlchemy models (6 tabelas)
│   │   └── repositories.py     # Data access layer
│   ├── dashboard/              # Dashboard web
│   │   └── app_v4.py           # FastAPI + Vue.js 3
│   ├── scripts/                # Scripts de inicializacao
│   │   ├── start_workers.py    # Launcher de workers
│   │   ├── start_all.py        # Launcher full stack
│   │   └── init_db.py          # Inicializacao do banco
│   └── config.py               # Configuracoes centralizadas
├── projects/                   # Projetos gerados pelos workers
├── docker-compose.yml          # PostgreSQL + Redis
├── .env.example                # Template de variaveis
└── requirements.txt            # Dependencias Python
```

## Iniciando a Fabrica

```bash
# 1. Iniciar infraestrutura (PostgreSQL + Redis)
docker-compose up -d

# 2. Inicializar banco de dados
python factory/scripts/init_db.py --seed

# 3. Iniciar stack completa
python factory/scripts/start_all.py --workers 2

# Dashboard disponivel em: http://localhost:9000
# API Docs: http://localhost:9000/docs
```

## Componentes Principais

### 1. Job Queue (`factory/core/job_queue.py`)

Gerencia fila de jobs usando Redis (com fallback SQLite).

```python
from factory.core.job_queue import get_queue

queue = await get_queue()

# Criar job
job = await queue.enqueue({
    "description": "API REST para e-commerce",
    "tech_stack": "python,fastapi",
    "features": ["CRUD produtos", "Carrinho", "Checkout"]
})

# Verificar status
status = await queue.get_job(job['job_id'])
print(f"Status: {status['status']} - Etapa: {status['current_step']}")
```

### 2. Worker (`factory/core/worker.py`)

Workers Claude que processam jobs da fila.

```python
from factory.core.worker import WorkerPool

pool = WorkerPool(num_workers=3, model="claude-sonnet-4-20250514")
await pool.start_all()
```

### 3. Autonomous Loop (`factory/core/autonomous_loop.py`)

Loop de desenvolvimento com auto-correcao.

```
1. SETUP    - Prepara ambiente
2. GENERATE - Claude gera codigo
3. LINT     - Valida com ruff/eslint
4. TEST     - Executa pytest/jest
5. FIX      - Claude corrige erros (max 5x)
6. COMPLETE - Projeto pronto
```

## API Endpoints

### Jobs
```bash
POST   /api/v1/jobs           # Criar job
GET    /api/v1/jobs           # Listar jobs
GET    /api/v1/jobs/{id}      # Status do job
DELETE /api/v1/jobs/{id}      # Cancelar job
```

### Queue
```bash
GET    /api/v1/queue/stats    # Estatisticas da fila
GET    /api/v1/queue/peek     # Ver proximos jobs
```

### Workers
```bash
GET    /api/v1/workers        # Listar workers
GET    /api/v1/workers/{id}   # Detalhes do worker
```

### Auth
```bash
POST   /api/v1/auth/login     # Autenticar (retorna JWT)
GET    /api/v1/auth/me        # Usuario atual
POST   /api/v1/auth/refresh   # Renovar token
```

### Health
```bash
GET    /api/v1/health         # Health check basico
GET    /api/v1/health/detailed # Health check detalhado
```

## Exemplo: Criando um Job

### Via API
```bash
# Autenticar
TOKEN=$(curl -s -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')

# Criar job
curl -X POST http://localhost:9000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Sistema de gerenciamento de tarefas",
    "tech_stack": "python,fastapi,postgresql",
    "features": ["CRUD tarefas", "Usuarios", "Categorias"]
  }'
```

### Via Python
```python
import asyncio
from factory.core.job_queue import get_queue

async def main():
    queue = await get_queue()

    job = await queue.enqueue({
        "description": "Blog com posts e comentarios",
        "tech_stack": "python,fastapi,react",
        "features": ["Posts", "Comentarios", "Tags"]
    })

    print(f"Job criado: {job['job_id']}")

asyncio.run(main())
```

## Workflow do Job

```
1. Job CRIADO via API/Dashboard
       |
       v
2. Job entra na FILA Redis (status: pending)
       |
       v
3. Worker PEGA job (status: running)
       |
       v
4. Autonomous Loop EXECUTA:
   - GENERATE: Claude cria codigo
   - LINT: Valida sintaxe/estilo
   - TEST: Executa testes
   - FIX: Corrige erros (se houver)
       |
       v
5. Job COMPLETO (status: completed)
   - Codigo em projects/{job_id}/
```

## Modelos de Dados

### Job
| Campo | Tipo | Descricao |
|-------|------|-----------|
| job_id | string | ID unico (JOB-YYYYMMDDHHMMSS-XXXX) |
| description | string | O que construir |
| tech_stack | string | Stack tecnologica |
| features | list | Lista de features |
| status | enum | pending/running/completed/failed/cancelled |
| current_step | string | Etapa atual do loop |
| progress | float | 0.0 a 1.0 |
| worker_id | string | Worker processando |
| output_path | string | Caminho do projeto gerado |
| error_message | string | Mensagem de erro (se falhou) |

### Worker
| Campo | Tipo | Descricao |
|-------|------|-----------|
| worker_id | string | ID unico (worker-XXXX) |
| status | enum | idle/busy/error |
| current_job_id | string | Job sendo processado |
| model | string | Modelo Claude |
| jobs_completed | int | Total de jobs completos |
| jobs_failed | int | Total de falhas |
| avg_job_duration | float | Duracao media (segundos) |

## Configuracoes

### Variaveis de Ambiente (.env)
```bash
# Claude API (obrigatorio)
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql+asyncpg://fabrica:fabrica_secret@localhost:5432/fabrica_db
REDIS_URL=redis://localhost:6379

# Workers
DEFAULT_WORKERS=2
MAX_WORKERS=5
WORKER_TIMEOUT=600

# Claude
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_MAX_TOKENS=4096

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Dashboard
DASHBOARD_PORT=9000
```

## Scripts Disponiveis

| Script | Comando | Descricao |
|--------|---------|-----------|
| Start All | `python factory/scripts/start_all.py` | Dashboard + Workers |
| Start Workers | `python factory/scripts/start_workers.py -w 3` | Apenas workers |
| Init DB | `python factory/scripts/init_db.py --seed` | Criar tabelas + dados |
| Dashboard | `python factory/dashboard/app_v4.py` | Apenas dashboard |

---

*Fabrica de Workers v4.0 - Desenvolvimento autonomo com Claude AI*
