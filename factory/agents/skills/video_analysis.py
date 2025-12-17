"""
Analise de Video
================

Skills para analise de arquivos de video:
- MP4 (MPEG-4 Part 14)
- AVI (Audio Video Interleave)
- MKV (Matroska)
- MOV (QuickTime)
- WEBM (WebM)
- WMV (Windows Media Video)
- FLV (Flash Video)

Funcionalidades:
- Extracao de metadados (duracao, resolucao, FPS)
- Analise de codecs
- Deteccao de streams (video, audio, legendas)
- Estatisticas de qualidade
- Extracao de thumbnails (quando possivel)
"""

import json
import struct
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .multimedia_base import (
    AnalysisResult,
    MediaAnalyzer,
    MediaFormat,
    MediaType
)


@dataclass
class VideoStream:
    """Informacoes de um stream de video"""
    codec: str = ""
    width: int = 0
    height: int = 0
    fps: float = 0.0
    bitrate_kbps: int = 0
    duration_seconds: float = 0.0
    frame_count: int = 0
    color_space: str = ""
    bit_depth: int = 8


@dataclass
class AudioStream:
    """Informacoes de um stream de audio"""
    codec: str = ""
    channels: int = 0
    sample_rate: int = 0
    bitrate_kbps: int = 0
    language: str = ""


@dataclass
class SubtitleStream:
    """Informacoes de um stream de legendas"""
    codec: str = ""
    language: str = ""
    title: str = ""


@dataclass
class VideoMetadata:
    """Metadados completos de arquivo de video"""
    container_format: str = ""
    duration_seconds: float = 0.0
    total_bitrate_kbps: int = 0

    video_streams: List[VideoStream] = field(default_factory=list)
    audio_streams: List[AudioStream] = field(default_factory=list)
    subtitle_streams: List[SubtitleStream] = field(default_factory=list)

    # Metadados adicionais
    title: Optional[str] = None
    creation_date: Optional[str] = None
    encoder: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


