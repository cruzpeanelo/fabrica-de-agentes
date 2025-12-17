# -*- coding: utf-8 -*-
"""
Gerador de User Stories Detalhadas - Belgo BPM Platform
========================================================

Gera User Stories completas com tasks por agente para o projeto
de visualizacao de processos AS-IS/TO-BE do GTM GO Wire.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
os.chdir(r'C:\Users\lcruz\Fabrica de Agentes')

from dotenv import load_dotenv
load_dotenv()

import json
import time
from datetime import datetime, timezone

from factory.ai.claude_integration import ClaudeClient
from factory.database.connection import SessionLocal
from factory.database.models import Story, Task, Project, Sprint
from factory.core.story_generator import (
    DetailedStory, AgentTask, generate_story_id, generate_task_id,
    get_agents_for_category, calculate_points, create_tasks_for_story,
    story_to_db_dict, task_to_db_dict, DEFAULT_DOD, AGENT_SPECIALTIES
)


# =============================================================================
# CONFIGURACAO DO PROJETO BELGO BPM
# =============================================================================

PROJECT_ID = "PROJ-20251216221517"
PROJECT_NAME = "Belgo BPM Platform"

PROJECT_DESCRIPTION = """
Plataforma de Visualizacao e Documentacao de Processos AS-IS e TO-BE
Projeto: GTM - GO Wire (Belgo Mineira)

OBJETIVO:
Ferramenta web para visualizar, documentar e editar os processos de negocio
do projeto GTM, permitindo comparacao entre estado atual (AS-IS) e futuro (TO-BE).

MODULOS DO GTM:
1. Cadastro de Clientes - Conta, Sintegra, Areas de Vendas, Canais
2. Documentos Fiscais - XML, Certificados, Faturamento
3. Logistica - Portal Logistico, Restricoes, Distribuicao
4. Pricing/Cotacoes - Tabela de Precos, Workflow de Aprovacao
5. Vendas - Ordem de Vendas, Cotacoes, Pipeline
6. Autoatendimento - Portal do Cliente, Downloads
7. Financeiro/Credito - Ficha de Credito, Analise

FUNCIONALIDADES PRINCIPAIS:
- Dashboard executivo com KPIs de processos
- Visualizador de diagramas BPMN interativo
- Editor visual drag-and-drop para fluxos
- Comparacao AS-IS vs TO-BE lado a lado
- Navegacao hierarquica (Area > Processo > Subprocesso > Etapa)
- Sistema de comentarios e anotacoes colaborativo
- Historico de versoes e alteracoes
- Exportacao para PDF/PNG
- Busca avancada por processos

