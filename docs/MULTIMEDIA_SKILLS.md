# Skills de Analise Multimidia

Sistema completo de analise de conteudo multimidia para os Agentes Autonomos.

---

## Visao Geral

O sistema de skills multimidia permite que os agentes analisem diferentes tipos de arquivos:

| Tipo | Formatos Suportados | Skills |
|------|---------------------|--------|
| **Texto** | TXT, MD, PDF, DOCX, HTML, XML | text_analysis, pdf_analysis, document_analysis |
| **Codigo** | Python, JavaScript, TypeScript, Java, C++, SQL | code_analysis |
| **Dados** | JSON, CSV, XLSX | data_analysis |
| **Audio** | MP3, WAV, FLAC, OGG, M4A, AAC, WMA | audio_analysis, speech_analysis, music_analysis |
| **Video** | MP4, AVI, MKV, MOV, WEBM, WMV, FLV | video_analysis, frame_analysis, scene_analysis |

**Total: 11 skills cobrindo 35+ formatos**

---

## Instalacao

As skills de midia fazem parte do sistema de agentes. Nenhuma dependencia externa e necessaria - todo o processamento e feito em Python puro.

```python
# Importacao
from factory.agents.skills import (
    analyze_file,
    get_supported_formats,
    list_skills,
    can_analyze
)
```

---

## Uso Rapido

### Analisar Qualquer Arquivo

```python
from factory.agents.skills.registry import analyze_file

# Analise automatica - detecta o tipo
result = analyze_file("documento.pdf")

if result.success:
    print(f"Tipo: {result.media_type.value}")
    print(f"Resumo: {result.content_summary}")
    print(f"Metadados: {result.metadata}")
```

### Verificar Suporte

```python
from factory.agents.skills.registry import can_analyze, get_media_type

# Verifica se formato e suportado
if can_analyze("video.mp4"):
    print("Formato suportado!")

# Obtem tipo de midia
tipo = get_media_type("audio.mp3")  # Retorna "audio"
```

### Listar Skills Disponiveis

```python
from factory.agents.skills.registry import list_skills, get_supported_formats

# Lista todas as skills
for skill in list_skills():
    print(f"{skill['name']}: {skill['description']}")

# Lista formatos por tipo
formatos = get_supported_formats()
print(f"Video: {formatos['video']}")
print(f"Audio: {formatos['audio']}")
```

---

## Skills de Texto

### TextAnalyzer

Analisa arquivos de texto puro (TXT) e Markdown (MD).

```python
from factory.agents.skills import TextAnalyzer

analyzer = TextAnalyzer()
result = analyzer.analyze(Path("documento.txt"))

# Estatisticas
print(f"Palavras: {result.stats['word_count']}")
print(f"Linhas: {result.stats['line_count']}")
print(f"Paragrafos: {result.stats['paragraph_count']}")

# Analise semantica
print(f"Keywords: {result.keywords}")
print(f"Idioma: {result.language}")  # pt, en, es
print(f"Sentimento: {result.sentiment}")  # positive, negative, neutral
```

**Para Markdown:**

```python
result = analyzer.analyze(Path("README.md"))

# Estrutura do Markdown
md_struct = result.metadata['markdown_structure']
print(f"Headers: {md_struct['headers']}")
print(f"Links: {md_struct['links']}")
print(f"Code blocks: {md_struct['code_blocks']}")
```

### PDFAnalyzer

Extrai texto e metadados de PDFs.

```python
from factory.agents.skills import PDFAnalyzer

analyzer = PDFAnalyzer()
result = analyzer.analyze(Path("documento.pdf"))

# Metadados do PDF
print(f"Titulo: {result.metadata.get('title')}")
print(f"Autor: {result.metadata.get('author')}")
print(f"Paginas: {result.metadata.get('page_count')}")
print(f"Versao: {result.metadata.get('pdf_version')}")

# Texto extraido
print(f"Conteudo: {result.content[:500]}...")
```

### DocumentAnalyzer

Analisa DOCX, HTML e XML.

