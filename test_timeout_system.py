"""
Teste do Sistema de Timeout para Aprovacoes Hierarquicas
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from factory.agents.core import (
    AutonomousAgent, HierarchyIntegration, HierarchyConfig,
    WorkHoursConfig, integrate_hierarchy
)

print("=" * 60)
print("TESTE: Sistema de Timeout para Aprovacoes")
print("=" * 60)

# Cria agente de teste
print("\n1. Criando agente de teste...")
agent = AutonomousAgent(
    agent_id='TEST-TIMEOUT',
    name='Test Timeout Agent',
    domain='backend',
    description='Agente para testar timeout'
)

# Configura com timeout de 1 hora
config = HierarchyConfig(
    corporate_id='DEV-SR-BACK',
    approval_timeout_hours=1.0,
    auto_approve_on_timeout=True,
    work_hours=WorkHoursConfig(
        timezone="America/Sao_Paulo",
        start_hour=8,
        end_hour=18,
        work_days=[0, 1, 2, 3, 4]  # Seg-Sex
    )
)

# Integra com hierarquia
hierarchy = integrate_hierarchy(agent, corporate_id='DEV-SR-BACK')
hierarchy.config = config

# Testa horario de trabalho
print("\n2. Verificando horario de trabalho Brasil...")
brazil_time = hierarchy.get_brazil_time()
is_work = hierarchy.is_work_hours()
print(f"   Hora atual (Brasil): {brazil_time.strftime('%d/%m/%Y %H:%M:%S')}")
print(f"   Dia da semana: {brazil_time.strftime('%A')}")
print(f"   Dentro do expediente (08:00-18:00): {'Sim' if is_work else 'Nao'}")

# Testa calculo de timeout
print("\n3. Calculando timeout...")
timeout_at = hierarchy.calculate_timeout()
print(f"   Timeout calculado para: {timeout_at.strftime('%d/%m/%Y %H:%M:%S')}")

# Solicita aprovacao
print("\n4. Solicitando aprovacao para acao...")
decision = hierarchy.request_approval(
    action="modify_database",
    description="Alterar schema da tabela de usuarios",
    estimated_cost=500
)
print(f"   ID da decisao: {decision.decision_id}")
print(f"   Status: {decision.approval_status}")
print(f"   Solicitado em: {decision.requested_at.strftime('%d/%m/%Y %H:%M:%S') if decision.requested_at else 'N/A'}")
print(f"   Expira em: {decision.timeout_at.strftime('%d/%m/%Y %H:%M:%S') if decision.timeout_at else 'N/A'}")
print(f"   Condicoes: {decision.conditions}")

# Verifica se pode prosseguir
print("\n5. Verificando autonomia...")
autonomy = hierarchy.can_proceed_autonomously(decision.decision_id)
print(f"   Pode prosseguir: {autonomy['can_proceed']}")
print(f"   Razao: {autonomy['reason']}")

# Simula passagem de tempo (para teste, criamos uma decisao ja expirada)
print("\n6. Simulando timeout expirado...")
decision.timeout_at = datetime.now() - timedelta(hours=2)  # Ja expirou
autonomy_after = hierarchy.can_proceed_autonomously(decision.decision_id)
print(f"   Pode prosseguir apos timeout: {autonomy_after['can_proceed']}")
print(f"   Razao: {autonomy_after['reason']}")

# Info da hierarquia
print("\n7. Informacoes da hierarquia...")
info = hierarchy.get_hierarchy_info()
if info.get("has_hierarchy"):
    print(f"   Agente: {info.get('name')} - {info.get('title')}")
    print(f"   Budget: ${info.get('budget_authority'):,}")
    superior = info.get("superior")
    if superior:
        print(f"   Superior: {superior.get('name')} ({superior.get('title')})")

print("\n" + "=" * 60)
print("TESTE CONCLUIDO COM SUCESSO!")
print("=" * 60)
print("\nResumo do Sistema:")
print("- Horario de trabalho: 08:00 - 18:00 (America/Sao_Paulo)")
print("- Timeout de aprovacao: 1 hora")
print("- Auto-aprovacao apos timeout: Habilitado")
print("- Dias uteis: Segunda a Sexta")
