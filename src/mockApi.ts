export interface Clause {
  id: string;
  text: string;
  risk: "safe" | "watch" | "danger";
  confidence: number;
  anomaly_score: number;
  category: string;
  explanation: string;
}

export interface AnalysisResponse {
  id: string;
  status: "complete";
  clause_count: number;
  risk_summary: {
    safe: number;
    watch: number;
    danger: number;
  };
  clauses: Clause[];
}

const MOCK_RESPONSE: AnalysisResponse = {
  id: "analysis-mock-001",
  status: "complete",
  clause_count: 5,
  risk_summary: {
    safe: 2,
    watch: 2,
    danger: 1,
  },
  clauses: [
    {
      id: "clause-1",
      text: "By using our services, you agree to binding arbitration and waive your right to a jury trial or class action.",
      risk: "danger",
      confidence: 0.94,
      anomaly_score: 0.87,
      category: "Dispute Resolution",
      explanation: "Mandatory arbitration with class action waiver is a high-risk clause.",
    },
    {
      id: "clause-2",
      text: "We may collect and process your personal data in accordance with our Privacy Policy.",
      risk: "watch",
      confidence: 0.82,
      anomaly_score: 0.45,
      category: "Data Collection",
      explanation: "Broad data collection language; review linked Privacy Policy.",
    },
    {
      id: "clause-3",
      text: "You may terminate your account at any time by contacting support.",
      risk: "safe",
      confidence: 0.91,
      anomaly_score: 0.12,
      category: "Termination",
      explanation: "Standard user-initiated termination right.",
    },
    {
      id: "clause-4",
      text: "We reserve the right to modify these terms at any time; continued use constitutes acceptance.",
      risk: "watch",
      confidence: 0.78,
      anomaly_score: 0.52,
      category: "Amendment",
      explanation: "Unilateral change with implied consent may limit your recourse.",
    },
    {
      id: "clause-5",
      text: "Your feedback and suggestions may be used by us without compensation or attribution.",
      risk: "safe",
      confidence: 0.85,
      anomaly_score: 0.21,
      category: "IP / Feedback",
      explanation: "Common feedback license; low user impact.",
    },
  ],
};

/**
 * Simulates analyzing raw Terms of Service text.
 * No real backend — returns hardcoded mock data after a 2-second delay.
 */
export function analyzeText(_rawText: string): Promise<AnalysisResponse> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_RESPONSE);
    }, 2000);
  });
}
