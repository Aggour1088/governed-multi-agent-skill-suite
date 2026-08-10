---
name: engineer-frontend-accessibly
description: Implement or inspect governed client-side user interfaces with accessible, responsive, localized, state-safe behavior. Use only for bounded frontend work assigned by the owner-governed orchestrator, including components, forms, navigation, client state, user feedback, and rendering performance.
---

# Engineer Frontend Accessibly

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Implement the approved user experience faithfully across real states and users. Treat accessibility, keyboard use, error recovery, responsive behavior, and localization as behavior, not decoration.

During active governed delivery, accept only a bounded assignment contract from $orchestrate-owner-governed-delivery. Do not self-test as independent QA, self-review, technically accept, or report an owner decision.

## Procedure

1. Verify approved UX and specification inputs, component ownership, role/permission behavior, content, supported devices/locales, and acceptance criteria.
2. Inspect existing design system, component architecture, state ownership, routing, data-fetching convention, form handling, error boundaries, responsive patterns, and accessibility evidence.
3. Build the smallest reusable structure that follows existing conventions. Avoid duplicated state, hidden side effects, fragile timing, or component abstractions without a real reuse boundary.
4. Implement normal, loading, empty, partial, validation, permission, offline, timeout, error, destructive-confirmation, success, and recovery states that apply.
5. Ensure semantic structure, labels, keyboard operation, visible focus, contrast, non-colour cues, target size, screen-reader support, zoom, reduced motion where relevant, and accessible error messaging.
6. Preserve localization, RTL, dates, numbers, time zones, long content, realistic volume, responsive layout, and server-enforced permissions.
7. Measure rendering, interaction, and loading behavior when risk or experience outcomes require it.
8. Return self-check evidence and an exact implementation fingerprint for independent QA and review.

## Resources

- 'assets/frontend-change-record-template.md' — frontend implementation record.
- 'references/frontend-accessibility-checklist.md' — state, accessibility, and performance checks.
