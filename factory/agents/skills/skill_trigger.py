"""
Sistema de Acionamento Autonomo de Skills
=========================================

Permite que agentes identifiquem e acionem skills automaticamente
baseado no contexto da tarefa e arquivos envolvidos.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from .multimedia_base import MediaFormat, MediaType, AnalysisResult
from .registry import (
    analyze_file,
    can_analyze,
    get_media_type,
    get_analyzer,
    list_skills,
    get_supported_formats
)

if TYPE_CHECKING:
    from factory.agents.learning.skill_acquisition import SkillAcquisition


@dataclass
class SkillTriggerContext:
    """Contexto para acionamento de skill"""
    task_description: str
    files_involved: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    domain: Optional[str] = None
    project_type: Optional[str] = None


@dataclass
class SkillTriggerResult:
    """Resultado de acionamento de skills"""
    skills_triggered: List[str]
    analysis_results: Dict[str, AnalysisResult]
    recommendations: List[str]
    duration_ms: int = 0


class SkillTrigger:
    """
    Sistema de Acionamento Autonomo de Skills

    Analisa contexto da tarefa e determina quais skills
    devem ser acionadas automaticamente.
    """

    # Mapeamento de palavras-chave para skills
    KEYWORD_SKILL_MAP = {
        # Analise de texto
        "documento": ["text_analysis", "pdf_analysis", "document_analysis"],
        "pdf": ["pdf_analysis"],
        "word": ["document_analysis"],
        "docx": ["document_analysis"],
        "markdown": ["text_analysis"],
        "readme": ["text_analysis"],

        # Analise de codigo
        "codigo": ["code_analysis"],
        "code": ["code_analysis"],
        "script": ["code_analysis"],
        "python": ["code_analysis"],
        "javascript": ["code_analysis"],
        "typescript": ["code_analysis"],

        # Analise de dados
        "dados": ["data_analysis"],
        "data": ["data_analysis"],
        "json": ["data_analysis"],
        "csv": ["data_analysis"],
        "excel": ["data_analysis"],
        "planilha": ["data_analysis"],

        # Analise de audio
        "audio": ["audio_analysis"],
        "musica": ["music_analysis"],
        "podcast": ["speech_analysis"],
        "transcricao": ["speech_analysis"],
        "mp3": ["audio_analysis"],
        "wav": ["audio_analysis"],

        # Analise de video
        "video": ["video_analysis"],
        "filme": ["video_analysis"],
        "mp4": ["video_analysis"],
        "cena": ["scene_analysis"],
        "frame": ["frame_analysis"],
    }

    # Mapeamento de dominio para skills relevantes
    DOMAIN_SKILL_MAP = {
        "backend": ["code_analysis", "data_analysis"],
        "frontend": ["code_analysis", "text_analysis"],
        "database": ["data_analysis", "code_analysis"],
        "data": ["data_analysis", "code_analysis"],
        "analysis": ["data_analysis", "text_analysis"],
        "documentation": ["text_analysis", "document_analysis"],
        "devops": ["code_analysis", "text_analysis"],
        "security": ["code_analysis", "text_analysis"],
        "testing": ["code_analysis", "data_analysis"],
        "multimedia": ["video_analysis", "audio_analysis", "text_analysis"],
    }

    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id
        self._trigger_history: List[Dict] = []

    def analyze_context(self, context: SkillTriggerContext) -> List[str]:
        """
        Analisa contexto e determina skills relevantes

        Args:
            context: Contexto da tarefa

        Returns:
            Lista de skills recomendadas
        """
        recommended_skills = set()

        # 1. Analisa arquivos envolvidos
        for file_path in context.files_involved:
            path = Path(file_path)
            if path.suffix:
                fmt = MediaFormat.from_extension(path.suffix.lstrip('.'))
                if fmt:
                    # Adiciona skill apropriada para o formato
                    skill = self._get_skill_for_format(fmt)
                    if skill:
                        recommended_skills.add(skill)

        # 2. Analisa palavras-chave na descricao da tarefa
        task_lower = context.task_description.lower()
        for keyword, skills in self.KEYWORD_SKILL_MAP.items():
            if keyword in task_lower:
                recommended_skills.update(skills)

        # 3. Considera dominio do agente
        if context.domain and context.domain in self.DOMAIN_SKILL_MAP:
            recommended_skills.update(self.DOMAIN_SKILL_MAP[context.domain])

        # 4. Analisa keywords explicitas
        for keyword in context.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self.KEYWORD_SKILL_MAP:
                recommended_skills.update(self.KEYWORD_SKILL_MAP[keyword_lower])

        return list(recommended_skills)

    def _get_skill_for_format(self, fmt: MediaFormat) -> Optional[str]:
        """Retorna skill apropriada para um formato"""
        format_skill_map = {
            # Texto
            MediaFormat.TXT: "text_analysis",
            MediaFormat.MD: "text_analysis",
            MediaFormat.PDF: "pdf_analysis",
            MediaFormat.DOCX: "document_analysis",
            MediaFormat.DOC: "document_analysis",
            MediaFormat.HTML: "document_analysis",
            MediaFormat.XML: "document_analysis",

            # Codigo
            MediaFormat.PY: "code_analysis",
            MediaFormat.JS: "code_analysis",
            MediaFormat.TS: "code_analysis",
            MediaFormat.JAVA: "code_analysis",
            MediaFormat.CPP: "code_analysis",
            MediaFormat.SQL: "code_analysis",

            # Dados
            MediaFormat.JSON: "data_analysis",
            MediaFormat.CSV: "data_analysis",
            MediaFormat.XLSX: "data_analysis",

            # Audio
            MediaFormat.MP3: "audio_analysis",
            MediaFormat.WAV: "audio_analysis",
            MediaFormat.FLAC: "audio_analysis",
            MediaFormat.OGG: "audio_analysis",
            MediaFormat.M4A: "audio_analysis",

            # Video
            MediaFormat.MP4: "video_analysis",
            MediaFormat.AVI: "video_analysis",
            MediaFormat.MKV: "video_analysis",
            MediaFormat.MOV: "video_analysis",
            MediaFormat.WEBM: "video_analysis",
        }
        return format_skill_map.get(fmt)

    def trigger_skills(self, context: SkillTriggerContext) -> SkillTriggerResult:
        """
        Aciona skills automaticamente baseado no contexto

        Args:
            context: Contexto da tarefa

        Returns:
            Resultado com analises realizadas
        """
        import time
        start = time.time()

        # Determina skills a acionar
        skills_to_trigger = self.analyze_context(context)
        analysis_results = {}
        recommendations = []

        # Analisa arquivos que existem
        for file_path in context.files_involved:
            path = Path(file_path)
            if path.exists() and can_analyze(file_path):
                try:
                    result = analyze_file(file_path, agent_id=self.agent_id)
                    if result.success:
                        analysis_results[file_path] = result

                        # Gera recomendacoes baseadas na analise
                        recs = self._generate_recommendations(result)
                        recommendations.extend(recs)

                except Exception as e:
                    recommendations.append(f"Erro ao analisar {file_path}: {str(e)}")

        # Registra no historico
        self._trigger_history.append({
            "timestamp": datetime.now().isoformat(),
            "context": {
                "task": context.task_description,
                "files": context.files_involved,
                "domain": context.domain
            },
            "skills_triggered": skills_to_trigger,
            "files_analyzed": list(analysis_results.keys())
        })

        duration = int((time.time() - start) * 1000)

        return SkillTriggerResult(
            skills_triggered=skills_to_trigger,
            analysis_results=analysis_results,
            recommendations=recommendations,
            duration_ms=duration
        )

    def _generate_recommendations(self, result: AnalysisResult) -> List[str]:
        """Gera recomendacoes baseadas na analise"""
        recommendations = []

        # Recomendacoes para codigo
        if result.media_type == MediaType.TEXT and 'code_analysis' in str(result.metadata):
            code_info = result.metadata.get('code_analysis', {})
            stats = result.stats

            # Complexidade alta
            if stats.get('estimated_complexity') == 'very_high':
                recommendations.append(
                    f"Codigo em {result.file_path} tem complexidade muito alta. "
                    "Considere refatorar em funcoes menores."
                )

            # Poucos comentarios
            if stats.get('comment_ratio', 0) < 0.1:
                recommendations.append(
                    f"Codigo em {result.file_path} tem poucos comentarios. "
                    "Considere adicionar documentacao."
                )

        # Recomendacoes para dados
        if result.media_type == MediaType.DATA:
            if 'column_types' in result.metadata:
                types = result.metadata['column_types']
                mixed_types = [col for col, t in types.items() if t == 'string']
                if len(mixed_types) > len(types) * 0.7:
                    recommendations.append(
                        f"Dados em {result.file_path} tem muitas colunas de texto. "
                        "Verifique se tipos estao corretos."
                    )

        # Recomendacoes para audio
        if result.media_type == MediaType.AUDIO:
            audio = result.metadata.get('audio', {})
            if audio.get('bitrate_kbps', 0) < 128:
                recommendations.append(
                    f"Audio em {result.file_path} tem bitrate baixo ({audio.get('bitrate_kbps')}kbps). "
                    "Qualidade pode ser comprometida."
                )

        # Recomendacoes para video
        if result.media_type == MediaType.VIDEO:
            video = result.metadata.get('video', {}).get('video', {})
            if video.get('resolution_name') in ['SD', 'Low']:
                recommendations.append(
                    f"Video em {result.file_path} tem resolucao baixa ({video.get('resolution')}). "
                    "Considere usar versao em maior resolucao."
                )

        return recommendations

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Retorna historico de acionamentos"""
        return self._trigger_history[-limit:]

    def update_skill_proficiency(
        self,
        skill_acquisition: "SkillAcquisition",
        result: SkillTriggerResult,
        success: bool = True
    ):
        """
        Atualiza proficiencia das skills usadas

        Args:
            skill_acquisition: Sistema de skills do agente
            result: Resultado do trigger
            success: Se a tarefa foi bem-sucedida
        """
        for skill_name in result.skills_triggered:
            # XP baseado no skill e sucesso
            base_xp = {
                "text_analysis": 5,
                "pdf_analysis": 10,
                "document_analysis": 10,
                "code_analysis": 15,
                "data_analysis": 10,
                "audio_analysis": 15,
                "speech_analysis": 20,
                "music_analysis": 15,
                "video_analysis": 20,
                "frame_analysis": 25,
                "scene_analysis": 25
            }.get(skill_name, 10)

            skill_acquisition.practice_skill(skill_name, success, base_xp)


