# Summarisation Pipeline – Cross-Encoder MVP (v3)

_Last updated: 2025-08-10_

---

## 1 · Purpose  
Build a **simplified summarisation pipeline** that ingests mixed-format documentation, applies a **sliding-window chunker**, scores each chunk against a user-refined query using a **local cross-encoder model**, and outputs a JSON file with only the most relevant chunks, within defined token budgets.

---

## 2 · Goals & Success Metrics  

| Goal | Metric | Target |
|------|--------|--------|
| Relevance | F1 (manual spot-check) | ≥ 0.85 |
| Token compliance | Medium ≤ 32k; Small ≤ 8k (±10 %, `tiktoken`) | 100 % |
| Code quality | `mypy --strict` + `ruff` | 0 errors |
| Test reliability | `pytest` local run | 100 % pass |

---

## 3 · Scope (MVP)  

**In-scope**  
- Query refinement: optional LLM intent extraction + expansion  
- Parsing: HTML (BeautifulSoup), PDF (PyMuPDF + OCR fallback), plaintext  
- Chunking: Sliding window default, configurable chunk size/overlap  
- Scoring: Local cross-encoder model (e.g., ColBERT or SBERT cross-encoder)  
- Thresholding: Score-sorted selection to meet token budgets, then resort by original doc order  
- Output: JSON with chunks, scores, citations, and original order  
- CLI interface  

**Out-of-scope (for MVP)**  
- BM25/vector hybrid  
- Multi-pass distillation  
- DB/cache layer  
- GUI / real-time watchers  
- Automatic eval tooling (planned later)  

---

## 4 · Functional Requirements  

| # | Component | Description |
|---|-----------|-------------|
| 1 | **Config Loader** | YAML → `Config` dataclass (pydantic) |
| 2 | **Query Prep** | Optional LLM pipeline: refine → expand; user confirms final query |
| 3 | **Ingest** | Walk directory, hash files (SHA-256) |
| 4 | **Parser** | Extract text; OCR scanned PDFs |
| 5 | **Chunker** | Sliding window default; configurable size & overlap |
| 6 | **Scorer** | Cross-encoder relevance score for each chunk |
| 7 | **Collector** | Store `(chunk_id, score, token_count, citation, order)` in memory or flat file |
| 8 | **Selector** | Sort by score (desc), select chunks until budget hit, then reorder by original doc position |
| 9 | **Writer** | Output `context.json` with all selected chunks |
| 10 | **CLI** | `summarise --config cfg.yml --goal "LLVM IR internals"` |

---

## 5 · Non-Functional Requirements  

- **Python 3.11+ only**  
- **Minimal dependencies**:  
  - `beautifulsoup4`, `pymupdf`, `pytesseract`, `sentence-transformers`, `tiktoken`, `rich`, `pydantic`  
- **Concurrency**:  
  - CPU parse/OCR: `ProcessPoolExecutor` (configurable workers)  
- **Configurable scoring model** via model name/path  
- **Retry policy** for LLM query-prep stage (if enabled)  

---

## 6 · Output Format  

Example `context.json`:
```json
{
  "query": "LLVM IR internals",
  "chunks": [
    {
      "id": "doc1_p3_c2",
      "order": 42,
      "text": "...",
      "tokens": 115,
      "score": 0.92,
      "citation": "§a1b2c3:P:3:2"
    }
  ],
  "limits": { "large": 32000, "small": 8000 }
}
```

---

## 7 · CLI Example  

```bash
summarise --config cfg.yml --goal "LLVM IR internals"
```

`cfg.yml` excerpt:
```yaml
chunk_size: 512
chunk_overlap: 128
score_threshold: null      # null = auto threshold to budget
large_limit: 32000
small_limit: 8000
model_path: "./models/cross-encoder"
```

---

## 8 · Acceptance Criteria  

- Produces JSON with all required metadata and citations.  
- Token budgets respected (±10%).  
- F1 ≥ 0.85 on manual spot-check of demo corpus.  
- No `mypy --strict` or `ruff` errors.  
- All non-LLM code ≥ 90% pytest coverage.  
