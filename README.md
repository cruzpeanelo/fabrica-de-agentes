# Fabrica de Workers

**Plataforma de Desenvolvimento Autonomo com Workers Claude**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Claude AI](https://img.shields.io/badge/Claude-Sonnet%204-purple.svg)](https://anthropic.com)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## O Que E a Fabrica de Workers?

A **Fabrica de Workers** e uma plataforma de desenvolvimento autonomo que utiliza **workers Claude** para gerar software completo de forma automatizada. Cada worker executa um loop inteligente de geracao, validacao e correcao ate produzir codigo funcional.

### Proposta de Valor

| Para Negocios | Para TI |
|---------------|---------|
| Reducao de **70-80%** no tempo de desenvolvimento | Codigo padronizado e de alta qualidade |
| Escalabilidade horizontal (2-5 workers) | Stack moderna (FastAPI, PostgreSQL, Redis) |
| Auto-correcao de erros (ate 5 tentativas) | Testes automatizados integrados |
| API simples e job-centric | Dashboard em tempo real |

---

## Arquitetura v4.0

```
+------------------------------------------------------------------+
|                     FABRICA DE WORKERS v4.0                       |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+    +------------------+    +---------------+ |
|  |   DASHBOARD      |    |   API REST       |    |   PostgreSQL  | |
|  |   (Vue.js 3)     |<-->|   (FastAPI)      |<-->|   + Redis     | |
|  +------------------+    +------------------+    +---------------+ |
|         ^                        |                                 |
|         |              +---------v----------+                      |
|         |              |    REDIS QUEUE     |                      |
|         |              |   (Job Manager)    |                      |
|         |              +---------+----------+                      |
|         |                        |                                 |
|  +------+------------------------v-------------------------------+ |
|  |                    WORKER POOL (2-5)                          | |
|  |                                                                | |
|  |  +-------------+  +-------------+  +-------------+            | |
|  |  |  Worker 1   |  |  Worker 2   |  |  Worker N   |            | |
|  |  | Claude API  |  | Claude API  |  | Claude API  |            | |
|  |  +------+------+  +------+------+  +------+------+            | |
|  |         |                |                |                    | |
|  |         v                v                v                    | |
|  |  +--------------------------------------------------+         | |
|  |  |           AUTONOMOUS LOOP (por job)              |         | |
|  |  |                                                  |         | |
|  |  |   +----------+    +------+    +------+          |         | |
|  |  |   | Generate |--->| Lint |--->| Test |          |         | |
|  |  |   +----------+    +------+    +--+---+          |         | |
|  |  |        ^                         |              |         | |
|  |  |        |     +-------+           |              |         | |
|  |  |        +-----| Fix   |<----------+              |         | |
|  |  |              +-------+   (max 5x)               |         | |
|  |  +--------------------------------------------------+         | |
|  +---------------------------------------------------------------+ |
|                                |                                   |
|                   +------------v-------------+                     |
|                   |      projects/ folder    |                     |
|                   |   (Codigo Gerado)        |                     |
|                   +--------------------------+                     |
+------------------------------------------------------------------+
```

---

## Componentes

### 1. API REST (`factory/api/`)

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| **Routes** | `routes.py` | Endpoints REST para jobs, workers e queue |
| **Auth** | `auth.py` | Autenticacao JWT com chave persistente |
| **Rate Limit** | `rate_limit.py` | Limitacao de requisicoes via Redis |

**Endpoints Principais:**
```
POST   /api/v1/jobs           - Criar job de desenvolvimento
GET    /api/v1/jobs/{id}      - Status do job
GET    /api/v1/jobs           - Listar jobs
DELETE /api/v1/jobs/{id}      - Cancelar job
GET    /api/v1/queue/stats    - Estatisticas da fila
GET    /api/v1/workers        - Listar workers ativos
POST   /api/v1/auth/login     - Autenticacao
GET    /api/v1/health         - Health check
```

### 2. Core (`factory/core/`)

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| **Job Queue** | `job_queue.py` | Fila Redis FIFO para jobs |
| **Worker** | `worker.py` | Claude Worker que processa jobs |
| **Autonomous Loop** | `autonomous_loop.py` | Loop Generate->Lint->Test->Fix |

**Job Queue:**
- Fila FIFO para jobs pendentes
- Pub/Sub para eventos em tempo real
- Fallback para SQLite se Redis indisponivel

**Worker:**
- Consome jobs da fila Redis
- Executa autonomous loop com Claude API
- Heartbeat para monitoramento de saude
- Retries automaticos em caso de falha

**Autonomous Loop:**
```
1. SETUP    - Prepara ambiente do projeto
2. GENERATE - Gera codigo via Claude API
3. LINT     - Executa linter (ruff/eslint)
4. TEST     - Executa testes (pytest/jest)
5. FIX      - Se erro, Claude corrige (max 5x)
6. COMPLETE - Projeto pronto em projects/
```

### 3. Database (`factory/database/`)

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| **Connection** | `connection.py` | PostgreSQL + Redis + SQLite fallback |
| **Models** | `models.py` | SQLAlchemy models (6 tabelas) |
| **Repositories** | `repositories.py` | Camada de acesso a dados |

**Modelos:**
| Tabela | Descricao |
|--------|-----------|
| `projects` | Metadados de projetos |
| `jobs` | Fila de trabalho (unidade principal) |
| `workers` | Registro de workers ativos |
| `failure_history` | Historico de falhas para analise |
| `users` | Autenticacao de usuarios |
| `activity_logs` | Logs de auditoria |

### 4. Dashboard (`factory/dashboard/`)

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| **App** | `app_v4.py` | Dashboard Vue.js 3 worker-centric |

**Funcionalidades:**
- Visao geral da fila (pendentes, processando, completos)
- Painel de workers (status, job atual, metricas)
- Lista de jobs com filtros e progresso
- Criacao de jobs via interface
- Atualizacao automatica a cada 5 segundos

### 5. Config (`factory/config.py`)

Configuracoes centralizadas:
- Paths do projeto
- Conexoes de banco (PostgreSQL, Redis, SQLite)
- Workers (min, max, timeouts)
- Claude API (modelo, tokens)
- Rate limiting
- MCP tools

### 6. Scripts (`factory/scripts/`)

| Script | Comando | Descricao |
|--------|---------|-----------|
| `start_workers.py` | `python factory/scripts/start_workers.py -w 3` | Inicia pool de workers |
| `start_all.py` | `python factory/scripts/start_all.py` | Inicia dashboard + workers |
| `init_db.py` | `python factory/scripts/init_db.py --seed` | Inicializa banco de dados |

---

## Instalacao

### Pre-requisitos

- Python 3.10+
- Docker (para PostgreSQL + Redis)
- Chave API Anthropic

### Instalacao Rapida

```bash
# Clone o repositorio
git clone https://github.com/cruzpeanelo/fabrica-de-workers.git
cd fabrica-de-workers

# Ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dependencias
pip install -r requirements.txt

# Configurar ambiente
cp .env.example .env
# Edite .env e adicione sua ANTHROPIC_API_KEY

# Iniciar infraestrutura (PostgreSQL + Redis)
docker-compose up -d

# Inicializar banco de dados
python factory/scripts/init_db.py --seed

# Iniciar tudo (Dashboard + Workers)
python factory/scripts/start_all.py --workers 2
```

**Acesse:** http://localhost:9000

### Sem Docker (SQLite + Redis local)

```bash
# Se Redis instalado localmente
redis-server &

# Ou use apenas SQLite (sem Redis)
# O sistema faz fallback automaticamente

python factory/scripts/start_all.py
```

---

## Uso

### Via Dashboard (Recomendado)

1. Acesse http://localhost:9000
2. Clique em "Novo Job"
3. Preencha descricao e stack tecnologica
4. Acompanhe o progresso em tempo real
5. Projeto gerado em `projects/`

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
    "description": "API REST para gerenciamento de tarefas com autenticacao JWT",
    "tech_stack": "python,fastapi,postgresql",
    "features": ["CRUD de tarefas", "Autenticacao JWT", "Rate limiting"]
  }'

