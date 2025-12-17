"""
Image Analysis Skills - Analise de Imagens
===========================================

Skills para analise de imagens em diversos formatos:
- Raster: PNG, JPG, JPEG, GIF, BMP, TIFF, WebP, ICO
- Vetorial: SVG
- RAW: CR2, NEF, ARW, DNG
- Outros: PSD, AI, EPS

Analisa:
- Metadados (EXIF, IPTC, XMP)
- Dimensoes e resolucao
- Espaco de cores
- Histograma
- Deteccao de faces (simulado)
- OCR (simulado)
"""

import os
import struct
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .multimedia_base import MediaType, MediaFormat, AnalysisResult, MediaAnalyzer


# =============================================================================
# FORMATOS DE IMAGEM SUPORTADOS
# =============================================================================

class ImageFormat(Enum):
    """Formatos de imagem suportados"""
    # Raster
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"
    TIF = "tif"
    WEBP = "webp"
    ICO = "ico"
    HEIC = "heic"
    HEIF = "heif"

    # Vetorial
    SVG = "svg"

    # RAW Camera
    CR2 = "cr2"    # Canon
    NEF = "nef"    # Nikon
    ARW = "arw"    # Sony
    DNG = "dng"    # Adobe
    RAF = "raf"    # Fuji
    ORF = "orf"    # Olympus

    # Design
    PSD = "psd"    # Photoshop
    AI = "ai"      # Illustrator
    EPS = "eps"    # Encapsulated PostScript

    @classmethod
    def from_extension(cls, ext: str) -> Optional["ImageFormat"]:
        ext = ext.lower().lstrip(".")
        for fmt in cls:
            if fmt.value == ext:
                return fmt
        return None


# Mapeamento de formatos para MediaFormat
IMAGE_FORMAT_MAP = {
    ImageFormat.PNG: MediaFormat.PNG,
    ImageFormat.JPG: MediaFormat.JPG,
    ImageFormat.JPEG: MediaFormat.JPG,
    ImageFormat.GIF: MediaFormat.GIF,
    ImageFormat.BMP: MediaFormat.BMP,
    ImageFormat.TIFF: MediaFormat.TIFF,
    ImageFormat.TIF: MediaFormat.TIFF,
    ImageFormat.WEBP: MediaFormat.WEBP,
    ImageFormat.SVG: MediaFormat.SVG,
}


# =============================================================================
# RESULTADO DE ANALISE DE IMAGEM
# =============================================================================

@dataclass
class ImageMetadata:
    """Metadados de imagem"""
    width: int = 0
    height: int = 0
    bit_depth: int = 8
    color_mode: str = "RGB"
    has_alpha: bool = False
    dpi: Tuple[int, int] = (72, 72)
    format: str = ""
    file_size: int = 0

    # EXIF
    exif: Dict[str, Any] = field(default_factory=dict)

    # Camera info
    camera_make: str = ""
    camera_model: str = ""
    date_taken: Optional[datetime] = None
    gps_location: Optional[Tuple[float, float]] = None

    # Image properties
    is_animated: bool = False
    frame_count: int = 1
    is_interlaced: bool = False
    compression: str = ""


# =============================================================================
# ANALISADOR DE PNG
# =============================================================================

class PNGAnalyzer(MediaAnalyzer):
    """Analisador de arquivos PNG"""

    skill_id = "png_analysis"
    name = "PNG Analyzer"
    description = "Analisa imagens PNG extraindo metadados e caracteristicas"
    supported_formats = [MediaFormat.PNG]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.PNG,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        metadata = {"image": {}}

        try:
            with open(file_path, "rb") as f:
                # Verifica assinatura PNG
                signature = f.read(8)
                if signature != b'\x89PNG\r\n\x1a\n':
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.IMAGE,
                        format=MediaFormat.PNG,
                        file_path=file_path,
                        error="Arquivo nao e um PNG valido"
                    )

                width = height = bit_depth = color_type = 0
                has_alpha = False
                is_interlaced = False
                chunks = []

                while True:
                    length_data = f.read(4)
                    if len(length_data) < 4:
                        break

                    length = struct.unpack(">I", length_data)[0]
                    chunk_type = f.read(4).decode("ascii", errors="ignore")
                    chunk_data = f.read(length)
                    crc = f.read(4)

                    chunks.append({"type": chunk_type, "size": length})

                    if chunk_type == "IHDR":
                        width = struct.unpack(">I", chunk_data[0:4])[0]
                        height = struct.unpack(">I", chunk_data[4:8])[0]
                        bit_depth = chunk_data[8]
                        color_type = chunk_data[9]
                        compression = chunk_data[10]
                        filter_method = chunk_data[11]
                        interlace = chunk_data[12]

                        is_interlaced = interlace == 1
                        has_alpha = color_type in [4, 6]

                    if chunk_type == "IEND":
                        break

                # Determina modo de cor
                color_modes = {
                    0: "Grayscale",
                    2: "RGB",
                    3: "Indexed",
                    4: "Grayscale+Alpha",
                    6: "RGBA"
                }
                color_mode = color_modes.get(color_type, "Unknown")

                file_size = path.stat().st_size

                metadata["image"] = {
                    "width": width,
                    "height": height,
                    "resolution": f"{width}x{height}",
                    "bit_depth": bit_depth,
                    "color_mode": color_mode,
                    "color_type": color_type,
                    "has_alpha": has_alpha,
                    "is_interlaced": is_interlaced,
                    "chunks": chunks[:10],  # Primeiros 10 chunks
                    "chunk_count": len(chunks),
                    "file_size": file_size,
                    "file_size_formatted": self._format_size(file_size),
                    "aspect_ratio": round(width / height, 2) if height > 0 else 0,
                    "megapixels": round((width * height) / 1_000_000, 2)
                }

                return AnalysisResult(
                    success=True,
                    media_type=MediaType.IMAGE,
                    format=MediaFormat.PNG,
                    file_path=file_path,
                    metadata=metadata,
                    summary=f"PNG {width}x{height} {color_mode} {bit_depth}bit"
                )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.PNG,
                file_path=file_path,
                error=str(e)
            )

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE JPEG
# =============================================================================

