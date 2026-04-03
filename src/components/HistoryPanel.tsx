import { useState, useEffect } from 'react';
import * as ScrollArea from '@radix-ui/react-scroll-area';
import { fetchHistory } from '../apiClient';
import type { HistoryEntry } from '../apiClient';

interface HistoryPanelProps {
  /** Increment to trigger a refetch (e.g. after a new analysis completes). */
  refreshKey: number;
  /** Called when the user clicks a history entry. */
  onSelect: (analysisId: string) => void;
  /** The analysis ID currently displayed in the results panel. */
  activeAnalysisId?: string;
}

export default function HistoryPanel({
  refreshKey,
  onSelect,
  activeAnalysisId,
}: HistoryPanelProps) {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchHistory()
      .then((entries) => {
        if (!cancelled) setHistory(entries);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/60">
      {/* Collapsible header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-slate-200 hover:text-slate-50"
      >
        <span className="flex items-center gap-2">
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
            />
          </svg>
          My History
          {history.length > 0 && (
            <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[11px] tabular-nums text-slate-400">
              {history.length}
            </span>
          )}
        </span>
        <svg
          className={`h-4 w-4 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="m19.5 8.25-7.5 7.5-7.5-7.5"
          />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-slate-800">
          {loading && (
            <div className="px-4 py-6 text-center text-xs text-slate-400">
              Loading history…
            </div>
          )}

          {!loading && history.length === 0 && (
            <div className="px-4 py-6 text-center text-xs text-slate-400">
              No analyses saved yet. Analyses you run while logged in will
              appear here.
            </div>
          )}

          {!loading && history.length > 0 && (
            <ScrollArea.Root className="max-h-72 overflow-hidden">
              <ScrollArea.Viewport className="h-full w-full">
                <ul className="divide-y divide-slate-800">
                  {history.map((entry) => {
                    const entryAnalysisId =
                      entry.analysis_result?.analysis_id ?? null;
                    return (
                      <HistoryItem
                        key={entry.id}
                        entry={entry}
                        active={
                          !!entryAnalysisId &&
                          entryAnalysisId === activeAnalysisId
                        }
                        onSelect={() => {
                          if (entryAnalysisId) onSelect(entryAnalysisId);
                        }}
                      />
                    );
                  })}
                </ul>
              </ScrollArea.Viewport>
              <ScrollArea.Scrollbar
                className="flex w-2.5 touch-none select-none border-l border-l-transparent p-[1px]"
                orientation="vertical"
              >
                <ScrollArea.Thumb className="relative flex-1 rounded-full bg-slate-600" />
              </ScrollArea.Scrollbar>
            </ScrollArea.Root>
          )}
        </div>
      )}
    </div>
  );
}

function HistoryItem({
  entry,
  active,
  onSelect,
}: {
  entry: HistoryEntry;
  active: boolean;
  onSelect: () => void;
}) {
  const rs = entry.analysis_result?.risk_summary;

  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        className={[
          'w-full px-4 py-3 text-left transition',
          active
            ? 'bg-sky-950/50 ring-1 ring-inset ring-sky-500/30'
            : 'hover:bg-slate-800/60',
        ].join(' ')}
      >
        <p
          className="truncate text-sm text-slate-200"
          title={entry.url ?? 'Text input'}
        >
          {entry.url ? prettifyUrl(entry.url) : 'Pasted text'}
        </p>

        {rs && (
          <div className="mt-1 flex gap-2 text-[11px]">
            <span className="text-emerald-400">{rs.safe} safe</span>
            <span className="text-amber-400">{rs.watch} watch</span>
            <span className="text-rose-400">{rs.danger} danger</span>
          </div>
        )}

        <p className="mt-0.5 text-[11px] text-slate-500">
          {new Date(entry.created_at).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          })}
        </p>
      </button>
    </li>
  );
}

function prettifyUrl(url: string): string {
  try {
    const u = new URL(url);
    return u.hostname + u.pathname;
  } catch {
    return url;
  }
}
