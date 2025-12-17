# -*- coding: utf-8 -*-
"""
Story Watcher - Desenvolvimento Autonomo de User Stories
=========================================================
Monitora o Kanban de Stories e processa automaticamente
quando entram na coluna "Ready" ou "In Progress".

Uso: python run_story_watcher.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
os.chdir(r'C:\Users\lcruz\Fabrica de Agentes')
sys.path.insert(0, r'C:\Users\lcruz\Fabrica de Agentes')

from dotenv import load_dotenv
load_dotenv()

import time
import signal
from datetime import datetime
from pathlib import Path

from factory.database.connection import SessionLocal
from factory.database.models import (
    Story, StoryStatus, StoryTask, StoryTaskStatus,
    StoryDocumentation, ActivityLog
)
from factory.database.repositories import (
    StoryRepository, StoryTaskRepository, StoryDocumentationRepository
)

# Tentar importar Claude
try:
    from factory.ai.claude_integration import ClaudeClient, AgentBrain
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False

# Configuracao
CHECK_INTERVAL = 30  # segundos entre verificacoes
PROJECT_PATH = Path(r'C:\Users\lcruz\Fabrica de Agentes\projects')

# Flag para shutdown graceful
running = True


def signal_handler(sig, frame):
    """Handler para Ctrl+C"""
    global running
    print('\n[WATCHER] Encerrando...')
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def log_activity(db, message, level='INFO', project_id=None, story_id=None):
    """Registra atividade no banco de dados"""
    log = ActivityLog(
        source='story-watcher',
        level=level,
        message=message,
        project_id=project_id,
        event_type='story_watcher',
        timestamp=datetime.now()
    )
    db.add(log)
    db.commit()


def process_story_task(db, task_repo, doc_repo, task, story, claude_client=None):
    """Processa uma task de uma story"""
    print(f'    [TASK] {task.task_id}: {task.title}')

    # Mover para in_progress
    task_repo.update(task.task_id, {"status": StoryTaskStatus.IN_PROGRESS.value})

    # Usar Claude se disponivel
    if HAS_CLAUDE and claude_client and claude_client.is_available():
        try:
            brain = AgentBrain(
                agent_id='AGT-08',
                agent_role='backend_developer',
                agent_capabilities=['python', 'fastapi', 'vue', 'code_generation']
            )

            prompt = f"""Gere codigo para implementar a seguinte task:

Task: {task.title}
Descricao: {task.description or 'N/A'}
Tipo: {task.task_type}

Contexto da Story:
- Titulo: {story.title}
- Narrativa: Como um {story.persona}, eu quero {story.action}, para que {story.benefit}
- Criterios de Aceite: {', '.join(story.acceptance_criteria or [])}

Gere codigo Python/Vue.js funcional e bem estruturado."""

            response = brain.generate_code_intelligent(
                task=task.title,
                language='python',
                context={'story': story.title, 'task': task.title}
            )

            if response.success:
                # Criar arquivo
                project_path = PROJECT_PATH / story.project_id.lower().replace('-', '_')
                file_name = task.task_id.lower().replace('-', '_') + '.py'
                file_path = project_path / 'src' / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)

                code = response.content
                if code.startswith('```'):
                    lines = code.split('\n')
                    code = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)

                # Completar task com output
                task_repo.complete(task.task_id, {
                    "files_created": [str(file_path)],
                    "code_output": code[:500] + "..." if len(code) > 500 else code,
                    "actual_hours": 0.5
                })

                # Criar documentacao automatica
                doc_repo.create({
                    "story_id": story.story_id,
                    "task_id": task.task_id,
                    "doc_type": "technical",
                    "title": f"Implementacao: {task.title}",
                    "content": f"""# {task.title}

## Arquivo Gerado
- `{file_name}`

## Resumo
Task implementada automaticamente pelo Claude AI.

