"""
Office Document Analysis Skills - Analise de Documentos Office
==============================================================

Skills para analise completa de documentos do pacote Office:
- Microsoft Office: DOC, DOCX, XLS, XLSX, PPT, PPTX
- LibreOffice/OpenOffice: ODT, ODS, ODP
- Outros: RTF, CSV

Analisa:
- Estrutura do documento
- Metadados (autor, titulo, data criacao)
- Conteudo textual
- Tabelas e dados
- Imagens embutidas
- Formatacao
"""

import os
import re
import xml.etree.ElementTree as ET
import zipfile
import struct
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .multimedia_base import MediaType, MediaFormat, AnalysisResult, MediaAnalyzer


# =============================================================================
# ANALISADOR DE DOCX (Word 2007+)
# =============================================================================

class DOCXAnalyzer(MediaAnalyzer):
    """Analisador de arquivos DOCX (Word 2007+)"""

    skill_id = "docx_analysis"
    name = "DOCX Analyzer"
    description = "Analisa documentos Microsoft Word (DOCX)"
    supported_formats = [MediaFormat.DOCX]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=MediaFormat.DOCX,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        metadata = {"document": {}, "content": {}}

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Verifica se e um DOCX valido
                if '[Content_Types].xml' not in zf.namelist():
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.TEXT,
                        format=MediaFormat.DOCX,
                        file_path=file_path,
                        error="Arquivo nao e um DOCX valido"
                    )

                # Extrai metadados do core.xml
                if 'docProps/core.xml' in zf.namelist():
                    core_xml = zf.read('docProps/core.xml').decode('utf-8', errors='ignore')
                    metadata["document"].update(self._parse_core_xml(core_xml))

                # Extrai metadados do app.xml
                if 'docProps/app.xml' in zf.namelist():
                    app_xml = zf.read('docProps/app.xml').decode('utf-8', errors='ignore')
                    metadata["document"].update(self._parse_app_xml(app_xml))

                # Extrai conteudo do document.xml
                if 'word/document.xml' in zf.namelist():
                    doc_xml = zf.read('word/document.xml').decode('utf-8', errors='ignore')
                    content_data = self._parse_document_xml(doc_xml)
                    metadata["content"] = content_data

                # Lista arquivos no pacote
                files_in_package = zf.namelist()

                # Conta imagens
                images = [f for f in files_in_package if f.startswith('word/media/')]

                # Conta styles
                has_styles = 'word/styles.xml' in files_in_package

                # Conta headers/footers
                headers = [f for f in files_in_package if 'header' in f.lower()]
                footers = [f for f in files_in_package if 'footer' in f.lower()]

                metadata["structure"] = {
                    "total_files": len(files_in_package),
                    "images_count": len(images),
                    "has_styles": has_styles,
                    "headers_count": len(headers),
                    "footers_count": len(footers),
                    "has_comments": 'word/comments.xml' in files_in_package,
                    "has_footnotes": 'word/footnotes.xml' in files_in_package,
                    "has_endnotes": 'word/endnotes.xml' in files_in_package
                }

            file_size = path.stat().st_size
            metadata["file"] = {
                "size": file_size,
                "size_formatted": self._format_size(file_size)
            }

            # Resumo
            pages = metadata["document"].get("pages", "?")
            words = metadata["content"].get("word_count", 0)

            return AnalysisResult(
                success=True,
                media_type=MediaType.TEXT,
                format=MediaFormat.DOCX,
                file_path=file_path,
                metadata=metadata,
                summary=f"DOCX: {pages} paginas, {words} palavras"
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=MediaFormat.DOCX,
                file_path=file_path,
                error=str(e)
            )

    def _parse_core_xml(self, xml_content: str) -> Dict:
        """Parse metadados do core.xml"""
        metadata = {}

        # Namespaces
        ns = {
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/'
        }

        try:
            root = ET.fromstring(xml_content)

            # Busca tags comuns
            tags = {
                'title': './/dc:title',
                'creator': './/dc:creator',
                'subject': './/dc:subject',
                'description': './/dc:description',
                'keywords': './/cp:keywords',
                'created': './/dcterms:created',
                'modified': './/dcterms:modified',
                'last_modified_by': './/cp:lastModifiedBy',
                'revision': './/cp:revision'
            }

            for key, xpath in tags.items():
                elem = root.find(xpath, ns)
                if elem is not None and elem.text:
                    metadata[key] = elem.text

        except Exception:
            pass

        return metadata

    def _parse_app_xml(self, xml_content: str) -> Dict:
        """Parse metadados do app.xml"""
        metadata = {}

        ns = {'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'}

        try:
            root = ET.fromstring(xml_content)

            tags = {
                'application': './/ep:Application',
                'app_version': './/ep:AppVersion',
                'pages': './/ep:Pages',
                'words': './/ep:Words',
                'characters': './/ep:Characters',
                'paragraphs': './/ep:Paragraphs',
                'lines': './/ep:Lines',
                'company': './/ep:Company',
                'template': './/ep:Template'
            }

            for key, xpath in tags.items():
                elem = root.find(xpath, ns)
                if elem is not None and elem.text:
                    try:
                        metadata[key] = int(elem.text)
                    except ValueError:
                        metadata[key] = elem.text

        except Exception:
            pass

        return metadata

    def _parse_document_xml(self, xml_content: str) -> Dict:
        """Parse conteudo do document.xml"""
        content = {
            "paragraphs": [],
            "tables_count": 0,
            "word_count": 0,
            "char_count": 0
        }

        try:
            # Remove namespaces para facilitar parsing
            xml_clean = re.sub(r'xmlns[^"]*"[^"]*"', '', xml_content)
            xml_clean = re.sub(r'\w+:', '', xml_clean)

            root = ET.fromstring(xml_clean)

            # Extrai paragrafos
            paragraphs = []
            for p in root.iter('p'):
                text_parts = []
                for t in p.iter('t'):
                    if t.text:
                        text_parts.append(t.text)
                if text_parts:
                    para_text = ''.join(text_parts)
                    paragraphs.append(para_text)

            full_text = '\n'.join(paragraphs)
            words = full_text.split()

            content["paragraphs"] = paragraphs[:10]  # Primeiros 10 paragrafos
            content["paragraph_count"] = len(paragraphs)
            content["word_count"] = len(words)
            content["char_count"] = len(full_text)

            # Conta tabelas
            content["tables_count"] = len(list(root.iter('tbl')))

            # Preview do conteudo
            content["preview"] = full_text[:500] if full_text else ""

        except Exception:
            pass

        return content

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE XLSX (Excel 2007+)
# =============================================================================

