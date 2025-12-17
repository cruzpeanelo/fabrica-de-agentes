"""
Memoria de Trabalho para Agentes
================================

Memoria de curto prazo para sessao atual:
- Contexto da tarefa em execucao
- Arquivos sendo modificados
- Decisoes pendentes
- Estado intermediario
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import deque


@dataclass
class WorkingContext:
    """Contexto de trabalho atual"""
    task_id: Optional[str] = None
    task_description: str = ""
    project_id: Optional[str] = None
    current_file: Optional[str] = None
    modified_files: List[str] = field(default_factory=list)
    pending_actions: List[str] = field(default_factory=list)
    recent_decisions: List[Dict] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())


class WorkingMemory:
    """
    Memoria de Trabalho

    Armazena informacoes temporarias da sessao atual.
    Limitada em tamanho para simular atencao focada.
    """

    def __init__(self, capacity: int = 50):
        """
        Args:
            capacity: Numero maximo de items na memoria de trabalho
        """
        self.capacity = capacity
        self.context = WorkingContext()
        self._attention_queue: deque = deque(maxlen=capacity)
        self._scratch_pad: Dict[str, Any] = {}

    def set_task(self, task_id: str, description: str, project_id: Optional[str] = None):
        """Define tarefa atual"""
        self.context = WorkingContext(
            task_id=task_id,
            task_description=description,
            project_id=project_id
        )
        self.focus(f"task_start: {description[:100]}")

    def focus(self, item: str):
        """
        Adiciona item ao foco de atencao

        Items mais antigos sao automaticamente removidos
        quando a capacidade eh atingida.
        """
        self._attention_queue.append({
            "item": item,
            "timestamp": datetime.now().isoformat()
        })

    def get_focus(self, limit: int = 10) -> List[str]:
        """Retorna items em foco recentes"""
        items = list(self._attention_queue)[-limit:]
        return [i["item"] for i in items]

    def note(self, content: str):
        """Adiciona nota ao contexto"""
        self.context.notes.append(content)
        self.focus(f"note: {content[:50]}")

    def record_file_change(self, file_path: str):
        """Registra arquivo modificado"""
        if file_path not in self.context.modified_files:
            self.context.modified_files.append(file_path)
        self.context.current_file = file_path
        self.focus(f"file: {file_path}")

    def record_error(self, error: str):
        """Registra erro encontrado"""
        self.context.errors_encountered.append(error)
        self.focus(f"error: {error[:50]}")

    def record_decision(self, context: str, decision: str, reasoning: str):
        """Registra decisao tomada"""
        self.context.recent_decisions.append({
            "context": context,
            "decision": decision,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        })
        self.focus(f"decision: {decision[:50]}")

    def add_pending_action(self, action: str):
        """Adiciona acao pendente"""
        self.context.pending_actions.append(action)
        self.focus(f"pending: {action[:50]}")

    def complete_action(self, action: str):
        """Marca acao como completa"""
        if action in self.context.pending_actions:
            self.context.pending_actions.remove(action)
        self.focus(f"completed: {action[:50]}")

    def scratch_write(self, key: str, value: Any):
        """Escreve no scratch pad (rascunho temporario)"""
        self._scratch_pad[key] = value

    def scratch_read(self, key: str) -> Optional[Any]:
        """Le do scratch pad"""
        return self._scratch_pad.get(key)

    def scratch_clear(self):
        """Limpa scratch pad"""
        self._scratch_pad.clear()

    def get_summary(self) -> str:
        """Gera resumo do contexto atual"""
        ctx = self.context
        parts = []

        if ctx.task_description:
            parts.append(f"Tarefa: {ctx.task_description}")

        if ctx.current_file:
            parts.append(f"Arquivo atual: {ctx.current_file}")

        if ctx.modified_files:
            parts.append(f"Arquivos modificados: {len(ctx.modified_files)}")

        if ctx.pending_actions:
            parts.append(f"Acoes pendentes: {', '.join(ctx.pending_actions[:3])}")

        if ctx.errors_encountered:
            parts.append(f"Erros: {len(ctx.errors_encountered)}")

        if ctx.notes:
            parts.append(f"Notas: {len(ctx.notes)}")

        return " | ".join(parts) if parts else "Contexto vazio"

    def clear(self):
        """Limpa memoria de trabalho"""
        self.context = WorkingContext()
        self._attention_queue.clear()
        self._scratch_pad.clear()

    def to_dict(self) -> Dict:
        """Exporta estado para dicionario"""
        return {
            "context": {
                "task_id": self.context.task_id,
                "task_description": self.context.task_description,
                "project_id": self.context.project_id,
                "current_file": self.context.current_file,
                "modified_files": self.context.modified_files,
                "pending_actions": self.context.pending_actions,
                "recent_decisions": self.context.recent_decisions,
                "errors_encountered": self.context.errors_encountered,
                "notes": self.context.notes,
                "started_at": self.context.started_at
            },
            "attention": self.get_focus(20),
            "scratch_pad": self._scratch_pad
        }