class VideoAnalyzer(MediaAnalyzer):
    """
    Analisador de Video

    Analisa arquivos de video e extrai metadados e caracteristicas.
    Implementacao pura em Python, sem dependencias externas.
    """

    supported_formats = [
        MediaFormat.MP4,
        MediaFormat.AVI,
        MediaFormat.MKV,
        MediaFormat.MOV,
        MediaFormat.WEBM,
        MediaFormat.WMV,
        MediaFormat.FLV
    ]
    skill_name = "video_analysis"
    skill_description = "Analise de arquivos de video (MP4, AVI, MKV, etc.)"
    skill_category = "video"

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa arquivo de video"""
        path = Path(path)
        fmt = MediaFormat.from_path(path)

        result = AnalysisResult(
            file_path=str(path),
            media_type=MediaType.VIDEO,
            media_format=fmt,
            success=False
        )

        try:
            # Metadados basicos do arquivo
            result.metadata = self.extract_metadata(path)

            # Analise especifica por formato
            if fmt in [MediaFormat.MP4, MediaFormat.MOV]:
                video_meta = self._analyze_mp4(path)
            elif fmt == MediaFormat.AVI:
                video_meta = self._analyze_avi(path)
            elif fmt == MediaFormat.MKV:
                video_meta = self._analyze_mkv(path)
            elif fmt == MediaFormat.WEBM:
                video_meta = self._analyze_webm(path)
            elif fmt == MediaFormat.FLV:
                video_meta = self._analyze_flv(path)
            else:
                video_meta = self._analyze_generic(path)

            # Adiciona metadados de video
            result.metadata['video'] = self._format_video_metadata(video_meta)

            # Estatisticas
            result.stats = self._calculate_stats(video_meta, path)

            # Gera resumo
            result.content_summary = self._generate_video_summary(video_meta)

            result.success = True
            self._success_count += 1

        except Exception as e:
            result.errors.append(f"Erro ao analisar video: {str(e)}")

        self._analysis_count += 1
        return result

    def _analyze_mp4(self, path: Path) -> VideoMetadata:
        """Analisa arquivo MP4/MOV"""
        meta = VideoMetadata(container_format="MP4/MOV")

        with open(path, 'rb') as f:
            meta = self._parse_mp4_atoms(f, meta, path.stat().st_size)

        return meta

    def _parse_mp4_atoms(self, f, meta: VideoMetadata, file_size: int, depth: int = 0) -> VideoMetadata:
        """Parse recursivo de atoms MP4"""
        if depth > 10:  # Previne recursao infinita
            return meta

        container_atoms = ['moov', 'trak', 'mdia', 'minf', 'stbl', 'udta', 'meta', 'ilst']

        while f.tell() < file_size:
            pos = f.tell()
            header = f.read(8)

            if len(header) < 8:
                break

            size = struct.unpack('>I', header[:4])[0]
            atom_type = header[4:8].decode('latin-1', errors='ignore')

            if size == 0:
                # Atom ate o final do arquivo
                size = file_size - pos
            elif size == 1:
                # Extended size
                ext_header = f.read(8)
                if len(ext_header) < 8:
                    break
                size = struct.unpack('>Q', ext_header)[0]

            if size < 8 or pos + size > file_size:
                break

            atom_end = pos + size

            if atom_type in container_atoms:
                # Container atom - parse recursivamente
                if atom_type == 'meta':
                    f.read(4)  # Skip version/flags
                    meta = self._parse_mp4_atoms(f, meta, atom_end - 4, depth + 1)
                else:
                    meta = self._parse_mp4_atoms(f, meta, atom_end, depth + 1)

            elif atom_type == 'mvhd':
                # Movie header
                meta = self._parse_mvhd(f, meta)

            elif atom_type == 'tkhd':
                # Track header
                meta = self._parse_tkhd(f, meta)

            elif atom_type == 'hdlr':
                # Handler reference
                pass  # Usado para identificar tipo de track

            elif atom_type == 'stsd':
                # Sample description
                meta = self._parse_stsd(f, meta, size - 8)

            elif atom_type == 'stts':
                # Time to sample
                meta = self._parse_stts(f, meta)

            # Avanca para proximo atom
            f.seek(atom_end)

        return meta

    def _parse_mvhd(self, f, meta: VideoMetadata) -> VideoMetadata:
        """Parse movie header"""
        version = struct.unpack('>B', f.read(1))[0]
        f.read(3)  # flags

        if version == 1:
            f.read(8)  # creation_time
            f.read(8)  # modification_time
            timescale = struct.unpack('>I', f.read(4))[0]
            duration = struct.unpack('>Q', f.read(8))[0]
        else:
            f.read(4)  # creation_time
            f.read(4)  # modification_time
            timescale = struct.unpack('>I', f.read(4))[0]
            duration = struct.unpack('>I', f.read(4))[0]

        if timescale > 0:
            meta.duration_seconds = duration / timescale

        return meta

    def _parse_tkhd(self, f, meta: VideoMetadata) -> VideoMetadata:
        """Parse track header"""
        data = f.read(84)
        if len(data) < 84:
            return meta

        version = data[0]

        if version == 1:
            # 64-bit timestamps
            width = struct.unpack('>I', data[76:80])[0] >> 16
            height = struct.unpack('>I', data[80:84])[0] >> 16
        else:
            width = struct.unpack('>I', data[76:80])[0] >> 16
            height = struct.unpack('>I', data[80:84])[0] >> 16

        if width > 0 and height > 0:
            # E um track de video
            if not meta.video_streams:
                meta.video_streams.append(VideoStream())
            meta.video_streams[-1].width = width
            meta.video_streams[-1].height = height

        return meta

    def _parse_stsd(self, f, meta: VideoMetadata, size: int) -> VideoMetadata:
        """Parse sample description"""
        data = f.read(min(size, 200))  # Le ate 200 bytes
        if len(data) < 16:
            return meta

        entry_count = struct.unpack('>I', data[4:8])[0]
        if entry_count == 0:
            return meta

        # Primeiro entry
        entry_size = struct.unpack('>I', data[8:12])[0]
        entry_type = data[12:16].decode('latin-1', errors='ignore')

        # Codecs de video comuns
        video_codecs = {
            'avc1': 'H.264/AVC',
            'hvc1': 'H.265/HEVC',
            'hev1': 'H.265/HEVC',
            'vp09': 'VP9',
            'av01': 'AV1',
            'mp4v': 'MPEG-4',
            'mjpg': 'Motion JPEG',
            'jpeg': 'JPEG'
        }

        # Codecs de audio comuns
        audio_codecs = {
            'mp4a': 'AAC',
            'ac-3': 'AC-3',
            'ec-3': 'E-AC-3',
            'opus': 'Opus',
            'alac': 'Apple Lossless',
            'alaw': 'A-Law',
            'ulaw': 'mu-Law'
        }

        if entry_type in video_codecs:
            if not meta.video_streams:
                meta.video_streams.append(VideoStream())
            meta.video_streams[-1].codec = video_codecs[entry_type]

            # Resolucao esta nos bytes 24-28 do entry
            if len(data) >= 40:
                width = struct.unpack('>H', data[32:34])[0]
                height = struct.unpack('>H', data[34:36])[0]
                if width > 0 and height > 0:
                    meta.video_streams[-1].width = width
                    meta.video_streams[-1].height = height

        elif entry_type in audio_codecs:
            audio = AudioStream(codec=audio_codecs[entry_type])

            if len(data) >= 36:
                audio.channels = struct.unpack('>H', data[24:26])[0]
                audio.sample_rate = struct.unpack('>I', data[30:34])[0] >> 16

            meta.audio_streams.append(audio)

        return meta

    def _parse_stts(self, f, meta: VideoMetadata) -> VideoMetadata:
        """Parse time-to-sample para calcular FPS"""
        data = f.read(16)
        if len(data) < 16:
            return meta

        entry_count = struct.unpack('>I', data[4:8])[0]

        if entry_count > 0:
            sample_count = struct.unpack('>I', data[8:12])[0]
            sample_delta = struct.unpack('>I', data[12:16])[0]

            if meta.video_streams and sample_delta > 0:
                # FPS = timescale / sample_delta
                # Usamos estimativa comum de 1000 se nao tivermos timescale
                timescale = 1000
                meta.video_streams[-1].fps = round(timescale / sample_delta, 2)
                meta.video_streams[-1].frame_count = sample_count

        return meta

    def _analyze_avi(self, path: Path) -> VideoMetadata:
        """Analisa arquivo AVI"""
        meta = VideoMetadata(container_format="AVI")

        with open(path, 'rb') as f:
            # Verifica RIFF header
            riff = f.read(12)
            if riff[:4] != b'RIFF' or riff[8:12] != b'AVI ':
                return meta

            file_size = struct.unpack('<I', riff[4:8])[0]

            # Parse chunks
            while f.tell() < file_size:
                chunk_header = f.read(8)
                if len(chunk_header) < 8:
                    break

                chunk_id = chunk_header[:4]
                chunk_size = struct.unpack('<I', chunk_header[4:8])[0]

                if chunk_id == b'LIST':
                    list_type = f.read(4)

                    if list_type == b'hdrl':
                        # Header list
                        meta = self._parse_avi_header_list(f, meta, chunk_size - 4)
                    elif list_type == b'strl':
                        # Stream list
                        meta = self._parse_avi_stream_list(f, meta, chunk_size - 4)
                    else:
                        f.seek(chunk_size - 4, 1)
                else:
                    f.seek(chunk_size, 1)

                # Alinha em 2 bytes
                if chunk_size % 2:
                    f.read(1)

        return meta

    def _parse_avi_header_list(self, f, meta: VideoMetadata, size: int) -> VideoMetadata:
        """Parse AVI header list"""
        end_pos = f.tell() + size

        while f.tell() < end_pos:
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                break

            chunk_id = chunk_header[:4]
            chunk_size = struct.unpack('<I', chunk_header[4:8])[0]

            if chunk_id == b'avih':
                # Main AVI header
                data = f.read(min(chunk_size, 56))
                if len(data) >= 32:
                    micro_sec_per_frame = struct.unpack('<I', data[:4])[0]
                    meta.total_bitrate_kbps = struct.unpack('<I', data[4:8])[0] * 8 // 1000
                    total_frames = struct.unpack('<I', data[16:20])[0]
                    width = struct.unpack('<I', data[32:36])[0] if len(data) >= 36 else 0
                    height = struct.unpack('<I', data[36:40])[0] if len(data) >= 40 else 0

                    if micro_sec_per_frame > 0:
                        fps = 1000000 / micro_sec_per_frame
                        meta.duration_seconds = total_frames / fps if fps > 0 else 0

                        vs = VideoStream(
                            width=width,
                            height=height,
                            fps=round(fps, 2),
                            frame_count=total_frames
                        )
                        meta.video_streams.append(vs)

                f.seek(chunk_size - len(data), 1)
            else:
                f.seek(chunk_size, 1)

            if chunk_size % 2:
                f.read(1)

        return meta

    def _parse_avi_stream_list(self, f, meta: VideoMetadata, size: int) -> VideoMetadata:
        """Parse AVI stream list"""
        end_pos = f.tell() + size

        while f.tell() < end_pos:
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                break

            chunk_id = chunk_header[:4]
            chunk_size = struct.unpack('<I', chunk_header[4:8])[0]

            if chunk_id == b'strh':
                # Stream header
                data = f.read(min(chunk_size, 56))
                if len(data) >= 4:
                    stream_type = data[:4].decode('latin-1', errors='ignore')

                    if stream_type == 'vids' and len(data) >= 28:
                        codec = data[4:8].decode('latin-1', errors='ignore').strip()
                        if meta.video_streams:
                            meta.video_streams[-1].codec = self._translate_fourcc(codec)

                    elif stream_type == 'auds' and len(data) >= 28:
                        audio = AudioStream()
                        audio.codec = "PCM"  # Padrao
                        meta.audio_streams.append(audio)

                f.seek(chunk_size - len(data), 1)

            elif chunk_id == b'strf':
                # Stream format
                f.seek(chunk_size, 1)
            else:
                f.seek(chunk_size, 1)

            if chunk_size % 2:
                f.read(1)

        return meta

    def _translate_fourcc(self, fourcc: str) -> str:
        """Traduz FourCC para nome do codec"""
        fourcc_map = {
            'H264': 'H.264/AVC',
            'h264': 'H.264/AVC',
            'avc1': 'H.264/AVC',
            'X264': 'H.264/AVC',
            'x264': 'H.264/AVC',
            'XVID': 'Xvid',
            'xvid': 'Xvid',
            'DIVX': 'DivX',
            'divx': 'DivX',
            'DX50': 'DivX 5',
            'MJPG': 'Motion JPEG',
            'mjpg': 'Motion JPEG',
            'VP80': 'VP8',
            'VP90': 'VP9',
            'HEVC': 'H.265/HEVC',
            'hevc': 'H.265/HEVC',
            'AV01': 'AV1'
        }
        return fourcc_map.get(fourcc, fourcc)

    def _analyze_mkv(self, path: Path) -> VideoMetadata:
        """Analisa arquivo MKV (Matroska)"""
        meta = VideoMetadata(container_format="Matroska/MKV")

        with open(path, 'rb') as f:
            # Verifica EBML header
            ebml_id = f.read(4)
            if ebml_id != b'\x1a\x45\xdf\xa3':
                return meta

            # Pula EBML header
            ebml_size = self._read_vint(f)
            f.seek(ebml_size, 1)

            # Segment
            seg_id = f.read(4)
            if seg_id == b'\x18\x53\x80\x67':
                seg_size = self._read_vint(f)

                # Parse segment children (ate Info e Tracks)
                end_pos = min(f.tell() + seg_size, f.tell() + 10000)  # Limita busca

                while f.tell() < end_pos:
                    elem_id = self._read_element_id(f)
                    if elem_id is None:
                        break

                    elem_size = self._read_vint(f)
                    if elem_size is None:
                        break

                    if elem_id == 0x1549A966:  # Info
                        meta = self._parse_mkv_info(f, meta, elem_size)
                    elif elem_id == 0x1654AE6B:  # Tracks
                        meta = self._parse_mkv_tracks(f, meta, elem_size)
                        break  # Ja temos o que precisamos
                    else:
                        f.seek(elem_size, 1)

        return meta

    def _read_vint(self, f) -> Optional[int]:
        """Le um VINT (variable integer) do Matroska"""
        first = f.read(1)
        if not first:
            return None

        first_byte = first[0]

        # Determina tamanho pelo numero de zeros a esquerda
        if first_byte & 0x80:
            size = 1
            value = first_byte & 0x7F
        elif first_byte & 0x40:
            size = 2
            value = first_byte & 0x3F
        elif first_byte & 0x20:
            size = 3
            value = first_byte & 0x1F
        elif first_byte & 0x10:
            size = 4
            value = first_byte & 0x0F
        else:
            return None

        # Le bytes restantes
        for _ in range(size - 1):
            b = f.read(1)
            if not b:
                return None
            value = (value << 8) | b[0]

        return value

    def _read_element_id(self, f) -> Optional[int]:
        """Le um Element ID do Matroska"""
        first = f.read(1)
        if not first:
            return None

        first_byte = first[0]

        if first_byte & 0x80:
            return first_byte
        elif first_byte & 0x40:
            second = f.read(1)
            if not second:
                return None
            return (first_byte << 8) | second[0]
        elif first_byte & 0x20:
            rest = f.read(2)
            if len(rest) < 2:
                return None
            return (first_byte << 16) | (rest[0] << 8) | rest[1]
        elif first_byte & 0x10:
            rest = f.read(3)
            if len(rest) < 3:
                return None
            return (first_byte << 24) | (rest[0] << 16) | (rest[1] << 8) | rest[2]

        return None

    def _parse_mkv_info(self, f, meta: VideoMetadata, size: int) -> VideoMetadata:
        """Parse MKV Segment Info"""
        end_pos = f.tell() + size
        timescale = 1000000  # Padrao

        while f.tell() < end_pos:
            elem_id = self._read_element_id(f)
            if elem_id is None:
                break

            elem_size = self._read_vint(f)
            if elem_size is None:
                break

            if elem_id == 0x2AD7B1:  # TimestampScale
                data = f.read(elem_size)
                timescale = int.from_bytes(data, 'big')
            elif elem_id == 0x4489:  # Duration
                data = f.read(elem_size)
                if elem_size == 4:
                    duration = struct.unpack('>f', data)[0]
                else:
                    duration = struct.unpack('>d', data)[0]
                meta.duration_seconds = duration * timescale / 1000000000
            elif elem_id == 0x7BA9:  # Title
                meta.title = f.read(elem_size).decode('utf-8', errors='ignore')
            else:
                f.seek(elem_size, 1)

        return meta

    def _parse_mkv_tracks(self, f, meta: VideoMetadata, size: int) -> VideoMetadata:
        """Parse MKV Tracks"""
        end_pos = f.tell() + size

        while f.tell() < end_pos:
            elem_id = self._read_element_id(f)
            if elem_id is None:
                break

            elem_size = self._read_vint(f)
            if elem_size is None:
                break

            if elem_id == 0xAE:  # TrackEntry
                meta = self._parse_mkv_track_entry(f, meta, elem_size)
            else:
                f.seek(elem_size, 1)

        return meta

    def _parse_mkv_track_entry(self, f, meta: VideoMetadata, size: int) -> VideoMetadata:
        """Parse MKV Track Entry"""
        end_pos = f.tell() + size

        track_type = 0
        codec_id = ""
        video_info = {}
        audio_info = {}

        while f.tell() < end_pos:
            elem_id = self._read_element_id(f)
            if elem_id is None:
                break

            elem_size = self._read_vint(f)
            if elem_size is None:
                break

            if elem_id == 0x83:  # TrackType
                track_type = int.from_bytes(f.read(elem_size), 'big')
            elif elem_id == 0x86:  # CodecID
                codec_id = f.read(elem_size).decode('utf-8', errors='ignore')
            elif elem_id == 0xE0:  # Video
                video_info = self._parse_mkv_video_info(f, elem_size)
            elif elem_id == 0xE1:  # Audio
                audio_info = self._parse_mkv_audio_info(f, elem_size)
            else:
                f.seek(elem_size, 1)

        # Cria stream baseado no tipo
        if track_type == 1:  # Video
            vs = VideoStream(
                codec=self._translate_mkv_codec(codec_id),
                width=video_info.get('width', 0),
                height=video_info.get('height', 0),
                fps=video_info.get('fps', 0)
            )
            meta.video_streams.append(vs)

        elif track_type == 2:  # Audio
            aus = AudioStream(
                codec=self._translate_mkv_codec(codec_id),
                channels=audio_info.get('channels', 0),
                sample_rate=int(audio_info.get('sample_rate', 0))
            )
            meta.audio_streams.append(aus)

        elif track_type == 17:  # Subtitle
            meta.subtitle_streams.append(SubtitleStream(codec=codec_id))

        return meta

    def _parse_mkv_video_info(self, f, size: int) -> Dict:
        """Parse MKV Video Info"""
        info = {}
        end_pos = f.tell() + size

        while f.tell() < end_pos:
            elem_id = self._read_element_id(f)
            if elem_id is None:
                break

            elem_size = self._read_vint(f)
            if elem_size is None:
                break

            if elem_id == 0xB0:  # PixelWidth
                info['width'] = int.from_bytes(f.read(elem_size), 'big')
            elif elem_id == 0xBA:  # PixelHeight
                info['height'] = int.from_bytes(f.read(elem_size), 'big')
            elif elem_id == 0x2383E3:  # FrameRate (deprecated but still used)
                data = f.read(elem_size)
                info['fps'] = struct.unpack('>f' if elem_size == 4 else '>d', data)[0]
            else:
                f.seek(elem_size, 1)

        return info

    def _parse_mkv_audio_info(self, f, size: int) -> Dict:
        """Parse MKV Audio Info"""
        info = {}
        end_pos = f.tell() + size

        while f.tell() < end_pos:
            elem_id = self._read_element_id(f)
            if elem_id is None:
                break

            elem_size = self._read_vint(f)
            if elem_size is None:
                break

            if elem_id == 0xB5:  # SamplingFrequency
                data = f.read(elem_size)
                info['sample_rate'] = struct.unpack('>f' if elem_size == 4 else '>d', data)[0]
            elif elem_id == 0x9F:  # Channels
                info['channels'] = int.from_bytes(f.read(elem_size), 'big')
            else:
                f.seek(elem_size, 1)

        return info

    def _translate_mkv_codec(self, codec_id: str) -> str:
        """Traduz CodecID do MKV"""
        codec_map = {
            'V_MPEG4/ISO/AVC': 'H.264/AVC',
            'V_MPEGH/ISO/HEVC': 'H.265/HEVC',
            'V_VP8': 'VP8',
            'V_VP9': 'VP9',
            'V_AV1': 'AV1',
            'V_MPEG4/ISO/SP': 'MPEG-4 SP',
            'V_MPEG4/ISO/AP': 'MPEG-4 AP',
            'A_AAC': 'AAC',
            'A_AAC/MPEG4/LC': 'AAC-LC',
            'A_AC3': 'AC-3',
            'A_EAC3': 'E-AC-3',
            'A_DTS': 'DTS',
            'A_FLAC': 'FLAC',
            'A_OPUS': 'Opus',
            'A_VORBIS': 'Vorbis',
            'A_MPEG/L3': 'MP3',
            'S_TEXT/UTF8': 'SRT',
            'S_TEXT/ASS': 'ASS/SSA',
            'S_VOBSUB': 'VobSub'
        }
        return codec_map.get(codec_id, codec_id)

    def _analyze_webm(self, path: Path) -> VideoMetadata:
        """Analisa arquivo WebM (usa mesma base do MKV)"""
        meta = self._analyze_mkv(path)
        meta.container_format = "WebM"
        return meta

    def _analyze_flv(self, path: Path) -> VideoMetadata:
        """Analisa arquivo FLV"""
        meta = VideoMetadata(container_format="FLV")

        with open(path, 'rb') as f:
            # FLV header
            header = f.read(9)
            if header[:3] != b'FLV':
                return meta

            version = header[3]
            flags = header[4]
            header_size = struct.unpack('>I', header[5:9])[0]

            has_video = flags & 0x01
            has_audio = flags & 0x04

            f.seek(header_size)

            # Parse tags
            tag_count = 0
            while tag_count < 20:  # Limita
                prev_size = f.read(4)
                if len(prev_size) < 4:
                    break

                tag_header = f.read(11)
                if len(tag_header) < 11:
                    break

                tag_type = tag_header[0]
                data_size = (tag_header[1] << 16) | (tag_header[2] << 8) | tag_header[3]
                timestamp = (tag_header[7] << 24) | (tag_header[4] << 16) | (tag_header[5] << 8) | tag_header[6]

                if tag_type == 8:  # Audio
                    audio_data = f.read(1)
                    if audio_data:
                        audio_flags = audio_data[0]
                        codec_id = (audio_flags >> 4) & 0x0F
                        sample_rate_idx = (audio_flags >> 2) & 0x03
                        channels = 2 if (audio_flags & 0x01) else 1

                        codec_map = {0: 'PCM', 2: 'MP3', 10: 'AAC', 11: 'Speex'}
                        rate_map = {0: 5512, 1: 11025, 2: 22050, 3: 44100}

                        if not meta.audio_streams:
                            meta.audio_streams.append(AudioStream(
                                codec=codec_map.get(codec_id, 'Unknown'),
                                channels=channels,
                                sample_rate=rate_map.get(sample_rate_idx, 44100)
                            ))

                    f.seek(data_size - 1, 1)

                elif tag_type == 9:  # Video
                    video_data = f.read(1)
                    if video_data:
                        video_flags = video_data[0]
                        codec_id = video_flags & 0x0F

                        codec_map = {2: 'Sorenson H.263', 4: 'VP6', 5: 'VP6 Alpha', 7: 'H.264/AVC'}

                        if not meta.video_streams:
                            meta.video_streams.append(VideoStream(
                                codec=codec_map.get(codec_id, 'Unknown')
                            ))

                    f.seek(data_size - 1, 1)

                elif tag_type == 18:  # Script data (metadata)
                    # Pode conter duracao, dimensoes, etc.
                    f.seek(data_size, 1)

                else:
                    f.seek(data_size, 1)

                tag_count += 1

                # Atualiza duracao
                meta.duration_seconds = max(meta.duration_seconds, timestamp / 1000)

        return meta

    def _analyze_generic(self, path: Path) -> VideoMetadata:
        """Analise generica para formatos nao suportados especificamente"""
        meta = VideoMetadata()
        meta.container_format = path.suffix.upper().lstrip('.')

        # Tenta detectar se e video pelo tamanho
        file_size = path.stat().st_size

        # Assume bitrate medio de 2Mbps se nao conseguir determinar
        assumed_bitrate = 2000
        meta.duration_seconds = file_size * 8 / (assumed_bitrate * 1000)
        meta.total_bitrate_kbps = assumed_bitrate

        return meta

    def _format_video_metadata(self, meta: VideoMetadata) -> Dict:
        """Formata metadados para resultado"""
        result = {
            'container': meta.container_format,
            'duration_seconds': round(meta.duration_seconds, 2),
            'duration_formatted': self._format_duration(meta.duration_seconds),
            'total_bitrate_kbps': meta.total_bitrate_kbps
        }

        if meta.video_streams:
            vs = meta.video_streams[0]  # Stream principal
            result['video'] = {
                'codec': vs.codec,
                'width': vs.width,
                'height': vs.height,
                'resolution': f"{vs.width}x{vs.height}" if vs.width and vs.height else 'Unknown',
                'resolution_name': self._get_resolution_name(vs.width, vs.height),
                'fps': vs.fps,
                'frame_count': vs.frame_count,
                'bitrate_kbps': vs.bitrate_kbps
            }

        if meta.audio_streams:
            result['audio_tracks'] = []
            for aus in meta.audio_streams:
                result['audio_tracks'].append({
                    'codec': aus.codec,
                    'channels': aus.channels,
                    'channel_layout': 'stereo' if aus.channels == 2 else 'mono' if aus.channels == 1 else f'{aus.channels}ch',
                    'sample_rate': aus.sample_rate,
                    'language': aus.language or 'und'
                })

        if meta.subtitle_streams:
            result['subtitle_tracks'] = [
                {'codec': s.codec, 'language': s.language or 'und'}
                for s in meta.subtitle_streams
            ]

        if meta.title:
            result['title'] = meta.title

        return result

    def _format_duration(self, seconds: float) -> str:
        """Formata duracao em HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _get_resolution_name(self, width: int, height: int) -> str:
        """Retorna nome da resolucao"""
        if height >= 2160:
            return "4K UHD"
        elif height >= 1440:
            return "2K QHD"
        elif height >= 1080:
            return "Full HD"
        elif height >= 720:
            return "HD"
        elif height >= 480:
            return "SD"
        elif height > 0:
            return "Low"
        return "Unknown"

    def _calculate_stats(self, meta: VideoMetadata, path: Path) -> Dict:
        """Calcula estatisticas do video"""
        stats = {
            'duration_seconds': round(meta.duration_seconds, 2),
            'file_size_mb': round(path.stat().st_size / (1024 * 1024), 2),
            'video_streams': len(meta.video_streams),
            'audio_streams': len(meta.audio_streams),
            'subtitle_streams': len(meta.subtitle_streams)
        }

        if meta.video_streams:
            vs = meta.video_streams[0]
            stats['width'] = vs.width
            stats['height'] = vs.height
            stats['fps'] = vs.fps
            stats['aspect_ratio'] = self._calculate_aspect_ratio(vs.width, vs.height)
            stats['quality_estimate'] = self._estimate_quality(vs, meta.total_bitrate_kbps)

        return stats

    def _calculate_aspect_ratio(self, width: int, height: int) -> str:
        """Calcula aspect ratio"""
        if width == 0 or height == 0:
            return "Unknown"

        ratio = width / height

        common_ratios = {
            1.33: "4:3",
            1.78: "16:9",
            1.85: "1.85:1",
            2.35: "2.35:1",
            2.39: "2.39:1",
            2.40: "2.40:1"
        }

        for r, name in common_ratios.items():
            if abs(ratio - r) < 0.1:
                return name

        return f"{ratio:.2f}:1"

    def _estimate_quality(self, vs: VideoStream, total_bitrate: int) -> str:
        """Estima qualidade do video"""
        pixels = vs.width * vs.height

        # Bitrate minimo recomendado por resolucao (kbps)
        recommended = {
            3840 * 2160: 20000,  # 4K
            2560 * 1440: 10000,  # 1440p
            1920 * 1080: 5000,   # 1080p
            1280 * 720: 2500,    # 720p
            854 * 480: 1000     # 480p
        }

        # Encontra recomendacao mais proxima
        closest_rec = 1000
        for res, rec in recommended.items():
            if pixels >= res * 0.8:
                closest_rec = rec
                break

        if total_bitrate >= closest_rec:
            return "high"
        elif total_bitrate >= closest_rec * 0.6:
            return "good"
        elif total_bitrate >= closest_rec * 0.4:
            return "medium"
        else:
            return "low"

    def _generate_video_summary(self, meta: VideoMetadata) -> str:
        """Gera resumo do video"""
        parts = []

        if meta.title:
            parts.append(meta.title)

        parts.append(meta.container_format)

        if meta.video_streams:
            vs = meta.video_streams[0]
            if vs.width and vs.height:
                res_name = self._get_resolution_name(vs.width, vs.height)
                parts.append(f"{vs.width}x{vs.height} ({res_name})")
            if vs.codec:
                parts.append(vs.codec)
            if vs.fps:
                parts.append(f"{vs.fps}fps")

        parts.append(f"Duracao: {self._format_duration(meta.duration_seconds)}")

        if meta.audio_streams:
            audio_info = f"{len(meta.audio_streams)} trilha(s) de audio"
            parts.append(audio_info)

        if meta.subtitle_streams:
            parts.append(f"{len(meta.subtitle_streams)} legenda(s)")

        return " | ".join(parts)