class JPEGAnalyzer(MediaAnalyzer):
    """Analisador de arquivos JPEG/JPG"""

    skill_id = "jpeg_analysis"
    name = "JPEG Analyzer"
    description = "Analisa imagens JPEG extraindo metadados EXIF e caracteristicas"
    supported_formats = [MediaFormat.JPG]

    # Tags EXIF comuns
    EXIF_TAGS = {
        0x010F: "Make",
        0x0110: "Model",
        0x0112: "Orientation",
        0x011A: "XResolution",
        0x011B: "YResolution",
        0x0128: "ResolutionUnit",
        0x0131: "Software",
        0x0132: "DateTime",
        0x0213: "YCbCrPositioning",
        0x8769: "ExifOffset",
        0x8825: "GPSInfo",
        0x829A: "ExposureTime",
        0x829D: "FNumber",
        0x8827: "ISOSpeedRatings",
        0x9003: "DateTimeOriginal",
        0x9004: "DateTimeDigitized",
        0x920A: "FocalLength",
        0xA405: "FocalLengthIn35mmFilm",
    }

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.JPG,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        metadata = {"image": {}, "exif": {}}

        try:
            with open(file_path, "rb") as f:
                # Verifica assinatura JPEG
                header = f.read(2)
                if header != b'\xff\xd8':
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.IMAGE,
                        format=MediaFormat.JPG,
                        file_path=file_path,
                        error="Arquivo nao e um JPEG valido"
                    )

                width = height = 0
                quality_estimate = 0

                # Parse markers
                while True:
                    marker = f.read(2)
                    if len(marker) < 2:
                        break

                    if marker[0] != 0xFF:
                        break

                    marker_type = marker[1]

                    # SOI, EOI, RST markers nao tem length
                    if marker_type in [0xD8, 0xD9] or 0xD0 <= marker_type <= 0xD7:
                        continue

                    # Le tamanho do segmento
                    length_data = f.read(2)
                    if len(length_data) < 2:
                        break

                    length = struct.unpack(">H", length_data)[0]
                    segment_data = f.read(length - 2)

                    # SOF markers (dimensoes)
                    if marker_type in [0xC0, 0xC1, 0xC2]:
                        precision = segment_data[0]
                        height = struct.unpack(">H", segment_data[1:3])[0]
                        width = struct.unpack(">H", segment_data[3:5])[0]
                        num_components = segment_data[5]

                    # APP1 (EXIF)
                    if marker_type == 0xE1:
                        if segment_data[:4] == b'Exif':
                            exif_data = self._parse_exif(segment_data[6:])
                            metadata["exif"] = exif_data

                    # DQT (Quantization table - quality estimate)
                    if marker_type == 0xDB:
                        quality_estimate = self._estimate_quality(segment_data)

                    # EOI
                    if marker_type == 0xD9:
                        break

                file_size = path.stat().st_size

                metadata["image"] = {
                    "width": width,
                    "height": height,
                    "resolution": f"{width}x{height}",
                    "format": "JPEG",
                    "file_size": file_size,
                    "file_size_formatted": self._format_size(file_size),
                    "aspect_ratio": round(width / height, 2) if height > 0 else 0,
                    "megapixels": round((width * height) / 1_000_000, 2),
                    "quality_estimate": quality_estimate,
                    "compression": "lossy"
                }

                # Adiciona info da camera se disponivel
                exif = metadata.get("exif", {})
                if exif.get("Make") or exif.get("Model"):
                    metadata["camera"] = {
                        "make": exif.get("Make", ""),
                        "model": exif.get("Model", ""),
                        "software": exif.get("Software", ""),
                        "date_taken": exif.get("DateTimeOriginal", "")
                    }

                summary = f"JPEG {width}x{height}"
                if quality_estimate:
                    summary += f" Q{quality_estimate}%"

                return AnalysisResult(
                    success=True,
                    media_type=MediaType.IMAGE,
                    format=MediaFormat.JPG,
                    file_path=file_path,
                    metadata=metadata,
                    summary=summary
                )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.JPG,
                file_path=file_path,
                error=str(e)
            )

    def _parse_exif(self, data: bytes) -> Dict:
        """Parse basico de dados EXIF"""
        exif = {}
        try:
            if len(data) < 8:
                return exif

            # Byte order
            byte_order = data[:2]
            if byte_order == b'II':
                endian = "<"  # Little endian
            elif byte_order == b'MM':
                endian = ">"  # Big endian
            else:
                return exif

            # Offset para primeiro IFD
            ifd_offset = struct.unpack(f"{endian}I", data[4:8])[0]

            if ifd_offset >= len(data):
                return exif

            # Numero de entradas
            num_entries = struct.unpack(f"{endian}H", data[ifd_offset:ifd_offset+2])[0]

            # Parse entries
            for i in range(min(num_entries, 20)):  # Limite de 20 tags
                entry_offset = ifd_offset + 2 + (i * 12)
                if entry_offset + 12 > len(data):
                    break

                tag = struct.unpack(f"{endian}H", data[entry_offset:entry_offset+2])[0]
                tag_type = struct.unpack(f"{endian}H", data[entry_offset+2:entry_offset+4])[0]
                count = struct.unpack(f"{endian}I", data[entry_offset+4:entry_offset+8])[0]

                tag_name = self.EXIF_TAGS.get(tag, f"Tag_{tag:04X}")

                # Valor simples (4 bytes ou menos)
                if tag_type == 2 and count <= 4:  # ASCII
                    value = data[entry_offset+8:entry_offset+8+count].decode("ascii", errors="ignore").strip('\x00')
                    exif[tag_name] = value
                elif tag_type == 3 and count == 1:  # SHORT
                    exif[tag_name] = struct.unpack(f"{endian}H", data[entry_offset+8:entry_offset+10])[0]
                elif tag_type == 4 and count == 1:  # LONG
                    exif[tag_name] = struct.unpack(f"{endian}I", data[entry_offset+8:entry_offset+12])[0]

        except Exception:
            pass

        return exif

    def _estimate_quality(self, dqt_data: bytes) -> int:
        """Estima qualidade JPEG baseado na tabela de quantizacao"""
        try:
            # Soma dos primeiros valores da tabela
            if len(dqt_data) > 1:
                table_sum = sum(dqt_data[1:min(65, len(dqt_data))])
                # Estimativa aproximada (valores menores = maior qualidade)
                if table_sum < 100:
                    return 95
                elif table_sum < 200:
                    return 85
                elif table_sum < 400:
                    return 75
                elif table_sum < 800:
                    return 60
                else:
                    return 40
        except Exception:
            pass
        return 0

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE GIF
# =============================================================================

