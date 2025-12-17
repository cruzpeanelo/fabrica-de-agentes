"""
Sistema de Feedback e Avaliacao de Resultados
=============================================

Permite que agentes aprendam com resultados de suas acoes:
- Avaliacao automatica de resultados
- Feedback de outros agentes
- Feedback humano (quando disponivel)
- Ajuste de comportamento baseado em feedback
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


class FeedbackType(str, Enum):
    """Tipos de feedback"""
    AUTO = "auto"           # Avaliacao automatica
    AGENT = "agent"         # Feedback de outro agente
    HUMAN = "human"         # Feedback humano
    SYSTEM = "system"       # Feedback do sistema
    TEST = "test"           # Resultado de teste


class FeedbackResult(str, Enum):
    """Resultado do feedback"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class TaskFeedback:
    """Feedback de uma tarefa"""
    id: str
    task_id: str
    agent_id: str
    feedback_type: FeedbackType
    result: FeedbackResult
    score: float                      # 0-1
    details: str
    suggestions: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    processed: bool = False


class FeedbackSystem:
    """
    Sistema de Feedback para Agentes

    Coleta, processa e aprende com feedback de multiplas fontes.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("factory/database/feedback.db")
        self._evaluators: List[Callable] = []
        self._init_database()

    def _init_database(self):
        """Inicializa banco"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)

        # Tabela de feedback
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                feedback_type TEXT,
                result TEXT,
                score REAL,
                details TEXT,
                suggestions TEXT,
                metrics TEXT,
                timestamp TEXT,
                processed INTEGER DEFAULT 0
            )
        """)

        # Tabela de metricas agregadas por agente
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_metrics (
                agent_id TEXT PRIMARY KEY,
                total_tasks INTEGER DEFAULT 0,
                successful_tasks INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0,
                recent_trend REAL DEFAULT 0,
                strongest_areas TEXT,
                weakest_areas TEXT,
                updated_at TEXT
            )
        """)

        # Tabela de tendencias
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                timestamp TEXT
            )
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_fb_agent ON feedback(agent_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fb_task ON feedback(task_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fb_processed ON feedback(processed)")

        conn.commit()
        conn.close()

    def _generate_id(self) -> str:
        import hashlib
        hash_input = f"FB_{datetime.now().isoformat()}"
        return f"FB-{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def register_evaluator(self, evaluator: Callable):
        """
        Registra avaliador automatico

        Args:
            evaluator: Funcao que recebe (task_result, context) e retorna score 0-1
        """
        self._evaluators.append(evaluator)

    def submit_feedback(self,
                       task_id: str,
                       agent_id: str,
                       feedback_type: FeedbackType,
                       result: FeedbackResult,
                       score: float,
                       details: str,
                       suggestions: Optional[List[str]] = None,
                       metrics: Optional[Dict] = None) -> TaskFeedback:
        """
        Submete feedback para uma tarefa

        Args:
            task_id: ID da tarefa
            agent_id: ID do agente
            feedback_type: Tipo de feedback
            result: Resultado (success, failure, etc)
            score: Score de 0 a 1
            details: Detalhes do feedback
            suggestions: Sugestoes de melhoria
            metrics: Metricas adicionais

        Returns:
            TaskFeedback criado
        """
        feedback = TaskFeedback(
            id=self._generate_id(),
            task_id=task_id,
            agent_id=agent_id,
            feedback_type=feedback_type,
            result=result,
            score=min(1.0, max(0.0, score)),
            details=details,
            suggestions=suggestions or [],
            metrics=metrics or {}
        )

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO feedback
            (id, task_id, agent_id, feedback_type, result, score,
             details, suggestions, metrics, timestamp, processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback.id,
            feedback.task_id,
            feedback.agent_id,
            feedback.feedback_type.value,
            feedback.result.value,
            feedback.score,
            feedback.details,
            json.dumps(feedback.suggestions),
            json.dumps(feedback.metrics),
            feedback.timestamp,
            0
        ))
        conn.commit()
        conn.close()

        # Atualiza metricas do agente
        self._update_agent_metrics(agent_id)

        return feedback

    def auto_evaluate(self,
                     task_id: str,
                     agent_id: str,
                     task_result: Dict,
                     context: Optional[Dict] = None) -> TaskFeedback:
        """
        Avalia automaticamente resultado de tarefa

        Args:
            task_id: ID da tarefa
            agent_id: ID do agente
            task_result: Resultado da tarefa
            context: Contexto adicional

        Returns:
            TaskFeedback gerado
        """
        context = context or {}
        scores = []
        suggestions = []
        details_parts = []

        # Avaliacao basica
        if "error" in task_result or "exception" in task_result:
            scores.append(0.0)
            details_parts.append("Erro encontrado na execucao")
            suggestions.append("Verificar tratamento de erros")
        elif "files_modified" in task_result:
            files = task_result.get("files_modified", [])
            if files:
                scores.append(0.8)
                details_parts.append(f"Modificou {len(files)} arquivo(s)")
            else:
                scores.append(0.5)
                details_parts.append("Nenhum arquivo modificado")

        # Avaliadores customizados
        for evaluator in self._evaluators:
            try:
                eval_score = evaluator(task_result, context)
                if isinstance(eval_score, tuple):
                    score, suggestion = eval_score
                    scores.append(score)
                    if suggestion:
                        suggestions.append(suggestion)
                else:
                    scores.append(eval_score)
            except Exception as e:
                details_parts.append(f"Avaliador falhou: {str(e)}")

        # Calcula score final
        final_score = sum(scores) / len(scores) if scores else 0.5

        # Determina resultado
        if final_score >= 0.8:
            result = FeedbackResult.SUCCESS
        elif final_score >= 0.5:
            result = FeedbackResult.PARTIAL
        elif final_score >= 0.2:
            result = FeedbackResult.FAILURE
        else:
            result = FeedbackResult.ERROR

        return self.submit_feedback(
            task_id=task_id,
            agent_id=agent_id,
            feedback_type=FeedbackType.AUTO,
            result=result,
            score=final_score,
            details=" | ".join(details_parts) if details_parts else "Avaliacao automatica",
            suggestions=suggestions,
            metrics={"task_result": task_result}
        )

    def _update_agent_metrics(self, agent_id: str):
        """Atualiza metricas agregadas do agente"""
        conn = sqlite3.connect(self.db_path)

        # Busca todos os feedbacks do agente
        cursor = conn.execute("""
            SELECT score, result, metrics FROM feedback
            WHERE agent_id = ?
            ORDER BY timestamp DESC
        """, (agent_id,))

        rows = cursor.fetchall()

        if not rows:
            conn.close()
            return

        total = len(rows)
        successful = sum(1 for r in rows if r[1] in ['success', 'partial'])
        avg_score = sum(r[0] for r in rows) / total

        # Calcula tendencia (ultimos 10 vs anteriores)
        recent = rows[:10]
        older = rows[10:20]
        recent_avg = sum(r[0] for r in recent) / len(recent) if recent else 0
        older_avg = sum(r[0] for r in older) / len(older) if older else recent_avg
        trend = recent_avg - older_avg

        # Analisa areas (baseado em metricas)
        area_scores: Dict[str, List[float]] = {}
        for row in rows:
            metrics = json.loads(row[2]) if row[2] else {}
            area = metrics.get("area", "general")
            if area not in area_scores:
                area_scores[area] = []
            area_scores[area].append(row[0])

        # Calcula medias por area
        area_avgs = {area: sum(scores)/len(scores) for area, scores in area_scores.items() if scores}
        sorted_areas = sorted(area_avgs.items(), key=lambda x: x[1], reverse=True)

        strongest = [a[0] for a in sorted_areas[:3]]
        weakest = [a[0] for a in sorted_areas[-3:]]

        # Salva metricas
        conn.execute("""
            INSERT OR REPLACE INTO agent_metrics
            (agent_id, total_tasks, successful_tasks, avg_score,
             recent_trend, strongest_areas, weakest_areas, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_id,
            total,
            successful,
            avg_score,
            trend,
            json.dumps(strongest),
            json.dumps(weakest),
            datetime.now().isoformat()
        ))

        # Registra tendencia
        conn.execute("""
            INSERT INTO performance_trends
            (agent_id, metric_name, metric_value, timestamp)
            VALUES (?, ?, ?, ?)
        """, (agent_id, "avg_score", avg_score, datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def get_agent_performance(self, agent_id: str) -> Dict:
        """
        Retorna performance de um agente

        Returns:
            Dict com metricas de performance
        """
        conn = sqlite3.connect(self.db_path)

        cursor = conn.execute(
            "SELECT * FROM agent_metrics WHERE agent_id = ?",
            (agent_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return {
                "agent_id": agent_id,
                "total_tasks": 0,
                "success_rate": 0,
                "avg_score": 0,
                "trend": "neutral"
            }

        # Busca tendencia historica
        cursor = conn.execute("""
            SELECT metric_value, timestamp FROM performance_trends
            WHERE agent_id = ? AND metric_name = 'avg_score'
            ORDER BY timestamp DESC
            LIMIT 30
        """, (agent_id,))
        trend_data = [(r[0], r[1]) for r in cursor.fetchall()]

        conn.close()

        trend_direction = "stable"
        if row[4] > 0.05:
            trend_direction = "improving"
        elif row[4] < -0.05:
            trend_direction = "declining"

        return {
            "agent_id": agent_id,
            "total_tasks": row[1],
            "successful_tasks": row[2],
            "success_rate": round(row[2] / row[1] * 100, 1) if row[1] > 0 else 0,
            "avg_score": round(row[3], 2),
            "recent_trend": round(row[4], 3),
            "trend_direction": trend_direction,
            "strongest_areas": json.loads(row[5]) if row[5] else [],
            "weakest_areas": json.loads(row[6]) if row[6] else [],
            "trend_history": trend_data[:10]
        }

    def get_improvement_suggestions(self, agent_id: str, limit: int = 10) -> List[str]:
        """
        Retorna sugestoes de melhoria para um agente

        Baseado em feedback recebido
        """
        conn = sqlite3.connect(self.db_path)

        cursor = conn.execute("""
            SELECT suggestions FROM feedback
            WHERE agent_id = ?
            AND suggestions != '[]'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (agent_id, limit * 2))

        all_suggestions = []
        for row in cursor.fetchall():
            suggestions = json.loads(row[0]) if row[0] else []
            all_suggestions.extend(suggestions)

        conn.close()

        # Remove duplicatas mantendo ordem
        seen = set()
        unique = []
        for s in all_suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)

        return unique[:limit]

    def get_recent_feedback(self,
                           agent_id: Optional[str] = None,
                           limit: int = 20) -> List[TaskFeedback]:
        """Retorna feedback recente"""
        conn = sqlite3.connect(self.db_path)

        if agent_id:
            cursor = conn.execute("""
                SELECT * FROM feedback
                WHERE agent_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent_id, limit))
        else:
            cursor = conn.execute("""
                SELECT * FROM feedback
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        feedbacks = []
        for row in cursor.fetchall():
            feedbacks.append(TaskFeedback(
                id=row[0],
                task_id=row[1],
                agent_id=row[2],
                feedback_type=FeedbackType(row[3]),
                result=FeedbackResult(row[4]),
                score=row[5],
                details=row[6],
                suggestions=json.loads(row[7]) if row[7] else [],
                metrics=json.loads(row[8]) if row[8] else {},
                timestamp=row[9],
                processed=bool(row[10])
            ))

        conn.close()
        return feedbacks

    def compare_agents(self, agent_ids: List[str]) -> Dict:
        """
        Compara performance de multiplos agentes

        Returns:
            Dict com comparacao
        """
        performances = []
        for agent_id in agent_ids:
            perf = self.get_agent_performance(agent_id)
            performances.append(perf)

        # Ordena por score
        performances.sort(key=lambda p: p["avg_score"], reverse=True)

        return {
            "agents": performances,
            "best_performer": performances[0]["agent_id"] if performances else None,
            "average_score": sum(p["avg_score"] for p in performances) / len(performances) if performances else 0
        }
