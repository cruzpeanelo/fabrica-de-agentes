"""
Teste do Sistema de Agentes Autonomos
=====================================

Verifica que todos os componentes funcionam corretamente:
1. Base de Conhecimento
2. Sistema de Memoria
3. Aprendizado e Feedback
4. Agente Autonomo
5. Runtime
"""

import sys
from pathlib import Path

# Adiciona path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from factory.agents.knowledge.embeddings import EmbeddingEngine, SemanticHashEmbedding
from factory.agents.knowledge.knowledge_base import KnowledgeBase, KnowledgeType
from factory.agents.knowledge.retriever import KnowledgeRetriever, RetrievalContext
from factory.agents.memory.agent_memory import AgentMemory, MemoryType
from factory.agents.memory.working_memory import WorkingMemory
from factory.agents.memory.episodic_memory import EpisodicMemory
from factory.agents.learning.feedback_system import FeedbackSystem, FeedbackType, FeedbackResult
from factory.agents.learning.learning_engine import LearningEngine
from factory.agents.learning.skill_acquisition import SkillAcquisition
from factory.agents.core.autonomous_agent import AutonomousAgent, TaskContext, AgentCapability
from factory.agents.core.agent_runtime import AgentRuntime, AgentConfig


def test_embeddings():
    """Testa motor de embeddings"""
    print("\n=== Teste: Embeddings ===")

    engine = EmbeddingEngine(backend="semantic", dimensions=256)

    # Testa embedding
    result = engine.embed("Criar API REST para gerenciamento de usuarios")
    print(f"  Modelo: {result.model}")
    print(f"  Dimensoes: {result.dimensions}")
    print(f"  Vetor (primeiros 5): {result.vector[:5]}")

    # Testa similaridade
    r1 = engine.embed("Implementar endpoint de autenticacao")
    r2 = engine.embed("Criar tela de login")
    r3 = engine.embed("Analisar dados de vendas")

    sim_12 = engine.similarity(r1.vector, r2.vector)
    sim_13 = engine.similarity(r1.vector, r3.vector)

    print(f"  Similaridade auth-login: {sim_12:.3f}")
    print(f"  Similaridade auth-vendas: {sim_13:.3f}")
    print(f"  OK: auth-login mais similar que auth-vendas: {sim_12 > sim_13}")


def test_knowledge_base():
    """Testa base de conhecimento"""
    print("\n=== Teste: Knowledge Base ===")

    kb = KnowledgeBase(db_path=Path("factory/database/test_kb.db"))

    # Adiciona conhecimento
    item1 = kb.add(
        content="FastAPI usa decoradores para definir rotas HTTP",
        knowledge_type=KnowledgeType.DOCUMENTATION,
        source="test",
        agent_id="08",
        tags=["fastapi", "python"]
    )
    print(f"  Item criado: {item1.id}")

    item2 = kb.add(
        content="Sempre validar entrada do usuario antes de processar",
        knowledge_type=KnowledgeType.BEST_PRACTICE,
        source="test",
        agent_id="08",
        tags=["security", "validation"]
    )

    # Busca
    results = kb.search("como criar rotas HTTP", limit=5)
    print(f"  Resultados busca: {len(results)}")
    if results:
        print(f"  Melhor resultado: {results[0].item.content[:50]}...")
        print(f"  Similaridade: {results[0].similarity:.3f}")


def test_memory():
    """Testa sistema de memoria"""
    print("\n=== Teste: Agent Memory ===")

    memory = AgentMemory("test_agent")

    # Cria memoria
    mem = memory.remember(
        content="Implementei API de usuarios com sucesso",
        memory_type=MemoryType.EPISODIC,
        context={"task_id": "T001"},
        importance=0.8,
        emotional_valence=0.5
    )
    print(f"  Memoria criada: {mem.id}")

    # Registra decisao
    dec = memory.record_decision(
        context="Implementar autenticacao",
        options=["JWT", "Session", "OAuth"],
        decision="JWT",
        reasoning="Mais adequado para API REST",
        task_id="T002"
    )
    print(f"  Decisao registrada: {dec.id}")

    # Aprende padrao
    pattern = memory.learn_pattern(
        pattern_type="success",
        trigger="implementar api",
        action="usar FastAPI com validacao Pydantic",
        expected_outcome="API funcional",
        confidence=0.7
    )
    print(f"  Padrao aprendido: {pattern.id}")

    # Busca padroes
    patterns = memory.get_applicable_patterns("criar nova api rest")
    print(f"  Padroes aplicaveis: {len(patterns)}")

    # Stats
    stats = memory.get_stats()
    print(f"  Stats: {stats['memories']}")


def test_episodic_memory():
    """Testa memoria episodica"""
    print("\n=== Teste: Episodic Memory ===")

    episodes = EpisodicMemory("test_agent")

    # Registra episodio
    ep = episodes.record(
        title="Implementacao de API Users",
        narrative="Implementei endpoints CRUD para usuarios usando FastAPI e SQLAlchemy",
        context={"task_id": "T001", "project": "test"},
        actions=["Criar modelo User", "Criar router", "Adicionar validacao"],
        outcome="success",
        emotional_impact=0.5,
        lessons=["Pydantic facilita validacao", "SQLAlchemy precisa de sessao"]
    )
    print(f"  Episodio criado: {ep.id}")

    # Busca experiencias similares
    similar = episodes.recall_similar("criar api para clientes", limit=3)
    print(f"  Episodios similares: {len(similar)}")

    # Gera sabedoria
    wisdom = episodes.generate_wisdom()
    print(f"  Licoes: {len(wisdom['licoes_importantes'])}")