# Verificar status
curl http://localhost:9000/api/v1/jobs/{job_id} \
  -H "Authorization: Bearer $TOKEN"

# Ver estatisticas da fila
curl http://localhost:9000/api/v1/queue/stats \
  -H "Authorization: Bearer $TOKEN"

# Listar workers
curl http://localhost:9000/api/v1/workers \
  -H "Authorization: Bearer $TOKEN"
```

### Via Python

```python
import asyncio
from factory.core.job_queue import get_queue

async def create_job():
    queue = await get_queue()

    job = await queue.enqueue({
        "description": "Sistema de blog com posts e comentarios",
        "tech_stack": "python,fastapi,react",
        "features": ["CRUD posts", "Comentarios", "Busca"]
    })

    print(f"Job criado: {job['job_id']}")

    # Acompanhar status
    while True:
        status = await queue.get_job(job['job_id'])
        print(f"Status: {status['status']} - {status['current_step']}")

        if status['status'] in ['completed', 'failed']:
            break

        await asyncio.sleep(5)

asyncio.run(create_job())
```

---

## Estrutura do Projeto

```
Fabrica de Workers/
├── factory/
│   ├── api/                    # API REST
│   │   ├── routes.py           # Endpoints de jobs/workers
│   │   ├── auth.py             # JWT authentication
│   │   └── rate_limit.py       # Redis rate limiting
│   ├── core/                   # Core do sistema
│   │   ├── job_queue.py        # Redis job queue
│   │   ├── worker.py           # Claude workers
│   │   └── autonomous_loop.py  # Loop de desenvolvimento
│   ├── database/               # Banco de dados
│   │   ├── connection.py       # PostgreSQL + Redis + SQLite
│   │   ├── models.py           # SQLAlchemy models
│   │   └── repositories.py     # Data access layer
│   ├── dashboard/              # Dashboard web
│   │   └── app_v4.py           # FastAPI + Vue.js
│   ├── scripts/                # Scripts de inicializacao
│   │   ├── start_workers.py    # Launcher de workers
│   │   ├── start_all.py        # Launcher completo
│   │   └── init_db.py          # Inicializacao do banco
│   └── config.py               # Configuracoes centralizadas
├── projects/                   # Projetos gerados
├── docker-compose.yml          # PostgreSQL + Redis
├── .env.example                # Template de variaveis
├── requirements.txt            # Dependencias Python
└── README.md
```

---

## Configuracao

### Variaveis de Ambiente

| Variavel | Descricao | Padrao |
|----------|-----------|--------|
| `ANTHROPIC_API_KEY` | Chave API Claude **(obrigatorio)** | - |
| `DATABASE_URL` | PostgreSQL connection string | SQLite local |
| `REDIS_URL` | Redis connection string | redis://localhost:6379 |
| `DEFAULT_WORKERS` | Workers iniciais | 2 |
| `MAX_WORKERS` | Maximo de workers | 5 |
| `CLAUDE_MODEL` | Modelo Claude | claude-sonnet-4-20250514 |
| `RATE_LIMIT_REQUESTS` | Requisicoes por janela | 100 |
| `RATE_LIMIT_WINDOW` | Janela em segundos | 60 |
| `JWT_SECRET_KEY` | Chave JWT (gerada automaticamente) | - |

### docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: fabrica
      POSTGRES_PASSWORD: fabrica_secret
      POSTGRES_DB: fabrica_db
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## Fluxo de Trabalho

```
1. Usuario cria JOB via API/Dashboard
       |
       v
