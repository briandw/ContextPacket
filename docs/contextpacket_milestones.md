# ContextPacket – MVP Milestones

_Last updated: 2025-08-10_

---

## High-level milestones
1. **M1: Parse & Chunk** – ingest corpus, extract clean text, sliding-window chunking with half-overlap, citations + stable ordering.
2. **M2: Score & Persist** – run cross-encoder over all chunks vs final query, record `(id, order, tokens, score, citation)` to JSONL (or parquet) for later thresholding.
3. **M3: Select & Assemble** – token-budget selection by score, then resort by original order, write `context.json` (and optional `context_{large,medium,small}.json`).

---

## Detailed breakdown

### M1: Parse & Chunk
**Scope**
- Ingest: walk directory, filter by extensions, SHA-256 per file.
- Parsers: HTML (BS4), PDF (PyMuPDF + OCR fallback), plaintext.
- Normalization: preserve paragraph boundaries, headings/anchors; strip boilerplate.
- Chunker: sliding window; `chunk_size = N`, `overlap = N/2`; each window yields a **middle segment** as the chunk text; store `order` and source offsets.
- Citations: `§{file_sha256}:{media}:{start}:{end}`.

**Artifacts**
- `contextpacket/parser.py`, `chunker.py`
- Intermediate: `chunks.jsonl` with `{id, doc_id, order, text, tokens, citation}`

**Exit criteria**
- Parses demo fixtures; OCR fallback exercised in tests.
- Overlap math correct (unit tests verify middle extraction).
- Deterministic `order` across runs.
- `mypy --strict` clean; tests pass.

---

### M2: Score & Persist
**Scope**
- Cross-encoder wrapper: configurable local model path/name; batched scoring (size tuned).
- Scoring run: `(query, chunk_text) -> score in [0,1]`.
- Persistence: append-only JSONL (or parquet) `{id, order, tokens, score, citation}` to avoid high RAM footprints.

**Artifacts**
- `scorer.py`
- `scores.jsonl` (or `scores.parquet`)

**Exit criteria**
- Stable, repeatable scores for same inputs (given fixed model).
- Throughput acceptable on demo corpus; batch size configurable.
- Unit tests with mocked model verify batching order intact.
- `mypy/ruff/pytest` clean.

---

### M3: Select & Assemble
**Scope**
- Budgeting: compute token budgets for Large/Medium/Small.
- Selection: sort by `score desc`, take top chunks until budget hit.
- **Reorder**: sort the selected set by `order` before output.
- Writer: emit `context.json` (or `context_{big,medium,small}.json`) with `query`, `limits`, `chunks:[{id, order, text, tokens, score, citation}]`.

**Artifacts**
- `selector.py`, `writer.py`
- Final: `context.json` (plus size variants if enabled)

**Exit criteria**
- Budgets respected (±10% with `tiktoken`).
- Manual spot-check F1 ≥ 0.85 on demo corpus.
- JSON schema validated in tests.
- `mypy/ruff/pytest` clean.

---

## Cross-cutting tasks (parallelizable)
- **Config & CLI** (tiny milestone): `contextpacket --config cfg.yml --goal "..."`; flags for `--dry-run`, `--dump-chunks`, `--dump-scores`.
- **Logging**: JSONL per stage (counts, durations).
- **Docs**: quickstart, config reference, sample outputs.
- **Fixtures & Tests**: demo corpus; mocks for LLM & scorer; ≥90% coverage for non-LLM code.

---

## Optional add-ons after M3 (fast wins)
- **Auto-threshold mode**: if `score_threshold: null`, keep top-K by score until budget; else fixed threshold plus cap to budget.
- **Markdown views**: generate `context_small.md` from selected chunks.
- **Parquet support**: faster local analytics on scores.
