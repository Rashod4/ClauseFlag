import { useState } from 'react';
import type { AnalysisResponse, Clause } from './mockApi';
import { analyzeText } from './mockApi';

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
    const [input, setInput] = useState('');
    const [filter, setFilter] = useState<RiskFilter>('all');
    const [result, setResult] = useState<AnalysisResponse | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleAnalyze = async () => {
        if (!input.trim()) {
            setError('Paste a terms of service or privacy policy first.');
            return;
        }
        setError(null);
        setIsAnalyzing(true);
        try {
            const data = await analyzeText(input);
            setResult(data);
        } catch (e) {
            console.error(e);
            const message =
                e instanceof Error ? e.message : 'Unknown error during analysis.';
            if (message.includes('GEMINI_API_KEY')) {
                setError(
                    'Your Gemini API key is not configured correctly. Check .env.local and restart the dev server.',
                );
            } else {
                setError(
                    `Something went wrong while analyzing: ${message} (see console for details).`,
                );
            }
        } finally {
            setIsAnalyzing(false);
        }
    };

    const filteredClauses =
        result && filter !== 'all'
            ? result.clauses.filter((c) => c.risk === filter)
            : result?.clauses ?? [];

    return (
        <div className="min-h-screen bg-slate-950 text-slate-50">
            <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8 md:flex-row md:py-12">
                <section className="md:w-1/2 space-y-4">
                    <header className="space-y-2">
                        <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
                            ClauseFlag
                        </h1>
                        <p className="text-sm text-slate-300 md:text-base">
                            Paste a Terms of Service or privacy policy to flag risky clauses
                            as <span className="font-medium text-emerald-300">Safe</span>,{' '}
                            <span className="font-medium text-amber-300">Watch</span>, or{' '}
                            <span className="font-medium text-rose-300">Danger</span>.
                        </p>
                    </header>

                    <div className="space-y-2">
                        <label
                            htmlFor="tos-input"
                            className="text-sm font-medium text-slate-200"
                        >
                            Contract or policy text
                        </label>
                        <textarea
                            id="tos-input"
                            className="h-64 w-full resize-none rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-50 shadow-sm outline-none placeholder:text-slate-500 focus:border-sky-400 focus:ring-1 focus:ring-sky-400"
                            placeholder="Paste the full text of a terms of service or privacy policy here..."
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                        />
                    </div>

                    {error && (
                        <p className="text-sm font-medium text-rose-400" role="alert">
                            {error}
                        </p>
                    )}

                    <div className="flex items-center justify-between gap-3">
                        <button
                            type="button"
                            onClick={handleAnalyze}
                            disabled={isAnalyzing}
                            className="inline-flex items-center justify-center rounded-md bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 shadow-sm transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {isAnalyzing ? 'Analyzing…' : 'Analyze clauses'}
                        </button>

                    </div>
                </section>

                <section className="md:w-1/2 space-y-4">
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
        </div>
    );
}

function SummaryPill(props: {
    label: string;
    value: number;
    color: string;
}) {
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
            <p className="mb-2 text-sm text-slate-50">{clause.text}</p>
            <p className="text-xs text-slate-300">{clause.explanation}</p>
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
