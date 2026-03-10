# Contrastive Loss for Sentence Embeddings

When fine-tuning sentence embedding models (like those from `sentence-transformers`), traditional classification losses fall short. Contrastive loss is a metric learning objective designed to directly shape the embedding space so that semantically similar items are grouped together and dissimilar items are pushed apart.

## Why Not Classification Loss?

Classification architectures (Cross-Entropy over a softmax projection) map inputs to a fixed set of predefined classes. This is highly ineffective for embedding models because:
1. **Open-vocabulary generalization:** Embeddings are usually deployed for similarity search (RAG, clustering, semantic search) where the "classes" (queries and documents) are potentially infinite and unseen during training.
2. **Metric space topology:** Cross-entropy optimizes for linear separability via hyperplanes. It does not explicitly force the intermediate representations to possess meaningful spatial distances (e.g., Euclidean or Cosine distance), which is the exact property vector databases rely on.

Contrastive loss abandons classes entirely. Instead, it optimizes the distance metric directly.

## The Mathematical Formulation

Given a pair of text inputs $(x_1, x_2)$, an encoder $f_\theta$ maps them to vectors $v_1, v_2$. Let $D(v_1, v_2)$ be the distance between them (usually Euclidean). 

Assume a binary label $Y$, where $Y=1$ implies the pair is similar (positive), and $Y=0$ implies they are dissimilar (negative). The contrastive loss is defined as:

$$ L = Y \cdot \frac{1}{2} D(v_1, v_2)^2 + (1 - Y) \cdot \frac{1}{2} \max(0, m - D(v_1, v_2))^2 $$

### The Role of the Margin ($m$)
The margin $m$ is the critical hyperparameter for negative pairs. 
* For positive pairs ($Y=1$), the loss simply minimizes their squared distance. 
* For negative pairs ($Y=0$), the loss penalizes them *only if they are closer than the margin $m$*. 

Without a margin, the model would spend infinite capacity trying to push negative pairs infinitely far apart. This destroys the local manifold structure of the embedding space and prevents the network from converging. The margin acts as a threshold: once a dissimilar pair is "far enough" apart, the gradient becomes zero, and the model focuses on harder examples.

## Implementation under the Hood

Here is how contrastive loss is typically implemented in PyTorch. 

```python
import torch
import torch.nn.functional as F

def contrastive_loss(v1: torch.Tensor, v2: torch.Tensor, y: torch.Tensor, margin: float = 1.0):
    """
    v1, v2: Embeddings of shape (batch_size, hidden_dim)
    y: Tensor of shape (batch_size,) containing 1 (similar) or 0 (dissimilar)
    """
    # Calculate Euclidean distance
    distances = F.pairwise_distance(v1, v2)
    
    # Loss for positive pairs: minimize distance
    loss_pos = y * (distances ** 2)
    
    # Loss for negative pairs: push apart up to the margin
    loss_neg = (1 - y) * F.relu(margin - distances) ** 2
    
    return torch.mean(loss_pos + loss_neg)
```

## Practical Considerations for Sentence Transformers

If you configure your fine-tuning pipeline to use `ContrastiveLoss`, be aware of the following data requirements and failure modes:

### 1. Data Format Requirements
Your dataset must be structured as explicit pairs with a binary or continuous label. 
* **Input:** `("How to reset password?", "Password recovery steps", 1)`
* **Input:** `("How to reset password?", "Update billing details", 0)`

### 2. The "Hard Negative" Problem
Because of the margin, random negative pairs quickly yield a loss of exactly `0.0`. If your dataset pairs random sentences as negatives, the network will learn nothing from them after the first few steps. You must use **hard negative mining**—selecting negative pairs that are syntactically similar but semantically distinct (e.g., "The cat chased the dog" vs "The dog chased the cat") so they violate the margin and produce gradients.

### 3. Feature Collapse
If your margin is too small or your learning rate too high, metric learning models are prone to "representation collapse," where the encoder learns to map every input to the exact same vector. Monitoring the average Euclidean distance of your embeddings during training is a good diagnostic.

## Contrastive vs. Related Losses

* **Triplet Loss:** Instead of taking pairs, Triplet Loss takes a tuple: (Anchor, Positive, Negative). It optimizes the *relative* distance, enforcing that $D(Anchor, Positive) < D(Anchor, Negative) - margin$. Triplet loss is generally superior for ranking tasks because it directly optimizes relative ordering rather than absolute distances, but it requires more complex data preparation (mining valid triplets).
* **Cosine Similarity Loss:** Often used when you have continuous similarity scores (e.g., human-annotated scores from 0.0 to 1.0) rather than binary labels. It computes the cosine similarity between $v_1$ and $v_2$ and typically applies Mean Squared Error (MSE) against the target score. Contrastive loss, by convention, operates on Euclidean distances and binary labels using a hinge-like margin.

## Related Concepts to Explore
* **InfoNCE / NT-Xent Loss:** The modern evolution of contrastive learning (used in SimCLR, CLIP). Instead of fixed negative pairs, it treats all other items in a training batch as negatives, calculating a softmax over similarities.
* **MultipleNegativesRankingLoss (MNRL):** The `sentence-transformers` implementation of InfoNCE. If you are fine-tuning a sentence transformer today, **MNRL is almost always preferred over standard Contrastive Loss**, as it automatically mines in-batch negatives, drastically improving training efficiency without requiring explicit negative pairs in your dataset.