class GIFAnalyzer(MediaAnalyzer):
    """Analisador de arquivos GIF"""

    skill_id = "gif_analysis"
    name = "GIF Analyzer"
    description = "Analisa imagens GIF incluindo animacoes"
    supported_formats = [MediaFormat.GIF]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.GIF,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        metadata = {"image": {}}

        try:
            with open(file_path, "rb") as f:
                # Verifica assinatura GIF
                signature = f.read(6)
                if signature[:3] != b'GIF':
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.IMAGE,
                        format=MediaFormat.GIF,
                        file_path=file_path,
                        error="Arquivo nao e um GIF valido"
                    )

                version = signature[3:].decode("ascii")

                # Logical Screen Descriptor
                width = struct.unpack("<H", f.read(2))[0]
                height = struct.unpack("<H", f.read(2))[0]
                packed = f.read(1)[0]

                has_global_color_table = (packed & 0x80) != 0
                color_resolution = ((packed >> 4) & 0x07) + 1
                sorted_flag = (packed & 0x08) != 0
                global_color_table_size = 2 ** ((packed & 0x07) + 1) if has_global_color_table else 0

                bg_color_index = f.read(1)[0]
                pixel_aspect_ratio = f.read(1)[0]

                # Pula Global Color Table
                if has_global_color_table:
                    f.read(global_color_table_size * 3)

                # Conta frames
                frame_count = 0
                total_delay = 0

                while True:
                    block_type = f.read(1)
                    if len(block_type) == 0:
                        break

                    block_type = block_type[0]

                    if block_type == 0x21:  # Extension
                        label = f.read(1)[0]

                        if label == 0xF9:  # Graphics Control Extension
                            block_size = f.read(1)[0]
                            block_data = f.read(block_size)
                            if len(block_data) >= 4:
                                delay = struct.unpack("<H", block_data[1:3])[0]
                                total_delay += delay
                            f.read(1)  # Block terminator
                        else:
                            # Skip other extensions
                            while True:
                                size = f.read(1)
                                if len(size) == 0 or size[0] == 0:
                                    break
                                f.read(size[0])

                    elif block_type == 0x2C:  # Image Descriptor
                        frame_count += 1
                        f.read(8)  # Skip descriptor

                        local_packed = f.read(1)[0]
                        has_local_color_table = (local_packed & 0x80) != 0

                        if has_local_color_table:
                            local_size = 2 ** ((local_packed & 0x07) + 1)
                            f.read(local_size * 3)

                        f.read(1)  # LZW minimum code size

                        # Skip image data
                        while True:
                            size = f.read(1)
                            if len(size) == 0 or size[0] == 0:
                                break
                            f.read(size[0])

                    elif block_type == 0x3B:  # Trailer
                        break

                    else:
                        break

                file_size = path.stat().st_size
                is_animated = frame_count > 1
                duration = total_delay / 100 if total_delay > 0 else 0
                fps = frame_count / duration if duration > 0 else 0

                metadata["image"] = {
                    "width": width,
                    "height": height,
                    "resolution": f"{width}x{height}",
                    "version": version,
                    "color_depth": color_resolution * 3,
                    "colors": global_color_table_size,
                    "is_animated": is_animated,
                    "frame_count": frame_count,
                    "duration_seconds": round(duration, 2),
                    "fps": round(fps, 1),
                    "file_size": file_size,
                    "file_size_formatted": self._format_size(file_size),
                    "aspect_ratio": round(width / height, 2) if height > 0 else 0
                }

                summary = f"GIF {width}x{height}"
                if is_animated:
                    summary += f" animated ({frame_count} frames, {duration:.1f}s)"

                return AnalysisResult(
                    success=True,
                    media_type=MediaType.IMAGE,
                    format=MediaFormat.GIF,
                    file_path=file_path,
                    metadata=metadata,
                    summary=summary
                )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.GIF,
                file_path=file_path,
                error=str(e)
            )

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE BMP
# =============================================================================

