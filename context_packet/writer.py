"""Output writers for chunks and context files."""

import json
from pathlib import Path

from .chunker import Chunk


def write_chunks_jsonl(chunks: list[Chunk], output_path: str | Path) -> None:
    """Write chunks to JSONL file."""
    output_path = Path(output_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            chunk_data = {
                'id': chunk.id,
                'doc_id': chunk.doc_id,
                'order': chunk.order,
                'text': chunk.text,
                'tokens': chunk.tokens,
                'citation': chunk.citation
            }
            f.write(json.dumps(chunk_data) + '\n')
    
    print(f"Wrote {len(chunks)} chunks to {output_path}")


def read_chunks_jsonl(input_path: str | Path) -> list[Chunk]:
    """Read chunks from JSONL file."""
    input_path = Path(input_path)
    chunks = []
    
    with open(input_path, encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                chunk = Chunk(
                    id=data['id'],
                    doc_id=data['doc_id'],
                    order=data['order'],
                    text=data['text'],
                    tokens=data['tokens'],
                    citation=data['citation'],
                    start_offset=0,  # These aren't stored in JSONL
                    end_offset=0
                )
                chunks.append(chunk)
    
    return chunks


def write_context_json(
    query: str,
    chunks: list[Chunk],
    limits: dict[str, int],
    output_path: str | Path
) -> None:
    """Write final context JSON file."""
    output_path = Path(output_path)
    
    context_data = {
        'query': query,
        'chunks': [
            {
                'id': chunk.id,
                'order': chunk.order,
                'text': chunk.text,
                'tokens': chunk.tokens,
                'score': getattr(chunk, 'score', 0.0),  # Score added later
                'citation': chunk.citation
            }
            for chunk in chunks
        ],
        'limits': limits
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(context_data, f, indent=2, ensure_ascii=False)
    
    total_tokens = sum(chunk.tokens for chunk in chunks)
    print(f"Wrote context with {len(chunks)} chunks ({total_tokens} tokens) to {output_path}")
