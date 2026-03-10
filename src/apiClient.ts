export interface Clause {
  id: string;
  text: string;
  risk: 'safe' | 'watch' | 'danger';
  confidence: number;
  anomaly_score: number;
  category: string;
  explanation: string;
}

export interface AnalysisResponse {
  id: string;
  status: 'processing' | 'complete' | 'failed';
  clause_count: number;
  risk_summary: {
    safe: number;
    watch: number;
    danger: number;
  };
  clauses?: Clause[];
}

// Function to poll the backend until the analysis is complete
export async function analyzeText(rawText: string): Promise<AnalysisResponse> {
  // 1. Send text to backend to start analysis
  const startRes = await fetch('/api/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text: rawText }),
  });

  if (!startRes.ok) {
    throw new Error(`Failed to start analysis: ${startRes.statusText}`);
  }

  const { id } = await startRes.json();

  // 2. Poll the backend until the analysis is complete
  let attempts = 0;
  const maxAttempts = 600; // Up to 10 minutes polling for the first model download

  while (attempts < maxAttempts) {
    const statusRes = await fetch(`/api/analyses/${id}`);
    if (!statusRes.ok) {
      throw new Error(`Failed to check status: ${statusRes.statusText}`);
    }

    const analysis: AnalysisResponse = await statusRes.json();

    if (analysis.status === 'failed') {
      throw new Error('Analysis failed on the server.');
    }

    if (analysis.status === 'complete') {
      // 3. Fetch the finished clauses
      const clausesRes = await fetch(`/api/analyses/${id}/clauses`);
      if (!clausesRes.ok) {
        throw new Error('Failed to fetch clauses.');
      }

      const { clauses } = await clausesRes.json();
      analysis.clauses = clauses;
      return analysis;
    }

    // Wait 1 second before polling again
    await new Promise(resolve => setTimeout(resolve, 1000));
    attempts++;
  }

  throw new Error('Analysis timed out. Please try again later.');
}
