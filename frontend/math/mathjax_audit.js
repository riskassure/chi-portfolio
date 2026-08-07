// frontend/math/mathjax_audit.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";
const AUDIT_VERSION = "mathjax-audit-overflow-v1";

let latestAuditRows = [];

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("auditManualBtn")?.addEventListener("click", auditManualList);
    document.getElementById("auditAllBtn")?.addEventListener("click", auditAllConcepts);
    document.getElementById("auditProblematicBtn")?.addEventListener("click", auditProblematicConcepts);
    document.getElementById("copyCsvBtn")?.addEventListener("click", copyLatestCsv);

    restoreLatestAuditSnapshot();
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

    await runAudit(conceptRefs, {
        mode: "manual",
        persistRun: false
    });
}

async function auditAllConcepts() {
    await auditConceptListMode("all");
}

async function auditProblematicConcepts() {
    await auditConceptListMode("problematic");
}

async function auditConceptListMode(mode) {
    try {
        setAuditStatus(`Loading ${mode} audit concept list...`, "info");

        const response = await fetch(
            `${API_ENDPOINT}/admin/math/concepts/audit-list?mode=${encodeURIComponent(mode)}`,
            {
                credentials: "include"
            }
        );

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

        latestAuditRows = [];
        renderAuditRows();

        if (conceptRefs.length === 0) {
            setAuditStatus(
                json.message || `No concepts returned for ${mode} audit mode.`,
                "success"
            );
            return;
        }

        await runAudit(conceptRefs, {
            mode,
            persistRun: true
        });

    } catch (err) {
        console.warn(err);
        setAuditStatus(
            `Audit ${mode} failed: ${err.message}`,
            "error"
        );
    }
}

async function runAudit(conceptRefs, options = {}) {
    latestAuditRows = [];
    renderAuditRows();
    clearLatestAuditSnapshot();

    const mode = options.mode || "manual";
    const persistRun = Boolean(options.persistRun);

    const total = conceptRefs.length;
    let checked = 0;
    let failed = 0;

    const auditResultPayload = [];

    setAuditStatus(`Starting ${mode} audit for ${total} concept(s)...`, "info");

    for (const ref of conceptRefs) {
        checked += 1;

        setAuditStatus(
            `Auditing ${checked} of ${total}: ${ref.title || ref.slug || ref.id}`,
            "info"
        );

        try {
            const concept =
                await window.MathCmsAuditApi
                    .fetchConcept(
                        API_ENDPOINT,
                        ref.identifier
                    );
            const auditResult = await auditConcept(concept);
            const rows = auditResult.rows || [];

            latestAuditRows.push(...rows);
            renderAuditRows();

            if (persistRun && concept.id) {
                auditResultPayload.push({
                    concept_id: concept.id,
                    rendered_tex_hash: auditResult.rendered_tex_hash || "unknown",
                    status: rows.length > 0 ? "problematic" : "clean",
                    issue_count:
                        window.MathCmsAuditResults
                            .getIssueCount(rows),

                    issue_summary:
                        window.MathCmsAuditResults
                            .summarizeRowsForConcept(rows)
                });
            }

        } catch (err) {
            failed += 1;

            console.warn("Fetch/render audit failed.", {
                checked,
                total,
                ref,
                error: err
            });

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

            if (persistRun && ref.id) {
                auditResultPayload.push({
                    concept_id: ref.id,
                    rendered_tex_hash: "unknown",
                    status: "error",
                    issue_count: 1,
                    issue_summary: err.message || String(err)
                });
            }
        }

        await sleep(25);
    }

    let batchSaveInfo = null;

    if (persistRun) {
        try {
            const preSaveMessage =
                `Scan complete. Saving audit run with ${auditResultPayload.length} result record(s)...`;

            setAuditStatus(preSaveMessage, "info");

            // Important:
            // Live Server may reload the page when SQLite changes during batch-save.
            // Save visible audit rows first so Copy CSV still works after reload.
            saveLatestAuditSnapshot(preSaveMessage);

            batchSaveInfo =
                await window.MathCmsAuditApi
                    .batchSaveAuditRun(
                        API_ENDPOINT,
                        AUDIT_VERSION,
                        mode,
                        auditResultPayload
                    );

        } catch (err) {
            console.warn("Unable to batch-save audit run.", err);

            latestAuditRows.push({
                command: "[AUDIT_BATCH_SAVE_ERROR]",
                count: 1,
                concept_id: "",
                slug: "",
                title: "Audit run",
                example: err.message || String(err),
                concept_url: ""
            });

            renderAuditRows();
        }
    }

    const issueConceptCount = new Set(
        latestAuditRows
            .filter(row =>
                row.command !== "[FETCH_OR_RENDER_ERROR]" &&
                row.command !== "[AUDIT_BATCH_SAVE_ERROR]"
            )
            .map(row => row.slug || row.concept_id)
    ).size;

    const doneMessage = [
        `Done. Checked ${checked}`,
        `concepts with rendering findings: ${issueConceptCount}`,
        `fetch/render failures: ${failed}`
    ];

    if (batchSaveInfo) {
        doneMessage.push(`saved audit run: ${batchSaveInfo.run_id}`);
    }

    const finalMessage = `${doneMessage.join("; ")}.`;

    setAuditStatus(
        finalMessage,
        latestAuditRows.length > 0 ? "warn" : "success"
    );

    saveLatestAuditSnapshot(finalMessage);
}

