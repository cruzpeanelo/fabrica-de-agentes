"""
Registro Central de Skills Multimidia
=====================================

Inicializa e gerencia todos os analisadores de midia.
Fornece interface unificada para analise de qualquer tipo de arquivo.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .multimedia_base import (
    MediaAnalyzer,
    MediaFormat,
    MediaSkillRegistry,
    MediaType,
    AnalysisResult
)

from .text_analysis import (
    TextAnalyzer,
    PDFAnalyzer,
    DocumentAnalyzer,
    CodeAnalyzer,
    DataFileAnalyzer
)

from .audio_analysis import (
    AudioAnalyzer,
    SpeechAnalyzer,
    MusicAnalyzer
)

from .video_analysis import (
    VideoAnalyzer,
    FrameAnalyzer,
    SceneAnalyzer
)


# Registro global singleton
_global_registry: Optional[MediaSkillRegistry] = None


def get_registry() -> MediaSkillRegistry:
    """
    Retorna registro global de skills

    Inicializa o registro na primeira chamada e registra todos os analisadores.

    Returns:
        MediaSkillRegistry: Registro global
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = MediaSkillRegistry()
        _register_all_analyzers(_global_registry)

    return _global_registry


def _register_all_analyzers(registry: MediaSkillRegistry):
    """Registra todos os analisadores no registry"""

    # Analisadores de texto
    registry.register_analyzer(TextAnalyzer)
    registry.register_analyzer(PDFAnalyzer)
    registry.register_analyzer(DocumentAnalyzer)
    registry.register_analyzer(CodeAnalyzer)
    registry.register_analyzer(DataFileAnalyzer)

    # Analisadores de audio
    registry.register_analyzer(AudioAnalyzer)
    registry.register_analyzer(SpeechAnalyzer)
    registry.register_analyzer(MusicAnalyzer)

    # Analisadores de video
    registry.register_analyzer(VideoAnalyzer)
    registry.register_analyzer(FrameAnalyzer)
    registry.register_analyzer(SceneAnalyzer)


def analyze_file(path: str | Path, agent_id: Optional[str] = None, **options) -> AnalysisResult:
    """
    Analisa um arquivo automaticamente

    Detecta o tipo de arquivo e usa o analisador apropriado.

    Args:
        path: Caminho do arquivo
        agent_id: ID do agente (opcional)
        **options: Opcoes de analise

    Returns:
        AnalysisResult: Resultado da analise

    Example:
        >>> result = analyze_file("documento.pdf")
        >>> print(result.content_summary)

        >>> result = analyze_file("video.mp4", agent_id="08")
        >>> print(result.metadata['video'])
    """
    registry = get_registry()
    return registry.analyze_file(Path(path), agent_id, **options)


def get_supported_formats() -> Dict[str, List[str]]:
    """
    Lista formatos suportados por tipo de midia

    Returns:
        Dict mapeando tipo de midia para lista de extensoes

    Example:
        >>> formats = get_supported_formats()
        >>> print(formats['video'])
        ['mp4', 'avi', 'mkv', 'mov', 'webm', 'wmv', 'flv']
    """
    registry = get_registry()
    return registry.get_supported_formats()


def list_skills() -> List[Dict]:
    """
    Lista todas as skills de analise registradas

    Returns:
        Lista de dicts com informacoes de cada skill

    Example:
        >>> skills = list_skills()
        >>> for skill in skills:
        ...     print(f"{skill['name']}: {skill['description']}")
    """
    registry = get_registry()
    return registry.list_skills()


def get_analyzer(skill_name: str, agent_id: Optional[str] = None) -> Optional[MediaAnalyzer]:
    """
    Obtem instancia de um analisador especifico

    Args:
        skill_name: Nome do skill (ex: "video_analysis")
        agent_id: ID do agente (opcional)

    Returns:
        Instancia do analisador ou None

    Example:
        >>> analyzer = get_analyzer("pdf_analysis", agent_id="08")
        >>> result = analyzer.analyze(Path("documento.pdf"))
    """
    registry = get_registry()
    return registry.get_analyzer(skill_name, agent_id)


def get_analysis_history(
    agent_id: Optional[str] = None,
    media_type: Optional[str] = None,
    limit: int = 100
) -> List[Dict]:
    """
    Retorna historico de analises

    Args:
        agent_id: Filtrar por agente
        media_type: Filtrar por tipo (text, audio, video)
        limit: Numero maximo de registros

    Returns:
        Lista de registros de analise

    Example:
        >>> history = get_analysis_history(agent_id="08", media_type="video")
        >>> for record in history:
        ...     print(f"{record['file_path']}: {record['success']}")
    """
    registry = get_registry()

    mt = None
    if media_type:
        mt = MediaType(media_type) if media_type in [m.value for m in MediaType] else None

    return registry.get_analysis_history(agent_id, mt, limit)


