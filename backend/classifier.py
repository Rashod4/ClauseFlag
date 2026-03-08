from transformers import pipeline

class ClauseClassifier:
    def __init__(self):
        # Using a fast, widely-available zero-shot classifier
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        self.labels = ["safe", "watch", "danger"]
        
        # We can contextualize the prompt to help the model
        self.hypothesis_template = "This terms of service clause is {}."

    def classify(self, text: str):
        result = self.classifier(text, candidate_labels=self.labels, hypothesis_template=self.hypothesis_template)
        
        # The first label is the highest scoring one
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        return {
            "risk": top_label,
            "confidence": top_score
        }

# Singleton instance
_classifier_instance = None

def get_classifier():
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = ClauseClassifier()
    return _classifier_instance
