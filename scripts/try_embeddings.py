import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

sentences = [
    "Postman now ships AI features without asking",
    "We moved the team to Bruno, collections live in git now",
    "My sourdough starter died over the weekend",
]

vectors = model.encode(sentences)

print(f"shape: {vectors.shape}")
print(f"first 5 numbers: {vectors[0][:5]}")

def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


print(f"\nAPI client vs API client: {cosine(vectors[0], vectors[1]):.3f}")
print(f"API client vs bread:      {cosine(vectors[0], vectors[2]):.3f}")
print(f"API client vs bread:      {cosine(vectors[1], vectors[2]):.3f}")