class BMPAnalyzer(MediaAnalyzer):
    """Analisador de arquivos BMP"""

    skill_id = "bmp_analysis"
    name = "BMP Analyzer"
    description = "Analisa imagens BMP (Bitmap)"
    supported_formats = [MediaFormat.BMP]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.BMP,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        try:
            with open(file_path, "rb") as f:
                # File header
                signature = f.read(2)
                if signature != b'BM':
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.IMAGE,
                        format=MediaFormat.BMP,
                        file_path=file_path,
                        error="Arquivo nao e um BMP valido"
                    )

                file_size = struct.unpack("<I", f.read(4))[0]
                f.read(4)  # Reserved
                data_offset = struct.unpack("<I", f.read(4))[0]

                # DIB header
                header_size = struct.unpack("<I", f.read(4))[0]
                width = struct.unpack("<i", f.read(4))[0]
                height = struct.unpack("<i", f.read(4))[0]
                planes = struct.unpack("<H", f.read(2))[0]
                bit_depth = struct.unpack("<H", f.read(2))[0]
                compression = struct.unpack("<I", f.read(4))[0]
                image_size = struct.unpack("<I", f.read(4))[0]
                h_resolution = struct.unpack("<i", f.read(4))[0]
                v_resolution = struct.unpack("<i", f.read(4))[0]

                # Compression types
                compressions = {
                    0: "None (BI_RGB)",
                    1: "RLE8",
                    2: "RLE4",
                    3: "Bitfields",
                    4: "JPEG",
                    5: "PNG"
                }

                height = abs(height)  # Height pode ser negativo

                # Color mode
                color_modes = {
                    1: "Monochrome",
                    4: "16 colors",
                    8: "256 colors",
                    16: "High Color",
                    24: "True Color",
                    32: "True Color + Alpha"
                }

                metadata = {
                    "image": {
                        "width": width,
                        "height": height,
                        "resolution": f"{width}x{height}",
                        "bit_depth": bit_depth,
                        "color_mode": color_modes.get(bit_depth, f"{bit_depth}-bit"),
                        "compression": compressions.get(compression, "Unknown"),
                        "dpi_h": round(h_resolution / 39.3701) if h_resolution > 0 else 72,
                        "dpi_v": round(v_resolution / 39.3701) if v_resolution > 0 else 72,
                        "file_size": file_size,
                        "file_size_formatted": self._format_size(file_size),
                        "header_size": header_size,
                        "data_offset": data_offset,
                        "aspect_ratio": round(width / height, 2) if height > 0 else 0,
                        "megapixels": round((width * height) / 1_000_000, 2)
                    }
                }

                return AnalysisResult(
                    success=True,
                    media_type=MediaType.IMAGE,
                    format=MediaFormat.BMP,
                    file_path=file_path,
                    metadata=metadata,
                    summary=f"BMP {width}x{height} {bit_depth}bit"
                )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.BMP,
                file_path=file_path,
                error=str(e)
            )

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE WEBP
# =============================================================================

