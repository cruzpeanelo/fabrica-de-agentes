"""Core do Sistema de Agentes Autonomos"""
from .autonomous_agent import AutonomousAgent, AgentState, AgentCapability, TaskContext, TaskResult
from .agent_runtime import AgentRuntime
from .task_executor import TaskExecutor
from .hierarchy_integration import (
    HierarchyIntegration, HierarchyConfig, HierarchicalDecision,
    ApprovalRequirement, WorkHoursConfig, integrate_hierarchy, with_hierarchy
)

__all__ = [
    'AutonomousAgent', 'AgentState', 'AgentCapability', 'TaskContext', 'TaskResult',
    'AgentRuntime', 'TaskExecutor',
    'HierarchyIntegration', 'HierarchyConfig', 'HierarchicalDecision',
    'ApprovalRequirement', 'WorkHoursConfig', 'integrate_hierarchy', 'with_hierarchy'
]