class XLSXAnalyzer(MediaAnalyzer):
    """Analisador de arquivos XLSX (Excel 2007+)"""

    skill_id = "xlsx_analysis"
    name = "XLSX Analyzer"
    description = "Analisa planilhas Microsoft Excel (XLSX)"
    supported_formats = [MediaFormat.XLSX]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.DATA,
                format=MediaFormat.XLSX,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        metadata = {"workbook": {}, "sheets": []}

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                if '[Content_Types].xml' not in zf.namelist():
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.DATA,
                        format=MediaFormat.XLSX,
                        file_path=file_path,
                        error="Arquivo nao e um XLSX valido"
                    )

                # Metadados do core.xml
                if 'docProps/core.xml' in zf.namelist():
                    core_xml = zf.read('docProps/core.xml').decode('utf-8', errors='ignore')
                    metadata["workbook"].update(self._parse_core_xml(core_xml))

                # Metadados do app.xml
                if 'docProps/app.xml' in zf.namelist():
                    app_xml = zf.read('docProps/app.xml').decode('utf-8', errors='ignore')
                    metadata["workbook"].update(self._parse_app_xml(app_xml))

                # Informacoes do workbook
                if 'xl/workbook.xml' in zf.namelist():
                    wb_xml = zf.read('xl/workbook.xml').decode('utf-8', errors='ignore')
                    sheets_info = self._parse_workbook_xml(wb_xml)

                    # Analisa cada sheet
                    for i, sheet in enumerate(sheets_info, 1):
                        sheet_file = f'xl/worksheets/sheet{i}.xml'
                        if sheet_file in zf.namelist():
                            sheet_xml = zf.read(sheet_file).decode('utf-8', errors='ignore')
                            sheet_data = self._parse_sheet_xml(sheet_xml)
                            sheet.update(sheet_data)
                        metadata["sheets"].append(sheet)

                # Shared strings
                shared_strings = []
                if 'xl/sharedStrings.xml' in zf.namelist():
                    ss_xml = zf.read('xl/sharedStrings.xml').decode('utf-8', errors='ignore')
                    shared_strings = self._parse_shared_strings(ss_xml)
                    metadata["workbook"]["unique_strings"] = len(shared_strings)

                # Conta elementos
                files = zf.namelist()
                metadata["structure"] = {
                    "total_sheets": len(metadata["sheets"]),
                    "has_charts": any('chart' in f for f in files),
                    "has_images": any('media' in f for f in files),
                    "has_pivot": any('pivot' in f for f in files),
                    "has_macros": 'xl/vbaProject.bin' in files
                }

            file_size = path.stat().st_size
            metadata["file"] = {
                "size": file_size,
                "size_formatted": self._format_size(file_size)
            }

            sheets_count = len(metadata["sheets"])
            total_rows = sum(s.get("row_count", 0) for s in metadata["sheets"])

            return AnalysisResult(
                success=True,
                media_type=MediaType.DATA,
                format=MediaFormat.XLSX,
                file_path=file_path,
                metadata=metadata,
                summary=f"XLSX: {sheets_count} planilhas, {total_rows} linhas"
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.DATA,
                format=MediaFormat.XLSX,
                file_path=file_path,
                error=str(e)
            )

    def _parse_core_xml(self, xml_content: str) -> Dict:
        """Parse metadados do core.xml"""
        metadata = {}
        ns = {
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/'
        }

        try:
            root = ET.fromstring(xml_content)

            for key, xpath in [
                ('title', './/dc:title'),
                ('creator', './/dc:creator'),
                ('created', './/dcterms:created'),
                ('modified', './/dcterms:modified')
            ]:
                elem = root.find(xpath, ns)
                if elem is not None and elem.text:
                    metadata[key] = elem.text
        except Exception:
            pass

        return metadata

    def _parse_app_xml(self, xml_content: str) -> Dict:
        """Parse metadados do app.xml"""
        metadata = {}
        ns = {'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'}

        try:
            root = ET.fromstring(xml_content)

            for key, xpath in [
                ('application', './/ep:Application'),
                ('app_version', './/ep:AppVersion'),
                ('company', './/ep:Company')
            ]:
                elem = root.find(xpath, ns)
                if elem is not None and elem.text:
                    metadata[key] = elem.text
        except Exception:
            pass

        return metadata

    def _parse_workbook_xml(self, xml_content: str) -> List[Dict]:
        """Parse informacoes do workbook"""
        sheets = []

        try:
            xml_clean = re.sub(r'xmlns[^"]*"[^"]*"', '', xml_content)
            xml_clean = re.sub(r'\w+:', '', xml_clean)

            root = ET.fromstring(xml_clean)

            for sheet in root.iter('sheet'):
                sheets.append({
                    "name": sheet.get('name', 'Sheet'),
                    "sheet_id": sheet.get('sheetId', '1')
                })
        except Exception:
            pass

        return sheets

    def _parse_sheet_xml(self, xml_content: str) -> Dict:
        """Parse dados de uma planilha"""
        data = {
            "row_count": 0,
            "col_count": 0,
            "cell_count": 0
        }

        try:
            xml_clean = re.sub(r'xmlns[^"]*"[^"]*"', '', xml_content)
            xml_clean = re.sub(r'\w+:', '', xml_clean)

            root = ET.fromstring(xml_clean)

            # Dimensao
            dimension = root.find('.//dimension')
            if dimension is not None:
                ref = dimension.get('ref', '')
                if ':' in ref:
                    data["dimension"] = ref

            # Conta linhas e celulas
            rows = list(root.iter('row'))
            data["row_count"] = len(rows)

            max_col = 0
            cell_count = 0
            for row in rows:
                cells = list(row.iter('c'))
                cell_count += len(cells)
                if cells:
                    last_cell = cells[-1].get('r', '')
                    col_letters = ''.join(c for c in last_cell if c.isalpha())
                    col_num = self._col_to_num(col_letters)
                    max_col = max(max_col, col_num)

            data["col_count"] = max_col
            data["cell_count"] = cell_count

        except Exception:
            pass

        return data

    def _parse_shared_strings(self, xml_content: str) -> List[str]:
        """Parse strings compartilhadas"""
        strings = []

        try:
            xml_clean = re.sub(r'xmlns[^"]*"[^"]*"', '', xml_content)
            xml_clean = re.sub(r'\w+:', '', xml_clean)

            root = ET.fromstring(xml_clean)

            for si in root.iter('si'):
                text_parts = []
                for t in si.iter('t'):
                    if t.text:
                        text_parts.append(t.text)
                if text_parts:
                    strings.append(''.join(text_parts))
        except Exception:
            pass

        return strings

    def _col_to_num(self, col: str) -> int:
        """Converte letra de coluna para numero"""
        result = 0
        for c in col.upper():
            result = result * 26 + (ord(c) - ord('A') + 1)
        return result

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE PPTX (PowerPoint 2007+)
# =============================================================================

