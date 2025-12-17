"""
Sistema de Perfil de Agentes - Experiências, Habilidades e Histórico
====================================================================

Gerencia o perfil completo de cada agente, incluindo:
- Habilidades técnicas e comportamentais
- Histórico de projetos e entregas
- Certificações e especializações
- Métricas de desempenho
- Evolução profissional (como um profissional real)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from pathlib import Path


class SkillLevel(Enum):
    """Níveis de proficiência em habilidades"""
    INICIANTE = (1, "Iniciante", "Conhecimento básico, precisa de supervisão")
    INTERMEDIARIO = (2, "Intermediário", "Executa tarefas com alguma autonomia")
    AVANCADO = (3, "Avançado", "Domínio técnico, resolve problemas complexos")
    ESPECIALISTA = (4, "Especialista", "Referência técnica, mentora outros")
    MASTER = (5, "Master", "Autoridade no assunto, define padrões")

    def __init__(self, level: int, display_name: str, description: str):
        self.level = level
        self.display_name = display_name
        self.description = description


class ExperienceType(Enum):
    """Tipos de experiência"""
    PROJETO = ("project", "Projeto")
    TAREFA = ("task", "Tarefa")
    CERTIFICACAO = ("certification", "Certificação")
    TREINAMENTO = ("training", "Treinamento")
    MENTORIA = ("mentorship", "Mentoria")
    DECISAO = ("decision", "Decisão Importante")
    INCIDENTE = ("incident", "Resolução de Incidente")
    INOVACAO = ("innovation", "Inovação/Melhoria")

    def __init__(self, type_id: str, display_name: str):
        self.type_id = type_id
        self.display_name = display_name


@dataclass
class AgentSkill:
    """Habilidade de um agente"""
    skill_id: str
    name: str
    category: str  # "technical", "behavioral", "domain"
    level: SkillLevel = SkillLevel.INICIANTE
    experience_points: int = 0
    times_used: int = 0
    last_used: Optional[datetime] = None
    certifications: List[str] = field(default_factory=list)

    def add_experience(self, points: int = 10):
        """Adiciona pontos de experiência (evolui automaticamente)"""
        self.experience_points += points
        self.times_used += 1
        self.last_used = datetime.now()

        # Evolução automática baseada em XP
        thresholds = {
            100: SkillLevel.INTERMEDIARIO,
            500: SkillLevel.AVANCADO,
            1500: SkillLevel.ESPECIALISTA,
            5000: SkillLevel.MASTER
        }

        for xp_threshold, new_level in thresholds.items():
            if self.experience_points >= xp_threshold and self.level.level < new_level.level:
                self.level = new_level

    def to_dict(self) -> Dict:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "category": self.category,
            "level": self.level.display_name,
            "level_num": self.level.level,
            "experience_points": self.experience_points,
            "times_used": self.times_used,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "certifications": self.certifications,
            "progress_to_next": self._calculate_progress()
        }

    def _calculate_progress(self) -> Dict:
        """Calcula progresso para próximo nível"""
        thresholds = [0, 100, 500, 1500, 5000]
        current_level = self.level.level

        if current_level >= 5:
            return {"current": self.experience_points, "next": None, "percent": 100}

        current_threshold = thresholds[current_level - 1]
        next_threshold = thresholds[current_level]

        progress = self.experience_points - current_threshold
        needed = next_threshold - current_threshold
        percent = min(100, int((progress / needed) * 100))

        return {
            "current": self.experience_points,
            "next": next_threshold,
            "percent": percent
        }


@dataclass
class Experience:
    """Registro de experiência do agente"""
    experience_id: str
    experience_type: ExperienceType
    title: str
    description: str
    date: datetime = field(default_factory=datetime.now)

    # Contexto
    project_name: Optional[str] = None
    story_id: Optional[str] = None
    task_id: Optional[str] = None

    # Resultados
    outcome: str = "success"  # success, partial, failed
    impact: str = "medium"  # low, medium, high, critical
    skills_used: List[str] = field(default_factory=list)
    skills_gained: List[str] = field(default_factory=list)

    # Métricas
    duration_hours: float = 0
    complexity: int = 5  # 1-10
    stakeholders_involved: List[str] = field(default_factory=list)

    # Reconhecimento
    feedback: Optional[str] = None
    rating: Optional[int] = None  # 1-5 estrelas

    def to_dict(self) -> Dict:
        return {
            "experience_id": self.experience_id,
            "type": self.experience_type.display_name,
            "type_id": self.experience_type.type_id,
            "title": self.title,
            "description": self.description,
            "date": self.date.isoformat(),
            "project_name": self.project_name,
            "outcome": self.outcome,
            "impact": self.impact,
            "skills_used": self.skills_used,
            "skills_gained": self.skills_gained,
            "duration_hours": self.duration_hours,
            "complexity": self.complexity,
            "rating": self.rating
        }


@dataclass
class AgentProfile:
    """Perfil completo de um agente"""
    agent_id: str

    # Informações básicas
    name: str
    title: str
    department: str
    area: str  # "business" ou "technology"
    level: int  # 1-10 na hierarquia

    # Bio e apresentação
    bio: str = ""
    specialization: str = ""
    avatar_url: str = ""

    # Habilidades
    skills: Dict[str, AgentSkill] = field(default_factory=dict)

    # Experiências
    experiences: List[Experience] = field(default_factory=list)

    # Métricas de carreira
    total_projects: int = 0
    total_tasks_completed: int = 0
    total_hours_worked: float = 0
    success_rate: float = 100.0

    # Decisões (para decisores)
    is_decision_maker: bool = False
    approval_timeout_hours: float = 1.0
    decisions_made: int = 0
    decisions_delegated: int = 0
    avg_decision_time_hours: float = 0

    # Conquistas
    achievements: List[Dict] = field(default_factory=list)

    # Relacionamentos
    mentees: List[str] = field(default_factory=list)  # IDs de agentes que mentoreou
    mentor: Optional[str] = None
    collaborators: Dict[str, int] = field(default_factory=dict)  # agent_id: times_worked_together

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None

    def add_skill(self, skill_id: str, name: str, category: str, initial_level: SkillLevel = SkillLevel.INICIANTE):
        """Adiciona uma nova habilidade"""
        if skill_id not in self.skills:
            self.skills[skill_id] = AgentSkill(
                skill_id=skill_id,
                name=name,
                category=category,
                level=initial_level
            )

    def use_skill(self, skill_id: str, xp_gained: int = 10):
        """Registra uso de habilidade e ganha XP"""
        if skill_id in self.skills:
            self.skills[skill_id].add_experience(xp_gained)
            self.last_activity = datetime.now()

    def add_experience(self, experience: Experience):
        """Adiciona uma experiência ao histórico"""
        self.experiences.append(experience)
        self.last_activity = datetime.now()

        # Atualiza métricas
        if experience.experience_type == ExperienceType.PROJETO:
            self.total_projects += 1
        elif experience.experience_type == ExperienceType.TAREFA:
            self.total_tasks_completed += 1

        self.total_hours_worked += experience.duration_hours

        # Ganha XP nas skills usadas
        for skill_id in experience.skills_used:
            self.use_skill(skill_id, xp_gained=experience.complexity * 5)

        # Adiciona novas skills
        for skill_id in experience.skills_gained:
            if skill_id not in self.skills:
                self.add_skill(skill_id, skill_id.replace("_", " ").title(), "domain")

    def get_top_skills(self, limit: int = 5) -> List[AgentSkill]:
        """Retorna as principais habilidades"""
        sorted_skills = sorted(
            self.skills.values(),
            key=lambda s: (s.level.level, s.experience_points),
            reverse=True
        )
        return sorted_skills[:limit]

    def get_recent_experiences(self, limit: int = 10) -> List[Experience]:
        """Retorna experiências mais recentes"""
        sorted_exp = sorted(self.experiences, key=lambda e: e.date, reverse=True)
        return sorted_exp[:limit]

    def get_experience_summary(self) -> Dict:
        """Resumo das experiências por tipo"""
        summary = {}
        for exp in self.experiences:
            type_name = exp.experience_type.display_name
            if type_name not in summary:
                summary[type_name] = {"count": 0, "success": 0, "high_impact": 0}

            summary[type_name]["count"] += 1
            if exp.outcome == "success":
                summary[type_name]["success"] += 1
            if exp.impact in ["high", "critical"]:
                summary[type_name]["high_impact"] += 1

        return summary

    def calculate_reliability_score(self) -> float:
        """Calcula score de confiabilidade (0-100)"""
        if not self.experiences:
            return 50.0  # Score neutro para novos

        success_count = sum(1 for e in self.experiences if e.outcome == "success")
        base_score = (success_count / len(self.experiences)) * 100

        # Bonus por experiência
        experience_bonus = min(10, self.total_projects * 0.5)

        # Bonus por skills avançadas
        advanced_skills = sum(1 for s in self.skills.values() if s.level.level >= 3)
        skill_bonus = min(10, advanced_skills * 2)

        return min(100, base_score + experience_bonus + skill_bonus)

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "title": self.title,
            "department": self.department,
            "area": self.area,
            "level": self.level,
            "bio": self.bio,
            "specialization": self.specialization,
            "avatar_url": self.avatar_url,

            # Skills
            "skills": [s.to_dict() for s in self.skills.values()],
            "top_skills": [s.to_dict() for s in self.get_top_skills()],
            "skills_count": len(self.skills),

            # Experiências
            "recent_experiences": [e.to_dict() for e in self.get_recent_experiences()],
            "experience_summary": self.get_experience_summary(),
            "total_experiences": len(self.experiences),

            # Métricas
            "metrics": {
                "total_projects": self.total_projects,
                "total_tasks_completed": self.total_tasks_completed,
                "total_hours_worked": round(self.total_hours_worked, 1),
                "success_rate": round(self.success_rate, 1),
                "reliability_score": round(self.calculate_reliability_score(), 1)
            },

            # Decisões
            "decision_maker": {
                "is_decision_maker": self.is_decision_maker,
                "approval_timeout_hours": self.approval_timeout_hours,
                "decisions_made": self.decisions_made,
                "decisions_delegated": self.decisions_delegated,
                "avg_decision_time_hours": round(self.avg_decision_time_hours, 2)
            },

            # Conquistas
            "achievements": self.achievements,
            "achievements_count": len(self.achievements),

            # Relacionamentos
            "mentees_count": len(self.mentees),
            "mentor": self.mentor,
            "top_collaborators": dict(sorted(
                self.collaborators.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),

            # Timestamps
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }


# =============================================================================
# GERADOR DE PERFIS PARA AGENTES EXISTENTES
# =============================================================================

def generate_profile_for_agent(
    agent_id: str,
    name: str,
    title: str,
    department: str,
    area: str,
    level: int,
    base_skills: List[str] = None,
    years_experience: int = 5
) -> AgentProfile:
    """Gera um perfil realista para um agente"""

    # Criar perfil base
    profile = AgentProfile(
        agent_id=agent_id,
        name=name,
        title=title,
        department=department,
        area=area,
        level=level,
        bio=f"Profissional com {years_experience} anos de experiência em {department}",
        specialization=department
    )

    # Determina se é decisor (níveis 1-7 são decisores)
    profile.is_decision_maker = level <= 7

    # Timeout baseado no nível (mais alto = mais autonomia)
    if level <= 2:
        profile.approval_timeout_hours = 4.0  # C-Level tem mais tempo
    elif level <= 4:
        profile.approval_timeout_hours = 2.0  # VPs/Diretores
    elif level <= 6:
        profile.approval_timeout_hours = 1.0  # Gerentes
    else:
        profile.approval_timeout_hours = 0.5  # Coordenadores

    # Adiciona skills base
    if base_skills:
        for i, skill_name in enumerate(base_skills):
            skill_id = skill_name.lower().replace(" ", "_")

            # Define nível baseado na experiência
            if years_experience >= 10:
                initial_level = SkillLevel.ESPECIALISTA
                initial_xp = 2000
            elif years_experience >= 5:
                initial_level = SkillLevel.AVANCADO
                initial_xp = 800
            elif years_experience >= 2:
                initial_level = SkillLevel.INTERMEDIARIO
                initial_xp = 200
            else:
                initial_level = SkillLevel.INICIANTE
                initial_xp = 50

            profile.add_skill(skill_id, skill_name, "technical" if i < len(base_skills)//2 else "domain", initial_level)
            profile.skills[skill_id].experience_points = initial_xp

    # Adiciona skills comportamentais universais
    behavioral_skills = ["Comunicação", "Trabalho em Equipe", "Resolução de Problemas", "Adaptabilidade"]
    for skill_name in behavioral_skills:
        skill_id = skill_name.lower().replace(" ", "_")
        profile.add_skill(skill_id, skill_name, "behavioral", SkillLevel.INTERMEDIARIO)
        profile.skills[skill_id].experience_points = 200 + (years_experience * 20)

    # Métricas iniciais baseadas na experiência
    profile.total_projects = years_experience * 3
    profile.total_tasks_completed = years_experience * 50
    profile.total_hours_worked = years_experience * 2000
    profile.success_rate = 85 + (level * 1.5)  # Níveis mais altos têm maior success rate

    return profile


# =============================================================================
# SKILLS PREDEFINIDAS POR ÁREA
# =============================================================================

SKILLS_BY_AREA = {
    "technology": {
        "development": ["Python", "JavaScript", "React", "FastAPI", "SQL", "Git", "Docker", "API Design"],
        "data": ["Python", "SQL", "Power BI", "Pandas", "Data Modeling", "ETL", "Statistics"],
        "infrastructure": ["Linux", "AWS", "Azure", "Docker", "Kubernetes", "Networking", "Security"],
        "security": ["Cybersecurity", "Penetration Testing", "SIEM", "Compliance", "Risk Assessment"],
        "devops": ["CI/CD", "Jenkins", "Docker", "Kubernetes", "Terraform", "Monitoring", "Automation"],
        "qa": ["Test Automation", "Selenium", "API Testing", "Performance Testing", "Test Planning"],
        "architecture": ["System Design", "Microservices", "Cloud Architecture", "Integration Patterns"],
        "it_management": ["IT Strategy", "Budget Management", "Vendor Management", "Team Leadership"]
    },
    "business": {
        "executive": ["Strategic Planning", "Executive Leadership", "Stakeholder Management", "P&L Management"],
        "finance": ["Financial Analysis", "Budgeting", "Forecasting", "Accounting", "Risk Management"],
        "sales": ["Negotiation", "Sales Strategy", "CRM", "Pipeline Management", "Account Management"],
        "marketing": ["Digital Marketing", "Brand Management", "Content Strategy", "Analytics", "SEO/SEM"],
        "hr": ["Recruitment", "Training & Development", "Performance Management", "Labor Law"],
        "operations": ["Process Optimization", "Supply Chain", "Quality Management", "Lean Six Sigma"],
        "legal": ["Contract Law", "Compliance", "Corporate Law", "Risk Management", "Negotiation"]
    }
}


def get_skills_for_department(department: str, area: str) -> List[str]:
    """Retorna skills sugeridas para um departamento"""
    area_skills = SKILLS_BY_AREA.get(area, {})
    dept_key = department.lower().replace(" ", "_")

    # Tenta match direto
    if dept_key in area_skills:
        return area_skills[dept_key]

    # Tenta match parcial
    for key, skills in area_skills.items():
        if key in dept_key or dept_key in key:
            return skills

    # Retorna skills genéricas
    return ["Problem Solving", "Communication", "Project Management", "Analysis"]


# =============================================================================
# CONQUISTAS POSSÍVEIS
# =============================================================================

ACHIEVEMENTS = [
    {"id": "first_project", "name": "Primeiro Projeto", "description": "Completou seu primeiro projeto", "icon": "🎯"},
    {"id": "team_player", "name": "Team Player", "description": "Colaborou com 10+ agentes diferentes", "icon": "🤝"},
    {"id": "fast_learner", "name": "Aprendizado Rápido", "description": "Dominou 5 novas habilidades", "icon": "📚"},
    {"id": "reliable", "name": "Confiável", "description": "Manteve 95%+ de taxa de sucesso", "icon": "⭐"},
    {"id": "mentor", "name": "Mentor", "description": "Mentoreou 3+ agentes", "icon": "🎓"},
    {"id": "decision_maker", "name": "Decisor", "description": "Tomou 50+ decisões importantes", "icon": "⚖️"},
    {"id": "innovator", "name": "Inovador", "description": "Propôs 5+ melhorias implementadas", "icon": "💡"},
    {"id": "specialist", "name": "Especialista", "description": "Atingiu nível Master em uma skill", "icon": "🏆"},
    {"id": "marathon", "name": "Maratonista", "description": "1000+ horas trabalhadas", "icon": "🏃"},
    {"id": "perfectionist", "name": "Perfeccionista", "description": "100 tarefas sem falhas", "icon": "✨"}
]


__all__ = [
    'SkillLevel', 'ExperienceType', 'AgentSkill', 'Experience', 'AgentProfile',
    'generate_profile_for_agent', 'get_skills_for_department', 'SKILLS_BY_AREA', 'ACHIEVEMENTS'
]
