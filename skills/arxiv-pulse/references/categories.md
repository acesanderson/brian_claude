# arXiv Category Codes

Reference for `get_recent_papers(category=...)` and category-filtered searches.
Full list: https://arxiv.org/category_taxonomy

## Computer Science (cs.*)

| Code | Name | Relevance |
|------|------|-----------|
| cs.AI | Artificial Intelligence | Core AI: planning, search, knowledge representation |
| cs.CL | Computation and Language | NLP, LLMs, text generation, translation, QA |
| cs.CV | Computer Vision and Pattern Recognition | Image/video understanding, object detection, generative vision |
| cs.LG | Machine Learning | Learning algorithms, deep learning, optimization, generalization |
| cs.NE | Neural and Evolutionary Computing | Neural networks, evolutionary algorithms |
| cs.IR | Information Retrieval | Search, recommendation, RAG systems |
| cs.HC | Human-Computer Interaction | UX, accessibility, human-AI interaction |
| cs.CY | Computers and Society | Ethics, fairness, ed-tech, policy, social impact |
| cs.SE | Software Engineering | Code generation, testing, program analysis |
| cs.DB | Databases | Data management, query languages, data mining |
| cs.DC | Distributed, Parallel, and Cluster Computing | Distributed systems, cloud computing |
| cs.CR | Cryptography and Security | Security, privacy, adversarial ML |
| cs.RO | Robotics | Robot learning, embodied AI |
| cs.MM | Multimedia | Audio, video, multimodal systems |
| cs.GT | Computer Science and Game Theory | Multi-agent systems, mechanism design |

## Statistics (stat.*)

| Code | Name | Relevance |
|------|------|-----------|
| stat.ML | Machine Learning | Probabilistic ML, Bayesian methods, statistical learning theory |
| stat.AP | Applications | Applied statistics across domains |
| stat.ME | Methodology | Statistical methods and inference |

## Mathematics (math.*)

| Code | Name | Relevance |
|------|------|-----------|
| math.OC | Optimization and Control | Convex optimization, reinforcement learning theory |
| math.ST | Statistics Theory | Theoretical foundations for ML |

## Electrical Engineering (eess.*)

| Code | Name | Relevance |
|------|------|-----------|
| eess.AS | Audio and Speech Processing | Speech recognition, TTS, audio generation |
| eess.IV | Image and Video Processing | Signal processing for vision |
| eess.SP | Signal Processing | General signal processing |

## Quantitative Biology (q-bio.*)

| Code | Name | Relevance |
|------|------|-----------|
| q-bio.NC | Neurons and Cognition | Computational neuroscience, brain-inspired AI |
| q-bio.QM | Quantitative Methods | Bioinformatics, biological data analysis |

## Physics (physics.*)

| Code | Name | Relevance |
|------|------|-----------|
| physics.ed-ph | Physics Education | Ed-tech, pedagogy, science education |

## Education / Ed-tech Notes

arXiv does not have a dedicated education category. Education-related CS papers typically appear in:
- **cs.CY** (Computers and Society) - ed-tech, educational technology policy
- **cs.HC** (HCI) - learning interfaces, adaptive tutoring
- **cs.AI** / **cs.CL** - intelligent tutoring systems, automated grading
- **physics.ed-ph** - physics-specific education research

## Common Multi-Category Searches

For broader coverage, search by keyword across all fields rather than filtering by category:

```python
# All LLM papers regardless of category
search_papers("large language model", max_results=20)

# Recent AI safety papers
search_papers("AI safety alignment", sort_by="submittedDate")

# RAG systems
search_papers("retrieval augmented generation", max_results=15)
```
