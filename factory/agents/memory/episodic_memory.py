"""
Memoria Episodica para Agentes
==============================

Armazena eventos e experiencias como episodios narrativos:
- O que aconteceu
- Quando aconteceu
- Qual foi o contexto
- Qual foi o resultado
- O que aprendeu
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class Episode:
    """Um episodio de experiencia"""
    id: str
    agent_id: str
    title: str
    narrative: str                    # Descricao do que aconteceu
    context: Dict[str, Any]           # Contexto (task, project, etc)
    actions_taken: List[str]          # Acoes realizadas
    outcome: str                      # Resultado
    emotional_impact: float           # -1 a 1 (negativo a positivo)
    lessons: List[str]                # Licoes aprendidas
    tags: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    importance: float = 0.5


class EpisodicMemory:
    """
    Sistema de Memoria Episodica

    Armazena experiencias como narrativas que podem
    ser recordadas e usadas para aprendizado.
    """

    def __init__(self, agent_id: str, db_path: Optional[Path] = None):
        self.agent_id = agent_id
        self.db_path = db_path or Path(f"factory/database/episodes_{agent_id}.db")
        self._init_database()

    def _init_database(self):
        """Inicializa banco"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                title TEXT,
                narrative TEXT,
                context TEXT,
                actions_taken TEXT,
                outcome TEXT,
                emotional_impact REAL,
                lessons TEXT,
                tags TEXT,
                timestamp TEXT,
                importance REAL DEFAULT 0.5
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ep_timestamp ON episodes(timestamp DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ep_importance ON episodes(importance DESC)")
        conn.commit()
        conn.close()

    def _generate_id(self) -> str:
        import hashlib
        hash_input = f"{self.agent_id}_EP_{datetime.now().isoformat()}"
        return f"EP-{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def record(self,
              title: str,
              narrative: str,
              context: Dict,
              actions: List[str],
              outcome: str,
              emotional_impact: float = 0.0,
              lessons: Optional[List[str]] = None,
              tags: Optional[List[str]] = None,
              importance: float = 0.5) -> Episode:
        """
        Registra um novo episodio

        Args:
            title: Titulo curto do episodio
            narrative: Descricao narrativa do que aconteceu
            context: Contexto (task_id, project_id, etc)
            actions: Lista de acoes realizadas
            outcome: Resultado final
            emotional_impact: Impacto emocional (-1 a 1)
            lessons: Licoes aprendidas
            tags: Tags para categorizacao
            importance: Importancia do episodio

        Returns:
            Episode criado
        """
        episode = Episode(
            id=self._generate_id(),
            agent_id=self.agent_id,
            title=title,
            narrative=narrative,
            context=context,
            actions_taken=actions,
            outcome=outcome,
            emotional_impact=emotional_impact,
            lessons=lessons or [],
            tags=tags or [],
            importance=importance
        )

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO episodes
            (id, agent_id, title, narrative, context, actions_taken,
             outcome, emotional_impact, lessons, tags, timestamp, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            episode.id,
            episode.agent_id,
            episode.title,
            episode.narrative,
            json.dumps(episode.context),
            json.dumps(episode.actions_taken),
            episode.outcome,
            episode.emotional_impact,
            json.dumps(episode.lessons),
            json.dumps(episode.tags),
            episode.timestamp,
            episode.importance
        ))
        conn.commit()
        conn.close()

        return episode

    def recall_similar(self, situation: str, limit: int = 5) -> List[Episode]:
        """
        Busca episodios similares a uma situacao

        Args:
            situation: Descricao da situacao atual
            limit: Maximo de episodios

        Returns:
            Lista de episodios similares
        """
        conn = sqlite3.connect(self.db_path)

        # Busca por keywords na narrativa
        keywords = situation.lower().split()[:5]
        like_clauses = " OR ".join(["narrative LIKE ?" for _ in keywords])

        cursor = conn.execute(f"""
            SELECT * FROM episodes
            WHERE agent_id = ?
            AND ({like_clauses})
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        """, [self.agent_id] + [f"%{kw}%" for kw in keywords] + [limit])

        episodes = [self._row_to_episode(row) for row in cursor.fetchall()]
        conn.close()

        return episodes

    def recall_by_outcome(self, positive: bool = True, limit: int = 10) -> List[Episode]:
        """
        Busca episodios por tipo de resultado

        Args:
            positive: True para resultados positivos, False para negativos
            limit: Maximo de episodios
        """
        conn = sqlite3.connect(self.db_path)

        if positive:
            cursor = conn.execute("""
                SELECT * FROM episodes
                WHERE agent_id = ? AND emotional_impact > 0
                ORDER BY emotional_impact DESC, importance DESC
                LIMIT ?
            """, (self.agent_id, limit))
        else:
            cursor = conn.execute("""
                SELECT * FROM episodes
                WHERE agent_id = ? AND emotional_impact < 0
                ORDER BY emotional_impact ASC, importance DESC
                LIMIT ?
            """, (self.agent_id, limit))

        episodes = [self._row_to_episode(row) for row in cursor.fetchall()]
        conn.close()

        return episodes

    def recall_lessons(self, tags: Optional[List[str]] = None, limit: int = 20) -> List[str]:
        """
        Recupera licoes aprendidas

        Args:
            tags: Filtrar por tags
            limit: Maximo de episodios a considerar

        Returns:
            Lista de licoes
        """
        conn = sqlite3.connect(self.db_path)

        cursor = conn.execute("""
            SELECT lessons FROM episodes
            WHERE agent_id = ?
            ORDER BY importance DESC
            LIMIT ?
        """, (self.agent_id, limit))

        all_lessons = []
        for row in cursor.fetchall():
            lessons = json.loads(row[0]) if row[0] else []
            all_lessons.extend(lessons)

        conn.close()

        # Remove duplicatas mantendo ordem
        seen = set()
        unique_lessons = []
        for lesson in all_lessons:
            if lesson not in seen:
                seen.add(lesson)
                unique_lessons.append(lesson)

        return unique_lessons

    def get_recent(self, limit: int = 10) -> List[Episode]:
        """Retorna episodios recentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT * FROM episodes
            WHERE agent_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (self.agent_id, limit))

        episodes = [self._row_to_episode(row) for row in cursor.fetchall()]
        conn.close()

        return episodes

    def _row_to_episode(self, row) -> Episode:
        """Converte row para Episode"""
        return Episode(
            id=row[0],
            agent_id=row[1],
            title=row[2],
            narrative=row[3],
            context=json.loads(row[4]) if row[4] else {},
            actions_taken=json.loads(row[5]) if row[5] else [],
            outcome=row[6],
            emotional_impact=row[7],
            lessons=json.loads(row[8]) if row[8] else [],
            tags=json.loads(row[9]) if row[9] else [],
            timestamp=row[10],
            importance=row[11]
        )

    def generate_wisdom(self) -> Dict[str, List[str]]:
        """
        Gera sabedoria acumulada dos episodios

        Analisa padroes nos episodios para extrair
        insights de alto nivel.
        """
        positive_eps = self.recall_by_outcome(positive=True, limit=20)
        negative_eps = self.recall_by_outcome(positive=False, limit=20)

        wisdom = {
            "o_que_funciona": [],
            "o_que_evitar": [],
            "licoes_importantes": self.recall_lessons(limit=30)
        }

        # Extrai padroes de sucesso
        for ep in positive_eps:
            for action in ep.actions_taken:
                if len(action) > 10:
                    wisdom["o_que_funciona"].append(action)

        # Extrai padroes de falha
        for ep in negative_eps:
            for action in ep.actions_taken:
                if len(action) > 10:
                    wisdom["o_que_evitar"].append(action)

        # Remove duplicatas
        wisdom["o_que_funciona"] = list(set(wisdom["o_que_funciona"]))[:15]
        wisdom["o_que_evitar"] = list(set(wisdom["o_que_evitar"]))[:15]

        return wisdom
