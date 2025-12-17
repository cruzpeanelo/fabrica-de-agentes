"""
Serviço de Gerenciamento de Perfis de Agentes
==============================================

Gerencia perfis de agentes, sincroniza com hierarquia corporativa,
e provê APIs para consulta e atualização de perfis.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import random

from factory.agents.agent_profile import (
    AgentProfile, AgentSkill, Experience, SkillLevel, ExperienceType,
    generate_profile_for_agent, get_skills_for_department, ACHIEVEMENTS
)

try:
    from factory.agents.corporate_hierarchy import (
        ALL_CORPORATE_AGENTS, get_agents_by_area, get_agent
    )
    HAS_HIERARCHY = True
except ImportError:
    HAS_HIERARCHY = False
    ALL_CORPORATE_AGENTS = {}


class ProfileService:
    """Serviço de gerenciamento de perfis de agentes"""

    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else Path(__file__).parent / "profiles_data"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, AgentProfile] = {}
        self._load_profiles()

    def _load_profiles(self):
        """Carrega perfis salvos ou gera novos"""
        profiles_file = self.storage_path / "profiles.json"

        if profiles_file.exists():
            try:
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # TODO: Deserializar perfis
            except Exception as e:
                print(f"Erro ao carregar perfis: {e}")

        # Gera perfis para agentes corporativos se não existirem
        if HAS_HIERARCHY:
            self._sync_with_hierarchy()

    def _sync_with_hierarchy(self):
        """Sincroniza perfis com hierarquia corporativa"""
        for agent_id, agent in ALL_CORPORATE_AGENTS.items():
            if agent_id not in self.profiles:
                # Gera perfil para o agente
                skills = get_skills_for_department(
                    agent.department.display_name,
                    agent.department.area
                )

                # Anos de experiência baseado no nível
                years_exp = max(1, 15 - agent.level.level_num)

                profile = generate_profile_for_agent(
                    agent_id=agent_id,
                    name=agent.name,
                    title=agent.title,
                    department=agent.department.display_name,
                    area=agent.department.area,
                    level=agent.level.level_num,
                    base_skills=skills,
                    years_experience=years_exp
                )

                # Adiciona bio personalizada
                profile.bio = self._generate_bio(agent, years_exp)
                profile.specialization = self._get_specialization(agent)

                # Adiciona experiências iniciais
                self._add_initial_experiences(profile, years_exp)

                # Adiciona conquistas baseadas em métricas
                self._award_achievements(profile)

                self.profiles[agent_id] = profile

    def _generate_bio(self, agent, years_exp: int) -> str:
        """Gera bio personalizada para o agente"""
        bios = {
            1: f"Líder executivo com {years_exp} anos de experiência em gestão estratégica e transformação organizacional.",
            2: f"Executivo C-Level com {years_exp} anos liderando iniciativas de alto impacto em {agent.department.display_name}.",
            3: f"Vice-Presidente com vasta experiência em {agent.department.display_name}, focado em resultados e inovação.",
            4: f"Diretor com {years_exp} anos de experiência em {agent.department.display_name}, especializado em liderar equipes de alta performance.",
            5: f"Gerente Sênior com {years_exp} anos de experiência, responsável por projetos estratégicos em {agent.department.display_name}.",
            6: f"Gerente com {years_exp} anos de experiência em {agent.department.display_name}, focado em entrega de resultados e desenvolvimento de equipes.",
            7: f"Coordenador experiente em {agent.department.display_name}, com forte habilidade em gestão de processos e pessoas.",
            8: f"Especialista técnico com {years_exp} anos de experiência profunda em {agent.department.display_name}.",
            9: f"Profissional com {years_exp} anos de experiência em {agent.department.display_name}, com foco em execução e qualidade.",
            10: f"Profissional em início de carreira em {agent.department.display_name}, com grande potencial de crescimento."
        }
        return bios.get(agent.level.level_num, f"Profissional de {agent.department.display_name}")

    def _get_specialization(self, agent) -> str:
        """Retorna especialização baseada no departamento"""
        specializations = {
            "Desenvolvimento": "Full-stack Development & System Architecture",
            "Dados e Analytics": "Data Engineering & Business Intelligence",
            "Infraestrutura": "Cloud Infrastructure & DevOps",
            "Seguranca da Informacao": "Cybersecurity & Risk Management",
            "Quality Assurance": "Test Automation & Quality Engineering",
            "DevOps/SRE": "Platform Engineering & Site Reliability",
            "Arquitetura": "Enterprise Architecture & Solutions Design",
            "Financeiro": "Financial Planning & Analysis",
            "Comercial/Vendas": "Sales Strategy & Client Relations",
            "Marketing": "Digital Marketing & Brand Strategy",
            "Recursos Humanos": "Talent Management & Organizational Development",
            "Operacoes": "Operations Excellence & Process Optimization",
            "Juridico": "Corporate Law & Compliance"
        }
        return specializations.get(agent.department.display_name, agent.department.display_name)

    def _add_initial_experiences(self, profile: AgentProfile, years_exp: int):
        """Adiciona experiências iniciais baseadas nos anos de experiência"""
        num_experiences = min(years_exp * 2, 20)

        experience_templates = [
            ("Implementação de {system}", ExperienceType.PROJETO, "high"),
            ("Melhoria de processo de {process}", ExperienceType.INOVACAO, "medium"),
            ("Resolução de incidente crítico", ExperienceType.INCIDENTE, "critical"),
            ("Treinamento em {skill}", ExperienceType.TREINAMENTO, "medium"),
            ("Mentoria de novo colaborador", ExperienceType.MENTORIA, "medium"),
            ("Entrega de sprint", ExperienceType.TAREFA, "medium"),
            ("Decisão técnica importante", ExperienceType.DECISAO, "high"),
        ]

        systems = ["ERP", "CRM", "Analytics", "API Gateway", "Data Pipeline", "Dashboard", "Microservices"]
        processes = ["deployment", "testes", "documentação", "code review", "monitoramento"]
        skills_list = list(profile.skills.keys())[:5] if profile.skills else ["general"]

        for i in range(num_experiences):
            template = random.choice(experience_templates)
            title = template[0].format(
                system=random.choice(systems),
                process=random.choice(processes),
                skill=random.choice(skills_list) if skills_list else "general"
            )

            exp = Experience(
                experience_id=f"EXP-{profile.agent_id}-{i+1:04d}",
                experience_type=template[1],
                title=title,
                description=f"Experiência em {profile.department}",
                date=datetime.now().replace(year=datetime.now().year - random.randint(0, years_exp)),
                project_name=f"Projeto {random.randint(1, 50)}",
                outcome="success" if random.random() > 0.1 else "partial",
                impact=template[2],
                skills_used=random.sample(skills_list, min(3, len(skills_list))) if skills_list else [],
                duration_hours=random.randint(4, 200),
                complexity=random.randint(3, 9),
                rating=random.choice([4, 4, 4, 5, 5, None])
            )

            profile.experiences.append(exp)

    def _award_achievements(self, profile: AgentProfile):
        """Atribui conquistas baseadas nas métricas do perfil"""
        if profile.total_projects >= 1:
            profile.achievements.append(ACHIEVEMENTS[0])  # first_project

        if len(profile.collaborators) >= 10:
            profile.achievements.append(ACHIEVEMENTS[1])  # team_player

        if len(profile.skills) >= 5:
            profile.achievements.append(ACHIEVEMENTS[2])  # fast_learner

        if profile.success_rate >= 95:
            profile.achievements.append(ACHIEVEMENTS[3])  # reliable

        if profile.is_decision_maker and profile.decisions_made >= 50:
            profile.achievements.append(ACHIEVEMENTS[5])  # decision_maker

        master_skills = [s for s in profile.skills.values() if s.level == SkillLevel.MASTER]
        if master_skills:
            profile.achievements.append(ACHIEVEMENTS[7])  # specialist

        if profile.total_hours_worked >= 1000:
            profile.achievements.append(ACHIEVEMENTS[8])  # marathon

    def get_profile(self, agent_id: str) -> Optional[AgentProfile]:
        """Busca perfil de um agente"""
        return self.profiles.get(agent_id)

    def get_all_profiles(self) -> List[AgentProfile]:
        """Retorna todos os perfis"""
        return list(self.profiles.values())

    def get_profiles_by_area(self, area: str) -> List[AgentProfile]:
        """Retorna perfis de uma área (business/technology)"""
        return [p for p in self.profiles.values() if p.area == area]

    def get_profiles_by_department(self, department: str) -> List[AgentProfile]:
        """Retorna perfis de um departamento"""
        return [p for p in self.profiles.values() if department.lower() in p.department.lower()]

    def get_decision_makers(self) -> List[AgentProfile]:
        """Retorna perfis de agentes decisores"""
        return [p for p in self.profiles.values() if p.is_decision_maker]

    def update_timeout(self, agent_id: str, timeout_hours: float) -> bool:
        """Atualiza timeout de aprovação de um agente decisor"""
        profile = self.profiles.get(agent_id)
        if profile and profile.is_decision_maker:
            profile.approval_timeout_hours = timeout_hours
            return True
        return False

    def record_activity(self, agent_id: str, activity_type: str, details: Dict):
        """Registra uma atividade do agente"""
        profile = self.profiles.get(agent_id)
        if not profile:
            return

        profile.last_activity = datetime.now()

        # Cria experiência baseada na atividade
        exp_type_map = {
            "task_complete": ExperienceType.TAREFA,
            "project_complete": ExperienceType.PROJETO,
            "decision_made": ExperienceType.DECISAO,
            "training": ExperienceType.TREINAMENTO,
            "incident": ExperienceType.INCIDENTE
        }

        if activity_type in exp_type_map:
            exp = Experience(
                experience_id=f"EXP-{agent_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                experience_type=exp_type_map[activity_type],
                title=details.get("title", "Atividade"),
                description=details.get("description", ""),
                project_name=details.get("project_name"),
                outcome=details.get("outcome", "success"),
                impact=details.get("impact", "medium"),
                skills_used=details.get("skills_used", []),
                duration_hours=details.get("duration_hours", 1),
                complexity=details.get("complexity", 5)
            )
            profile.add_experience(exp)

    def get_org_chart_data(self) -> Dict:
        """Retorna dados formatados para o organograma hierárquico"""
        if not HAS_HIERARCHY:
            return {"business": {}, "technology": {}, "hierarchy_tree": {}}

        # Constrói árvore hierárquica completa
        hierarchy_tree = self._build_hierarchy_tree()

        # Separa por área
        business_tree = {}
        tech_tree = {}

        for agent_id, node in hierarchy_tree.items():
            if node["area"] == "business":
                business_tree[agent_id] = node
            else:
                tech_tree[agent_id] = node

        return {
            "business": business_tree,
            "technology": tech_tree,
            "hierarchy_tree": hierarchy_tree,
            "total_agents": len(self.profiles),
            "total_business": len([p for p in self.profiles.values() if p.area == "business"]),
            "total_technology": len([p for p in self.profiles.values() if p.area == "technology"])
        }

    def _build_hierarchy_tree(self) -> Dict:
        """Constrói árvore hierárquica com relacionamentos"""
        tree = {}

        for agent_id, agent in ALL_CORPORATE_AGENTS.items():
            profile = self.profiles.get(agent_id)

            tree[agent_id] = {
                "agent_id": agent_id,
                "name": agent.name,
                "title": agent.title,
                "level": agent.level.level_num,
                "level_name": agent.level.title,
                "department": agent.department.display_name,
                "area": agent.department.area,
                "reports_to": agent.reports_to,
                "direct_reports": agent.direct_reports,
                "direct_reports_count": len(agent.direct_reports),
                "is_decision_maker": profile.is_decision_maker if profile else False,
                "reliability_score": profile.calculate_reliability_score() if profile else 0,
                "timeout_hours": profile.approval_timeout_hours if profile else 1.0,
                "budget_authority": agent.budget_authority
            }

        return tree

    def get_hierarchy_by_area(self, area: str) -> Dict:
        """Retorna hierarquia de uma área específica com estrutura em árvore"""
        if not HAS_HIERARCHY:
            return {"roots": [], "nodes": {}}

        # Encontra os nós raiz (quem não reporta a ninguém ou reporta a alguém de outra área)
        roots = []
        nodes = {}

        for agent_id, agent in ALL_CORPORATE_AGENTS.items():
            if agent.department.area != area:
                continue

            profile = self.profiles.get(agent_id)
            node = {
                "agent_id": agent_id,
                "name": agent.name,
                "title": agent.title,
                "level": agent.level.level_num,
                "level_name": agent.level.title,
                "department": agent.department.display_name,
                "reports_to": agent.reports_to,
                "direct_reports": [dr for dr in agent.direct_reports
                                   if dr in ALL_CORPORATE_AGENTS and
                                   ALL_CORPORATE_AGENTS[dr].department.area == area],
                "is_decision_maker": profile.is_decision_maker if profile else False,
                "reliability_score": profile.calculate_reliability_score() if profile else 0,
                "timeout_hours": profile.approval_timeout_hours if profile else 1.0,
                "budget_authority": agent.budget_authority,
                "skills_count": len(profile.skills) if profile else 0,
                "projects_count": profile.total_projects if profile else 0
            }
            nodes[agent_id] = node

            # É raiz se não reporta a ninguém ou reporta a alguém de outra área
            if not agent.reports_to or agent.reports_to not in ALL_CORPORATE_AGENTS:
                roots.append(agent_id)
            elif ALL_CORPORATE_AGENTS[agent.reports_to].department.area != area:
                roots.append(agent_id)

        # Ordena raízes por nível
        roots.sort(key=lambda x: nodes[x]["level"])

        return {"roots": roots, "nodes": nodes}

    def get_top_performers(self, limit: int = 10) -> List[Dict]:
        """Retorna os agentes com melhor desempenho"""
        sorted_profiles = sorted(
            self.profiles.values(),
            key=lambda p: (p.calculate_reliability_score(), p.total_projects),
            reverse=True
        )

        return [
            {
                "agent_id": p.agent_id,
                "name": p.name,
                "title": p.title,
                "department": p.department,
                "reliability_score": p.calculate_reliability_score(),
                "projects": p.total_projects,
                "tasks": p.total_tasks_completed
            }
            for p in sorted_profiles[:limit]
        ]


# Singleton instance
_profile_service: Optional[ProfileService] = None


def get_profile_service() -> ProfileService:
    """Retorna instância singleton do serviço de perfis"""
    global _profile_service
    if _profile_service is None:
        _profile_service = ProfileService()
    return _profile_service


__all__ = ['ProfileService', 'get_profile_service']
