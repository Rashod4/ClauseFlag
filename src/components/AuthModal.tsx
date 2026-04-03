import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { login, register } from '../apiClient';
import type { AuthResponse } from '../apiClient';

type AuthMode = 'login' | 'register';

interface AuthModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: (auth: AuthResponse) => void;
}

export default function AuthModal({
  open,
  onOpenChange,
  onSuccess,
}: AuthModalProps) {
  const [mode, setMode] = useState<AuthMode>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const reset = () => {
    setUsername('');
    setPassword('');
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const auth = await (mode === 'login'
        ? login(username, password)
        : register(username, password));
      onSuccess(auth);
      onOpenChange(false);
      reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg border border-slate-700 bg-slate-900 p-6 shadow-xl focus:outline-none">
          <Dialog.Title className="text-lg font-semibold text-slate-50">
            {mode === 'login' ? 'Log in' : 'Create account'}
          </Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-slate-400">
            {mode === 'login'
              ? 'Sign in to save your analysis history.'
              : 'Create an account to track your analyses.'}
          </Dialog.Description>

          {/* Login / Register toggle */}
          <div className="mt-4 inline-flex rounded-lg bg-slate-800 p-1 text-sm">
            {(['login', 'register'] as AuthMode[]).map((tab) => (
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
                {tab === 'login' ? 'Log in' : 'Register'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="mt-4 space-y-3">
            <div>
              <label
                htmlFor="auth-username"
                className="mb-1 block text-xs font-medium text-slate-300"
              >
                Username
              </label>
              <input
                id="auth-username"
                type="text"
                required
                minLength={3}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-50 outline-none placeholder:text-slate-500 focus:border-sky-400 focus:ring-1 focus:ring-sky-400"
                placeholder="Enter username"
              />
            </div>
            <div>
              <label
                htmlFor="auth-password"
                className="mb-1 block text-xs font-medium text-slate-300"
              >
                Password
              </label>
              <input
                id="auth-password"
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-50 outline-none placeholder:text-slate-500 focus:border-sky-400 focus:ring-1 focus:ring-sky-400"
                placeholder="Enter password"
              />
            </div>

            {error && (
              <div className="rounded-md border border-rose-500/30 bg-rose-950/40 px-3 py-2 text-xs text-rose-200">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 shadow-sm transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading
                ? 'Please wait…'
                : mode === 'login'
                  ? 'Log in'
                  : 'Create account'}
            </button>
          </form>

          <Dialog.Close asChild>
            <button
              type="button"
              className="absolute right-3 top-3 rounded-md p-1 text-slate-400 hover:text-slate-200"
              aria-label="Close"
            >
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                <path
                  d="M11.782 4.032a.575.575 0 0 0-.814-.814L7.5 6.687 4.032 3.218a.575.575 0 1 0-.814.814L6.687 7.5l-3.469 3.468a.575.575 0 0 0 .814.814L7.5 8.313l3.468 3.469a.575.575 0 0 0 .814-.814L8.313 7.5l3.469-3.468Z"
                  fill="currentColor"
                  fillRule="evenodd"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