class AutoSkillAgent:
    """
    Mixin para adicionar capacidade de acionamento autonomo de skills
    a um agente.

    Uso:
        class MyAgent(AutonomousAgent, AutoSkillAgent):
            pass
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skill_trigger = SkillTrigger(agent_id=self.agent_id)

    def analyze_task_files(self, files: List[str]) -> SkillTriggerResult:
        """
        Analisa arquivos relacionados a tarefa

        Args:
            files: Lista de caminhos de arquivos

        Returns:
            Resultado da analise
        """
        context = SkillTriggerContext(
            task_description=self._current_task.description if self._current_task else "",
            files_involved=files,
            domain=self.domain
        )

        result = self.skill_trigger.trigger_skills(context)

        # Atualiza proficiencia
        self.skill_trigger.update_skill_proficiency(
            self.skills,
            result,
            success=True
        )

        return result

    def auto_analyze(self, task_description: str, files: Optional[List[str]] = None) -> Dict:
        """
        Analise automatica baseada na descricao da tarefa

        Args:
            task_description: Descricao da tarefa
            files: Arquivos opcionais

        Returns:
            Dict com resultados e recomendacoes
        """
        context = SkillTriggerContext(
            task_description=task_description,
            files_involved=files or [],
            domain=self.domain
        )

        # Analisa contexto
        recommended_skills = self.skill_trigger.analyze_context(context)

        # Se tem arquivos, analisa
        analysis_results = {}
        if files:
            trigger_result = self.skill_trigger.trigger_skills(context)
            analysis_results = {
                path: result.to_dict()
                for path, result in trigger_result.analysis_results.items()
            }

        return {
            "recommended_skills": recommended_skills,
            "analysis_results": analysis_results,
            "agent_domain": self.domain,
            "agent_skills": [s.name for s in self.skills.get_all_skills()]
        }


def integrate_skills_with_agent(agent_class):
    """
    Decorator para integrar skills automaticas em um agente

    Uso:
        @integrate_skills_with_agent
        class MyAgent(AutonomousAgent):
            pass
    """
    original_init = agent_class.__init__
    original_think = getattr(agent_class, '_think', None)

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.skill_trigger = SkillTrigger(agent_id=self.agent_id)

    def new_think(self, task):
        """Think phase com analise automatica de skills"""
        # Executa think original
        context = original_think(self, task) if original_think else {}

        # Analisa arquivos mencionados na tarefa
        files = self._extract_files_from_task(task)
        if files:
            trigger_context = SkillTriggerContext(
                task_description=task.description,
                files_involved=files,
                domain=self.domain
            )
            skill_result = self.skill_trigger.trigger_skills(trigger_context)

            # Adiciona ao contexto
            context['skill_analysis'] = {
                'skills_triggered': skill_result.skills_triggered,
                'recommendations': skill_result.recommendations,
                'file_analyses': {
                    path: result.to_dict()
                    for path, result in skill_result.analysis_results.items()
                }
            }

            # Atualiza memoria de trabalho
            for rec in skill_result.recommendations:
                self.working_memory.add_note(rec)

        return context

    def _extract_files_from_task(self, task):
        """Extrai caminhos de arquivos da descricao da tarefa"""
        files = []

        # Padroes comuns de caminhos
        patterns = [
            r'[A-Za-z]:\\[^\s]+\.[a-zA-Z0-9]+',  # Windows path
            r'/[^\s]+\.[a-zA-Z0-9]+',             # Unix path
            r'[a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+',     # Relative path
        ]

        for pattern in patterns:
            matches = re.findall(pattern, task.description)
            for match in matches:
                if can_analyze(match):
                    files.append(match)

        # Arquivos em metadata
        if hasattr(task, 'metadata') and 'files' in task.metadata:
            files.extend(task.metadata['files'])

        return list(set(files))

    agent_class.__init__ = new_init
    agent_class._think = new_think
    agent_class._extract_files_from_task = _extract_files_from_task

    return agent_class
