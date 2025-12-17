"""
Testes para Skills de Analise Multimidia
========================================

Testes unitarios para validar funcionamento dos analisadores.
"""

import json
import tempfile
import wave
import struct
from pathlib import Path
from datetime import datetime

# Importacoes dos modulos
from .multimedia_base import MediaFormat, MediaType, MediaSkillRegistry, AnalysisResult
from .text_analysis import TextAnalyzer, CodeAnalyzer, DataFileAnalyzer
from .audio_analysis import AudioAnalyzer
from .video_analysis import VideoAnalyzer
from .registry import (
    get_registry,
    analyze_file,
    get_supported_formats,
    list_skills,
    can_analyze,
    get_media_type
)


def test_media_format_detection():
    """Testa deteccao de formato de midia"""
    print("Teste: Deteccao de Formato de Midia")

    # Testa varios formatos
    test_cases = [
        ("arquivo.txt", MediaFormat.TXT, MediaType.TEXT),
        ("video.mp4", MediaFormat.MP4, MediaType.VIDEO),
        ("audio.mp3", MediaFormat.MP3, MediaType.AUDIO),
        ("dados.json", MediaFormat.JSON, MediaType.DATA),
        ("codigo.py", MediaFormat.PY, MediaType.TEXT),
        ("planilha.xlsx", MediaFormat.XLSX, MediaType.DATA),
    ]

    for filename, expected_format, expected_type in test_cases:
        fmt = MediaFormat.from_extension(filename.split('.')[-1])
        assert fmt == expected_format, f"Formato incorreto para {filename}"
        assert fmt.media_type == expected_type, f"Tipo incorreto para {filename}"
        print(f"  OK {filename}: {fmt.extension} ({fmt.media_type.value})")

    print("  PASSOU!\n")


def test_text_analyzer():
    """Testa analisador de texto"""
    print("Teste: Analisador de Texto")

    analyzer = TextAnalyzer()

    # Cria arquivo de teste
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("""Este e um arquivo de teste.

Ele contem multiplos paragrafos e sentencas.
O objetivo e testar o analisador de texto.

Python e uma linguagem de programacao muito popular.
Ela e usada para desenvolvimento web, ciencia de dados e automacao.
""")
        temp_path = Path(f.name)

    try:
        result = analyzer.analyze(temp_path)

        assert result.success, "Analise deveria ter sucesso"
        assert result.content is not None, "Conteudo deveria estar presente"
        assert result.stats['word_count'] > 0, "Deveria ter contagem de palavras"
        assert len(result.keywords) > 0, "Deveria ter keywords"
        assert result.language in ['pt', 'en', 'es'], "Deveria detectar idioma"

        print(f"  OK Palavras: {result.stats['word_count']}")
        print(f"  OK Linhas: {result.stats['line_count']}")
        print(f"  OK Keywords: {result.keywords[:5]}")
        print(f"  OK Idioma: {result.language}")
        print(f"  OK Sentimento: {result.sentiment}")

    finally:
        temp_path.unlink()

    print("  PASSOU!\n")


def test_code_analyzer():
    """Testa analisador de codigo"""
    print("Teste: Analisador de Codigo")

    analyzer = CodeAnalyzer()

    # Cria arquivo Python de teste
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write('''"""Modulo de exemplo"""

import os
from typing import List, Optional

class Usuario:
    """Classe de usuario"""

    def __init__(self, nome: str, idade: int):
        self.nome = nome
        self.idade = idade

    def saudacao(self) -> str:
        """Retorna saudacao"""
        return f"Ola, {self.nome}!"


def processar_usuarios(usuarios: List[Usuario]) -> int:
    """Processa lista de usuarios"""
    count = 0
    for usuario in usuarios:
        if usuario.idade >= 18:
            print(usuario.saudacao())
            count += 1
    return count


if __name__ == "__main__":
    u = Usuario("Maria", 25)
    print(u.saudacao())
''')
        temp_path = Path(f.name)

    try:
        result = analyzer.analyze(temp_path)

        assert result.success, "Analise deveria ter sucesso"
        assert 'code_analysis' in result.metadata, "Deveria ter analise de codigo"

        code_info = result.metadata['code_analysis']
        assert len(code_info['classes']) > 0, "Deveria detectar classes"
        assert len(code_info['functions']) > 0, "Deveria detectar funcoes"
        assert len(code_info['imports']) > 0, "Deveria detectar imports"

        print(f"  OK Classes: {code_info['classes']}")
        print(f"  OK Funcoes: {code_info['functions']}")
        print(f"  OK Imports: {code_info['imports']}")
        print(f"  OK Linhas de codigo: {result.stats['code_lines']}")
        print(f"  OK Complexidade: {result.stats['estimated_complexity']}")

    finally:
        temp_path.unlink()

    print("  PASSOU!\n")


