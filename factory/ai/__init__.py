"""
Modulo de Inteligencia Artificial da Fabrica de Agentes
=======================================================

Este pacote fornece integracao com LLMs para dar inteligencia
real aos agentes da plataforma.
"""

from .claude_integration import (
    ClaudeClient,
    ClaudeMessage,
    ClaudeResponse,
    AgentBrain,
    get_claude_client,
    create_agent_brain
)

__all__ = [
    "ClaudeClient",
    "ClaudeMessage",
    "ClaudeResponse",
    "AgentBrain",
    "get_claude_client",
    "create_agent_brain"
]
