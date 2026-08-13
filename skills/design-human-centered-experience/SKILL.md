---
name: design-human-centered-experience
description: Define clear, accessible, ethical, and owner-governable user experiences before implementation. Use when an approved or in-review feature affects screens, navigation, workflows, forms, dashboards, settings, reports, permissions, states, localization, responsive behavior, or UX acceptance outcomes.
---

# Design Human-Centered Experience

## Direct invocation boundary

This procedure may modify a governed project only after the orchestrator supplies a validated assignment contract. If invoked directly without that contract, provide only a bounded read-only consultation, return control to `$orchestrate-owner-governed-delivery`, and do not modify a project, accept work, release, or communicate an owner decision. Do not call a direct or sequential pass independent unless a trusted host attests distinct principals; otherwise label it `separate-pass-not-independent`. This behavioral gate does not itself create host-level access control.

Design the experience around real user jobs, safe decisions, and recovery. Use human factors to reduce confusion and cognitive load; never use psychology to manipulate, pressure, or conceal.

Do not invent business scope. Return to $shape-feature-foundation when a proposed journey changes owner-approved intent.

## Establish the experience foundation

1. Inspect current navigation, terminology, role model, data volume, devices, locales, design patterns, accessibility evidence, and relevant journey.
2. Define each user role's job, trigger, knowledge needed, shortest safe path, likely error, confirmation of success, and next action.
3. Choose navigation and information hierarchy by user goal, not database structure or implementation convenience.
4. Define normal, first-use, empty, loading, partial, invalid, error, permission, offline, timeout, destructive-confirmation, success, correction, archived, and recovery states that apply.
5. Design a safe owner operating experience for legitimate business controls: scope, values, limits, dependencies, effective date, preview, impact, approval, history, and recovery.
6. Keep technical controls, secrets, source-code concepts, database access, and infrastructure commands outside ordinary owner UI.
7. Specify clear language, responsive behavior, keyboard and assistive access, contrast, focus, non-colour cues, realistic names and volumes, dates, numbers, time zones, RTL, and localization requirements.
8. Define measurable experience outcomes and testable UX acceptance criteria.

## Validate before implementation

Use evidence or proportional research when it could alter a material design decision. Prefer accessible, predictable patterns over novelty. Show the owner a small number of consequential decisions and explain them in plain language.

Create 'ux-foundation.md' from 'assets/ux-foundation-template.md' for complex journeys. Link it to the Feature Foundation and preserve its fingerprint in downstream artifacts.

Treat a material UX decision as a Foundation change when it alters role access, workflow, business rule, scope, or accepted outcome. Return it for owner reapproval.

## Handoff

Provide journey, state, content, accessibility, localization, and owner-control requirements to $specify-approved-change and $engineer-frontend-accessibly. Request the UI/UX audit mode from $assure-quality-systematically when implementation needs independent visual and usability evidence.

## V2 contract and evidence boundary

Route this work through `$using-governed-suite` and the current v2 contract. Classify material statements as **Verified**, **Reproducible**, **Reported**, **Inferred**, **Unknown**, or **Failed**. Only an allowed E2+ host or CI receipt may support **Verified**; a screenshot or design opinion remains **Reported** or **Reproducible**. Stop if the approved user outcome, accessibility evidence, or scope is missing or stale.

## Resources

- 'assets/ux-foundation-template.md' — complex-experience artifact.
- 'references/human-centered-experience-checklist.md' — experience and ethical-human-factors checks.
