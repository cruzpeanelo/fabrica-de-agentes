"""
Analise de Texto e Documentos
=============================

Skills para analise de diferentes formatos de texto:
- PDF (Portable Document Format)
- DOCX/DOC (Microsoft Word)
- TXT (Texto puro)
- MD (Markdown)
- HTML (HyperText Markup Language)
- XML (eXtensible Markup Language)
- JSON (JavaScript Object Notation)
- CSV (Comma-Separated Values)
- Codigo fonte (Python, JavaScript, Java, etc.)
"""

import csv
import json
import re
import struct
import zlib
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree

from .multimedia_base import (
    AnalysisResult,
    MediaAnalyzer,
    MediaFormat,
    MediaType
)


@dataclass
class TextStats:
    """Estatisticas de texto"""
    char_count: int = 0
    word_count: int = 0
    line_count: int = 0
    paragraph_count: int = 0
    sentence_count: int = 0
    avg_word_length: float = 0.0
    avg_sentence_length: float = 0.0
    unique_words: int = 0
    vocabulary_richness: float = 0.0


class TextAnalyzer(MediaAnalyzer):
    """
    Analisador de texto puro

    Analisa arquivos TXT, MD e outros formatos de texto simples.
    """

    supported_formats = [MediaFormat.TXT, MediaFormat.MD]
    skill_name = "text_analysis"
    skill_description = "Analise de arquivos de texto puro e Markdown"
    skill_category = "text"

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa arquivo de texto"""
        path = Path(path)

        result = AnalysisResult(
            file_path=str(path),
            media_type=MediaType.TEXT,
            media_format=MediaFormat.from_path(path),
            success=False
        )

        try:
            # Extrai metadados basicos
            result.metadata = self.extract_metadata(path)

            # Le conteudo
            encoding = options.get("encoding", "utf-8")
            try:
                content = path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                # Tenta latin-1 como fallback
                content = path.read_text(encoding="latin-1")
                result.warnings.append("Arquivo lido com encoding latin-1 (fallback)")

            result.content = content

            # Calcula estatisticas
            stats = self._calculate_stats(content)
            result.stats = {
                "char_count": stats.char_count,
                "word_count": stats.word_count,
                "line_count": stats.line_count,
                "paragraph_count": stats.paragraph_count,
                "sentence_count": stats.sentence_count,
                "avg_word_length": round(stats.avg_word_length, 2),
                "avg_sentence_length": round(stats.avg_sentence_length, 2),
                "unique_words": stats.unique_words,
                "vocabulary_richness": round(stats.vocabulary_richness, 3)
            }

            # Extrai keywords
            result.keywords = self._extract_keywords(content)

            # Detecta idioma
            result.language = self._detect_language(content)

            # Analise de sentimento
            result.sentiment = self._simple_sentiment(content)

            # Para Markdown, extrai estrutura
            if result.media_format == MediaFormat.MD:
                result.metadata["markdown_structure"] = self._parse_markdown_structure(content)

            # Gera resumo
            result.content_summary = self._generate_summary(content)

            result.success = True
            self._success_count += 1

        except Exception as e:
            result.errors.append(f"Erro ao analisar texto: {str(e)}")

        self._analysis_count += 1
        return result

    def _calculate_stats(self, text: str) -> TextStats:
        """Calcula estatisticas do texto"""
        stats = TextStats()

        stats.char_count = len(text)
        stats.line_count = text.count('\n') + 1
        stats.paragraph_count = len(re.split(r'\n\s*\n', text))

        # Palavras
        words = re.findall(r'\b\w+\b', text)
        stats.word_count = len(words)

        if words:
            stats.avg_word_length = sum(len(w) for w in words) / len(words)
            unique = set(w.lower() for w in words)
            stats.unique_words = len(unique)
            stats.vocabulary_richness = stats.unique_words / stats.word_count

        # Sentencas
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        stats.sentence_count = len(sentences)

        if sentences:
            stats.avg_sentence_length = stats.word_count / stats.sentence_count

        return stats

    def _parse_markdown_structure(self, content: str) -> Dict:
        """Extrai estrutura do Markdown"""
        structure = {
            "headers": [],
            "links": [],
            "code_blocks": [],
            "images": [],
            "lists": 0
        }

        # Headers
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            structure["headers"].append({
                "level": len(match.group(1)),
                "text": match.group(2)
            })

        # Links
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
            structure["links"].append({
                "text": match.group(1),
                "url": match.group(2)
            })

        # Code blocks
        for match in re.finditer(r'```(\w*)\n(.*?)```', content, re.DOTALL):
            structure["code_blocks"].append({
                "language": match.group(1) or "text",
                "lines": len(match.group(2).split('\n'))
            })

        # Images
        for match in re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', content):
            structure["images"].append({
                "alt": match.group(1),
                "src": match.group(2)
            })

        # Lists
        structure["lists"] = len(re.findall(r'^[\s]*[-*+]\s', content, re.MULTILINE))
        structure["lists"] += len(re.findall(r'^[\s]*\d+\.\s', content, re.MULTILINE))

        return structure

    def _generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """Gera resumo do texto"""
        # Divide em sentencas
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if not sentences:
            return text[:200] + "..." if len(text) > 200 else text

        # Pega as primeiras sentencas
        summary = ' '.join(sentences[:max_sentences])

        if len(summary) > 500:
            summary = summary[:500] + "..."

        return summary


class PDFAnalyzer(MediaAnalyzer):
    """
    Analisador de PDF

    Extrai texto e metadados de arquivos PDF sem dependencias externas.
    Usa parsing direto da estrutura PDF.
    """

    supported_formats = [MediaFormat.PDF]
    skill_name = "pdf_analysis"
    skill_description = "Analise de documentos PDF (extrai texto e metadados)"
    skill_category = "text"

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa arquivo PDF"""
        path = Path(path)

        result = AnalysisResult(
            file_path=str(path),
            media_type=MediaType.TEXT,
            media_format=MediaFormat.PDF,
            success=False
        )

        try:
            result.metadata = self.extract_metadata(path)

            with open(path, 'rb') as f:
                pdf_data = f.read()

            # Extrai metadados do PDF
            pdf_meta = self._extract_pdf_metadata(pdf_data)
            result.metadata.update(pdf_meta)

            # Extrai texto
            text = self._extract_text_from_pdf(pdf_data)

            if text:
                result.content = text
                result.keywords = self._extract_keywords(text)
                result.language = self._detect_language(text)
                result.sentiment = self._simple_sentiment(text)
                result.content_summary = self._generate_summary(text)

                # Estatisticas
                result.stats = {
                    "char_count": len(text),
                    "word_count": len(text.split()),
                    "pages": pdf_meta.get("page_count", 0)
                }
            else:
                result.warnings.append("Nao foi possivel extrair texto do PDF")

            result.success = True
            self._success_count += 1

        except Exception as e:
            result.errors.append(f"Erro ao analisar PDF: {str(e)}")

        self._analysis_count += 1
        return result

    def _extract_pdf_metadata(self, pdf_data: bytes) -> Dict:
        """Extrai metadados do PDF"""
        metadata = {}

        try:
            # Busca Info dictionary
            info_match = re.search(rb'/Info\s*(\d+)\s+\d+\s+R', pdf_data)
            if info_match:
                obj_num = info_match.group(1).decode()
                obj_pattern = rf'{obj_num}\s+\d+\s+obj.*?endobj'
                obj_match = re.search(obj_pattern.encode(), pdf_data, re.DOTALL)

                if obj_match:
                    obj_data = obj_match.group(0).decode('latin-1', errors='ignore')

                    # Extrai campos comuns
                    fields = {
                        'Title': 'title',
                        'Author': 'author',
                        'Subject': 'subject',
                        'Creator': 'creator',
                        'Producer': 'producer',
                        'CreationDate': 'created',
                        'ModDate': 'modified'
                    }

                    for pdf_field, meta_field in fields.items():
                        match = re.search(rf'/{pdf_field}\s*\(([^)]*)\)', obj_data)
                        if match:
                            metadata[meta_field] = match.group(1)

            # Conta paginas
            page_count = len(re.findall(rb'/Type\s*/Page[^s]', pdf_data))
            metadata['page_count'] = page_count

            # Versao do PDF
            version_match = re.match(rb'%PDF-(\d+\.\d+)', pdf_data)
            if version_match:
                metadata['pdf_version'] = version_match.group(1).decode()

        except Exception:
            pass

        return metadata

    def _extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extrai texto do PDF"""
        text_parts = []

        try:
            # Procura por streams de conteudo
            stream_pattern = rb'stream\r?\n(.*?)\r?\nendstream'

            for match in re.finditer(stream_pattern, pdf_data, re.DOTALL):
                stream_data = match.group(1)

                # Tenta descomprimir se for FlateDecode
                try:
                    if b'/FlateDecode' in pdf_data[max(0, match.start()-200):match.start()]:
                        stream_data = zlib.decompress(stream_data)
                except:
                    pass

                # Extrai texto dos operadores de texto
                text = self._extract_text_from_stream(stream_data)
                if text:
                    text_parts.append(text)

            # Tambem busca texto literal
            for match in re.finditer(rb'\(([^)]+)\)\s*Tj', pdf_data):
                try:
                    text_parts.append(match.group(1).decode('latin-1', errors='ignore'))
                except:
                    pass

        except Exception:
            pass

        return '\n'.join(text_parts)

    def _extract_text_from_stream(self, stream: bytes) -> str:
        """Extrai texto de um stream de conteudo"""
        text_parts = []

        try:
            stream_str = stream.decode('latin-1', errors='ignore')

            # Texto entre parenteses antes de Tj/TJ
            for match in re.finditer(r'\(([^)]*)\)\s*T[jJ]', stream_str):
                text_parts.append(match.group(1))

            # Arrays de texto (TJ operator)
            for match in re.finditer(r'\[(.*?)\]\s*TJ', stream_str, re.DOTALL):
                array_content = match.group(1)
                for text_match in re.finditer(r'\(([^)]*)\)', array_content):
                    text_parts.append(text_match.group(1))

        except:
            pass

        return ' '.join(text_parts)

    def _generate_summary(self, text: str, max_length: int = 500) -> str:
        """Gera resumo do texto"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) > max_length:
                break
            summary += sentence + " "

        return summary.strip() or text[:max_length]


