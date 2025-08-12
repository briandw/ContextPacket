"""Test queries for provenance talk annotation."""

# Mix of technical definitions, conceptual understanding, and examples
TEST_QUERIES = [
    {
        "id": "q1", 
        "query": "What is provenance in C memory model?",
        "type": "technical_definition"
    },
    {
        "id": "q2",
        "query": "How does provenance prevent aliasing violations?", 
        "type": "conceptual"
    },
    {
        "id": "q3",
        "query": "What are storage instances and how do they relate to provenance?",
        "type": "technical_definition" 
    },
    {
        "id": "q4",
        "query": "Show examples of pointer exposure and synthesis",
        "type": "examples"
    },
    {
        "id": "q5", 
        "query": "What problems does the C memory model have with out-of-bounds access?",
        "type": "conceptual"
    },
    {
        "id": "q6",
        "query": "How does provenance tracking work through pointer operations?",
        "type": "technical_definition"
    },
    {
        "id": "q7",
        "query": "What is the relationship between provenance and undefined behavior?",
        "type": "conceptual"
    }
]