class PPTXAnalyzer(MediaAnalyzer):
    """Analisador de arquivos PPTX (PowerPoint 2007+)"""

    skill_id = "pptx_analysis"
    name = "PPTX Analyzer"
    description = "Analisa apresentacoes Microsoft PowerPoint (PPTX)"
    supported_formats = [MediaFormat.PPTX]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=MediaFormat.PPTX,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        metadata = {"presentation": {}, "slides": []}

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                if '[Content_Types].xml' not in zf.namelist():
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.TEXT,
                        format=MediaFormat.PPTX,
                        file_path=file_path,
                        error="Arquivo nao e um PPTX valido"
                    )

                # Metadados
                if 'docProps/core.xml' in zf.namelist():
                    core_xml = zf.read('docProps/core.xml').decode('utf-8', errors='ignore')
                    metadata["presentation"].update(self._parse_core_xml(core_xml))

                if 'docProps/app.xml' in zf.namelist():
                    app_xml = zf.read('docProps/app.xml').decode('utf-8', errors='ignore')
                    metadata["presentation"].update(self._parse_app_xml(app_xml))

                # Conta slides
                files = zf.namelist()
                slide_files = sorted([f for f in files if f.startswith('ppt/slides/slide') and f.endswith('.xml')])

                # Analisa cada slide
                for slide_file in slide_files[:20]:  # Limita a 20 slides
                    slide_xml = zf.read(slide_file).decode('utf-8', errors='ignore')
                    slide_data = self._parse_slide_xml(slide_xml)
                    slide_data["file"] = slide_file
                    metadata["slides"].append(slide_data)

                # Estrutura
                metadata["structure"] = {
                    "slide_count": len(slide_files),
                    "has_notes": any('notesSlide' in f for f in files),
                    "has_comments": any('comment' in f for f in files),
                    "has_charts": any('chart' in f for f in files),
                    "images_count": len([f for f in files if f.startswith('ppt/media/')]),
                    "slide_masters": len([f for f in files if 'slideMaster' in f]),
                    "slide_layouts": len([f for f in files if 'slideLayout' in f])
                }

            file_size = path.stat().st_size
            metadata["file"] = {
                "size": file_size,
                "size_formatted": self._format_size(file_size)
            }

            slides_count = metadata["structure"]["slide_count"]
            images_count = metadata["structure"]["images_count"]

            return AnalysisResult(
                success=True,
                media_type=MediaType.TEXT,
                format=MediaFormat.PPTX,
                file_path=file_path,
                metadata=metadata,
                summary=f"PPTX: {slides_count} slides, {images_count} imagens"
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=MediaFormat.PPTX,
                file_path=file_path,
                error=str(e)
            )

    def _parse_core_xml(self, xml_content: str) -> Dict:
        """Parse metadados do core.xml"""
        metadata = {}
        ns = {
            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/'
        }

        try:
            root = ET.fromstring(xml_content)
            for key, xpath in [
                ('title', './/dc:title'),
                ('creator', './/dc:creator'),
                ('created', './/dcterms:created'),
                ('modified', './/dcterms:modified')
            ]:
                elem = root.find(xpath, ns)
                if elem is not None and elem.text:
                    metadata[key] = elem.text
        except Exception:
            pass

        return metadata

    def _parse_app_xml(self, xml_content: str) -> Dict:
        """Parse metadados do app.xml"""
        metadata = {}
        ns = {'ep': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'}

        try:
            root = ET.fromstring(xml_content)
            for key, xpath in [
                ('application', './/ep:Application'),
                ('slides', './/ep:Slides'),
                ('paragraphs', './/ep:Paragraphs'),
                ('words', './/ep:Words'),
                ('notes', './/ep:Notes'),
                ('hidden_slides', './/ep:HiddenSlides'),
                ('company', './/ep:Company')
            ]:
                elem = root.find(xpath, ns)
                if elem is not None and elem.text:
                    try:
                        metadata[key] = int(elem.text)
                    except ValueError:
                        metadata[key] = elem.text
        except Exception:
            pass

        return metadata

    def _parse_slide_xml(self, xml_content: str) -> Dict:
        """Parse conteudo de um slide"""
        data = {
            "text_blocks": [],
            "shapes_count": 0,
            "images_count": 0
        }

        try:
            xml_clean = re.sub(r'xmlns[^"]*"[^"]*"', '', xml_content)
            xml_clean = re.sub(r'\w+:', '', xml_clean)

            root = ET.fromstring(xml_clean)

            # Extrai texto
            text_blocks = []
            for t in root.iter('t'):
                if t.text and t.text.strip():
                    text_blocks.append(t.text.strip())

            data["text_blocks"] = text_blocks[:5]  # Primeiros 5 blocos
            data["text_count"] = len(text_blocks)

            # Conta shapes
            data["shapes_count"] = len(list(root.iter('sp')))

            # Conta imagens
            data["images_count"] = len(list(root.iter('pic')))

        except Exception:
            pass

        return data

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE ODT (OpenDocument Text)
# =============================================================================

class ODTAnalyzer(MediaAnalyzer):
    """Analisador de arquivos ODT (OpenDocument Text)"""

    skill_id = "odt_analysis"
    name = "ODT Analyzer"
    description = "Analisa documentos OpenDocument Text (ODT)"
    supported_formats = [MediaFormat.ODT]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=MediaFormat.ODT,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        metadata = {"document": {}, "content": {}}

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                if 'mimetype' not in zf.namelist():
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.TEXT,
                        format=MediaFormat.ODT,
                        file_path=file_path,
                        error="Arquivo nao e um ODT valido"
                    )

                # Verifica mimetype
                mimetype = zf.read('mimetype').decode('utf-8').strip()
                metadata["document"]["mimetype"] = mimetype

                # Metadados
                if 'meta.xml' in zf.namelist():
                    meta_xml = zf.read('meta.xml').decode('utf-8', errors='ignore')
                    metadata["document"].update(self._parse_meta_xml(meta_xml))

                # Conteudo
                if 'content.xml' in zf.namelist():
                    content_xml = zf.read('content.xml').decode('utf-8', errors='ignore')
                    metadata["content"] = self._parse_content_xml(content_xml)

                # Estrutura
                files = zf.namelist()
                metadata["structure"] = {
                    "has_styles": 'styles.xml' in files,
                    "has_settings": 'settings.xml' in files,
                    "images_count": len([f for f in files if f.startswith('Pictures/')])
                }

            file_size = path.stat().st_size
            metadata["file"] = {
                "size": file_size,
                "size_formatted": self._format_size(file_size)
            }

            words = metadata["content"].get("word_count", 0)

            return AnalysisResult(
                success=True,
                media_type=MediaType.TEXT,
                format=MediaFormat.ODT,
                file_path=file_path,
                metadata=metadata,
                summary=f"ODT: {words} palavras"
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=MediaFormat.ODT,
                file_path=file_path,
                error=str(e)
            )

    def _parse_meta_xml(self, xml_content: str) -> Dict:
        """Parse metadados do meta.xml"""
        metadata = {}

        try:
            xml_clean = re.sub(r'xmlns[^"]*"[^"]*"', '', xml_content)
            xml_clean = re.sub(r'\w+:', '', xml_clean)

            root = ET.fromstring(xml_clean)

            # Procura tags de metadados
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if elem.text and elem.text.strip():
                    if tag in ['title', 'subject', 'description', 'keyword',
                               'creator', 'date', 'creation-date', 'editing-cycles',
                               'editing-duration', 'generator']:
                        metadata[tag.replace('-', '_')] = elem.text.strip()

        except Exception:
            pass

        return metadata

    def _parse_content_xml(self, xml_content: str) -> Dict:
        """Parse conteudo do content.xml"""
        content = {
            "paragraphs": [],
            "word_count": 0,
            "char_count": 0
        }

        try:
            xml_clean = re.sub(r'xmlns[^"]*"[^"]*"', '', xml_content)
            xml_clean = re.sub(r'\w+:', '', xml_clean)

            root = ET.fromstring(xml_clean)

            # Extrai texto de paragrafos
            paragraphs = []
            for p in root.iter('p'):
                text = ''.join(p.itertext())
                if text.strip():
                    paragraphs.append(text.strip())

            full_text = '\n'.join(paragraphs)

            content["paragraphs"] = paragraphs[:10]
            content["paragraph_count"] = len(paragraphs)
            content["word_count"] = len(full_text.split())
            content["char_count"] = len(full_text)
            content["preview"] = full_text[:500]

        except Exception:
            pass

        return content

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE ODS (OpenDocument Spreadsheet)
# =============================================================================

