import { useState } from "react";
import { analyzeText } from "./mockApi";
import type { AnalysisResponse } from "./mockApi";
import { Flag, Loader2 } from "lucide-react";

function Header() {
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm">
      <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-800 text-white">
            <Flag className="h-5 w-5" aria-hidden />
          </div>
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-slate-900 sm:text-2xl">
              ClauseFlag
            </h1>
            <p className="text-sm text-slate-500">
              Terms of Service Gotcha Detector
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}

function RiskBadge({
  risk,
}: {
  risk: "safe" | "watch" | "danger";
}) {
  const styles = {
    safe: "bg-emerald-100 text-emerald-800 border-emerald-200",
    watch: "bg-amber-100 text-amber-800 border-amber-200",
    danger: "bg-red-100 text-red-800 border-red-200",
  };
  const label = risk.charAt(0).toUpperCase() + risk.slice(1);
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-medium ${styles[risk]}`}
      role="status"
    >
      {label}
    </span>
  );
}

function InputSection({
  onAnalyze,
  loading,
}: {
  onAnalyze: (text: string) => void;
  loading: boolean;
}) {
  const [text, setText] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (text.trim()) onAnalyze(text.trim());
  }

  return (
    <section className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <label htmlFor="tos-input" className="sr-only">
          Paste Terms of Service text
        </label>
        <textarea
          id="tos-input"
          value={text}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setText(e.target.value)}
          placeholder="Paste your Terms of Service text here…"
          rows={10}
          className="w-full resize-y rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-800 placeholder-slate-400 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-500/20"
          disabled={loading}
        />
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                Analyzing…
              </>
            ) : (
              "Analyze text"
            )}
          </button>
        </div>
      </form>
    </section>
  );
}

function ResultsSection({ data }: { data: AnalysisResponse }) {
  const { risk_summary, clauses } = data;

  return (
    <section className="mx-auto max-w-4xl px-4 pb-16 sm:px-6">
      <div className="space-y-8">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Risk Summary</h2>
          <div className="mt-3 flex flex-wrap gap-4">
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2">
              <span className="text-sm font-medium text-red-800">Danger</span>
              <span className="rounded-full bg-red-200 px-2 py-0.5 text-sm font-semibold text-red-900">
                {risk_summary.danger}
              </span>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2">
              <span className="text-sm font-medium text-amber-800">Watch</span>
              <span className="rounded-full bg-amber-200 px-2 py-0.5 text-sm font-semibold text-amber-900">
                {risk_summary.watch}
              </span>
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2">
              <span className="text-sm font-medium text-emerald-800">Safe</span>
              <span className="rounded-full bg-emerald-200 px-2 py-0.5 text-sm font-semibold text-emerald-900">
                {risk_summary.safe}
              </span>
            </div>
          </div>
        </div>

        <div>
          <h2 className="text-lg font-semibold text-slate-900">Clause Table</h2>
          <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-slate-200">
              <thead>
                <tr className="bg-slate-50">
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600"
                  >
                    Clause
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600"
                  >
                    Risk
                  </th>
                  <th
                    scope="col"
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-600"
                  >
                    Anomaly Score
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {clauses.map((clause) => (
                  <tr key={clause.id} className="align-top">
                    <td className="px-4 py-3 text-sm text-slate-800">
                      {clause.text}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge risk={clause.risk} />
                    </td>
                    <td className="px-4 py-3 font-mono text-sm text-slate-600">
                      {clause.anomaly_score.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);

  async function handleAnalyze(text: string) {
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeText(text);
      setResult(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <InputSection onAnalyze={handleAnalyze} loading={loading} />
      {loading && (
        <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
          <div className="flex flex-col items-center gap-4 rounded-xl border border-slate-200 bg-white p-12 shadow-sm">
            <Loader2
              className="h-10 w-10 animate-spin text-slate-400"
              aria-hidden
            />
            <p className="text-sm font-medium text-slate-600">
              Analyzing your Terms of Service…
            </p>
            <p className="text-xs text-slate-500">
              This may take a few seconds.
            </p>
          </div>
        </div>
      )}
      {!loading && result && <ResultsSection data={result} />}
    </div>
  );
}