```python
from factory.agents.skills import DocumentAnalyzer

analyzer = DocumentAnalyzer()

# DOCX
result = analyzer.analyze(Path("documento.docx"))
print(f"Titulo: {result.metadata.get('title')}")
print(f"Criador: {result.metadata.get('creator')}")

# HTML
result = analyzer.analyze(Path("pagina.html"))
estrutura = result.metadata.get('structure', {})
print(f"Headings: {estrutura.get('headings')}")
print(f"Links: {estrutura.get('links')}")
print(f"Imagens: {estrutura.get('images')}")
```

### CodeAnalyzer

Analisa codigo fonte em varias linguagens.

```python
from factory.agents.skills import CodeAnalyzer

analyzer = CodeAnalyzer()
result = analyzer.analyze(Path("app.py"))

# Estrutura do codigo
code_info = result.metadata['code_analysis']
print(f"Classes: {code_info['classes']}")
print(f"Funcoes: {code_info['functions']}")
print(f"Imports: {code_info['imports']}")

# Estatisticas
print(f"Linhas de codigo: {result.stats['code_lines']}")
print(f"Linhas de comentario: {result.stats['comment_lines']}")
print(f"Complexidade estimada: {result.stats['estimated_complexity']}")
```

**Linguagens suportadas:**
- Python (.py)
- JavaScript (.js)
- TypeScript (.ts)
- Java (.java)
- C++ (.cpp)
- SQL (.sql)

### DataFileAnalyzer

Analisa arquivos de dados estruturados.

```python
from factory.agents.skills import DataFileAnalyzer

analyzer = DataFileAnalyzer()

# JSON
result = analyzer.analyze(Path("dados.json"))
print(f"Tipo: {result.metadata.get('type')}")  # dict ou list
print(f"Schema: {result.metadata.get('schema')}")

# CSV
result = analyzer.analyze(Path("planilha.csv"))
print(f"Colunas: {result.metadata.get('columns')}")
print(f"Linhas: {result.metadata['stats'].get('row_count')}")
print(f"Tipos: {result.metadata.get('column_types')}")

# Excel
result = analyzer.analyze(Path("dados.xlsx"))
print(f"Planilhas: {result.metadata.get('sheets')}")
```

---

## Skills de Audio

### AudioAnalyzer

Analisa metadados e caracteristicas de arquivos de audio.

```python
from factory.agents.skills import AudioAnalyzer

analyzer = AudioAnalyzer()
result = analyzer.analyze(Path("musica.mp3"))

# Metadados tecnicos
audio = result.metadata['audio']
print(f"Duracao: {audio['duration_formatted']}")  # 03:45
print(f"Sample rate: {audio['sample_rate']} Hz")
print(f"Canais: {audio['channel_layout']}")  # stereo, mono
print(f"Bitrate: {audio['bitrate_kbps']} kbps")
print(f"Codec: {audio['codec']}")

# Tags (ID3, Vorbis)
tags = result.metadata.get('tags', {})
print(f"Titulo: {tags.get('title')}")
print(f"Artista: {tags.get('artist')}")
print(f"Album: {tags.get('album')}")
print(f"Ano: {tags.get('year')}")
print(f"Genero: {tags.get('genre')}")

# Qualidade estimada
print(f"Qualidade: {result.stats['estimated_quality']}")
# lossless, high, good, standard, low
```

**Formatos suportados:**
- MP3 (ID3v1, ID3v2)
- WAV (PCM)
- FLAC (Vorbis Comments)
- OGG (Vorbis)
- M4A/AAC (iTunes tags)
- WMA

### SpeechAnalyzer

Prepara audio de fala para transcricao.

```python
from factory.agents.skills import SpeechAnalyzer

analyzer = SpeechAnalyzer()
result = analyzer.analyze(Path("gravacao.wav"))

speech = result.metadata.get('speech_analysis', {})
print(f"Adequado para transcricao: {speech['suitable_for_transcription']}")
print(f"Palavras estimadas: {speech['estimated_word_count']}")
```

### MusicAnalyzer

Analise especializada em musica.

