"""Command line interface for ContextPacket."""

import argparse
import sys
from pathlib import Path

from .chunker import SlidingWindowChunker, chunk_documents
from .config import Config, create_default_config, load_config
from .ingest import ingest_corpus
from .parser import DocumentParser
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
        help='Query goal for context creation (M2/M3 feature)'
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
        '--create-config',
        type=str,
        help='Create default config file at specified path'
    )
    
    return parser


def run_m1_pipeline(config: Config, corpus_path: str, output_dir: str, dry_run: bool = False, dump_chunks: bool = False) -> None:
    """Run the M1 pipeline: Parse & Chunk."""
    print(f"Running M1 pipeline on corpus: {corpus_path}")
    print(f"Config: chunk_size={config.chunk_size}, overlap={config.chunk_overlap}")
    
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
    
    print("M1 pipeline complete!")


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
        run_m1_pipeline(
            config=config,
            corpus_path=args.corpus,
            output_dir=args.output,
            dry_run=args.dry_run,
            dump_chunks=args.dump_chunks
        )
    except Exception as e:
        print(f"Pipeline error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
