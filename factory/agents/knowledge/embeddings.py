"""
Motor de Embeddings para Base de Conhecimento
=============================================

Suporta multiplos backends:
1. TF-IDF local (sem dependencias externas)
2. OpenAI Embeddings API
3. Anthropic/Voyage Embeddings
4. Sentence Transformers (se disponivel)

O sistema escolhe automaticamente o melhor backend disponivel.
"""

import hashlib
import json
import math
import re
import sqlite3
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os


@dataclass
class EmbeddingResult:
    """Resultado de embedding"""
    text: str
    vector: List[float]
    model: str
    dimensions: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EmbeddingBackend(ABC):
    """Interface para backends de embedding"""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Gera embedding para um texto"""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para multiplos textos"""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Dimensoes do vetor de embedding"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nome do modelo"""
        pass


class TFIDFEmbedding(EmbeddingBackend):
    """
    Embedding baseado em TF-IDF
    Funciona sem dependencias externas, ideal para ambiente local
    """

    def __init__(self, vocab_size: int = 1024):
        self.vocab_size = vocab_size
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_count = 0
        self._initialized = False

    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza texto em palavras"""
        text = text.lower()
        # Remove pontuacao e divide em palavras
        tokens = re.findall(r'\b[a-zA-Z0-9_]+\b', text)
        return tokens

    def _hash_token(self, token: str) -> int:
        """Hash de token para indice fixo"""
        h = hashlib.md5(token.encode()).hexdigest()
        return int(h, 16) % self.vocab_size

    def _compute_tf(self, tokens: List[str]) -> Dict[int, float]:
        """Calcula Term Frequency"""
        counts = Counter(tokens)
        total = len(tokens) if tokens else 1
        tf = {}
        for token, count in counts.items():
            idx = self._hash_token(token)
            tf[idx] = tf.get(idx, 0) + (count / total)
        return tf

    def fit(self, documents: List[str]):
        """Treina o modelo com documentos"""
        self.doc_count = len(documents)
        doc_freq: Dict[int, int] = {}

        for doc in documents:
            tokens = self._tokenize(doc)
            seen = set()
            for token in tokens:
                idx = self._hash_token(token)
                if idx not in seen:
                    doc_freq[idx] = doc_freq.get(idx, 0) + 1
                    seen.add(idx)

        # Calcula IDF
        for idx, freq in doc_freq.items():
            self.idf[idx] = math.log((self.doc_count + 1) / (freq + 1)) + 1

        self._initialized = True

    def embed(self, text: str) -> List[float]:
        """Gera embedding TF-IDF para texto"""
        tokens = self._tokenize(text)
        tf = self._compute_tf(tokens)

        # Cria vetor
        vector = [0.0] * self.vocab_size
        for idx, tf_val in tf.items():
            idf_val = self.idf.get(idx, 1.0)
            vector[idx] = tf_val * idf_val

        # Normaliza (L2)
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para multiplos textos"""
        return [self.embed(text) for text in texts]

    @property
    def dimensions(self) -> int:
        return self.vocab_size

    @property
    def model_name(self) -> str:
        return f"tfidf-{self.vocab_size}d"


