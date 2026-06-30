// frontend/math/mathjax_audit.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";

let latestAuditRows = [];

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("auditManualBtn")?.addEventListener("click", auditManualList);
    document.getElementById("auditAllBtn")?.addEventListener("click", auditAllConcepts);
    document.getElementById("copyCsvBtn")?.addEventListener("click", copyLatestCsv);
});

async function auditManualList() {
    const raw = document.getElementById("manualSlugsInput")?.value || "";

    const identifiers = raw
        .split(/\r?\n/)
        .map(x => x.trim())
        .filter(Boolean);

    if (identifiers.length === 0) {
        setAuditStatus("Paste at least one slug or ID first.", "error");
        return;
    }

    const conceptRefs = identifiers.map(identifier => ({
        id: null,
        slug: identifier,
        title: identifier,
        identifier
    }));

    await runAudit(conceptRefs);
}

async function auditAllConcepts() {
    try {
        setAuditStatus("Loading audit concept list...", "info");

        const response = await fetch(`${API_ENDPOINT}/admin/math/concepts/audit-list`, {
            credentials: "include"
        });

        const json = await response.json();

        if (!response.ok || json.status !== "success") {
            throw new Error(json.message || "Unable to load audit-list endpoint.");
        }

        const rows = Array.isArray(json.data) ? json.data : [];

        const conceptRefs = rows
            .map(row => ({
                id: row.id || null,
                slug: row.slug || "",
                title: row.title || row.slug || row.id || "Untitled concept",
                identifier: row.slug || row.id
            }))
            .filter(row => row.identifier);

        if (conceptRefs.length === 0) {
            throw new Error("Audit-list endpoint returned zero concepts.");
        }

        await runAudit(conceptRefs);

    } catch (err) {
        console.warn(err);
        setAuditStatus(
            `Full crawl is not ready yet: ${err.message}. Use manual slug mode for now.`,
            "error"
        );
    }
}

async function runAudit(conceptRefs) {
    latestAuditRows = [];
    renderAuditRows();

    const total = conceptRefs.length;
    let checked = 0;
    let failed = 0;

    setAuditStatus(`Starting audit for ${total} concept(s)...`, "info");

    for (const ref of conceptRefs) {
        checked += 1;

        setAuditStatus(
            `Auditing ${checked} of ${total}: ${ref.title || ref.slug || ref.id}`,
            "info"
        );

        try {
            const concept = await fetchConcept(ref.identifier);
            const rows = await auditConcept(concept);

            latestAuditRows.push(...rows);
            renderAuditRows();

            // Small pause keeps the browser responsive during bigger runs.
            await sleep(25);

        } catch (err) {
            failed += 1;

            latestAuditRows.push({
                command: "[FETCH_OR_RENDER_ERROR]",
                count: 1,
                concept_id: ref.id || "",
                slug: ref.slug || ref.identifier || "",
                title: ref.title || "",
                example: err.message || String(err),
                concept_url: ""
            });

            renderAuditRows();
        }
    }

    const issueConceptCount = new Set(
        latestAuditRows
            .filter(row => row.command !== "[FETCH_OR_RENDER_ERROR]")
            .map(row => row.slug || row.concept_id)
    ).size;

    setAuditStatus(
        `Done. Checked ${checked}; concepts with visible macro issues: ${issueConceptCount}; fetch/render failures: ${failed}.`,
        latestAuditRows.length > 0 ? "warn" : "success"
    );
}

async function fetchConcept(identifier) {
    const response = await fetch(
        `${API_ENDPOINT}/math/concepts/${encodeURIComponent(identifier)}`
    );

    const json = await response.json();

    if (!response.ok || json.status !== "success") {
        throw new Error(json.message || `Failed to fetch concept ${identifier}.`);
    }

    return json.data;
}

