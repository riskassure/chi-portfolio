# Website documentation

Start with the [admin runbook](ADMIN_RUNBOOK.md) for everyday editing,
publication, database copies, backups, credentials and Spotify refresh.
Committing code does not publish it to the website.

## Operating the website

| Guide | Use it for |
| --- | --- |
| [Admin runbook](ADMIN_RUNBOOK.md) | Current operating procedures and recorded deployment status |
| [Content synchronization](../MATH_SYNC.md) | Detailed helper preparation, checks and publication |
| [Travel map](../TRAVEL_MAP.md) | Map editing, reference data, photo bindings and gallery settings |
| [Spotify](../backend/src/services/music/README.md) | Current top-track workflow; older export workflow is labeled separately |
| [Google Photos](../backend/src/services/photography/README.md) | Photo import implementation and setup |
| [Math authoring](../frontend/math/AUTHORING_STANDARDS.md) | Mathematics content conventions |
| [Math frontend](../frontend/math/README.md) | Mathematics frontend implementation notes |

## Maintenance

- [Maintenance plan](MAINTENANCE_PLAN.md): scope, sequence and pending checks.
- [Assessment](MAINTENANCE_ASSESSMENT.md): findings and proposed priorities, not a deletion list.
- [Agent instructions](../AGENTS.md): expectations for future coding sessions.

The math section has already undergone substantial modularization and
simplification, as confirmed by the owner. Review that history before proposing
further changes. File size alone is not a reason to refactor it again.

## Historical and alternative deployment references

| Guide | Context |
| --- | --- |
| [PythonAnywhere first installation](../PYTHONANYWHERE.md) | Initial hosting setup; do not repeat over the live site |
| [Manual update and recovery](../UPDATING_WEBSITE.md) | Older package-based updates and recovery detail; use the runbook for routine updates |
| [Generic deployment preparation](../DEPLOYMENT.md) | Alternative Waitress hosting design, not the current PythonAnywhere setup |

Existing guides remain at their current paths because code and other documents
reference them. Move them only after updating their callers, including deployment
package builders. This index is a repository reference; older deployment archives
may not include the `docs` directory.

Keep procedures synchronized with implementation. Label historical facts and
unverified operational checks explicitly, and never include credential values.
