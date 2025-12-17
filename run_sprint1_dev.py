# -*- coding: utf-8 -*-
"""
Desenvolvimento Autonomo - Sprint 1
====================================
Executa o desenvolvimento das stories do Sprint 1 usando agentes inteligentes.
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
from pathlib import Path

from factory.ai.claude_integration import ClaudeClient, AgentBrain
from factory.database.connection import SessionLocal
from factory.database.models import Story, Task, Agent, ActivityLog
from factory.core.story_generator import AGENT_SPECIALTIES

# Configuracao
PROJECT_ID = "PROJ-20251216221517"
PROJECT_PATH = Path(r"C:\Users\lcruz\Fabrica de Agentes\projects\belgo-bpm-platform")
SPRINT = 1


def log_activity(db, agent_id: str, message: str, level: str = "INFO",
                 story_id: str = None, task_id: str = None):
    """Registra atividade no banco"""
    log = ActivityLog(
        source=agent_id,
        level=level,
        message=message,
        project_id=PROJECT_ID,
        agent_id=agent_id,
        story_id=story_id,
        task_id=task_id,
        event_type="task_progress",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

    icon = {"INFO": "📝", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}.get(level, "📝")
    print(f"{icon} [{agent_id}] {message}")


def update_agent_status(db, agent_id: str, status: str, story_id: str = None):
    """Atualiza status do agente"""
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if agent:
        agent.status = status
        agent.current_story_id = story_id
        agent.current_project_id = PROJECT_ID if status == "EXECUTING" else None
        agent.last_activity = datetime.now(timezone.utc)
        db.commit()


def update_story_status(db, story: Story, status: str):
    """Atualiza status da story"""
    story.status = status
    if status == "IN_PROGRESS" and not story.started_at:
        story.started_at = datetime.now(timezone.utc)
    elif status == "DONE":
        story.completed_at = datetime.now(timezone.utc)
    story.updated_at = datetime.now(timezone.utc)
    db.commit()


def update_task_status(db, task: Task, status: str, result: str = None):
    """Atualiza status da task"""
    task.status = status
    if status == "in_progress" and not task.started_at:
        task.started_at = datetime.now(timezone.utc)
    elif status == "completed":
        task.completed_at = datetime.now(timezone.utc)
        task.result = result
    task.updated_at = datetime.now(timezone.utc)
    db.commit()


def generate_code_for_task(client: ClaudeClient, task: Task, story: Story) -> str:
    """Gera codigo usando Claude para uma task especifica"""

    agent_info = AGENT_SPECIALTIES.get(task.agent_id, {})
    agent_name = agent_info.get("name", "Agente")

    # Preparar contexto
    acceptance_criteria = story.acceptance_criteria
    if isinstance(acceptance_criteria, str):
        try:
            acceptance_criteria = json.loads(acceptance_criteria)
        except:
            acceptance_criteria = [acceptance_criteria]

    technical_notes = story.technical_notes
    if isinstance(technical_notes, str):
        try:
            technical_notes = json.loads(technical_notes)
        except:
            technical_notes = [technical_notes]

    # Determinar linguagem e tipo de arquivo
    if task.task_type in ["database", "backend"]:
        language = "python"
        file_ext = ".py"
    elif task.task_type == "frontend":
        language = "vue"
        file_ext = ".vue"
    elif task.task_type == "design":
        language = "css"
        file_ext = ".css"
    else:
        language = "python"
        file_ext = ".py"

    prompt = f"""Voce eh o agente {agent_name} ({task.agent_id}) da Fabrica de Agentes.

TAREFA: {task.title}
DESCRICAO: {task.description}
TIPO: {task.task_type}

STORY RELACIONADA: {story.title}
{story.narrative_persona}, {story.narrative_action}, {story.narrative_benefit}

CRITERIOS DE ACEITE DA STORY:
{json.dumps(acceptance_criteria, indent=2, ensure_ascii=False)}

NOTAS TECNICAS:
{json.dumps(technical_notes, indent=2, ensure_ascii=False)}

