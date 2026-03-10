# HNSW: What It Is and Why FAISS Defaults to It

## The core problem HNSW solves

When you have a large collection of high-dimensional vectors and need to find the nearest neighbors of a query vector, the brute-force approach — compute distance to every vector, return the closest — is exact but O(n) per query. At 10M vectors, that's too slow for most real-time applications.

The alternative is Approximate Nearest Neighbor (ANN) search: trade a small amount of accuracy for a large gain in speed. HNSW is currently the dominant ANN algorithm for in-memory search.

## What HNSW actually is

HNSW stands for **Hierarchical Navigable Small World**. It's a graph-based index structure. The key ideas:

**Navigable Small World (NSW)** graphs connect each vector node to a fixed number of neighbors (`M` neighbors per node). The "small world" property means you can reach any node from any other node in a logarithmic number of hops. Search works by greedy traversal: start at an entry point, move to whichever neighbor is closest to the query, repeat until you stop improving.

**The hierarchical part** adds multiple layers on top of NSW. The bottom layer (layer 0) contains all vectors. Each successive layer contains a random subset — roughly 1/e of the layer below. The top layer has very few nodes, acting as a coarse "highway" network.

Search works top-down:
1. Enter at the top layer with a single entry point
2. Greedily navigate to the local minimum at that layer
3. Drop down to the next layer, using the best node found as the new entry point
4. Repeat until you reach layer 0
5. At layer 0, expand the search using `ef` candidate neighbors (the `efSearch` parameter), return the top-k

This is analogous to zooming in on a map: coarse navigation first, then fine-grained local search.

## Key parameters you'll encounter in FAISS

When you use `faiss.IndexHNSWFlat` or similar, you control:

- **M** (connections per node): Controls index quality and memory. Higher M = more edges = better recall but more RAM and slower build time. Typical range: 16–64. 32 is a common default.
- **efConstruction**: How many candidates are explored during index build. Higher = better quality graph = slower build. Set this once at index creation time. Typical: 40–200.
- **efSearch** (`hnsw.efSearch` in FAISS): How many candidates are explored during query time. This is the primary recall/speed knob you tune at runtime. Higher = better recall, slower queries.

```python
import faiss

d = 128  # vector dimension
M = 32
index = faiss.IndexHNSWFlat(d, M)
index.hnsw.efConstruction = 200  # set before adding vectors
index.add(vectors)

index.hnsw.efSearch = 64  # tune this per query latency budget
D, I = index.search(query, k=10)
```

## Why HNSW is preferred over alternatives

FAISS offers several index types. The main contenders:

| Index | Method | Recall | Speed | Memory | Build time |
|---|---|---|---|---|---|
| `IndexFlatL2` | Brute force | 100% | Slow at scale | Low | Instant |
| `IndexIVFFlat` | Inverted file (clustering) | High (tunable) | Fast | Moderate | Moderate |
| `IndexHNSWFlat` | Graph traversal | High (tunable) | Fast | Higher | Slower |
| `IndexIVFPQ` | IVF + product quantization | Lower | Very fast | Very low | Slow |

HNSW's advantages over IVF-based indexes:
- **No training step**: IVF requires a k-means clustering pass over your data before you can add vectors. HNSW builds incrementally — you can add vectors one at a time.
- **Better recall at the same speed**: On most benchmarks (ann-benchmarks.com), HNSW achieves higher recall for equivalent query latency.
- **Simpler tuning**: IVF has `nlist` (number of clusters) and `nprobe` (clusters to search) that interact in non-obvious ways. HNSW's `efSearch` is a single intuitive dial.
- **No catastrophic recall cliff**: With IVF, if a vector's nearest neighbors land in a cluster you didn't probe, you miss them entirely. HNSW's graph structure is more robust to this.

HNSW's disadvantages:
- **Memory**: Storing the graph edges costs RAM. At M=32 and d=128 float32 vectors, the graph overhead is significant compared to the raw vectors.
- **No GPU support in FAISS**: FAISS's GPU indexes use IVF-based structures. If you need GPU-accelerated search, HNSW is not an option within FAISS.
- **Slower builds**: Building a high-quality HNSW graph is slower than IVF training + insertion, especially at hundreds of millions of vectors.

## When to use what

- **< 100K vectors**: `IndexFlatL2` (exact search, fast enough, no approximation error)
- **100K–50M vectors, CPU, care about recall**: `IndexHNSWFlat`
- **Massive scale or GPU**: IVF-based (`IndexIVFFlat`, `IndexIVFPQ`)
- **Memory-constrained**: Add PQ compression — `IndexHNSWPQ` combines HNSW graph with product quantization

## The practical upshot

HNSW is preferred in FAISS for workloads that fit in memory, run on CPU, and need strong recall without a training step. Its recall-speed tradeoff curve is better than IVF in most published benchmarks, and the single `efSearch` parameter makes it straightforward to tune against a latency SLA. The cost is memory and build time, both of which are acceptable for most production vector search applications at the scale where FAISS is typically used.
