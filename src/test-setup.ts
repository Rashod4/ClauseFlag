import '@testing-library/jest-dom/vitest';

class MockStorage implements Storage {
  private store: Record<string, string> = {};

  get length() {
    return Object.keys(this.store).length;
  }

  clear() {
    this.store = {};
  }

  getItem(key: string): string | null {
    return this.store[key] ?? null;
  }

  key(index: number): string | null {
    return Object.keys(this.store)[index] ?? null;
  }

  removeItem(key: string): void {
    delete this.store[key];
  }

  setItem(key: string, value: string): void {
    this.store[key] = String(value);
  }
}

const storage = new MockStorage();

Object.defineProperty(globalThis, 'localStorage', { value: storage, writable: true, configurable: true });
Object.defineProperty(window, 'localStorage', { value: storage, writable: true, configurable: true });