class ODSAnalyzer(MediaAnalyzer):
    """Analisador de arquivos ODS (OpenDocument Spreadsheet)"""

    skill_id = "ods_analysis"
    name = "ODS Analyzer"
    description = "Analisa planilhas OpenDocument Spreadsheet (ODS)"
    supported_formats = [MediaFormat.ODS]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.DATA,
                format=MediaFormat.ODS,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        metadata = {"workbook": {}, "sheets": []}

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                if 'mimetype' not in zf.namelist():
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.DATA,
                        format=MediaFormat.ODS,
                        file_path=file_path,
                        error="Arquivo nao e um ODS valido"
                    )

                # Metadados
                if 'meta.xml' in zf.namelist():
                    meta_xml = zf.read('meta.xml').decode('utf-8', errors='ignore')
                    metadata["workbook"].update(self._parse_meta_xml(meta_xml))

                # Conteudo
                if 'content.xml' in zf.namelist():
                    content_xml = zf.read('content.xml').decode('utf-8', errors='ignore')
                    metadata["sheets"] = self._parse_content_xml(content_xml)

            file_size = path.stat().st_size
            metadata["file"] = {
                "size": file_size,
                "size_formatted": self._format_size(file_size)
            }

            sheets_count = len(metadata["sheets"])
            total_rows = sum(s.get("row_count", 0) for s in metadata["sheets"])

            return AnalysisResult(
                success=True,
                media_type=MediaType.DATA,
                format=MediaFormat.ODS,
                file_path=file_path,
                metadata=metadata,
                summary=f"ODS: {sheets_count} planilhas, {total_rows} linhas"
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.DATA,
                format=MediaFormat.ODS,
                file_path=file_path,
                error=str(e)
            )

    def _parse_meta_xml(self, xml_content: str) -> Dict:
        """Parse metadados"""
        metadata = {}
        try:
            xml_clean = re.sub(r'xmlns[^"]*"[^"]*"', '', xml_content)
            xml_clean = re.sub(r'\w+:', '', xml_clean)
            root = ET.fromstring(xml_clean)

            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if elem.text and elem.text.strip():
                    if tag in ['title', 'creator', 'date', 'creation-date']:
                        metadata[tag.replace('-', '_')] = elem.text.strip()
        except Exception:
            pass
        return metadata

    def _parse_content_xml(self, xml_content: str) -> List[Dict]:
        """Parse conteudo das planilhas"""
        sheets = []

        try:
            xml_clean = re.sub(r'xmlns[^"]*"[^"]*"', '', xml_content)
            xml_clean = re.sub(r'\w+:', '', xml_clean)
            root = ET.fromstring(xml_clean)

            for table in root.iter('table'):
                name = table.get('name', 'Sheet')
                rows = list(table.iter('table-row'))

                cell_count = 0
                for row in rows:
                    cells = list(row.iter('table-cell'))
                    cell_count += len(cells)

                sheets.append({
                    "name": name,
                    "row_count": len(rows),
                    "cell_count": cell_count
                })
        except Exception:
            pass

        return sheets

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE RTF
# =============================================================================

