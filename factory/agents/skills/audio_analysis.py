"""
Analise de Audio
================

Skills para analise de arquivos de audio:
- MP3 (MPEG Audio Layer 3)
- WAV (Waveform Audio File Format)
- FLAC (Free Lossless Audio Codec)
- OGG (Ogg Vorbis)
- M4A (MPEG-4 Audio)
- AAC (Advanced Audio Coding)
- WMA (Windows Media Audio)

Funcionalidades:
- Extracao de metadados (duracao, bitrate, sample rate)
- Analise de forma de onda
- Deteccao de silencio
- Analise de espectro (basica)
- Transcricao de fala (quando disponivel API)
"""

import json
import struct
import wave
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .multimedia_base import (
    AnalysisResult,
    MediaAnalyzer,
    MediaFormat,
    MediaType
)


@dataclass
class AudioMetadata:
    """Metadados de arquivo de audio"""
    duration_seconds: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    bit_depth: int = 0
    bitrate_kbps: int = 0
    codec: str = ""
    format: str = ""

    # Tags ID3/Vorbis
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[str] = None
    genre: Optional[str] = None
    track_number: Optional[str] = None
    comment: Optional[str] = None


class AudioAnalyzer(MediaAnalyzer):
    """
    Analisador de Audio

    Analisa arquivos de audio e extrai metadados e caracteristicas.
    Implementacao pura em Python, sem dependencias externas.
    """

    supported_formats = [
        MediaFormat.MP3,
        MediaFormat.WAV,
        MediaFormat.FLAC,
        MediaFormat.OGG,
        MediaFormat.M4A,
        MediaFormat.AAC,
        MediaFormat.WMA
    ]
    skill_name = "audio_analysis"
    skill_description = "Analise de arquivos de audio (MP3, WAV, FLAC, OGG, etc.)"
    skill_category = "audio"

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa arquivo de audio"""
        path = Path(path)
        fmt = MediaFormat.from_path(path)

        result = AnalysisResult(
            file_path=str(path),
            media_type=MediaType.AUDIO,
            media_format=fmt,
            success=False
        )

        try:
            # Metadados basicos do arquivo
            result.metadata = self.extract_metadata(path)

            # Analise especifica por formato
            if fmt == MediaFormat.WAV:
                audio_meta = self._analyze_wav(path)
            elif fmt == MediaFormat.MP3:
                audio_meta = self._analyze_mp3(path)
            elif fmt == MediaFormat.FLAC:
                audio_meta = self._analyze_flac(path)
            elif fmt == MediaFormat.OGG:
                audio_meta = self._analyze_ogg(path)
            elif fmt in [MediaFormat.M4A, MediaFormat.AAC]:
                audio_meta = self._analyze_m4a(path)
            else:
                audio_meta = self._analyze_generic(path)

            # Adiciona metadados de audio
            result.metadata['audio'] = {
                'duration_seconds': round(audio_meta.duration_seconds, 2),
                'duration_formatted': self._format_duration(audio_meta.duration_seconds),
                'sample_rate': audio_meta.sample_rate,
                'channels': audio_meta.channels,
                'channel_layout': 'stereo' if audio_meta.channels == 2 else 'mono' if audio_meta.channels == 1 else f'{audio_meta.channels}ch',
                'bit_depth': audio_meta.bit_depth,
                'bitrate_kbps': audio_meta.bitrate_kbps,
                'codec': audio_meta.codec,
                'format': audio_meta.format
            }

            # Tags de metadados (ID3, Vorbis, etc.)
            tags = {}
            for tag in ['title', 'artist', 'album', 'year', 'genre', 'track_number', 'comment']:
                value = getattr(audio_meta, tag, None)
                if value:
                    tags[tag] = value

            if tags:
                result.metadata['tags'] = tags

            # Estatisticas
            result.stats = {
                'duration_seconds': round(audio_meta.duration_seconds, 2),
                'sample_rate': audio_meta.sample_rate,
                'channels': audio_meta.channels,
                'bitrate_kbps': audio_meta.bitrate_kbps,
                'estimated_quality': self._estimate_quality(audio_meta)
            }

            # Gera resumo
            result.content_summary = self._generate_audio_summary(audio_meta, tags)

            result.success = True
            self._success_count += 1

        except Exception as e:
            result.errors.append(f"Erro ao analisar audio: {str(e)}")

        self._analysis_count += 1
        return result

    def _analyze_wav(self, path: Path) -> AudioMetadata:
        """Analisa arquivo WAV"""
        meta = AudioMetadata(format="WAV", codec="PCM")

        try:
            with wave.open(str(path), 'rb') as wav:
                meta.channels = wav.getnchannels()
                meta.sample_rate = wav.getframerate()
                meta.bit_depth = wav.getsampwidth() * 8
                frames = wav.getnframes()
                meta.duration_seconds = frames / meta.sample_rate if meta.sample_rate else 0
                meta.bitrate_kbps = int(meta.sample_rate * meta.channels * meta.bit_depth / 1000)

        except Exception:
            # Fallback: parse manual do header
            with open(path, 'rb') as f:
                riff = f.read(12)
                if riff[:4] == b'RIFF' and riff[8:12] == b'WAVE':
                    while True:
                        chunk_header = f.read(8)
                        if len(chunk_header) < 8:
                            break

                        chunk_id = chunk_header[:4]
                        chunk_size = struct.unpack('<I', chunk_header[4:8])[0]

                        if chunk_id == b'fmt ':
                            fmt_data = f.read(min(chunk_size, 16))
                            if len(fmt_data) >= 16:
                                audio_format, channels, sample_rate, byte_rate, block_align, bits_per_sample = \
                                    struct.unpack('<HHIIHH', fmt_data[:16])
                                meta.channels = channels
                                meta.sample_rate = sample_rate
                                meta.bit_depth = bits_per_sample
                                meta.bitrate_kbps = byte_rate * 8 // 1000

                        elif chunk_id == b'data':
                            if meta.sample_rate and meta.channels and meta.bit_depth:
                                bytes_per_sample = meta.bit_depth // 8
                                total_samples = chunk_size // (meta.channels * bytes_per_sample)
                                meta.duration_seconds = total_samples / meta.sample_rate
                            break
                        else:
                            f.seek(chunk_size, 1)

        return meta

    def _analyze_mp3(self, path: Path) -> AudioMetadata:
        """Analisa arquivo MP3"""
        meta = AudioMetadata(format="MP3", codec="MPEG Audio Layer 3")

        with open(path, 'rb') as f:
            data = f.read()

        # Procura por tags ID3v2 no inicio
        if data[:3] == b'ID3':
            meta = self._parse_id3v2(data, meta)

        # Procura por tags ID3v1 no final
        if data[-128:-125] == b'TAG':
            meta = self._parse_id3v1(data[-128:], meta)

        # Analisa frames MP3
        meta = self._parse_mp3_frames(data, meta)

        return meta

    def _parse_id3v2(self, data: bytes, meta: AudioMetadata) -> AudioMetadata:
        """Parse ID3v2 tags"""
        try:
            version = data[3]
            flags = data[5]

            # Tamanho do header ID3 (syncsafe integer)
            size = (data[6] & 0x7f) << 21 | (data[7] & 0x7f) << 14 | \
                   (data[8] & 0x7f) << 7 | (data[9] & 0x7f)

            pos = 10
            if flags & 0x40:  # Extended header
                ext_size = struct.unpack('>I', data[pos:pos+4])[0]
                pos += ext_size

            # Parse frames
            while pos < size + 10:
                if pos + 10 > len(data):
                    break

                frame_id = data[pos:pos+4].decode('latin-1', errors='ignore')
                if not frame_id or frame_id[0] == '\x00':
                    break

                frame_size = struct.unpack('>I', data[pos+4:pos+8])[0]
                if frame_size == 0 or frame_size > size:
                    break

                frame_data = data[pos+10:pos+10+frame_size]

                # Decodifica texto
                try:
                    if frame_data and frame_data[0] == 0:
                        text = frame_data[1:].decode('latin-1', errors='ignore').strip('\x00')
                    elif frame_data and frame_data[0] == 1:
                        text = frame_data[1:].decode('utf-16', errors='ignore').strip('\x00')
                    elif frame_data and frame_data[0] == 3:
                        text = frame_data[1:].decode('utf-8', errors='ignore').strip('\x00')
                    else:
                        text = frame_data.decode('latin-1', errors='ignore').strip('\x00')

                    if frame_id in ['TIT2', 'TT2']:
                        meta.title = text
                    elif frame_id in ['TPE1', 'TP1']:
                        meta.artist = text
                    elif frame_id in ['TALB', 'TAL']:
                        meta.album = text
                    elif frame_id in ['TYER', 'TYE', 'TDRC']:
                        meta.year = text[:4]
                    elif frame_id in ['TCON', 'TCO']:
                        meta.genre = text
                    elif frame_id in ['TRCK', 'TRK']:
                        meta.track_number = text
                    elif frame_id in ['COMM', 'COM']:
                        meta.comment = text

                except:
                    pass

                pos += 10 + frame_size

        except Exception:
            pass

        return meta

    def _parse_id3v1(self, data: bytes, meta: AudioMetadata) -> AudioMetadata:
        """Parse ID3v1 tags"""
        try:
            # So usa ID3v1 se nao tiver ID3v2
            if not meta.title:
                meta.title = data[3:33].decode('latin-1', errors='ignore').strip('\x00 ')
            if not meta.artist:
                meta.artist = data[33:63].decode('latin-1', errors='ignore').strip('\x00 ')
            if not meta.album:
                meta.album = data[63:93].decode('latin-1', errors='ignore').strip('\x00 ')
            if not meta.year:
                meta.year = data[93:97].decode('latin-1', errors='ignore').strip('\x00 ')

        except:
            pass

        return meta

    def _parse_mp3_frames(self, data: bytes, meta: AudioMetadata) -> AudioMetadata:
        """Parse MP3 frame headers para bitrate e duracao"""
        # Tabela de bitrates MPEG1 Layer III
        bitrate_table = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]

        # Tabela de sample rates
        samplerate_table = [44100, 48000, 32000, 0]

        # Procura primeiro frame sync
        pos = 0
        frame_count = 0
        total_bitrate = 0

        # Pula ID3v2 se presente
        if data[:3] == b'ID3':
            size = (data[6] & 0x7f) << 21 | (data[7] & 0x7f) << 14 | \
                   (data[8] & 0x7f) << 7 | (data[9] & 0x7f)
            pos = size + 10

        while pos < len(data) - 4:
            # Procura sync word (0xFF followed by 0xE or 0xF in high nibble)
            if data[pos] == 0xFF and (data[pos+1] & 0xE0) == 0xE0:
                header = struct.unpack('>I', data[pos:pos+4])[0]

                # Parse header
                version = (header >> 19) & 0x3
                layer = (header >> 17) & 0x3
                bitrate_idx = (header >> 12) & 0xF
                samplerate_idx = (header >> 10) & 0x3
                padding = (header >> 9) & 0x1
                channels = (header >> 6) & 0x3

                if version == 3 and layer == 1:  # MPEG1 Layer 3
                    if bitrate_idx > 0 and bitrate_idx < 15 and samplerate_idx < 3:
                        bitrate = bitrate_table[bitrate_idx]
                        samplerate = samplerate_table[samplerate_idx]

                        if frame_count == 0:
                            meta.sample_rate = samplerate
                            meta.channels = 1 if channels == 3 else 2

                        total_bitrate += bitrate
                        frame_count += 1

                        # Calcula tamanho do frame
                        frame_size = int(144 * bitrate * 1000 / samplerate) + padding
                        pos += frame_size
                        continue

            pos += 1

        if frame_count > 0:
            meta.bitrate_kbps = total_bitrate // frame_count
            # Duracao estimada
            file_size = len(data)
            if meta.bitrate_kbps > 0:
                meta.duration_seconds = file_size * 8 / (meta.bitrate_kbps * 1000)

        return meta

    def _analyze_flac(self, path: Path) -> AudioMetadata:
        """Analisa arquivo FLAC"""
        meta = AudioMetadata(format="FLAC", codec="Free Lossless Audio Codec")

        with open(path, 'rb') as f:
            # Verifica magic number
            if f.read(4) != b'fLaC':
                return meta

            # Le blocos de metadados
            while True:
                header = f.read(4)
                if len(header) < 4:
                    break

                is_last = (header[0] & 0x80) != 0
                block_type = header[0] & 0x7F
                block_size = (header[1] << 16) | (header[2] << 8) | header[3]

                if block_type == 0:  # STREAMINFO
                    info = f.read(34)
                    if len(info) >= 18:
                        min_block = (info[0] << 8) | info[1]
                        max_block = (info[2] << 8) | info[3]
                        min_frame = (info[4] << 16) | (info[5] << 8) | info[6]
                        max_frame = (info[7] << 16) | (info[8] << 8) | info[9]

                        # Sample rate (20 bits)
                        meta.sample_rate = (info[10] << 12) | (info[11] << 4) | (info[12] >> 4)

                        # Channels (3 bits) + 1
                        meta.channels = ((info[12] >> 1) & 0x7) + 1

                        # Bits per sample (5 bits) + 1
                        meta.bit_depth = ((info[12] & 0x1) << 4 | (info[13] >> 4)) + 1

                        # Total samples (36 bits)
                        total_samples = ((info[13] & 0xF) << 32) | (info[14] << 24) | \
                                       (info[15] << 16) | (info[16] << 8) | info[17]

                        if meta.sample_rate > 0:
                            meta.duration_seconds = total_samples / meta.sample_rate

                elif block_type == 4:  # VORBIS_COMMENT
                    comment_data = f.read(block_size)
                    meta = self._parse_vorbis_comment(comment_data, meta)

                else:
                    f.seek(block_size, 1)

                if is_last:
                    break

        # Calcula bitrate
        if meta.duration_seconds > 0:
            file_size = path.stat().st_size
            meta.bitrate_kbps = int(file_size * 8 / meta.duration_seconds / 1000)

        return meta

    def _analyze_ogg(self, path: Path) -> AudioMetadata:
        """Analisa arquivo OGG Vorbis"""
        meta = AudioMetadata(format="OGG", codec="Vorbis")

        with open(path, 'rb') as f:
            # Verifica magic number
            if f.read(4) != b'OggS':
                return meta

            # Volta ao inicio
            f.seek(0)

            page_count = 0
            total_granule = 0

            while True:
                page_header = f.read(27)
                if len(page_header) < 27 or page_header[:4] != b'OggS':
                    break

                # Granule position (8 bytes)
                granule = struct.unpack('<Q', page_header[6:14])[0]
                if granule != 0xFFFFFFFFFFFFFFFF:
                    total_granule = granule

                # Numero de segmentos
                num_segments = page_header[26]
                segment_table = f.read(num_segments)

                page_size = sum(segment_table)

                # Primeira pagina contem header de identificacao
                if page_count == 0:
                    page_data = f.read(page_size)
                    if len(page_data) > 16 and page_data[:7] == b'\x01vorbis':
                        meta.channels = page_data[11]
                        meta.sample_rate = struct.unpack('<I', page_data[12:16])[0]
                        meta.bitrate_kbps = struct.unpack('<i', page_data[20:24])[0] // 1000

                # Segunda pagina pode conter comentarios
                elif page_count == 1:
                    page_data = f.read(page_size)
                    if len(page_data) > 7 and page_data[:7] == b'\x03vorbis':
                        meta = self._parse_vorbis_comment(page_data[7:], meta)

                else:
                    f.seek(page_size, 1)

                page_count += 1

                if page_count > 10:  # Limita para nao ler arquivo inteiro
                    break

            # Duracao
            if meta.sample_rate > 0 and total_granule > 0:
                meta.duration_seconds = total_granule / meta.sample_rate

        return meta

    def _analyze_m4a(self, path: Path) -> AudioMetadata:
        """Analisa arquivo M4A/AAC"""
        meta = AudioMetadata(format="M4A", codec="AAC")

        with open(path, 'rb') as f:
            # M4A usa formato de atoms (boxes)
            while True:
                header = f.read(8)
                if len(header) < 8:
                    break

                size = struct.unpack('>I', header[:4])[0]
                atom_type = header[4:8].decode('latin-1', errors='ignore')

                if size == 0:
                    break
                if size == 1:
                    # Extended size
                    ext_size = struct.unpack('>Q', f.read(8))[0]
                    size = ext_size - 8

                content_size = size - 8

                if atom_type == 'moov':
                    # Container, le recursivamente
                    moov_data = f.read(content_size)
                    meta = self._parse_moov_atom(moov_data, meta)
                    break
                else:
                    f.seek(content_size, 1)

        return meta

    def _parse_moov_atom(self, data: bytes, meta: AudioMetadata) -> AudioMetadata:
        """Parse moov atom para metadados de audio"""
        pos = 0

        while pos < len(data) - 8:
            size = struct.unpack('>I', data[pos:pos+4])[0]
            atom_type = data[pos+4:pos+8].decode('latin-1', errors='ignore')

            if size < 8 or pos + size > len(data):
                break

            content = data[pos+8:pos+size]

            if atom_type == 'trak':
                meta = self._parse_moov_atom(content, meta)
            elif atom_type == 'mdia':
                meta = self._parse_moov_atom(content, meta)
            elif atom_type == 'minf':
                meta = self._parse_moov_atom(content, meta)
            elif atom_type == 'stbl':
                meta = self._parse_moov_atom(content, meta)
            elif atom_type == 'stsd':
                # Sample description
                if len(content) > 16:
                    # Pula para mp4a atom
                    entry_count = struct.unpack('>I', content[4:8])[0]
                    if entry_count > 0 and len(content) > 28:
                        sample_type = content[12:16].decode('latin-1', errors='ignore')
                        if sample_type == 'mp4a':
                            meta.channels = struct.unpack('>H', content[24:26])[0]
                            meta.sample_rate = struct.unpack('>I', content[28:32])[0] >> 16

            elif atom_type == 'mdhd':
                # Media header
                version = content[0]
                if version == 0 and len(content) >= 20:
                    timescale = struct.unpack('>I', content[12:16])[0]
                    duration = struct.unpack('>I', content[16:20])[0]
                    if timescale > 0:
                        meta.duration_seconds = duration / timescale

            elif atom_type == 'udta':
                meta = self._parse_moov_atom(content, meta)
            elif atom_type == 'meta':
                if len(content) > 4:
                    meta = self._parse_moov_atom(content[4:], meta)
            elif atom_type == 'ilst':
                meta = self._parse_ilst(content, meta)

            pos += size

        return meta

    def _parse_ilst(self, data: bytes, meta: AudioMetadata) -> AudioMetadata:
        """Parse ilst atom para tags de metadados"""
        tag_map = {
            '\xa9nam': 'title',
            '\xa9ART': 'artist',
            '\xa9alb': 'album',
            '\xa9day': 'year',
            '\xa9gen': 'genre',
            'trkn': 'track_number',
            '\xa9cmt': 'comment'
        }

        pos = 0
        while pos < len(data) - 8:
            size = struct.unpack('>I', data[pos:pos+4])[0]
            tag_type = data[pos+4:pos+8].decode('latin-1', errors='ignore')

            if size < 8 or pos + size > len(data):
                break

            if tag_type in tag_map:
                # Busca data atom dentro
                content = data[pos+8:pos+size]
                data_pos = 0
                while data_pos < len(content) - 8:
                    data_size = struct.unpack('>I', content[data_pos:data_pos+4])[0]
                    data_type = content[data_pos+4:data_pos+8]

                    if data_type == b'data' and data_size > 16:
                        text = content[data_pos+16:data_pos+data_size].decode('utf-8', errors='ignore')
                        setattr(meta, tag_map[tag_type], text)
                        break

                    data_pos += data_size

            pos += size

        return meta

    def _parse_vorbis_comment(self, data: bytes, meta: AudioMetadata) -> AudioMetadata:
        """Parse Vorbis comment block"""
        try:
            pos = 0

            # Vendor string length
            vendor_len = struct.unpack('<I', data[pos:pos+4])[0]
            pos += 4 + vendor_len

            # Number of comments
            if pos + 4 > len(data):
                return meta

            comment_count = struct.unpack('<I', data[pos:pos+4])[0]
            pos += 4

            for _ in range(min(comment_count, 20)):
                if pos + 4 > len(data):
                    break

                comment_len = struct.unpack('<I', data[pos:pos+4])[0]
                pos += 4

                if pos + comment_len > len(data):
                    break

                comment = data[pos:pos+comment_len].decode('utf-8', errors='ignore')
                pos += comment_len

                if '=' in comment:
                    key, value = comment.split('=', 1)
                    key = key.upper()

                    if key == 'TITLE':
                        meta.title = value
                    elif key == 'ARTIST':
                        meta.artist = value
                    elif key == 'ALBUM':
                        meta.album = value
                    elif key == 'DATE':
                        meta.year = value[:4]
                    elif key == 'GENRE':
                        meta.genre = value
                    elif key == 'TRACKNUMBER':
                        meta.track_number = value
                    elif key == 'COMMENT':
                        meta.comment = value

        except:
            pass

        return meta

    def _analyze_generic(self, path: Path) -> AudioMetadata:
        """Analise generica para formatos nao suportados especificamente"""
        meta = AudioMetadata()
        meta.format = path.suffix.upper().lstrip('.')

        # Tenta estimar duracao pelo tamanho do arquivo
        file_size = path.stat().st_size

        # Assume bitrate medio de 128kbps se nao conseguir determinar
        meta.bitrate_kbps = 128
        meta.duration_seconds = file_size * 8 / (meta.bitrate_kbps * 1000)

        return meta

    def _format_duration(self, seconds: float) -> str:
        """Formata duracao em HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _estimate_quality(self, meta: AudioMetadata) -> str:
        """Estima qualidade do audio"""
        if meta.format == "FLAC":
            return "lossless"

        if meta.bitrate_kbps >= 320:
            return "high"
        elif meta.bitrate_kbps >= 192:
            return "good"
        elif meta.bitrate_kbps >= 128:
            return "standard"
        else:
            return "low"

    def _generate_audio_summary(self, meta: AudioMetadata, tags: Dict) -> str:
        """Gera resumo do audio"""
        parts = []

        if tags.get('title'):
            if tags.get('artist'):
                parts.append(f"{tags['artist']} - {tags['title']}")
            else:
                parts.append(tags['title'])

        if tags.get('album'):
            parts.append(f"Album: {tags['album']}")

        parts.append(f"{meta.format} {meta.bitrate_kbps}kbps")
        parts.append(f"Duracao: {self._format_duration(meta.duration_seconds)}")

        if meta.sample_rate:
            parts.append(f"{meta.sample_rate}Hz {'Stereo' if meta.channels == 2 else 'Mono'}")

        return " | ".join(parts)


