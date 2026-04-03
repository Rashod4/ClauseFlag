import { useState, useEffect, useCallback } from 'react';
import { Info, AlertTriangle, ShieldAlert } from 'lucide-react';
import type { AnalysisResponse, Clause, AuthUser } from './apiClient';
import { analyze, fetchAnalysis, getStoredUser, clearAuth } from './apiClient';
import AuthModal from './components/AuthModal';
import HistoryPanel from './components/HistoryPanel';

type InputMode = 'text' | 'url';
type RiskFilter = 'all' | 'safe' | 'watch' | 'danger';

const riskColors: Record<RiskFilter, string> = {
  all: 'bg-slate-100 text-slate-800',
  safe: 'bg-emerald-100 text-emerald-800',
  watch: 'bg-amber-100 text-amber-800',
  danger: 'bg-rose-100 text-rose-800',
};

const riskBorderColors: Record<Clause['risk'], string> = {
  safe: 'border-emerald-300',
  watch: 'border-amber-300',
  danger: 'border-rose-300',
};

export default function App() {
  const [mode, setMode] = useState<InputMode>('text');
  const [textInput, setTextInput] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [filter, setFilter] = useState<RiskFilter>('all');
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  // Auth state
  const [user, setUser] = useState<AuthUser | null>(getStoredUser);
  const [authOpen, setAuthOpen] = useState(false);
  const [historyKey, setHistoryKey] = useState(0);

  const handleLogout = useCallback(() => {
    clearAuth();
    setUser(null);
  }, []);

  const handleHistorySelect = useCallback(async (analysisId: string) => {
    setError(null);
    setIsAnalyzing(true);
    try {
      const data = await fetchAnalysis(analysisId);
      setResult(data);
      setFilter('all');
      if (data.url) {
        setMode('url');
        setUrlInput(data.url);
      } else if (data.raw_text) {
        setMode('text');
        setTextInput(data.raw_text);
      }
    } catch (e) {
      const message =
        e instanceof Error ? e.message : 'Failed to load analysis.';
      setError(message);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  useEffect(() => {
    if (!isAnalyzing) return;
    setElapsed(0);
    const t0 = Date.now();
    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - t0) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [isAnalyzing]);

  const handleAnalyze = async () => {
    const value = mode === 'text' ? textInput.trim() : urlInput.trim();
    if (!value) {
      setError(
        mode === 'text'
          ? 'Paste a terms of service or privacy policy first.'
          : 'Enter a URL to a terms of service or privacy policy.',
      );
      return;
    }
    setError(null);
    setIsAnalyzing(true);
    try {
      const request = mode === 'text' ? { text: value } : { url: value };
      const data = await analyze(request);
      setResult(data);
      if (user) setHistoryKey((k) => k + 1);
    } catch (e) {
      console.error(e);
      const message =
        e instanceof Error ? e.message : 'Unknown error during analysis.';
      setError(message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const filteredClauses =
    result && filter !== 'all'
      ? result.clauses!.filter((c) => c.risk === filter)
      : result?.clauses ?? [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8 md:flex-row md:py-12">
        {/* ── Left column: input + history ── */}
        <section className="space-y-4 md:w-1/2">
          {/* Header row */}
          <header className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
                ClauseFlag
              </h1>
              <p className="text-sm text-slate-300 md:text-base">
                Paste a Terms of Service or privacy policy to flag risky clauses
                as{' '}
                <span className="font-medium text-emerald-300">Safe</span>,{' '}
                <span className="font-medium text-amber-300">Watch</span>, or{' '}
                <span className="font-medium text-rose-300">Danger</span>.
              </p>
            </div>

            {/* Auth controls */}
            <div className="shrink-0 pt-1">
              {user ? (
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-sky-500/10 px-3 py-1 text-xs font-medium text-sky-300 ring-1 ring-sky-500/30">
                    {user.username}
                  </span>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="rounded-md px-2 py-1 text-xs text-slate-400 transition hover:text-slate-200"
                  >
                    Log out
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setAuthOpen(true)}
                  className="rounded-md bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 ring-1 ring-slate-700 transition hover:bg-slate-700"
                >
                  Log in
                </button>
              )}
            </div>
          </header>

          {/* Input area */}
          <div className="space-y-3">
            <div className="inline-flex rounded-lg bg-slate-900 p-1 text-sm">
              {(['text', 'url'] as InputMode[]).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => {
                    setMode(tab);
                    setError(null);
                  }}
                  className={[
                    'rounded-md px-4 py-1.5 font-medium transition',
                    tab === mode
                      ? 'bg-sky-500 text-slate-950 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200',
                  ].join(' ')}
                >
                  {tab === 'text' ? 'Paste Text' : 'URL'}
                </button>
              ))}
            </div>

            {mode === 'text' ? (
              <textarea
                id="tos-input"
                className="h-64 w-full resize-none rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-50 shadow-sm outline-none placeholder:text-slate-500 focus:border-sky-400 focus:ring-1 focus:ring-sky-400"
                placeholder="Paste the full text of a terms of service or privacy policy here..."
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
              />
            ) : (
              <input
                type="url"
                id="url-input"
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-50 shadow-sm outline-none placeholder:text-slate-500 focus:border-sky-400 focus:ring-1 focus:ring-sky-400"
                placeholder="https://example.com/privacy-policy"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
              />
            )}
          </div>

          {error && (
            <div
              className="rounded-md border border-rose-500/30 bg-rose-950/40 px-4 py-3 text-sm text-rose-200"
              role="alert"
            >
              {error}
            </div>
          )}

          <div className="space-y-3">
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="inline-flex items-center justify-center rounded-md bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 shadow-sm transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isAnalyzing ? 'Analyzing…' : 'Analyze clauses'}
            </button>

            {isAnalyzing && (
              <div className="flex items-center gap-3 rounded-md border border-sky-500/20 bg-sky-950/30 px-4 py-3">
                <svg
                  className="h-4 w-4 shrink-0 animate-spin text-sky-400"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                <div className="text-sm">
                  <p className="text-sky-200">
                    Scraping and analyzing… this may take a minute for the first
                    run.
                  </p>
                  <p className="tabular-nums text-xs text-sky-300/60">
                    {elapsed}s elapsed
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* History panel (only when logged in) */}
          {user && (
            <div className="pt-2">
              <HistoryPanel
                refreshKey={historyKey}
                onSelect={handleHistorySelect}
                activeAnalysisId={result?.id}
              />
            </div>
          )}
        </section>

        {/* ── Right column: results ── */}
        <section className="space-y-4 md:w-1/2">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-slate-100">
              Analysis results
            </h2>
            <div className="inline-flex gap-2 rounded-full bg-slate-900 p-1 text-xs">
              {(['all', 'safe', 'watch', 'danger'] as RiskFilter[]).map(
                (key) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setFilter(key)}
                    className={[
                      'rounded-full px-3 py-1 capitalize transition',
                      key === filter
                        ? riskColors[key]
                        : 'text-slate-300 hover:bg-slate-800',
                    ].join(' ')}
                  >
                    {key}
                  </button>
                ),
              )}
            </div>
          </div>

          {!result && (
            <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/60 p-6 text-sm text-slate-300">
              No analysis yet. Paste a document on the left and select{' '}
              <span className="font-medium text-sky-300">Analyze clauses</span>{' '}
              to see flagged sections here.
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-3 text-xs">
                <SummaryPill
                  label="Safe"
                  value={result.risk_summary.safe}
                  color="bg-emerald-900/40 text-emerald-200 border-emerald-600/60"
                />
                <SummaryPill
                  label="Watch"
                  value={result.risk_summary.watch}
                  color="bg-amber-900/40 text-amber-200 border-amber-600/60"
                />
                <SummaryPill
                  label="Danger"
                  value={result.risk_summary.danger}
                  color="bg-rose-900/40 text-rose-200 border-rose-600/60"
                />
                <SummaryPill
                  label="Total clauses"
                  value={result.clause_count}
                  color="bg-slate-900/60 text-slate-200 border-slate-600/60"
                />
              </div>

              <div className="space-y-3">
                {filteredClauses.map((clause) => (
                  <ClauseCard key={clause.id} clause={clause} />
                ))}
              </div>
            </div>
          )}
        </section>
      </div>

      {/* Auth modal */}
      <AuthModal
        open={authOpen}
        onOpenChange={setAuthOpen}
        onSuccess={(auth) =>
          setUser({ user_id: auth.user_id, username: auth.username })
        }
      />
    </div>
  );
}

// ── Local presentational components ─────────────────────────────────

function SummaryPill(props: { label: string; value: number; color: string }) {
  const { label, value, color } = props;
  return (
    <div
      className={[
        'inline-flex items-center gap-2 rounded-full border px-3 py-1',
        color,
      ].join(' ')}
    >
      <span className="text-xs font-medium">{label}</span>
      <span className="text-xs tabular-nums">{value}</span>
    </div>
  );
}

function ClauseCard({ clause }: { clause: Clause }) {
  const borderColor = riskBorderColors[clause.risk];
  const { summary, unusual, risks } = clause.explanation;

  return (
    <article
      className={[
        'rounded-lg border bg-slate-900/70 p-4 shadow-sm',
        borderColor,
      ].join(' ')}
    >
      <header className="mb-2 flex items-center justify-between gap-3 text-xs">
        <div className="inline-flex items-center gap-2">
          <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[11px] uppercase tracking-wide text-slate-300">
            {clause.category}
          </span>
          <RiskBadge risk={clause.risk} />
        </div>
        <div className="flex gap-2 text-[11px] text-slate-400">
          <span className="tabular-nums">
            Confidence: {(clause.confidence * 100).toFixed(0)}%
          </span>
          <span className="tabular-nums">
            Anomaly: {(clause.anomaly_score * 100).toFixed(0)}%
          </span>
        </div>
      </header>

      <p className="mb-3 text-sm text-slate-50">{clause.text}</p>

      <div className="space-y-2 border-t border-slate-800 pt-3">
        <div className="flex gap-2.5 rounded-md bg-sky-950/40 px-3 py-2.5 ring-1 ring-sky-500/20">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-sky-400" />
          <div className="text-xs">
            <p className="font-medium text-sky-300">Layman's Summary</p>
            <p className="mt-1 leading-relaxed text-slate-300">{summary}</p>
          </div>
        </div>

        {unusual && (
          <div className="flex gap-2.5 rounded-md bg-amber-950/30 px-3 py-2.5 ring-1 ring-amber-500/20">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" />
            <div className="text-xs">
              <p className="font-medium text-amber-300">Why this is unusual</p>
              <p className="mt-1 leading-relaxed text-slate-300">{unusual}</p>
            </div>
          </div>
        )}

        {risks && (
          <div className="flex gap-2.5 rounded-md bg-rose-950/30 px-3 py-2.5 ring-1 ring-rose-500/20">
            <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0 text-rose-400" />
            <div className="text-xs">
              <p className="font-medium text-rose-300">Potential Risks</p>
              <p className="mt-1 leading-relaxed text-slate-300">{risks}</p>
            </div>
          </div>
        )}
      </div>
    </article>
  );
}

function RiskBadge({ risk }: { risk: Clause['risk'] }) {
  const label =
    risk === 'safe' ? 'Safe' : risk === 'watch' ? 'Watch' : 'Danger';
  const base =
    risk === 'safe'
      ? 'bg-emerald-900/60 text-emerald-200 border-emerald-600/70'
      : risk === 'watch'
        ? 'bg-amber-900/60 text-amber-200 border-amber-600/70'
        : 'bg-rose-900/60 text-rose-200 border-rose-600/70';

  return (
    <span
      className={[
        'inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide',
        base,
      ].join(' ')}
    >
      {label}
    </span>
  );
}
