# -*- coding: utf-8 -*-
"""
Desenvolvimento Autonomo - Belgo BPM Platform
=============================================
Este script executa o desenvolvimento autonomo usando os agentes da Fabrica.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
os.chdir(r'C:\Users\lcruz\Fabrica de Agentes')

from dotenv import load_dotenv
load_dotenv()

import json
import time
from datetime import datetime
from pathlib import Path

from factory.ai.claude_integration import ClaudeClient, AgentBrain
from factory.database.connection import SessionLocal
from factory.database.models import Story, Project, Agent, ActivityLog

# Configuracao
PROJECT_ID = 'PROJ-20251216221517'
PROJECT_PATH = Path(r'C:\Users\lcruz\Fabrica de Agentes\projects\belgo-bpm-platform')

def log_activity(db, agent_id, message, level='INFO', project_id=PROJECT_ID):
    """Registra atividade no banco de dados"""
    log = ActivityLog(
        source=f'AGT-{agent_id:02d}',
        level=level,
        message=message,
        project_id=project_id,
        agent_id=f'AGT-{agent_id:02d}',
        event_type='task_progress',
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    print(f'[AGT-{agent_id:02d}] {message}')

def update_agent_status(db, agent_id, status, current_task=None):
    """Atualiza status do agente"""
    agent = db.query(Agent).filter(Agent.agent_id == f'AGT-{agent_id:02d}').first()
    if agent:
        agent.status = status
        agent.current_task_id = current_task
        agent.last_activity = datetime.utcnow()
        db.commit()

def develop_story(db, client, story, project_path):
    """Desenvolve uma story usando Claude AI"""

    # Determinar agente responsavel
    category_agents = {
        'database': 7,   # DBA
        'backend': 8,    # Backend Dev
        'frontend': 9,   # Frontend Dev
        'api': 8,        # Backend Dev
        'security': 10,  # Security
    }

    agent_id = category_agents.get(story.category, 8)

    # Atualizar status
    update_agent_status(db, agent_id, 'EXECUTING', story.story_id)
    log_activity(db, agent_id, f'Iniciando: {story.title}')

    # Atualizar story
    story.status = 'IN_PROGRESS'
    db.commit()

    # Gerar codigo com Claude
    brain = AgentBrain(
        agent_id=f'AGT-{agent_id:02d}',
        agent_role=story.category,
        agent_capabilities=[story.category, 'code_generation', 'documentation']
    )

    prompt = f"""Gere o codigo para implementar a seguinte User Story:

TITULO: {story.title}
DESCRICAO: {story.description}
CATEGORIA: {story.category}
PERSONA: {story.narrative_persona}
ACAO: {story.narrative_action}
BENEFICIO: {story.narrative_benefit}
CRITERIOS DE ACEITE: {story.acceptance_criteria}

CONTEXTO DO PROJETO:
- Plataforma de visualizacao de processos BPM (AS-IS/TO-BE)
- Stack: FastAPI (backend), Vue.js 3 (frontend), SQLite (database)
- Biblioteca de diagramas: Vue Flow ou similar para BPMN
- Estilo: Tailwind CSS

Gere o codigo completo e funcional para esta story. Inclua:
1. Arquivo principal com a implementacao
2. Comentarios explicativos
3. Estrutura de dados se necessario

Responda com o codigo organizado.
"""

    log_activity(db, agent_id, f'Gerando codigo com IA...')

    response = brain.generate_code_intelligent(
        task=story.title,
        language='python' if story.category in ['backend', 'database', 'api'] else 'javascript',
        context={'story': story.title, 'category': story.category}
    )

    if response.success:
        # Salvar arquivo
        if story.category == 'database':
            file_path = project_path / 'database' / f'{story.story_id.lower().replace("-", "_")}_models.py'
        elif story.category == 'backend':
            file_path = project_path / 'backend' / f'{story.story_id.lower().replace("-", "_")}_api.py'
        elif story.category == 'frontend':
            file_path = project_path / 'frontend' / f'{story.story_id.lower().replace("-", "_")}.vue'
        else:
            file_path = project_path / f'{story.story_id.lower().replace("-", "_")}.py'

        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Limpar codigo (remover markdown)
        code = response.content
        if code.startswith('```'):
            lines = code.split('\n')
            code = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        log_activity(db, agent_id, f'Arquivo gerado: {file_path.name}')

        # Atualizar story
        story.status = 'DONE'
        story.artifacts = json.dumps([str(file_path)], ensure_ascii=False)
        db.commit()

        log_activity(db, agent_id, f'Story concluida: {story.title}', level='INFO')
        update_agent_status(db, agent_id, 'STANDBY')

        return True
    else:
        log_activity(db, agent_id, f'Erro ao gerar codigo: {response.error}', level='ERROR')
        story.status = 'BLOCKED'
        db.commit()
        update_agent_status(db, agent_id, 'ERROR')
        return False

def main():
    print('=' * 70)
    print('  DESENVOLVIMENTO AUTONOMO - BELGO BPM PLATFORM')
    print('  Fabrica de Agentes v2.0')
    print('=' * 70)
    print()

    # Conectar
    db = SessionLocal()
    client = ClaudeClient()

    if not client.is_available():
        print('[ERRO] Claude API nao disponivel!')
        return

    print('[OK] Claude API conectada')
    print(f'[OK] Projeto: {PROJECT_ID}')
    print(f'[OK] Path: {PROJECT_PATH}')
    print()

    # Buscar stories pendentes
    stories = db.query(Story).filter(
        Story.project_id == PROJECT_ID,
        Story.status.in_(['TODO', 'BLOCKED'])
    ).order_by(
        Story.priority.desc(),  # HIGH primeiro
        Story.points.asc()      # Menores primeiro
    ).all()

    print(f'[INFO] {len(stories)} stories para desenvolver')
    print()

    # Log inicio
    log_activity(db, 1, f'Desenvolvimento autonomo iniciado - {len(stories)} stories')

    # Processar cada story
    completed = 0
    failed = 0

    for i, story in enumerate(stories, 1):
        print(f'\n--- [{i}/{len(stories)}] {story.title} ({story.category}) ---')

        try:
            success = develop_story(db, client, story, PROJECT_PATH)
            if success:
                completed += 1
            else:
                failed += 1
        except Exception as e:
            print(f'[ERRO] Excecao: {e}')
            failed += 1

        # Pequena pausa para nao sobrecarregar API
        time.sleep(2)

    # Resumo final
    print()
    print('=' * 70)
    print(f'  DESENVOLVIMENTO CONCLUIDO')
    print(f'  Completas: {completed} | Falhas: {failed}')
    print('=' * 70)

    log_activity(db, 1, f'Desenvolvimento autonomo finalizado - {completed} completas, {failed} falhas')

    db.close()

if __name__ == '__main__':
    main()