```python
from factory.agents.skills import MusicAnalyzer

analyzer = MusicAnalyzer()
result = analyzer.analyze(Path("musica.flac"))

music = result.metadata.get('music_analysis', {})
print(f"E musica: {music['is_likely_music']}")
print(f"Categoria de duracao: {music['duration_category']}")
# very_short, short, standard, extended, very_long
```

---

## Skills de Video

### VideoAnalyzer

Analisa metadados e streams de arquivos de video.

```python
from factory.agents.skills import VideoAnalyzer

analyzer = VideoAnalyzer()
result = analyzer.analyze(Path("video.mp4"))

# Informacoes gerais
video_meta = result.metadata['video']
print(f"Container: {video_meta['container']}")
print(f"Duracao: {video_meta['duration_formatted']}")

# Stream de video
video_stream = video_meta.get('video', {})
print(f"Resolucao: {video_stream['resolution']}")  # 1920x1080
print(f"Nome: {video_stream['resolution_name']}")  # Full HD
print(f"Codec: {video_stream['codec']}")  # H.264/AVC
print(f"FPS: {video_stream['fps']}")

# Streams de audio
for i, audio in enumerate(video_meta.get('audio_tracks', [])):
    print(f"Audio {i+1}: {audio['codec']} {audio['channels']}ch")

# Legendas
for sub in video_meta.get('subtitle_tracks', []):
    print(f"Legenda: {sub['language']}")

# Estatisticas
print(f"Aspect ratio: {result.stats['aspect_ratio']}")
print(f"Qualidade: {result.stats['quality_estimate']}")
```

**Formatos suportados:**
- MP4/MOV (H.264, H.265, AAC)
- AVI (diversos codecs)
- MKV/WebM (VP8, VP9, Opus)
- FLV (Flash)
- WMV

### FrameAnalyzer

Informacoes sobre frames do video.

```python
from factory.agents.skills import FrameAnalyzer

analyzer = FrameAnalyzer()
result = analyzer.analyze(Path("video.mp4"))

frames = result.metadata.get('frame_analysis', {})
print(f"Total de frames: {frames['frame_count']}")
print(f"FPS: {frames['fps']}")
print(f"Keyframes estimados: {frames['estimated_keyframes']}")
```

### SceneAnalyzer

Analise de cenas e cortes.

```python
from factory.agents.skills import SceneAnalyzer

analyzer = SceneAnalyzer()
result = analyzer.analyze(Path("video.mp4"))

scenes = result.metadata.get('scene_analysis', {})
print(f"Cenas estimadas: {scenes['estimated_scenes']}")
```

---

## Integracao com Agentes

### Registrar Skills para um Agente

```python
from factory.agents.learning import SkillAcquisition
from factory.agents.skills.registry import register_skills_for_agent

# Cria sistema de skills do agente
skills = SkillAcquisition(agent_id="08")

# Registra todas as skills de midia
register_skills_for_agent("08", skills)

# Agora o agente tem todas as 11 skills de midia
```

### Praticar Skills

```python
from factory.agents.skills.registry import practice_media_skill

# Apos analisar um video com sucesso
practice_media_skill("08", "video_analysis", success=True, skill_acquisition=skills)

# XP ganho varia por skill:
# - text_analysis: 5 XP
# - pdf_analysis: 10 XP
# - video_analysis: 20 XP
# - scene_analysis: 25 XP
```

### Fluxo Completo

```python
from factory.agents.core import AutonomousAgent, TaskContext
from factory.agents.skills.registry import analyze_file, practice_media_skill

# Agente analisa arquivo
agent = AutonomousAgent(agent_id="08", name="Analista", domain="analysis")

def analyze_media_task(file_path: str):
    """Tarefa de analise de midia"""
    result = analyze_file(file_path, agent_id="08")

    if result.success:
        # Registra pratica
        practice_media_skill("08", result.analyzer_name, True, agent.skills)

        # Armazena conhecimento
        agent.knowledge_base.add(
            content=result.content_summary,
            knowledge_type="analysis",
            source=file_path,
            tags=result.keywords
        )

    return result
```