# ==================================================
# INTEGRACAO COM SISTEMA DE AGENTES
# ==================================================

def register_skills_for_agent(agent_id: str, skill_acquisition):
    """
    Registra skills de midia para um agente

    Integra as skills de analise multimidia com o sistema de
    aquisicao de skills do agente.

    Args:
        agent_id: ID do agente
        skill_acquisition: Instancia de SkillAcquisition do agente

    Example:
        >>> from factory.agents.learning import SkillAcquisition
        >>> skills = SkillAcquisition(agent_id="08")
        >>> register_skills_for_agent("08", skills)
    """
    registry = get_registry()

    for skill_info in registry.list_skills():
        skill_acquisition.acquire_skill(
            name=skill_info['name'],
            description=skill_info['description'],
            category=skill_info['category'],
            initial_proficiency=0.3  # Começa com nivel basico
        )


def practice_media_skill(agent_id: str, skill_name: str, success: bool, skill_acquisition):
    """
    Registra pratica de skill de midia

    Atualiza proficiencia baseado no uso.

    Args:
        agent_id: ID do agente
        skill_name: Nome do skill usado
        success: Se a analise foi bem-sucedida
        skill_acquisition: Instancia de SkillAcquisition

    Example:
        >>> practice_media_skill("08", "video_analysis", True, skills)
    """
    # Calcula XP baseado no skill
    xp_map = {
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
    }

    xp = xp_map.get(skill_name, 10)
    skill_acquisition.practice_skill(skill_name, success, xp)


# ==================================================
# FUNCOES UTILITARIAS
# ==================================================

def can_analyze(path: str | Path) -> bool:
    """
    Verifica se um arquivo pode ser analisado

    Args:
        path: Caminho do arquivo

    Returns:
        True se existe um analisador para o formato

    Example:
        >>> can_analyze("video.mp4")
        True
        >>> can_analyze("arquivo.xyz")
        False
    """
    path = Path(path)
    fmt = MediaFormat.from_path(path)
    if not fmt:
        return False

    registry = get_registry()
    analyzer = registry.get_analyzer_for_file(path)
    return analyzer is not None


def get_media_type(path: str | Path) -> Optional[str]:
    """
    Retorna tipo de midia de um arquivo

    Args:
        path: Caminho do arquivo

    Returns:
        Tipo de midia (text, audio, video, image, data) ou None

    Example:
        >>> get_media_type("video.mp4")
        'video'
        >>> get_media_type("documento.pdf")
        'text'
    """
    path = Path(path)
    fmt = MediaFormat.from_path(path)
    return fmt.media_type.value if fmt else None


def batch_analyze(paths: List[str | Path], agent_id: Optional[str] = None) -> List[AnalysisResult]:
    """
    Analisa multiplos arquivos

    Args:
        paths: Lista de caminhos
        agent_id: ID do agente

    Returns:
        Lista de resultados

    Example:
        >>> files = ["video1.mp4", "audio.mp3", "doc.pdf"]
        >>> results = batch_analyze(files)
        >>> for r in results:
        ...     print(f"{r.file_path}: {'OK' if r.success else 'ERRO'}")
    """
    results = []
    for path in paths:
        result = analyze_file(path, agent_id)
        results.append(result)
    return results


# ==================================================
# RESUMO DAS CAPACIDADES
# ==================================================

CAPABILITIES_SUMMARY = """
SKILLS DE ANALISE MULTIMIDIA
============================

TEXTO:
------
- text_analysis: TXT, MD (Markdown)
- pdf_analysis: PDF (extrai texto e metadados)
- document_analysis: DOCX, HTML, XML
- code_analysis: Python, JavaScript, TypeScript, Java, C++, SQL
- data_analysis: JSON, CSV, XLSX (Excel)

AUDIO:
------
- audio_analysis: MP3, WAV, FLAC, OGG, M4A, AAC, WMA
  * Extrai: duracao, bitrate, sample rate, canais
  * Tags: ID3v1, ID3v2, Vorbis Comments
- speech_analysis: Preparacao para transcricao
- music_analysis: Analise musical (waveform basico)

VIDEO:
------
- video_analysis: MP4, AVI, MKV, MOV, WEBM, WMV, FLV
  * Extrai: resolucao, FPS, codec, duracao
  * Streams: video, audio, legendas
- frame_analysis: Informacoes de frames
- scene_analysis: Estimativa de cenas

TOTAL: 11 skills de analise cobrindo 35+ formatos
"""


def print_capabilities():
    """Imprime resumo das capacidades"""
    print(CAPABILITIES_SUMMARY)


if __name__ == "__main__":
    print_capabilities()
    print("\nFormatos suportados:")
    for media_type, formats in get_supported_formats().items():
        print(f"  {media_type}: {', '.join(formats)}")
