"""
Intelligent Skills - Skills Inteligentes com LLM
=================================================

Este modulo fornece skills que usam Claude (LLM) para gerar
codigo de forma inteligente e contextualizada.

Diferente das RealSkills que usam templates, estas skills:
- Analisam o contexto do projeto
- Geram codigo adaptado aos requisitos
- Aprendem com feedback e melhoram ao longo do tempo
- Tomam decisoes sobre arquitetura e implementacao
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from factory.ai.claude_integration import AgentBrain, ClaudeClient, get_claude_client
from factory.skills.real_skills import SkillResult, AgentMemory


@dataclass
class IntelligentSkillResult(SkillResult):
    """Resultado de uma skill inteligente"""
    reasoning: Optional[str] = None  # Raciocinio do agente
    confidence: int = 0  # Confianca na solucao (0-100)
    alternatives: List[str] = field(default_factory=list)  # Alternativas consideradas


class IntelligentSkills:
    """
    Skills inteligentes que usam LLM para gerar codigo

    Cada skill usa Claude para:
    - Entender o contexto
    - Decidir a melhor abordagem
    - Gerar codigo adaptado
    - Aprender com o resultado
    """

    def __init__(self):
        self.claude = get_claude_client()
        self.memories: Dict[str, AgentMemory] = {}
        self.brains: Dict[str, AgentBrain] = {}

    def get_brain(self, agent_id: str, role: str = None, capabilities: List[str] = None) -> AgentBrain:
        """Retorna ou cria o cerebro de um agente"""
        if agent_id not in self.brains:
            self.brains[agent_id] = AgentBrain(
                agent_id=agent_id,
                agent_role=role or self._get_agent_role(agent_id),
                agent_capabilities=capabilities or self._get_agent_capabilities(agent_id)
            )
        return self.brains[agent_id]

    def get_memory(self, agent_id: str) -> AgentMemory:
        """Retorna memoria de um agente"""
        if agent_id not in self.memories:
            self.memories[agent_id] = AgentMemory(agent_id)
        return self.memories[agent_id]

    def _get_agent_role(self, agent_id: str) -> str:
        """Retorna papel do agente"""
        roles = {
            "AGT-005": "Analista de Sistemas",
            "AGT-007": "Especialista em Banco de Dados",
            "AGT-008": "Desenvolvedor Backend Senior",
            "AGT-009": "Desenvolvedor Frontend Senior",
            "AGT-011": "Revisor de Codigo",
            "AGT-013": "Arquiteto de Software",
            "AGT-015": "Engenheiro de QA",
        }
        return roles.get(agent_id, "Desenvolvedor")

    def _get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Retorna capacidades do agente"""
        capabilities = {
            "AGT-005": ["analise de requisitos", "documentacao", "modelagem"],
            "AGT-007": ["SQLAlchemy", "PostgreSQL", "SQLite", "modelagem de dados"],
            "AGT-008": ["FastAPI", "Python", "REST APIs", "autenticacao"],
            "AGT-009": ["Vue.js", "JavaScript", "CSS", "componentes"],
            "AGT-011": ["code review", "seguranca", "boas praticas"],
            "AGT-013": ["arquitetura", "design patterns", "escalabilidade"],
            "AGT-015": ["pytest", "testes unitarios", "testes de integracao"],
        }
        return capabilities.get(agent_id, ["desenvolvimento"])

    def _extract_code_block(self, text: str, language: str = None) -> str:
        """Extrai bloco de codigo de uma resposta"""
        # Tenta extrair codigo entre ```
        pattern = r'```(?:' + (language or r'\w*') + r')?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()

        # Se nao encontrar, retorna texto limpo
        return text.strip()

    def generate_fastapi_router_intelligent(
        self, agent_id: str, project_path: str, entity_name: str,
        entity_description: str, fields: List[Dict], business_rules: List[str] = None
    ) -> IntelligentSkillResult:
        """
        Gera router FastAPI de forma INTELIGENTE usando Claude

        O agente analisa os requisitos e gera codigo adaptado.
        """
        brain = self.get_brain(agent_id)
        memory = self.get_memory(agent_id)

        # Prepara contexto
        context = {
            "entity_name": entity_name,
            "description": entity_description,
            "fields": fields,
            "business_rules": business_rules or [],
            "past_experiences": memory.get_relevant_knowledge("fastapi_router"),
            "project_structure": "FastAPI + SQLAlchemy + Pydantic"
        }

        # Agente pensa sobre a tarefa
        thinking = brain.think(
            f"Preciso criar um router FastAPI completo para a entidade '{entity_name}'. "
            f"Descricao: {entity_description}. "
            f"Campos: {json.dumps(fields, ensure_ascii=False)}. "
            f"Regras de negocio: {business_rules}",
            context
        )

        # Gera codigo com Claude
        specification = f"""
        Crie um router FastAPI COMPLETO para a entidade: {entity_name}

        Descricao: {entity_description}

        Campos da entidade:
        {json.dumps(fields, indent=2, ensure_ascii=False)}

        Regras de negocio:
        {json.dumps(business_rules or [], indent=2, ensure_ascii=False)}

        Requisitos:
        1. Endpoints CRUD completos (GET lista, GET por ID, POST, PUT, DELETE)
        2. Usar Pydantic para validacao (schemas Create, Update, Response)
        3. Usar SQLAlchemy Session via Depends(get_db)
        4. Tratamento de erros com HTTPException
        5. Documentacao com docstrings
        6. O prefix deve ser /api/{entity_name.lower().replace(' ', '_')}
        7. Importar: from database import get_db
        8. Importar model de: from models.{entity_name.lower()} import {entity_name}
        9. Importar schemas de: from schemas.{entity_name.lower()} import *

        Retorne APENAS o codigo Python, sem explicacoes.
        """

        response = brain.generate_code_intelligent(
            task=specification,
            language="python",
            framework="FastAPI",
            context=json.dumps(context, ensure_ascii=False)
        )

        if not response.success:
            return IntelligentSkillResult(
                success=False,
                skill_name="generate_fastapi_router_intelligent",
                agent_id=agent_id,
                errors=[response.error or "Erro ao gerar codigo"]
            )

        # Extrai codigo
        code = self._extract_code_block(response.content, "python")

        # Salva arquivo
        file_name = entity_name.lower().replace(" ", "_")
        file_path = Path(project_path) / "backend" / "routers" / f"{file_name}.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")

        # Registra aprendizado
        result = IntelligentSkillResult(
            success=True,
            skill_name="generate_fastapi_router_intelligent",
            agent_id=agent_id,
            files_created=[str(file_path)],
            reasoning=thinking.content if thinking.success else None,
            confidence=85
        )

        memory.record_skill_execution(result)
        memory.add_knowledge(f"Criado router FastAPI inteligente para {entity_name}")

        # Agente aprende
        brain.learn({
            "success": True,
            "pattern": "fastapi_router",
            "context": entity_name,
            "entity_fields": len(fields)
        })

        return result

    def generate_sqlalchemy_model_intelligent(
        self, agent_id: str, project_path: str, entity_name: str,
        entity_description: str, fields: List[Dict], relationships: List[Dict] = None
    ) -> IntelligentSkillResult:
        """
        Gera modelo SQLAlchemy de forma INTELIGENTE
        """
        brain = self.get_brain(agent_id)
        memory = self.get_memory(agent_id)

        specification = f"""
        Crie um modelo SQLAlchemy COMPLETO para: {entity_name}

        Descricao: {entity_description}

        Campos:
        {json.dumps(fields, indent=2, ensure_ascii=False)}

        Relacionamentos:
        {json.dumps(relationships or [], indent=2, ensure_ascii=False)}

        Requisitos:
        1. Herdar de Base (from database import Base)
        2. Incluir campos id, created_at, updated_at automaticos
        3. Usar tipos corretos do SQLAlchemy (Integer, String, Float, DateTime, Text, Boolean)
        4. Definir __tablename__ como {entity_name.lower().replace(' ', '_')}
        5. Incluir metodo to_dict() para serializacao
        6. Documentar com docstrings

        Retorne APENAS o codigo Python.
        """

        response = brain.generate_code_intelligent(
            task=specification,
            language="python",
            framework="SQLAlchemy"
        )

        if not response.success:
            return IntelligentSkillResult(
                success=False,
                skill_name="generate_sqlalchemy_model_intelligent",
                agent_id=agent_id,
                errors=[response.error or "Erro ao gerar modelo"]
            )

        code = self._extract_code_block(response.content, "python")

        file_name = entity_name.lower().replace(" ", "_")
        file_path = Path(project_path) / "backend" / "models" / f"{file_name}.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")

        result = IntelligentSkillResult(
            success=True,
            skill_name="generate_sqlalchemy_model_intelligent",
            agent_id=agent_id,
            files_created=[str(file_path)],
            confidence=90
        )

        memory.record_skill_execution(result)
        memory.add_knowledge(f"Criado modelo SQLAlchemy inteligente para {entity_name}")

        return result

    def generate_pydantic_schemas_intelligent(
        self, agent_id: str, project_path: str, entity_name: str,
        fields: List[Dict]
    ) -> IntelligentSkillResult:
        """
        Gera schemas Pydantic de forma INTELIGENTE
        """
        brain = self.get_brain(agent_id)
        memory = self.get_memory(agent_id)

        specification = f"""
        Crie schemas Pydantic COMPLETOS para: {entity_name}

        Campos:
        {json.dumps(fields, indent=2, ensure_ascii=False)}

        Crie 3 schemas:
        1. {entity_name}Base - campos comuns
        2. {entity_name}Create - para criacao (herda de Base)
        3. {entity_name}Update - para atualizacao (campos opcionais)
        4. {entity_name}Response - para resposta (com id, created_at, updated_at)

        Use Config com from_attributes = True para compatibilidade com ORM.
        Retorne APENAS o codigo Python.
        """

        response = brain.generate_code_intelligent(
            task=specification,
            language="python",
            framework="Pydantic"
        )

        if not response.success:
            return IntelligentSkillResult(
                success=False,
                skill_name="generate_pydantic_schemas_intelligent",
                agent_id=agent_id,
                errors=[response.error or "Erro ao gerar schemas"]
            )

        code = self._extract_code_block(response.content, "python")

        file_name = entity_name.lower().replace(" ", "_")
        file_path = Path(project_path) / "backend" / "schemas" / f"{file_name}.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")

        result = IntelligentSkillResult(
            success=True,
            skill_name="generate_pydantic_schemas_intelligent",
            agent_id=agent_id,
            files_created=[str(file_path)],
            confidence=85
        )

        memory.record_skill_execution(result)

        return result

    def generate_vue_component_intelligent(
        self, agent_id: str, project_path: str, component_name: str,
        description: str, fields: List[Dict], api_endpoint: str
    ) -> IntelligentSkillResult:
        """
        Gera componente Vue.js de forma INTELIGENTE
        """
        brain = self.get_brain(agent_id)
        memory = self.get_memory(agent_id)

        specification = f"""
        Crie um componente Vue.js 3 COMPLETO para: {component_name}

        Descricao: {description}

        Campos do formulario:
        {json.dumps(fields, indent=2, ensure_ascii=False)}

        API Endpoint: {api_endpoint}

        Requisitos:
        1. Usar Composition API com <script setup>
        2. Incluir listagem com tabela/cards
        3. Modal para criacao/edicao
        4. Confirmacao para exclusao
        5. Usar fetch para chamadas a API
        6. Estados de loading e erro
        7. Estilos scoped
        8. Design responsivo

        Retorne APENAS o codigo Vue (template, script, style).
        """

        response = brain.generate_code_intelligent(
            task=specification,
            language="vue",
            framework="Vue.js 3"
        )

        if not response.success:
            return IntelligentSkillResult(
                success=False,
                skill_name="generate_vue_component_intelligent",
                agent_id=agent_id,
                errors=[response.error or "Erro ao gerar componente"]
            )

        code = response.content
        # Limpa codigo se vier com markdown
        if "```vue" in code:
            code = self._extract_code_block(code, "vue")
        elif "```" in code:
            code = self._extract_code_block(code)

        file_name = component_name.replace(" ", "")
        file_path = Path(project_path) / "frontend" / "src" / "components" / f"{file_name}.vue"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")

        result = IntelligentSkillResult(
            success=True,
            skill_name="generate_vue_component_intelligent",
            agent_id=agent_id,
            files_created=[str(file_path)],
            confidence=80
        )

        memory.record_skill_execution(result)
        memory.add_knowledge(f"Criado componente Vue inteligente para {component_name}")

        return result

    def generate_tests_intelligent(
        self, agent_id: str, project_path: str, entity_name: str,
        api_endpoint: str, test_scenarios: List[str] = None
    ) -> IntelligentSkillResult:
        """
        Gera testes automatizados de forma INTELIGENTE
        """
        brain = self.get_brain(agent_id)
        memory = self.get_memory(agent_id)

        specification = f"""
        Crie testes pytest COMPLETOS para: {entity_name}

        API Endpoint: {api_endpoint}

        Cenarios a testar:
        {json.dumps(test_scenarios or ['CRUD completo', 'validacoes', 'erros'], indent=2)}

        Requisitos:
        1. Usar pytest e pytest-asyncio se necessario
        2. Usar TestClient do FastAPI
        3. Fixtures para setup/teardown
        4. Testar todos os endpoints CRUD
        5. Testar casos de erro (404, 422, etc)
        6. Testar validacoes de campos
        7. Documentar cada teste com docstring

        Retorne APENAS o codigo Python de testes.
        """

        response = brain.generate_code_intelligent(
            task=specification,
            language="python",
            framework="pytest"
        )

        if not response.success:
            return IntelligentSkillResult(
                success=False,
                skill_name="generate_tests_intelligent",
                agent_id=agent_id,
                errors=[response.error or "Erro ao gerar testes"]
            )

        code = self._extract_code_block(response.content, "python")

        file_name = entity_name.lower().replace(" ", "_")
        file_path = Path(project_path) / "backend" / "tests" / f"test_{file_name}.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")

        result = IntelligentSkillResult(
            success=True,
            skill_name="generate_tests_intelligent",
            agent_id=agent_id,
            files_created=[str(file_path)],
            confidence=75
        )

        memory.record_skill_execution(result)

        return result

    def analyze_requirements_intelligent(
        self, agent_id: str, requirements_text: str, project_context: str = ""
    ) -> IntelligentSkillResult:
        """
        Analisa requisitos de forma INTELIGENTE

        Retorna estrutura com entidades, relacionamentos e regras de negocio
        """
        brain = self.get_brain(agent_id)

        response = self.claude.analyze_requirements(requirements_text, project_context)

        if not response.success:
            return IntelligentSkillResult(
                success=False,
                skill_name="analyze_requirements_intelligent",
                agent_id=agent_id,
                errors=[response.error or "Erro ao analisar requisitos"]
            )

        # Tenta parsear JSON
        try:
            analysis = json.loads(response.content)
        except json.JSONDecodeError:
            analysis = {"raw_analysis": response.content}

        result = IntelligentSkillResult(
            success=True,
            skill_name="analyze_requirements_intelligent",
            agent_id=agent_id,
            outputs=analysis,
            reasoning=f"Analisados {len(requirements_text)} caracteres de requisitos",
            confidence=85
        )

        return result

    def create_user_story_intelligent(
        self, agent_id: str, requirement: str, project_context: str = ""
    ) -> IntelligentSkillResult:
        """
        Cria user story de forma INTELIGENTE
        """
        response = self.claude.create_user_story(requirement, project_context)

        if not response.success:
            return IntelligentSkillResult(
                success=False,
                skill_name="create_user_story_intelligent",
                agent_id=agent_id,
                errors=[response.error or "Erro ao criar story"]
            )

        # Tenta parsear JSON
        try:
            story = json.loads(response.content)
        except json.JSONDecodeError:
            story = {"titulo": requirement, "raw": response.content}

        result = IntelligentSkillResult(
            success=True,
            skill_name="create_user_story_intelligent",
            agent_id=agent_id,
            outputs=story,
            confidence=90
        )

        return result

    def review_code_intelligent(
        self, agent_id: str, code: str, language: str = "python"
    ) -> IntelligentSkillResult:
        """
        Revisa codigo de forma INTELIGENTE
        """
        brain = self.get_brain(agent_id)

        response = self.claude.review_code(code, language)

        if not response.success:
            return IntelligentSkillResult(
                success=False,
                skill_name="review_code_intelligent",
                agent_id=agent_id,
                errors=[response.error or "Erro ao revisar codigo"]
            )

        # Tenta parsear JSON
        try:
            review = json.loads(response.content)
        except json.JSONDecodeError:
            review = {"raw_review": response.content}

        result = IntelligentSkillResult(
            success=True,
            skill_name="review_code_intelligent",
            agent_id=agent_id,
            outputs=review,
            confidence=review.get("qualidade_geral", 5) * 10 if isinstance(review, dict) else 50
        )

        return result

    def decide_architecture_intelligent(
        self, agent_id: str, project_requirements: str, constraints: List[str] = None
    ) -> IntelligentSkillResult:
        """
        Decide arquitetura do projeto de forma INTELIGENTE
        """
        brain = self.get_brain(agent_id)

        situation = f"""
        Preciso definir a arquitetura para um projeto com os seguintes requisitos:

        {project_requirements}

        Restricoes: {constraints or ['Nenhuma especifica']}

        Considere:
        - Escalabilidade
        - Manutenibilidade
        - Performance
        - Seguranca
        - Complexidade de implementacao
        """

        response = brain.think(situation, {
            "role": "Arquiteto de Software",
            "decision_type": "architecture"
        })

        if not response.success:
            return IntelligentSkillResult(
                success=False,
                skill_name="decide_architecture_intelligent",
                agent_id=agent_id,
                errors=[response.error or "Erro ao decidir arquitetura"]
            )

        result = IntelligentSkillResult(
            success=True,
            skill_name="decide_architecture_intelligent",
            agent_id=agent_id,
            outputs={"architecture_decision": response.content},
            reasoning=response.content,
            confidence=80
        )

        return result


# Instancia global
_intelligent_skills: Optional[IntelligentSkills] = None


def get_intelligent_skills() -> IntelligentSkills:
    """Retorna instancia global das skills inteligentes"""
    global _intelligent_skills
    if _intelligent_skills is None:
        _intelligent_skills = IntelligentSkills()
    return _intelligent_skills