class WebPAnalyzer(MediaAnalyzer):
    """Analisador de arquivos WebP"""

    skill_id = "webp_analysis"
    name = "WebP Analyzer"
    description = "Analisa imagens WebP (lossy, lossless, animated)"
    supported_formats = [MediaFormat.WEBP]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.WEBP,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        try:
            with open(file_path, "rb") as f:
                # RIFF header
                riff = f.read(4)
                if riff != b'RIFF':
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.IMAGE,
                        format=MediaFormat.WEBP,
                        file_path=file_path,
                        error="Arquivo nao e um WebP valido"
                    )

                file_size = struct.unpack("<I", f.read(4))[0] + 8
                webp = f.read(4)
                if webp != b'WEBP':
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.IMAGE,
                        format=MediaFormat.WEBP,
                        file_path=file_path,
                        error="Arquivo nao e um WebP valido"
                    )

                width = height = 0
                is_lossy = False
                is_lossless = False
                is_animated = False
                has_alpha = False
                frame_count = 1

                while True:
                    chunk_header = f.read(4)
                    if len(chunk_header) < 4:
                        break

                    chunk_type = chunk_header.decode("ascii", errors="ignore")
                    chunk_size = struct.unpack("<I", f.read(4))[0]
                    chunk_data = f.read(chunk_size)

                    # Padding byte
                    if chunk_size % 2 == 1:
                        f.read(1)

                    if chunk_type == "VP8 ":  # Lossy
                        is_lossy = True
                        if len(chunk_data) >= 10:
                            # Skip frame tag (3 bytes) + start code (3 bytes)
                            w = struct.unpack("<H", chunk_data[6:8])[0] & 0x3FFF
                            h = struct.unpack("<H", chunk_data[8:10])[0] & 0x3FFF
                            if w > 0 and h > 0:
                                width, height = w, h

                    elif chunk_type == "VP8L":  # Lossless
                        is_lossless = True
                        if len(chunk_data) >= 5:
                            signature = chunk_data[0]
                            bits = struct.unpack("<I", chunk_data[1:5])[0]
                            w = (bits & 0x3FFF) + 1
                            h = ((bits >> 14) & 0x3FFF) + 1
                            has_alpha = ((bits >> 28) & 1) == 1
                            if w > 0 and h > 0:
                                width, height = w, h

                    elif chunk_type == "VP8X":  # Extended
                        if len(chunk_data) >= 10:
                            flags = chunk_data[0]
                            has_alpha = (flags & 0x10) != 0
                            is_animated = (flags & 0x02) != 0
                            w = struct.unpack("<I", chunk_data[4:7] + b'\x00')[0] + 1
                            h = struct.unpack("<I", chunk_data[7:10] + b'\x00')[0] + 1
                            width, height = w, h

                    elif chunk_type == "ANIM":  # Animation
                        is_animated = True

                    elif chunk_type == "ANMF":  # Animation frame
                        frame_count += 1

                compression = "lossless" if is_lossless else "lossy"

                metadata = {
                    "image": {
                        "width": width,
                        "height": height,
                        "resolution": f"{width}x{height}",
                        "compression": compression,
                        "has_alpha": has_alpha,
                        "is_animated": is_animated,
                        "frame_count": frame_count if is_animated else 1,
                        "file_size": file_size,
                        "file_size_formatted": self._format_size(file_size),
                        "aspect_ratio": round(width / height, 2) if height > 0 else 0,
                        "megapixels": round((width * height) / 1_000_000, 2)
                    }
                }

                summary = f"WebP {width}x{height} {compression}"
                if is_animated:
                    summary += f" animated ({frame_count} frames)"

                return AnalysisResult(
                    success=True,
                    media_type=MediaType.IMAGE,
                    format=MediaFormat.WEBP,
                    file_path=file_path,
                    metadata=metadata,
                    summary=summary
                )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.WEBP,
                file_path=file_path,
                error=str(e)
            )

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE SVG
# =============================================================================

