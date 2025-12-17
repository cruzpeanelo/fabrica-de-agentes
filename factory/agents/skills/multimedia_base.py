"""
Base para Analise Multimidia
============================

Classes base e infraestrutura para analise de diferentes tipos de midia.
"""

import json
import sqlite3
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type


class MediaType(Enum):
    """Tipos de midia suportados"""
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    DATA = "data"


class MediaFormat(Enum):
    """Formatos de arquivo suportados"""
    # Texto
    TXT = ("txt", MediaType.TEXT, "text/plain")
    PDF = ("pdf", MediaType.TEXT, "application/pdf")
    DOCX = ("docx", MediaType.TEXT, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    DOC = ("doc", MediaType.TEXT, "application/msword")
    MD = ("md", MediaType.TEXT, "text/markdown")
    HTML = ("html", MediaType.TEXT, "text/html")
    XML = ("xml", MediaType.TEXT, "application/xml")
    JSON = ("json", MediaType.DATA, "application/json")
    CSV = ("csv", MediaType.DATA, "text/csv")
    XLSX = ("xlsx", MediaType.DATA, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Codigo
    PY = ("py", MediaType.TEXT, "text/x-python")
    JS = ("js", MediaType.TEXT, "text/javascript")
    TS = ("ts", MediaType.TEXT, "text/typescript")
    JAVA = ("java", MediaType.TEXT, "text/x-java")
    CPP = ("cpp", MediaType.TEXT, "text/x-c++")
    SQL = ("sql", MediaType.TEXT, "text/x-sql")

    # Audio
    MP3 = ("mp3", MediaType.AUDIO, "audio/mpeg")
    WAV = ("wav", MediaType.AUDIO, "audio/wav")
    FLAC = ("flac", MediaType.AUDIO, "audio/flac")
    OGG = ("ogg", MediaType.AUDIO, "audio/ogg")
    M4A = ("m4a", MediaType.AUDIO, "audio/mp4")
    AAC = ("aac", MediaType.AUDIO, "audio/aac")
    WMA = ("wma", MediaType.AUDIO, "audio/x-ms-wma")

    # Video
    MP4 = ("mp4", MediaType.VIDEO, "video/mp4")
    AVI = ("avi", MediaType.VIDEO, "video/x-msvideo")
    MKV = ("mkv", MediaType.VIDEO, "video/x-matroska")
    MOV = ("mov", MediaType.VIDEO, "video/quicktime")
    WEBM = ("webm", MediaType.VIDEO, "video/webm")
    WMV = ("wmv", MediaType.VIDEO, "video/x-ms-wmv")
    FLV = ("flv", MediaType.VIDEO, "video/x-flv")

    # Imagem Raster
    PNG = ("png", MediaType.IMAGE, "image/png")
    JPG = ("jpg", MediaType.IMAGE, "image/jpeg")
    JPEG = ("jpeg", MediaType.IMAGE, "image/jpeg")
    GIF = ("gif", MediaType.IMAGE, "image/gif")
    BMP = ("bmp", MediaType.IMAGE, "image/bmp")
    WEBP = ("webp", MediaType.IMAGE, "image/webp")
    TIFF = ("tiff", MediaType.IMAGE, "image/tiff")
    TIF = ("tif", MediaType.IMAGE, "image/tiff")
    ICO = ("ico", MediaType.IMAGE, "image/x-icon")
    HEIC = ("heic", MediaType.IMAGE, "image/heic")
    HEIF = ("heif", MediaType.IMAGE, "image/heif")

    # Imagem Vetorial
    SVG = ("svg", MediaType.IMAGE, "image/svg+xml")
    EPS = ("eps", MediaType.IMAGE, "application/postscript")

    # Imagem RAW
    CR2 = ("cr2", MediaType.IMAGE, "image/x-canon-cr2")
    NEF = ("nef", MediaType.IMAGE, "image/x-nikon-nef")
    ARW = ("arw", MediaType.IMAGE, "image/x-sony-arw")
    DNG = ("dng", MediaType.IMAGE, "image/x-adobe-dng")

    # Imagem Design
    PSD = ("psd", MediaType.IMAGE, "image/vnd.adobe.photoshop")
    AI = ("ai", MediaType.IMAGE, "application/illustrator")

    # Office Documents
    XLS = ("xls", MediaType.DATA, "application/vnd.ms-excel")
    PPT = ("ppt", MediaType.TEXT, "application/vnd.ms-powerpoint")
    PPTX = ("pptx", MediaType.TEXT, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
    RTF = ("rtf", MediaType.TEXT, "application/rtf")
    ODT = ("odt", MediaType.TEXT, "application/vnd.oasis.opendocument.text")
    ODS = ("ods", MediaType.DATA, "application/vnd.oasis.opendocument.spreadsheet")
    ODP = ("odp", MediaType.TEXT, "application/vnd.oasis.opendocument.presentation")

    # Unknown
    UNKNOWN = ("unknown", MediaType.TEXT, "application/octet-stream")

    def __init__(self, extension: str, media_type: MediaType, mime_type: str):
        self.extension = extension
        self.media_type = media_type
        self.mime_type = mime_type

    @classmethod
    def from_extension(cls, ext: str) -> Optional["MediaFormat"]:
        """Obtem formato pela extensao"""
        ext = ext.lower().lstrip(".")
        for fmt in cls:
            if fmt.extension == ext:
                return fmt
        return None

    @classmethod
    def from_path(cls, path: Path) -> Optional["MediaFormat"]:
        """Obtem formato pelo caminho do arquivo"""
        return cls.from_extension(path.suffix)


@dataclass
class AnalysisResult:
    """Resultado de uma analise de midia"""
    file_path: str
    media_type: MediaType
    media_format: Optional[MediaFormat]
    success: bool

    # Metadados extraidos
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Conteudo extraido
    content: Optional[str] = None
    content_summary: Optional[str] = None

    # Analise semantica
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    sentiment: Optional[str] = None
    language: Optional[str] = None

    # Estatisticas
    stats: Dict[str, Any] = field(default_factory=dict)

    # Erros e avisos
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Contexto
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    analysis_duration_ms: int = 0
    analyzer_version: str = "1.0.0"

    def to_dict(self) -> Dict:
        """Converte para dicionario"""
        return {
            "file_path": self.file_path,
            "media_type": self.media_type.value,
            "media_format": self.media_format.extension if self.media_format else None,
            "success": self.success,
            "metadata": self.metadata,
            "content": self.content[:1000] if self.content else None,  # Trunca para armazenamento
            "content_summary": self.content_summary,
            "entities": self.entities,
            "keywords": self.keywords,
            "topics": self.topics,
            "sentiment": self.sentiment,
            "language": self.language,
            "stats": self.stats,
            "errors": self.errors,
            "warnings": self.warnings,
            "analyzed_at": self.analyzed_at,
            "analysis_duration_ms": self.analysis_duration_ms
        }


class MediaAnalyzer(ABC):
    """
    Base abstrata para analisadores de midia

    Todos os analisadores especializados devem herdar desta classe.
    """

    # Formatos suportados por este analisador
    supported_formats: List[MediaFormat] = []

    # Nome do skill associado
    skill_name: str = "media_analysis"
    skill_description: str = "Analise de midia generica"
    skill_category: str = "multimedia"

    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id
        self._analysis_count = 0
        self._success_count = 0

    def can_analyze(self, path: Path) -> bool:
        """Verifica se pode analisar o arquivo"""
        fmt = MediaFormat.from_path(path)
        return fmt in self.supported_formats if fmt else False

    @abstractmethod
    def analyze(self, path: Path, **options) -> AnalysisResult:
        """
        Analisa um arquivo

        Args:
            path: Caminho do arquivo
            **options: Opcoes especificas do analisador

        Returns:
            Resultado da analise
        """
        pass

    def extract_metadata(self, path: Path) -> Dict[str, Any]:
        """Extrai metadados basicos do arquivo"""
        stat = path.stat()
        return {
            "file_name": path.name,
            "file_size_bytes": stat.st_size,
            "file_size_human": self._format_size(stat.st_size),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix.lower(),
        }

    def _format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para humano"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extrai palavras-chave do texto"""
        import re
        from collections import Counter

        # Stopwords basicas em portugues e ingles
        stopwords = {
            "a", "o", "e", "de", "da", "do", "em", "para", "com", "um", "uma",
            "que", "os", "as", "dos", "das", "no", "na", "por", "se", "ao",
            "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "is",
            "it", "that", "this", "with", "as", "by", "be", "are", "was", "were"
        }

        # Tokeniza e normaliza
        words = re.findall(r'\b[a-zA-Z\u00C0-\u00FF]{3,}\b', text.lower())
        words = [w for w in words if w not in stopwords and len(w) > 3]

        # Conta frequencia
        counter = Counter(words)
        return [word for word, _ in counter.most_common(max_keywords)]

    def _detect_language(self, text: str) -> str:
        """Detecta idioma do texto (heuristica simples)"""
        # Palavras comuns por idioma
        pt_words = {"de", "da", "do", "em", "para", "com", "que", "uma", "os", "as"}
        en_words = {"the", "of", "and", "to", "in", "is", "that", "for", "it", "as"}
        es_words = {"de", "la", "el", "en", "que", "y", "los", "las", "por", "con"}

        words = set(text.lower().split())

        pt_score = len(words & pt_words)
        en_score = len(words & en_words)
        es_score = len(words & es_words)

        scores = {"pt": pt_score, "en": en_score, "es": es_score}
        return max(scores, key=scores.get)

    def _simple_sentiment(self, text: str) -> str:
        """Analise de sentimento simplificada"""
        positive = {
            "bom", "otimo", "excelente", "perfeito", "maravilhoso", "fantastico",
            "good", "great", "excellent", "perfect", "wonderful", "amazing",
            "love", "like", "happy", "success", "sucesso", "feliz"
        }
        negative = {
            "ruim", "pessimo", "terrivel", "horrivel", "mau", "falha",
            "bad", "terrible", "horrible", "awful", "fail", "error", "erro",
            "hate", "dislike", "sad", "triste", "problema", "problem"
        }

        words = set(text.lower().split())
        pos_score = len(words & positive)
        neg_score = len(words & negative)

        if pos_score > neg_score * 1.5:
            return "positive"
        elif neg_score > pos_score * 1.5:
            return "negative"
        return "neutral"

    def get_stats(self) -> Dict:
        """Retorna estatisticas do analisador"""
        return {
            "total_analyses": self._analysis_count,
            "successful": self._success_count,
            "success_rate": self._success_count / self._analysis_count if self._analysis_count > 0 else 0,
            "supported_formats": [f.extension for f in self.supported_formats]
        }


class MediaSkillRegistry:
    """
    Registro central de skills de analise de midia

    Gerencia analisadores disponiveis e integra com sistema de skills.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("factory/database/media_skills.db")
        self._analyzers: Dict[str, Type[MediaAnalyzer]] = {}
        self._instances: Dict[str, MediaAnalyzer] = {}
        self._init_database()

    def _init_database(self):
        """Inicializa banco de dados"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)

        # Tabela de analises realizadas
        conn.execute("""
            CREATE TABLE IF NOT EXISTS media_analyses (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                media_type TEXT,
                media_format TEXT,
                analyzer_name TEXT,
                agent_id TEXT,
                success INTEGER,
                result_json TEXT,
                analyzed_at TEXT,
                duration_ms INTEGER
            )
        """)

        # Tabela de skills de midia
        conn.execute("""
            CREATE TABLE IF NOT EXISTS media_skills (
                id TEXT PRIMARY KEY,
                skill_name TEXT UNIQUE NOT NULL,
                skill_description TEXT,
                skill_category TEXT,
                supported_formats TEXT,
                analyzer_class TEXT,
                registered_at TEXT
            )
        """)

        # Indices
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_file ON media_analyses(file_path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_type ON media_analyses(media_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_agent ON media_analyses(agent_id)")

        conn.commit()
        conn.close()

    def register_analyzer(self, analyzer_class: Type[MediaAnalyzer]):
        """
        Registra um analisador

        Args:
            analyzer_class: Classe do analisador
        """
        name = analyzer_class.skill_name
        self._analyzers[name] = analyzer_class

        # Persiste no banco
        conn = sqlite3.connect(self.db_path)

        skill_id = hashlib.sha256(name.encode()).hexdigest()[:12]

        conn.execute("""
            INSERT OR REPLACE INTO media_skills
            (id, skill_name, skill_description, skill_category, supported_formats, analyzer_class, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            skill_id,
            name,
            analyzer_class.skill_description,
            analyzer_class.skill_category,
            json.dumps([f.extension for f in analyzer_class.supported_formats]),
            analyzer_class.__name__,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def get_analyzer(self, skill_name: str, agent_id: Optional[str] = None) -> Optional[MediaAnalyzer]:
        """
        Obtem instancia de analisador

        Args:
            skill_name: Nome do skill
            agent_id: ID do agente (opcional)

        Returns:
            Instancia do analisador
        """
        if skill_name not in self._analyzers:
            return None

        key = f"{skill_name}_{agent_id or 'default'}"

        if key not in self._instances:
            self._instances[key] = self._analyzers[skill_name](agent_id=agent_id)

        return self._instances[key]

    def get_analyzer_for_file(self, path: Path, agent_id: Optional[str] = None) -> Optional[MediaAnalyzer]:
        """
        Encontra analisador apropriado para um arquivo

        Args:
            path: Caminho do arquivo
            agent_id: ID do agente

        Returns:
            Analisador que suporta o formato
        """
        fmt = MediaFormat.from_path(path)
        if not fmt:
            return None

        for name, analyzer_class in self._analyzers.items():
            if fmt in analyzer_class.supported_formats:
                return self.get_analyzer(name, agent_id)

        return None

    def analyze_file(self, path: Path, agent_id: Optional[str] = None, **options) -> Optional[AnalysisResult]:
        """
        Analisa um arquivo automaticamente

        Args:
            path: Caminho do arquivo
            agent_id: ID do agente
            **options: Opcoes de analise

        Returns:
            Resultado da analise
        """
        path = Path(path)

        if not path.exists():
            return AnalysisResult(
                file_path=str(path),
                media_type=MediaType.TEXT,
                media_format=None,
                success=False,
                errors=[f"Arquivo nao encontrado: {path}"]
            )

        analyzer = self.get_analyzer_for_file(path, agent_id)

        if not analyzer:
            fmt = MediaFormat.from_path(path)
            return AnalysisResult(
                file_path=str(path),
                media_type=fmt.media_type if fmt else MediaType.TEXT,
                media_format=fmt,
                success=False,
                errors=[f"Nenhum analisador disponivel para formato: {path.suffix}"]
            )

        # Executa analise
        import time
        start = time.time()
        result = analyzer.analyze(path, **options)
        result.analysis_duration_ms = int((time.time() - start) * 1000)

        # Persiste resultado
        self._save_analysis(result, analyzer, agent_id)

        return result

    def _save_analysis(self, result: AnalysisResult, analyzer: MediaAnalyzer, agent_id: Optional[str]):
        """Salva resultado da analise"""
        conn = sqlite3.connect(self.db_path)

        analysis_id = hashlib.sha256(
            f"{result.file_path}_{result.analyzed_at}".encode()
        ).hexdigest()[:16]

        # Hash do arquivo para cache
        file_hash = None
        try:
            with open(result.file_path, "rb") as f:
                file_hash = hashlib.md5(f.read(8192)).hexdigest()
        except:
            pass

        conn.execute("""
            INSERT INTO media_analyses
            (id, file_path, file_hash, media_type, media_format, analyzer_name, agent_id, success, result_json, analyzed_at, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis_id,
            result.file_path,
            file_hash,
            result.media_type.value,
            result.media_format.extension if result.media_format else None,
            analyzer.skill_name,
            agent_id,
            1 if result.success else 0,
            json.dumps(result.to_dict()),
            result.analyzed_at,
            result.analysis_duration_ms
        ))

        conn.commit()
        conn.close()

    def get_analysis_history(self,
                           agent_id: Optional[str] = None,
                           media_type: Optional[MediaType] = None,
                           limit: int = 100) -> List[Dict]:
        """Retorna historico de analises"""
        conn = sqlite3.connect(self.db_path)

        query = "SELECT * FROM media_analyses WHERE 1=1"
        params = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        if media_type:
            query += " AND media_type = ?"
            params.append(media_type.value)

        query += " ORDER BY analyzed_at DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "file_path": row[1],
                "media_type": row[3],
                "media_format": row[4],
                "analyzer": row[5],
                "agent_id": row[6],
                "success": bool(row[7]),
                "analyzed_at": row[9],
                "duration_ms": row[10]
            })

        conn.close()
        return results

    def list_skills(self) -> List[Dict]:
        """Lista todas as skills de midia registradas"""
        conn = sqlite3.connect(self.db_path)

        cursor = conn.execute("SELECT * FROM media_skills ORDER BY skill_name")

        skills = []
        for row in cursor.fetchall():
            skills.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "category": row[3],
                "formats": json.loads(row[4]) if row[4] else [],
                "analyzer_class": row[5]
            })

        conn.close()
        return skills

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Retorna formatos suportados por tipo de midia"""
        formats = {
            MediaType.TEXT.value: [],
            MediaType.AUDIO.value: [],
            MediaType.VIDEO.value: [],
            MediaType.IMAGE.value: [],
            MediaType.DATA.value: []
        }

        for analyzer_class in self._analyzers.values():
            for fmt in analyzer_class.supported_formats:
                if fmt.extension not in formats[fmt.media_type.value]:
                    formats[fmt.media_type.value].append(fmt.extension)

        return formats