def test_json_analyzer():
    """Testa analisador de JSON"""
    print("Teste: Analisador de JSON")

    analyzer = DataFileAnalyzer()

    # Cria arquivo JSON de teste
    test_data = {
        "usuarios": [
            {"id": 1, "nome": "Maria", "email": "maria@email.com"},
            {"id": 2, "nome": "Joao", "email": "joao@email.com"},
            {"id": 3, "nome": "Ana", "email": "ana@email.com"}
        ],
        "config": {
            "ativo": True,
            "versao": "1.0.0"
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_data, f, indent=2)
        temp_path = Path(f.name)

    try:
        result = analyzer.analyze(temp_path)

        assert result.success, "Analise deveria ter sucesso"
        assert result.metadata.get('type') == 'dict', "Deveria detectar tipo dict"
        assert 'schema' in result.metadata, "Deveria inferir schema"

        print(f"  OK Tipo: {result.metadata['type']}")
        print(f"  OK Chaves: {result.metadata['stats'].get('keys', [])}")
        print(f"  OK Schema inferido: presente")

    finally:
        temp_path.unlink()

    print("  PASSOU!\n")


def test_csv_analyzer():
    """Testa analisador de CSV"""
    print("Teste: Analisador de CSV")

    analyzer = DataFileAnalyzer()

    # Cria arquivo CSV de teste
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write("""nome,idade,cidade,salario
Maria,28,Sao Paulo,5000.00
Joao,35,Rio de Janeiro,7500.00
Ana,22,Belo Horizonte,3200.50
Pedro,45,Curitiba,9000.00
""")
        temp_path = Path(f.name)

    try:
        result = analyzer.analyze(temp_path)

        assert result.success, "Analise deveria ter sucesso"
        assert 'columns' in result.metadata, "Deveria detectar colunas"
        assert result.metadata['stats'].get('row_count', 0) >= 4, "Deveria contar linhas"

        print(f"  OK Colunas: {result.metadata.get('columns', [])}")
        print(f"  OK Linhas: {result.metadata['stats'].get('row_count', 0)}")
        print(f"  OK Tipos: {result.metadata.get('column_types', {})}")

    finally:
        temp_path.unlink()

    print("  PASSOU!\n")


def test_wav_analyzer():
    """Testa analisador de audio WAV"""
    print("Teste: Analisador de Audio WAV")

    analyzer = AudioAnalyzer()

    # Cria arquivo WAV de teste (1 segundo de silencio)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = Path(f.name)

    sample_rate = 44100
    duration = 1  # segundos
    channels = 2

    with wave.open(str(temp_path), 'w') as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)  # 16 bits
        wav.setframerate(sample_rate)

        # Gera silencio (zeros)
        for _ in range(sample_rate * duration):
            wav.writeframes(struct.pack('<hh', 0, 0))

    try:
        result = analyzer.analyze(temp_path)

        assert result.success, "Analise deveria ter sucesso"
        assert 'audio' in result.metadata, "Deveria ter metadados de audio"

        audio_info = result.metadata['audio']
        assert audio_info['sample_rate'] == sample_rate, "Sample rate incorreto"
        assert audio_info['channels'] == channels, "Numero de canais incorreto"
        assert abs(audio_info['duration_seconds'] - duration) < 0.1, "Duracao incorreta"

        print(f"  OK Sample rate: {audio_info['sample_rate']} Hz")
        print(f"  OK Canais: {audio_info['channels']}")
        print(f"  OK Duracao: {audio_info['duration_formatted']}")
        print(f"  OK Bitrate: {audio_info['bitrate_kbps']} kbps")

    finally:
        temp_path.unlink()

    print("  PASSOU!\n")