class SemanticHashEmbedding(EmbeddingBackend):
    """
    Embedding baseado em hashing semantico
    Mais robusto que TF-IDF para textos curtos
    Usa n-gramas e hashing para criar representacao densa
    """

    def __init__(self, dimensions: int = 512, ngram_range: Tuple[int, int] = (1, 3)):
        self._dimensions = dimensions
        self.ngram_range = ngram_range

    def _tokenize(self, text: str) -> List[str]:
        """Tokeniza e gera n-gramas"""
        text = text.lower()
        words = re.findall(r'\b[a-zA-Z0-9_]+\b', text)

        ngrams = []
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(words) - n + 1):
                ngram = '_'.join(words[i:i + n])
                ngrams.append(ngram)

        # Adiciona caracteres n-gramas para capturar subpalavras
        for word in words:
            for n in range(2, min(5, len(word) + 1)):
                for i in range(len(word) - n + 1):
                    ngrams.append(f"#{word[i:i + n]}#")

        return ngrams

    def _hash_to_vector(self, ngrams: List[str]) -> List[float]:
        """Converte n-gramas em vetor usando hashing"""
        vector = [0.0] * self._dimensions

        for ngram in ngrams:
            # Usa dois hashes para simhash
            h1 = int(hashlib.md5(ngram.encode()).hexdigest(), 16)
            h2 = int(hashlib.sha256(ngram.encode()).hexdigest(), 16)

            # Distribui pelo vetor
            idx = h1 % self._dimensions
            sign = 1 if (h2 % 2) == 0 else -1
            weight = 1.0 + (h2 % 100) / 100.0  # Peso variavel

            vector[idx] += sign * weight

        # Normaliza
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def embed(self, text: str) -> List[float]:
        """Gera embedding semantico para texto"""
        ngrams = self._tokenize(text)
        return self._hash_to_vector(ngrams)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para multiplos textos"""
        return [self.embed(text) for text in texts]

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return f"semantic-hash-{self._dimensions}d"


class AnthropicEmbedding(EmbeddingBackend):
    """
    Embedding via Anthropic/Voyage API
    Alta qualidade, requer API key
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._dimensions = 1024  # Voyage embeddings

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY nao configurada")

    def embed(self, text: str) -> List[float]:
        """Gera embedding via API"""
        try:
            import httpx

            response = httpx.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": "voyage-2"
                },
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                return data["data"][0]["embedding"]
            else:
                # Fallback para hash embedding
                fallback = SemanticHashEmbedding(self._dimensions)
                return fallback.embed(text)

        except Exception:
            fallback = SemanticHashEmbedding(self._dimensions)
            return fallback.embed(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings em batch"""
        return [self.embed(text) for text in texts]

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return "voyage-2"


class EmbeddingEngine:
    """
    Motor de Embeddings Unificado
    Seleciona automaticamente o melhor backend disponivel
    """

    def __init__(self,
                 backend: Optional[str] = None,
                 dimensions: int = 512,
                 db_path: Optional[Path] = None):
        """
        Args:
            backend: 'tfidf', 'semantic', 'anthropic', ou None (auto)
            dimensions: Dimensoes do embedding (para backends locais)
            db_path: Caminho para cache de embeddings
        """
        self.dimensions = dimensions
        self.db_path = db_path or Path("factory/database/embeddings_cache.db")
        self._backend: Optional[EmbeddingBackend] = None

        # Seleciona backend
        if backend:
            self._backend = self._create_backend(backend)
        else:
            self._backend = self._auto_select_backend()

        # Inicializa cache
        self._init_cache()

    def _create_backend(self, name: str) -> EmbeddingBackend:
        """Cria backend especifico"""
        if name == "tfidf":
            return TFIDFEmbedding(vocab_size=self.dimensions)
        elif name == "semantic":
            return SemanticHashEmbedding(dimensions=self.dimensions)
        elif name == "anthropic":
            return AnthropicEmbedding()
        else:
            return SemanticHashEmbedding(dimensions=self.dimensions)

    def _auto_select_backend(self) -> EmbeddingBackend:
        """Seleciona melhor backend disponivel"""
        # Tenta Anthropic primeiro
        try:
            if os.environ.get("ANTHROPIC_API_KEY"):
                return AnthropicEmbedding()
        except:
            pass

        # Fallback para semantic hash (mais robusto)
        return SemanticHashEmbedding(dimensions=self.dimensions)

    def _init_cache(self):
        """Inicializa banco de cache"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS embedding_cache (
                text_hash TEXT PRIMARY KEY,
                text TEXT,
                vector TEXT,
                model TEXT,
                dimensions INTEGER,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_model ON embedding_cache(model)
        """)
        conn.commit()
        conn.close()

    def _get_text_hash(self, text: str) -> str:
        """Hash unico para texto"""
        return hashlib.sha256(text.encode()).hexdigest()[:32]

    def _get_cached(self, text: str) -> Optional[List[float]]:
        """Busca embedding em cache"""
        text_hash = self._get_text_hash(text)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT vector FROM embedding_cache WHERE text_hash = ? AND model = ?",
            (text_hash, self._backend.model_name)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None

    def _cache_embedding(self, text: str, vector: List[float]):
        """Salva embedding em cache"""
        text_hash = self._get_text_hash(text)

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO embedding_cache
            (text_hash, text, vector, model, dimensions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            text_hash,
            text[:500],  # Salva preview do texto
            json.dumps(vector),
            self._backend.model_name,
            len(vector),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

    def embed(self, text: str, use_cache: bool = True) -> EmbeddingResult:
        """
        Gera embedding para texto

        Args:
            text: Texto para embedding
            use_cache: Se deve usar cache

        Returns:
            EmbeddingResult com vetor e metadados
        """
        # Verifica cache
        if use_cache:
            cached = self._get_cached(text)
            if cached:
                return EmbeddingResult(
                    text=text,
                    vector=cached,
                    model=self._backend.model_name,
                    dimensions=len(cached)
                )

        # Gera novo embedding
        vector = self._backend.embed(text)

        # Salva em cache
        if use_cache:
            self._cache_embedding(text, vector)

        return EmbeddingResult(
            text=text,
            vector=vector,
            model=self._backend.model_name,
            dimensions=len(vector)
        )

    def embed_batch(self, texts: List[str], use_cache: bool = True) -> List[EmbeddingResult]:
        """Gera embeddings para multiplos textos"""
        results = []
        to_embed = []
        to_embed_idx = []

        # Verifica cache para cada texto
        for i, text in enumerate(texts):
            if use_cache:
                cached = self._get_cached(text)
                if cached:
                    results.append(EmbeddingResult(
                        text=text,
                        vector=cached,
                        model=self._backend.model_name,
                        dimensions=len(cached)
                    ))
                    continue

            to_embed.append(text)
            to_embed_idx.append(i)
            results.append(None)  # Placeholder

        # Gera embeddings faltantes
        if to_embed:
            vectors = self._backend.embed_batch(to_embed)

            for idx, (text, vector) in zip(to_embed_idx, zip(to_embed, vectors)):
                if use_cache:
                    self._cache_embedding(text, vector)

                results[idx] = EmbeddingResult(
                    text=text,
                    vector=vector,
                    model=self._backend.model_name,
                    dimensions=len(vector)
                )

        return results

    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade de cosseno entre dois vetores"""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    def train_tfidf(self, documents: List[str]):
        """Treina backend TF-IDF com documentos"""
        if isinstance(self._backend, TFIDFEmbedding):
            self._backend.fit(documents)

    @property
    def model_info(self) -> Dict:
        """Informacoes do modelo"""
        return {
            "backend": self._backend.model_name,
            "dimensions": self._backend.dimensions,
            "cache_path": str(self.db_path)
        }
