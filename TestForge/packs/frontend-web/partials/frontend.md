# Frontend Web Pack Rules (stub)

- Batch 2 will add Vitest/RTL/MSW, Playwright a11y/visual, and Playwright Agents templates.
- Selector priority: role → label → testid → stable text → CSS → XPath.
- No `sleep`/fixed waits; use web-first assertions.
- Visual regression must use a blocking gate; don't trust green unit/E2E alone.
- Accessibility: axe-core on every PR for critical pages.
