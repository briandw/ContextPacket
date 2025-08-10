Summarisation Pipeline – Database Schema and Persistence Layer

Last updated: 2025-06-29

⸻

Overview

This document defines the SQLite schema and persistence logic used to support document processing, chunk storage, vector scoring, and multi-query support within the summarisation pipeline. It is designed for durability, queryability, and efficient update support.

1 · Database Schema

1.1 Table: document

Column	Type	Notes
doc_id	INTEGER	PRIMARY KEY
path	TEXT	Relative or absolute filepath
sha256	TEXT	SHA-256 of file content
mime	TEXT	e.g., application/pdf
created_at	TIMESTAMP	Default: CURRENT_TIMESTAMP

Indexes:
	•	CREATE UNIQUE INDEX uq_document_sha ON document(sha256);

⸻

1.2 Table: chunk

Column	Type	Notes
chunk_id	INTEGER	PRIMARY KEY
doc_id	INTEGER	FK to document.doc_id
idx	INTEGER	0-based index within document
text	TEXT	Raw chunk text
citation	TEXT	Format: [§hash:P3:10:20]
embedding	BLOB	384 × float32 (≈1.5KB)
token_count	INTEGER	Token count via tiktoken

FTS5 Table:
	•	CREATE VIRTUAL TABLE chunk_fts USING fts5(text, content='chunk', content_rowid='chunk_id', tokenize='unicode61');

Indexes:
	•	CREATE INDEX idx_chunk_doc ON chunk(doc_id);

⸻

1.3 Table: query

Column	Type	Notes
query_id	INTEGER	PRIMARY KEY
goal	TEXT	Descriptive label or task
original	TEXT	Raw user input
normalized	TEXT	Lowercased, cleaned version
corrected	TEXT	Spell/grammar fixed
expanded	TEXT	Synonyms or enriched expression
created_at	TIMESTAMP	Default: CURRENT_TIMESTAMP

Indexes:
	•	CREATE UNIQUE INDEX uq_query_original ON query(original);

⸻

1.4 Table: query_chunk (Many-to-Many)

Column	Type	Notes
query_id	INTEGER	FK to query
chunk_id	INTEGER	FK to chunk
bm25_score	REAL	FTS5-based lexical similarity
vec_score	REAL	Cosine similarity to query embedding
combined_score	REAL	Weighted: α * max + (1-α) * mean top-K
PRIMARY KEY	(query_id, chunk_id)	

Indexes:
	•	CREATE INDEX idx_qc_score ON query_chunk(query_id, combined_score DESC);

⸻

2 · Persistence Layer (Python Interface)

2.1 Models

@dataclass(frozen=True)
class Document:
    doc_id: int
    path: str
    sha256: str
    mime: str
    created_at: datetime

@dataclass(frozen=True)
class Chunk:
    chunk_id: int
    doc_id: int
    idx: int
    text: str
    citation: str
    embedding: bytes  # float32 array serialized
    token_count: int

@dataclass(frozen=True)
class Query:
    query_id: int
    original: str
    normalized: str
    corrected: str
    expanded: str
    created_at: datetime

@dataclass(frozen=True)
class QueryChunk:
    query_id: int
    chunk_id: int
    bm25_score: float
    vec_score: float
    combined_score: float


⸻

2.2 Access Layer (Functions)

def insert_document(db, path: str, sha256: str, mime: str) -> int: ...
def insert_chunk(db, doc_id: int, idx: int, text: str, citation: str, embedding: bytes, token_count: int) -> int: ...
def get_or_create_query(db, prompt: str) -> Query: ...
def update_query_expansion(db, query_id: int, normalized: str, corrected: str, expanded: str): ...
def insert_query_chunk_scores(db, query_id: int, scores: list[QueryChunk]): ...
def get_top_chunks_for_query(db, query_id: int, limit: int) -> list[Chunk]: ...


⸻

2.3 Initialization

def init_db(path: str):
    db = sqlite3.connect(path)
    db.execute("PRAGMA journal_mode=WAL;")
    db.executescript(open("schema.sql").read())
    return db


⸻

3 · Notes
	•	Embeddings are stored as serialized float32 arrays using .tobytes().
	•	FTS5 enables fast BM25 ranking without loading full chunk text.
	•	Expansion reuse: identical prompts hit uq_query_original, skipping LLM calls.
	•	Score reuse: vector sim only recomputed if embedding model hash changes.

