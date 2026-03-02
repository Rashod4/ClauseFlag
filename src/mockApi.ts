import {GoogleGenerativeAI} from '@google/generative-ai';

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
  status: 'complete';
  clause_count: number;
  risk_summary: {
    safe: number;
    watch: number;
    danger: number;
  };
  clauses: Clause[];
}

const apiKey = process.env.GEMINI_API_KEY as string | undefined;

if (!apiKey) {
  // Surface clearly during development if the key is missing.
  // eslint-disable-next-line no-console
  console.error('GEMINI_API_KEY is not set. Add it to .env.local.');
}

const genAI = apiKey ? new GoogleGenerativeAI(apiKey) : null;

function buildPrompt(rawText: string): string {
  return `
You are a legal and privacy policy clause risk analyzer.

Given the following policy or terms-of-service text, identify the most important clauses and
classify each as one of: "safe", "watch", or "danger". Focus on things like dispute resolution,
data collection/processing, termination, unilateral changes, IP, and other rights or limitations.

Return ONLY valid JSON matching this exact TypeScript type (no extra keys, no comments, no prose):

type Risk = "safe" | "watch" | "danger";

interface Clause {
  id: string;
  text: string;
  risk: Risk;
  confidence: number;        // 0–1
  anomaly_score: number;     // 0–1, how unusual or unexpected the clause is
  category: string;          // short label like "Data Collection", "Termination"
  explanation: string;       // 1–2 sentence plain-language explanation
}

interface AnalysisResponse {
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

Now analyze this text:
---
${rawText}
---

Remember: respond with JSON ONLY that matches AnalysisResponse exactly.`;
}

function extractJson(text: string): string {
  const trimmed = text.trim();

  // Prefer content inside fenced code blocks, especially ```json.
  const fenceMatch = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fenceMatch && fenceMatch[1]) {
    return fenceMatch[1].trim();
  }

  // Fallback: try to pull out the first JSON object, even if mixed with prose.
  const objectMatch = trimmed.match(/\{[\s\S]*\}/);
  if (objectMatch && objectMatch[0]) {
    return objectMatch[0];
  }

  // Last resort: assume the whole thing is JSON (may still fail to parse).
  return trimmed;
}

export async function analyzeText(rawText: string): Promise<AnalysisResponse> {
  if (!genAI) {
    throw new Error('GEMINI_API_KEY is not configured.');
  }

  const model = genAI.getGenerativeModel({
    // Use a broadly available text model for this deprecated SDK.
    model: 'gemini-2.5-flash',
  });

//   client = genai.Client(http_options={'api_version': 'v1alpha'})

//   response = client.models.generate_content(
//       model='gemini-2.5-flash',
//       contents="Explain how AI works",
//   )


  const prompt = buildPrompt(rawText);
  const result = await model.generateContent(prompt);
  const raw = result.response.text();
  const json = extractJson(raw);

  let parsed: AnalysisResponse;
  try {
    parsed = JSON.parse(json) as AnalysisResponse;
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('Failed to parse Gemini JSON response:', {raw, json, err});
    throw new Error('Gemini returned an unparseable response. Try again or simplify the input.');
  }

  if (!parsed || parsed.status !== 'complete' || !Array.isArray(parsed.clauses)) {
    throw new Error('Unexpected response shape from Gemini.');
  }

  return parsed;
}
