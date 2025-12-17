"""
Motor de Aprendizado para Agentes
=================================

Processa feedback e experiencias para:
- Extrair padroes de sucesso/falha
- Ajustar comportamento
- Melhorar decisoes futuras
- Compartilhar aprendizado entre agentes
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..memory.agent_memory import AgentMemory, MemoryType
from ..memory.episodic_memory import EpisodicMemory
from .feedback_system import FeedbackSystem, FeedbackResult


@dataclass
class LearningInsight:
    """Insight aprendido"""
    id: str
    insight_type: str           # 'pattern', 'rule', 'heuristic'
    condition: str              # Quando se aplica
    action: str                 # O que fazer
    confidence: float           # 0-1
    source_count: int           # Quantas experiencias geraram isso
    last_validated: str


class LearningEngine:
    """
    Motor de Aprendizado

    Analisa experiencias e feedback para extrair
    conhecimento acionavel que melhora performance.
    """

    def __init__(self,
                 agent_id: str,
                 memory: Optional[AgentMemory] = None,
                 episodes: Optional[EpisodicMemory] = None,
                 feedback: Optional[FeedbackSystem] = None,
                 db_path: Optional[Path] = None):
        """
        Args:
            agent_id: ID do agente
            memory: Sistema de memoria
            episodes: Memoria episodica
            feedback: Sistema de feedback
            db_path: Caminho do banco
        """
        self.agent_id = agent_id
        self.memory = memory or AgentMemory(agent_id)
        self.episodes = episodes or EpisodicMemory(agent_id)
        self.feedback = feedback or FeedbackSystem()
        self.db_path = db_path or Path(f"factory/database/learning_{agent_id}.db")

        self._init_database()

    def _init_database(self):
        """Inicializa banco"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)

        # Tabela de insights
        conn.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id TEXT PRIMARY KEY,
                insight_type TEXT,
                condition TEXT,
                action TEXT,
                confidence REAL,
                source_count INTEGER,
                last_validated TEXT,
                created_at TEXT
            )
        """)

        # Tabela de regras aprendidas
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learned_rules (
                id TEXT PRIMARY KEY,
                rule_type TEXT,
                trigger TEXT,
                response TEXT,
                success_rate REAL,
                usage_count INTEGER,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Tabela de associacoes (conexoes entre conceitos)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_a TEXT,
                concept_b TEXT,
                strength REAL,
                context TEXT,
                created_at TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _generate_id(self, prefix: str) -> str:
        import hashlib
        hash_input = f"{self.agent_id}_{prefix}_{datetime.now().isoformat()}"
        return f"{prefix}-{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def learn_from_task(self,
                       task_id: str,
                       task_description: str,
                       actions_taken: List[str],
                       result: Dict,
                       success: bool) -> List[LearningInsight]:
        """
        Aprende com resultado de uma tarefa

        Args:
            task_id: ID da tarefa
            task_description: Descricao da tarefa
            actions_taken: Acoes realizadas
            result: Resultado da tarefa
            success: Se foi sucesso

        Returns:
            Lista de insights aprendidos
        """
        insights = []

        # Cria episodio
        self.episodes.record(
            title=f"Task: {task_description[:50]}",
            narrative=f"Executei tarefa '{task_description}' com {len(actions_taken)} acoes. Resultado: {'sucesso' if success else 'falha'}.",
            context={"task_id": task_id},
            actions=actions_taken,
            outcome="success" if success else "failure",
            emotional_impact=0.5 if success else -0.3,
            lessons=self._extract_lessons(actions_taken, result, success),
            importance=0.6 if success else 0.4
        )

        # Aprende padroes
        if success:
            # Padrao de sucesso
            pattern = self.memory.learn_pattern(
                pattern_type="success",
                trigger=task_description[:100],
                action="; ".join(actions_taken[:5]),
                expected_outcome="task_completed",
                confidence=0.6
            )

            insights.append(LearningInsight(
                id=pattern.id,
                insight_type="pattern",
                condition=pattern.trigger_condition,
                action=pattern.action,
                confidence=pattern.confidence,
                source_count=1,
                last_validated=datetime.now().isoformat()
            ))

        else:
            # Aprende o que evitar
            if "error" in str(result).lower():
                pattern = self.memory.learn_pattern(
                    pattern_type="failure",
                    trigger=task_description[:100],
                    action=f"EVITAR: {actions_taken[-1] if actions_taken else 'acao desconhecida'}",
                    expected_outcome="error",
                    confidence=0.4
                )

        # Cria memoria da experiencia
        self.memory.remember(
            content=f"Tarefa: {task_description}. Resultado: {'sucesso' if success else 'falha'}",
            memory_type=MemoryType.EPISODIC,
            context={"task_id": task_id, "success": success},
            importance=0.5,
            emotional_valence=0.5 if success else -0.3
        )

        return insights

    def _extract_lessons(self,
                        actions: List[str],
                        result: Dict,
                        success: bool) -> List[str]:
        """Extrai licoes de uma experiencia"""
        lessons = []

        if success:
            if len(actions) <= 3:
                lessons.append("Solucao eficiente - poucas acoes necessarias")
            if "test" in str(actions).lower():
                lessons.append("Testes ajudam a garantir qualidade")
        else:
            if "error" in str(result).lower():
                error_msg = result.get("error", "")[:100]
                lessons.append(f"Erro encontrado: {error_msg}")
            if len(actions) > 10:
                lessons.append("Muitas acoes podem indicar complexidade excessiva")

        return lessons

    def analyze_patterns(self) -> Dict:
        """
        Analisa padroes nas experiencias

        Returns:
            Dict com padroes identificados
        """
        # Busca episodios positivos e negativos
        positive = self.episodes.recall_by_outcome(positive=True, limit=50)
        negative = self.episodes.recall_by_outcome(positive=False, limit=50)

        # Extrai padroes de acoes
        success_actions = []
        failure_actions = []

        for ep in positive:
            success_actions.extend(ep.actions_taken)

        for ep in negative:
            failure_actions.extend(ep.actions_taken)

        # Conta frequencia
        from collections import Counter
        success_freq = Counter(success_actions)
        failure_freq = Counter(failure_actions)

        # Identifica acoes que levam ao sucesso
        good_actions = [a for a, c in success_freq.most_common(10) if a not in failure_freq]
        bad_actions = [a for a, c in failure_freq.most_common(10) if a not in success_freq]

        return {
            "acoes_efetivas": good_actions,
            "acoes_problematicas": bad_actions,
            "total_episodios_analisados": len(positive) + len(negative),
            "taxa_sucesso": len(positive) / (len(positive) + len(negative)) if (positive or negative) else 0
        }

    def get_recommendation(self, situation: str) -> Optional[str]:
        """
        Retorna recomendacao baseada em aprendizado

        Args:
            situation: Descricao da situacao atual

        Returns:
            Recomendacao ou None
        """
        # Busca padroes aplicaveis
        patterns = self.memory.get_applicable_patterns(situation, "success")

        if patterns:
            # Retorna acao do padrao mais confiavel
            best = max(patterns, key=lambda p: p.confidence)
            return f"[Confianca: {best.confidence:.0%}] {best.action}"

        # Busca decisoes similares
        decisions = self.memory.get_similar_decisions(situation, limit=3)
        if decisions:
            best = max(decisions, key=lambda d: d.success_rating or 0)
            if best.success_rating and best.success_rating >= 0.7:
                return f"[Historico] {best.decision_made}"

        return None

    def consolidate_learning(self) -> Dict:
        """
        Consolida aprendizado

        Analisa todas as experiencias e atualiza regras
        """
        # Analisa padroes
        patterns = self.analyze_patterns()

        # Gera sabedoria dos episodios
        wisdom = self.episodes.generate_wisdom()

        # Busca performance do feedback
        performance = self.feedback.get_agent_performance(self.agent_id)
        suggestions = self.feedback.get_improvement_suggestions(self.agent_id)

        # Cria insights consolidados
        insights_created = 0

        for action in patterns["acoes_efetivas"][:5]:
            self._save_insight(
                insight_type="heuristic",
                condition="situacao_geral",
                action=action,
                confidence=0.7
            )
            insights_created += 1

        return {
            "insights_created": insights_created,
            "patterns_found": len(patterns["acoes_efetivas"]) + len(patterns["acoes_problematicas"]),
            "success_rate": patterns["taxa_sucesso"],
            "performance": performance,
            "suggestions": suggestions,
            "wisdom": wisdom
        }

    def _save_insight(self,
                     insight_type: str,
                     condition: str,
                     action: str,
                     confidence: float):
        """Salva insight no banco"""
        conn = sqlite3.connect(self.db_path)

        insight_id = self._generate_id("INS")

        conn.execute("""
            INSERT OR REPLACE INTO insights
            (id, insight_type, condition, action, confidence, source_count, last_validated, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            insight_id,
            insight_type,
            condition,
            action,
            confidence,
            1,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def strengthen_association(self, concept_a: str, concept_b: str, strength_delta: float = 0.1):
        """
        Fortalece associacao entre dois conceitos

        Usado para aprendizado associativo
        """
        conn = sqlite3.connect(self.db_path)

        # Verifica se associacao existe
        cursor = conn.execute("""
            SELECT id, strength FROM associations
            WHERE concept_a = ? AND concept_b = ?
        """, (concept_a, concept_b))

        row = cursor.fetchone()

        if row:
            # Atualiza forca
            new_strength = min(1.0, row[1] + strength_delta)
            conn.execute(
                "UPDATE associations SET strength = ? WHERE id = ?",
                (new_strength, row[0])
            )
        else:
            # Cria nova associacao
            conn.execute("""
                INSERT INTO associations (concept_a, concept_b, strength, created_at)
                VALUES (?, ?, ?, ?)
            """, (concept_a, concept_b, 0.1 + strength_delta, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_associated_concepts(self, concept: str, min_strength: float = 0.3) -> List[Tuple[str, float]]:
        """
        Busca conceitos associados

        Returns:
            Lista de (conceito, forca)
        """
        conn = sqlite3.connect(self.db_path)

        cursor = conn.execute("""
            SELECT concept_b, strength FROM associations
            WHERE concept_a = ? AND strength >= ?
            ORDER BY strength DESC
        """, (concept, min_strength))

        results = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()

        return results

    def get_learning_summary(self) -> Dict:
        """Retorna resumo do aprendizado"""
        conn = sqlite3.connect(self.db_path)

        # Conta insights
        cursor = conn.execute("SELECT COUNT(*) FROM insights")
        insights_count = cursor.fetchone()[0]

        # Conta regras
        cursor = conn.execute("SELECT COUNT(*) FROM learned_rules")
        rules_count = cursor.fetchone()[0]

        # Conta associacoes
        cursor = conn.execute("SELECT COUNT(*) FROM associations")
        associations_count = cursor.fetchone()[0]

        conn.close()

        # Stats da memoria
        memory_stats = self.memory.get_stats()

        # Performance
        performance = self.feedback.get_agent_performance(self.agent_id)

        return {
            "agent_id": self.agent_id,
            "insights": insights_count,
            "rules": rules_count,
            "associations": associations_count,
            "memory": memory_stats,
            "performance": performance
        }
