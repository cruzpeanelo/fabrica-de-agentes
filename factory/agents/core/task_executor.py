"""
Executor de Tarefas para Agentes
================================

Executa tarefas usando Claude CLI de forma inteligente:
- Monta contexto completo para o agente
- Gerencia timeout e retries
- Processa resultado e extrai informacoes
"""

import json
import subprocess
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import re


@dataclass
class ExecutionResult:
    """Resultado de execucao"""
    success: bool
    output: str
    files_modified: List[str]
    errors: List[str]
    duration_seconds: float
    raw_response: Optional[str] = None


class TaskExecutor:
    """
    Executor de Tarefas via Claude CLI

    Executa tarefas invocando Claude com contexto apropriado.
    """

    def __init__(self,
                 project_path: Optional[Path] = None,
                 timeout: int = 300,
                 max_retries: int = 2):
        """
        Args:
            project_path: Caminho do projeto
            timeout: Timeout em segundos
            max_retries: Tentativas maximas
        """
        self.project_path = project_path or Path.cwd()
        self.timeout = timeout
        self.max_retries = max_retries

    def execute(self,
               task_description: str,
               agent_context: Dict,
               additional_instructions: Optional[str] = None) -> ExecutionResult:
        """
        Executa tarefa via Claude CLI

        Args:
            task_description: Descricao da tarefa
            agent_context: Contexto do agente (conhecimento, memoria, etc)
            additional_instructions: Instrucoes adicionais

        Returns:
            ExecutionResult
        """
        import time
        start_time = time.time()

        # Monta prompt
        prompt = self._build_prompt(task_description, agent_context, additional_instructions)

        # Executa
        for attempt in range(self.max_retries + 1):
            try:
                result = self._run_claude(prompt)
                duration = time.time() - start_time

                # Processa resultado
                parsed = self._parse_result(result)

                return ExecutionResult(
                    success=parsed["success"],
                    output=parsed["output"],
                    files_modified=parsed["files"],
                    errors=parsed["errors"],
                    duration_seconds=duration,
                    raw_response=result
                )

            except subprocess.TimeoutExpired:
                if attempt == self.max_retries:
                    return ExecutionResult(
                        success=False,
                        output="",
                        files_modified=[],
                        errors=["Timeout na execucao"],
                        duration_seconds=time.time() - start_time
                    )
            except Exception as e:
                if attempt == self.max_retries:
                    return ExecutionResult(
                        success=False,
                        output="",
                        files_modified=[],
                        errors=[str(e)],
                        duration_seconds=time.time() - start_time
                    )

        return ExecutionResult(
            success=False,
            output="",
            files_modified=[],
            errors=["Falha apos todas as tentativas"],
            duration_seconds=time.time() - start_time
        )

    def _build_prompt(self,
                     task: str,
                     context: Dict,
                     instructions: Optional[str]) -> str:
        """Constroi prompt para Claude"""

        prompt_parts = [
            "# EXECUCAO AUTONOMA DE AGENTE",
            "",
            f"## Agente: {context.get('agent_id', 'unknown')} - {context.get('agent_name', 'Agent')}",
            f"## Dominio: {context.get('domain', 'general')}",
            "",
            "## TAREFA",
            task,
            ""
        ]

        # Adiciona conhecimento relevante
        if context.get("relevant_knowledge"):
            prompt_parts.append("## CONHECIMENTO RELEVANTE")
            for k in context["relevant_knowledge"][:5]:
                prompt_parts.append(f"- {k.get('content', '')[:200]}")
            prompt_parts.append("")

        # Adiciona experiencias
        if context.get("similar_experiences"):
            prompt_parts.append("## EXPERIENCIAS ANTERIORES")
            for exp in context["similar_experiences"][:3]:
                prompt_parts.append(f"- {exp.get('title', '')}: {exp.get('outcome', '')}")
                if exp.get("lessons"):
                    for lesson in exp["lessons"][:2]:
                        prompt_parts.append(f"  - Licao: {lesson}")
            prompt_parts.append("")

        # Adiciona padroes
        if context.get("patterns"):
            prompt_parts.append("## PADROES DE SUCESSO")
            for p in context["patterns"][:3]:
                prompt_parts.append(f"- {p.get('action', '')} (confianca: {p.get('confidence', 0):.0%})")
            prompt_parts.append("")

        # Adiciona instrucoes
        prompt_parts.extend([
            "## INSTRUCOES",
            "1. Execute a tarefa especificada",
            "2. Use as ferramentas disponiveis (Read, Write, Edit, Bash)",
            "3. Seja preciso e eficiente",
            "4. Documente decisoes importantes"
        ])

        if instructions:
            prompt_parts.append(f"5. {instructions}")

        prompt_parts.extend([
            "",
            "## FORMATO DE RESPOSTA",
            "Ao concluir, retorne um JSON com:",
            "```json",
            "{",
            '  "success": true/false,',
            '  "summary": "resumo do que foi feito",',
            '  "files_modified": ["lista", "de", "arquivos"],',
            '  "decisions": ["decisoes", "tomadas"],',
            '  "lessons_learned": ["licoes", "aprendidas"]',
            "}",
            "```"
        ])

        return "\n".join(prompt_parts)

    def _run_claude(self, prompt: str) -> str:
        """Executa Claude CLI"""
        # Prepara comando
        cmd = [
            "claude",
            "--print",
            "-p", prompt
        ]

        # Executa
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            cwd=str(self.project_path)
        )

        if result.returncode != 0:
            raise Exception(f"Claude CLI falhou: {result.stderr}")

        return result.stdout

    def _parse_result(self, raw: str) -> Dict:
        """Parseia resultado do Claude"""
        result = {
            "success": False,
            "output": raw,
            "files": [],
            "errors": []
        }

        # Tenta extrair JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', raw, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                result["success"] = data.get("success", False)
                result["files"] = data.get("files_modified", [])
                result["output"] = data.get("summary", raw)
            except json.JSONDecodeError:
                pass

        # Detecta erros
        if "error" in raw.lower() or "falha" in raw.lower():
            result["errors"].append("Possivel erro detectado na saida")

        # Se nao encontrou JSON mas parece OK
        if not json_match and "concluido" in raw.lower():
            result["success"] = True

        return result

    def execute_with_tools(self,
                          task: str,
                          context: Dict,
                          allowed_tools: List[str] = None) -> ExecutionResult:
        """
        Executa com ferramentas especificas

        Args:
            task: Tarefa
            context: Contexto
            allowed_tools: Ferramentas permitidas

        Returns:
            ExecutionResult
        """
        tools_instruction = None
        if allowed_tools:
            tools_instruction = f"Use apenas as seguintes ferramentas: {', '.join(allowed_tools)}"

        return self.execute(task, context, tools_instruction)