class FrameAnalyzer(MediaAnalyzer):
    """
    Analisador de Frames

    Analisa frames individuais de video.
    Nota: Extracao real de frames requer biblioteca externa (opencv, ffmpeg)
    """

    supported_formats = [
        MediaFormat.MP4,
        MediaFormat.AVI,
        MediaFormat.MKV,
        MediaFormat.MOV
    ]
    skill_name = "frame_analysis"
    skill_description = "Analise de frames de video (requer processamento adicional)"
    skill_category = "video"

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa frames de video"""
        # Usa VideoAnalyzer como base
        base_analyzer = VideoAnalyzer(self.agent_id)
        result = base_analyzer.analyze(path, **options)

        if not result.success:
            return result

        # Adiciona informacoes sobre frames
        try:
            video_meta = result.metadata.get('video', {}).get('video', {})

            frame_analysis = {
                "frame_count": video_meta.get('frame_count', 0),
                "fps": video_meta.get('fps', 0),
                "frame_extraction_available": False,
                "note": "Extracao de frames requer ffmpeg ou opencv"
            }

            # Estima numero de keyframes
            if frame_analysis['frame_count'] > 0 and frame_analysis['fps'] > 0:
                # Keyframe tipico a cada 2-10 segundos
                estimated_keyframes = int(frame_analysis['frame_count'] / (frame_analysis['fps'] * 5))
                frame_analysis['estimated_keyframes'] = max(1, estimated_keyframes)

            result.metadata['frame_analysis'] = frame_analysis

        except Exception as e:
            result.warnings.append(f"Analise de frames parcial: {str(e)}")

        return result


class SceneAnalyzer(MediaAnalyzer):
    """
    Analisador de Cenas

    Detecta mudancas de cena em videos.
    """

    supported_formats = [
        MediaFormat.MP4,
        MediaFormat.AVI,
        MediaFormat.MKV,
        MediaFormat.MOV
    ]
    skill_name = "scene_analysis"
    skill_description = "Analise de cenas de video (deteccao de cortes)"
    skill_category = "video"

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa cenas do video"""
        # Usa VideoAnalyzer como base
        base_analyzer = VideoAnalyzer(self.agent_id)
        result = base_analyzer.analyze(path, **options)

        if not result.success:
            return result

        try:
            video_meta = result.metadata.get('video', {}).get('video', {})
            duration = result.metadata.get('video', {}).get('duration_seconds', 0)

            scene_analysis = {
                "scene_detection_available": False,
                "note": "Deteccao de cenas requer processamento de frames",
                "estimated_scenes": self._estimate_scene_count(duration)
            }

            result.metadata['scene_analysis'] = scene_analysis

        except Exception as e:
            result.warnings.append(f"Analise de cenas parcial: {str(e)}")

        return result

    def _estimate_scene_count(self, duration: float) -> int:
        """Estima numero de cenas baseado na duracao"""
        # Cena media de 3-5 segundos para videos curtos
        # 5-10 segundos para videos longos
        if duration < 60:
            avg_scene = 3
        elif duration < 600:
            avg_scene = 5
        else:
            avg_scene = 8

        return max(1, int(duration / avg_scene))