class DocumentAnalyzer(MediaAnalyzer):
    """
    Analisador de Documentos Office

    Analisa DOCX, HTML e XML.
    """

    supported_formats = [MediaFormat.DOCX, MediaFormat.HTML, MediaFormat.XML]
    skill_name = "document_analysis"
    skill_description = "Analise de documentos Office (DOCX), HTML e XML"
    skill_category = "text"

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa documento"""
        path = Path(path)
        fmt = MediaFormat.from_path(path)

        result = AnalysisResult(
            file_path=str(path),
            media_type=MediaType.TEXT,
            media_format=fmt,
            success=False
        )

        try:
            result.metadata = self.extract_metadata(path)

            if fmt == MediaFormat.DOCX:
                text, doc_meta = self._analyze_docx(path)
                result.metadata.update(doc_meta)
            elif fmt == MediaFormat.HTML:
                text, html_meta = self._analyze_html(path)
                result.metadata.update(html_meta)
            elif fmt == MediaFormat.XML:
                text, xml_meta = self._analyze_xml(path)
                result.metadata.update(xml_meta)
            else:
                text = path.read_text(errors='ignore')

            result.content = text

            if text:
                result.keywords = self._extract_keywords(text)
                result.language = self._detect_language(text)
                result.sentiment = self._simple_sentiment(text)

                result.stats = {
                    "char_count": len(text),
                    "word_count": len(text.split()),
                    "line_count": text.count('\n') + 1
                }

            result.success = True
            self._success_count += 1

        except Exception as e:
            result.errors.append(f"Erro ao analisar documento: {str(e)}")

        self._analysis_count += 1
        return result

    def _analyze_docx(self, path: Path) -> Tuple[str, Dict]:
        """Analisa arquivo DOCX"""
        import zipfile

        text_parts = []
        metadata = {}

        try:
            with zipfile.ZipFile(path, 'r') as docx:
                # Extrai texto do document.xml
                if 'word/document.xml' in docx.namelist():
                    with docx.open('word/document.xml') as doc:
                        tree = ElementTree.parse(doc)
                        root = tree.getroot()

                        # Namespace do Word
                        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

                        # Extrai texto de todos os paragrafos
                        for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                            para_text = ''.join(
                                node.text or ''
                                for node in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                            )
                            if para_text:
                                text_parts.append(para_text)

                # Extrai metadados do core.xml
                if 'docProps/core.xml' in docx.namelist():
                    with docx.open('docProps/core.xml') as core:
                        tree = ElementTree.parse(core)
                        root = tree.getroot()

                        # Namespaces do Dublin Core
                        namespaces = {
                            'dc': 'http://purl.org/dc/elements/1.1/',
                            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'
                        }

                        for prefix, ns in namespaces.items():
                            for child in root:
                                if child.tag.startswith('{' + ns + '}'):
                                    key = child.tag.split('}')[1]
                                    if child.text:
                                        metadata[key] = child.text

        except Exception:
            pass

        return '\n'.join(text_parts), metadata

    def _analyze_html(self, path: Path) -> Tuple[str, Dict]:
        """Analisa arquivo HTML"""
        content = path.read_text(errors='ignore')
        metadata = {}

        # Extrai titulo
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            metadata['title'] = title_match.group(1)

        # Extrai meta tags
        for match in re.finditer(r'<meta\s+name=["\'](\w+)["\']\s+content=["\']([^"\']+)["\']', content, re.IGNORECASE):
            metadata[f'meta_{match.group(1)}'] = match.group(2)

        # Remove tags e scripts
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # Estrutura do HTML
        metadata['structure'] = {
            'headings': len(re.findall(r'<h[1-6][^>]*>', content, re.IGNORECASE)),
            'paragraphs': len(re.findall(r'<p[^>]*>', content, re.IGNORECASE)),
            'links': len(re.findall(r'<a[^>]*>', content, re.IGNORECASE)),
            'images': len(re.findall(r'<img[^>]*>', content, re.IGNORECASE)),
            'forms': len(re.findall(r'<form[^>]*>', content, re.IGNORECASE))
        }

        return text, metadata

    def _analyze_xml(self, path: Path) -> Tuple[str, Dict]:
        """Analisa arquivo XML"""
        content = path.read_text(errors='ignore')
        metadata = {}

        try:
            tree = ElementTree.parse(path)
            root = tree.getroot()

            metadata['root_tag'] = root.tag
            metadata['attributes'] = dict(root.attrib)

            # Conta elementos
            elements = {}
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                elements[tag] = elements.get(tag, 0) + 1

            metadata['element_counts'] = elements
            metadata['total_elements'] = sum(elements.values())

            # Extrai texto
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())

            return '\n'.join(text_parts), metadata

        except ElementTree.ParseError as e:
            metadata['parse_error'] = str(e)
            # Fallback: remove tags
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            return text, metadata


class CodeAnalyzer(MediaAnalyzer):
    """
    Analisador de Codigo Fonte

    Analisa Python, JavaScript, TypeScript, Java, C++, SQL.
    """

    supported_formats = [
        MediaFormat.PY,
        MediaFormat.JS,
        MediaFormat.TS,
        MediaFormat.JAVA,
        MediaFormat.CPP,
        MediaFormat.SQL
    ]
    skill_name = "code_analysis"
    skill_description = "Analise de codigo fonte (Python, JavaScript, Java, etc.)"
    skill_category = "text"

    # Padroes para cada linguagem
    PATTERNS = {
        "py": {
            "function": r'def\s+(\w+)\s*\(',
            "class": r'class\s+(\w+)',
            "import": r'^(?:from\s+\S+\s+)?import\s+(.+)$',
            "comment": r'#.*$|\'\'\'[\s\S]*?\'\'\'|"""[\s\S]*?"""',
            "decorator": r'@\w+'
        },
        "js": {
            "function": r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))',
            "class": r'class\s+(\w+)',
            "import": r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            "comment": r'//.*$|/\*[\s\S]*?\*/',
            "async": r'async\s+\w+'
        },
        "ts": {
            "function": r'(?:function\s+(\w+)|(?:const|let)\s+(\w+)\s*(?::\s*\w+)?\s*=)',
            "class": r'class\s+(\w+)',
            "interface": r'interface\s+(\w+)',
            "type": r'type\s+(\w+)\s*=',
            "import": r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            "comment": r'//.*$|/\*[\s\S]*?\*/'
        },
        "java": {
            "class": r'(?:public|private|protected)?\s*class\s+(\w+)',
            "method": r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\(',
            "interface": r'interface\s+(\w+)',
            "import": r'import\s+([\w.]+);',
            "comment": r'//.*$|/\*[\s\S]*?\*/'
        },
        "cpp": {
            "class": r'class\s+(\w+)',
            "function": r'(?:\w+\s+)+(\w+)\s*\([^)]*\)\s*(?:const)?\s*\{',
            "include": r'#include\s*[<"]([^>"]+)[>"]',
            "comment": r'//.*$|/\*[\s\S]*?\*/'
        },
        "sql": {
            "select": r'SELECT\s+.*?\s+FROM\s+(\w+)',
            "table": r'(?:CREATE|ALTER)\s+TABLE\s+(\w+)',
            "insert": r'INSERT\s+INTO\s+(\w+)',
            "procedure": r'CREATE\s+PROCEDURE\s+(\w+)',
            "comment": r'--.*$|/\*[\s\S]*?\*/'
        }
    }

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa codigo fonte"""
        path = Path(path)
        fmt = MediaFormat.from_path(path)

        result = AnalysisResult(
            file_path=str(path),
            media_type=MediaType.TEXT,
            media_format=fmt,
            success=False
        )

        try:
            result.metadata = self.extract_metadata(path)
            content = path.read_text(errors='ignore')
            result.content = content

            # Identifica linguagem
            lang = fmt.extension if fmt else path.suffix.lstrip('.')
            patterns = self.PATTERNS.get(lang, {})

            # Analise especifica da linguagem
            code_analysis = self._analyze_code(content, patterns, lang)
            result.metadata['code_analysis'] = code_analysis

            # Estatisticas
            lines = content.split('\n')
            code_lines = [l for l in lines if l.strip() and not self._is_comment(l, lang)]
            comment_lines = [l for l in lines if self._is_comment(l, lang)]
            blank_lines = [l for l in lines if not l.strip()]

            result.stats = {
                "total_lines": len(lines),
                "code_lines": len(code_lines),
                "comment_lines": len(comment_lines),
                "blank_lines": len(blank_lines),
                "comment_ratio": round(len(comment_lines) / max(len(code_lines), 1), 2),
                "language": lang,
                "functions": len(code_analysis.get('functions', [])),
                "classes": len(code_analysis.get('classes', [])),
                "imports": len(code_analysis.get('imports', []))
            }

            # Complexidade ciclomatica simplificada
            complexity = self._estimate_complexity(content, lang)
            result.stats['estimated_complexity'] = complexity

            # Keywords de programacao
            result.keywords = self._extract_code_keywords(content, lang)

            result.success = True
            self._success_count += 1

        except Exception as e:
            result.errors.append(f"Erro ao analisar codigo: {str(e)}")

        self._analysis_count += 1
        return result

    def _analyze_code(self, content: str, patterns: Dict, lang: str) -> Dict:
        """Analisa estrutura do codigo"""
        analysis = {
            "functions": [],
            "classes": [],
            "imports": [],
            "other": {}
        }

        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, content, re.MULTILINE)

            # Flatten matches se forem tuplas (grupos de captura)
            flat_matches = []
            for m in matches:
                if isinstance(m, tuple):
                    flat_matches.extend([x for x in m if x])
                else:
                    flat_matches.append(m)

            if pattern_name in ['function', 'method']:
                analysis['functions'].extend(flat_matches[:20])  # Limita
            elif pattern_name in ['class', 'interface']:
                analysis['classes'].extend(flat_matches)
            elif pattern_name in ['import', 'include']:
                analysis['imports'].extend(flat_matches[:30])
            else:
                analysis['other'][pattern_name] = len(flat_matches)

        return analysis

    def _is_comment(self, line: str, lang: str) -> bool:
        """Verifica se linha e comentario"""
        line = line.strip()
        if not line:
            return False

        comment_starts = {
            'py': ['#'],
            'js': ['//', '/*', '*'],
            'ts': ['//', '/*', '*'],
            'java': ['//', '/*', '*'],
            'cpp': ['//', '/*', '*'],
            'sql': ['--', '/*', '*']
        }

        for start in comment_starts.get(lang, ['#', '//']):
            if line.startswith(start):
                return True
        return False

    def _estimate_complexity(self, content: str, lang: str) -> str:
        """Estima complexidade do codigo"""
        # Conta estruturas de controle
        control_patterns = [
            r'\bif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b',
            r'\bswitch\b', r'\bcase\b', r'\btry\b', r'\bcatch\b',
            r'\band\b', r'\bor\b', r'\b\|\|\b', r'\b&&\b'
        ]

        complexity = 1  # Base
        for pattern in control_patterns:
            complexity += len(re.findall(pattern, content))

        if complexity < 10:
            return "low"
        elif complexity < 30:
            return "medium"
        elif complexity < 50:
            return "high"
        else:
            return "very_high"

    def _extract_code_keywords(self, content: str, lang: str) -> List[str]:
        """Extrai palavras-chave do codigo"""
        # Remove strings e comentarios
        content = re.sub(r'["\'].*?["\']', '', content)
        content = re.sub(r'//.*$|#.*$|--.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Extrai identificadores
        identifiers = re.findall(r'\b[a-zA-Z_]\w{2,}\b', content)

        # Filtra palavras reservadas comuns
        reserved = {
            'def', 'class', 'return', 'import', 'from', 'if', 'else', 'for',
            'while', 'try', 'except', 'function', 'const', 'let', 'var',
            'public', 'private', 'static', 'void', 'int', 'string', 'boolean',
            'true', 'false', 'null', 'none', 'self', 'this', 'new', 'async',
            'await', 'select', 'from', 'where', 'and', 'not', 'with'
        }

        from collections import Counter
        counts = Counter(id.lower() for id in identifiers if id.lower() not in reserved)

        return [word for word, _ in counts.most_common(15)]


class DataFileAnalyzer(MediaAnalyzer):
    """
    Analisador de Arquivos de Dados

    Analisa JSON, CSV e XLSX.
    """

    supported_formats = [MediaFormat.JSON, MediaFormat.CSV, MediaFormat.XLSX]
    skill_name = "data_analysis"
    skill_description = "Analise de arquivos de dados (JSON, CSV, Excel)"
    skill_category = "data"

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa arquivo de dados"""
        path = Path(path)
        fmt = MediaFormat.from_path(path)

        result = AnalysisResult(
            file_path=str(path),
            media_type=MediaType.DATA,
            media_format=fmt,
            success=False
        )

        try:
            result.metadata = self.extract_metadata(path)

            if fmt == MediaFormat.JSON:
                data, meta = self._analyze_json(path)
            elif fmt == MediaFormat.CSV:
                data, meta = self._analyze_csv(path)
            elif fmt == MediaFormat.XLSX:
                data, meta = self._analyze_xlsx(path)
            else:
                raise ValueError(f"Formato nao suportado: {fmt}")

            result.metadata.update(meta)
            result.stats = meta.get('stats', {})

            # Gera resumo do conteudo
            if data:
                result.content_summary = self._generate_data_summary(data, fmt)

            result.success = True
            self._success_count += 1

        except Exception as e:
            result.errors.append(f"Erro ao analisar dados: {str(e)}")

        self._analysis_count += 1
        return result

    def _analyze_json(self, path: Path) -> Tuple[Any, Dict]:
        """Analisa arquivo JSON"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        metadata = {
            "type": type(data).__name__,
            "stats": {}
        }

        if isinstance(data, dict):
            metadata['stats']['keys'] = list(data.keys())[:20]
            metadata['stats']['key_count'] = len(data)
            metadata['schema'] = self._infer_json_schema(data)

        elif isinstance(data, list):
            metadata['stats']['length'] = len(data)
            if data and isinstance(data[0], dict):
                metadata['stats']['sample_keys'] = list(data[0].keys())[:20]
                metadata['schema'] = self._infer_json_schema(data[0])

        return data, metadata

    def _analyze_csv(self, path: Path) -> Tuple[List, Dict]:
        """Analisa arquivo CSV"""
        rows = []
        metadata = {"stats": {}}

        # Detecta delimitador
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(4096)
            try:
                dialect = csv.Sniffer().sniff(sample)
                delimiter = dialect.delimiter
            except:
                delimiter = ','

        with open(path, 'r', encoding='utf-8', errors='ignore', newline='') as f:
            reader = csv.reader(f, delimiter=delimiter)

            # Header
            try:
                header = next(reader)
                metadata['columns'] = header
                metadata['stats']['column_count'] = len(header)
            except StopIteration:
                return [], metadata

            # Conta linhas e coleta amostra
            for i, row in enumerate(reader):
                if i < 100:  # Amostra
                    rows.append(row)

            metadata['stats']['row_count'] = i + 1 if 'i' in dir() else 0

        # Analisa tipos de colunas
        if rows and metadata.get('columns'):
            column_types = {}
            for col_idx, col_name in enumerate(metadata['columns']):
                values = [row[col_idx] for row in rows if col_idx < len(row)]
                column_types[col_name] = self._infer_column_type(values)
            metadata['column_types'] = column_types

        return rows, metadata

    def _analyze_xlsx(self, path: Path) -> Tuple[List, Dict]:
        """Analisa arquivo Excel (XLSX)"""
        import zipfile

        metadata = {"stats": {}, "sheets": []}
        data = []

        try:
            with zipfile.ZipFile(path, 'r') as xlsx:
                # Lista de planilhas
                if 'xl/workbook.xml' in xlsx.namelist():
                    with xlsx.open('xl/workbook.xml') as f:
                        tree = ElementTree.parse(f)
                        root = tree.getroot()

                        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                        for sheet in root.findall('.//main:sheet', ns):
                            metadata['sheets'].append(sheet.get('name'))

                metadata['stats']['sheet_count'] = len(metadata['sheets'])

                # Le strings compartilhadas
                shared_strings = []
                if 'xl/sharedStrings.xml' in xlsx.namelist():
                    with xlsx.open('xl/sharedStrings.xml') as f:
                        tree = ElementTree.parse(f)
                        root = tree.getroot()
                        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                        for si in root.findall('.//main:t', ns):
                            shared_strings.append(si.text or '')

                # Le primeira planilha
                if 'xl/worksheets/sheet1.xml' in xlsx.namelist():
                    with xlsx.open('xl/worksheets/sheet1.xml') as f:
                        tree = ElementTree.parse(f)
                        root = tree.getroot()
                        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

                        rows = root.findall('.//main:row', ns)
                        metadata['stats']['row_count'] = len(rows)

                        # Extrai header da primeira linha
                        if rows:
                            header = []
                            for cell in rows[0].findall('.//main:c', ns):
                                value = cell.find('main:v', ns)
                                if value is not None:
                                    # Verifica se e string compartilhada
                                    if cell.get('t') == 's':
                                        idx = int(value.text) if value.text else 0
                                        header.append(shared_strings[idx] if idx < len(shared_strings) else '')
                                    else:
                                        header.append(value.text or '')

                            metadata['columns'] = header
                            metadata['stats']['column_count'] = len(header)

        except Exception as e:
            metadata['parse_error'] = str(e)

        return data, metadata

    def _infer_json_schema(self, obj: Any, max_depth: int = 3) -> Dict:
        """Infere schema de objeto JSON"""
        if max_depth <= 0:
            return {"type": "any"}

        if obj is None:
            return {"type": "null"}
        elif isinstance(obj, bool):
            return {"type": "boolean"}
        elif isinstance(obj, int):
            return {"type": "integer"}
        elif isinstance(obj, float):
            return {"type": "number"}
        elif isinstance(obj, str):
            return {"type": "string"}
        elif isinstance(obj, list):
            if not obj:
                return {"type": "array", "items": {"type": "any"}}
            return {"type": "array", "items": self._infer_json_schema(obj[0], max_depth - 1)}
        elif isinstance(obj, dict):
            properties = {}
            for key, value in list(obj.items())[:10]:  # Limita propriedades
                properties[key] = self._infer_json_schema(value, max_depth - 1)
            return {"type": "object", "properties": properties}
        else:
            return {"type": "unknown"}

    def _infer_column_type(self, values: List[str]) -> str:
        """Infere tipo de coluna baseado nos valores"""
        non_empty = [v for v in values if v]
        if not non_empty:
            return "empty"

        # Tenta tipos em ordem
        int_count = 0
        float_count = 0
        date_count = 0

        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}',
            r'^\d{2}/\d{2}/\d{4}',
            r'^\d{2}-\d{2}-\d{4}'
        ]

        for v in non_empty:
            try:
                int(v)
                int_count += 1
                continue
            except:
                pass

            try:
                float(v.replace(',', '.'))
                float_count += 1
                continue
            except:
                pass

            for pattern in date_patterns:
                if re.match(pattern, v):
                    date_count += 1
                    break

        threshold = len(non_empty) * 0.8

        if int_count >= threshold:
            return "integer"
        elif float_count >= threshold or int_count + float_count >= threshold:
            return "number"
        elif date_count >= threshold:
            return "date"
        else:
            return "string"

    def _generate_data_summary(self, data: Any, fmt: MediaFormat) -> str:
        """Gera resumo dos dados"""
        if fmt == MediaFormat.JSON:
            if isinstance(data, dict):
                return f"Objeto JSON com {len(data)} chaves: {list(data.keys())[:5]}"
            elif isinstance(data, list):
                return f"Array JSON com {len(data)} elementos"

        elif fmt == MediaFormat.CSV:
            return f"CSV com {len(data)} linhas analisadas"

        elif fmt == MediaFormat.XLSX:
            return "Planilha Excel analisada"

        return "Dados estruturados analisados"
