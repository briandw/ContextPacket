# Summarisation Pipeline – Product Requirements & Implementation Plan (v2)

_Last updated: 2025‑06‑29_

---

## 1 · Purpose  
Create a **summarisation pipeline** that ingests mixed‑format documentation and outputs three context packets—**Big** (unlimited), **Medium** (≤ `large_limit`, default 32 k tokens), and **Small** (≤ `small_limit`, default 8 k tokens). These packets are designed to prime downstream LLM calls.

---

## 2 · Goals & Success Metrics  

| Goal | Metric | Target |
|------|--------|--------|
| Coverage – document level | **Recall@Doc**: critical docs kept<br>**Precision@Doc**: non‑critical skipped | 100 % / 100 % |
| Coverage – paragraph level | **Recall@Para**: critical paragraphs summarised<br>**Precision@Para**: irrelevant paragraphs excluded | 100 % / ≥ 95 % |
| Size compliance | Medium ≤ 32 k; Small ≤ 8 k (±10 %, `tiktoken` encoding) | 100 % |
| Code quality | `mypy --strict` + `ruff` | 0 errors |
| Test reliability | `pytest` local run | 100 % pass |
| Human spot‑check | Manual pass rate | ≥ 90 % |


---

## 3 · In‑Scope  

* Directory ingestion & SHA‑256 hashing  
* Parsers: PDF (Unstructured + PyMuPDF + OCR fallback), HTML/MD (BeautifulSoup), plaintext  
* **QueryFix** node: normalize → correct → expand  
* **Glance** classifier: BM25 + vector similarity (top‑K aggregation)  
* Digest summariser  
* Two‑pass **Distiller** with token‑budget enforcement  
* SQLite cache keyed by `(sha256(raw_text) ^ sha256(final_query))`  
* Config via YAML  
* Outputs: `context_big.md`, `context_medium.md`, `context_small.md` with URI‑style citations `[§hash:media:start:end]`  
* Orchestration with **LangGraph** event loop + process pool for CPU‑bound parsing  
* Progress bar (`rich`) and benchmarking script  

### 3.1 Out‑of‑Scope (v1)

* Vector databases / RAG retrieval  
* Real‑time file‑system watchers  
* GUI / dashboard  
* Bit‑exact determinism guarantees  


---

## 4 · Functional Requirements  

| # | Component | Description |
|---|-----------|-------------|
| 1 | **Config Loader** | YAML → `Config` object with defaults & validation (pydantic) |
| 2 | **QueryFix Node** | Optional pipeline: _normalize_ ➜ _correct_ ➜ _expand_ |
| 3 | **Ingest Module** | Walk directory, hash files; emit `DocBlob` |
| 4 | **Parser/Chunker** | Extract text, apply OCR to scanned PDF pages, chunk at headings |
| 5 | **Glance Node** | Score each doc using BM25 **plus** vector top‑K aggregation (see §6.1) |
| 6 | **Digest Node** | Summarise kept chunks ≤ 120 tokens, attach citation |
| 7 | **Distiller (Pass 1)** | Keep/drop chunks until ≤ budget × 1.2 (critical never dropped) |
| 8 | **Distiller (Pass 2)** | LLM compress remaining chunks adaptively (≥ 50 % of original) |
| 9 | **Writer** | Assemble three Markdown files |
|10 | **Cache Layer** | SQLite keyed by text + query |
|11 | **Benchmark** | `make benchmark` prints wall‑clock & node p99 latency |
|12 | **CLI** | `summarise --config cfg.yml --goal "Explain LLVM IR"` |

---

## 5 · Non‑Functional Requirements  

* **Python 3.11+ only**  
* **Concurrency**  
  * Event‑loop: all network LLM calls (`asyncio`, semaphore)  
  * CPU parse/OCR: `ProcessPoolExecutor` (8 workers default)  
* **Retries**: max 3 attempts, exponential back‑off (1 s, 2 s, 4 s) on `LLMError`, HTTP 5xx, `TimeoutError`  
* **Logging**: JSONL per node with duration, tokens, cache‑hit, retry count  
* **Extensibility**: pluggable LLM providers via `LLMRouter` registry  
* **Packaging**: wheels must build on x86‑64 & ARM macOS  

---

## 6 · Algorithmic Detail  

### 6.1 Glance Scoring  

```
sims  = cosine(Q, S_i)  # section vectors
top_k = sorted(sims, desc)[:K]
doc_vec = α * max(top_k) + (1‑α) * mean(top_k)
score  = w_bm25 * bm25(Q, D) + w_vec * doc_vec
```