def test_registry():
    """Testa registro central de skills"""
    print("Teste: Registro de Skills")

    registry = get_registry()

    # Testa listagem de skills
    skills = list_skills()
    assert len(skills) >= 10, "Deveria ter pelo menos 10 skills registrados"

    print(f"  OK Skills registrados: {len(skills)}")

    # Testa formatos suportados
    formats = get_supported_formats()
    assert 'text' in formats, "Deveria ter formatos de texto"
    assert 'audio' in formats, "Deveria ter formatos de audio"
    assert 'video' in formats, "Deveria ter formatos de video"

    print(f"  OK Formatos de texto: {formats['text']}")
    print(f"  OK Formatos de audio: {formats['audio']}")
    print(f"  OK Formatos de video: {formats['video']}")

    # Testa can_analyze
    assert can_analyze("video.mp4") == True
    assert can_analyze("audio.mp3") == True
    assert can_analyze("arquivo.xyz") == False

    print(f"  OK can_analyze funciona corretamente")

    # Testa get_media_type
    assert get_media_type("video.mp4") == "video"
    assert get_media_type("audio.mp3") == "audio"
    assert get_media_type("doc.pdf") == "text"

    print(f"  OK get_media_type funciona corretamente")

    print("  PASSOU!\n")


def test_analyze_file_function():
    """Testa funcao analyze_file"""
    print("Teste: Funcao analyze_file")

    # Cria arquivo de teste
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("Teste de analise automatica de arquivo.")
        temp_path = f.name

    try:
        result = analyze_file(temp_path)

        assert result.success, "Analise deveria ter sucesso"
        assert result.media_type == MediaType.TEXT, "Tipo deveria ser TEXT"
        assert result.content is not None, "Conteudo deveria estar presente"

        print(f"  OK Arquivo analisado com sucesso")
        print(f"  OK Tipo: {result.media_type.value}")
        print(f"  OK Formato: {result.media_format.extension if result.media_format else 'N/A'}")

    finally:
        Path(temp_path).unlink()

    print("  PASSOU!\n")


def test_markdown_analysis():
    """Testa analise de Markdown"""
    print("Teste: Analisador de Markdown")

    analyzer = TextAnalyzer()

    # Cria arquivo Markdown de teste
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write("""# Titulo Principal

## Secao 1

Este e um paragrafo com **negrito** e *italico*.

### Subsecao 1.1

- Item 1
- Item 2
- Item 3

## Secao 2

```python
def hello():
    print("Hello, World!")
```

[Link para Google](https://google.com)

![Imagem](imagem.png)
""")
        temp_path = Path(f.name)

    try:
        result = analyzer.analyze(temp_path)

        assert result.success, "Analise deveria ter sucesso"
        assert 'markdown_structure' in result.metadata, "Deveria ter estrutura de Markdown"

        md_struct = result.metadata['markdown_structure']
        assert len(md_struct['headers']) > 0, "Deveria detectar headers"
        assert len(md_struct['links']) > 0, "Deveria detectar links"
        assert len(md_struct['code_blocks']) > 0, "Deveria detectar code blocks"

        print(f"  OK Headers: {len(md_struct['headers'])}")
        print(f"  OK Links: {len(md_struct['links'])}")
        print(f"  OK Code blocks: {len(md_struct['code_blocks'])}")
        print(f"  OK Lists: {md_struct['lists']}")

    finally:
        temp_path.unlink()

    print("  PASSOU!\n")


def run_all_tests():
    """Executa todos os testes"""
    print("=" * 60)
    print("TESTES DE SKILLS DE ANALISE MULTIMIDIA")
    print("=" * 60)
    print()

    tests = [
        test_media_format_detection,
        test_text_analyzer,
        test_code_analyzer,
        test_json_analyzer,
        test_csv_analyzer,
        test_wav_analyzer,
        test_registry,
        test_analyze_file_function,
        test_markdown_analysis
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FALHOU: {e}\n")
            failed += 1
        except Exception as e:
            print(f"  ERRO: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"RESULTADO: {passed} passou, {failed} falhou")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
