# Development Plan – ContextPacket (Cross-Encoder MVP)

_Last updated: 2025-08-12_

---

## Milestone Progress

### ✅ M1: Parse & Chunk (COMPLETE)
**Status**: Delivered and tested
- ✅ Ingest: Directory walking, file filtering, SHA-256 hashing
- ✅ Parsers: HTML (BeautifulSoup), PDF (PyMuPDF + OCR), plaintext
- ✅ Chunker: Sliding window (512 tokens, 256 overlap, middle segment extraction)
- ✅ Citations: `§{file_sha256}:{media}:{start}:{end}` format
- ✅ Output: `chunks.jsonl` with deterministic ordering
- ✅ CLI: Basic interface with config loading

**Artifacts**: `config.py`, `ingest.py`, `parser.py`, `chunker.py`, `writer.py`, `cli.py`

### ✅ M2: Score & Persist (COMPLETE)
**Status**: Delivered and tested with mock scorer
- ✅ Scorer: Cross-encoder wrapper with batching (32 default batch size)
- ✅ MockScorer: Deterministic testing scorer for development
- ✅ MxbaiReranker: Integration ready for `mixedbread-ai/mxbai-rerank-base-v2`
- ✅ Persistence: JSONL format `{id, order, tokens, score, citation}`
- ✅ CLI: `--goal` query parameter and `--dump-scores` flag
- ✅ Pipeline: Integrated M1 → M2 flow

**Artifacts**: `scorer.py`, enhanced `cli.py`, `scores.jsonl` output

### 🔄 M3: Select & Assemble (NEXT)
**Status**: Ready to implement
- ⏳ Selector: Token budget-based selection by score (desc → original order)
- ⏳ Writer: Final `context.json` output with selected chunks
- ⏳ Multi-size outputs: `context_{large,medium,small}.json` variants
- ⏳ CLI: Complete pipeline M1 → M2 → M3

**Target Artifacts**: `selector.py`, enhanced `writer.py`, final `context.json`

---

## Current Technical Stack

### Environment Management
- **UV**: Fast Python package installer and resolver
- **Virtual Environment**: Clean `.venv` setup with Python 3.11+
- **pyproject.toml**: Modern Python packaging with optional dependencies

### Core Dependencies
- **pydantic**: Configuration and data models
- **tiktoken**: Token counting (cl100k_base encoding)
- **PyMuPDF**: PDF parsing with OCR fallback
- **beautifulsoup4**: HTML parsing
- **PyYAML**: Configuration file format

### Optional Dependencies
- **mxbai-rerank**: Production reranking model (v2) - requires auth
- **sentence-transformers**: Alternative cross-encoder support

### Development Tools
- **mypy**: Type checking with types-PyYAML stubs
- **ruff**: Linting and formatting
- **pytest**: Testing framework (ready to add)

### Model Integration
**Primary Reranker**: `mixedbread-ai/mxbai-rerank-base-v2`
```python
from mxbai_rerank import MxbaiRerankV2
model = MxbaiRerankV2("mixedbread-ai/mxbai-rerank-base-v2")
results = model.rank(query, documents, return_documents=True, top_k=3)
```

**Fallback**: MockScorer for testing and development

---

## Implementation Notes

### MxBai Reranker Integration
The scorer now supports the MxBai v2 reranker as the primary scoring model:

1. **Installation**: `pip install mxbai-rerank`
2. **Model**: `mixedbread-ai/mxbai-rerank-base-v2`
3. **API**: Uses `.rank()` method with `top_k` parameter
4. **Output**: Returns relevance scores in [0,1] range

### Configuration Updates
The config now includes:
- `model_path`: Path or HuggingFace model name
- `batch_size`: Configurable batch processing (default 32)
- `score_threshold`: Optional score cutoff (null = auto-budget)

### Current Pipeline Flow
```
Input Corpus → M1(Parse & Chunk) → M2(Score) → [M3(Select & Assemble)] → context.json
```

**M1**: Processes 1,951 chunks from test corpus (499k tokens)
**M2**: Scores all chunks against query (avg ~0.49 with mock scorer)
**M3**: Will select optimal chunks within token budgets

---

## Next Steps (M3 Implementation)

1. **Create selector.py**
   - Token budget enforcement (large: 32k, medium: 16k, small: 8k)
   - Score-based selection with original order restoration
   
2. **Enhance writer.py**
   - Multi-format output (`context.json`, size variants)
   - Schema validation and token verification
   
3. **Complete CLI integration**
   - Full M1→M2→M3 pipeline
   - Budget selection flags
   
4. **Testing & validation**
   - End-to-end pipeline tests
   - Manual F1 evaluation on demo corpus

---

## Deliverables (Updated)
- ✅ `contextpacket` CLI tool with M1+M2 capabilities
- ✅ JSONL intermediate outputs (`chunks.jsonl`, `scores.jsonl`)
- ⏳ `context.json` final output matching PRD format
- ✅ Type-clean (`mypy --strict`) and lint-clean (`ruff`)
- ⏳ ≥ 90% pytest coverage on all non-LLM logic
