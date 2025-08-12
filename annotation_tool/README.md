# Chunk Relevance Annotation Tool

This tool provides a web interface for manually annotating chunk relevance against various queries to evaluate the MxBai reranker performance.

## Features

- **Query-based annotation**: Test multiple query types (technical definitions, conceptual understanding, examples)
- **Context display**: Shows chunks in context with surrounding chunks for better judgment
- **Binary relevance**: Simple thumbs up/down annotation
- **Progress tracking**: Shows completion status for each query
- **Export/evaluation**: Generate F1 scores and performance metrics

## Setup

1. **Generate chunks**: First create annotation-sized chunks:
   ```bash
   # From the main ContextPacket directory
   source .venv/bin/activate
   contextpacket --config annotation_config.yml --corpus test_corpus_small --goal "test query" --dump-chunks --dump-scores
   ```

2. **Start annotation tool**:
   ```bash
   cd annotation_tool
   python app.py
   ```

3. **Open browser**: Navigate to `http://localhost:5001`

## Usage

### Annotation Workflow

1. **Select Query**: Choose from 7 predefined queries covering different aspects of the provenance talk
2. **Review Context**: Each chunk is shown with 2 preceding and 2 following chunks for context  
3. **Annotate**: Mark each chunk as relevant 👍 or not relevant 👎 to the query
4. **Progress**: Track completion across all chunks for each query

### Query Types

- **Technical Definition**: "What is provenance in C memory model?"
- **Conceptual**: "How does provenance prevent aliasing violations?"
- **Examples**: "Show examples of pointer exposure and synthesis"

### Evaluation

Once annotation is complete:

```bash
cd annotation_tool
python evaluation.py
```

This generates:
- **F1 scores** at optimal thresholds
- **Precision/Recall** metrics  
- **AUC scores** for ranking quality
- **evaluation_report.md** with detailed results

## Files

- `app.py`: FastHTML web application
- `queries.py`: Test query definitions
- `evaluation.py`: Performance evaluation tools
- `annotations.json`: Stored annotations (created after first use)
- `chunks.jsonl`: Input chunks (copied from main directory)
- `evaluation_report.md`: Generated evaluation report

## Data Format

### Annotations
```json
{
  "q1": {
    "chunk_id_1": {"relevance": 1, "timestamp": "2025-01-12 10:30:00"},
    "chunk_id_2": {"relevance": 0, "timestamp": "2025-01-12 10:31:00"}
  }
}
```

### Evaluation Output
- **F1 Score**: Harmonic mean of precision and recall
- **Optimal Threshold**: MxBai score threshold that maximizes F1
- **AUC**: Area under ROC curve for ranking quality
- **Relevance Rate**: Proportion of chunks marked relevant

## Expected Workflow

1. **Annotate 2-3 queries** (focus on different types)
2. **Run evaluation** to get baseline F1 scores  
3. **Analyze results** - which query types work best?
4. **Iterate** on chunk size or query formulation if needed

The goal is to achieve **F1 ≥ 0.85** as specified in the PRD.
