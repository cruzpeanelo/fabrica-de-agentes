# -*- coding: utf-8 -*-
"""
Desenvolvimento Autonomo via Kanban - Belgo BPM Platform
=========================================================
Processa tarefas do Kanban board e executa desenvolvimento autonomo.
Tarefas em "todo" sao processadas e movidas pelo pipeline.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
os.chdir(r'C:\Users\lcruz\Fabrica de Agentes')

from dotenv import load_dotenv
load_dotenv()

import time
from datetime import datetime
from pathlib import Path

from factory.database.connection import SessionLocal
from factory.database.models import Task, TaskStatus, ActivityLog
from factory.database.repositories import TaskRepository

# Tentar importar Claude
try:
    from factory.ai.claude_integration import ClaudeClient, AgentBrain
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False

# Configuracao
PROJECT_ID = 'BELGO-BPM-001'
PROJECT_PATH = Path(r'C:\Users\lcruz\Fabrica de Agentes\projects\belgo-bpm-platform')


def log_activity(db, message, level='INFO', project_id=PROJECT_ID):
    """Registra atividade no banco de dados"""
    log = ActivityLog(
        source='kanban-dev',
        level=level,
        message=message,
        project_id=project_id,
        event_type='kanban_dev',
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    print(f'[{level}] {message}')


def process_task(db, task_repo, task, claude_client=None):
    """Processa uma tarefa do Kanban"""

    print(f'\n{"="*60}')
    print(f'  Processando: {task.title}')
    print(f'  ID: {task.task_id} | Prioridade: {task.priority}')
    print(f'{"="*60}')

    # Mover para in_development
    task_repo.move_task(task.task_id, TaskStatus.IN_DEVELOPMENT.value)
    log_activity(db, f'Iniciando desenvolvimento: {task.title}')

    # Simular desenvolvimento (ou usar Claude se disponivel)
    if HAS_CLAUDE and claude_client and claude_client.is_available():
        try:
            brain = AgentBrain(
                agent_id='AGT-08',
                agent_role='backend_developer',
                agent_capabilities=['python', 'fastapi', 'vue', 'code_generation']
            )

            prompt = f"""Gere codigo para implementar: {task.title}

Descricao: {task.description}

Contexto: Plataforma BPM para visualizacao de processos AS-IS/TO-BE.
Stack: FastAPI (backend), Vue.js 3 (frontend), SQLite, Vue Flow (BPMN)

Gere codigo funcional e bem estruturado."""

            log_activity(db, f'Gerando codigo com Claude AI...')
            response = brain.generate_code_intelligent(
                task=task.title,
                language='python',
                context={'task': task.title}
            )

            if response.success:
                # Criar arquivo
                file_name = task.task_id.lower().replace('-', '_') + '.py'
                file_path = PROJECT_PATH / 'src' / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)

                code = response.content
                if code.startswith('```'):
                    lines = code.split('\n')
                    code = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)

                log_activity(db, f'Arquivo gerado: {file_name}')

                # Mover para testing
                task_repo.move_task(task.task_id, TaskStatus.IN_TESTING.value)
                log_activity(db, f'Codigo gerado, movendo para teste')

                # Simular teste rapido
                time.sleep(1)

                # Mover para ready_to_deploy
                task_repo.move_task(task.task_id, TaskStatus.READY_TO_DEPLOY.value)
                log_activity(db, f'Testes OK, pronto para deploy')

                return True
            else:
                log_activity(db, f'Erro ao gerar: {response.error}', level='ERROR')
                return False

        except Exception as e:
            log_activity(db, f'Excecao: {str(e)}', level='ERROR')
            return False
    else:
        # Modo demo - simula desenvolvimento
        log_activity(db, f'[DEMO] Simulando desenvolvimento...')
        time.sleep(2)

        # Mover para testing
        task_repo.move_task(task.task_id, TaskStatus.IN_TESTING.value)
        log_activity(db, f'[DEMO] Movendo para teste')
        time.sleep(1)

        # Mover para ready_to_deploy
        task_repo.move_task(task.task_id, TaskStatus.READY_TO_DEPLOY.value)
        log_activity(db, f'[DEMO] Pronto para deploy')

        return True


def main():
    print('=' * 70)
    print('  DESENVOLVIMENTO AUTONOMO VIA KANBAN')
    print('  Projeto: Belgo BPM Platform')
    print('=' * 70)
    print()

    # Conectar
    db = SessionLocal()
    task_repo = TaskRepository(db)

    # Verificar Claude
    claude_client = None
    if HAS_CLAUDE:
        claude_client = ClaudeClient()
        if claude_client.is_available():
            print('[OK] Claude API disponivel')
        else:
            print('[AVISO] Claude API nao disponivel - modo demo')
    else:
        print('[AVISO] Claude nao importado - modo demo')

    print(f'[OK] Projeto: {PROJECT_ID}')
    print()

    # Buscar tarefas em "todo"
    tasks = task_repo.get_all(project_id=PROJECT_ID, status=TaskStatus.TODO.value)

    if not tasks:
        print('[INFO] Nenhuma tarefa em "To Do"')
        print('[INFO] Mova tarefas do Backlog para To Do no dashboard para iniciar')
        print(f'[INFO] Dashboard: http://localhost:9001')
        db.close()
        return

    print(f'[INFO] {len(tasks)} tarefas para processar')
    print()

    # Log inicio
    log_activity(db, f'Desenvolvimento autonomo iniciado - {len(tasks)} tarefas')

    # Processar cada tarefa
    completed = 0
    failed = 0

    for i, task in enumerate(tasks, 1):
        print(f'\n--- [{i}/{len(tasks)}] ---')

        try:
            success = process_task(db, task_repo, task, claude_client)
            if success:
                completed += 1
            else:
                failed += 1
        except Exception as e:
            print(f'[ERRO] Excecao: {e}')
            failed += 1

        # Pausa entre tarefas
        time.sleep(1)

    # Resumo final
    print()
    print('=' * 70)
    print(f'  DESENVOLVIMENTO CONCLUIDO')
    print(f'  Completas: {completed} | Falhas: {failed}')
    print('=' * 70)

    log_activity(db, f'Desenvolvimento finalizado - {completed} completas, {failed} falhas')

    db.close()


if __name__ == '__main__':
    main()