async function auditConcept(concept) {
    const canvas = document.getElementById("auditCanvas");

    if (!canvas) {
        throw new Error("Audit canvas was not found.");
    }

    const rawTex = window.MathCmsRender.getDisplayTex(concept);
    const html = window.MathCmsRender.prepareConceptHtml(rawTex, {
        apiEndpoint: API_ENDPOINT
    });

    canvas.innerHTML = html;

    let leftovers = [];

    if (
        window.MathCmsMathJax &&
        typeof window.MathCmsMathJax.typesetElement === "function"
    ) {
        leftovers = await window.MathCmsMathJax.typesetElement(canvas, {
            page: "mathjax_audit",
            concept_id: concept.id || null,
            slug: concept.slug || null,
            title: concept.title || null
        });
    } else {
        throw new Error("MathCmsMathJax.typesetElement is not available.");
    }

    return leftovers.map(item => ({
        command: item.command,
        count: item.count,
        concept_id: concept.id || "",
        slug: concept.slug || "",
        title: concept.title || "",
        example: (item.examples || [])[0] || "",
        concept_url: concept.slug
            ? `concept.html?slug=${encodeURIComponent(concept.slug)}`
            : concept.id
                ? `concept.html?id=${encodeURIComponent(concept.id)}`
                : ""
    }));
}

function renderAuditRows() {
    const body = document.getElementById("auditResultsBody");
    const summary = document.getElementById("auditSummary");

    if (!body || !summary) return;

    body.innerHTML = "";

    if (latestAuditRows.length === 0) {
        summary.innerText = "No unresolved visible macros found so far.";
        return;
    }

    const commandCounts = new Map();

    latestAuditRows.forEach(row => {
        commandCounts.set(
            row.command,
            (commandCounts.get(row.command) || 0) + Number(row.count || 0)
        );
    });

    const commandSummary = Array.from(commandCounts.entries())
        .sort((a, b) => b[1] - a[1])
        .map(([command, count]) => `${command}: ${count}`)
        .join(" | ");

    summary.innerText = `${latestAuditRows.length} result row(s). ${commandSummary}`;

    latestAuditRows
        .slice()
        .sort((a, b) => {
            const byCommand = String(a.command).localeCompare(String(b.command));
            if (byCommand !== 0) return byCommand;

            return String(a.slug || a.title).localeCompare(String(b.slug || b.title));
        })
        .forEach(row => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;"><code>${escapeHtml(row.command)}</code></td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">${escapeHtml(row.count)}</td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">${renderConceptLink(row)}</td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;"><code>${escapeHtml(row.slug)}</code></td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">${escapeHtml(row.example)}</td>
            `;

            body.appendChild(tr);
        });
}

function renderConceptLink(row) {
    const title = escapeHtml(row.title || row.slug || row.concept_id || "Open concept");

    if (!row.concept_url) {
        return title;
    }

    return `<a href="${escapeHtml(row.concept_url)}" target="_blank" rel="noopener noreferrer">${title}</a>`;
}

async function copyLatestCsv() {
    if (latestAuditRows.length === 0) {
        setAuditStatus("No audit rows to copy.", "error");
        return;
    }

    const csv = rowsToCsv(latestAuditRows);

    try {
        await navigator.clipboard.writeText(csv);
        setAuditStatus("Copied audit CSV to clipboard.", "success");
    } catch (err) {
        console.warn(err);
        setAuditStatus("Unable to copy CSV automatically. Check console for CSV output.", "error");
        console.log(csv);
    }
}

function rowsToCsv(rows) {
    const headers = [
        "command",
        "count",
        "concept_id",
        "slug",
        "title",
        "example",
        "concept_url"
    ];

    const lines = [headers.join(",")];

    rows.forEach(row => {
        lines.push(headers.map(header => csvCell(row[header])).join(","));
    });

    return lines.join("\n");
}

function csvCell(value) {
    const text = String(value ?? "");

    if (/[",\n\r]/.test(text)) {
        return `"${text.replace(/"/g, '""')}"`;
    }

    return text;
}

function setAuditStatus(message, type = "info") {
    const status = document.getElementById("auditStatus");

    if (!status) return;

    const colors = {
        info: "#334155",
        success: "#047857",
        warn: "#92400e",
        error: "#b91c1c"
    };

    status.style.color = colors[type] || colors.info;
    status.innerText = message;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}