## Como Testar
1. Verificar se o arquivo foi criado em `{file_path}`
2. Revisar o codigo gerado
3. Executar testes unitarios
""",
                    "files_created": [str(file_path)],
                    "test_instructions": "Executar pytest no diretorio do projeto"
                })

                print(f'      [OK] Arquivo: {file_name}')
                return True
            else:
                print(f'      [ERRO] {response.error}')
                return False

        except Exception as e:
            print(f'      [ERRO] {str(e)}')
            return False
    else:
        # Modo demo - simula desenvolvimento
        print(f'      [DEMO] Simulando desenvolvimento...')
        time.sleep(1)

        # Completar task em modo demo
        task_repo.complete(task.task_id, {
            "files_created": ["demo_file.py"],
            "code_output": f"# Demo code for: {task.title}\nprint('Hello from {task.task_id}')",
            "actual_hours": 0.25
        })

        print(f'      [DEMO] Task concluida')
        return True


def process_story(db, story_repo, task_repo, doc_repo, story, claude_client=None):
    """Processa uma story movendo suas tasks pelo pipeline"""
    project_id = story.project_id

    print(f'\n{"="*60}')
    print(f'  Processando Story: {story.title}')
    print(f'  ID: {story.story_id} | {story.story_points} pts | {len(story.story_tasks)} tasks')
    print(f'{"="*60}')

    # Mover story para in_progress se estiver em ready
    if story.status == StoryStatus.READY.value:
        story_repo.move_story(story.story_id, StoryStatus.IN_PROGRESS.value)
        log_activity(db, f'Iniciando: {story.title}', project_id=project_id, story_id=story.story_id)

    # Processar cada task pendente
    tasks_completed = 0
    tasks_failed = 0

    for task in story.story_tasks:
        if task.status == StoryTaskStatus.PENDING.value:
            if not running:
                break

            success = process_story_task(db, task_repo, doc_repo, task, story, claude_client)
            if success:
                tasks_completed += 1
            else:
                tasks_failed += 1

            time.sleep(0.5)  # Pausa entre tasks

    # Atualizar progresso da story
    story_repo.update_progress(story.story_id)

    # Se todas tasks completas, mover para testing
    story = story_repo.get_by_id(story.story_id)
    if story.tasks_completed == story.tasks_total and story.tasks_total > 0:
        story_repo.move_story(story.story_id, StoryStatus.TESTING.value)
        log_activity(db, f'Story pronta para teste: {story.title}', project_id=project_id, story_id=story.story_id)
        print(f'\n  [OK] Story movida para Testing')

        # Simular teste rapido e mover para done
        time.sleep(1)
        story_repo.move_story(story.story_id, StoryStatus.DONE.value)
        log_activity(db, f'Story concluida: {story.title}', project_id=project_id, story_id=story.story_id)
        print(f'  [OK] Story concluida!')

    return tasks_completed, tasks_failed


def check_and_process(db, story_repo, task_repo, doc_repo, claude_client):
    """Verifica e processa stories em Ready ou In Progress com tasks pendentes"""
    # Buscar stories em "ready" ou "in_progress"
    ready_stories = story_repo.get_all(status=StoryStatus.READY.value)
    in_progress_stories = story_repo.get_all(status=StoryStatus.IN_PROGRESS.value)

    # Filtrar apenas stories com tasks pendentes
    stories_to_process = []

    for story in ready_stories + in_progress_stories:
        pending_tasks = [t for t in story.story_tasks if t.status == StoryTaskStatus.PENDING.value]
        if pending_tasks:
            stories_to_process.append(story)

    if stories_to_process:
        print(f'\n[WATCHER] {len(stories_to_process)} story(s) para processar')

        total_completed = 0
        total_failed = 0

        for story in stories_to_process:
            if not running:
                break
            completed, failed = process_story(db, story_repo, task_repo, doc_repo, story, claude_client)
            total_completed += completed
            total_failed += failed
            time.sleep(1)

        return len(stories_to_process), total_completed, total_failed

    return 0, 0, 0


def main():
    global running

    print('=' * 60)
    print('  STORY WATCHER - Desenvolvimento Autonomo de Stories')
    print('  Monitorando stories em "Ready" e "In Progress"...')
    print('  Pressione Ctrl+C para encerrar')
    print('=' * 60)
    print()

    # Inicializar
    db = SessionLocal()
    story_repo = StoryRepository(db)
    task_repo = StoryTaskRepository(db)
    doc_repo = StoryDocumentationRepository(db)

    # Claude
    claude_client = None
    if HAS_CLAUDE:
        claude_client = ClaudeClient()
        if claude_client.is_available():
            print('[OK] Claude API disponivel')
        else:
            print('[AVISO] Claude indisponivel - modo demo')
    else:
        print('[AVISO] Claude nao importado - modo demo')

    print(f'[OK] Verificando a cada {CHECK_INTERVAL}s')
    print()

    log_activity(db, 'Story Watcher iniciado')

    # Loop principal
    while running:
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')

            # Verificar stories
            stories_count, completed, failed = check_and_process(
                db, story_repo, task_repo, doc_repo, claude_client
            )

            if stories_count == 0:
                print(f'[{timestamp}] Aguardando stories em Ready...', end='\r')

            # Aguardar proximo ciclo
            for _ in range(CHECK_INTERVAL):
                if not running:
                    break
                time.sleep(1)

        except Exception as e:
            print(f'\n[ERRO] {str(e)}')
            time.sleep(5)

    # Cleanup
    log_activity(db, 'Story Watcher encerrado')
    db.close()
    print('\n[WATCHER] Encerrado.')


if __name__ == '__main__':
    main()
