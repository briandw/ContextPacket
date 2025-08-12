"""Cross-encoder scoring for chunk relevance."""

import json
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

try:
    from dotenv import load_dotenv
    load_dotenv()
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

try:
    from sentence_transformers import CrossEncoder
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    from mxbai_rerank import MxbaiRerankV2
    from huggingface_hub import login
    HAS_MXBAI = True
except ImportError:
    HAS_MXBAI = False

from .chunker import Chunk
from .config import Config


@dataclass
class ScoredChunk:
    """A chunk with its relevance score."""

    id: str
    doc_id: str
    order: int
    text: str
    tokens: int
    citation: str
    score: float


class Scorer(Protocol):
    """Protocol for chunk scoring models."""

    def score_batch(self, query: str, chunks: list[Chunk]) -> list[float]:
        """Score a batch of chunks against a query."""
        ...


class MockScorer:
    """Mock scorer for testing that returns random-like but deterministic scores."""

    def __init__(self, seed: int = 42):
        """Initialize with seed for deterministic scores."""
        self.seed = seed

    def score_batch(self, query: str, chunks: list[Chunk]) -> list[float]:
        """Return deterministic pseudo-random scores based on chunk content."""
        scores = []
        for chunk in chunks:
            # Simple hash-based scoring that's deterministic
            # Use a more stable hash approach
            hash_input = f"{query}|{chunk.id}|{chunk.citation}"
            content_hash = abs(hash(hash_input))
            score = (content_hash % 1000) / 1000.0 * 0.8 + 0.1  # Range 0.1-0.9
            scores.append(score)
        return scores


class CrossEncoderScorer:
    """Cross-encoder based scorer using sentence-transformers."""

    def __init__(self, model_path: str, batch_size: int = 32):
        """Initialize cross-encoder scorer."""
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError("sentence-transformers required for CrossEncoderScorer")

        self.model_path = model_path
        self.batch_size = batch_size
        self.model = None

    def _load_model(self) -> None:
        """Lazy load the model."""
        if self.model is None:
            try:
                self.model = CrossEncoder(self.model_path)
            except Exception as e:
                raise ValueError(f"Failed to load cross-encoder model from {self.model_path}: {e}") from e

    def score_batch(self, query: str, chunks: list[Chunk]) -> list[float]:
        """Score chunks using cross-encoder model."""
        self._load_model()

        if not chunks:
            return []

        # Prepare input pairs for cross-encoder
        pairs = [(query, chunk.text) for chunk in chunks]

        # Get scores from model (returns raw logits, need to convert to [0,1])
        raw_scores = self.model.predict(pairs)  # type: ignore

        # Convert to probabilities using sigmoid
        import math
        scores = [1.0 / (1.0 + math.exp(-score)) for score in raw_scores]

        return scores


class MxbaiScorer:
    """MxBai reranker based scorer."""

    def __init__(self, model_path: str = "mixedbread-ai/mxbai-rerank-base-v2"):
        """Initialize MxBai reranker."""
        if not HAS_MXBAI:
            raise ImportError("mxbai-rerank required for MxbaiScorer")

        self.model_path = model_path
        self.model = None

    def _load_model(self) -> None:
        """Lazy load the model."""
        if self.model is None:
            # Ensure HuggingFace token is available and authenticate
            hf_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
            if not hf_token:
                raise ValueError(
                    "HUGGINGFACE_HUB_TOKEN environment variable is required for MxBai reranker. "
                    "Please set it in your .env file or environment."
                )
            
            # Authenticate with HuggingFace
            login(token=hf_token)
            
            try:
                self.model = MxbaiRerankV2(self.model_path)
                print(f"✓ Loaded MxBai reranker: {self.model_path}")
            except Exception as e:
                raise ValueError(f"Failed to load MxBai model from {self.model_path}: {e}") from e

    def score_batch(self, query: str, chunks: list[Chunk]) -> list[float]:
        """Score chunks using MxBai reranker."""
        self._load_model()

        if not chunks:
            return []

        # Prepare documents for MxBai
        documents = [chunk.text for chunk in chunks]

        # Get ranked results
        results = self.model.rank(query, documents, return_documents=False)  # type: ignore
        
        # Extract scores (MxBai returns RankResult objects)
        scores = [result.score for result in results]

        return scores


