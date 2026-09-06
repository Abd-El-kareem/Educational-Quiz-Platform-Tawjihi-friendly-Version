---
name: surgical-editing
description: Perform minimal, safe, test-driven modifications to an existing codebase without breaking unrelated functionality.
---

# Skill: Surgical Feature Editing

## Purpose

Apply targeted modifications to an existing software project while preserving all existing functionality, architecture, coding conventions, and behavior that are outside the requested change.

This skill is for **editing an existing codebase**, not redesigning or rebuilding it.

---

## 1. Core Principles

### Surgical Scope

* Modify **only what is necessary** to implement the requested change.
* Do not refactor unrelated working code.
* Do not reformat surrounding code.
* Do not rewrite existing comments unless they are directly affected.
* Do not rename unrelated variables, functions, classes, files, or modules.
* Do not introduce new abstractions unless they are genuinely required.
* Do not add features that were not requested.

### Preserve Existing Behavior

Before making changes, identify existing behavior that could be affected.

The modification must:

* Preserve all unrelated functionality.
* Preserve existing APIs and interfaces unless the requested feature explicitly requires changes.
* Preserve existing database behavior unless schema changes are necessary.
* Avoid regressions.

### Match the Existing Codebase

Follow the project's existing:

* coding style
* naming conventions
* directory structure
* architectural patterns
* error-handling patterns
* testing conventions
* dependency choices

Do not "improve" existing code simply because a different approach would be preferable.

---

## 2. Think Before Coding

Before editing:

1. Read and understand the relevant project structure.
2. Read `PROJECT_MAP.md` if it exists.
3. Identify the exact files and components likely to be affected.
4. Identify dependencies between the requested feature and existing functionality.
5. State your assumptions explicitly.
6. Identify ambiguities or missing requirements.

### Ambiguity Rule

If an ambiguity could materially affect the architecture, implementation, data model, user experience, or existing behavior:

**Stop and ask for clarification.**

Do not silently invent requirements.

If the ambiguity is minor and has an obvious, low-risk interpretation, state the assumption and proceed.

---

## 3. Impact Analysis

Before modifying code, determine:

* Which files need to change.
* Which existing components will be reused.
* Whether a database/schema change is required.
* Whether API endpoints need modification or creation.
* Whether templates/UI need modification.
* Whether JavaScript behavior needs modification.
* Whether dependencies need to be added or changed.
* Which existing tests could be affected.
* Which new tests are required.

Prefer the **smallest possible change surface**.

Do not modify files merely because they are related conceptually. Modify them only when the implementation actually requires it.

---

## 4. Dependency Discipline

If the requested feature requires a new dependency:

1. Determine the current date/time using the available system tools.
2. Check the dependency's official documentation/repository.
3. Use the latest appropriate **stable, non-deprecated** version compatible with the project.
4. Verify compatibility with the project's existing stack.
5. Avoid adding a dependency when the existing stack can solve the problem cleanly.

Do not upgrade unrelated dependencies.

Do not perform dependency upgrades merely as maintenance unless explicitly requested.

---

## 5. Architecture & Abstraction

### Simplicity First

Use the minimum architecture necessary to implement the feature correctly.

Follow existing architectural boundaries.

If the project uses a service layer, selectors, repositories, utilities, or shared/core modules, integrate with those patterns rather than bypassing them.

### Shared/Core Rule

Use `Shared/Core` only when:

* logic is genuinely shared by multiple components, or
* the project's existing architecture explicitly requires it.

Do **not** create a generic utility or abstraction for logic that will only be used once.

### DRY

Avoid duplicating existing logic.

Before creating new logic, search the project for an existing implementation that can safely be reused.

Do not force unrelated code into a shared abstraction merely to satisfy DRY.

---

## 6. Implementation Protocol

Implement the change in the smallest logical increments.

For each change:

1. Make the smallest required modification.
2. Preserve the surrounding code.
3. Follow existing conventions.
4. Add only the necessary supporting code.
5. Avoid speculative functionality.
6. Keep the implementation easy to remove or modify later.