class SpeechAnalyzer(MediaAnalyzer):
    """
    Analisador de Fala

    Analisa audio de voz e prepara para transcricao.
    Nota: Transcricao real requer API externa (Whisper, Google Speech, etc.)
    """

    supported_formats = [
        MediaFormat.MP3,
        MediaFormat.WAV,
        MediaFormat.M4A
    ]
    skill_name = "speech_analysis"
    skill_description = "Analise de audio de fala (preparacao para transcricao)"
    skill_category = "audio"

    def __init__(self, agent_id: Optional[str] = None, transcription_api: Optional[str] = None):
        super().__init__(agent_id)
        self.transcription_api = transcription_api

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa audio de fala"""
        # Usa AudioAnalyzer como base
        base_analyzer = AudioAnalyzer(self.agent_id)
        result = base_analyzer.analyze(path, **options)

        if not result.success:
            return result

        # Adiciona analise especifica de fala
        try:
            speech_analysis = {
                "suitable_for_transcription": self._check_transcription_suitability(result),
                "estimated_word_count": self._estimate_word_count(result),
                "transcription_api_configured": self.transcription_api is not None
            }

            result.metadata['speech_analysis'] = speech_analysis

            if options.get('transcribe') and self.transcription_api:
                # Aqui entraria a integracao com API de transcricao
                result.metadata['transcription'] = {
                    "status": "not_implemented",
                    "message": "Integracao com API de transcricao pendente"
                }

        except Exception as e:
            result.warnings.append(f"Analise de fala parcial: {str(e)}")

        return result

    def _check_transcription_suitability(self, result: AnalysisResult) -> bool:
        """Verifica se audio e adequado para transcricao"""
        audio_meta = result.metadata.get('audio', {})

        # Verifica duracao (max 30 min para maioria das APIs)
        duration = audio_meta.get('duration_seconds', 0)
        if duration > 1800:
            result.warnings.append("Audio muito longo (>30min). Considere dividir.")
            return False

        # Verifica qualidade minima
        sample_rate = audio_meta.get('sample_rate', 0)
        if sample_rate < 8000:
            result.warnings.append("Sample rate baixo. Transcricao pode ter baixa qualidade.")

        return True

    def _estimate_word_count(self, result: AnalysisResult) -> int:
        """Estima numero de palavras baseado na duracao"""
        # Media de fala: 150 palavras por minuto
        duration = result.metadata.get('audio', {}).get('duration_seconds', 0)
        return int(duration / 60 * 150)


class MusicAnalyzer(MediaAnalyzer):
    """
    Analisador de Musica

    Analise especializada em conteudo musical.
    """

    supported_formats = [
        MediaFormat.MP3,
        MediaFormat.WAV,
        MediaFormat.FLAC,
        MediaFormat.OGG,
        MediaFormat.M4A
    ]
    skill_name = "music_analysis"
    skill_description = "Analise de arquivos de musica (BPM, tom, etc.)"
    skill_category = "audio"

    def analyze(self, path: Path, **options) -> AnalysisResult:
        """Analisa arquivo de musica"""
        # Usa AudioAnalyzer como base
        base_analyzer = AudioAnalyzer(self.agent_id)
        result = base_analyzer.analyze(path, **options)

        if not result.success:
            return result

        try:
            # Adiciona analise musical
            music_analysis = {
                "has_tags": bool(result.metadata.get('tags')),
                "is_likely_music": self._detect_music(result),
                "duration_category": self._categorize_duration(result)
            }

            # Se for WAV, tenta analise de waveform
            if result.media_format == MediaFormat.WAV:
                waveform_stats = self._analyze_waveform_basic(path)
                if waveform_stats:
                    music_analysis['waveform'] = waveform_stats

            result.metadata['music_analysis'] = music_analysis

        except Exception as e:
            result.warnings.append(f"Analise musical parcial: {str(e)}")

        return result

    def _detect_music(self, result: AnalysisResult) -> bool:
        """Detecta se e provavelmente musica"""
        tags = result.metadata.get('tags', {})
        duration = result.metadata.get('audio', {}).get('duration_seconds', 0)

        # Musica tipicamente tem tags e duracao entre 30s e 10min
        has_music_tags = any(tags.get(t) for t in ['title', 'artist', 'album'])
        reasonable_duration = 30 < duration < 600

        return has_music_tags or reasonable_duration

    def _categorize_duration(self, result: AnalysisResult) -> str:
        """Categoriza duracao"""
        duration = result.metadata.get('audio', {}).get('duration_seconds', 0)

        if duration < 30:
            return "very_short"
        elif duration < 180:
            return "short"
        elif duration < 360:
            return "standard"
        elif duration < 600:
            return "extended"
        else:
            return "very_long"

    def _analyze_waveform_basic(self, path: Path) -> Optional[Dict]:
        """Analise basica de waveform para WAV"""
        try:
            with wave.open(str(path), 'rb') as wav:
                frames = wav.readframes(wav.getnframes())
                sample_width = wav.getsampwidth()

                # Converte para valores
                if sample_width == 1:
                    samples = list(struct.unpack(f'{len(frames)}B', frames))
                    samples = [s - 128 for s in samples]  # Centraliza
                elif sample_width == 2:
                    samples = list(struct.unpack(f'{len(frames)//2}h', frames))
                else:
                    return None

                # Calcula estatisticas basicas
                if not samples:
                    return None

                abs_samples = [abs(s) for s in samples]
                max_amplitude = max(abs_samples)
                avg_amplitude = sum(abs_samples) / len(abs_samples)

                # Peak to average ratio (indica compressao dinamica)
                par = max_amplitude / avg_amplitude if avg_amplitude > 0 else 0

                return {
                    "max_amplitude": max_amplitude,
                    "avg_amplitude": round(avg_amplitude, 2),
                    "peak_to_avg_ratio": round(par, 2),
                    "dynamic_range": "high" if par > 5 else "medium" if par > 2 else "low"
                }

        except Exception:
            return None
