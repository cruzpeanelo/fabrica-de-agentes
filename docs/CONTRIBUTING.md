# Contribuindo para a Fábrica de Agentes

Obrigado pelo interesse em contribuir!

## Como Contribuir

### Reportando Bugs

1. Verifique se o bug já não foi reportado
2. Abra uma issue com:
   - Descrição clara do problema
   - Passos para reproduzir
   - Comportamento esperado vs atual
   - Logs relevantes

### Sugerindo Funcionalidades

1. Abra uma issue descrevendo:
   - O problema que a funcionalidade resolve
   - Como você imagina a solução
   - Alternativas consideradas

### Pull Requests

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/minha-feature`
3. Faça suas alterações
4. Execute os testes: `python -m factory.agents.test_autonomous_agents`
5. Commit: `git commit -m "feat: adiciona minha feature"`
6. Push: `git push origin feature/minha-feature`
7. Abra um Pull Request

## Padrões de Código

### Python

- Use type hints
- Docstrings em português
- PEP 8 para estilo
- Nomes de variáveis em snake_case

### Commits

Use [Conventional Commits](https://conventionalcommits.org/):

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` documentação
- `refactor:` refatoração
- `test:` testes

## Estrutura de Arquivos

```
factory/agents/
├── core/          # Alterações no core do agente
├── knowledge/     # Base de conhecimento e RAG
├── memory/        # Sistemas de memória
└── learning/      # Motor de aprendizado
```

## Testes

Sempre adicione testes para novas funcionalidades:

```python
def test_nova_funcionalidade():
    """Testa a nova funcionalidade"""
    # Setup
    agent = AutonomousAgent(...)

    # Execute
    result = agent.nova_funcionalidade()

    # Assert
    assert result.success == True
```

## Dúvidas?

Abra uma issue com a tag `question`.