STACK TECNICA:
- Backend: FastAPI + Python
- Frontend: Vue.js 3 + Tailwind CSS
- Database: SQLite/PostgreSQL
- Diagramas: Vue Flow / BPMN.js
"""

# Epics do projeto
EPICS = {
    "EPIC-01": "Infraestrutura e Arquitetura",
    "EPIC-02": "Dashboard e Navegacao",
    "EPIC-03": "Visualizador de Processos",
    "EPIC-04": "Editor Visual de Fluxos",
    "EPIC-05": "Comparacao AS-IS/TO-BE",
    "EPIC-06": "Colaboracao e Comentarios",
    "EPIC-07": "Exportacao e Relatorios",
    "EPIC-08": "Modulos de Negocio GTM"
}

# Stories detalhadas para o projeto
STORIES_CONFIG = [
    # EPIC-01: Infraestrutura
    {
        "epic": "EPIC-01",
        "title": "Modelo de Dados para Processos BPM",
        "persona": "arquiteto de sistemas",
        "action": "ter um modelo de dados robusto para armazenar processos, fluxos, etapas e metadados",
        "benefit": "a plataforma tenha uma base solida para persistir e recuperar informacoes de processos",
        "category": "database",
        "complexity": "high",
        "priority": "HIGH",
        "sprint": 1,
        "component": "database",
        "acceptance_criteria": [
            "Tabela de Areas/Modulos criada (id, nome, descricao, icone, ordem)",
            "Tabela de Processos criada (id, area_id, nome, descricao, tipo[AS-IS/TO-BE], versao)",
            "Tabela de Etapas/Nodes criada (id, processo_id, tipo, posicao_x, posicao_y, dados)",
            "Tabela de Conexoes/Edges criada (id, processo_id, origem_id, destino_id, label)",
            "Tabela de Versoes criada para historico de alteracoes",
            "Tabela de Comentarios criada (id, processo_id, etapa_id, usuario, texto, timestamp)",
            "Indices otimizados para consultas frequentes",
            "Seeds com dados iniciais dos 7 modulos do GTM"
        ],
        "business_rules": [
            "Todo processo deve pertencer a uma area",
            "Processos AS-IS e TO-BE sao versoes do mesmo processo base",
            "Etapas deletadas sao soft-deleted para historico"
        ],
        "technical_notes": [
            "Usar SQLAlchemy ORM",
            "Suportar JSON para dados flexiveis das etapas",
            "Implementar audit trail automatico"
        ]
    },
    {
        "epic": "EPIC-01",
        "title": "API REST para Gestao de Processos",
        "persona": "desenvolvedor frontend",
        "action": "ter endpoints REST completos para CRUD de processos e etapas",
        "benefit": "o frontend possa consumir e manipular dados de processos",
        "category": "backend",
        "complexity": "high",
        "priority": "HIGH",
        "sprint": 1,
        "component": "api",
        "acceptance_criteria": [
            "GET /api/areas - Lista todas as areas com contagem de processos",
            "GET /api/processes - Lista processos com filtros (area, tipo, busca)",
            "GET /api/processes/{id} - Retorna processo completo com etapas e conexoes",
            "POST /api/processes - Cria novo processo",
            "PUT /api/processes/{id} - Atualiza processo existente",
            "DELETE /api/processes/{id} - Remove processo (soft delete)",
            "POST /api/processes/{id}/duplicate - Duplica processo (AS-IS para TO-BE)",
            "GET /api/processes/{id}/versions - Lista versoes do processo",
            "Documentacao OpenAPI/Swagger completa"
        ],
        "business_rules": [
            "Apenas usuarios autenticados podem modificar processos",
            "Duplicacao cria nova versao mantendo referencia ao original"
        ],
        "technical_notes": [
            "Usar FastAPI com Pydantic schemas",
            "Implementar paginacao em listagens",
            "Retornar erros padronizados"
        ]
    },
    # EPIC-02: Dashboard
    {
        "epic": "EPIC-02",
        "title": "Dashboard Executivo com KPIs",
        "persona": "gestor do projeto GTM",
        "action": "visualizar um dashboard com metricas e status geral dos processos",
        "benefit": "tenha visao rapida do progresso da documentacao de processos",
        "category": "frontend",
        "complexity": "medium",
        "priority": "HIGH",
        "sprint": 1,
        "component": "dashboard",
        "acceptance_criteria": [
            "Card com total de processos documentados (AS-IS vs TO-BE)",
            "Card com percentual de completude por area",
            "Grafico de barras com processos por area/modulo",
            "Lista de atividades recentes (ultimas alteracoes)",
            "Indicadores de processos pendentes de revisao",
            "Links rapidos para areas mais acessadas",
            "Responsivo para desktop e tablet"
        ],
        "business_rules": [
            "KPIs atualizados em tempo real",
            "Filtro por periodo disponivel"
        ],
        "technical_notes": [
            "Usar Vue.js 3 com Composition API",
            "Graficos com Chart.js ou ApexCharts",
            "Estilizacao com Tailwind CSS"
        ]
    },
    {
        "epic": "EPIC-02",
        "title": "Menu de Navegacao por Areas GTM",
        "persona": "usuario da plataforma",
        "action": "navegar facilmente entre as 7 areas do GTM atraves de um menu intuitivo",
        "benefit": "encontre rapidamente os processos que precisa visualizar",
        "category": "frontend",
        "complexity": "low",
        "priority": "HIGH",
        "sprint": 1,
        "component": "navigation",
        "acceptance_criteria": [
            "Menu lateral com as 7 areas do GTM com icones",
            "Submenu expandivel mostrando processos de cada area",
            "Indicador visual de area/processo atual",
            "Breadcrumb mostrando caminho de navegacao",
            "Menu colapsavel para mais espaco de visualizacao",
            "Busca rapida no menu",
            "Badge com contagem de processos por area"
        ],
        "business_rules": [
            "Areas ordenadas conforme definido no GTM",
            "Processos ordenados por nome ou data de atualizacao"
        ],
        "technical_notes": [
            "Componente Vue reutilizavel",
            "Estado persistido no localStorage",
            "Animacoes suaves de transicao"
        ]
    },
    # EPIC-03: Visualizador
    {
        "epic": "EPIC-03",
        "title": "Visualizador de Diagramas BPMN",
        "persona": "analista de processos",
        "action": "visualizar diagramas de processos em formato BPMN de forma interativa",
        "benefit": "entenda claramente o fluxo de cada processo",
        "category": "frontend",
        "complexity": "very_high",
        "priority": "HIGH",
        "sprint": 2,
        "component": "viewer",
        "acceptance_criteria": [
            "Renderizacao de nodes BPMN (tarefa, decisao, evento inicio/fim, subprocesso)",
            "Conexoes com setas e labels entre nodes",
            "Zoom in/out com controles e scroll do mouse",
            "Pan/arrastar para navegar pelo diagrama",
            "Minimap para orientacao em diagramas grandes",
            "Click em node abre painel de detalhes",
            "Cores diferenciadas por tipo de etapa",
            "Layout automatico quando necessario"
        ],
        "business_rules": [
            "Diagramas devem respeitar notacao BPMN simplificada",
            "Detalhes mostram descricao, responsavel, sistemas envolvidos"
        ],
        "technical_notes": [
            "Usar Vue Flow (baseado em React Flow)",
            "Custom nodes para tipos BPMN",
            "Performance otimizada para 100+ nodes"
        ]
    },
    {
        "epic": "EPIC-03",
        "title": "Painel de Detalhes da Etapa",
        "persona": "analista de processos",
        "action": "ver e editar detalhes completos de cada etapa do processo",
        "benefit": "documente informacoes importantes como responsavel, sistemas e regras",
        "category": "frontend",
        "complexity": "medium",
        "priority": "MEDIUM",
        "sprint": 2,
        "component": "viewer",
        "acceptance_criteria": [
            "Painel lateral que abre ao clicar em uma etapa",
            "Campos: nome, descricao, tipo, responsavel/area",
            "Campo para sistemas envolvidos (SAP, Portal, etc)",
            "Campo para documentos relacionados",
            "Campo para regras de negocio da etapa",
            "Campo para observacoes/notas",
            "Botao de salvar alteracoes",
            "Historico de alteracoes da etapa"
        ],
        "business_rules": [
            "Alteracoes geram nova versao",
            "Campos obrigatorios: nome e tipo"
        ],
        "technical_notes": [
            "Form com validacao",
            "Auto-save opcional",
            "Rich text editor para descricao"
        ]
    },
    # EPIC-04: Editor
    {
        "epic": "EPIC-04",
        "title": "Editor Visual Drag-and-Drop",
        "persona": "analista de processos",
        "action": "criar e editar diagramas de processo arrastando elementos",
        "benefit": "documente processos de forma visual e intuitiva",
        "category": "frontend",
        "complexity": "very_high",
        "priority": "HIGH",
        "sprint": 2,
        "component": "editor",
        "acceptance_criteria": [
            "Paleta de elementos BPMN arrastáveis (tarefa, decisão, evento, gateway)",
            "Arrastar elemento da paleta para o canvas",
            "Mover elementos existentes no canvas",
            "Criar conexões clicando e arrastando entre elementos",
            "Deletar elementos e conexões selecionados",
            "Undo/Redo de alterações (Ctrl+Z, Ctrl+Y)",
            "Copiar/Colar elementos (Ctrl+C, Ctrl+V)",
            "Snap to grid para alinhamento",
            "Auto-layout para organizar diagrama"
        ],
        "business_rules": [
            "Eventos de início/fim são obrigatórios",
            "Conexões só podem partir de portas válidas"
        ],
        "technical_notes": [
            "Usar Vue Flow com modo de edição",
            "Debounce em auto-save",
            "State management com Pinia"
        ]
    },
    {
        "epic": "EPIC-04",
        "title": "Toolbar de Edicao com Acoes",
        "persona": "analista de processos",
        "action": "ter uma barra de ferramentas com acoes rapidas de edicao",
        "benefit": "seja mais produtivo ao editar diagramas",
        "category": "frontend",
        "complexity": "low",
        "priority": "MEDIUM",
        "sprint": 2,
        "component": "editor",
        "acceptance_criteria": [
            "Botao Salvar com indicador de alteracoes pendentes",
            "Botao Desfazer/Refazer",
            "Botao Zoom In/Out/Reset",
            "Botao Auto-Layout",
            "Botao Exportar (PNG/PDF)",
            "Botao Tela Cheia",
            "Atalhos de teclado exibidos em tooltip",
            "Toolbar fixa no topo do editor"
        ],
        "business_rules": [
            "Salvar desabilitado se nao houver alteracoes"
        ],
        "technical_notes": [
            "Componente Vue reutilizavel",
            "Icones com Heroicons ou similar"
        ]
    },
    # EPIC-05: Comparacao
    {
        "epic": "EPIC-05",
        "title": "Tela de Comparacao AS-IS vs TO-BE",
        "persona": "gestor de area",
        "action": "comparar visualmente o processo atual (AS-IS) com o futuro (TO-BE) lado a lado",
        "benefit": "entenda claramente as mudancas propostas",
        "category": "frontend",
        "complexity": "high",
        "priority": "HIGH",
        "sprint": 3,
        "component": "comparison",
        "acceptance_criteria": [
            "Split view com AS-IS a esquerda e TO-BE a direita",
            "Sincronizacao de zoom e pan entre os dois paineis",
            "Destaque visual de elementos adicionados no TO-BE (verde)",
            "Destaque visual de elementos removidos do AS-IS (vermelho)",
            "Destaque visual de elementos modificados (amarelo)",
            "Toggle para mostrar/ocultar highlights de diferenças",
            "Resumo de mudanças no topo (X adicionados, Y removidos, Z modificados)",
            "Botao para alternar entre split view e overlay"
        ],
        "business_rules": [
            "Comparacao baseada em IDs de referencia das etapas",
            "Mudancas detectadas automaticamente"
        ],
        "technical_notes": [
            "Algoritmo de diff para detectar mudancas",
            "Scroll sincronizado entre paineis",
            "Performance otimizada para diagramas grandes"
        ]
    },
    # EPIC-06: Colaboracao
    {
        "epic": "EPIC-06",
        "title": "Sistema de Comentarios em Etapas",
        "persona": "membro da equipe",
        "action": "adicionar comentarios e discussoes em etapas especificas do processo",
        "benefit": "a equipe colabore e documente decisoes",
        "category": "frontend",
        "complexity": "medium",
        "priority": "MEDIUM",
        "sprint": 3,
        "component": "collaboration",
        "acceptance_criteria": [
            "Icone de comentario visivel em etapas que possuem comentarios",
            "Painel de comentarios ao clicar no icone",
            "Formulario para adicionar novo comentario",
            "Lista de comentarios com autor, data e texto",
            "Responder a comentarios existentes (thread)",
            "Marcar comentario como resolvido",
            "Mencionar usuarios com @",
            "Notificacao visual de novos comentarios"
        ],
        "business_rules": [
            "Comentarios nao podem ser deletados, apenas resolvidos",
            "Autor pode editar seu comentario em ate 5 minutos"
        ],
        "technical_notes": [
            "WebSocket para updates em tempo real (opcional)",
            "Paginacao de comentarios"
        ]
    },
    {
        "epic": "EPIC-06",
        "title": "Historico de Versoes e Alteracoes",
        "persona": "gestor do projeto",
        "action": "visualizar o historico completo de alteracoes de um processo",
        "benefit": "rastreie mudancas e possa reverter se necessario",
        "category": "backend",
        "complexity": "medium",
        "priority": "MEDIUM",
        "sprint": 3,
        "component": "versioning",
        "acceptance_criteria": [
            "Endpoint GET /api/processes/{id}/history retorna lista de versoes",
            "Cada versao contem: numero, autor, data, descricao da mudanca",
            "Endpoint GET /api/processes/{id}/versions/{version} retorna estado naquela versao",
            "Endpoint POST /api/processes/{id}/restore/{version} restaura versao anterior",
            "Frontend com timeline de versoes",
            "Diff visual entre versoes selecionadas",
            "Filtro por periodo e autor"
        ],
        "business_rules": [
            "Versoes nunca sao deletadas",
            "Restaurar cria nova versao (nao sobrescreve)"
        ],
        "technical_notes": [
            "Armazenar snapshots comprimidos",
            "Limite de versoes configuravel"
        ]
    },
    # EPIC-07: Exportacao
    {
        "epic": "EPIC-07",
        "title": "Exportacao de Diagramas para PDF/PNG",
        "persona": "usuario da plataforma",
        "action": "exportar diagramas em formato PDF ou imagem PNG",
        "benefit": "compartilhe e inclua em apresentacoes e documentos",
        "category": "frontend",
        "complexity": "medium",
        "priority": "LOW",
        "sprint": 3,
        "component": "export",
        "acceptance_criteria": [
            "Botao de exportar no toolbar do visualizador",
            "Opcoes: PNG, PDF, SVG",
            "Configuracao de tamanho (A4, A3, personalizado)",
            "Opcao de incluir cabecalho com nome do processo",
            "Opcao de incluir legenda de simbolos",
            "Qualidade alta para impressao",
            "Preview antes de exportar"
        ],
        "business_rules": [
            "Exportacao respeita zoom atual ou fit-to-page"
        ],
        "technical_notes": [
            "Usar html2canvas + jsPDF",
            "Exportacao no client-side"
        ]
    },
    # EPIC-08: Modulos GTM
    {
        "epic": "EPIC-08",
        "title": "Modulo Cadastro de Clientes - Processos",
        "persona": "analista da area comercial",
        "action": "visualizar e editar processos de cadastro de clientes do GTM",
        "benefit": "documente o fluxo de cadastro com integracao Sintegra e SAP",
        "category": "frontend",
        "complexity": "medium",
        "priority": "MEDIUM",
        "sprint": 4,
        "component": "modules",
        "acceptance_criteria": [
            "Processo AS-IS de Cadastro de Cliente documentado",
            "Processo TO-BE de Cadastro de Cliente documentado",
            "Subprocessos: Validacao Sintegra, Areas de Vendas, Canais",
            "Etapas com responsaveis e sistemas (SAP, Sintegra)",
            "Regras de negocio documentadas em cada etapa",
            "Integracao com dados das reunioes de levantamento"
        ],
        "business_rules": [
            "Dados baseados nas transcricoes das reunioes GTM",
            "Fluxos validados com stakeholders"
        ],
        "technical_notes": [
            "Importar dados estruturados das reunioes",
            "Templates de etapas pre-definidos"
        ]
    },
    {
        "epic": "EPIC-08",
        "title": "Modulo Documentos Fiscais - Processos",
        "persona": "analista fiscal",
        "action": "visualizar processos de emissao e gestao de documentos fiscais",
        "benefit": "entenda o fluxo de XML, certificados e faturamento",
        "category": "frontend",
        "complexity": "medium",
        "priority": "MEDIUM",
        "sprint": 4,
        "component": "modules",
        "acceptance_criteria": [
            "Processo AS-IS de Documentos Fiscais documentado",
            "Processo TO-BE de Documentos Fiscais documentado",
            "Subprocessos: Emissao XML, Certificados, Download",
            "Integracoes SAP documentadas",
            "Fluxo de autoatendimento incluido"
        ],
        "business_rules": [
            "Conformidade com legislacao fiscal"
        ],
        "technical_notes": [
            "Dados das reunioes de 10/dez e 16/dez"
        ]
    }
]


def create_story_from_config(config: dict, project_id: str) -> DetailedStory:
    """Cria uma DetailedStory a partir de configuracao"""

    story_id = generate_story_id()
    category = config.get("category", "frontend")
    complexity = config.get("complexity", "medium")
    agents = get_agents_for_category(category)

    # Adicionar agentes de QA e Review
    agents.extend(["AGT-13", "AGT-15"])  # Code Reviewer e QA

    # Remover duplicatas mantendo ordem
    agents = list(dict.fromkeys(agents))

    # Criar tasks para cada agente
    tasks = create_tasks_for_story(
        story_id=story_id,
        story_title=config["title"],
        category=category,
        agents=agents,
        complexity=complexity
    )

    # Calcular estimativa total
    total_hours = sum(t.estimated_hours for t in tasks)
    points = calculate_points(complexity, len(tasks))

    story = DetailedStory(
        story_id=story_id,
        project_id=project_id,
        title=config["title"],
        description=config.get("description", f"Implementacao de {config['title']}"),
        persona=f"Como {config['persona']}",
        action=f"eu quero {config['action']}",
        benefit=f"para que {config['benefit']}",
        epic=config.get("epic", "EPIC-01"),
        sprint=config.get("sprint", 1),
        priority=config.get("priority", "MEDIUM"),
        points=points,
        complexity=complexity,
        business_value=config.get("business_value", 50),
        acceptance_criteria=config.get("acceptance_criteria", []),
        definition_of_done=config.get("definition_of_done", DEFAULT_DOD),
        business_rules=config.get("business_rules", []),
        technical_notes=config.get("technical_notes", []),
        assigned_to=agents[0] if agents else "AGT-08",
        agents=agents,
        tasks=tasks,
        dependencies=config.get("dependencies", []),
        estimated_hours=total_hours,
        risk_level=config.get("risk_level", "low"),
        category=config.get("category", "feature"),
        component=config.get("component", ""),
        tags=config.get("tags", [])
    )

    return story


def save_story_to_db(db, story: DetailedStory):
    """Salva story e tasks no banco de dados"""

    # Converter para dict do modelo
    story_dict = story_to_db_dict(story)

    # Criar Story
    db_story = Story(
        story_id=story_dict["story_id"],
        project_id=story_dict["project_id"],
        title=story_dict["title"],
        description=story_dict["description"],
        epic_id=story_dict["epic_id"],
        status=story_dict["status"],
        sprint=story_dict["sprint"],
        points=story_dict["points"],
        priority=story_dict["priority"],
        business_value=story_dict["business_value"],
        narrative_persona=story_dict["narrative_persona"],
        narrative_action=story_dict["narrative_action"],
        narrative_benefit=story_dict["narrative_benefit"],
        acceptance_criteria=json.dumps(story_dict["acceptance_criteria"], ensure_ascii=False),
        business_rules=json.dumps(story_dict["business_rules"], ensure_ascii=False),
        definition_of_done=json.dumps(story_dict["definition_of_done"], ensure_ascii=False),
        technical_notes=json.dumps(story_dict["technical_notes"], ensure_ascii=False),
        dependencies=json.dumps(story_dict["dependencies"], ensure_ascii=False),
        assigned_to=story_dict["assigned_to"],
        agents=json.dumps(story_dict["agents"], ensure_ascii=False),
        estimated_hours=story_dict["estimated_hours"],
        complexity=story_dict["complexity"],
        risk_level=story_dict["risk_level"],
        tags=json.dumps(story_dict["tags"], ensure_ascii=False),
        category=story_dict["category"],
        component=story_dict["component"],
        source=story_dict["source"]
    )
    db.add(db_story)

    # Criar Tasks
    for task in story.tasks:
        task_dict = task_to_db_dict(task, story.story_id, story.project_id)

        db_task = Task(
            task_id=task_dict["task_id"],
            task_type=task_dict["task_type"],
            project_id=task_dict["project_id"],
            story_id=task_dict["story_id"],
            agent_id=task_dict["agent_id"],
            title=task_dict["title"],
            description=task_dict["description"],
            priority=task_dict["priority"],
            payload=json.dumps(task_dict["payload"], ensure_ascii=False),
            dependencies=json.dumps(task_dict["dependencies"], ensure_ascii=False),
            skills_required=json.dumps(task_dict["skills_required"], ensure_ascii=False),
            status=task_dict["status"]
        )
        db.add(db_task)

    db.commit()


def main():
    print("=" * 70)
    print("  GERADOR DE USER STORIES DETALHADAS")
    print("  Projeto: Belgo BPM Platform")
    print("=" * 70)
    print()

    # Conectar ao banco
    db = SessionLocal()

    # Verificar/atualizar projeto
    project = db.query(Project).filter(Project.project_id == PROJECT_ID).first()
    if project:
        project.name = PROJECT_NAME
        project.description = PROJECT_DESCRIPTION
        project.status = "IN_PROGRESS"
        db.commit()
        print(f"[OK] Projeto atualizado: {PROJECT_NAME}")
    else:
        print(f"[ERRO] Projeto {PROJECT_ID} nao encontrado!")
        db.close()
        return

    # Limpar stories e tasks existentes
    deleted_tasks = db.query(Task).filter(Task.project_id == PROJECT_ID).delete()
    deleted_stories = db.query(Story).filter(Story.project_id == PROJECT_ID).delete()
    db.commit()
    print(f"[OK] Removidos: {deleted_stories} stories, {deleted_tasks} tasks")

    # Criar Sprint 1
    existing_sprint = db.query(Sprint).filter(
        Sprint.project_id == PROJECT_ID,
        Sprint.sprint_number == 1
    ).first()

    if not existing_sprint:
        sprint1 = Sprint(
            project_id=PROJECT_ID,
            sprint_number=1,
            name="Sprint 1 - Fundacao",
            status="active",
            goal="Criar infraestrutura base: modelo de dados, API e dashboard"
        )
        db.add(sprint1)
        db.commit()
        print("[OK] Sprint 1 criado")

    # Gerar stories
    print()
    print("Gerando User Stories detalhadas...")
    print("-" * 70)

    total_stories = 0
    total_tasks = 0
    total_points = 0
    total_hours = 0

    for config in STORIES_CONFIG:
        story = create_story_from_config(config, PROJECT_ID)
        save_story_to_db(db, story)

        total_stories += 1
        total_tasks += len(story.tasks)
        total_points += story.points
        total_hours += story.estimated_hours

        # Exibir resumo da story
        priority_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "CRITICAL": "⚫"}.get(story.priority, "⚪")
        print(f"\n{priority_icon} [{story.story_id}] {story.title}")
        print(f"   Epic: {story.epic} | Sprint: {story.sprint} | Pontos: {story.points} | Horas: {story.estimated_hours:.1f}h")
        print(f"   {story.persona}, {story.action}")
        print(f"   Agentes: {', '.join(story.agents)}")
        print(f"   Tasks ({len(story.tasks)}):")
        for task in story.tasks:
            agent_name = AGENT_SPECIALTIES.get(task.agent_id, {}).get("name", "Agente")
            print(f"      - [{task.task_id}] {agent_name}: {task.title[:50]}...")

    # Resumo final
    print()
    print("=" * 70)
    print("  RESUMO DA GERACAO")
    print("=" * 70)
    print(f"  Total de Stories: {total_stories}")
    print(f"  Total de Tasks:   {total_tasks}")
    print(f"  Total de Pontos:  {total_points}")
    print(f"  Total de Horas:   {total_hours:.1f}h")
    print()
    print("  Por Sprint:")

    # Agrupar por sprint
    stories_by_sprint = {}
    for config in STORIES_CONFIG:
        sprint = config.get("sprint", 1)
        if sprint not in stories_by_sprint:
            stories_by_sprint[sprint] = {"count": 0, "points": 0}
        stories_by_sprint[sprint]["count"] += 1

    for sprint_num in sorted(stories_by_sprint.keys()):
        info = stories_by_sprint[sprint_num]
        print(f"    Sprint {sprint_num}: {info['count']} stories")

    print()
    print(f"  📊 Dashboard: http://localhost:9000")
    print(f"  📋 Projeto: {PROJECT_ID}")
    print("=" * 70)

    db.close()


if __name__ == "__main__":
    main()
