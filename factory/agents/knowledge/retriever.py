"""
Knowledge Retriever - Busca Inteligente de Conhecimento
======================================================

Combina multiplas estrategias de busca:
- Busca semantica (embeddings)
- Busca por keywords
- Busca por contexto
- Reranking baseado em relevancia
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from .knowledge_base import KnowledgeBase, KnowledgeType, SearchResult


@dataclass
class RetrievalContext:
    """Contexto para busca"""
    agent_id: Optional[str] = None
    project_id: Optional[str] = None
    task_type: Optional[str] = None
    current_file: Optional[str] = None
    recent_actions: List[str] = None

    def __post_init__(self):
        if self.recent_actions is None:
            self.recent_actions = []


class KnowledgeRetriever:
    """
    Recuperador inteligente de conhecimento

    Combina busca semantica com filtros contextuais
    e reranking para melhor relevancia.
    """

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base

    def retrieve(self,
                query: str,
                context: Optional[RetrievalContext] = None,
                knowledge_types: Optional[List[KnowledgeType]] = None,
                limit: int = 10) -> List[SearchResult]:
        """
        Recupera conhecimento relevante

        Args:
            query: Texto de busca
            context: Contexto adicional
            knowledge_types: Tipos de conhecimento a buscar
            limit: Maximo de resultados

        Returns:
            Lista de resultados ordenados por relevancia
        """
        context = context or RetrievalContext()
        all_results = []

        # Busca por tipo se especificado
        if knowledge_types:
            for k_type in knowledge_types:
                results = self.kb.search(
                    query=query,
                    knowledge_type=k_type,
                    agent_id=context.agent_id,
                    project_id=context.project_id,
                    limit=limit * 2  # Busca mais para reranking
                )
                all_results.extend(results)
        else:
            # Busca geral
            all_results = self.kb.search(
                query=query,
                agent_id=context.agent_id,
                project_id=context.project_id,
                limit=limit * 2
            )

        # Rerank baseado em contexto
        reranked = self._rerank(all_results, query, context)

        # Remove duplicatas mantendo maior score
        seen = set()
        unique_results = []
        for result in reranked:
            if result.item.id not in seen:
                seen.add(result.item.id)
                unique_results.append(result)

        return unique_results[:limit]

    def _rerank(self,
               results: List[SearchResult],
               query: str,
               context: RetrievalContext) -> List[SearchResult]:
        """
        Reordena resultados baseado em fatores adicionais
        """
        for result in results:
            boost = 0.0

            # Boost por relevancia historica
            boost += result.item.relevance_score * 0.1

            # Boost se do mesmo agente
            if context.agent_id and result.item.agent_id == context.agent_id:
                boost += 0.15

            # Boost se do mesmo projeto
            if context.project_id and result.item.project_id == context.project_id:
                boost += 0.1

            # Boost por tipo de tarefa
            if context.task_type:
                if context.task_type in str(result.item.metadata):
                    boost += 0.1

            # Boost por recencia (items mais novos)
            # Versoes mais novas sao mais relevantes
            boost += min(result.item.version * 0.02, 0.1)

            # Aplica boost
            result.similarity = min(1.0, result.similarity + boost)

        # Reordena
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results

    def retrieve_for_task(self,
                         task_description: str,
                         agent_id: str,
                         project_id: Optional[str] = None) -> Dict[str, List[SearchResult]]:
        """
        Recupera conhecimento relevante para uma task

        Returns:
            Dict com resultados por categoria:
            - 'patterns': Padroes aprendidos
            - 'errors': Erros e solucoes conhecidas
            - 'best_practices': Boas praticas
            - 'related_code': Codigo relacionado
        """
        context = RetrievalContext(
            agent_id=agent_id,
            project_id=project_id
        )

        return {
            "patterns": self.retrieve(
                task_description,
                context,
                [KnowledgeType.PATTERN],
                limit=5
            ),
            "errors": self.retrieve(
                task_description,
                context,
                [KnowledgeType.ERROR],
                limit=5
            ),
            "best_practices": self.retrieve(
                task_description,
                context,
                [KnowledgeType.BEST_PRACTICE],
                limit=5
            ),
            "related_code": self.retrieve(
                task_description,
                context,
                [KnowledgeType.CODE],
                limit=5
            ),
            "documentation": self.retrieve(
                task_description,
                context,
                [KnowledgeType.DOCUMENTATION],
                limit=3
            )
        }

    def get_agent_context(self, agent_id: str, limit: int = 20) -> List[SearchResult]:
        """
        Recupera contexto geral do agente

        Busca conhecimento mais relevante e usado pelo agente
        """
        # Busca conhecimento do agente ordenado por relevancia
        items = self.kb.get_agent_knowledge(agent_id)

        results = []
        for item in items[:limit]:
            results.append(SearchResult(
                item=item,
                similarity=item.relevance_score
            ))

        return results