class SVGAnalyzer(MediaAnalyzer):
    """Analisador de arquivos SVG"""

    skill_id = "svg_analysis"
    name = "SVG Analyzer"
    description = "Analisa imagens vetoriais SVG"
    supported_formats = [MediaFormat.SVG]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.SVG,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Verifica se e SVG
            if "<svg" not in content.lower():
                return AnalysisResult(
                    success=False,
                    media_type=MediaType.IMAGE,
                    format=MediaFormat.SVG,
                    file_path=file_path,
                    error="Arquivo nao e um SVG valido"
                )

            # Extrai atributos do elemento svg
            import re

            width = height = "100%"
            viewbox = ""

            svg_match = re.search(r'<svg[^>]*>', content, re.IGNORECASE)
            if svg_match:
                svg_tag = svg_match.group()

                width_match = re.search(r'width=["\']([^"\']+)["\']', svg_tag)
                height_match = re.search(r'height=["\']([^"\']+)["\']', svg_tag)
                viewbox_match = re.search(r'viewBox=["\']([^"\']+)["\']', svg_tag)

                if width_match:
                    width = width_match.group(1)
                if height_match:
                    height = height_match.group(1)
                if viewbox_match:
                    viewbox = viewbox_match.group(1)

            # Conta elementos
            elements = {
                "path": len(re.findall(r'<path', content, re.IGNORECASE)),
                "rect": len(re.findall(r'<rect', content, re.IGNORECASE)),
                "circle": len(re.findall(r'<circle', content, re.IGNORECASE)),
                "ellipse": len(re.findall(r'<ellipse', content, re.IGNORECASE)),
                "line": len(re.findall(r'<line', content, re.IGNORECASE)),
                "polygon": len(re.findall(r'<polygon', content, re.IGNORECASE)),
                "polyline": len(re.findall(r'<polyline', content, re.IGNORECASE)),
                "text": len(re.findall(r'<text', content, re.IGNORECASE)),
                "image": len(re.findall(r'<image', content, re.IGNORECASE)),
                "g": len(re.findall(r'<g', content, re.IGNORECASE)),
            }

            total_elements = sum(elements.values())

            # Verifica animacoes
            has_animation = bool(re.search(r'<animate|<animateTransform|<animateMotion', content, re.IGNORECASE))

            # Verifica estilos
            has_css = bool(re.search(r'<style', content, re.IGNORECASE))
            has_script = bool(re.search(r'<script', content, re.IGNORECASE))

            file_size = path.stat().st_size

            metadata = {
                "image": {
                    "width": width,
                    "height": height,
                    "viewBox": viewbox,
                    "format": "SVG (Scalable Vector Graphics)",
                    "type": "vector",
                    "elements": elements,
                    "total_elements": total_elements,
                    "has_animation": has_animation,
                    "has_css": has_css,
                    "has_script": has_script,
                    "file_size": file_size,
                    "file_size_formatted": self._format_size(file_size),
                    "lines": content.count('\n') + 1
                }
            }

            summary = f"SVG {width}x{height} ({total_elements} elements)"
            if has_animation:
                summary += " animated"

            return AnalysisResult(
                success=True,
                media_type=MediaType.IMAGE,
                format=MediaFormat.SVG,
                file_path=file_path,
                metadata=metadata,
                summary=summary
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.SVG,
                file_path=file_path,
                error=str(e)
            )

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE TIFF
# =============================================================================

