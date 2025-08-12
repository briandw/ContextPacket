# ContextPacket

A document chunking and context creation pipeline with cross-encoder scoring for building high-quality context windows from mixed-format document corpora.

## Features

- **Multi-format parsing**: HTML, PDF (with OCR fallback), and plaintext
- **Sliding window chunking**: Configurable chunk size with overlap for optimal context
- **Cross-encoder scoring**: Relevance scoring using MxBai reranker or custom models
- **Token budget management**: Automatic selection within configurable token limits
- **Deterministic output**: Stable citations and ordering across runs
- **CLI interface**: Simple command-line tool for batch processing

## Quick Start

### Prerequisites

1. **HuggingFace Authentication**: Create a `.env` file with your HuggingFace token:
   ```bash
   echo "HUGGINGFACE_HUB_TOKEN=hf_your_token_here" > .env
   ```

2. **Python 3.11+**: Required for modern type hints and performance

### Installation with UV (Recommended)

```bash
# Create virtual environment
uv venv --python 3.11
source .venv/bin/activate

# Install ContextPacket
uv pip install -e .

# Or install from requirements
uv pip install -r requirements.txt
```

### Installation with pip

```bash
pip install -r requirements.txt
pip install -e .
```

### Basic Usage

```bash
# M1: Parse and chunk documents
contextpacket --config config.yml --corpus ./docs --dump-chunks

# M2: Add relevance scoring with query
contextpacket --config config.yml --corpus ./docs --goal "machine learning concepts" --dump-scores

# M3: Generate final context (coming soon)
contextpacket --config config.yml --corpus ./docs --goal "machine learning concepts"
```

## Configuration

Create a `config.yml` file:

```yaml
# Chunking parameters
chunk_size: 512
chunk_overlap: 256

# Token budgets
large_limit: 32000
medium_limit: 16000
small_limit: 8000

# Scoring model
model_path: "mixedbread-ai/mxbai-rerank-base-v2"
batch_size: 32

# File processing
include_extensions:
  - "txt"
  - "md"
  - "html"
  - "pdf"
recursive: true
```

## Current Status

### ✅ M1: Parse & Chunk (Complete)
- Multi-format document parsing
- Sliding window chunking with configurable overlap
- Citation generation (`§{hash}:{media}:{start}:{end}`)
- JSONL output for chunk data

### ✅ M2: Score & Persist (Complete)
- Cross-encoder relevance scoring
- MxBai reranker integration
- Batched processing for performance
- Score persistence to JSONL

### 🔄 M3: Select & Assemble (Next)
- Token budget-based selection
- Final context.json output
- Multi-size context variants

## Pipeline Architecture

```
Input Corpus → M1(Parse & Chunk) → M2(Score) → M3(Select & Assemble) → context.json
```

## Development

### Code Quality

```bash
# Type checking
mypy . --ignore-missing-imports

# Linting and formatting
ruff check --fix

# Format code
ruff format
```

### Project Structure

```
context_packet/
├── __init__.py
├── config.py      # Configuration management
├── ingest.py      # File discovery and hashing
├── parser.py      # Multi-format text extraction
├── chunker.py     # Sliding window chunking
├── scorer.py      # Cross-encoder scoring
├── writer.py      # Output formatting
└── cli.py         # Command-line interface
```

## Model Support

### Primary Reranker
- **MxBai v2**: `mixedbread-ai/mxbai-rerank-base-v2`
- Requires HuggingFace authentication for production use

### Fallback Options
- **MockScorer**: Deterministic scoring for testing
- **sentence-transformers**: Alternative cross-encoder support

## License

MIT License - see [LICENSE](LICENSE) for details.
