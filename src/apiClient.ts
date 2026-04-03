// ── Types ───────────────────────────────────────────────────────────

export interface ClauseExplanation {
  summary: string;
  unusual: string;
  risks: string;
}

export interface Clause {
  id: string;
  text: string;
  risk: 'safe' | 'watch' | 'danger';
  confidence: number;
  anomaly_score: number;
  category: string;
  explanation: ClauseExplanation;
}

export interface AnalysisResponse {
  id: string;
  url: string | null;
  raw_text?: string | null;
  status: 'processing' | 'complete' | 'failed';
  clause_count: number;
  risk_summary: {
    safe: number;
    watch: number;
    danger: number;
  };
  created_at: string | null;
  completed_at: string | null;
  clauses?: Clause[];
}

export interface AnalyzeRequest {
  url?: string;
  text?: string;
}

export interface AuthUser {
  user_id: string;
  username: string;
}

export interface AuthResponse {
  token: string;
  user_id: string;
  username: string;
}

export interface HistoryEntry {
  id: string;
  url: string | null;
  analysis_result: {
    analysis_id: string;
    clause_count: number;
    risk_summary: { safe: number; watch: number; danger: number };
  } | null;
  created_at: string;
}

// ── Token / session helpers ─────────────────────────────────────────

const TOKEN_KEY = 'clauseflag_token';
const USER_KEY = 'clauseflag_user';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveAuth(auth: AuthResponse): void {
  localStorage.setItem(TOKEN_KEY, auth.token);
  localStorage.setItem(
    USER_KEY,
    JSON.stringify({ user_id: auth.user_id, username: auth.username }),
  );
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function authHeaders(): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

// ── Auth endpoints ──────────────────────────────────────────────────

export async function register(
  username: string,
  password: string,
): Promise<AuthResponse> {
  const res = await fetch('/api/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Registration failed');
  }
  const data: AuthResponse = await res.json();
  saveAuth(data);
  return data;
}

export async function login(
  username: string,
  password: string,
): Promise<AuthResponse> {
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'Login failed');
  }
  const data: AuthResponse = await res.json();
  saveAuth(data);
  return data;
}

// ── History endpoint ────────────────────────────────────────────────

export async function fetchHistory(): Promise<HistoryEntry[]> {
  const token = getToken();
  if (!token) return [];
  const res = await fetch('/api/history', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    if (res.status === 401) {
      clearAuth();
      return [];
    }
    throw new Error('Failed to fetch history');
  }
  const data = await res.json();
  return data.history;
}

// ── Load a past analysis by ID ──────────────────────────────────────

export async function fetchAnalysis(
  analysisId: string,
): Promise<AnalysisResponse> {
  const [analysisRes, clausesRes] = await Promise.all([
    fetch(`/api/analyses/${analysisId}`),
    fetch(`/api/analyses/${analysisId}/clauses`),
  ]);

  if (!analysisRes.ok) {
    throw new Error('Failed to load analysis');
  }
  if (!clausesRes.ok) {
    throw new Error('Failed to load clauses');
  }

  const analysis: AnalysisResponse = await analysisRes.json();
  const { clauses } = await clausesRes.json();
  analysis.clauses = clauses;
  return analysis;
}

// ── Analysis (existing, now with auth header) ───────────────────────

export async function analyze(
  request: AnalyzeRequest,
): Promise<AnalysisResponse> {
  if (!request.url && !request.text) {
    throw new Error("Either 'url' or 'text' must be provided.");
  }

  const startRes = await fetch('/api/analyze', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(request),
  });

  if (!startRes.ok) {
    let detail = startRes.statusText;
    try {
      const body = await startRes.json();
      if (body.detail) detail = body.detail;
    } catch {
      /* use statusText fallback */
    }
    throw new Error(detail);
  }

  const { id } = await startRes.json();

  let attempts = 0;
  const maxAttempts = 600;

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
      const clausesRes = await fetch(`/api/analyses/${id}/clauses`);
      if (!clausesRes.ok) {
        throw new Error('Failed to fetch clauses.');
      }
      const { clauses } = await clausesRes.json();
      analysis.clauses = clauses;
      return analysis;
    }

    await new Promise((resolve) => setTimeout(resolve, 1000));
    attempts++;
  }

  throw new Error('Analysis timed out. Please try again later.');
}

export async function analyzeText(
  rawText: string,
): Promise<AnalysisResponse> {
  return analyze({ text: rawText });
}
