"""
Input Processor - Processador de Arquivos de Entrada
Responsavel por ler arquivos de reunioes (transcricoes, documentos) e extrair requisitos

Workflow:
1. Le arquivos de entrada (DOCX, TXT, PDF)
2. Extrai conteudo textual
3. Identifica processos, requisitos e regras de negocio
4. Envia para o RequirementsExtractor
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

# Conditional imports
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from factory.database.connection import SessionLocal
from factory.database.models import Project, Story, ActivityLog


@dataclass
class TranscriptionSegment:
    """Segmento de uma transcricao"""
    speaker: str
    timestamp: str
    text: str
    topics: List[str] = field(default_factory=list)


@dataclass
class ExtractedProcess:
    """Processo extraido de uma transcricao"""
    name: str
    type: str  # AS-IS, TO-BE, NOVO
    description: str
    participants: List[str]
    steps: List[str]
    pain_points: List[str]
    improvements: List[str]
    systems_involved: List[str]
    business_rules: List[str]


@dataclass
class ExtractedRequirement:
    """Requisito extraido"""
    title: str
    description: str
    type: str  # funcional, nao-funcional, regra-negocio
    priority: str  # alta, media, baixa
    source: str  # referencia na transcricao
    related_process: str
    stakeholders: List[str]
    acceptance_criteria: List[str]
    technical_notes: List[str]


class InputProcessor:
    """
    Processador de arquivos de entrada
    Le transcricoes e documentos para extrair requisitos
    """

    # Palavras-chave para identificar processos
    PROCESS_KEYWORDS = [
        'processo', 'workflow', 'fluxo', 'etapa', 'passo',
        'cadastro', 'aprovacao', 'validacao', 'integracao',
        'as-is', 'to-be', 'atual', 'futuro', 'melhoria'
    ]

    # Palavras-chave para identificar problemas/dores
    PAIN_KEYWORDS = [
        'problema', 'dificuldade', 'manual', 'demora', 'erro',
        'retrabalho', 'gargalo', 'falta', 'nao tem', 'precisa'
    ]

    # Palavras-chave para requisitos
    REQUIREMENT_KEYWORDS = [
        'precisa', 'deve', 'tem que', 'necessario', 'obrigatorio',
        'importante', 'essencial', 'critico', 'fundamental'
    ]

    # Sistemas mencionados frequentemente
    KNOWN_SYSTEMS = [
        'SAP', 'S4HANA', 'CRM', 'ERP', 'Portal', 'Excel',
        'Email', 'Teams', 'SharePoint', 'Power BI', 'TOTVS'
    ]

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.segments: List[TranscriptionSegment] = []
        self.processes: List[ExtractedProcess] = []
        self.requirements: List[ExtractedRequirement] = []

    def process_folder(self, folder_path: str) -> Dict:
        """Processa todos os arquivos de uma pasta"""
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": f"Pasta nao encontrada: {folder_path}"}

        results = {
            "files_processed": [],
            "transcriptions": [],
            "processes": [],
            "requirements": [],
            "errors": []
        }

        # Processa arquivos DOCX
        for docx_file in folder.rglob("*.docx"):
            try:
                content = self.read_docx(str(docx_file))
                if content:
                    results["files_processed"].append(str(docx_file))
                    results["transcriptions"].append({
                        "file": docx_file.name,
                        "segments": len(self.segments)
                    })
            except Exception as e:
                results["errors"].append(f"{docx_file.name}: {str(e)}")

        # Processa arquivos TXT
        for txt_file in folder.rglob("*.txt"):
            if "Error" not in txt_file.name:
                try:
                    content = self.read_txt(str(txt_file))
                    if content:
                        results["files_processed"].append(str(txt_file))
                except Exception as e:
                    results["errors"].append(f"{txt_file.name}: {str(e)}")

        # Extrai processos e requisitos
        self.extract_processes()
        self.extract_requirements()

        results["processes"] = [p.__dict__ for p in self.processes]
        results["requirements"] = [r.__dict__ for r in self.requirements]

        return results

    def read_docx(self, file_path: str) -> str:
        """Le arquivo DOCX e extrai texto"""
        if not HAS_DOCX:
            raise ImportError("python-docx nao instalado. Execute: pip install python-docx")

        doc = Document(file_path)
        full_text = []
        current_speaker = ""
        current_timestamp = ""

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Detecta padrao de speaker (Nome, Sobrenome)
            speaker_match = re.match(r'^([A-Za-z]+,\s+[A-Za-z\s]+)$', text)
            if speaker_match:
                current_speaker = speaker_match.group(1)
                continue

            # Detecta timestamp
            time_match = re.match(r'^(\d+\s+(minutes?|hours?)\s+\d+\s+seconds?).*', text)
            if time_match:
                current_timestamp = time_match.group(1)
                continue

            # Texto normal - adiciona como segmento
            if text and not text.startswith(current_speaker):
                segment = TranscriptionSegment(
                    speaker=current_speaker,
                    timestamp=current_timestamp,
                    text=text
                )
                self.segments.append(segment)
                full_text.append(text)

        return "\n".join(full_text)

    def read_txt(self, file_path: str) -> str:
        """Le arquivo TXT"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Adiciona como um unico segmento
        self.segments.append(TranscriptionSegment(
            speaker="Documento",
            timestamp="",
            text=content
        ))

        return content

    def extract_processes(self):
        """Extrai processos mencionados na transcricao"""
        full_text = " ".join([s.text for s in self.segments]).lower()

        # Identifica processos mencionados
        process_patterns = [
            (r'cadastro\s+de\s+(\w+)', 'Cadastro de {}'),
            (r'processo\s+de\s+(\w+)', 'Processo de {}'),
            (r'fluxo\s+de\s+(\w+)', 'Fluxo de {}'),
            (r'workflow\s+(\w+)', 'Workflow {}'),
            (r'(\w+)\s+as-is', '{} AS-IS'),
            (r'(\w+)\s+to-be', '{} TO-BE'),
            (r'ordem\s+de\s+(\w+)', 'Ordem de {}'),
            (r'documentos?\s+fiscais?', 'Documentos Fiscais'),
            (r'restricao\s+logistica', 'Restricao Logistica'),
            (r'pricing|precificacao', 'Pricing'),
            (r'cotacao|cotacoes', 'Cotacao'),
            (r'aprovacao\s+de\s+(\w+)', 'Aprovacao de {}'),
        ]

        found_processes = set()

        for pattern, template in process_patterns:
            matches = re.findall(pattern, full_text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                process_name = template.format(match.title()) if '{}' in template else template
                found_processes.add(process_name)

        # Cria objetos de processo
        for proc_name in found_processes:
            # Determina tipo
            proc_type = "NOVO"
            if "as-is" in proc_name.lower():
                proc_type = "AS-IS"
            elif "to-be" in proc_name.lower():
                proc_type = "TO-BE"

            # Identifica participantes
            participants = self._extract_participants()

            # Identifica sistemas
            systems = self._extract_systems(full_text)

            # Identifica problemas
            pain_points = self._extract_pain_points(full_text, proc_name.lower())

            process = ExtractedProcess(
                name=proc_name,
                type=proc_type,
                description=f"Processo de {proc_name} identificado na transcricao",
                participants=participants,
                steps=[],
                pain_points=pain_points,
                improvements=[],
                systems_involved=systems,
                business_rules=[]
            )
            self.processes.append(process)

    def extract_requirements(self):
        """Extrai requisitos das transcricoes"""
        full_text = " ".join([s.text for s in self.segments])

        # Padroes para identificar requisitos
        requirement_patterns = [
            (r'precisa\s+(?:de\s+)?(.+?)(?:\.|,|$)', 'funcional'),
            (r'deve\s+(?:ter|ser|fazer)\s+(.+?)(?:\.|,|$)', 'funcional'),
            (r'tem\s+que\s+(.+?)(?:\.|,|$)', 'funcional'),
            (r'necessario\s+(.+?)(?:\.|,|$)', 'funcional'),
            (r'importante\s+(?:que\s+)?(.+?)(?:\.|,|$)', 'funcional'),
            (r'regra\s+(?:de\s+)?(.+?)(?:\.|,|$)', 'regra-negocio'),
            (r'validar\s+(.+?)(?:\.|,|$)', 'regra-negocio'),
            (r'nao\s+pode\s+(.+?)(?:\.|,|$)', 'regra-negocio'),
        ]

        found_requirements = []

        for pattern, req_type in requirement_patterns:
            matches = re.findall(pattern, full_text.lower())
            for match in matches:
                if len(match) > 10 and len(match) < 200:  # Filtro de tamanho
                    found_requirements.append((match.strip(), req_type))

        # Cria objetos de requisito
        for i, (req_text, req_type) in enumerate(found_requirements[:20]):  # Limita a 20
            requirement = ExtractedRequirement(
                title=f"REQ-{i+1:03d}: {req_text[:50]}...",
                description=req_text,
                type=req_type,
                priority="media",
                source="Transcricao de reuniao",
                related_process=self.processes[0].name if self.processes else "",
                stakeholders=self._extract_participants()[:3],
                acceptance_criteria=[],
                technical_notes=[]
            )
            self.requirements.append(requirement)

    def _extract_participants(self) -> List[str]:
        """Extrai participantes unicos da transcricao"""
        speakers = set()
        for segment in self.segments:
            if segment.speaker and segment.speaker != "Documento":
                speakers.add(segment.speaker)
        return list(speakers)

    def _extract_systems(self, text: str) -> List[str]:
        """Extrai sistemas mencionados"""
        systems = []
        for system in self.KNOWN_SYSTEMS:
            if system.lower() in text.lower():
                systems.append(system)
        return systems

    def _extract_pain_points(self, text: str, process_name: str) -> List[str]:
        """Extrai problemas/dores relacionados a um processo"""
        pain_points = []

        for keyword in self.PAIN_KEYWORDS:
            pattern = rf'{keyword}\s+(.{{10,100}}?)(?:\.|,|$)'
            matches = re.findall(pattern, text)
            for match in matches:
                if process_name in match.lower() or len(pain_points) < 3:
                    pain_points.append(match.strip())

        return pain_points[:5]  # Limita a 5


class StoryGenerator:
    """
    Gerador de User Stories com estrutura padrao de mercado
    Cria stories completas a partir de processos e requisitos extraidos
    """

    # Mapeamento de categoria para agentes
    CATEGORY_AGENTS = {
        'cadastro': ['AGT-008', 'AGT-007'],  # Backend, BD
        'integracao': ['AGT-019', 'AGT-008'],  # Integrador, Backend
        'workflow': ['AGT-008', 'AGT-009'],  # Backend, Frontend
        'relatorio': ['AGT-006', 'AGT-009'],  # Dados, Frontend
        'validacao': ['AGT-010', 'AGT-008'],  # Seguranca, Backend
        'pricing': ['AGT-008', 'AGT-006'],  # Backend, Dados
        'documento': ['AGT-008', 'AGT-007'],  # Backend, BD
        'logistica': ['AGT-008', 'AGT-019'],  # Backend, Integrador
    }

    # Template de Definition of Done
    DEFAULT_DOD = [
        "Codigo implementado seguindo padroes do projeto",
        "Testes unitarios com cobertura minima de 80%",
        "Testes de integracao para fluxos criticos",
        "Code review aprovado por pelo menos 1 revisor",
        "Documentacao tecnica atualizada",
        "Sem vulnerabilidades de seguranca (OWASP Top 10)",
        "Performance dentro dos limites aceitaveis"
    ]

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.db = SessionLocal()

    def generate_stories_from_processes(
        self,
        processes: List[ExtractedProcess],
        requirements: List[ExtractedRequirement]
    ) -> List[Story]:
        """Gera stories a partir de processos e requisitos extraidos"""
        stories = []
        story_counter = 1

        for process in processes:
            # Gera story principal do processo
            main_story = self._create_process_story(process, story_counter)
            stories.append(main_story)
            story_counter += 1

            # Gera sub-stories para cada dor/problema identificado
            for pain in process.pain_points[:3]:
                pain_story = self._create_pain_point_story(process, pain, story_counter)
                stories.append(pain_story)
                story_counter += 1

        # Gera stories para requisitos que nao estao cobertos
        for req in requirements[:10]:
            req_story = self._create_requirement_story(req, story_counter)
            stories.append(req_story)
            story_counter += 1

        return stories

    def _create_process_story(self, process: ExtractedProcess, counter: int) -> Story:
        """Cria story para um processo"""

        # Determina categoria baseada no nome do processo
        category = self._determine_category(process.name)
        agents = self.CATEGORY_AGENTS.get(category, ['AGT-014', 'AGT-008'])

        # Determina complexidade
        complexity = 'high' if len(process.systems_involved) > 2 else 'medium'
        estimated_hours = 40 if complexity == 'high' else 24

        # Calcula pontos (fibonacci)
        points = 13 if complexity == 'high' else 8

        # Gera acceptance criteria
        acceptance_criteria = self._generate_acceptance_criteria(process)

        # Gera regras de negocio
        business_rules = self._generate_business_rules(process)

        # Gera notas tecnicas
        technical_notes = self._generate_technical_notes(process)

        # Gera tasks
        tasks = self._generate_tasks(process)

        story = Story(
            story_id=f"US-BPM-{counter:03d}",
            project_id=self.project_id,
            title=f"Implementar {process.name}",
            description=self._generate_description(process),
            status="BACKLOG",
            sprint=self._determine_sprint(process),
            points=points,
            priority=1 if process.type == "TO-BE" else 2,
            epic_id=f"EPIC-{category.upper()[:3]}",
            category=category,
            narrative_persona=self._determine_persona(process),
            narrative_action=f"utilizar o {process.name} de forma automatizada",
            narrative_benefit=self._determine_benefit(process),
            acceptance_criteria=json.dumps(acceptance_criteria),
            business_rules=json.dumps(business_rules),
            definition_of_done=json.dumps(self.DEFAULT_DOD),
            technical_notes=json.dumps(technical_notes),
            dependencies=json.dumps([]),
            agents=json.dumps(agents),
            assigned_to=agents[0] if agents else "AGT-014",
            reviewer="AGT-011",
            qa_agent="AGT-015",
            estimated_hours=estimated_hours,
            complexity=complexity,
            risk_level='medium' if process.systems_involved else 'low',
            tags=json.dumps([category, process.type.lower()]),
            source="transcription_extraction",
            created_by="AGT-002"
        )

        return story

    def _create_pain_point_story(self, process: ExtractedProcess, pain: str, counter: int) -> Story:
        """Cria story para resolver um problema identificado"""

        category = self._determine_category(process.name)
        agents = self.CATEGORY_AGENTS.get(category, ['AGT-014', 'AGT-008'])

        story = Story(
            story_id=f"US-BPM-{counter:03d}",
            project_id=self.project_id,
            title=f"Resolver: {pain[:60]}",
            description=f"Problema identificado no processo {process.name}:\n\n{pain}\n\nEsta story visa resolver este problema atraves de automacao e melhorias no sistema.",
            status="BACKLOG",
            sprint=self._determine_sprint(process),
            points=5,
            priority=1,  # Pain points tem alta prioridade
            epic_id=f"EPIC-{category.upper()[:3]}",
            category=category,
            narrative_persona=self._determine_persona(process),
            narrative_action=f"nao ter mais o problema de {pain[:30]}",
            narrative_benefit="aumentar produtividade e reduzir erros",
            acceptance_criteria=json.dumps([
                f"Problema '{pain[:50]}' resolvido",
                "Usuarios confirmam que nao ocorre mais",
                "Metricas mostram melhoria"
            ]),
            business_rules=json.dumps([]),
            definition_of_done=json.dumps(self.DEFAULT_DOD),
            technical_notes=json.dumps([f"Relacionado ao processo: {process.name}"]),
            agents=json.dumps(agents),
            assigned_to=agents[0] if agents else "AGT-014",
            reviewer="AGT-011",
            qa_agent="AGT-015",
            estimated_hours=16,
            complexity='medium',
            risk_level='low',
            tags=json.dumps([category, 'pain-point', 'melhoria']),
            source="transcription_extraction",
            created_by="AGT-002"
        )

        return story

    def _create_requirement_story(self, req: ExtractedRequirement, counter: int) -> Story:
        """Cria story para um requisito"""

        category = 'backend'  # Default
        agents = ['AGT-008', 'AGT-014']

        story = Story(
            story_id=f"US-BPM-{counter:03d}",
            project_id=self.project_id,
            title=req.title,
            description=req.description,
            status="BACKLOG",
            sprint=1,
            points=5,
            priority=2 if req.priority == 'alta' else 3,
            category=category,
            narrative_persona="usuario do sistema",
            narrative_action=req.description[:50],
            narrative_benefit="atender requisito de negocio",
            acceptance_criteria=json.dumps(req.acceptance_criteria or [
                "Requisito implementado conforme especificado",
                "Testes validando o comportamento"
            ]),
            business_rules=json.dumps([]),
            definition_of_done=json.dumps(self.DEFAULT_DOD),
            technical_notes=json.dumps(req.technical_notes or []),
            agents=json.dumps(agents),
            assigned_to=agents[0],
            reviewer="AGT-011",
            qa_agent="AGT-015",
            estimated_hours=8,
            complexity='low',
            source="transcription_extraction",
            created_by="AGT-002"
        )

        return story

    def _determine_category(self, name: str) -> str:
        """Determina categoria baseada no nome"""
        name_lower = name.lower()

        if 'cadastro' in name_lower:
            return 'cadastro'
        elif 'integracao' in name_lower or 'sap' in name_lower:
            return 'integracao'
        elif 'workflow' in name_lower or 'fluxo' in name_lower or 'aprovacao' in name_lower:
            return 'workflow'
        elif 'relatorio' in name_lower or 'dashboard' in name_lower:
            return 'relatorio'
        elif 'validacao' in name_lower:
            return 'validacao'
        elif 'pricing' in name_lower or 'preco' in name_lower:
            return 'pricing'
        elif 'documento' in name_lower or 'fiscal' in name_lower:
            return 'documento'
        elif 'logistica' in name_lower or 'restricao' in name_lower:
            return 'logistica'

        return 'backend'

    def _determine_sprint(self, process: ExtractedProcess) -> int:
        """Determina sprint baseado no tipo de processo"""
        if process.type == "AS-IS":
            return 1  # Documentacao primeiro
        elif process.type == "TO-BE":
            return 2  # Melhorias depois
        return 3  # Novos processos por ultimo

    def _determine_persona(self, process: ExtractedProcess) -> str:
        """Determina persona baseada no processo"""
        name_lower = process.name.lower()

        if 'vendas' in name_lower or 'cotacao' in name_lower:
            return "vendedor"
        elif 'logistica' in name_lower:
            return "analista de logistica"
        elif 'fiscal' in name_lower or 'documento' in name_lower:
            return "analista fiscal"
        elif 'cadastro' in name_lower and 'cliente' in name_lower:
            return "atendente comercial"
        elif 'pricing' in name_lower:
            return "analista de pricing"

        return "usuario do sistema"

    def _determine_benefit(self, process: ExtractedProcess) -> str:
        """Determina beneficio baseado no processo"""
        if process.pain_points:
            return f"eliminar problemas como: {process.pain_points[0][:50]}"

        return "aumentar produtividade e reduzir erros manuais"

    def _generate_description(self, process: ExtractedProcess) -> str:
        """Gera descricao detalhada"""
        desc = f"## {process.name}\n\n"
        desc += f"**Tipo:** {process.type}\n\n"
        desc += f"### Descricao\n{process.description}\n\n"

        if process.participants:
            desc += f"### Participantes\n"
            for p in process.participants[:5]:
                desc += f"- {p}\n"
            desc += "\n"

        if process.systems_involved:
            desc += f"### Sistemas Envolvidos\n"
            for s in process.systems_involved:
                desc += f"- {s}\n"
            desc += "\n"

        if process.pain_points:
            desc += f"### Problemas Identificados\n"
            for pain in process.pain_points:
                desc += f"- {pain}\n"
            desc += "\n"

        return desc

    def _generate_acceptance_criteria(self, process: ExtractedProcess) -> List[str]:
        """Gera criterios de aceite"""
        criteria = [
            f"Processo {process.name} implementado e funcionando",
            "Interface de usuario intuitiva e responsiva",
            "Validacoes de entrada implementadas",
            "Tratamento de erros adequado",
            "Logs de auditoria registrados"
        ]

        if process.systems_involved:
            criteria.append(f"Integracao com {', '.join(process.systems_involved)} funcionando")

        return criteria

    def _generate_business_rules(self, process: ExtractedProcess) -> List[str]:
        """Gera regras de negocio"""
        rules = process.business_rules.copy() if process.business_rules else []

        # Adiciona regras padrao baseadas no tipo
        if 'cadastro' in process.name.lower():
            rules.extend([
                "Campos obrigatorios devem ser validados",
                "CNPJ/CPF deve ser validado na Receita Federal",
                "Duplicidade de cadastro deve ser bloqueada"
            ])
        elif 'aprovacao' in process.name.lower():
            rules.extend([
                "Alcada de aprovacao deve ser respeitada",
                "Historico de aprovacoes deve ser mantido",
                "Notificacao para aprovadores pendentes"
            ])

        return rules[:5]

    def _generate_technical_notes(self, process: ExtractedProcess) -> List[str]:
        """Gera notas tecnicas"""
        notes = []

        if process.systems_involved:
            for system in process.systems_involved:
                notes.append(f"Verificar API disponivel para integracao com {system}")

        notes.extend([
            "Utilizar arquitetura de microservicos",
            "Implementar cache para melhorar performance",
            "Considerar filas para processamento assincrono"
        ])

        return notes[:5]

    def _generate_tasks(self, process: ExtractedProcess) -> List[Dict]:
        """Gera lista de tasks para a story"""
        tasks = [
            {"title": "Analise e refinamento de requisitos", "agent": "AGT-005", "hours": 4},
            {"title": "Design da solucao tecnica", "agent": "AGT-013", "hours": 4},
            {"title": "Implementacao do backend", "agent": "AGT-008", "hours": 16},
            {"title": "Implementacao do frontend", "agent": "AGT-009", "hours": 8},
            {"title": "Testes unitarios", "agent": "AGT-015", "hours": 4},
            {"title": "Testes de integracao", "agent": "AGT-016", "hours": 4},
            {"title": "Code review", "agent": "AGT-011", "hours": 2},
            {"title": "Documentacao", "agent": "AGT-017", "hours": 2}
        ]

        if process.systems_involved:
            tasks.insert(3, {
                "title": f"Integracao com {', '.join(process.systems_involved)}",
                "agent": "AGT-019",
                "hours": 8
            })

        return tasks

    def save_stories(self, stories: List[Story]) -> int:
        """Salva stories no banco de dados"""
        count = 0
        for story in stories:
            try:
                self.db.add(story)
                self.db.commit()
                count += 1
                print(f"[StoryGenerator] Criada: {story.story_id} - {story.title}")
            except Exception as e:
                self.db.rollback()
                print(f"[StoryGenerator] Erro ao criar story: {e}")

        return count

    def close(self):
        """Fecha conexao com banco"""
        self.db.close()


class AgentValidationFlow:
    """
    Fluxo de validacao entre agentes
    Garante que stories passem por revisao antes de ir para desenvolvimento
    """

    VALIDATION_STAGES = [
        {"stage": "pm_review", "agent": "AGT-002", "role": "Product Manager"},
        {"stage": "po_review", "agent": "AGT-003", "role": "Product Owner"},
        {"stage": "tech_review", "agent": "AGT-013", "role": "Arquiteto"},
        {"stage": "ready_for_dev", "agent": "AGT-014", "role": "Tech Lead"}
    ]

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.db = SessionLocal()

    def submit_for_validation(self, story: Story) -> Dict:
        """Submete story para fluxo de validacao"""

        # Registra log de inicio
        self._log_activity(
            story_id=story.story_id,
            agent_id="AGT-002",
            action="validation_started",
            message=f"Story {story.story_id} submetida para validacao"
        )

        # Simula validacao de cada estagio
        for stage in self.VALIDATION_STAGES:
            result = self._validate_stage(story, stage)
            if not result["approved"]:
                return {
                    "success": False,
                    "stage": stage["stage"],
                    "reason": result["reason"]
                }

        # Story aprovada - move para TO_DO
        story.status = "TO_DO"
        self.db.commit()

        self._log_activity(
            story_id=story.story_id,
            agent_id="AGT-014",
            action="validation_completed",
            message=f"Story {story.story_id} aprovada e movida para TO_DO"
        )

        return {"success": True, "status": "TO_DO"}

    def _validate_stage(self, story: Story, stage: Dict) -> Dict:
        """Valida um estagio especifico"""

        # Verifica campos obrigatorios
        if stage["stage"] == "pm_review":
            if not story.acceptance_criteria or story.acceptance_criteria == "[]":
                return {"approved": False, "reason": "Faltam criterios de aceite"}
            if not story.narrative_persona:
                return {"approved": False, "reason": "Falta persona (Como...)"}

        elif stage["stage"] == "po_review":
            if not story.business_rules or story.business_rules == "[]":
                return {"approved": False, "reason": "Faltam regras de negocio"}
            if story.points == 0:
                return {"approved": False, "reason": "Falta estimativa de pontos"}

        elif stage["stage"] == "tech_review":
            if not story.technical_notes or story.technical_notes == "[]":
                return {"approved": False, "reason": "Faltam notas tecnicas"}
            if not story.agents or story.agents == "[]":
                return {"approved": False, "reason": "Faltam agentes designados"}

        # Log da aprovacao
        self._log_activity(
            story_id=story.story_id,
            agent_id=stage["agent"],
            action=f"{stage['stage']}_approved",
            message=f"Story aprovada por {stage['role']}"
        )

        return {"approved": True}

    def _log_activity(self, story_id: str, agent_id: str, action: str, message: str):
        """Registra atividade no log"""
        log = ActivityLog(
            source="validation_flow",
            source_id="VALIDATOR",
            agent_id=agent_id,
            project_id=self.project_id,
            story_id=story_id,
            event_type=action,
            message=message,
            level="INFO"
        )
        self.db.add(log)
        self.db.commit()

    def close(self):
        """Fecha conexao"""
        self.db.close()


def process_project_inputs(project_id: str) -> Dict:
    """
    Funcao principal para processar inputs de um projeto
    Orquestra todo o fluxo de processamento
    """
    db = SessionLocal()

    try:
        # Busca projeto
        project = db.query(Project).filter(Project.project_id == project_id).first()
        if not project:
            return {"error": f"Projeto {project_id} nao encontrado"}

        # Pega caminho dos arquivos de entrada
        config = project.config or {}
        source_path = config.get("source_path")

        if not source_path:
            return {"error": "Projeto nao tem source_path configurado"}

        print(f"[InputProcessor] Processando arquivos de: {source_path}")

        # 1. Processa arquivos de entrada
        processor = InputProcessor(project_id)
        results = processor.process_folder(source_path)

        if "error" in results:
            return results

        print(f"[InputProcessor] Arquivos processados: {len(results['files_processed'])}")
        print(f"[InputProcessor] Processos extraidos: {len(results['processes'])}")
        print(f"[InputProcessor] Requisitos extraidos: {len(results['requirements'])}")

        # 2. Gera stories
        generator = StoryGenerator(project_id)
        stories = generator.generate_stories_from_processes(
            processor.processes,
            processor.requirements
        )

        print(f"[StoryGenerator] Stories geradas: {len(stories)}")

        # 3. Salva stories
        saved_count = generator.save_stories(stories)
        generator.close()

        # 4. Submete para validacao
        validator = AgentValidationFlow(project_id)
        validated = 0

        for story in stories[:5]:  # Valida as 5 primeiras como exemplo
            result = validator.submit_for_validation(story)
            if result.get("success"):
                validated += 1

        validator.close()

        return {
            "success": True,
            "files_processed": len(results['files_processed']),
            "processes_extracted": len(results['processes']),
            "requirements_extracted": len(results['requirements']),
            "stories_created": saved_count,
            "stories_validated": validated
        }

    finally:
        db.close()


if __name__ == "__main__":
    # Teste com projeto de exemplo
    result = process_project_inputs("PROJ-20251216221517")
    print("\n=== RESULTADO ===")
    print(json.dumps(result, indent=2))