2. Job entra na REDIS QUEUE (FIFO)
       |
       v
3. WORKER disponivel pega o job
       |
       v
4. AUTONOMOUS LOOP executa:

   [GENERATE] --> Claude gera codigo
        |
        v
   [LINT] --> ruff/eslint valida
        |
        +---> Erro? --> [FIX] --> Claude corrige --> volta para LINT
        |
        v
   [TEST] --> pytest/jest executa
        |
        +---> Erro? --> [FIX] --> Claude corrige --> volta para LINT
        |
        v
   [COMPLETE] --> Projeto salvo em projects/

5. Status atualizado em tempo real via Redis Pub/Sub
```

---

## Comparacao: v3.0 vs v4.0

| Aspecto | v3.0 (Agentes) | v4.0 (Workers) |
|---------|----------------|----------------|
| Unidade de trabalho | 19 agentes especializados | 2-5 workers genericos |
| Coordenacao | Complexa entre agentes | Fila simples Redis |
| Escalabilidade | Dificil | Horizontal (mais workers) |
| Banco | SQLite apenas | PostgreSQL + Redis |
| API | 80+ endpoints | ~15 endpoints |
| Dashboard | 5000+ linhas | ~800 linhas |
| Auto-correcao | Limitada | Loop ate 5 tentativas |

---

## Roadmap

### v4.0 (Atual)
- [x] Workers Claude com pool configuravel
- [x] Redis Queue para jobs
- [x] PostgreSQL + Redis infrastructure
- [x] Autonomous loop (Generate -> Lint -> Test -> Fix)
- [x] JWT authentication persistente
- [x] Rate limiting via Redis
- [x] Dashboard worker-centric
- [x] API simplificada

### v4.1 (Planejado)
- [ ] WebSocket para atualizacoes em tempo real
- [ ] Multiplos modelos Claude (Opus, Haiku)
- [ ] MCP tools integration
- [ ] Logs estruturados (ELK stack)

### v5.0 (Futuro)
- [ ] Multi-tenant (SaaS)
- [ ] Kubernetes deployment
- [ ] CI/CD integrado
- [ ] Marketplace de templates

---

## Contribuindo

1. Fork o repositorio
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudancas (`git commit -m 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## Licenca

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

## Contato

- **Autor**: Luis Cruz
- **GitHub**: [cruzpeanelo](https://github.com/cruzpeanelo)

---

<p align="center">
  <strong>Fabrica de Workers</strong> - Desenvolvimento autonomo com Claude AI
</p>
