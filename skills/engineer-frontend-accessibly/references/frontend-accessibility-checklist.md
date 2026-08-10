# Frontend Accessibility Checklist

## Structure and state

- Keep state ownership clear and avoid copying server state without a reason.
- Handle normal, loading, empty, partial, invalid, permission, error, offline, timeout, success, and recovery states.
- Preserve safe user input after recoverable failure.
- Use server-derived authorization as the source of truth.

## Inclusive interaction

- Use semantic elements, labels, keyboard access, visible focus, logical order, accessible names, contrast, non-colour cues, target size, and readable error messages.
- Test zoom, assistive technology, responsive layout, long content, realistic data volume, mobile/tablet/desktop, locale, RTL, date, number, and time-zone behavior.

## Performance

- Measure meaningful loading, rendering, and interaction paths before optimizing.
- Avoid expensive effects, waterfalls, duplicated fetches, unnecessary client state, and unbounded lists where data volume demands a strategy.