If a requested feature can be implemented without changing the existing architecture, prefer that approach.

---

## 7. Testing — Goal-Driven Development

Convert the requested modification into explicit **verifiable goals**.

For example:

> **Goal:** Users can perform X, and the system produces Y without affecting existing behavior.

Then define tests that prove the goal.

### TDD When Practical

For new behavior:

1. Write the test describing the desired behavior.
2. Confirm that the test fails for the expected reason.
3. Implement the minimum code required.
4. Confirm that the test passes.
5. Run relevant existing tests.

Do not artificially force TDD when the project's existing testing architecture makes it impractical; maintain the same testing conventions already used by the project.

### Regression Protection

After implementation:

* Run the new tests.
* Run affected existing tests.
* Run the broader test suite when practical.
* Investigate failures rather than ignoring them.

Never declare the feature complete while known regressions remain unexplained.

---

## 8. Logging

Add logging only where it provides meaningful operational value.

Follow the project's existing logging architecture.

Logging must:

* avoid sensitive information
* avoid excessive verbosity
* avoid unnecessary performance overhead
* use appropriate log levels
* follow existing conventions

Do not introduce an entirely new logging framework for a small feature unless explicitly required.

---

## 9. Cleanup Rule

Clean up **only the consequences of your own changes**.

If your modification causes:

* an import to become unused
* a function to become orphaned
* a variable to become unnecessary
* a route to become obsolete
* a component to become unreachable

remove or update it when appropriate.

### Do Not Clean Existing Debt

Do not remove or refactor pre-existing:

* dead code
* unused imports
* deprecated patterns
* technical debt
* inconsistent formatting
* unrelated comments

unless the requested feature directly requires addressing them.

---

## 10. State Synchronization

After implementation, update `PROJECT_MAP.md`.

Update only the sections affected by the modification, including where relevant:

* `[TECH_STACK]`
* `[SYSTEM_FLOW]`
* `[ARCHITECTURE]`
* `[ORPHANS & PENDING]`

Record:

* new components
* changed dependencies
* architectural changes
* important data-flow changes
* remaining limitations
* intentionally deferred work

Do not turn `PROJECT_MAP.md` into a changelog unless the existing project structure already uses it that way.

---

## 11. Feature Creep Prevention

Reject changes that are outside the requested scope.

Do not add:

* unrelated UI improvements
* additional configuration
* speculative extensibility
* unnecessary abstraction
* unrelated refactoring
* extra APIs
* additional features
* "nice-to-have" functionality

If an additional change appears genuinely necessary for correctness or security, explain why before making it.

---

## 12. Final Verification

Before declaring the modification complete, verify:

### Functional

* [ ] Requested behavior works.
* [ ] Existing functionality still works.
* [ ] Edge cases relevant to the feature are handled.
* [ ] Error states are handled appropriately.

### Technical

* [ ] Tests pass.
* [ ] No unnecessary dependencies were added.
* [ ] No unrelated files were modified.
* [ ] No unrelated refactoring was performed.
* [ ] No new dead code was introduced.
* [ ] Logging follows project conventions.
* [ ] `PROJECT_MAP.md` is synchronized.

### Scope

* [ ] No feature creep.
* [ ] No unnecessary architectural changes.
* [ ] No unrelated cleanup.

---

## 13. Execution Mode

When given a feature request, follow this sequence:

**Understand → Inspect → Analyze Impact → State Assumptions → Identify Ambiguities → Propose Minimal Plan → Wait for Approval → Implement → Test → Regression Check → Synchronize `PROJECT_MAP.md` → Report**

### Important

If the user explicitly asks:

> **"Tell me the plan before building."**

Do **not** implement anything.

Instead, provide:

1. Assumptions.
2. Impact analysis.
3. Proposed files/components to change.
4. Data/API/UI implications.
5. Dependency implications.
6. Testing strategy.
7. Verifiable goals.
8. Risks or unresolved questions.
9. A concise implementation plan.

Then **wait for approval before modifying the codebase**.

When approval is given, execute the approved plan surgically and do not expand its scope without asking.

