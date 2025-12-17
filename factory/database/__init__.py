"""
Factory Database Package v4.0
"""
from .connection import Base, SessionLocal, get_db, init_db, reset_db, engine
from .models import (
    Project,
    Job,
    Worker,
    FailureHistory,
    User,
    ActivityLog,
    Task,
    ProjectStatus,
    JobStatus,
    JobStep,
    WorkerStatus,
    TaskStatus,
    TaskPriority
)
from .repositories import TaskRepository

__all__ = [
    # Connection
    "Base",
    "SessionLocal",
    "get_db",
    "init_db",
    "reset_db",
    "engine",
    # Models
    "Project",
    "Job",
    "Worker",
    "FailureHistory",
    "User",
    "ActivityLog",
    "Task",
    # Enums
    "ProjectStatus",
    "JobStatus",
    "JobStep",
    "WorkerStatus",
    "TaskStatus",
    "TaskPriority",
    # Repositories
    "TaskRepository"
]