class TIFFAnalyzer(MediaAnalyzer):
    """Analisador de arquivos TIFF"""

    skill_id = "tiff_analysis"
    name = "TIFF Analyzer"
    description = "Analisa imagens TIFF"
    supported_formats = [MediaFormat.TIFF]

    # TIFF Tags
    TIFF_TAGS = {
        256: "ImageWidth",
        257: "ImageLength",
        258: "BitsPerSample",
        259: "Compression",
        262: "PhotometricInterpretation",
        270: "ImageDescription",
        271: "Make",
        272: "Model",
        273: "StripOffsets",
        274: "Orientation",
        277: "SamplesPerPixel",
        282: "XResolution",
        283: "YResolution",
        296: "ResolutionUnit",
        305: "Software",
        306: "DateTime",
    }

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.TIFF,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        try:
            with open(file_path, "rb") as f:
                # Byte order
                byte_order = f.read(2)
                if byte_order == b'II':
                    endian = "<"
                elif byte_order == b'MM':
                    endian = ">"
                else:
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.IMAGE,
                        format=MediaFormat.TIFF,
                        file_path=file_path,
                        error="Arquivo nao e um TIFF valido"
                    )

                # Magic number
                magic = struct.unpack(f"{endian}H", f.read(2))[0]
                if magic != 42:
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.IMAGE,
                        format=MediaFormat.TIFF,
                        file_path=file_path,
                        error="Arquivo nao e um TIFF valido"
                    )

                # First IFD offset
                ifd_offset = struct.unpack(f"{endian}I", f.read(4))[0]

                tags = {}
                page_count = 0

                while ifd_offset > 0:
                    page_count += 1
                    f.seek(ifd_offset)

                    num_entries = struct.unpack(f"{endian}H", f.read(2))[0]

                    for i in range(min(num_entries, 50)):
                        tag = struct.unpack(f"{endian}H", f.read(2))[0]
                        tag_type = struct.unpack(f"{endian}H", f.read(2))[0]
                        count = struct.unpack(f"{endian}I", f.read(4))[0]
                        value_offset = f.read(4)

                        tag_name = self.TIFF_TAGS.get(tag, f"Tag_{tag}")

                        # Parse value based on type
                        if tag_type == 3 and count == 1:  # SHORT
                            value = struct.unpack(f"{endian}H", value_offset[:2])[0]
                            tags[tag_name] = value
                        elif tag_type == 4 and count == 1:  # LONG
                            value = struct.unpack(f"{endian}I", value_offset)[0]
                            tags[tag_name] = value

                    # Next IFD offset
                    next_ifd = struct.unpack(f"{endian}I", f.read(4))[0]
                    if next_ifd == ifd_offset or page_count > 100:
                        break
                    ifd_offset = next_ifd

                width = tags.get("ImageWidth", 0)
                height = tags.get("ImageLength", 0)
                bits = tags.get("BitsPerSample", 8)
                samples = tags.get("SamplesPerPixel", 1)
                compression = tags.get("Compression", 1)

                compression_types = {
                    1: "None",
                    2: "CCITT Group 3",
                    3: "CCITT Group 4",
                    5: "LZW",
                    6: "JPEG (old)",
                    7: "JPEG",
                    8: "Deflate",
                    32773: "PackBits"
                }

                file_size = path.stat().st_size

                metadata = {
                    "image": {
                        "width": width,
                        "height": height,
                        "resolution": f"{width}x{height}",
                        "bit_depth": bits * samples,
                        "samples_per_pixel": samples,
                        "compression": compression_types.get(compression, f"Unknown ({compression})"),
                        "pages": page_count,
                        "is_multipage": page_count > 1,
                        "byte_order": "Little Endian" if endian == "<" else "Big Endian",
                        "file_size": file_size,
                        "file_size_formatted": self._format_size(file_size),
                        "aspect_ratio": round(width / height, 2) if height > 0 else 0,
                        "megapixels": round((width * height) / 1_000_000, 2)
                    },
                    "tags": {k: v for k, v in tags.items() if not k.startswith("Tag_")}
                }

                summary = f"TIFF {width}x{height} {bits*samples}bit"
                if page_count > 1:
                    summary += f" ({page_count} pages)"

                return AnalysisResult(
                    success=True,
                    media_type=MediaType.IMAGE,
                    format=MediaFormat.TIFF,
                    file_path=file_path,
                    metadata=metadata,
                    summary=summary
                )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.TIFF,
                file_path=file_path,
                error=str(e)
            )

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR DE ICO
# =============================================================================

class ICOAnalyzer(MediaAnalyzer):
    """Analisador de arquivos ICO (icones)"""

    skill_id = "ico_analysis"
    name = "ICO Analyzer"
    description = "Analisa arquivos de icone ICO"
    supported_formats = [MediaFormat.ICO]

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.ICO,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        try:
            with open(file_path, "rb") as f:
                # Header
                reserved = struct.unpack("<H", f.read(2))[0]
                image_type = struct.unpack("<H", f.read(2))[0]
                image_count = struct.unpack("<H", f.read(2))[0]

                if reserved != 0 or image_type not in [1, 2]:
                    return AnalysisResult(
                        success=False,
                        media_type=MediaType.IMAGE,
                        format=MediaFormat.ICO,
                        file_path=file_path,
                        error="Arquivo nao e um ICO valido"
                    )

                images = []
                for i in range(min(image_count, 50)):
                    width = f.read(1)[0] or 256
                    height = f.read(1)[0] or 256
                    colors = f.read(1)[0]
                    f.read(1)  # Reserved
                    planes = struct.unpack("<H", f.read(2))[0]
                    bits = struct.unpack("<H", f.read(2))[0]
                    size = struct.unpack("<I", f.read(4))[0]
                    offset = struct.unpack("<I", f.read(4))[0]

                    images.append({
                        "width": width,
                        "height": height,
                        "resolution": f"{width}x{height}",
                        "colors": colors if colors > 0 else (2 ** bits if bits > 0 else "True Color"),
                        "bit_depth": bits,
                        "size": size
                    })

                file_size = path.stat().st_size
                type_name = "ICO" if image_type == 1 else "CUR"

                # Encontra maior imagem
                largest = max(images, key=lambda x: x["width"] * x["height"]) if images else None

                metadata = {
                    "image": {
                        "format": type_name,
                        "image_count": image_count,
                        "images": images,
                        "largest": largest,
                        "file_size": file_size,
                        "file_size_formatted": self._format_size(file_size)
                    }
                }

                sizes = ", ".join([f"{img['width']}x{img['height']}" for img in images[:5]])
                summary = f"{type_name} {image_count} images ({sizes})"

                return AnalysisResult(
                    success=True,
                    media_type=MediaType.IMAGE,
                    format=MediaFormat.ICO,
                    file_path=file_path,
                    metadata=metadata,
                    summary=summary
                )

        except Exception as e:
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.ICO,
                file_path=file_path,
                error=str(e)
            )

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# =============================================================================
# ANALISADOR GENERICO DE IMAGENS
# =============================================================================