CONTEXTO DO PROJETO:
- Plataforma de visualizacao de processos BPM (AS-IS/TO-BE)
- Projeto GTM GO Wire da Belgo Mineira
- Stack: FastAPI + Vue.js 3 + SQLite + Tailwind CSS
- Biblioteca de diagramas: Vue Flow

INSTRUCOES:
1. Gere codigo {language} completo e funcional
2. Inclua imports necessarios
3. Adicione docstrings e comentarios
4. Siga boas praticas e padroes de mercado
5. O codigo deve ser production-ready

Responda APENAS com o codigo, sem explicacoes adicionais.
"""

    response = client.chat(
        message=prompt,
        system_prompt=f"Voce eh um desenvolvedor senior especialista em {language}. Gere codigo limpo, bem documentado e funcional.",
        max_tokens=4000
    )

    if response.success:
        code = response.content
        # Limpar markdown se houver
        if code.startswith("```"):
            lines = code.split("\n")
            # Remover primeira e ultima linha se forem ```
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        return code
    else:
        return f"# Erro ao gerar codigo: {response.error}"


def get_file_path_for_task(task: Task, story: Story) -> Path:
    """Determina o caminho do arquivo para a task"""

    # Extrair nome base da story
    story_name = story.title.lower()
    story_name = story_name.replace(" ", "_").replace("-", "_")
    story_name = "".join(c for c in story_name if c.isalnum() or c == "_")[:30]

    if task.task_type == "database":
        return PROJECT_PATH / "database" / f"{story_name}_models.py"
    elif task.task_type == "backend":
        return PROJECT_PATH / "backend" / "api" / f"{story_name}_api.py"
    elif task.task_type == "frontend":
        component_name = "".join(word.capitalize() for word in story_name.split("_"))
        return PROJECT_PATH / "frontend" / "components" / f"{component_name}.vue"
    elif task.task_type == "design":
        return PROJECT_PATH / "frontend" / "assets" / f"{story_name}.css"
    elif task.task_type == "testing":
        return PROJECT_PATH / "tests" / f"test_{story_name}.py"
    elif task.task_type == "documentation":
        return PROJECT_PATH / "docs" / f"{story_name}.md"
    else:
        return PROJECT_PATH / f"{story_name}_{task.task_type}.py"


def process_task(db, client: ClaudeClient, task: Task, story: Story) -> bool:
    """Processa uma task individual"""

    agent_id = task.agent_id
    agent_info = AGENT_SPECIALTIES.get(agent_id, {})
    agent_name = agent_info.get("name", "Agente")

    # Atualizar status
    update_agent_status(db, agent_id, "EXECUTING", story.story_id)
    update_task_status(db, task, "in_progress")
    log_activity(db, agent_id, f"Iniciando: {task.title[:50]}...", "INFO", story.story_id, task.task_id)

    try:
        # Pular tasks de review e QA por enquanto (precisam de codigo primeiro)
        if task.task_type in ["review", "testing"]:
            log_activity(db, agent_id, f"Task de {task.task_type} sera executada apos desenvolvimento", "INFO", story.story_id, task.task_id)
            update_task_status(db, task, "pending")
            update_agent_status(db, agent_id, "STANDBY")
            return True

        # Gerar codigo
        log_activity(db, agent_id, f"Gerando codigo com IA...", "INFO", story.story_id, task.task_id)
        code = generate_code_for_task(client, task, story)

        if code.startswith("# Erro"):
            log_activity(db, agent_id, f"Erro na geracao de codigo", "ERROR", story.story_id, task.task_id)
            update_task_status(db, task, "failed", code)
            update_agent_status(db, agent_id, "ERROR")
            return False

        # Salvar arquivo
        file_path = get_file_path_for_task(task, story)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        log_activity(db, agent_id, f"Arquivo criado: {file_path.name}", "SUCCESS", story.story_id, task.task_id)

        # Atualizar task como completa
        update_task_status(db, task, "completed", f"Arquivo: {file_path}")
        update_agent_status(db, agent_id, "STANDBY")

        # Atualizar metricas do agente
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if agent:
            agent.tasks_completed = (agent.tasks_completed or 0) + 1
            db.commit()

        return True

    except Exception as e:
        log_activity(db, agent_id, f"Erro: {str(e)}", "ERROR", story.story_id, task.task_id)
        update_task_status(db, task, "failed", str(e))
        update_agent_status(db, agent_id, "ERROR")
        return False


def process_story(db, client: ClaudeClient, story: Story) -> bool:
    """Processa uma story completa com todas as suas tasks"""

    print(f"\n{'='*60}")
    print(f"📋 STORY: {story.title}")
    print(f"   ID: {story.story_id}")
    print(f"   Pontos: {story.points} | Horas: {story.estimated_hours}h")
    print(f"{'='*60}")

    # Atualizar status da story
    update_story_status(db, story, "IN_PROGRESS")
    log_activity(db, "AGT-01", f"Iniciando story: {story.title}", "INFO", story.story_id)

    # Buscar tasks da story
    tasks = db.query(Task).filter(
        Task.story_id == story.story_id
    ).order_by(Task.priority).all()

    print(f"   Tasks: {len(tasks)}")

    completed = 0
    failed = 0

    for task in tasks:
        print(f"\n   → Task: {task.title[:50]}...")
        print(f"     Agente: {task.agent_id} | Tipo: {task.task_type}")

        success = process_task(db, client, task, story)

        if success:
            completed += 1
        else:
            failed += 1

        # Pequena pausa para nao sobrecarregar API
        time.sleep(1)

    # Atualizar status final da story
    if failed == 0:
        update_story_status(db, story, "DONE")
        log_activity(db, "AGT-01", f"Story concluida: {story.title}", "SUCCESS", story.story_id)
        return True
    else:
        update_story_status(db, story, "IN_PROGRESS")
        log_activity(db, "AGT-01", f"Story com falhas: {failed} tasks falharam", "WARNING", story.story_id)
        return False


def main():
    print("=" * 70)
    print("  DESENVOLVIMENTO AUTONOMO - SPRINT 1")
    print("  Projeto: Belgo BPM Platform")
    print("=" * 70)
    print()

    # Conectar
    db = SessionLocal()
    client = ClaudeClient()

    if not client.is_available():
        print("[ERRO] Claude API nao disponivel!")
        return

    print("[OK] Claude API conectada")
    print(f"[OK] Projeto: {PROJECT_ID}")
    print(f"[OK] Sprint: {SPRINT}")
    print(f"[OK] Output: {PROJECT_PATH}")
    print()

    # Buscar stories do Sprint 1
    stories = db.query(Story).filter(
        Story.project_id == PROJECT_ID,
        Story.sprint == SPRINT,
        Story.status.in_(["BACKLOG", "TODO", "IN_PROGRESS"])
    ).order_by(Story.priority.desc()).all()

    print(f"[INFO] {len(stories)} stories no Sprint {SPRINT}")
    print()

    # Log inicio
    log_activity(db, "AGT-01", f"Sprint {SPRINT} iniciado - {len(stories)} stories", "INFO")

    # Processar cada story
    completed_stories = 0
    failed_stories = 0

    for i, story in enumerate(stories, 1):
        print(f"\n[{i}/{len(stories)}] Processando story...")

        try:
            success = process_story(db, client, story)
            if success:
                completed_stories += 1
            else:
                failed_stories += 1
        except Exception as e:
            print(f"[ERRO] Excecao: {e}")
            failed_stories += 1

        # Pausa entre stories
        time.sleep(2)

    # Resumo final
    print()
    print("=" * 70)
    print("  SPRINT 1 - RESUMO")
    print("=" * 70)
    print(f"  Stories Completas: {completed_stories}")
    print(f"  Stories com Falhas: {failed_stories}")
    print()
    print(f"  📁 Arquivos gerados em: {PROJECT_PATH}")
    print(f"  📊 Dashboard: http://localhost:9000")
    print("=" * 70)

    log_activity(db, "AGT-01", f"Sprint {SPRINT} finalizado - {completed_stories} completas, {failed_stories} falhas", "INFO")

    db.close()


if __name__ == "__main__":
    main()
