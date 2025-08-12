"""Text chunking with sliding window approach."""

from collections.abc import Iterator

import tiktoken
from pydantic import BaseModel

from .parser import ParsedDocument


class Chunk(BaseModel):
    """A chunk of text with metadata."""

    id: str
    doc_id: str
    order: int
    text: str
    tokens: int
    citation: str
    start_offset: int
    end_offset: int


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def create_citation(file_hash: str, media_type: str, start: int, end: int) -> str:
    """Create citation in format §{file_sha256}:{media}:{start}:{end}."""
    media_short = media_type[0].upper()  # 'P' for pdf, 'H' for html, 'T' for text
    return f"§{file_hash}:{media_short}:{start}:{end}"


class SlidingWindowChunker:
    """Sliding window chunker that extracts middle segments."""

    def __init__(self, chunk_size: int = 512, overlap: int = 256):
        """Initialize chunker with size and overlap parameters."""
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")

        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk_size")

        # Calculate middle segment size
        self.middle_size = chunk_size - overlap
        self.padding = overlap // 2

    def chunk_document(self, doc: ParsedDocument) -> Iterator[Chunk]:
        """Chunk document using sliding window approach."""
        # Tokenize the full document
        tokens = self.encoding.encode(doc.text)

        if len(tokens) <= self.chunk_size:
            # Document is smaller than chunk size, return as single chunk
            chunk_text = self.encoding.decode(tokens)

            yield Chunk(
                id=f"{doc.file_info.sha256[:8]}_c0",
                doc_id=doc.file_info.sha256,
                order=0,
                text=chunk_text,
                tokens=len(tokens),
                citation=create_citation(
                    doc.file_info.sha256,
                    doc.media_type,
                    0,
                    len(tokens)
                ),
                start_offset=0,
                end_offset=len(tokens)
            )
            return

        chunk_order = 0
        position = 0

        while position < len(tokens):
            # Define window boundaries
            window_start = position
            window_end = min(position + self.chunk_size, len(tokens))

            # Extract middle segment for scoring
            if window_end - window_start >= self.chunk_size:
                # Full window: extract middle segment
                middle_start = window_start + self.padding
                middle_end = middle_start + self.middle_size
            else:
                # Partial window at end: use entire remaining content
                middle_start = window_start
                middle_end = window_end

            # Ensure we don't go beyond token boundaries
            middle_start = max(window_start, middle_start)
            middle_end = min(window_end, middle_end)

            if middle_start >= middle_end:
                break

            # Extract text for the middle segment
            middle_tokens = tokens[middle_start:middle_end]
            chunk_text = self.encoding.decode(middle_tokens)

            # Create chunk
            yield Chunk(
                id=f"{doc.file_info.sha256[:8]}_c{chunk_order}",
                doc_id=doc.file_info.sha256,
                order=chunk_order,
                text=chunk_text,
                tokens=len(middle_tokens),
                citation=create_citation(
                    doc.file_info.sha256,
                    doc.media_type,
                    middle_start,
                    middle_end
                ),
                start_offset=middle_start,
                end_offset=middle_end
            )

            chunk_order += 1

            # Move position by step size (chunk_size - overlap)
            step_size = self.chunk_size - self.overlap
            position += step_size


def chunk_documents(docs: list[ParsedDocument], chunker: SlidingWindowChunker) -> list[Chunk]:
    """Chunk multiple documents and return all chunks with global ordering."""
    all_chunks = []
    global_order = 0

    for doc in docs:
        doc_chunks = list(chunker.chunk_document(doc))

        # Update global order for each chunk
        for chunk in doc_chunks:
            chunk.order = global_order
            all_chunks.append(chunk)
            global_order += 1

    return all_chunks
