# Contrastive Loss for Sentence Embedding Fine-Tuning

## What it is

Contrastive loss is a training objective that teaches a model to pull similar pairs of inputs closer together in embedding space, and push dissimilar pairs farther apart. That's the whole idea — the model learns by contrast.

When you fine-tune a sentence embedding model with contrastive loss, you're not training the model to predict a label. You're training it to organize sentences geometrically, so that semantically similar sentences end up near each other in the vector space, and semantically different ones end up far apart.

## The setup: pairs

Contrastive loss requires your training data to be structured as pairs, each labeled as either positive (similar) or negative (dissimilar):

- Positive pair: "The dog ran through the park." / "A dog was running outside." → label: 1
- Negative pair: "The dog ran through the park." / "Interest rates rose sharply." → label: 0

The model encodes both sentences independently into embeddings, then the loss function looks at the distance between those embeddings and asks: is that distance consistent with the label?

## The math (conceptually)

The classic formulation (Hadsell et al., 2006):

```
L = (1 - y) * D^2 + y * max(0, margin - D)^2
```

Where:
- `y` = 1 if the pair is similar, 0 if dissimilar
- `D` = distance between the two embeddings (usually Euclidean)
- `margin` = a hyperparameter defining how far apart negatives should be pushed

Breaking this down:
- When `y = 1` (similar): loss = D^2. The model is penalized for any distance — it should be zero.
- When `y = 0` (dissimilar): loss = max(0, margin - D)^2. The model is only penalized if the distance is *less than* the margin. Once they're far enough apart, no further gradient signal.

The margin is important — without it, the model could trivially minimize loss by mapping everything to zero, which would make negatives "far apart" in a degenerate way.

## In the context of sentence-transformers

If you're using the `sentence-transformers` library, `ContrastiveLoss` wraps this cleanly. It takes a model (typically a BERT-based encoder with a pooling layer) and expects pairs with binary labels.

Internally:
1. Each sentence in the pair is passed through the encoder independently.
2. The resulting embeddings are compared (cosine similarity or Euclidean distance, depending on config).
3. The loss is computed and backpropagated through both encoder passes.

The key training signal is relational — the model never sees an absolute "correct" embedding. It only learns from how embeddings relate to each other.

## What the model is actually learning

The gradient updates push the encoder to produce a representation space where:
- Semantic similarity correlates with geometric proximity
- The "meaning" of a sentence is captured by its position relative to other sentences

This is fundamentally different from classification losses, where each example is evaluated independently. Contrastive loss is inherently about relationships.

## Practical notes

**Negative pair quality matters a lot.** Easy negatives (completely unrelated sentences) give weak gradient signal — the model already pushes them apart. Hard negatives (sentences that look similar but aren't) are where the learning happens. If your training set has only easy negatives, loss may drop quickly but the model won't generalize well to subtle distinctions.

**The margin hyperparameter is worth tuning.** Too small and dissimilar pairs aren't pushed far enough apart. Too large and you force the model to waste capacity on already-separated pairs.

**Cosine vs. Euclidean distance.** `sentence-transformers` often uses cosine similarity rather than raw Euclidean distance, because embeddings are typically L2-normalized. Cosine distance is bounded [0, 2], which makes margin semantics more interpretable.

**Alternatives to be aware of.** Contrastive loss on pairs is the baseline. More advanced approaches include:
- **Triplet loss** — anchor, positive, negative all at once; stronger signal
- **Multiple Negatives Ranking Loss (MNR)** — treats other items in the batch as negatives; very sample-efficient and often preferred now
- **CoSENT / AnglE loss** — newer objectives with better gradient properties

If you're starting fresh and have flexibility, MNR loss tends to outperform binary contrastive loss in most benchmarks, assuming your data supports it (you need clear positive pairs, and batch size matters). But contrastive loss is well-understood, stable, and a reasonable default.

## One-sentence summary

Contrastive loss trains your embedding model by showing it pairs of sentences and penalizing it whenever similar pairs are far apart in vector space or dissimilar pairs are too close — teaching the model geometry by example.