async function auditConcept(concept) {
    const canvas = document.getElementById("auditCanvas");

    if (!canvas) {
        throw new Error("Audit canvas was not found.");
    }

    canvas.classList.add("tex2jax_process");

    const rawTex =
        window.MathCmsRender.getDisplayTex(concept);

    const localMacroSource =
        concept.cleaned_tex || "";

    /*
    * Local macro definitions affect the final rendering, so include
    * cleaned_tex in the audit hash as well.
    */
    const renderedTexHash =
        await window.MathCmsAuditResults
            .hashText(
                [
                    rawTex || "",
                    "PMLOCAL-SOURCE:",
                    localMacroSource
                ].join("\n")
            );

    const html =
        window.MathCmsRender.prepareConceptHtml(
            rawTex,
            {
                apiEndpoint: API_ENDPOINT,

                localMacroSource,

                context: {
                    page: "mathjax_audit",
                    concept_id: concept.id || null,
                    slug: concept.slug || null,
                    title: concept.title || null
                }
            }
        );

    // Important for full-audit mode:
    // MathJax keeps internal references to previously typeset nodes.
    // Clear those references before replacing the reused audit canvas HTML.
    if (window.MathJax && typeof window.MathJax.typesetClear === "function") {
        window.MathJax.typesetClear([canvas]);
    }

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

    /*
     * Give MathJax and the generated diagram wrappers two browser
     * layout frames to settle before measuring their rendered widths.
     */
    await new Promise(resolve => {
        window.requestAnimationFrame(() => {
            window.requestAnimationFrame(resolve);
        });
    });

    const overflowFindings =
        window.MathCmsOverflowAudit
            .collectHorizontalOverflowFindings(
                canvas
            );

    const findings = [
        ...(
            Array.isArray(leftovers)
                ? leftovers
                : []
        ),
        ...overflowFindings
    ];

    return {
        rendered_tex_hash: renderedTexHash,
        rows: findings.map(item => ({
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
        }))
    };
}


function saveLatestAuditSnapshot(statusMessage = "") {
    window.MathCmsAuditSnapshot
        .saveAuditSnapshot(
            latestAuditRows,
            statusMessage
        );
}


function restoreLatestAuditSnapshot() {
    const snapshot =
        window.MathCmsAuditSnapshot
            .readAuditSnapshot();

    if (!snapshot) {
        return;
    }

    latestAuditRows = snapshot.rows;
    renderAuditRows();

    setAuditStatus(
        snapshot.statusMessage ||
            `Restored ${snapshot.rows.length} audit result row(s) from the previous audit${
                snapshot.savedAt
                    ? ` saved at ${snapshot.savedAt}`
                    : ""
            }. You can copy CSV now.`,
        "warn"
    );
}


function clearLatestAuditSnapshot() {
    window.MathCmsAuditSnapshot
        .clearAuditSnapshot();
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
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;"><code>${window.MathCmsAuditView.escapeHtml(row.command)}</code></td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">${window.MathCmsAuditView.escapeHtml(row.count)}</td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">${window.MathCmsAuditView.renderConceptLink(row)}</td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;"><code>${window.MathCmsAuditView.escapeHtml(row.slug)}</code></td>
                <td style="border-bottom: 1px solid #e2e8f0; padding: 0.5rem;">${window.MathCmsAuditView.escapeHtml(row.example)}</td>
            `;

            body.appendChild(tr);
        });
}

async function copyLatestCsv() {
    if (latestAuditRows.length === 0) {
        setAuditStatus("No audit rows to copy.", "error");
        return;
    }

    const csv =
        window.MathCmsAuditCsv.rowsToCsv(
            latestAuditRows
        );

    try {
        await navigator.clipboard.writeText(csv);
        setAuditStatus("Copied audit CSV to clipboard.", "success");
    } catch (err) {
        console.warn(err);
        setAuditStatus("Unable to copy CSV automatically. Check console for CSV output.", "error");
        console.log(csv);
    }
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

