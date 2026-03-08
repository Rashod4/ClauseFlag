import csv
import os
import json
import torch
from sentence_transformers import SentenceTransformer, util

class AnomalyDetector:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.corpus_embeddings = None
        self._load_corpus()

    def _load_corpus(self):
        # Load the training dataset to act as our baseline corpus
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'training_dataset.json')
        sentences = []
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                sentences = [item['text'] for item in data]
        else:
            # Fallback if no dataset
            sentences = ["We collect your email address.", "You must be 13 to use this service."]

        # Precompute embeddings for the corpus
        with torch.no_grad():
            self.corpus_embeddings = self.model.encode(sentences, convert_to_tensor=True)

    def compute_anomaly_score(self, text: str) -> float:
        if self.corpus_embeddings is None or len(self.corpus_embeddings) == 0:
            return 0.5

        # Embed the input clause
        with torch.no_grad():
            query_embedding = self.model.encode(text, convert_to_tensor=True)

        # Compute cosine similarities between the input and all corpus sentences
        cosine_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        
        # Find the most similar sentence in the corpus
        max_similarity = torch.max(cosine_scores).item()

        # Anomaly score is conceptually the opposite of similarity to the nearest neighbor
        # If max_similarity is 1.0 (exact match in corpus), anomaly is 0.0
        # If max_similarity is 0.0 (completely unlike anything seen), anomaly is 1.0
        anomaly_score = max(0.0, 1.0 - max_similarity)
        
        return anomaly_score

# Singleton instance
_anomaly_instance = None

def get_anomaly_detector():
    global _anomaly_instance
    if _anomaly_instance is None:
        _anomaly_instance = AnomalyDetector()
    return _anomaly_instance
