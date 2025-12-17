"""
Skills Multimedia para Agentes Autonomos
=========================================

Sistema de habilidades para analise de conteudo multimidia:
- Texto (PDF, DOCX, TXT, JSON, CSV, XML, HTML, Markdown)
- Imagem (PNG, JPG, GIF, BMP, TIFF, WebP, SVG, ICO, HEIC, RAW)
- Audio (MP3, WAV, FLAC, OGG, M4A)
- Video (MP4, AVI, MKV, MOV, WEBM)
- Office (DOC, DOCX, XLS, XLSX, PPT, PPTX, ODT, ODS, ODP)

Acionamento Autonomo:
- SkillTrigger: Detecta e aciona skills automaticamente
- AutoSkillAgent: Mixin para agentes com skills automaticas
"""

from .multimedia_base import (
    MediaType,
    MediaFormat,
    AnalysisResult,
    MediaAnalyzer,
    MediaSkillRegistry
)

from .text_analysis import (
    TextAnalyzer,
    PDFAnalyzer,
    DocumentAnalyzer,
    CodeAnalyzer,
    DataFileAnalyzer
)

from .image_analysis import (
    ImageAnalyzer,
    PNGAnalyzer,
    JPEGAnalyzer,
    GIFAnalyzer,
    BMPAnalyzer,
    WebPAnalyzer,
    SVGAnalyzer,
    TIFFAnalyzer,
    ICOAnalyzer
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

from .office_analysis import (
    OfficeAnalyzer,
    DOCXAnalyzer,
    XLSXAnalyzer,
    PPTXAnalyzer,
    ODTAnalyzer,
    ODSAnalyzer,
    RTFAnalyzer
)

from .skill_trigger import (
    SkillTrigger,
    SkillTriggerContext,
    SkillTriggerResult,
    AutoSkillAgent,
    integrate_skills_with_agent
)

from .registry import (
    analyze_file,
    can_analyze,
    get_media_type,
    get_supported_formats,
    list_skills
)

__all__ = [
    # Base
    "MediaType",
    "MediaFormat",
    "AnalysisResult",
    "MediaAnalyzer",
    "MediaSkillRegistry",
    # Text
    "TextAnalyzer",
    "PDFAnalyzer",
    "DocumentAnalyzer",
    "CodeAnalyzer",
    "DataFileAnalyzer",
    # Image
    "ImageAnalyzer",
    "PNGAnalyzer",
    "JPEGAnalyzer",
    "GIFAnalyzer",
    "BMPAnalyzer",
    "WebPAnalyzer",
    "SVGAnalyzer",
    "TIFFAnalyzer",
    "ICOAnalyzer",
    # Audio
    "AudioAnalyzer",
    "SpeechAnalyzer",
    "MusicAnalyzer",
    # Video
    "VideoAnalyzer",
    "FrameAnalyzer",
    "SceneAnalyzer",
    # Office
    "OfficeAnalyzer",
    "DOCXAnalyzer",
    "XLSXAnalyzer",
    "PPTXAnalyzer",
    "ODTAnalyzer",
    "ODSAnalyzer",
    "RTFAnalyzer",
    # Skill Trigger
    "SkillTrigger",
    "SkillTriggerContext",
    "SkillTriggerResult",
    "AutoSkillAgent",
    "integrate_skills_with_agent",
    # Registry
    "analyze_file",
    "can_analyze",
    "get_media_type",
    "get_supported_formats",
    "list_skills"
]
