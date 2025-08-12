# Annotation Tool Workflow

## How It Works

The annotation tool shows **one chunk at a time for annotation**, with surrounding chunks for context.

### Visual Layout (Sliding Window)

```
⬅️ [PREVIOUS CHUNK] ← context for flow
📍 [CURRENT CHUNK] ← THIS IS WHAT YOU ANNOTATE (384 tokens)
➡️ [NEXT CHUNK] ← context for continuation

👍 Relevant    👎 Not Relevant  ← buttons for CURRENT CHUNK only
```

Note: Previous/Next chunks only show when they exist (not shown for first/last chunks).

### Step by Step

1. **Read the query** at the top
2. **Find the green highlighted chunk** (marked "📍 ANNOTATING THIS CHUNK")
3. **Read that chunk in context** - use the surrounding chunks to understand the full meaning
4. **Decide**: Is the highlighted chunk relevant to answering the query?
5. **Click** 👍 Relevant or 👎 Not Relevant 
6. **Next chunk loads automatically** - repeat until all chunks are annotated

### Key Points

- ✅ **One annotation per chunk** - you'll go through all 6 chunks one by one
- ✅ **Sliding window context** - previous and next chunks show document flow
- ✅ **Larger chunks** - 384 tokens (~1,500 chars) provide substantial content
- ✅ **Green highlighting** - makes it crystal clear which chunk you're judging
- ✅ **Progress tracking** - see how many chunks left per query

### Example Decision Process

**Query**: "What is provenance in C memory model?"

**Chunk to annotate**: "Each valid pointer holds an ID of the corresponding storage instance an address..."

**Context chunks**: Show discussion of storage instances, pointer tracking, etc.

**Decision**: 👍 Relevant (this chunk explains how provenance works)

## Why This Design?

- **Context matters**: A chunk might seem irrelevant in isolation but relevant when you see the full discussion
- **One decision at a time**: Prevents decision fatigue and ensures focused annotation
- **Consistent evaluation**: Each chunk gets equal attention and consideration

The goal is quality annotations that accurately reflect whether each chunk helps answer the query!