class ImageAnalyzer(MediaAnalyzer):
    """Analisador generico que detecta e delega para analisadores especificos"""

    skill_id = "image_analysis"
    name = "Image Analyzer"
    description = "Analisa imagens de diversos formatos automaticamente"
    supported_formats = [
        MediaFormat.PNG, MediaFormat.JPG, MediaFormat.GIF,
        MediaFormat.BMP, MediaFormat.WEBP, MediaFormat.SVG,
        MediaFormat.TIFF, MediaFormat.ICO
    ]

    def __init__(self):
        self._analyzers = {
            MediaFormat.PNG: PNGAnalyzer(),
            MediaFormat.JPG: JPEGAnalyzer(),
            MediaFormat.GIF: GIFAnalyzer(),
            MediaFormat.BMP: BMPAnalyzer(),
            MediaFormat.WEBP: WebPAnalyzer(),
            MediaFormat.SVG: SVGAnalyzer(),
            MediaFormat.TIFF: TIFFAnalyzer(),
            MediaFormat.ICO: ICOAnalyzer(),
        }

    def analyze(self, file_path: str, options: Dict = None) -> AnalysisResult:
        path = Path(file_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.UNKNOWN,
                file_path=file_path,
                error="Arquivo nao encontrado"
            )

        # Detecta formato pela extensao
        ext = path.suffix.lower().lstrip(".")
        format_map = {
            "png": MediaFormat.PNG,
            "jpg": MediaFormat.JPG,
            "jpeg": MediaFormat.JPG,
            "gif": MediaFormat.GIF,
            "bmp": MediaFormat.BMP,
            "webp": MediaFormat.WEBP,
            "svg": MediaFormat.SVG,
            "tiff": MediaFormat.TIFF,
            "tif": MediaFormat.TIFF,
            "ico": MediaFormat.ICO,
        }

        fmt = format_map.get(ext)
        if not fmt:
            # Tenta detectar pelo header
            fmt = self._detect_by_header(file_path)

        if not fmt:
            return AnalysisResult(
                success=False,
                media_type=MediaType.IMAGE,
                format=MediaFormat.UNKNOWN,
                file_path=file_path,
                error=f"Formato de imagem nao suportado: {ext}"
            )

        analyzer = self._analyzers.get(fmt)
        if analyzer:
            return analyzer.analyze(file_path, options)

        return AnalysisResult(
            success=False,
            media_type=MediaType.IMAGE,
            format=fmt,
            file_path=file_path,
            error=f"Analisador nao disponivel para formato: {fmt.value}"
        )

    def _detect_by_header(self, file_path: str) -> Optional[MediaFormat]:
        """Detecta formato pelo header do arquivo"""
        try:
            with open(file_path, "rb") as f:
                header = f.read(12)

            if header[:8] == b'\x89PNG\r\n\x1a\n':
                return MediaFormat.PNG
            elif header[:2] == b'\xff\xd8':
                return MediaFormat.JPG
            elif header[:6] in [b'GIF87a', b'GIF89a']:
                return MediaFormat.GIF
            elif header[:2] == b'BM':
                return MediaFormat.BMP
            elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                return MediaFormat.WEBP
            elif header[:4] in [b'II*\x00', b'MM\x00*']:
                return MediaFormat.TIFF
            elif header[:4] == b'\x00\x00\x01\x00':
                return MediaFormat.ICO

        except Exception:
            pass

        return None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ImageFormat",
    "ImageMetadata",
    "PNGAnalyzer",
    "JPEGAnalyzer",
    "GIFAnalyzer",
    "BMPAnalyzer",
    "WebPAnalyzer",
    "SVGAnalyzer",
    "TIFFAnalyzer",
    "ICOAnalyzer",
    "ImageAnalyzer",
]
