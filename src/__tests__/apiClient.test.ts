import { describe, it, expect, beforeEach } from 'vitest';
import { getToken, getStoredUser, clearAuth } from '../apiClient';
import type { AuthUser } from '../apiClient';

const TOKEN_KEY = 'clauseflag_token';
const USER_KEY = 'clauseflag_user';

beforeEach(() => {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
});

describe('getToken', () => {
  it('returns null when no token is stored', () => {
    expect(getToken()).toBeNull();
  });

  it('returns the stored token', () => {
    window.localStorage.setItem(TOKEN_KEY, 'my-jwt-token');
    expect(getToken()).toBe('my-jwt-token');
  });
});

describe('getStoredUser', () => {
  it('returns null when no user is stored', () => {
    expect(getStoredUser()).toBeNull();
  });

  it('returns parsed user object', () => {
    const user: AuthUser = { user_id: 'u1', username: 'alice' };
    window.localStorage.setItem(USER_KEY, JSON.stringify(user));
    expect(getStoredUser()).toEqual(user);
  });

  it('returns null for corrupted JSON', () => {
    window.localStorage.setItem(USER_KEY, '{invalid json');
    expect(getStoredUser()).toBeNull();
  });
});

describe('clearAuth', () => {
  it('removes both token and user from localStorage', () => {
    window.localStorage.setItem(TOKEN_KEY, 'token');
    window.localStorage.setItem(
      USER_KEY,
      '{"user_id":"u1","username":"bob"}',
    );

    clearAuth();

    expect(window.localStorage.getItem(TOKEN_KEY)).toBeNull();
    expect(window.localStorage.getItem(USER_KEY)).toBeNull();
  });

  it('does not throw when nothing is stored', () => {
    expect(() => clearAuth()).not.toThrow();
  });
});