def test_feedback():
    """Testa sistema de feedback"""
    print("\n=== Teste: Feedback System ===")

    feedback = FeedbackSystem(db_path=Path("factory/database/test_feedback.db"))

    # Submete feedback
    fb = feedback.submit_feedback(
        task_id="T001",
        agent_id="08",
        feedback_type=FeedbackType.AUTO,
        result=FeedbackResult.SUCCESS,
        score=0.85,
        details="Tarefa concluida com sucesso",
        suggestions=["Adicionar mais testes"]
    )
    print(f"  Feedback criado: {fb.id}")

    # Avalia automaticamente
    fb2 = feedback.auto_evaluate(
        task_id="T002",
        agent_id="08",
        task_result={"files_modified": ["api.py", "models.py"]},
        context={"area": "backend"}
    )
    print(f"  Avaliacao automatica: score={fb2.score:.2f}, result={fb2.result.value}")

    # Performance
    perf = feedback.get_agent_performance("08")
    print(f"  Performance agente 08: {perf}")


def test_learning():
    """Testa motor de aprendizado"""
    print("\n=== Teste: Learning Engine ===")

    learning = LearningEngine("test_agent")

    # Aprende com tarefa
    insights = learning.learn_from_task(
        task_id="T001",
        task_description="Implementar API de autenticacao",
        actions_taken=["Criar modelo User", "Implementar JWT", "Adicionar middleware"],
        result={"success": True},
        success=True
    )
    print(f"  Insights gerados: {len(insights)}")

    # Analisa padroes
    patterns = learning.analyze_patterns()
    print(f"  Taxa de sucesso: {patterns['taxa_sucesso']:.0%}")

    # Recomendacao
    rec = learning.get_recommendation("criar api de pagamentos")
    print(f"  Recomendacao: {rec if rec else 'Nenhuma'}")


def test_skills():
    """Testa sistema de skills"""
    print("\n=== Teste: Skill Acquisition ===")

    skills = SkillAcquisition("test_agent")

    # Adquire skill
    skill = skills.acquire_skill(
        name="FastAPI",
        description="Desenvolvimento de APIs com FastAPI",
        category="technical",
        initial_proficiency=0.5
    )
    print(f"  Skill adquirida: {skill.name} (proficiencia: {skill.proficiency:.0%})")

    # Pratica
    for i in range(5):
        skills.practice_skill("FastAPI", success=True, xp_gain=20)

    skill_updated = skills.get_skill("FastAPI")
    print(f"  Apos pratica: {skill_updated.proficiency:.0%}")

    # Summary
    summary = skills.get_skill_summary()
    print(f"  Total skills: {summary['total_skills']}")
    print(f"  Media proficiencia: {summary['avg_proficiency']:.0%}")


def test_autonomous_agent():
    """Testa agente autonomo"""
    print("\n=== Teste: Autonomous Agent ===")

    agent = AutonomousAgent(
        agent_id="08",
        name="Backend Developer",
        domain="backend",
        description="Desenvolve APIs e logica de negocio"
    )

    print(f"  Agente criado: {agent.name}")
    print(f"  Estado: {agent.state.value}")

    # Status
    status = agent.get_status()
    print(f"  Skills: {status['skills']['total_skills']}")
    print(f"  Domain: {agent.domain}")

    # Simula tarefa
    task = TaskContext(
        task_id="T001",
        description="Criar endpoint para listar usuarios",
        project_id="PRJ-001",
        priority=5
    )

    result = agent.execute_task(task)
    print(f"  Tarefa executada: success={result.success}")
    print(f"  Acoes: {result.actions_taken}")
    print(f"  Duracao: {result.duration_seconds:.2f}s")

    # Consulta
    answer = agent.consult("como implementar autenticacao JWT?")
    print(f"  Consulta: {answer[:100] if answer else 'Sem resposta'}...")


def test_runtime():
    """Testa runtime de agentes"""
    print("\n=== Teste: Agent Runtime ===")

    runtime = AgentRuntime(max_workers=2)

    # Registra agentes
    runtime.register_agent(AgentConfig(
        agent_id="08",
        name="Backend Dev",
        domain="backend",
        description="Desenvolve APIs"
    ))

    runtime.register_agent(AgentConfig(
        agent_id="09",
        name="Frontend Dev",
        domain="frontend",
        description="Desenvolve interfaces"
    ))

    print(f"  Agentes registrados: {len(runtime.list_agents())}")

    # Seleciona agente
    selected = runtime.select_agent("criar api REST")
    print(f"  Agente selecionado para API: {selected}")

    selected2 = runtime.select_agent("criar componente React")
    print(f"  Agente selecionado para React: {selected2}")

    # Stats
    stats = runtime.get_runtime_stats()
    print(f"  Stats: {stats}")

    # Sabedoria coletiva
    wisdom = runtime.get_collective_wisdom()
    print(f"  Sabedoria coletiva: {len(wisdom.get('licoes', []))} licoes")


def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("TESTE DO SISTEMA DE AGENTES AUTONOMOS")
    print("=" * 60)

    tests = [
        ("Embeddings", test_embeddings),
        ("Knowledge Base", test_knowledge_base),
        ("Agent Memory", test_memory),
        ("Episodic Memory", test_episodic_memory),
        ("Feedback System", test_feedback),
        ("Learning Engine", test_learning),
        ("Skill Acquisition", test_skills),
        ("Autonomous Agent", test_autonomous_agent),
        ("Agent Runtime", test_runtime),
    ]

    results = []

    for name, test_func in tests:
        try:
            test_func()
            results.append((name, True, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ERRO: {e}")

    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)

    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed

    for name, ok, error in results:
        status = "PASSOU" if ok else "FALHOU"
        print(f"  {name}: {status}")
        if error:
            print(f"    -> {error[:50]}...")

    print(f"\nTotal: {passed} passaram, {failed} falharam")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
