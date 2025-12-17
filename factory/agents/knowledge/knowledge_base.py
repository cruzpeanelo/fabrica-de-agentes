"""
Base de Conhecimento Vetorial para Agentes Autonomos
====================================================

Armazena e recupera conhecimento de forma inteligente:
- Documentacao tecnica
- Codigo fonte indexado
- Decisoes passadas
- Padroes aprendidos
- Boas praticas

Funcionalidades:
- Indexacao automatica de arquivos
- Busca semantica
- Versionamento de conhecimento
- Compartilhamento entre agentes
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from .embeddings import EmbeddingEngine, EmbeddingResult


class KnowledgeType(str, Enum):
    """Tipos de conhecimento"""
    DOCUMENTATION = "documentation"      # Docs, READMEs
    CODE = "code"                         # Codigo fonte
    DECISION = "decision"                 # Decisoes tecnicas
    PATTERN = "pattern"                   # Padroes aprendidos
    ERROR = "error"                       # Erros e solucoes
    BEST_PRACTICE = "best_practice"       # Boas praticas
    DOMAIN = "domain"                     # Conhecimento de dominio
    TASK = "task"                         # Conhecimento de tarefas


@dataclass
class KnowledgeItem:
    """Item de conhecimento"""
    id: str
    content: str
    knowledge_type: KnowledgeType
    source: str                           # Arquivo, agente, etc
    agent_id: Optional[str] = None        # Agente que criou
    project_id: Optional[str] = None      # Projeto relacionado
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1
    relevance_score: float = 0.0          # Score de uso/relevancia


@dataclass
class SearchResult:
    """Resultado de busca"""
    item: KnowledgeItem
    similarity: float
    context_snippets: List[str] = field(default_factory=list)


class KnowledgeBase:
    """
    Base de Conhecimento Vetorial

    Armazena conhecimento de forma estruturada e permite
    busca semantica eficiente para os agentes.
    """

    def __init__(self,
                 db_path: Optional[Path] = None,
                 embedding_engine: Optional[EmbeddingEngine] = None):
        """
        Args:
            db_path: Caminho do banco SQLite
            embedding_engine: Motor de embeddings (cria um se nao fornecido)
        """
        self.db_path = db_path or Path("factory/database/knowledge_base.db")
        self.embedding = embedding_engine or EmbeddingEngine()

        self._init_database()

    def _init_database(self):
        """Inicializa banco de dados"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)

        # Tabela principal de conhecimento
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                knowledge_type TEXT NOT NULL,
                source TEXT,
                agent_id TEXT,
                project_id TEXT,
                tags TEXT,
                metadata TEXT,
                embedding TEXT,
                created_at TEXT,
                updated_at TEXT,
                version INTEGER DEFAULT 1,
                relevance_score REAL DEFAULT 0.0
            )
        """)

        # Indice para busca por tipo
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_type
            ON knowledge(knowledge_type)
        """)

        # Indice para busca por agente
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_agent
            ON knowledge(agent_id)
        """)

        # Indice para busca por projeto
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_project
            ON knowledge(project_id)
        """)

        # Tabela de relacoes entre conhecimentos
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                created_at TEXT,
                FOREIGN KEY (source_id) REFERENCES knowledge(id),
                FOREIGN KEY (target_id) REFERENCES knowledge(id)
            )
        """)

        # Tabela de uso de conhecimento (para aprendizado)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT NOT NULL,
                agent_id TEXT,
                task_id TEXT,
                usage_type TEXT,
                was_useful INTEGER,
                feedback TEXT,
                timestamp TEXT,
                FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
            )
        """)

        conn.commit()
        conn.close()

    def _generate_id(self, content: str, knowledge_type: str) -> str:
        """Gera ID unico para item"""
        import hashlib
        hash_input = f"{content[:100]}_{knowledge_type}_{datetime.now().isoformat()}"
        return f"K-{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"

    def add(self,
            content: str,
            knowledge_type: KnowledgeType,
            source: str,
            agent_id: Optional[str] = None,
            project_id: Optional[str] = None,
            tags: Optional[List[str]] = None,
            metadata: Optional[Dict] = None) -> KnowledgeItem:
        """
        Adiciona conhecimento a base

        Args:
            content: Conteudo do conhecimento
            knowledge_type: Tipo de conhecimento
            source: Origem (arquivo, agente, etc)
            agent_id: ID do agente que criou
            project_id: ID do projeto relacionado
            tags: Tags para categorizacao
            metadata: Metadados adicionais

        Returns:
            KnowledgeItem criado
        """
        # Gera ID
        item_id = self._generate_id(content, knowledge_type.value)

        # Gera embedding
        embed_result = self.embedding.embed(content)

        # Cria item
        item = KnowledgeItem(
            id=item_id,
            content=content,
            knowledge_type=knowledge_type,
            source=source,
            agent_id=agent_id,
            project_id=project_id,
            tags=tags or [],
            metadata=metadata or {},
            embedding=embed_result.vector
        )

        # Salva no banco
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO knowledge
            (id, content, knowledge_type, source, agent_id, project_id,
             tags, metadata, embedding, created_at, updated_at, version, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.id,
            item.content,
            item.knowledge_type.value,
            item.source,
            item.agent_id,
            item.project_id,
            json.dumps(item.tags),
            json.dumps(item.metadata),
            json.dumps(item.embedding),
            item.created_at,
            item.updated_at,
            item.version,
            item.relevance_score
        ))
        conn.commit()
        conn.close()

        return item

    def search(self,
               query: str,
               knowledge_type: Optional[KnowledgeType] = None,
               agent_id: Optional[str] = None,
               project_id: Optional[str] = None,
               tags: Optional[List[str]] = None,
               limit: int = 10,
               min_similarity: float = 0.3) -> List[SearchResult]:
        """
        Busca semantica na base de conhecimento

        Args:
            query: Texto de busca
            knowledge_type: Filtrar por tipo
            agent_id: Filtrar por agente
            project_id: Filtrar por projeto
            tags: Filtrar por tags
            limit: Maximo de resultados
            min_similarity: Similaridade minima

        Returns:
            Lista de SearchResult ordenada por similaridade
        """
        # Gera embedding da query
        query_embed = self.embedding.embed(query)

        # Busca no banco
        conn = sqlite3.connect(self.db_path)

        # Constroi query SQL
        sql = "SELECT * FROM knowledge WHERE 1=1"
        params = []

        if knowledge_type:
            sql += " AND knowledge_type = ?"
            params.append(knowledge_type.value)

        if agent_id:
            sql += " AND agent_id = ?"
            params.append(agent_id)

        if project_id:
            sql += " AND project_id = ?"
            params.append(project_id)

        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        # Calcula similaridade para cada item
        results = []
        for row in rows:
            item = self._row_to_item(row)

            # Filtra por tags se especificado
            if tags:
                if not any(t in item.tags for t in tags):
                    continue

            # Calcula similaridade
            if item.embedding:
                similarity = self.embedding.similarity(
                    query_embed.vector,
                    item.embedding
                )

                if similarity >= min_similarity:
                    results.append(SearchResult(
                        item=item,
                        similarity=similarity
                    ))

        # Ordena por similaridade
        results.sort(key=lambda r: r.similarity, reverse=True)

        return results[:limit]

    def _row_to_item(self, row) -> KnowledgeItem:
        """Converte row do banco para KnowledgeItem"""
        return KnowledgeItem(
            id=row[0],
            content=row[1],
            knowledge_type=KnowledgeType(row[2]),
            source=row[3],
            agent_id=row[4],
            project_id=row[5],
            tags=json.loads(row[6]) if row[6] else [],
            metadata=json.loads(row[7]) if row[7] else {},
            embedding=json.loads(row[8]) if row[8] else None,
            created_at=row[9],
            updated_at=row[10],
            version=row[11] or 1,
            relevance_score=row[12] or 0.0
        )

    def get(self, item_id: str) -> Optional[KnowledgeItem]:
        """Busca item por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT * FROM knowledge WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_item(row)
        return None

    def update(self, item_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Atualiza item existente"""
        item = self.get(item_id)
        if not item:
            return False

        # Gera novo embedding
        embed_result = self.embedding.embed(content)

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE knowledge
            SET content = ?, embedding = ?, metadata = ?,
                updated_at = ?, version = version + 1
            WHERE id = ?
        """, (
            content,
            json.dumps(embed_result.vector),
            json.dumps(metadata) if metadata else item.metadata,
            datetime.now().isoformat(),
            item_id
        ))
        conn.commit()
        conn.close()

        return True

    def delete(self, item_id: str) -> bool:
        """Remove item da base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM knowledge WHERE id = ?", (item_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def record_usage(self,
                    knowledge_id: str,
                    agent_id: str,
                    task_id: Optional[str] = None,
                    was_useful: bool = True,
                    feedback: Optional[str] = None):
        """
        Registra uso de conhecimento (para aprendizado)

        Args:
            knowledge_id: ID do conhecimento usado
            agent_id: Agente que usou
            task_id: Task onde foi usado
            was_useful: Se foi util
            feedback: Feedback adicional
        """
        conn = sqlite3.connect(self.db_path)

        # Registra uso
        conn.execute("""
            INSERT INTO knowledge_usage
            (knowledge_id, agent_id, task_id, usage_type, was_useful, feedback, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            knowledge_id,
            agent_id,
            task_id,
            "retrieval",
            1 if was_useful else 0,
            feedback,
            datetime.now().isoformat()
        ))

        # Atualiza relevancia
        if was_useful:
            conn.execute("""
                UPDATE knowledge
                SET relevance_score = relevance_score + 0.1
                WHERE id = ?
            """, (knowledge_id,))
        else:
            conn.execute("""
                UPDATE knowledge
                SET relevance_score = MAX(0, relevance_score - 0.05)
                WHERE id = ?
            """, (knowledge_id,))

        conn.commit()
        conn.close()

    def add_relation(self,
                    source_id: str,
                    target_id: str,
                    relation_type: str,
                    weight: float = 1.0):
        """
        Adiciona relacao entre conhecimentos

        Args:
            source_id: ID do conhecimento origem
            target_id: ID do conhecimento destino
            relation_type: Tipo de relacao (ex: 'related', 'depends', 'contradicts')
            weight: Peso da relacao
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO knowledge_relations
            (source_id, target_id, relation_type, weight, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            source_id,
            target_id,
            relation_type,
            weight,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

    def get_related(self, item_id: str, limit: int = 10) -> List[Tuple[KnowledgeItem, str, float]]:
        """
        Busca conhecimentos relacionados

        Returns:
            Lista de (KnowledgeItem, relation_type, weight)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT k.*, r.relation_type, r.weight
            FROM knowledge k
            JOIN knowledge_relations r ON k.id = r.target_id
            WHERE r.source_id = ?
            ORDER BY r.weight DESC
            LIMIT ?
        """, (item_id, limit))

        results = []
        for row in cursor.fetchall():
            item = self._row_to_item(row[:-2])
            relation_type = row[-2]
            weight = row[-1]
            results.append((item, relation_type, weight))

        conn.close()
        return results

    def get_agent_knowledge(self, agent_id: str) -> List[KnowledgeItem]:
        """Busca todo conhecimento de um agente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM knowledge WHERE agent_id = ? ORDER BY relevance_score DESC",
            (agent_id,)
        )
        results = [self._row_to_item(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def index_file(self,
                   file_path: Path,
                   agent_id: Optional[str] = None,
                   project_id: Optional[str] = None) -> List[KnowledgeItem]:
        """
        Indexa arquivo na base de conhecimento

        Args:
            file_path: Caminho do arquivo
            agent_id: Agente responsavel
            project_id: Projeto relacionado

        Returns:
            Lista de items criados
        """
        if not file_path.exists():
            return []

        # Determina tipo pelo extensao
        ext = file_path.suffix.lower()
        if ext in ['.py', '.js', '.ts', '.tsx', '.java', '.go', '.rs']:
            k_type = KnowledgeType.CODE
        elif ext in ['.md', '.rst', '.txt']:
            k_type = KnowledgeType.DOCUMENTATION
        else:
            k_type = KnowledgeType.DOMAIN

        # Le conteudo
        try:
            content = file_path.read_text(encoding='utf-8')
        except:
            return []

        items = []

        # Para arquivos grandes, divide em chunks
        if len(content) > 2000:
            chunks = self._split_content(content, k_type)
            for i, chunk in enumerate(chunks):
                item = self.add(
                    content=chunk,
                    knowledge_type=k_type,
                    source=str(file_path),
                    agent_id=agent_id,
                    project_id=project_id,
                    metadata={"chunk_index": i, "total_chunks": len(chunks)}
                )
                items.append(item)
        else:
            item = self.add(
                content=content,
                knowledge_type=k_type,
                source=str(file_path),
                agent_id=agent_id,
                project_id=project_id
            )
            items.append(item)

        return items

    def _split_content(self, content: str, k_type: KnowledgeType) -> List[str]:
        """Divide conteudo em chunks semanticos"""
        chunks = []

        if k_type == KnowledgeType.CODE:
            # Divide por funcoes/classes
            import re
            # Pattern para Python
            pattern = r'(?:^|\n)((?:class|def|async def)\s+\w+[^:]*:[\s\S]*?)(?=\n(?:class|def|async def)|\Z)'
            matches = re.findall(pattern, content, re.MULTILINE)

            if matches:
                chunks = [m.strip() for m in matches if len(m.strip()) > 50]
            else:
                # Fallback para divisao por linhas
                lines = content.split('\n')
                chunk_size = 50
                for i in range(0, len(lines), chunk_size):
                    chunk = '\n'.join(lines[i:i + chunk_size])
                    if len(chunk.strip()) > 50:
                        chunks.append(chunk)
        else:
            # Divide por paragrafos ou secoes
            sections = content.split('\n\n')
            current_chunk = ""

            for section in sections:
                if len(current_chunk) + len(section) < 1500:
                    current_chunk += section + "\n\n"
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = section + "\n\n"

            if current_chunk.strip():
                chunks.append(current_chunk.strip())

        return chunks if chunks else [content]

    def get_stats(self) -> Dict:
        """Retorna estatisticas da base"""
        conn = sqlite3.connect(self.db_path)

        # Total por tipo
        cursor = conn.execute("""
            SELECT knowledge_type, COUNT(*) as count
            FROM knowledge
            GROUP BY knowledge_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        # Total por agente
        cursor = conn.execute("""
            SELECT agent_id, COUNT(*) as count
            FROM knowledge
            WHERE agent_id IS NOT NULL
            GROUP BY agent_id
        """)
        by_agent = {row[0]: row[1] for row in cursor.fetchall()}

        # Total geral
        cursor = conn.execute("SELECT COUNT(*) FROM knowledge")
        total = cursor.fetchone()[0]

        # Mais usados
        cursor = conn.execute("""
            SELECT k.id, k.content, COUNT(u.id) as usage_count
            FROM knowledge k
            LEFT JOIN knowledge_usage u ON k.id = u.knowledge_id
            GROUP BY k.id
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        most_used = [(row[0], row[1][:100], row[2]) for row in cursor.fetchall()]

        conn.close()

        return {
            "total": total,
            "by_type": by_type,
            "by_agent": by_agent,
            "most_used": most_used
        }
