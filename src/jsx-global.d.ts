/**
 * Fallback JSX/React types when @types/react is not yet installed (e.g. before `npm install`).
 * Run `npm install` so React's full types are used; this file ensures the project type-checks either way.
 */
declare global {
  namespace React {
    interface FormEvent<T = Element> {
      preventDefault(): void;
      currentTarget: EventTarget & T;
    }
    interface ChangeEvent<T = Element> {
      target: EventTarget & T;
    }
  }

  namespace JSX {
    interface Element extends unknown {}
    interface ElementClass {
      render(): unknown;
    }
    interface ElementAttributesProperty {
      props: unknown;
    }
    interface IntrinsicAttributes {
      key?: string | number | null;
    }
    interface IntrinsicClassAttributes<T> {
      ref?: unknown;
    }
    interface IntrinsicElements {
      [tag: string]: Record<string, unknown> | null;
    }
  }
}

export {};
