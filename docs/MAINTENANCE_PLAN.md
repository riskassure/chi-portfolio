# Maintenance assessment plan

Status: documentation baseline committed. A first-pass static inventory and
dependency review is recorded in [the maintenance assessment](MAINTENANCE_ASSESSMENT.md).
The documentation index and current-workflow pointers have been added. Code
implementation and file-retention decisions remain pending.
No file removal, code refactoring, dependency change or deployment is part of this
initial documentation change.

## Sequence

1. Verify and review the admin runbook against actual workflows.
2. Inventory production entry points, local tools, reusable services, tests,
   configuration, generated data, historical scripts, and backups. Identify
   callers and operational dependencies before calling anything unused.
3. Record findings with file references, concrete problem, proposed change,
   expected benefit, risk, verification, and rollback approach.
4. Prioritize small changes that reduce maintenance burden. Separate structural
   cleanup from measured performance problems; measure before optimizing.
5. Implement one agreed area at a time, preserving behavior and user data.
6. Test the affected behavior, update documentation, and commit focused changes.
   Deploy only applicable production changes and verify them separately.
7. Agree on retention and archive/delete candidates separately from code cleanup.

## Candidates to investigate (not established defects)

The owner confirms that mathematics already underwent extensive modularization
and simplification. Keep further math restructuring low priority, review its
history first, and require a concrete maintenance problem or measured bottleneck.
Large files alone do not establish a need for another refactor.

- Older Spotify export/history tools versus the current top-track workflow.
- Repeated preparation, staging, validation and publication code.
- Large route modules mixing HTTP handling and database operations.
- Multiple database snapshots, review scripts and generated artifacts.
- Conflicting or outdated instructions across existing Markdown guides.

## Assessment deliverable

A table of proposed changes, ordered by value and risk, with evidence and a
recommended first batch. Include an explicit keep/archive/remove classification
only after checking usage. Do not infer that a file is disposable from age, size,
name, or its presence in `dist`.

## Pending operational checks

- Inspect a real automatic Spotify task run; current evidence covers an initial
  manual production refresh and creation of an enabled daily task only.
- Identify backup retention needs and plan a restoration exercise on an isolated
  copy. Do not test recovery by restoring over the live site.
