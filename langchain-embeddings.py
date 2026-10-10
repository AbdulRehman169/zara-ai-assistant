from langchain_community.embeddings import SentenceTransformerEmbeddings

embedding_model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Convert 3 sentences to embeddings
text1 = "Zara is an AI assistant"
text2 = "Zara is a helpful chatbot"
text3 = "Abdul loves playing cricket"

emb1 = embedding_model.embed_query(text1)
emb2 = embedding_model.embed_query(text2)
emb3 = embedding_model.embed_query(text3)

print(f"Each embedding has {len(emb1)} numbers")
print(f"First 5 numbers of text1: {emb1[:5]}")
print(f"First 5 numbers of text2: {emb2[:5]}")
print(f"First 5 numbers of text3: {emb3[:5]}")
import numpy as np

def cosine_similarity(a, b):
    #dot product divided by the product of both magnitudes
    dot = np.dot(a, b)
    length_a = np.linalg.norm(a)
    length_b = np.linalg.norm(b)

    similarity = dot / (length_a * length_b)

    return similarity

sim_1_2 = cosine_similarity(emb1, emb2)
sim_1_3 = cosine_similarity(emb1, emb3)

print(f"Similarity between text1 and text2 (both about Zara): {sim_1_2:.4f}")
print(f"Similarity between text1 and text3 (different topics): {sim_1_3:.4f}")
print(f"text1 and text2 are more similar: {sim_1_2 > sim_1_3}")