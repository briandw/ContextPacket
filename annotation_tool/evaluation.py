"""Evaluation tools for comparing human annotations with MxBai reranker scores."""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score, roc_curve


def load_evaluation_data() -> Tuple[List[Dict], Dict, Dict]:
    """Load chunks, annotations, and scores for evaluation."""
    
    # Load chunks
    chunks = []
    with open("chunks.jsonl", 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    
    # Load annotations
    annotations = {}
    if Path("annotations.json").exists():
        with open("annotations.json", 'r', encoding='utf-8') as f:
            annotations = json.load(f)
    
    # Load scores
    scores = {}
    if Path("../scores.jsonl").exists():
        with open("../scores.jsonl", 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    score_data = json.loads(line)
                    scores[score_data["id"]] = score_data["score"]
    
    return chunks, annotations, scores


def calculate_f1_at_threshold(human_labels: List[int], scores: List[float], threshold: float) -> Dict:
    """Calculate F1 score at a specific threshold."""
    predictions = [1 if score >= threshold else 0 for score in scores]
    
    if len(set(human_labels)) == 1:
        # Only one class present
        if human_labels[0] == 1:
            # Only relevant chunks
            precision = sum(predictions) / len(predictions) if sum(predictions) > 0 else 0
            recall = 1.0
        else:
            # Only non-relevant chunks
            precision = 1.0
            recall = (len(predictions) - sum(predictions)) / len(predictions) if len(predictions) > sum(predictions) else 0
        
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    else:
        precision, recall, f1, _ = precision_recall_fscore_support(
            human_labels, predictions, average='binary', zero_division=0
        )
    
    return {
        "threshold": threshold,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "predictions": predictions
    }


def find_optimal_threshold(human_labels: List[int], scores: List[float]) -> Dict:
    """Find the optimal threshold that maximizes F1 score."""
    if not human_labels or not scores:
        return {"threshold": 0.0, "f1": 0.0, "precision": 0.0, "recall": 0.0}
    
    # Try a range of thresholds
    thresholds = np.percentile(scores, np.arange(0, 101, 5))  # 0%, 5%, 10%, ..., 100%
    thresholds = np.unique(thresholds)  # Remove duplicates
    
    best_result = {"f1": -1}
    
    for threshold in thresholds:
        result = calculate_f1_at_threshold(human_labels, scores, threshold)
        if result["f1"] > best_result["f1"]:
            best_result = result
    
    return best_result


def evaluate_query(query_id: str, chunks: List[Dict], annotations: Dict, scores: Dict) -> Dict:
    """Evaluate a single query's performance."""
    
    if query_id not in annotations:
        return {"error": "No annotations found for this query"}
    
    query_annotations = annotations[query_id]
    
    # Prepare data for evaluation
    chunk_ids = []
    human_labels = []
    mxbai_scores = []
    
    for chunk in chunks:
        chunk_id = chunk["id"]
        if chunk_id in query_annotations and chunk_id in scores:
            # Only evaluate chunks that are both annotated and scored
            relevance = query_annotations[chunk_id]["relevance"]
            if relevance != -1:  # Skip skipped chunks
                chunk_ids.append(chunk_id)
                human_labels.append(relevance)
                mxbai_scores.append(scores[chunk_id])
    
    if not human_labels:
        return {"error": "No valid annotations found for evaluation"}
    
    # Calculate statistics
    total_annotated = len(human_labels)
    relevant_count = sum(human_labels)
    relevance_rate = relevant_count / total_annotated
    
    # Find optimal threshold
    optimal_result = find_optimal_threshold(human_labels, mxbai_scores)
    
    # Calculate AUC if we have both classes
    auc_score = None
    if len(set(human_labels)) > 1:
        try:
            auc_score = roc_auc_score(human_labels, mxbai_scores)
        except Exception:
            auc_score = None
    
    return {
        "query_id": query_id,
        "total_chunks": len(chunks),
        "annotated_chunks": total_annotated,
        "relevant_chunks": relevant_count,
        "relevance_rate": relevance_rate,
        "optimal_threshold": optimal_result["threshold"],
        "optimal_f1": optimal_result["f1"],
        "optimal_precision": optimal_result["precision"],
        "optimal_recall": optimal_result["recall"],
        "auc_score": auc_score,
        "score_stats": {
            "min": float(min(mxbai_scores)),
            "max": float(max(mxbai_scores)),
            "mean": float(np.mean(mxbai_scores)),
            "std": float(np.std(mxbai_scores))
        }
    }


def run_full_evaluation() -> Dict:
    """Run evaluation across all queries."""
    chunks, annotations, scores = load_evaluation_data()
    
    results = {}
    overall_stats = {
        "total_queries": 0,
        "queries_with_data": 0,
        "average_f1": 0,
        "average_auc": 0,
    }
    
    from queries import TEST_QUERIES
    
    f1_scores = []
    auc_scores = []
    
    for query_info in TEST_QUERIES:
        query_id = query_info["id"]
        result = evaluate_query(query_id, chunks, annotations, scores)
        results[query_id] = result
        results[query_id]["query_text"] = query_info["query"]
        results[query_id]["query_type"] = query_info["type"]
        
        overall_stats["total_queries"] += 1
        
        if "error" not in result:
            overall_stats["queries_with_data"] += 1
            f1_scores.append(result["optimal_f1"])
            if result["auc_score"] is not None:
                auc_scores.append(result["auc_score"])
    
    # Calculate averages
    if f1_scores:
        overall_stats["average_f1"] = float(np.mean(f1_scores))
    if auc_scores:
        overall_stats["average_auc"] = float(np.mean(auc_scores))
    
    return {
        "overall_stats": overall_stats,
        "query_results": results,
        "evaluation_timestamp": str(Path("annotations.json").stat().st_mtime if Path("annotations.json").exists() else "")
    }


def generate_evaluation_report() -> str:
    """Generate a human-readable evaluation report."""
    evaluation = run_full_evaluation()
    
    report = []
    report.append("# MxBai Reranker Evaluation Report\n")
    
    # Overall stats
    stats = evaluation["overall_stats"]
    report.append("## Overall Statistics")
    report.append(f"- Total queries: {stats['total_queries']}")
    report.append(f"- Queries with evaluation data: {stats['queries_with_data']}")
    report.append(f"- Average F1 score: {stats['average_f1']:.3f}")
    if stats['average_auc'] > 0:
        report.append(f"- Average AUC score: {stats['average_auc']:.3f}")
    report.append("")
    
    # Per-query results
    report.append("## Per-Query Results")
    
    for query_id, result in evaluation["query_results"].items():
        if "error" in result:
            report.append(f"### {result.get('query_text', query_id)}")
            report.append(f"**Error**: {result['error']}")
            report.append("")
            continue
        
        report.append(f"### {result['query_text']}")
        report.append(f"**Type**: {result['query_type']}")
        report.append(f"**Chunks annotated**: {result['annotated_chunks']}/{result['total_chunks']}")
        report.append(f"**Relevance rate**: {result['relevance_rate']:.1%}")
        report.append(f"**Optimal F1**: {result['optimal_f1']:.3f} (threshold: {result['optimal_threshold']:.2f})")
        report.append(f"**Precision**: {result['optimal_precision']:.3f}")
        report.append(f"**Recall**: {result['optimal_recall']:.3f}")
        if result['auc_score']:
            report.append(f"**AUC**: {result['auc_score']:.3f}")
        report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    print("Running evaluation...")
    report = generate_evaluation_report()
    
    with open("evaluation_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Evaluation complete! Report saved to evaluation_report.md")
    print("\n" + report)