class RTFAnalyzer(MediaAnalyzer):
    """Analisador de arquivos RTF (Rich Text Format)"""

    skill_id = "rtf_analysis"
    name = "RTF Analyzer"
    description = "Analisa documentos Rich Text Format (RTF)"
    supported_formats = [MediaFormat.RTF]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=MediaFormat.RTF,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            # Verifica assinatura RTF
            if not content.startswith(b'{\\rtf'):
                return AnalysisResult(
                    success=False,
                    media_type=MediaType.TEXT,
                    format=MediaFormat.RTF,
                    file_path=file_path,
                    error="Arquivo nao e um RTF valido"
                )

            # Decodifica
            try:
                text_content = content.decode('cp1252', errors='ignore')
            except:
                text_content = content.decode('utf-8', errors='ignore')

            # Extrai texto simples (remove comandos RTF)
            plain_text = self._extract_plain_text(text_content)

            # Analisa estrutura
            has_images = b'\\pict' in content
            has_tables = b'\\trowd' in content
            has_fonts = b'\\fonttbl' in content
            has_colors = b'\\colortbl' in content

            file_size = path.stat().st_size

            metadata = {
                "document": {
                    "format": "RTF",
                    "version": self._get_rtf_version(text_content)
                },
                "content": {
                    "word_count": len(plain_text.split()),
                    "char_count": len(plain_text),
                    "preview": plain_text[:500]
                },
                "structure": {
                    "has_images": has_images,
                    "has_tables": has_tables,
                    "has_fonts": has_fonts,
                    "has_colors": has_colors
                },
                "file": {
                    "size": file_size,
                    "size_formatted": self._format_size(file_size)
                }
            }

            words = metadata["content"]["word_count"]

            return AnalysisResult(
                success=True,
                media_type=MediaType.TEXT,
                format=MediaFormat.RTF,
                file_path=file_path,
                metadata=metadata,
                summary=f"RTF: {words} palavras"
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=MediaFormat.RTF,
                file_path=file_path,
                error=str(e)
            )

    def _extract_plain_text(self, rtf_content: str) -> str:
        """Extrai texto puro do RTF"""
        # Remove grupos de controle
        text = re.sub(r'\\[a-z]+[-]?\d*[ ]?', '', rtf_content)
        # Remove chaves
        text = re.sub(r'[{}]', '', text)
        # Remove caracteres especiais
        text = re.sub(r'\\\'[0-9a-f]{2}', ' ', text)
        # Limpa espacos
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _get_rtf_version(self, content: str) -> str:
        """Extrai versao do RTF"""
        match = re.search(r'\\rtf(\d+)', content)
        return match.group(1) if match else "1"

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR GENERICO DE OFFICE
# =============================================================================

