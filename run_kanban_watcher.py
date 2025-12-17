# -*- coding: utf-8 -*-
"""
Kanban Watcher - Desenvolvimento Autonomo Automatico
=====================================================
Monitora o Kanban board e processa tarefas automaticamente
quando entram na coluna "To Do".

Uso: python run_kanban_watcher.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
os.chdir(r'C:\Users\lcruz\Fabrica de Agentes')

from dotenv import load_dotenv
load_dotenv()

import time
import signal
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


def log_activity(db, message, level='INFO', project_id=None):
    """Registra atividade no banco de dados"""
    log = ActivityLog(
        source='kanban-watcher',
        level=level,
        message=message,
        project_id=project_id,
        event_type='kanban_watcher',
        timestamp=datetime.now()
    )
    db.add(log)
    db.commit()


def process_task(db, task_repo, task, claude_client=None):
    """Processa uma tarefa do Kanban"""
    project_id = task.project_id
    project_path = PROJECT_PATH / project_id.lower().replace('-', '_')

    print(f'\n  [PROCESSANDO] {task.task_id}: {task.title}')

    # Mover para in_development
    task_repo.move_task(task.task_id, TaskStatus.IN_DEVELOPMENT.value)
    log_activity(db, f'Iniciando: {task.title}', project_id=project_id)

    # Usar Claude se disponivel
    if HAS_CLAUDE and claude_client and claude_client.is_available():
        try:
            brain = AgentBrain(
                agent_id='AGT-08',
                agent_role='backend_developer',
                agent_capabilities=['python', 'fastapi', 'vue', 'code_generation']
            )

            response = brain.generate_code_intelligent(
                task=task.title,
                language='python',
                context={'task': task.title, 'description': task.description}
            )

            if response.success:
                # Criar arquivo
                file_name = task.task_id.lower().replace('-', '_') + '.py'
                file_path = project_path / 'src' / file_name
                file_path.parent.mkdir(parents=True, exist_ok=True)

                code = response.content
                if code.startswith('```'):
                    lines = code.split('\n')
                    code = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)

                print(f'    [OK] Arquivo: {file_name}')
                log_activity(db, f'Gerado: {file_name}', project_id=project_id)

                # Pipeline: Dev -> Test -> Ready
                task_repo.move_task(task.task_id, TaskStatus.IN_TESTING.value)
                time.sleep(0.5)
                task_repo.move_task(task.task_id, TaskStatus.READY_TO_DEPLOY.value)

                print(f'    [OK] Pronto para deploy')
                log_activity(db, f'Concluido: {task.title}', project_id=project_id)
                return True
            else:
                print(f'    [ERRO] {response.error}')
                log_activity(db, f'Erro: {response.error}', level='ERROR', project_id=project_id)
                return False

        except Exception as e:
            print(f'    [ERRO] {str(e)}')
            log_activity(db, f'Excecao: {str(e)}', level='ERROR', project_id=project_id)
            return False
    else:
        # Modo demo
        print(f'    [DEMO] Simulando desenvolvimento...')
        time.sleep(2)
        task_repo.move_task(task.task_id, TaskStatus.IN_TESTING.value)
        time.sleep(1)
        task_repo.move_task(task.task_id, TaskStatus.READY_TO_DEPLOY.value)
        print(f'    [DEMO] Pronto para deploy')
        return True


def check_and_process(db, task_repo, claude_client):
    """Verifica e processa tarefas em To Do"""
    # Buscar TODAS as tarefas em "todo" (de qualquer projeto)
    tasks = task_repo.get_all(status=TaskStatus.TODO.value)

    if tasks:
        print(f'\n[WATCHER] {len(tasks)} tarefa(s) em To Do')

        for task in tasks:
            if not running:
                break
            process_task(db, task_repo, task, claude_client)
            time.sleep(1)  # Pausa entre tarefas

        return len(tasks)
    return 0


def main():
    global running

    print('=' * 60)
    print('  KANBAN WATCHER - Desenvolvimento Autonomo')
    print('  Monitorando tarefas em "To Do"...')
    print('  Pressione Ctrl+C para encerrar')
    print('=' * 60)
    print()

    # Inicializar
    db = SessionLocal()
    task_repo = TaskRepository(db)

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

    log_activity(db, 'Watcher iniciado')

    # Loop principal
    while running:
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')

            # Verificar tarefas
            processed = check_and_process(db, task_repo, claude_client)

            if processed == 0:
                print(f'[{timestamp}] Aguardando tarefas em To Do...', end='\r')

            # Aguardar proximo ciclo
            for _ in range(CHECK_INTERVAL):
                if not running:
                    break
                time.sleep(1)

        except Exception as e:
            print(f'\n[ERRO] {str(e)}')
            time.sleep(5)

    # Cleanup
    log_activity(db, 'Watcher encerrado')
    db.close()
    print('\n[WATCHER] Encerrado.')


if __name__ == '__main__':
    main()
