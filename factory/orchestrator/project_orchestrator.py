"""
Project Orchestrator - Orquestra agentes para criar e desenvolver projetos autonomamente

Quando um projeto e criado:
1. Agente Analista le os inputs (documentos, videos, audio)
2. Agente Product Manager cria as stories baseado nos requisitos
3. Stories sao movidas para o pipeline automaticamente
4. Agentes de desenvolvimento executam as stories

Este e o componente que faz os agentes trabalharem de forma AUTONOMA.
"""

import os
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import uuid

# Adiciona path do projeto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from factory.database.connection import SessionLocal
from factory.database.models import Project, Story, Agent, ActivityLog

# Tenta importar bibliotecas opcionais para processamento de arquivos
try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


@dataclass
class InputFile:
    """Arquivo de entrada para processamento"""
    path: str
    file_type: str
    name: str
    size: int
    content: Optional[str] = None
    metadata: Dict = None


class InputProcessor:
    """
    Processa arquivos de entrada de qualquer formato
    Skill usada pelos agentes para ler documentos, videos, audio
    """

    SUPPORTED_EXTENSIONS = {
        '.txt': 'text',
        '.md': 'markdown',
        '.doc': 'word',
        '.docx': 'word',
        '.pdf': 'pdf',
        '.json': 'json',
        '.csv': 'csv',
        '.mp4': 'video',
        '.avi': 'video',
        '.mkv': 'video',
        '.mov': 'video',
        '.mp3': 'audio',
        '.wav': 'audio',
        '.m4a': 'audio',
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
    }

    def __init__(self):
        self.processed_files: List[InputFile] = []

    def scan_directory(self, path: str) -> List[InputFile]:
        """Escaneia diretorio e identifica arquivos para processar"""
        files = []
        path_obj = Path(path)

        if not path_obj.exists():
            print(f"[InputProcessor] Diretorio nao existe: {path}")
            return files

        for file_path in path_obj.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    files.append(InputFile(
                        path=str(file_path),
                        file_type=self.SUPPORTED_EXTENSIONS[ext],
                        name=file_path.name,
                        size=file_path.stat().st_size,
                        metadata={"extension": ext}
                    ))

        print(f"[InputProcessor] Encontrados {len(files)} arquivos em {path}")
        return files

    def process_file(self, input_file: InputFile) -> InputFile:
        """Processa um arquivo e extrai conteudo"""
        try:
            if input_file.file_type == 'text':
                input_file.content = self._read_text(input_file.path)
            elif input_file.file_type == 'markdown':
                input_file.content = self._read_text(input_file.path)
            elif input_file.file_type == 'word':
                input_file.content = self._read_word(input_file.path)
            elif input_file.file_type == 'pdf':
                input_file.content = self._read_pdf(input_file.path)
            elif input_file.file_type == 'json':
                input_file.content = self._read_json(input_file.path)
            elif input_file.file_type in ['video', 'audio']:
                # Para video/audio, verifica se existe transcricao
                input_file.content = self._find_transcription(input_file.path)
            else:
                input_file.content = f"[Arquivo {input_file.file_type}: {input_file.name}]"

            print(f"[InputProcessor] Processado: {input_file.name}")
            return input_file

        except Exception as e:
            print(f"[InputProcessor] Erro processando {input_file.name}: {e}")
            input_file.content = f"[Erro ao processar: {e}]"
            return input_file

    def _read_text(self, path: str) -> str:
        """Le arquivo de texto"""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return "[Erro de encoding]"

    def _read_word(self, path: str) -> str:
        """Le arquivo Word (.doc, .docx)"""
        if not HAS_DOCX:
            # Tenta ler como texto se nao tem python-docx
            try:
                return self._read_text(path)
            except:
                return "[Instale python-docx para ler arquivos Word]"

        try:
            doc = DocxDocument(path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return '\n\n'.join(paragraphs)
        except Exception as e:
            return f"[Erro lendo Word: {e}]"

    def _read_pdf(self, path: str) -> str:
        """Le arquivo PDF"""
        if not HAS_PDF:
            return "[Instale PyPDF2 para ler arquivos PDF]"

        try:
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                return '\n\n'.join(text)
        except Exception as e:
            return f"[Erro lendo PDF: {e}]"

    def _read_json(self, path: str) -> str:
        """Le arquivo JSON"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"[Erro lendo JSON: {e}]"

    def _find_transcription(self, media_path: str) -> str:
        """Procura transcricao para arquivo de video/audio"""
        base_path = Path(media_path)

        # Procura arquivos de transcricao no mesmo diretorio
        transcription_patterns = [
            base_path.with_suffix('.txt'),
            base_path.with_suffix('.docx'),
            base_path.with_suffix('.doc'),
            base_path.parent / f"transcricao_{base_path.stem}.txt",
            base_path.parent / f"transcricao_{base_path.stem}.docx",
            base_path.parent / f"{base_path.stem}_transcricao.txt",
            base_path.parent / f"{base_path.stem}_transcription.txt",
        ]

        for pattern in transcription_patterns:
            if pattern.exists():
                print(f"[InputProcessor] Encontrada transcricao: {pattern}")
                if pattern.suffix == '.docx':
                    return self._read_word(str(pattern))
                else:
                    return self._read_text(str(pattern))

        return f"[Video/Audio: {base_path.name} - Transcricao nao encontrada. Use skill de transcricao.]"


class StoryGenerator:
    """
    Gera stories baseado no conteudo processado
    Simula o trabalho do Product Manager/Product Owner
    """

    def __init__(self):
        self.story_templates = {
            "backend": {
                "category": "backend",
                "agents": ["AGT-007", "AGT-008", "AGT-013"],
                "points_base": 8
            },
            "frontend": {
                "category": "frontend",
                "agents": ["AGT-009", "AGT-012"],
                "points_base": 5
            },
            "database": {
                "category": "database",
                "agents": ["AGT-007", "AGT-006"],
                "points_base": 5
            },
            "integration": {
                "category": "integracao",
                "agents": ["AGT-019", "AGT-008"],
                "points_base": 13
            },
            "infrastructure": {
                "category": "infraestrutura",
                "agents": ["AGT-014", "AGT-010"],
                "points_base": 8
            }
        }

    def analyze_and_create_stories(self, project: Project, inputs: List[InputFile], db) -> List[Story]:
        """Analisa inputs e cria stories para o projeto"""
        stories = []

        # Combina todo conteudo dos inputs
        all_content = "\n\n---\n\n".join([
            f"## {inp.name}\n{inp.content or '[Sem conteudo]'}"
            for inp in inputs if inp.content
        ])

        # Extrai requisitos do conteudo
        requirements = self._extract_requirements(all_content, project)

        # Cria stories baseado nos requisitos
        for i, req in enumerate(requirements, 1):
            story = self._create_story(project, req, i, db)
            if story:
                stories.append(story)

        print(f"[StoryGenerator] Criadas {len(stories)} stories para {project.name}")
        return stories

    def _extract_requirements(self, content: str, project: Project) -> List[Dict]:
        """Extrai requisitos do conteudo"""
        requirements = []

        # Analisa tipo de projeto para gerar stories apropriadas
        project_type = project.project_type or "web-app"
        project_config = project.config or {}

        # Se e projeto BPM, gera stories para plataforma BPM
        if project_type == "bpm" or "bpm" in project.name.lower():
            requirements = self._generate_bpm_platform_requirements(project)
        else:
            # Projeto generico - analisa conteudo para extrair requisitos
            requirements = self._analyze_content_for_requirements(content, project)

        return requirements

    def _generate_bpm_platform_requirements(self, project: Project) -> List[Dict]:
        """Gera requisitos para plataforma BPM"""
        return [
            {
                "title": "Backend FastAPI - Modelos de Dados BPM",
                "description": "Criar modelos SQLAlchemy para Process, ProcessStep, ProcessProblem, ProcessImprovement, ProcessDocument",
                "type": "backend",
                "priority": 1,
                "acceptance_criteria": [
                    "Modelo Process com campos: name, description, type (AS-IS/TO-BE), area, owner",
                    "Modelo ProcessStep com: name, order, role, system, duration",
                    "Modelo ProcessProblem com: title, category, severity, impact",
                    "Modelo ProcessImprovement com: title, type, expected_reduction",
                    "Relacionamentos configurados entre modelos"
                ],
                "technical_notes": [
                    "Usar SQLAlchemy ORM",
                    "SQLite como banco de dados",
                    "Implementar to_dict() em cada modelo"
                ]
            },
            {
                "title": "Backend FastAPI - API REST de Processos",
                "description": "Criar endpoints REST para CRUD de processos BPM",
                "type": "backend",
                "priority": 1,
                "acceptance_criteria": [
                    "GET /api/processes - Listar processos",
                    "POST /api/processes - Criar processo",
                    "GET /api/processes/{id} - Detalhe do processo",
                    "PUT /api/processes/{id} - Atualizar processo",
                    "DELETE /api/processes/{id} - Deletar processo",
                    "POST /api/processes/{id}/clone-to-tobe - Clonar AS-IS para TO-BE"
                ],
                "technical_notes": [
                    "FastAPI com routers separados",
                    "Pydantic schemas para validacao",
                    "Dependency injection para DB session"
                ]
            },
            {
                "title": "Backend FastAPI - API de Etapas e Problemas",
                "description": "Criar endpoints para gerenciar etapas de processo e problemas identificados",
                "type": "backend",
                "priority": 2,
                "acceptance_criteria": [
                    "CRUD completo de ProcessStep",
                    "CRUD completo de ProcessProblem",
                    "CRUD completo de ProcessImprovement",
                    "Endpoints aninhados sob /api/processes/{id}/steps etc"
                ],
                "technical_notes": [
                    "Validar que step/problem pertence ao processo",
                    "Cascade delete quando processo e deletado"
                ]
            },
            {
                "title": "Backend FastAPI - Upload de Documentos",
                "description": "Implementar upload e gerenciamento de documentos associados a processos",
                "type": "backend",
                "priority": 2,
                "acceptance_criteria": [
                    "POST /api/processes/{id}/documents - Upload de documento",
                    "GET /api/processes/{id}/documents - Listar documentos",
                    "DELETE /api/documents/{id} - Deletar documento",
                    "Suporte a PDF, DOCX, imagens"
                ],
                "technical_notes": [
                    "Usar python-multipart para uploads",
                    "Armazenar em pasta local inicialmente",
                    "Registrar metadados no banco"
                ]
            },
            {
                "title": "Frontend Vue - Layout Principal",
                "description": "Criar layout principal da aplicacao com navegacao e estrutura base",
                "type": "frontend",
                "priority": 1,
                "acceptance_criteria": [
                    "Header com logo e navegacao",
                    "Sidebar com menu de opcoes",
                    "Area de conteudo principal",
                    "Footer com informacoes"
                ],
                "technical_notes": [
                    "Vue 3 Composition API",
                    "CSS moderno com flexbox/grid",
                    "Responsivo para desktop"
                ]
            },
            {
                "title": "Frontend Vue - Lista de Processos",
                "description": "Criar tela de listagem de processos com filtros",
                "type": "frontend",
                "priority": 1,
                "acceptance_criteria": [
                    "Tabela com lista de processos",
                    "Filtro por tipo (AS-IS/TO-BE)",
                    "Filtro por area",
                    "Busca por nome",
                    "Botao para criar novo processo"
                ],
                "technical_notes": [
                    "Componente ProcessList.vue",
                    "Fetch API para buscar dados",
                    "Estado reativo com ref/reactive"
                ]
            },
            {
                "title": "Frontend Vue - Visualizacao de Processo",
                "description": "Criar tela de visualizacao detalhada de um processo",
                "type": "frontend",
                "priority": 2,
                "acceptance_criteria": [
                    "Exibir dados basicos do processo",
                    "Lista de etapas ordenadas",
                    "Lista de problemas identificados",
                    "Lista de melhorias propostas",
                    "Opcao de editar cada secao"
                ],
                "technical_notes": [
                    "Componente ProcessDetail.vue",
                    "Tabs para organizar informacoes",
                    "Modais para edicao inline"
                ]
            },
            {
                "title": "Frontend Vue - Formulario de Processo",
                "description": "Criar formulario para criar/editar processos",
                "type": "frontend",
                "priority": 2,
                "acceptance_criteria": [
                    "Campos para dados basicos",
                    "Adicionar/remover etapas",
                    "Adicionar/remover problemas",
                    "Validacao de campos obrigatorios",
                    "Botao clonar para TO-BE"
                ],
                "technical_notes": [
                    "Componente ProcessForm.vue",
                    "Validacao client-side",
                    "Preview antes de salvar"
                ]
            },
            {
                "title": "Integracao Backend-Frontend",
                "description": "Integrar frontend com backend e testar fluxo completo",
                "type": "integration",
                "priority": 3,
                "acceptance_criteria": [
                    "Frontend conecta com API backend",
                    "CORS configurado corretamente",
                    "Criar processo funciona end-to-end",
                    "Editar processo funciona end-to-end",
                    "Clonar AS-IS para TO-BE funciona"
                ],
                "technical_notes": [
                    "Configurar CORS no FastAPI",
                    "Testar em ambiente local",
                    "Documentar endpoints"
                ]
            },
            {
                "title": "Deploy e Documentacao",
                "description": "Preparar aplicacao para deploy e documentar uso",
                "type": "infrastructure",
                "priority": 3,
                "acceptance_criteria": [
                    "Script de inicializacao",
                    "README com instrucoes",
                    "Documentacao da API",
                    "Configuracao de ambiente"
                ],
                "technical_notes": [
                    "Criar main.py que inicia tudo",
                    "requirements.txt atualizado",
                    "Documentar endpoints da API"
                ]
            }
        ]

    def _analyze_content_for_requirements(self, content: str, project: Project) -> List[Dict]:
        """Analisa conteudo textual para extrair requisitos"""
        requirements = []

        # Palavras-chave para identificar tipos de requisitos
        keywords = {
            "backend": ["api", "endpoint", "servidor", "banco", "dados", "crud"],
            "frontend": ["tela", "interface", "usuario", "botao", "formulario", "lista"],
            "database": ["tabela", "modelo", "schema", "migracao", "indice"],
            "integration": ["integracao", "sap", "api externa", "webhook", "sync"]
        }

        content_lower = content.lower()

        # Conta ocorrencias de cada tipo
        type_counts = {}
        for req_type, words in keywords.items():
            count = sum(content_lower.count(word) for word in words)
            type_counts[req_type] = count

        # Gera pelo menos uma story de cada tipo relevante
        for req_type, count in type_counts.items():
            if count > 0:
                requirements.append({
                    "title": f"Implementar {req_type.title()} - {project.name}",
                    "description": f"Desenvolver componentes de {req_type} baseado nos requisitos do projeto",
                    "type": req_type,
                    "priority": 2 if req_type in ["backend", "frontend"] else 3,
                    "acceptance_criteria": [
                        f"Componente {req_type} implementado",
                        "Testes basicos passando",
                        "Documentacao atualizada"
                    ],
                    "technical_notes": [
                        f"Baseado na analise do conteudo do projeto"
                    ]
                })

        return requirements

    def _create_story(self, project: Project, requirement: Dict, order: int, db) -> Optional[Story]:
        """Cria uma story no banco de dados"""
        try:
            template = self.story_templates.get(requirement["type"], self.story_templates["backend"])

            story_id = f"US-{project.project_id[:8]}-{str(order).zfill(3)}"

            # Verifica se ja existe
            existing = db.query(Story).filter(Story.story_id == story_id).first()
            if existing:
                print(f"[StoryGenerator] Story {story_id} ja existe, pulando")
                return None

            story = Story(
                story_id=story_id,
                project_id=project.project_id,
                title=requirement["title"],
                description=requirement["description"],
                status="BACKLOG",
                sprint=order // 3 + 1,  # Distribui em sprints
                points=template["points_base"],
                priority=requirement.get("priority", 2),
                narrative={
                    "persona": "desenvolvedor",
                    "action": requirement["title"].lower(),
                    "benefit": "entregar funcionalidade do projeto",
                    "full": f"Como desenvolvedor, quero {requirement['title'].lower()}, para entregar funcionalidade do projeto"
                },
                acceptance_criteria=json.dumps(requirement.get("acceptance_criteria", [])),
                technical_notes=json.dumps(requirement.get("technical_notes", [])),
                assigned_to=template["agents"][0] if template["agents"] else "AGT-008",
                agents=json.dumps(template["agents"]),
                category=template["category"],
                created_by="AGT-002",  # Product Manager
                tags=json.dumps([template["category"], project.project_type or "web-app"])
            )

            db.add(story)
            db.commit()
            db.refresh(story)

            return story

        except Exception as e:
            print(f"[StoryGenerator] Erro criando story: {e}")
            db.rollback()
            return None


class ProjectOrchestrator:
    """
    Orquestra o fluxo autonomo de desenvolvimento de projetos

    1. Monitora projetos novos ou pendentes
    2. Processa inputs do projeto
    3. Aciona agentes para criar stories
    4. Move stories pelo pipeline
    """

    def __init__(self):
        self.input_processor = InputProcessor()
        self.story_generator = StoryGenerator()
        self._running = False
        self._thread = None

    def start(self):
        """Inicia o orchestrator"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print("[ProjectOrchestrator] Iniciado")

    def stop(self):
        """Para o orchestrator"""
        self._running = False
        print("[ProjectOrchestrator] Parado")

    def _run(self):
        """Loop principal do orchestrator"""
        while self._running:
            try:
                db = SessionLocal()
                try:
                    self._process_pending_projects(db)
                finally:
                    db.close()
            except Exception as e:
                print(f"[ProjectOrchestrator] Erro: {e}")

            time.sleep(5)  # Verifica a cada 5 segundos

    def _process_pending_projects(self, db):
        """Processa projetos que precisam de atencao"""

        # Busca projetos pendentes (novos ou sem stories)
        projects = db.query(Project).filter(
            Project.status.in_(["pending", "planning"])
        ).all()

        for project in projects:
            stories_count = db.query(Story).filter(
                Story.project_id == project.project_id
            ).count()

            # Se projeto nao tem stories suficientes, processa
            if stories_count < 3:
                self._process_project(project, db)

    def _process_project(self, project: Project, db):
        """Processa um projeto - le inputs e cria stories"""
        print(f"[ProjectOrchestrator] Processando projeto: {project.name}")

        # Log de inicio
        self._log_activity(db, project.project_id, "AGT-002",
                          "project_processing_started",
                          f"Iniciando processamento autonomo do projeto {project.name}")

        # 1. Identifica pasta de inputs
        config = project.config or {}
        source_path = config.get("source_path", "")

        input_files = []
        if source_path and Path(source_path).exists():
            # Escaneia pasta de inputs
            input_files = self.input_processor.scan_directory(source_path)

            # Processa cada arquivo
            for input_file in input_files:
                self.input_processor.process_file(input_file)

                self._log_activity(db, project.project_id, "AGT-005",
                                  "input_processed",
                                  f"Processado: {input_file.name} ({input_file.file_type})")

        # 2. Gera stories baseado nos inputs
        stories = self.story_generator.analyze_and_create_stories(project, input_files, db)

        # Log de stories criadas
        for story in stories:
            self._log_activity(db, project.project_id, "AGT-002",
                              "story_created",
                              f"Story criada: {story.story_id} - {story.title}",
                              story_id=story.story_id)

        # 3. Atualiza status do projeto
        project.status = "IN_PROGRESS"
        db.commit()

        self._log_activity(db, project.project_id, "AGT-001",
                          "project_ready",
                          f"Projeto {project.name} pronto para desenvolvimento com {len(stories)} stories")

        print(f"[ProjectOrchestrator] Projeto {project.name} processado: {len(stories)} stories criadas")

    def process_project_now(self, project_id: str) -> Dict:
        """Processa um projeto imediatamente (trigger manual)"""
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.project_id == project_id).first()
            if not project:
                return {"success": False, "error": "Projeto nao encontrado"}

            self._process_project(project, db)

            stories_count = db.query(Story).filter(
                Story.project_id == project_id
            ).count()

            return {
                "success": True,
                "project": project.name,
                "stories_created": stories_count
            }
        finally:
            db.close()

    def _log_activity(self, db, project_id: str, agent_id: str,
                      event_type: str, message: str, story_id: str = None):
        """Registra atividade no log"""
        log = ActivityLog(
            source="project_orchestrator",
            source_id="ORCHESTRATOR",
            agent_id=agent_id,
            project_id=project_id,
            story_id=story_id,
            event_type=event_type,
            message=message,
            level="INFO"
        )
        db.add(log)
        db.commit()


# Instancia global
_orchestrator: Optional[ProjectOrchestrator] = None


def get_orchestrator() -> ProjectOrchestrator:
    """Retorna instancia global do orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ProjectOrchestrator()
    return _orchestrator


def start_orchestrator():
    """Inicia o orchestrator global"""
    orchestrator = get_orchestrator()
    orchestrator.start()
    return orchestrator


def stop_orchestrator():
    """Para o orchestrator global"""
    global _orchestrator
    if _orchestrator:
        _orchestrator.stop()
        _orchestrator = None


if __name__ == "__main__":
    # Teste
    orchestrator = start_orchestrator()
    print("Orchestrator rodando... Pressione Ctrl+C para parar")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_orchestrator()
