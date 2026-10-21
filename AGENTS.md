# Repository working instructions

Before maintenance, deployment, or changing administrator workflows, read
`docs/ADMIN_RUNBOOK.md` and the task-relevant implementation. Consult
`docs/maintenance/MAINTENANCE_PLAN.md` before structural cleanup. These files are persistent
references, not substitutes for checking actual code or live state.

- Preserve user edits. Distinguish production, local working databases, immutable
  baselines, generated artifacts, and backups before changing files.
- Keep documentation current in the same change when behavior, menu choices,
  configuration, credentials locations, or operational procedures change.
- Never put actual credentials in documentation, source control, logs, or packages.
- Git push is not production deployment. Use the reviewed helper workflow where
  supported; verify the affected feature after publication.
- Do not replace a live database with a local copy or delete backups as incidental
  cleanup. Inventory first and follow the user's agreed scope and retention plan.
- Use focused commits and relevant tests for behavior changes. For documentation,
  check commands, paths, links and claims; do not run mutating examples to validate
  prose. Separate findings from proposed work and verified production facts.
- Give standalone Python programs/modules concise purpose docstrings. Describe
  invocation and material side effects where relevant. Document non-obvious
  function/class contracts; use equivalent comments in JavaScript/PowerShell.
  Inline comments should explain reasons, constraints or safeguards, not narrate
  obvious code. Avoid blanket boilerplate or unrelated docstring churn.
- User authorization determines scope. These instructions do not add a separate
  approval step for already authorized work. Do not claim deployment or scheduled
  execution succeeded without evidence.
