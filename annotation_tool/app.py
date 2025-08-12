"""FastHTML annotation tool for chunk relevance evaluation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fasthtml.common import *
from queries import TEST_QUERIES

# Load chunks data  
CHUNKS_FILE = Path("chunks.jsonl") 
ANNOTATIONS_FILE = Path("annotations.json")

def load_chunks() -> List[Dict]:
    """Load chunks from JSONL file."""
    chunks = []
    if CHUNKS_FILE.exists():
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))
    return chunks

def load_annotations() -> Dict:
    """Load existing annotations."""
    if ANNOTATIONS_FILE.exists():
        with open(ANNOTATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_annotations(annotations: Dict) -> None:
    """Save annotations to JSON file."""
    with open(ANNOTATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(annotations, f, indent=2)

# Initialize FastHTML app
app, rt = fast_app()

# Global state
chunks_data = load_chunks()
annotations = load_annotations()

@rt("/")
def get():
    """Main page - query selection."""
    query_buttons = []
    for query_info in TEST_QUERIES:
        # Count completed annotations
        query_id = query_info["id"]
        completed = len(annotations.get(query_id, {}))
        total = len(chunks_data)
        
        button = A(
            Div(
                H3(query_info["query"]),
                P(f"Type: {query_info['type']}", cls="text-muted"),
                P(f"Progress: {completed}/{total} chunks annotated", 
                  cls="text-success" if completed == total else "text-warning"),
                cls="card-body"
            ),
            href=f"/annotate/{query_id}",
            cls="card mb-3 text-decoration-none"
        )
        query_buttons.append(button)
    
    return Titled("Chunk Relevance Annotation Tool",
        Container(
            H1("Select Query to Annotate", cls="mb-4"),
            P(f"Total chunks: {len(chunks_data)}", cls="text-muted mb-4"),
            Div(*query_buttons),
            A("View Results", href="/results", cls="btn btn-primary mt-4")
        )
    )

@rt("/annotate/{query_id}")
def get(query_id: str):
    """Annotation interface for a specific query."""
    # Find query info
    query_info = next((q for q in TEST_QUERIES if q["id"] == query_id), None)
    if not query_info:
        return "Query not found", 404
    
    # Get current annotations for this query
    query_annotations = annotations.get(query_id, {})
    
    # Find next unannotated chunk
    current_chunk_idx = 0
    for i, chunk in enumerate(chunks_data):
        if chunk["id"] not in query_annotations:
            current_chunk_idx = i
            break
    else:
        # All chunks annotated
        return Titled("Annotation Complete!",
            Container(
                H1("All chunks annotated for this query!"),
                A("Back to queries", href="/", cls="btn btn-primary"),
                A("View results", href="/results", cls="btn btn-secondary ms-2")
            )
        )
    
    current_chunk = chunks_data[current_chunk_idx]
    
    # Get sliding window context (previous, current, next)
    context_chunks = []
    
    # Add previous chunk if exists
    if current_chunk_idx > 0:
        context_chunks.append({
            "chunk": chunks_data[current_chunk_idx - 1],
            "is_current": False,
            "position": "previous"
        })
    
    # Add current chunk (always present)
    context_chunks.append({
        "chunk": chunks_data[current_chunk_idx],
        "is_current": True,
        "position": "current"
    })
    
    # Add next chunk if exists
    if current_chunk_idx < len(chunks_data) - 1:
        context_chunks.append({
            "chunk": chunks_data[current_chunk_idx + 1],
            "is_current": False,
            "position": "next"
        })
    
    progress = len(query_annotations)
    total = len(chunks_data)
    
    return Titled(f"Annotating: {query_info['query'][:50]}...",
        Container(
            # Header
            Div(
                H2("Query", cls="text-primary"),
                P(query_info["query"], cls="fs-5 fw-bold mb-3"),
                P(f"Type: {query_info['type']}", cls="text-muted"),
                cls="mb-4"
            ),
            
            # Progress and instructions
            Div(
                f"Progress: {progress}/{total} chunks",
                Progress(value=progress, max=total, cls="mt-2"),
                P("📍 You annotate ONE chunk at a time. The chunk to annotate is highlighted in green below.", 
                  cls="text-success mt-2 fw-bold"),
                cls="mb-4"
            ),
            
            # Sliding window: Previous → Current → Next
            H3("Sliding Window Context", cls="mb-3"),
            P("⬅️ Previous | 📍 Current (Annotate This) | ➡️ Next", cls="text-muted mb-3"),
            
            *[
                Card(
                    Div(
                        # Header with position indicator
                        Div(
                            H4(
                                "📍 ANNOTATING THIS CHUNK" if ctx['is_current'] 
                                else f"⬅️ Previous: Chunk {ctx['chunk']['order']}" if ctx['position'] == 'previous'
                                else f"➡️ Next: Chunk {ctx['chunk']['order']}",
                                cls="text-white bg-success p-2 rounded mb-2" if ctx['is_current'] 
                                else "text-primary bg-light p-2 rounded mb-2"
                            ),
                            P(f"Chunk {ctx['chunk']['order']}: {ctx['chunk']['id']}", 
                              cls="fw-bold " + ("text-success" if ctx['is_current'] else "text-muted")),
                            cls="mb-2"
                        ),
                        
                        # Chunk text
                        P(ctx['chunk']['text'], 
                          cls="p-3 " + 
                              ("border border-success border-3 bg-light" if ctx['is_current'] 
                               else "bg-light border")),
                        
                        # Metadata  
                        P(f"Tokens: {ctx['chunk']['tokens']} | Citation: {ctx['chunk']['citation']}", 
                          cls="small text-muted"),
                    ),
                    cls="mb-4 " + ("border-success shadow-lg" if ctx['is_current'] else "border-light")
                ) for ctx in context_chunks
            ],
            
            # Annotation buttons
            H3("📍 Is the highlighted chunk above relevant to the query?", cls="mb-3 text-success"),
            Form(
                Input(type="hidden", name="query_id", value=query_id),
                Input(type="hidden", name="chunk_id", value=current_chunk["id"]),
                Button("👍 Relevant", type="submit", name="relevance", value="1", 
                       cls="btn btn-success btn-lg me-3"),
                Button("👎 Not Relevant", type="submit", name="relevance", value="0", 
                       cls="btn btn-danger btn-lg"),
                hx_post="/annotate_submit",
                hx_target="body",
                cls="mb-4"
            ),
            
            # Navigation
            Div(
                A("← Back to queries", href="/", cls="btn btn-secondary"),
                A("Skip chunk", href=f"/skip/{query_id}/{current_chunk['id']}", 
                  cls="btn btn-warning ms-2"),
                cls="mt-4"
            )
        )
    )

@rt("/annotate_submit", methods=["POST"])
def post(query_id: str, chunk_id: str, relevance: str):
    """Submit annotation."""
    global annotations
    
    if query_id not in annotations:
        annotations[query_id] = {}
    
    annotations[query_id][chunk_id] = {
        "relevance": int(relevance),
        "timestamp": str(datetime.now())
    }
    
    save_annotations(annotations)
    
    # Redirect back to annotation page
    return RedirectResponse(f"/annotate/{query_id}", status_code=303)

@rt("/skip/{query_id}/{chunk_id}")  
def get(query_id: str, chunk_id: str):
    """Skip a chunk (mark as -1)."""
    global annotations
    
    if query_id not in annotations:
        annotations[query_id] = {}
    
    annotations[query_id][chunk_id] = {
        "relevance": -1,  # -1 means skipped
        "timestamp": str(datetime.now())
    }
    
    save_annotations(annotations)
    return RedirectResponse(f"/annotate/{query_id}", status_code=303)

@rt("/results")
def get():
    """View annotation results and statistics."""
    stats = []
    
    for query_info in TEST_QUERIES:
        query_id = query_info["id"]
        query_annotations = annotations.get(query_id, {})
        
        relevant_count = sum(1 for a in query_annotations.values() if a["relevance"] == 1)
        not_relevant_count = sum(1 for a in query_annotations.values() if a["relevance"] == 0)
        skipped_count = sum(1 for a in query_annotations.values() if a["relevance"] == -1)
        total_annotated = len(query_annotations)
        
        stats.append({
            "query": query_info["query"],
            "type": query_info["type"], 
            "relevant": relevant_count,
            "not_relevant": not_relevant_count,
            "skipped": skipped_count,
            "total_annotated": total_annotated,
            "total_chunks": len(chunks_data),
            "completion": f"{total_annotated}/{len(chunks_data)}"
        })
    
    return Titled("Annotation Results",
        Container(
            H1("Annotation Statistics", cls="mb-4"),
            
            Table(
                Thead(
                    Tr(
                        Th("Query"),
                        Th("Type"),
                        Th("Relevant"), 
                        Th("Not Relevant"),
                        Th("Skipped"),
                        Th("Completion")
                    )
                ),
                Tbody(
                    *[Tr(
                        Td(stat["query"][:50] + "..." if len(stat["query"]) > 50 else stat["query"]),
                        Td(stat["type"]),
                        Td(str(stat["relevant"]), cls="text-success"),
                        Td(str(stat["not_relevant"]), cls="text-danger"),
                        Td(str(stat["skipped"]), cls="text-warning"),
                        Td(stat["completion"])
                    ) for stat in stats]
                ),
                cls="table table-striped"
            ),
            
            A("Export Annotations", href="/export", cls="btn btn-primary me-2"),
            A("Back to Queries", href="/", cls="btn btn-secondary"),
            
            cls="mt-4"
        )
    )

@rt("/export")
def get():
    """Export annotations as JSON."""
    export_data = {
        "queries": TEST_QUERIES,
        "chunks": chunks_data,
        "annotations": annotations,
        "export_timestamp": str(datetime.now())
    }
    
    return Response(
        json.dumps(export_data, indent=2),
        headers={"Content-Type": "application/json",
                "Content-Disposition": "attachment; filename=annotations_export.json"}
    )

if __name__ == "__main__":
    serve()
