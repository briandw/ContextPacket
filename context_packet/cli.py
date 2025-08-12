"""Command line interface for ContextPacket."""

import argparse
import sys
from pathlib import Path

from .chunker import SlidingWindowChunker, chunk_documents
from .config import Config, create_default_config, load_config
from .ingest import ingest_corpus
from .parser import DocumentParser
from .scorer import ChunkScorer, write_scores_jsonl
from .writer import write_chunks_jsonl


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="ContextPacket - Document chunking and context creation"
    )

    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to configuration YAML file'
    )

    parser.add_argument(
        '--corpus',
        type=str,
        required=True,
        help='Path to corpus directory'
    )

    parser.add_argument(
        '--goal',
        type=str,
        help='Query goal for context creation'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='.',
        help='Output directory (default: current directory)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Stop after parsing, don\'t chunk'
    )

    parser.add_argument(
        '--dump-chunks',
        action='store_true',
        help='Output chunks.jsonl file'
    )

    parser.add_argument(
        '--dump-scores',
        action='store_true',
        help='Output scores.jsonl file'
    )

    parser.add_argument(
        '--create-config',
        type=str,
        help='Create default config file at specified path'
    )

    return parser


def run_pipeline(config: Config, corpus_path: str, output_dir: str, query: str | None = None, dry_run: bool = False, dump_chunks: bool = False, dump_scores: bool = False) -> None:
    """Run the ContextPacket pipeline: Parse & Chunk, and optionally Score."""
    pipeline_stage = "M1 (Parse & Chunk)"
    if query:
        pipeline_stage = "M2 (Parse & Chunk & Score)"

    print(f"Running {pipeline_stage} on corpus: {corpus_path}")
    print(f"Config: chunk_size={config.chunk_size}, overlap={config.chunk_overlap}")
    if query:
        print(f"Query: {query}")

    # Step 1: Ingest corpus
    print("\n1. Ingesting corpus...")
    files = ingest_corpus(corpus_path, config)

    if not files:
        print("No files found in corpus!")
        return

    # Step 2: Parse documents
    print("\n2. Parsing documents...")
    parser = DocumentParser()
    docs = []

    for file_info in files:
        try:
            if parser.can_parse(file_info):
                doc = parser.parse(file_info)
                docs.append(doc)
                print(f"  Parsed {file_info.relative_path} ({len(doc.text)} chars)")
            else:
                print(f"  Skipped {file_info.relative_path} (no parser)")
        except Exception as e:
            print(f"  Error parsing {file_info.relative_path}: {e}")

    print(f"Successfully parsed {len(docs)} documents")

    if dry_run:
        print("Dry run complete - stopping before chunking")
        return

    # Step 3: Chunk documents
    print("\n3. Chunking documents...")
    chunker = SlidingWindowChunker(
        chunk_size=config.chunk_size,
        overlap=config.chunk_overlap
    )

    chunks = chunk_documents(docs, chunker)

    total_tokens = sum(chunk.tokens for chunk in chunks)
    print(f"Created {len(chunks)} chunks with {total_tokens} total tokens")

    # Step 4: Output chunks if requested
    if dump_chunks:
        output_path = Path(output_dir) / "chunks.jsonl"
        write_chunks_jsonl(chunks, output_path)

    # Step 5: Score chunks if query provided
    if query:
        print("\n4. Scoring chunks against query...")
        scorer = ChunkScorer(config, use_mock=False)  # Use real scorer
        scored_chunks = scorer.score_chunks(query, chunks)

        avg_score = sum(sc.score for sc in scored_chunks) / len(scored_chunks)
        print(f"Scored {len(scored_chunks)} chunks, average score: {avg_score:.3f}")

        # Output scores if requested
        if dump_scores:
            scores_path = Path(output_dir) / "scores.jsonl"
            write_scores_jsonl(scored_chunks, scores_path)

    stage_name = "M2" if query else "M1"
    print(f"{stage_name} pipeline complete!")


def main() -> None:
    """Main CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle config creation
    if args.create_config:
        create_default_config(args.create_config)
        print(f"Created default config at {args.create_config}")
        return

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Run pipeline
    try:
        run_pipeline(
            config=config,
            corpus_path=args.corpus,
            output_dir=args.output,
            query=args.goal,
            dry_run=args.dry_run,
            dump_chunks=args.dump_chunks,
            dump_scores=args.dump_scores
        )
    except Exception as e:
        print(f"Pipeline error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
