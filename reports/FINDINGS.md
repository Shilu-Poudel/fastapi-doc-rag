# Retrieval Findings Report

This report compares chunking strategies, embedding models, and vector-store
similarity algorithms on retrieval accuracy and latency. All numbers are
produced by [benchmarks/run_benchmark.py](../benchmarks/run_benchmark.py) against
a local Qdrant instance.

## Methodology

- **Corpus**: 41 machine-learning facts across several topics, including
  deliberately confusable pairs - precision vs recall, L1 vs L2 regularization,
  vanishing vs exploding gradients, cosine vs dot vs Euclidean
  ([benchmarks/corpus.txt](../benchmarks/corpus.txt)).
- **Query set**: 24 questions, each paraphrased so it does not lexically match
  the source sentence. Retrieval therefore has to match meaning, and has to pick
  the correct fact over its confusable neighbours.
- **Metrics**:
  - `hit@1` - the correct fact is the single top result.
  - `hit@3` - the correct fact is within the top 3 results.
  - `mrr` - mean reciprocal rank; 1.0 if the answer is always rank 1, 0.5 if
    typically rank 2, etc. A finer signal than hit-rate.
- **Latency**: query embedding (`embed_ms`) and Qdrant search (`search_ms`),
  averaged over the query set. Latency is indicative on a CPU/WSL2 machine and
  varies run to run; accuracy metrics are exact and reproducible.
- **Fixed settings**: chunk size 250 chars, overlap 40, search depth 10.

## Part 1 - Chunking strategy x Embedding model

Distance fixed to cosine.

| Embedding model    | Chunking  | Chunks | hit@1 | hit@3 | MRR  | embed_ms | search_ms |
|--------------------|-----------|:------:|:-----:|:-----:|:----:|:--------:|:---------:|
| all-MiniLM-L6-v2   | recursive | 23     | 0.83  | 1.00  | 0.92 | ~10      | ~4        |
| all-MiniLM-L6-v2   | sentence  | 21     | 0.83  | 1.00  | 0.92 | ~7       | ~3        |
| all-MiniLM-L6-v2   | fixed     | 18     | 0.54  | 0.79  | 0.65 | ~6       | ~3        |
| all-mpnet-base-v2  | recursive | 23     | 0.83  | 1.00  | 0.92 | ~15      | ~4        |
| all-mpnet-base-v2  | sentence  | 21     | 0.79  | 1.00  | 0.89 | ~12      | ~4        |
| all-mpnet-base-v2  | fixed     | 18     | 0.54  | 0.83  | 0.67 | ~13      | ~4        |

### Observations

- **Fixed chunking is clearly the worst**, on every metric: hit@1 drops from
  0.83 to 0.54 and MRR from 0.92 to 0.65. Blind character windows cut a fact in
  half, so the answer is spread across two chunks and neither ranks first.
- **Recursive and sentence chunking tie at the top** (hit@1 0.83, hit@3 1.00,
  MRR 0.92). Recursive is the better default because it also handles documents
  without clean sentence punctuation (tables, code, lists), where sentence
  splitting breaks down.
- **The larger embedding model gives no accuracy gain here.**
  `all-mpnet-base-v2` (768-dim) matches `all-MiniLM-L6-v2` (384-dim) on accuracy
  - and is actually a touch worse with sentence chunking - while costing roughly
  **1.5x the embedding latency** and **2x the storage**. On this corpus the
  smaller model is the better trade-off.

### Recommendation

Use **recursive chunking + all-MiniLM-L6-v2**: top accuracy, lowest latency and
storage. This is the configuration shipped in the application. Reserve
`all-mpnet-base-v2` for harder corpora where its extra capacity actually pays off.

## Part 2 - Similarity search algorithm

Fixed to all-MiniLM-L6-v2 + recursive chunking. Embeddings here are
**un-normalized** so that vector magnitude has a chance to affect the ranking.

| Distance  | hit@1 | hit@3 | MRR  | embed_ms | search_ms |
|-----------|:-----:|:-----:|:----:|:--------:|:---------:|
| cosine    | 0.83  | 1.00  | 0.92 | ~6       | ~3        |
| dot       | 0.83  | 1.00  | 0.92 | ~7       | ~3        |
| euclid    | 0.83  | 1.00  | 0.92 | ~6       | ~3        |

### Observations

- **All three distances are identical on accuracy**, even on the harder corpus
  with confusable facts. The reason is mathematical:
  - With L2-normalized embeddings (the production default), cosine, dot and
    Euclidean are monotonically equivalent and produce the exact same ranking
    (`dot = cosine` and `euclid^2 = 2 - 2*cosine`).
  - `all-MiniLM-L6-v2` vectors already have near-uniform magnitude, so even
    un-normalized the magnitude-sensitive dot product does not diverge from
    cosine.
- **The real differentiators are score semantics and compute.** Cosine gives
  bounded, interpretable scores in [-1, 1]; dot product skips normalization and
  is marginally cheaper; Euclidean offers no benefit and is the most sensitive to
  magnitude.

### Recommendation

Use **cosine** (the application default): identical accuracy to dot and
Euclidean, with interpretable bounded scores. **Dot product** is an equally
accurate, slightly cheaper alternative when vectors are pre-normalized.
**Euclidean** is not recommended here - same accuracy, no interpretability gain.

### When would they differ?

The three metrics are equivalent here only because the embeddings are
(near) unit length. They diverge when vectors are **not normalized**, so that
magnitude carries meaning - for example with raw TF-IDF or count vectors, where a
longer document has a larger magnitude. In that case the dot product is biased
toward high-magnitude vectors (longer documents), while cosine cancels magnitude
out and compares direction only. This is exactly why cosine is the standard
default for text retrieval. The sentence-transformer embeddings used here are
already near unit length, so that bias does not appear and the metrics coincide.

## Reproducing

```bash
docker compose up -d            # Qdrant must be running
.venv/bin/python -m benchmarks.run_benchmark
```
