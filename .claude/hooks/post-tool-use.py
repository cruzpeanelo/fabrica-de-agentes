#!/usr/bin/env python
"""
Claude Code Hook: Post-Tool-Use
Intercepta cada execucao de ferramenta e registra automaticamente no banco de dados.

Este hook eh chamado AUTOMATICAMENTE pelo Claude Code apos cada uso de ferramenta.
"""
import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime

# Adiciona path da factory
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "factory"))
sys.path.insert(0, str(PROJECT_ROOT / "factory" / "database"))

def extract_agent_from_context(tool_input: dict, tool_name: str) -> str:
    """Tenta extrair ID do agente do contexto"""
    # Verifica se ha referencia a agente no input
    input_str = json.dumps(tool_input).lower()

    # Padrao: "agente 01", "agent_05", "agente-08"
    patterns = [
        r'agente[\s_-]*(\d{1,2})',
        r'agent[\s_-]*(\d{1,2})',
        r'ag[\s_-]*(\d{1,2})',
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1).zfill(2)

    # Default baseado no tipo de ferramenta
    tool_agent_map = {
        'Write': '08',      # Backend/Codigo
        'Edit': '08',       # Backend/Codigo
        'Read': '05',       # Analise
        'Bash': '14',       # DevOps
        'Glob': '05',       # Analise
        'Grep': '05',       # Analise
        'Task': '01',       # Gestao
    }

    return tool_agent_map.get(tool_name, '01')

def log_tool_execution(tool_name: str, tool_input: dict, tool_output: str, success: bool):
    """Registra execucao de ferramenta no banco de dados"""
    try:
        from factory.database.connection import SessionLocal, init_db
        from factory.database.models import ActivityLog

        init_db()
        db = SessionLocal()

        agent_id = extract_agent_from_context(tool_input, tool_name)

        # Monta mensagem descritiva
        if tool_name == 'Write':
            file_path = tool_input.get('file_path', 'arquivo')
            msg = f"Arquivo criado: {Path(file_path).name}"
            event_type = "code_generated"

        elif tool_name == 'Edit':
            file_path = tool_input.get('file_path', 'arquivo')
            msg = f"Arquivo editado: {Path(file_path).name}"
            event_type = "file_edited"

        elif tool_name == 'Bash':
            cmd = tool_input.get('command', '')[:100]
            msg = f"Comando executado: {cmd}"
            event_type = "bash_executed" if success else "bash_failed"

        elif tool_name == 'Task':
            prompt = tool_input.get('prompt', '')[:100]
            msg = f"Subagente lancado: {prompt}"
            event_type = "subagent_launched"

        elif tool_name in ['Read', 'Glob', 'Grep']:
            # Operacoes de leitura - nao loga
            db.close()
            return

        else:
            msg = f"Ferramenta {tool_name} executada"
            event_type = "tool_executed"

        # Cria log
        log = ActivityLog(
            source=f"agent_{agent_id}",
            source_id=agent_id,
            agent_id=agent_id,
            level="INFO" if success else "WARNING",
            event_type=event_type,
            message=msg,
            details={"tool": tool_name, "success": success},
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        db.close()

    except Exception as e:
        # Loga erro em arquivo
        error_log = PROJECT_ROOT / "factory" / "hook_errors.log"
        try:
            with open(error_log, 'a') as f:
                f.write(f"{datetime.now()} - Error in hook: {e}\n")
        except:
            pass

def main():
    """Entry point do hook"""
    # Le input do Claude Code via stdin
    try:
        hook_data = json.load(sys.stdin)
    except:
        return

    tool_name = hook_data.get('tool_name', '')
    tool_input = hook_data.get('tool_input', {})
    tool_output = hook_data.get('tool_output', '')
    success = hook_data.get('success', True)

    # Ignora algumas ferramentas que geram muito ruido
    ignored_tools = ['TodoWrite', 'AgentOutputTool', 'BashOutput']
    if tool_name in ignored_tools:
        return

    log_tool_execution(tool_name, tool_input, tool_output, success)

if __name__ == "__main__":
    main()