class OfficeAnalyzer(MediaAnalyzer):
    """Analisador generico que detecta e delega para analisadores especificos"""

    skill_id = "office_analysis"
    name = "Office Document Analyzer"
    description = "Analisa documentos Office automaticamente"
    supported_formats = [
        MediaFormat.DOCX, MediaFormat.XLSX, MediaFormat.PPTX,
        MediaFormat.ODT, MediaFormat.ODS, MediaFormat.RTF
    ]

    def __init__(self):
        self._analyzers = {
            MediaFormat.DOCX: DOCXAnalyzer(),
            MediaFormat.XLSX: XLSXAnalyzer(),
            MediaFormat.PPTX: PPTXAnalyzer(),
            MediaFormat.ODT: ODTAnalyzer(),
            MediaFormat.ODS: ODSAnalyzer(),
            MediaFormat.RTF: RTFAnalyzer(),
        }

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=None,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        # Detecta formato pela extensao
        ext = path.suffix.lower().lstrip(".")
        format_map = {
            "docx": MediaFormat.DOCX,
            "xlsx": MediaFormat.XLSX,
            "pptx": MediaFormat.PPTX,
            "odt": MediaFormat.ODT,
            "ods": MediaFormat.ODS,
            "rtf": MediaFormat.RTF,
        }

        fmt = format_map.get(ext)
        if not fmt:
            return AnalysisResult(
                success=False,
                media_type=MediaType.TEXT,
                format=None,
                file_path=file_path,
                error=f"Formato Office nao suportado: {ext}"
            )

        analyzer = self._analyzers.get(fmt)
        if analyzer:
            return analyzer.analyze(file_path, options)

        return AnalysisResult(
            success=False,
            media_type=MediaType.TEXT,
            format=fmt,
            file_path=file_path,
            error=f"Analisador nao disponivel para formato: {fmt.extension}"
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "DOCXAnalyzer",
    "XLSXAnalyzer",
    "PPTXAnalyzer",
    "ODTAnalyzer",
    "ODSAnalyzer",
    "RTFAnalyzer",
    "OfficeAnalyzer",
]
