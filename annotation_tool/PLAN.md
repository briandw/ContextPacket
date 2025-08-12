# Annotation Tool Implementation Plan

## ✅ **COMPLETED**

### 1. Analysis & Query Generation
- **Analyzed provenance talk PDF**: 8,062 chars, 36 provenance mentions, rich technical content
- **Created 7 test queries**: Mix of technical definitions, conceptual understanding, and examples
- **Generated evaluation chunks**: 6 chunks with 384-token size (middle segment from 512-token windows)

### 2. FastHTML Annotation Interface  
- **Multi-query support**: One query at a time with progress tracking
- **Sliding window display**: Shows Previous → Current → Next chunks for context flow
- **Binary annotation**: Simple thumbs up 👍 / thumbs down 👎 interface
- **Larger chunks**: 384 tokens (~1,500 chars) for substantial content decisions
- **Progress tracking**: Completion status across all queries
- **JSON storage**: Lightweight persistence with timestamps
- **Update script**: `update_chunks.py` to regenerate with new configurations

### 3. Evaluation Framework
- **F1 score calculation**: At optimal thresholds for each query
- **AUC analysis**: Ranking quality assessment  
- **Threshold optimization**: Find best MxBai score cutoff
- **Multi-query evaluation**: Compare performance across query types
- **Automated reporting**: Generate markdown evaluation reports

## 🎯 **READY TO USE**

### Quick Start
```bash
# 1. Generate annotation data
source .venv/bin/activate
contextpacket --config annotation_config.yml --corpus test_corpus_small --goal "test" --dump-chunks --dump-scores

# 2. Start annotation tool
cd annotation_tool
python app.py
# Visit: http://localhost:5001

# 3. Run evaluation after annotation
python evaluation.py
```

### Expected Workflow
1. **Annotate 2-3 diverse queries** (start with q1, q2, q4)  
2. **Annotate all 6 chunks per query** - manageable size with substantial content (384 tokens each)
3. **Run evaluation** to get F1 scores vs PRD target of ≥0.85
4. **Analyze query types** - which work best with MxBai?

### Data Output
- **annotations.json**: Human relevance judgments
- **evaluation_report.md**: F1, precision, recall, AUC metrics
- **annotations_export.json**: Complete dataset for further analysis

## 📊 **SUCCESS METRICS**

### Primary Goal (from PRD)
- **F1 ≥ 0.85** on manual spot-check of demo corpus

### Detailed Analysis  
- **Per-query F1 scores**: Which query types work best?
- **Optimal thresholds**: What MxBai score cutoffs maximize F1?
- **AUC scores**: How good is the ranking quality?
- **Relevance rates**: What proportion of chunks are actually relevant?

### Query Coverage
- **q1-q3**: Technical definitions (provenance, storage instances, etc.)
- **q4**: Examples (exposure/synthesis cases)  
- **q5-q7**: Conceptual understanding (problems, tracking, UB)

## 🔧 **TECHNICAL IMPLEMENTATION**

### Architecture
- **FastHTML**: Clean web UI with Bootstrap styling
- **JSON storage**: Simple file-based persistence
- **scikit-learn**: Professional evaluation metrics  
- **Context display**: Chunk ±2 neighbors for informed decisions

### Integration with ContextPacket
- **Uses pipeline output**: chunks.jsonl and scores.jsonl
- **Same chunk IDs**: Direct correlation with MxBai scores  
- **Configurable chunk size**: annotation_config.yml for fine-grained evaluation

### Quality Assurance
- **Binary decisions**: Eliminates annotation ambiguity
- **Context provision**: Surrounding chunks prevent isolated judgments
- **Timestamp tracking**: Audit trail for annotation sessions  
- **Skip functionality**: Handle unclear/ambiguous chunks

## 🚀 **NEXT STEPS**

1. **Start annotating!** Focus on diverse query types
2. **Measure baseline F1** against PRD target of 0.85
3. **Identify patterns** - which chunks/queries work best?
4. **Iterate if needed** - adjust chunk size or query formulation

The annotation tool is production-ready and will provide the ground truth evaluation needed to validate the MxBai reranker performance against human judgment.