---

## Arquitetura

### Estrutura de Arquivos

```
factory/agents/skills/
├── __init__.py              # Exports principais
├── multimedia_base.py       # Classes base (MediaAnalyzer, MediaFormat)
├── text_analysis.py         # Analisadores de texto
├── audio_analysis.py        # Analisadores de audio
├── video_analysis.py        # Analisadores de video
├── registry.py              # Registro central e funcoes utilitarias
└── test_multimedia_skills.py # Testes
```

### Diagrama de Classes

```
MediaAnalyzer (ABC)
    |
    +-- TextAnalyzer
    +-- PDFAnalyzer
    +-- DocumentAnalyzer
    +-- CodeAnalyzer
    +-- DataFileAnalyzer
    +-- AudioAnalyzer
    |       +-- SpeechAnalyzer
    |       +-- MusicAnalyzer
    +-- VideoAnalyzer
            +-- FrameAnalyzer
            +-- SceneAnalyzer
```

### Fluxo de Analise

```
Arquivo
    |
    v
[MediaFormat.from_path()]
    |
    v
[Registry.get_analyzer_for_file()]
    |
    v
[Analyzer.analyze()]
    |
    +-- extract_metadata()
    +-- parse_content()
    +-- analyze_semantics()
    |
    v
[AnalysisResult]
    |
    +-- metadata (Dict)
    +-- content (str)
    +-- stats (Dict)
    +-- keywords (List)
    |
    v
[Registry.save_analysis()]
    |
    v
SQLite (historico)
```

---

## API Reference

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    file_path: str           # Caminho do arquivo
    media_type: MediaType    # Tipo de midia
    media_format: MediaFormat # Formato especifico
    success: bool            # Se analise teve sucesso

    metadata: Dict           # Metadados extraidos
    content: str             # Conteudo (truncado se muito grande)
    content_summary: str     # Resumo do conteudo

    entities: List[str]      # Entidades detectadas
    keywords: List[str]      # Palavras-chave
    topics: List[str]        # Topicos
    sentiment: str           # Sentimento
    language: str            # Idioma detectado

    stats: Dict              # Estatisticas
    errors: List[str]        # Erros
    warnings: List[str]      # Avisos

    analyzed_at: str         # Timestamp
    analysis_duration_ms: int # Duracao
```

### MediaFormat

```python
class MediaFormat(Enum):
    # Texto
    TXT, PDF, DOCX, DOC, MD, HTML, XML

    # Codigo
    PY, JS, TS, JAVA, CPP, SQL

    # Dados
    JSON, CSV, XLSX

    # Audio
    MP3, WAV, FLAC, OGG, M4A, AAC, WMA

    # Video
    MP4, AVI, MKV, MOV, WEBM, WMV, FLV

    # Imagem
    PNG, JPG, JPEG, GIF, BMP, WEBP, SVG
```

### MediaType

```python
class MediaType(Enum):
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    DATA = "data"
```

---

## Execucao de Testes

```bash
# Executa todos os testes
python -m factory.agents.skills.test_multimedia_skills
```

**Saida esperada:**
```
============================================================
TESTES DE SKILLS DE ANALISE MULTIMIDIA
============================================================

Teste: Deteccao de Formato de Midia
  PASSOU!

Teste: Analisador de Texto
  PASSOU!

... (mais testes)

============================================================
RESULTADO: 9 passou, 0 falhou
============================================================
```

---

## Limitacoes

1. **PDF**: Extracao de texto pode ser incompleta para PDFs com layout complexo
2. **Audio**: Transcricao real requer API externa (Whisper, Google Speech)
3. **Video**: Extracao de frames requer ffmpeg ou opencv
4. **Imagem**: Analise de conteudo visual nao implementada

---

## Proximos Passos

- [ ] Integracao com API de transcricao (Whisper)
- [ ] Suporte a OCR para PDFs escaneados
- [ ] Extracao de frames via ffmpeg
- [ ] Analise de imagens com visao computacional
- [ ] Deteccao de cenas por diferenca de histograma