Default: `K=5`, `α=0.5`, `w_bm25=0.7`, `w_vec=0.3`.

### 6.2 QueryFix Prompts  

1. **Normalize** – “Rewrite the query in formal English; remove slang.”  
2. **Correct** – “Fix misspellings, malformed boolean ops.”  
3. **Expand** – “Suggest up to five synonyms/domain terms.”

Each stage optional (`true`/`false`).

### 6.3 Two‑Pass Distiller  

| Pass | Action | Guard |
|------|--------|-------|
| 1 | Sort by Glance score; keep critical always; drop tail until tokens ≤ budget×1.2 | — |
| 2 | For each remaining chunk, compress to `target = clamp(tokens * budget / current_total, min = 50 %)` | Compression floor 50 % |

If still over budget, hard‑truncate last chunk (rare).

---

## 7 · User Stories  

1. **Developer** runs one command, receives three context files.  
2. **Reviewer** can click every sentence back to file, page, and line/anchor.  
3. **Ops Engineer** tweaks token limits in YAML; no code changes.

---

## 8 · Acceptance Criteria  

* Coverage metrics meet targets on demo corpus (`tests/corpus_demo`).  
* Medium and Small files respect token budgets (±10 %).  
* All critical citations appear in outputs.  
* `pytest -q` passes locally.  
* `make benchmark` completes and prints summary (no hard SLA).  

---

## 9 · Implementation Task List  

| ID | Title | Tags | Criteria |
|----|-------|------|----------|
| **EPIC‑1** | Project setup (`uv`, `ruff`, `mypy`, `pytest`) | `#infra` |
| **EPIC‑2** | Core data classes (`DocBlob`, `Chunk`) | `#core` | hash equality tests |
| **EPIC‑3** | Config Loader | `#core` | invalid YAML raises |
| **EPIC‑4** | Ingest + Parser + OCR | `#core` | fixtures parsed |
| **EPIC‑5** | **QueryFix Node** | `#core` | unit test: miss‑spelled query fixed |
| **EPIC‑6** | Glance Node w/ BM25 + VecTopK | `#core` | coverage recall = 1.00 on corpus |
| **EPIC‑7** | Digest Node | `#core` | tokens ≤ 120 |
| **EPIC‑8** | Cache Layer | `#core` | second run cache hit |
| **EPIC‑9** | Distiller Pass1/Pass2 | `#core` | budgets met, critical kept |
| **EPIC‑10** | Writer | `#core` | files sizes correct |
| **EPIC‑11** | CLI & Progress Bar | `#core` | demo run OK |
| **EPIC‑12** | Benchmark Script | `#core` | timing report printed |
| **EPIC‑13** | Testing & Fixtures | `#test` | coverage ≥ 90 % |
| **EPIC‑14** | Documentation | `#docs` | contributor quick‑start |

---

## 10 · Testing Guidelines  

* `pytest‑asyncio` (auto mode) for async nodes  
* Monkey‑patch `LLMRouter.run` to static responses  
* Fuzz HTML/PDF inputs with Hypothesis  
* Property tests:  
  * Glance Recall/Precision metrics  
  * Distiller token budget  
* Coverage target ≥ 90 %.

---

## 11 · YAML Config Reference (excerpt)

```yaml
large_limit: 32000
small_limit: 8000

query_pipeline:
  normalize: true
  correct:   true
  expand:    true

glance:
  bm25_weight: 0.7
  vec_weight: 0.3
  vec_top_k: 5
  vec_alpha: 0.5
  embed_model: "sentence-transformers/all-MiniLM-L6-v2"

distiller:
  compression_floor: 0.5     # min 50 % of original
  critical_tag: "priority=1"

retries:
  max_attempts: 3
  backoff: exponential
```

---

## 12 · Demo Corpus & Coverage Evaluation  

*Folder*: `tests/corpus_demo/`  
*Files*: 10–15 small docs (PDF, HTML, MD) plus `relevance.yml` critical‑section map.  
Automated test asserts Recall/Precision goals.

---

## 13 · Citation Format (universal)

```
[§{file_sha256}:{media}:{start}:{end}]

media:
  P → PDF page number
  L → plain‑text line range
  H → HTML heading id
```

---

## 14 · Concurrency Model  

| Layer | Owner | Mechanism |
|-------|-------|-----------|
| LLM calls | LangGraph event loop | `asyncio`, bounded semaphore |
| CPU parse/OCR | Parse node | `ProcessPoolExecutor` (8) |
| Misc I/O | sync | — |

---

The document above merges all agreed changes and is ready for distribution.
