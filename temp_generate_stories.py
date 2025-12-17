# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
os.chdir(r'C:\Users\lcruz\Fabrica de Agentes')

from dotenv import load_dotenv
load_dotenv()

from factory.ai.claude_integration import ClaudeClient
from factory.database.connection import SessionLocal
from factory.database.models import Story, Project
from datetime import datetime
import uuid
import json
import re

# Conectar ao banco
db = SessionLocal()

# Atualizar projeto
project = db.query(Project).filter(Project.project_id == 'PROJ-20251216221517').first()
if project:
    project.name = 'Belgo BPM Platform'
    project.description = '''Plataforma de visualizacao e documentacao de processos AS-IS e TO-BE do projeto GTM - GO Wire.

Funcionalidades:
- Visualizacao de diagramas de processos e fluxos
- Comparacao AS-IS vs TO-BE lado a lado
- Editor visual para criar/modificar fluxos
- Organizacao por modulos (Cadastro Clientes, Documentos Fiscais, Logistica, Pricing, Vendas, Autoatendimento)
- Edicao colaborativa de desenhos, descricoes e fluxos
- Navegacao por areas e detalhes dos processos'''
    project.project_type = 'web-app'
    project.status = 'IN_PROGRESS'
    db.commit()
    print(f'Projeto atualizado: {project.name}')
else:
    print('Projeto nao encontrado!')
    db.close()
    exit(1)

# Usar Claude para gerar User Stories
client = ClaudeClient()

contexto = """
PROJETO: Belgo BPM Platform - Visualizacao de Processos GTM GO Wire

OBJETIVO: Plataforma web para visualizar e documentar processos AS-IS (atual) e TO-BE (futuro) do projeto GTM.

MODULOS DO GTM:
1. Cadastro de Clientes
2. Documentos Fiscais
3. Logistica/Distribuicao
4. Pricing/Cotacoes
5. Vendas/Ordem de Vendas
6. Autoatendimento
7. Financeiro/Credito

FUNCIONALIDADES NECESSARIAS:
- Dashboard com visao geral dos modulos e processos
- Visualizador de diagramas de fluxo (estilo BPMN)
- Comparacao AS-IS vs TO-BE lado a lado
- Editor visual drag-and-drop para criar/editar fluxos
- Descricao detalhada de cada etapa do processo
- Organizacao hierarquica: Area > Processo > Subprocesso > Etapa
- Sistema de comentarios e anotacoes
- Historico de alteracoes
- Exportacao para PDF/imagem
- Busca por processos, areas, responsaveis

USUARIOS: Analistas de processos, gestores, equipe de TI, stakeholders do projeto GTM
"""

print('\nGerando User Stories com Claude AI...')

response = client.chat(
    message=f"""Com base no contexto abaixo, gere 12 User Stories para uma plataforma de VISUALIZACAO E DOCUMENTACAO de processos.

{contexto}

IMPORTANTE: O foco eh VISUALIZAR e EDITAR documentacao de processos, NAO eh automacao BPM.

Retorne APENAS um JSON array valido com este formato:
[
  {{"title": "Titulo curto", "description": "Descricao detalhada da funcionalidade", "persona": "Como [analista de processos/gestor/usuario]", "action": "eu quero [acao especifica]", "benefit": "para que [beneficio claro]", "acceptance_criteria": ["Criterio 1", "Criterio 2", "Criterio 3"], "category": "frontend|backend|database", "priority": "HIGH|MEDIUM|LOW", "points": 3}}
]

Cubra: dashboard, visualizador de fluxos, editor visual, comparacao AS-IS/TO-BE, organizacao por modulos, busca, exportacao.
""",
    system_prompt='Voce e um Product Owner experiente em sistemas de documentacao de processos. Retorne APENAS JSON valido.',
    max_tokens=4000
)

if not response.success:
    print(f'Erro: {response.error}')
    db.close()
    exit(1)

# Parse JSON
content = response.content.strip()
if '```' in content:
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        content = match.group(0)
content = content.strip()

try:
    stories_data = json.loads(content)
    print(f'\n{len(stories_data)} User Stories geradas')
except json.JSONDecodeError as e:
    print(f'Erro ao parsear JSON: {e}')
    print(f'Conteudo: {content[:500]}')
    db.close()
    exit(1)

# Salvar no banco
print('\nSalvando User Stories no banco de dados...')
print('=' * 60)

for i, s in enumerate(stories_data, 1):
    story_id = f'US-{datetime.now().strftime("%Y%m%d%H%M%S")}-{str(uuid.uuid4())[:4].upper()}'

    story = Story(
        story_id=story_id,
        project_id='PROJ-20251216221517',
        title=s.get('title', f'Story {i}'),
        description=s.get('description', ''),
        status='TODO',
        priority=s.get('priority', 'MEDIUM'),
        points=s.get('points', 3),
        sprint=1,
        narrative_persona=s.get('persona', ''),
        narrative_action=s.get('action', ''),
        narrative_benefit=s.get('benefit', ''),
        acceptance_criteria=json.dumps(s.get('acceptance_criteria', []), ensure_ascii=False),
        category=s.get('category', 'frontend')
    )
    db.add(story)

    priority_icon = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(s.get('priority', 'MEDIUM'), '⚪')
    print(f'{priority_icon} [{i:02d}] {story.title}')
    print(f'     Categoria: {story.category} | Pontos: {story.points}')
    print(f'     {story.narrative_persona}, {story.narrative_action}')
    print()

db.commit()
print('=' * 60)
print(f'\n✅ {len(stories_data)} User Stories salvas com sucesso!')
print(f'📊 Visualize no dashboard: http://localhost:9000')
db.close()
