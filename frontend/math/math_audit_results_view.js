(() => {

function renderAuditRows(rows) {
    const body = document.getElementById("auditResultsBody");
    const summary = document.getElementById("auditSummary");

    if (!body || !summary) return;

    body.innerHTML = "";

    if (rows.length === 0) {
        summary.innerText =
            "No unresolved visible macros found so far.";
        return;
    }

    const commandCounts = new Map();

    rows.forEach(row => {
        commandCounts.set(
            row.command,
            (commandCounts.get(row.command) || 0)
                + Number(row.count || 0)
        );
    });

    const commandSummary =
        Array.from(commandCounts.entries())
            .sort((a, b) => b[1] - a[1])
            .map(
                ([command, count]) =>
                    `${command}: ${count}`
            )
            .join(" | ");

    summary.innerText =
        `${rows.length} result row(s). ${commandSummary}`;

    rows
        .slice()
        .sort((a, b) => {
            const byCommand =
                String(a.command)
                    .localeCompare(
                        String(b.command)
                    );

            if (byCommand !== 0) {
                return byCommand;
            }

            return String(
                a.slug || a.title
            ).localeCompare(
                String(b.slug || b.title)
            );
        })
        .forEach(row => {
            const tr =
                document.createElement("tr");

            tr.innerHTML = `
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;"><code>${window.MathCmsAuditView.escapeHtml(row.command)}</code></td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">${window.MathCmsAuditView.escapeHtml(row.count)}</td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">${window.MathCmsAuditView.renderConceptLink(row)}</td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;"><code>${window.MathCmsAuditView.escapeHtml(row.slug)}</code></td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">${window.MathCmsAuditView.escapeHtml(row.example)}</td>
            `;

            body.appendChild(tr);
        });
}


window.MathCmsAuditResultsView = {
    renderAuditRows
};

})();
