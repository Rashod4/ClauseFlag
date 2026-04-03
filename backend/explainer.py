class Explainer:
    def __init__(self):
        self.rules = {
            "sell": {
                "category": "Data Selling",
                "explanation": {
                    "summary": "This clause states that the company may sell your personal data to outside parties.",
                    "unusual": "Most reputable services share data only for operational needs, not for direct sale. Explicitly mentioning 'selling' data is a red flag.",
                    "risks": "Your personal information could be sold to data brokers, advertisers, or other third parties without your direct knowledge of who receives it.",
                },
            },
            "arbitration": {
                "category": "Dispute Resolution",
                "explanation": {
                    "summary": "This requires you to settle any disputes through private arbitration rather than in a court of law.",
                    "unusual": "Mandatory arbitration strips away your right to a jury trial and typically uses a process that statistically favors the company.",
                    "risks": "You lose access to the public court system, and arbitration decisions are usually final with very limited options to appeal.",
                },
            },
            "class action": {
                "category": "Dispute Resolution",
                "explanation": {
                    "summary": "This prevents you from joining a group lawsuit (class action) against the company.",
                    "unusual": "Class action waivers make it impractical to challenge small but widespread harms, since individual cases are rarely worth pursuing alone.",
                    "risks": "Even if thousands of users are affected by the same issue, each person must file and fund their own separate legal claim.",
                },
            },
            "perpetual": {
                "category": "IP Rights",
                "explanation": {
                    "summary": "This grants the company permanent, irrevocable rights over content or material you submit.",
                    "unusual": "Most services only need temporary licenses to display your content. Claiming perpetual rights goes well beyond what is operationally necessary.",
                    "risks": "You may permanently lose control of your content, even after deleting your account or stopping use of the service.",
                },
            },
            "without notice": {
                "category": "Termination",
                "explanation": {
                    "summary": "This allows the company to change terms, end your account, or modify the service without telling you first.",
                    "unusual": "Standard practice is to notify users of significant changes. Reserving the right to act 'without notice' removes your ability to respond.",
                    "risks": "You could lose access to your account, data, or paid services without any warning or opportunity to back up your information.",
                },
            },
            "indemnify": {
                "category": "Liability",
                "explanation": {
                    "summary": "This makes you financially responsible for legal costs if the company faces claims related to your use of the service.",
                    "unusual": "Indemnification clauses shift legal liability from the company to you, even for situations you may not have directly caused.",
                    "risks": "You could be required to pay the company's legal fees, settlements, or damages arising from lawsuits related to your account.",
                },
            },
            "location": {
                "category": "Data Collection",
                "explanation": {
                    "summary": "This relates to the collection of your physical geographic location data.",
                    "unusual": "Location tracking is one of the most sensitive forms of data collection, as it can reveal your daily routines and habits.",
                    "risks": "Your physical movements could be tracked, stored, and potentially shared, creating a detailed map of where you go and when.",
                },
            },
            "cookies": {
                "category": "Tracking",
                "explanation": {
                    "summary": "This describes the use of cookies or similar technology to track your online activity.",
                    "unusual": "While cookies are common, the scope of tracking varies widely. Broad cookie policies can enable extensive cross-site profiling.",
                    "risks": "Your browsing habits, preferences, and behavior may be monitored across websites to build a detailed advertising profile.",
                },
            },
            "third party": {
                "category": "Data Sharing",
                "explanation": {
                    "summary": "This indicates your information may be shared with or accessed by external companies.",
                    "unusual": "Third-party sharing is common, but vague language about who receives data and why should raise questions about how far your data travels.",
                    "risks": "Your data may end up with companies whose privacy practices you have not reviewed and cannot control.",
                },
            },
            "anonymized": {
                "category": "Data Processing",
                "explanation": {
                    "summary": "This mentions removing identifying details from your data before it is processed or shared.",
                    "unusual": "Anonymization sounds protective, but research has shown that supposedly anonymized data can sometimes be re-identified.",
                    "risks": "Even 'anonymized' data combined with other datasets could potentially be traced back to you.",
                },
            },
            "delete": {
                "category": "Data Rights",
                "explanation": {
                    "summary": "This describes your ability to request deletion of your data or account.",
                    "unusual": "The right to delete is increasingly standard, but companies often retain some data even after a deletion request.",
                    "risks": "Deletion may not be complete — backups, logs, or aggregated data derived from your information may persist.",
                },
            },
            "protect": {
                "category": "Security",
                "explanation": {
                    "summary": "This describes the security measures the company uses to safeguard your information.",
                    "unusual": "Security commitments are standard, but vague language like 'reasonable measures' leaves the actual level of protection undefined.",
                    "risks": "Without specific security commitments, you have limited recourse if a data breach occurs due to inadequate protections.",
                },
            },
        }

        self._fallbacks = {
            "safe": {
                "category": "General",
                "explanation": {
                    "summary": "This is a standard clause covering routine service operations.",
                    "unusual": "Nothing in this clause stands out as unusual compared to typical terms of service.",
                    "risks": "This clause poses minimal risk to your rights or privacy.",
                },
            },
            "watch": {
                "category": "General",
                "explanation": {
                    "summary": "This clause grants the company certain rights over your data or usage that are worth noting.",
                    "unusual": "While common in many agreements, this language gives the company more flexibility than strictly necessary.",
                    "risks": "These terms could be used broadly to justify actions you might not expect, so it is worth understanding exactly what you are agreeing to.",
                },
            },
            "danger": {
                "category": "General",
                "explanation": {
                    "summary": "This clause significantly limits your rights or gives the company extensive control over your data.",
                    "unusual": "The breadth of this clause goes beyond what is typical and heavily favors the company over the user.",
                    "risks": "You may be giving up important legal protections or granting access to your data in ways that are difficult to reverse.",
                },
            },
        }

    def generate_explanation(self, text: str, risk: str) -> dict:
        text_lower = text.lower()

        for keyword, data in self.rules.items():
            if keyword in text_lower:
                return data

        return self._fallbacks.get(risk, self._fallbacks["watch"])


_explainer_instance = None


def get_explainer():
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = Explainer()
    return _explainer_instance
