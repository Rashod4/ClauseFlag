class Explainer:
    def __init__(self):
        # Rule-based explanations depending on keywords found in the clause
        self.rules = {
            "sell": {
                "category": "Data Selling",
                "explanation": "This explicitly mentions the sale of your personal data to outside parties, which is a major privacy concern."
            },
            "arbitration": {
                "category": "Dispute Resolution",
                "explanation": "This forces you to use private arbitration to settle disputes, taking away your right to sue in court."
            },
            "class action": {
                "category": "Dispute Resolution",
                "explanation": "This prevents you from joining with others in a class action lawsuit against the company."
            },
            "perpetual": {
                "category": "IP Rights",
                "explanation": "This claims permanent, likely unbreakable rights to content or ideas you submit."
            },
            "without notice": {
                "category": "Termination",
                "explanation": "They assert the right to end your account or change rules without telling you beforehand."
            },
            "indemnify": {
                "category": "Liability",
                "explanation": "This shifts legal and financial responsibility onto you if something goes wrong."
            },
            "location": {
                "category": "Data Collection",
                "explanation": "This relates to the collection of your physical geographic location data."
            },
            "cookies": {
                "category": "Tracking",
                "explanation": "Mentions the use of cookies or similar trackers to monitor your activity."
            },
            "third party": {
                "category": "Data Sharing",
                "explanation": "Indicates information may be shared with or accessed by external companies."
            },
            "anonymized": {
                "category": "Data Processing",
                "explanation": "Mentions stripping identifying details from your data before use."
            },
            "delete": {
                "category": "Data Rights",
                "explanation": "Discusses your ability to remove your data or account."
            },
            "protect": {
                "category": "Security",
                "explanation": "Relates to the security measures used to safeguard your information."
            }
        }

    def generate_explanation(self, text: str, risk: str) -> dict:
        text_lower = text.lower()
        
        # Check rule matches
        for keyword, data in self.rules.items():
            if keyword in text_lower:
                return data

        # Fallbacks depending on risk
        if risk == "safe":
            return {
                "category": "General",
                "explanation": "This appears to be a standard, low-risk clause regarding basic service operations."
            }
        elif risk == "watch":
            return {
                "category": "General",
                "explanation": "This clause is fairly standard but grants the company rights you should be mindful of."
            }
        else:
            return {
                "category": "General",
                "explanation": "This clause strongly favors the company and significantly limits your rights or privacy."
            }

# Singleton instance
_explainer_instance = None

def get_explainer():
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = Explainer()
    return _explainer_instance
