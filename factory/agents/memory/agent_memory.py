"""
Sistema de Memoria de Longo Prazo para Agentes
==============================================

Cada agente possui:
1. Memoria Episodica: Eventos e experiencias passadas
2. Memoria Semantica: Conhecimento factual e conceitos
3. Memoria Procedural: Como fazer tarefas especificas
4. Memoria de Trabalho: Contexto da sessao atual

A memoria permite:
- Lembrar decisoes passadas e seus resultados
- Aprender padroes de sucesso/falha
- Manter consistencia entre sessoes
- Evoluir com base em experiencias
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class MemoryType(str, Enum):
    """Tipos de memoria"""
    EPISODIC = "episodic"       # Eventos e experiencias
    SEMANTIC = "semantic"       # Conhecimento factual
    PROCEDURAL = "procedural"   # Como fazer coisas
    WORKING = "working"         # Contexto atual


@dataclass
class MemoryEntry:
    """Entrada de memoria"""
    id: str
    agent_id: str
    memory_type: MemoryType
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5           # 0-1, quão importante
    emotional_valence: float = 0.0    # -1 a 1 (negativo a positivo)
    access_count: int = 0             # Quantas vezes acessado
    last_access: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    decay_rate: float = 0.01          # Taxa de esquecimento
    associations: List[str] = field(default_factory=list)  # IDs de memorias relacionadas


@dataclass
class Decision:
    """Registro de decisao"""
    id: str
    agent_id: str
    task_id: Optional[str]
    context: str
    options_considered: List[str]
    decision_made: str
    reasoning: str
    outcome: Optional[str] = None
    success_rating: Optional[float] = None  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class LearnedPattern:
    """Padrao aprendido"""
    id: str
    agent_id: str
    pattern_type: str              # 'success', 'failure', 'optimization'
    trigger_condition: str         # Quando o padrao se aplica
    action: str                    # O que fazer
    expected_outcome: str          # Resultado esperado
    confidence: float = 0.5        # 0-1, confianca no padrao
    usage_count: int = 0
    success_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentMemory:
    """
    Sistema de Memoria Completo para Agentes

    Gerencia todos os tipos de memoria e permite
    que o agente aprenda e evolua com base em experiencias.
    """

    def __init__(self, agent_id: str, db_path: Optional[Path] = None):
        """
        Args:
            agent_id: ID do agente
            db_path: Caminho do banco de memoria
        """
        self.agent_id = agent_id
        self.db_path = db_path or Path(f"factory/database/memory_{agent_id}.db")
        self._init_database()

    def _init_database(self):
        """Inicializa banco de dados"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)

        # Tabela de memorias
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                context TEXT,
                importance REAL DEFAULT 0.5,
                emotional_valence REAL DEFAULT 0.0,
                access_count INTEGER DEFAULT 0,
                last_access TEXT,
                created_at TEXT,
                decay_rate REAL DEFAULT 0.01,
                associations TEXT
            )
        """)

        # Tabela de decisoes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                task_id TEXT,
                context TEXT,
                options_considered TEXT,
                decision_made TEXT,
                reasoning TEXT,
                outcome TEXT,
                success_rating REAL,
                timestamp TEXT
            )
        """)

        # Tabela de padroes aprendidos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                pattern_type TEXT,
                trigger_condition TEXT,
                action TEXT,
                expected_outcome TEXT,
                confidence REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Tabela de sessoes de trabalho
        conn.execute("""
            CREATE TABLE IF NOT EXISTS work_sessions (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                project_id TEXT,
                task_id TEXT,
                start_time TEXT,
                end_time TEXT,
                actions_taken TEXT,
                files_modified TEXT,
                errors_encountered TEXT,
                lessons_learned TEXT,
                success INTEGER
            )
        """)

        # Indices
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(memory_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mem_importance ON memories(importance DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_decisions_task ON decisions(task_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type)")

        conn.commit()
        conn.close()

    def _generate_id(self, prefix: str) -> str:
        """Gera ID unico"""
        import hashlib
        hash_input = f"{self.agent_id}_{prefix}_{datetime.now().isoformat()}"
        return f"{prefix}-{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    # ==================== MEMORIA ====================

    def remember(self,
                content: str,
                memory_type: MemoryType,
                context: Optional[Dict] = None,
                importance: float = 0.5,
                emotional_valence: float = 0.0) -> MemoryEntry:
        """
        Armazena uma nova memoria

        Args:
            content: Conteudo da memoria
            memory_type: Tipo de memoria
            context: Contexto adicional
            importance: Importancia (0-1)
            emotional_valence: Valencia emocional (-1 a 1)

        Returns:
            MemoryEntry criada
        """
        entry = MemoryEntry(
            id=self._generate_id("MEM"),
            agent_id=self.agent_id,
            memory_type=memory_type,
            content=content,
            context=context or {},
            importance=importance,
            emotional_valence=emotional_valence
        )

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO memories
            (id, agent_id, memory_type, content, context, importance,
             emotional_valence, access_count, created_at, decay_rate, associations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id,
            entry.agent_id,
            entry.memory_type.value,
            entry.content,
            json.dumps(entry.context),
            entry.importance,
            entry.emotional_valence,
            0,
            entry.created_at,
            entry.decay_rate,
            json.dumps([])
        ))
        conn.commit()
        conn.close()

        return entry

    def recall(self,
              query: str,
              memory_type: Optional[MemoryType] = None,
              limit: int = 10,
              min_importance: float = 0.0) -> List[MemoryEntry]:
        """
        Recupera memorias relevantes

        Args:
            query: Texto de busca
            memory_type: Filtrar por tipo
            limit: Maximo de resultados
            min_importance: Importancia minima

        Returns:
            Lista de memorias ordenadas por relevancia
        """
        conn = sqlite3.connect(self.db_path)

        sql = """
            SELECT * FROM memories
            WHERE agent_id = ?
            AND importance >= ?
        """
        params = [self.agent_id, min_importance]

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type.value)

        # Busca simples por conteudo (pode ser melhorado com FTS)
        sql += " AND content LIKE ?"
        params.append(f"%{query}%")

        sql += " ORDER BY importance DESC, access_count DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()

        # Atualiza access_count
        for row in rows:
            conn.execute("""
                UPDATE memories
                SET access_count = access_count + 1,
                    last_access = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), row[0]))

        conn.commit()
        conn.close()

        return [self._row_to_memory(row) for row in rows]

    def _row_to_memory(self, row) -> MemoryEntry:
        """Converte row para MemoryEntry"""
        return MemoryEntry(
            id=row[0],
            agent_id=row[1],
            memory_type=MemoryType(row[2]),
            content=row[3],
            context=json.loads(row[4]) if row[4] else {},
            importance=row[5],
            emotional_valence=row[6],
            access_count=row[7],
            last_access=row[8],
            created_at=row[9],
            decay_rate=row[10],
            associations=json.loads(row[11]) if row[11] else []
        )

    def forget_unimportant(self, threshold: float = 0.1, days_old: int = 30):
        """
        Remove memorias antigas e pouco importantes

        Simula esquecimento natural para manter memoria eficiente
        """
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            DELETE FROM memories
            WHERE agent_id = ?
            AND importance < ?
            AND created_at < ?
            AND access_count < 5
        """, (self.agent_id, threshold, cutoff_date))
        deleted = conn.total_changes
        conn.commit()
        conn.close()

        return deleted

    def reinforce(self, memory_id: str, boost: float = 0.1):
        """
        Reforça uma memoria (aumenta importancia)

        Chamado quando memoria foi util
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE memories
            SET importance = MIN(1.0, importance + ?),
                access_count = access_count + 1,
                last_access = ?
            WHERE id = ?
        """, (boost, datetime.now().isoformat(), memory_id))
        conn.commit()
        conn.close()

    # ==================== DECISOES ====================

    def record_decision(self,
                       context: str,
                       options: List[str],
                       decision: str,
                       reasoning: str,
                       task_id: Optional[str] = None) -> Decision:
        """
        Registra uma decisao tomada

        Args:
            context: Contexto da decisao
            options: Opcoes consideradas
            decision: Decisao tomada
            reasoning: Raciocinio usado
            task_id: ID da task relacionada

        Returns:
            Decision registrada
        """
        entry = Decision(
            id=self._generate_id("DEC"),
            agent_id=self.agent_id,
            task_id=task_id,
            context=context,
            options_considered=options,
            decision_made=decision,
            reasoning=reasoning
        )

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO decisions
            (id, agent_id, task_id, context, options_considered,
             decision_made, reasoning, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id,
            entry.agent_id,
            entry.task_id,
            entry.context,
            json.dumps(entry.options_considered),
            entry.decision_made,
            entry.reasoning,
            entry.timestamp
        ))
        conn.commit()
        conn.close()

        return entry

    def record_decision_outcome(self,
                               decision_id: str,
                               outcome: str,
                               success_rating: float):
        """
        Registra resultado de uma decisao

        Args:
            decision_id: ID da decisao
            outcome: O que aconteceu
            success_rating: Taxa de sucesso (0-1)
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE decisions
            SET outcome = ?, success_rating = ?
            WHERE id = ?
        """, (outcome, success_rating, decision_id))
        conn.commit()
        conn.close()

        # Se foi sucesso, cria memoria positiva
        if success_rating >= 0.7:
            cursor = conn.execute(
                "SELECT context, decision_made, reasoning FROM decisions WHERE id = ?",
                (decision_id,)
            )
            row = cursor.fetchone()
            if row:
                self.remember(
                    content=f"Decisao bem-sucedida: {row[1]}. Contexto: {row[0]}. Raciocinio: {row[2]}",
                    memory_type=MemoryType.EPISODIC,
                    context={"decision_id": decision_id, "outcome": outcome},
                    importance=0.7,
                    emotional_valence=0.5
                )

    def get_similar_decisions(self, context: str, limit: int = 5) -> List[Decision]:
        """
        Busca decisoes similares para aprender com o passado
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT * FROM decisions
            WHERE agent_id = ?
            AND context LIKE ?
            AND success_rating IS NOT NULL
            ORDER BY success_rating DESC
            LIMIT ?
        """, (self.agent_id, f"%{context[:50]}%", limit))

        decisions = []
        for row in cursor.fetchall():
            decisions.append(Decision(
                id=row[0],
                agent_id=row[1],
                task_id=row[2],
                context=row[3],
                options_considered=json.loads(row[4]) if row[4] else [],
                decision_made=row[5],
                reasoning=row[6],
                outcome=row[7],
                success_rating=row[8],
                timestamp=row[9]
            ))
        conn.close()

        return decisions

    # ==================== PADROES APRENDIDOS ====================

    def learn_pattern(self,
                     pattern_type: str,
                     trigger: str,
                     action: str,
                     expected_outcome: str,
                     confidence: float = 0.5) -> LearnedPattern:
        """
        Aprende um novo padrao

        Args:
            pattern_type: 'success', 'failure', 'optimization'
            trigger: Condicao que ativa o padrao
            action: Acao a tomar
            expected_outcome: Resultado esperado
            confidence: Confianca inicial

        Returns:
            LearnedPattern criado
        """
        pattern = LearnedPattern(
            id=self._generate_id("PAT"),
            agent_id=self.agent_id,
            pattern_type=pattern_type,
            trigger_condition=trigger,
            action=action,
            expected_outcome=expected_outcome,
            confidence=confidence
        )

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO patterns
            (id, agent_id, pattern_type, trigger_condition, action,
             expected_outcome, confidence, usage_count, success_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern.id,
            pattern.agent_id,
            pattern.pattern_type,
            pattern.trigger_condition,
            pattern.action,
            pattern.expected_outcome,
            pattern.confidence,
            0, 0,
            pattern.created_at,
            pattern.updated_at
        ))
        conn.commit()
        conn.close()

        return pattern

    def get_applicable_patterns(self, situation: str, pattern_type: Optional[str] = None) -> List[LearnedPattern]:
        """
        Busca padroes aplicaveis a uma situacao
        """
        conn = sqlite3.connect(self.db_path)

        sql = """
            SELECT * FROM patterns
            WHERE agent_id = ?
            AND confidence >= 0.3
        """
        params = [self.agent_id]

        if pattern_type:
            sql += " AND pattern_type = ?"
            params.append(pattern_type)

        sql += " ORDER BY confidence DESC, usage_count DESC"

        cursor = conn.execute(sql, params)

        patterns = []
        for row in cursor.fetchall():
            pattern = LearnedPattern(
                id=row[0],
                agent_id=row[1],
                pattern_type=row[2],
                trigger_condition=row[3],
                action=row[4],
                expected_outcome=row[5],
                confidence=row[6],
                usage_count=row[7],
                success_count=row[8],
                created_at=row[9],
                updated_at=row[10]
            )

            # Verifica se o trigger se aplica
            if self._pattern_matches(pattern.trigger_condition, situation):
                patterns.append(pattern)

        conn.close()
        return patterns

    def _pattern_matches(self, trigger: str, situation: str) -> bool:
        """Verifica se um trigger se aplica a uma situacao"""
        # Busca simples por keywords
        trigger_words = set(trigger.lower().split())
        situation_words = set(situation.lower().split())
        common = trigger_words.intersection(situation_words)
        return len(common) >= len(trigger_words) * 0.3

    def update_pattern_outcome(self, pattern_id: str, was_successful: bool):
        """
        Atualiza resultado de uso de padrao

        Ajusta confianca baseado no resultado
        """
        conn = sqlite3.connect(self.db_path)

        # Incrementa uso
        conn.execute("""
            UPDATE patterns
            SET usage_count = usage_count + 1,
                updated_at = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), pattern_id))

        if was_successful:
            # Aumenta confianca e contagem de sucesso
            conn.execute("""
                UPDATE patterns
                SET success_count = success_count + 1,
                    confidence = MIN(1.0, confidence + 0.05)
                WHERE id = ?
            """, (pattern_id,))
        else:
            # Diminui confianca
            conn.execute("""
                UPDATE patterns
                SET confidence = MAX(0.0, confidence - 0.1)
                WHERE id = ?
            """, (pattern_id,))

        conn.commit()
        conn.close()

    # ==================== SESSOES DE TRABALHO ====================

    def start_session(self, project_id: Optional[str] = None, task_id: Optional[str] = None) -> str:
        """Inicia sessao de trabalho"""
        session_id = self._generate_id("SES")

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO work_sessions
            (id, agent_id, project_id, task_id, start_time, actions_taken, files_modified, errors_encountered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            self.agent_id,
            project_id,
            task_id,
            datetime.now().isoformat(),
            json.dumps([]),
            json.dumps([]),
            json.dumps([])
        ))
        conn.commit()
        conn.close()

        return session_id

    def end_session(self,
                   session_id: str,
                   actions: List[str],
                   files: List[str],
                   errors: List[str],
                   lessons: List[str],
                   success: bool):
        """Finaliza sessao de trabalho"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE work_sessions
            SET end_time = ?,
                actions_taken = ?,
                files_modified = ?,
                errors_encountered = ?,
                lessons_learned = ?,
                success = ?
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            json.dumps(actions),
            json.dumps(files),
            json.dumps(errors),
            json.dumps(lessons),
            1 if success else 0,
            session_id
        ))
        conn.commit()
        conn.close()

        # Cria memorias das licoes aprendidas
        for lesson in lessons:
            self.remember(
                content=lesson,
                memory_type=MemoryType.PROCEDURAL,
                context={"session_id": session_id},
                importance=0.6 if success else 0.4,
                emotional_valence=0.3 if success else -0.3
            )

    # ==================== ESTATISTICAS ====================

    def get_stats(self) -> Dict:
        """Retorna estatisticas da memoria"""
        conn = sqlite3.connect(self.db_path)

        # Memorias por tipo
        cursor = conn.execute("""
            SELECT memory_type, COUNT(*) FROM memories
            WHERE agent_id = ?
            GROUP BY memory_type
        """, (self.agent_id,))
        memories_by_type = {row[0]: row[1] for row in cursor.fetchall()}

        # Total de decisoes
        cursor = conn.execute(
            "SELECT COUNT(*), AVG(success_rating) FROM decisions WHERE agent_id = ?",
            (self.agent_id,)
        )
        dec_row = cursor.fetchone()
        total_decisions = dec_row[0]
        avg_success = dec_row[1] or 0

        # Padroes
        cursor = conn.execute(
            "SELECT COUNT(*), AVG(confidence) FROM patterns WHERE agent_id = ?",
            (self.agent_id,)
        )
        pat_row = cursor.fetchone()
        total_patterns = pat_row[0]
        avg_confidence = pat_row[1] or 0

        # Sessoes
        cursor = conn.execute("""
            SELECT COUNT(*), SUM(success) FROM work_sessions WHERE agent_id = ?
        """, (self.agent_id,))
        ses_row = cursor.fetchone()
        total_sessions = ses_row[0]
        successful_sessions = ses_row[1] or 0

        conn.close()

        return {
            "agent_id": self.agent_id,
            "memories": {
                "total": sum(memories_by_type.values()),
                "by_type": memories_by_type
            },
            "decisions": {
                "total": total_decisions,
                "avg_success_rate": round(avg_success, 2)
            },
            "patterns": {
                "total": total_patterns,
                "avg_confidence": round(avg_confidence, 2)
            },
            "sessions": {
                "total": total_sessions,
                "successful": successful_sessions,
                "success_rate": round(successful_sessions / total_sessions, 2) if total_sessions > 0 else 0
            }
        }