class ChunkScorer:
    """Main chunk scorer that handles batching and persistence."""

    def __init__(self, config: Config, use_mock: bool = False):
        """Initialize chunk scorer."""
        self.config = config
        self.batch_size = getattr(config, 'batch_size', 32)

        if use_mock:
            self.scorer: Scorer = MockScorer()
            print("Using MockScorer for testing")
        elif HAS_MXBAI:
            # Prefer MxBai reranker as primary scorer
            self.scorer = MxbaiScorer(model_path=config.model_path)
            print(f"Using MxBaiScorer with model: {config.model_path}")
        elif HAS_SENTENCE_TRANSFORMERS:
            # Fallback to sentence-transformers
            self.scorer = CrossEncoderScorer(
                model_path=config.model_path,
                batch_size=self.batch_size
            )
            print(f"Using CrossEncoderScorer with model: {config.model_path}")
        else:
            # Final fallback to mock scorer
            self.scorer = MockScorer()
            print("Using MockScorer (no other scorers available)")

    def score_chunks(self, query: str, chunks: list[Chunk]) -> list[ScoredChunk]:
        """Score all chunks against query with batching."""
        if not chunks:
            return []

        scored_chunks = []

        # Process chunks in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_scores = self.scorer.score_batch(query, batch)

            # Create scored chunks
            for chunk, score in zip(batch, batch_scores, strict=False):
                scored_chunk = ScoredChunk(
                    id=chunk.id,
                    doc_id=chunk.doc_id,
                    order=chunk.order,
                    text=chunk.text,
                    tokens=chunk.tokens,
                    citation=chunk.citation,
                    score=score
                )
                scored_chunks.append(scored_chunk)

        return scored_chunks

    def score_chunks_streaming(self, query: str, chunks: list[Chunk]) -> Iterator[ScoredChunk]:
        """Score chunks in batches and yield results as they're ready."""
        if not chunks:
            return

        # Process chunks in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_scores = self.scorer.score_batch(query, batch)

            # Yield scored chunks
            for chunk, score in zip(batch, batch_scores, strict=False):
                scored_chunk = ScoredChunk(
                    id=chunk.id,
                    doc_id=chunk.doc_id,
                    order=chunk.order,
                    text=chunk.text,
                    tokens=chunk.tokens,
                    citation=chunk.citation,
                    score=score
                )
                yield scored_chunk


def write_scores_jsonl(scored_chunks: list[ScoredChunk], output_path: str | Path) -> None:
    """Write scored chunks to JSONL file."""
    output_path = Path(output_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in scored_chunks:
            chunk_data = {
                'id': chunk.id,
                'order': chunk.order,
                'tokens': chunk.tokens,
                'score': chunk.score,
                'citation': chunk.citation
            }
            f.write(json.dumps(chunk_data) + '\n')

    print(f"Wrote {len(scored_chunks)} scored chunks to {output_path}")


def append_scores_jsonl(scored_chunks: list[ScoredChunk], output_path: str | Path) -> None:
    """Append scored chunks to JSONL file (for streaming)."""
    output_path = Path(output_path)

    with open(output_path, 'a', encoding='utf-8') as f:
        for chunk in scored_chunks:
            chunk_data = {
                'id': chunk.id,
                'order': chunk.order,
                'tokens': chunk.tokens,
                'score': chunk.score,
                'citation': chunk.citation
            }
            f.write(json.dumps(chunk_data) + '\n')


def read_scores_jsonl(input_path: str | Path) -> list[ScoredChunk]:
    """Read scored chunks from JSONL file."""
    input_path = Path(input_path)
    scored_chunks = []

    with open(input_path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                scored_chunk = ScoredChunk(
                    id=data['id'],
                    doc_id='',  # Not stored in scores JSONL
                    order=data['order'],
                    text='',    # Not stored in scores JSONL
                    tokens=data['tokens'],
                    citation=data['citation'],
                    score=data['score']
                )
                scored_chunks.append(scored_chunk)

    return scored_chunks
