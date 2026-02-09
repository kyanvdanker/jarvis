# Long term memory layer for Jarvis 2.0 that uses a vector database to store 
# and retrieve information based on semantic similarity. 
# This allows Jarvis to remember past interactions, facts, 
# and other information in a way that can be easily accessed and used in future conversations.

import os
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class Memory:
    def __init__(self, memory_file="memory.json", embedding_model="all-MiniLM-L6-v2"):
        self.memory_file = memory_file
        self.embedding_model = SentenceTransformer(embedding_model)
        self.memory = []
        self.load_memory()

    def load_memory(self):
        self.memory = []
        if os.path.isfile(self.memory_file):
            with open(self.memory_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.memory.append(json.loads(line))


    def save_memory(self):
        with open(self.memory_file, "w") as f:
            for entry in self.memory:
                f.write(json.dumps(entry) + "\n")

    def add_memory(self, text):
        embedding = self.embedding_model.encode(text).tolist()
        self.memory.append({
            "text": text,
            "embedding": embedding,
            "timestamp": datetime.now().isoformat()
        })
        self.save_memory()

    def retrieve_memory(self, query):
        """
        Return ALL memories sorted by similarity (highest first).
        Each item: {"text": ..., "score": float, "timestamp": ...}
        """
        if not self.memory:
            return []

        query_embedding = self.embedding_model.encode(query).reshape(1, -1)
        embeddings = np.array([entry["embedding"] for entry in self.memory])
        similarities = cosine_similarity(query_embedding, embeddings)[0]

        results = []
        for entry, score in zip(self.memory, similarities):
            results.append({
                "text": entry["text"],
                "score": float(score),
                "timestamp": entry.get("timestamp")
            })

        # Sort descending by similarity
        results.sort(key=lambda x: x["score"], reverse=True)
        return results


    def find_relevant_memories(self, query, threshold=0.13, max_results=10):
        """
        Return up to max_results memories with similarity >= threshold.
        Sorted by similarity.
        """
        all_results = self.retrieve_memory(query)
        relevant = [m for m in all_results if m["score"] >= threshold]
        return [m["text"] for m in relevant[:max_results]]

    
    # Classifier to determine if a memory is relevant to a query
    def is_relevant(self, query, memory_text):
        query_embedding = self.embedding_model.encode(query).reshape(1, -1)
        memory_embedding = self.embedding_model.encode(memory_text).reshape(1, -1)
        similarity = cosine_similarity(query_embedding, memory_embedding)[0][0]
        return similarity > 0.5  # Threshold for relevance
    