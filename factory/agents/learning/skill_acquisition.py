"""
Sistema de Aquisicao de Skills para Agentes
===========================================

Permite que agentes:
- Desenvolvam novas habilidades
- Melhorem habilidades existentes
- Compartilhem skills entre si
- Avaliem competencia em areas especificas
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Skill:
    """Uma habilidade do agente"""
    id: str
    name: str
    description: str
    category: str                     # 'technical', 'domain', 'soft'
    proficiency: float = 0.0          # 0-1 (novato a expert)
    experience_points: int = 0
    usage_count: int = 0
    last_used: Optional[str] = None
    sub_skills: List[str] = field(default_factory=list)
    learned_from: Optional[str] = None  # agent_id que ensinou
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SkillAssessment:
    """Avaliacao de skill"""
    skill_id: str
    agent_id: str
    score: float
    feedback: str
    assessed_at: str


class SkillAcquisition:
    """
    Sistema de Aquisicao de Skills

    Gerencia desenvolvimento e compartilhamento de habilidades.
    """

    def __init__(self, agent_id: str, db_path: Optional[Path] = None):
        self.agent_id = agent_id
        self.db_path = db_path or Path("factory/database/skills.db")
        self._init_database()

    def _init_database(self):
        """Inicializa banco"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)

        # Tabela de skills
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_skills (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                proficiency REAL DEFAULT 0.0,
                experience_points INTEGER DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                last_used TEXT,
                sub_skills TEXT,
                learned_from TEXT,
                created_at TEXT,
                UNIQUE(agent_id, name)
            )
        """)

        # Tabela de avaliacoes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS skill_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                score REAL,
                feedback TEXT,
                assessed_at TEXT
            )
        """)

        # Tabela de progressao
        conn.execute("""
            CREATE TABLE IF NOT EXISTS skill_progression (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                skill_name TEXT NOT NULL,
                old_proficiency REAL,
                new_proficiency REAL,
                reason TEXT,
                timestamp TEXT
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_skills_agent ON agent_skills(agent_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_skills_category ON agent_skills(category)")

        conn.commit()
        conn.close()

    def _generate_id(self) -> str:
        import hashlib
        hash_input = f"{self.agent_id}_SKILL_{datetime.now().isoformat()}"
        return f"SK-{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def acquire_skill(self,
                     name: str,
                     description: str,
                     category: str = "technical",
                     initial_proficiency: float = 0.1,
                     learned_from: Optional[str] = None) -> Skill:
        """
        Adquire uma nova skill

        Args:
            name: Nome da skill
            description: Descricao
            category: Categoria (technical, domain, soft)
            initial_proficiency: Proficiencia inicial
            learned_from: Agente que ensinou (se aplicavel)

        Returns:
            Skill criada
        """
        skill = Skill(
            id=self._generate_id(),
            name=name,
            description=description,
            category=category,
            proficiency=initial_proficiency,
            learned_from=learned_from
        )

        conn = sqlite3.connect(self.db_path)

        try:
            conn.execute("""
                INSERT INTO agent_skills
                (id, agent_id, name, description, category, proficiency,
                 experience_points, usage_count, sub_skills, learned_from, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                skill.id,
                self.agent_id,
                skill.name,
                skill.description,
                skill.category,
                skill.proficiency,
                0, 0,
                json.dumps([]),
                skill.learned_from,
                skill.created_at
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            # Skill ja existe, atualiza
            conn.execute("""
                UPDATE agent_skills
                SET description = ?, category = ?
                WHERE agent_id = ? AND name = ?
            """, (description, category, self.agent_id, name))
            conn.commit()

        conn.close()
        return skill

    def practice_skill(self, skill_name: str, success: bool = True, xp_gain: int = 10):
        """
        Pratica uma skill (aumenta experiencia)

        Args:
            skill_name: Nome da skill
            success: Se a pratica foi bem-sucedida
            xp_gain: XP a ganhar (ajustado por sucesso)
        """
        conn = sqlite3.connect(self.db_path)

        # Busca skill atual
        cursor = conn.execute("""
            SELECT id, proficiency, experience_points, usage_count
            FROM agent_skills
            WHERE agent_id = ? AND name = ?
        """, (self.agent_id, skill_name))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        skill_id, current_prof, current_xp, usage = row

        # Calcula novo XP (menos se falhou)
        actual_xp = xp_gain if success else xp_gain // 4
        new_xp = current_xp + actual_xp

        # Calcula nova proficiencia baseada em XP
        # Formula: proficiency = 1 - e^(-xp/1000)
        import math
        new_prof = min(1.0, 1 - math.exp(-new_xp / 1000))

        # Atualiza
        conn.execute("""
            UPDATE agent_skills
            SET proficiency = ?,
                experience_points = ?,
                usage_count = usage_count + 1,
                last_used = ?
            WHERE id = ?
        """, (new_prof, new_xp, datetime.now().isoformat(), skill_id))

        # Registra progressao se houve mudanca significativa
        if new_prof - current_prof >= 0.01:
            conn.execute("""
                INSERT INTO skill_progression
                (agent_id, skill_name, old_proficiency, new_proficiency, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.agent_id,
                skill_name,
                current_prof,
                new_prof,
                "practice" if success else "practice_failure",
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Busca skill por nome"""
        conn = sqlite3.connect(self.db_path)

        cursor = conn.execute("""
            SELECT * FROM agent_skills
            WHERE agent_id = ? AND name = ?
        """, (self.agent_id, skill_name))

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_skill(row)
        return None

    def _row_to_skill(self, row) -> Skill:
        return Skill(
            id=row[0],
            name=row[2],
            description=row[3],
            category=row[4],
            proficiency=row[5],
            experience_points=row[6],
            usage_count=row[7],
            last_used=row[8],
            sub_skills=json.loads(row[9]) if row[9] else [],
            learned_from=row[10],
            created_at=row[11]
        )

    def get_all_skills(self, category: Optional[str] = None) -> List[Skill]:
        """Lista todas as skills do agente"""
        conn = sqlite3.connect(self.db_path)

        if category:
            cursor = conn.execute("""
                SELECT * FROM agent_skills
                WHERE agent_id = ? AND category = ?
                ORDER BY proficiency DESC
            """, (self.agent_id, category))
        else:
            cursor = conn.execute("""
                SELECT * FROM agent_skills
                WHERE agent_id = ?
                ORDER BY proficiency DESC
            """, (self.agent_id,))

        skills = [self._row_to_skill(row) for row in cursor.fetchall()]
        conn.close()

        return skills

    def get_proficiency_level(self, proficiency: float) -> str:
        """Converte proficiencia em nivel"""
        if proficiency >= 0.9:
            return "Expert"
        elif proficiency >= 0.7:
            return "Avancado"
        elif proficiency >= 0.5:
            return "Intermediario"
        elif proficiency >= 0.3:
            return "Basico"
        else:
            return "Novato"

    def can_teach(self, skill_name: str, min_proficiency: float = 0.7) -> bool:
        """Verifica se pode ensinar uma skill"""
        skill = self.get_skill(skill_name)
        return skill is not None and skill.proficiency >= min_proficiency

    def teach_skill(self, skill_name: str, student_agent_id: str) -> Optional[Skill]:
        """
        Ensina skill para outro agente

        Args:
            skill_name: Nome da skill
            student_agent_id: ID do agente aluno

        Returns:
            Skill ensinada ou None se nao pode ensinar
        """
        if not self.can_teach(skill_name):
            return None

        teacher_skill = self.get_skill(skill_name)

        # Cria instancia para o aluno
        student = SkillAcquisition(student_agent_id, self.db_path)

        # Aluno adquire skill com proficiencia inicial baseada no professor
        initial_prof = teacher_skill.proficiency * 0.3  # Comeca com 30% do nivel do professor

        return student.acquire_skill(
            name=skill_name,
            description=teacher_skill.description,
            category=teacher_skill.category,
            initial_proficiency=initial_prof,
            learned_from=self.agent_id
        )

    def assess_skill(self, skill_name: str, score: float, feedback: str):
        """
        Avalia uma skill

        Args:
            skill_name: Nome da skill
            score: Score da avaliacao (0-1)
            feedback: Feedback textual
        """
        skill = self.get_skill(skill_name)
        if not skill:
            return

        conn = sqlite3.connect(self.db_path)

        conn.execute("""
            INSERT INTO skill_assessments
            (skill_id, agent_id, score, feedback, assessed_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            skill.id,
            self.agent_id,
            score,
            feedback,
            datetime.now().isoformat()
        ))

        # Ajusta proficiencia baseada na avaliacao
        if score > skill.proficiency:
            adjustment = (score - skill.proficiency) * 0.2
        else:
            adjustment = (score - skill.proficiency) * 0.1

        new_prof = max(0.0, min(1.0, skill.proficiency + adjustment))

        conn.execute("""
            UPDATE agent_skills
            SET proficiency = ?
            WHERE id = ?
        """, (new_prof, skill.id))

        conn.commit()
        conn.close()

    def get_skill_gaps(self, required_skills: Dict[str, float]) -> Dict[str, float]:
        """
        Identifica gaps de skill

        Args:
            required_skills: Dict de {skill_name: required_proficiency}

        Returns:
            Dict de {skill_name: gap} (negativo se abaixo do requerido)
        """
        gaps = {}

        for skill_name, required in required_skills.items():
            current_skill = self.get_skill(skill_name)
            current_prof = current_skill.proficiency if current_skill else 0.0
            gap = current_prof - required
            if gap < 0:
                gaps[skill_name] = gap

        return gaps

    def get_strongest_skills(self, limit: int = 5) -> List[Skill]:
        """Retorna skills mais fortes"""
        skills = self.get_all_skills()
        return sorted(skills, key=lambda s: s.proficiency, reverse=True)[:limit]

    def get_skill_summary(self) -> Dict:
        """Retorna resumo das skills"""
        skills = self.get_all_skills()

        by_category = {}
        for skill in skills:
            if skill.category not in by_category:
                by_category[skill.category] = []
            by_category[skill.category].append({
                "name": skill.name,
                "proficiency": round(skill.proficiency, 2),
                "level": self.get_proficiency_level(skill.proficiency)
            })

        avg_proficiency = sum(s.proficiency for s in skills) / len(skills) if skills else 0

        return {
            "agent_id": self.agent_id,
            "total_skills": len(skills),
            "avg_proficiency": round(avg_proficiency, 2),
            "by_category": by_category,
            "strongest": [s.name for s in self.get_strongest_skills(3)],
            "recently_used": [s.name for s in sorted(skills, key=lambda x: x.last_used or "", reverse=True)[:3]]
        }
