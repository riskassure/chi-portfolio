// frontend/math/mathjax_audit.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";
const AUDIT_VERSION = "mathjax-audit-overflow-v1";

let latestAuditRows = [];

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("auditManualBtn")?.addEventListener("click", auditManualList);
    document.getElementById("auditAllBtn")?.addEventListener("click", auditAllConcepts);
    document.getElementById("auditProblematicBtn")?.addEventListener("click", auditProblematicConcepts);
    document.getElementById("copyCsvBtn")
        ?.addEventListener(
            "click",
            () =>
                window.MathCmsAuditClipboard
                    .copyAuditCsv(
                        latestAuditRows
                    )
        );

    restoreLatestAuditSnapshot();
});

async function auditManualList() {
    const raw = document.getElementById("manualSlugsInput")?.value || "";

    const identifiers = raw
        .split(/\r?\n/)
        .map(x => x.trim())
        .filter(Boolean);

    if (identifiers.length === 0) {
        window.MathCmsAuditView.setAuditStatus("Paste at least one slug or ID first.", "error");
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
        window.MathCmsAuditView.setAuditStatus(`Loading ${mode} audit concept list...`, "info");

        const json =
            await window.MathCmsAuditApi
                .fetchAuditConceptList(
                    API_ENDPOINT,
                    mode
                );

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
        window.MathCmsAuditResultsView
            .renderAuditRows(
                latestAuditRows
            );

        if (conceptRefs.length === 0) {
            window.MathCmsAuditView.setAuditStatus(
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
        window.MathCmsAuditView.setAuditStatus(
            `Audit ${mode} failed: ${err.message}`,
            "error"
        );
    }
}

async function runAudit(conceptRefs, options = {}) {
    latestAuditRows = [];
    window.MathCmsAuditResultsView
        .renderAuditRows(
            latestAuditRows
        );
    clearLatestAuditSnapshot();

    const mode = options.mode || "manual";
    const persistRun = Boolean(options.persistRun);

    const total = conceptRefs.length;
    let checked = 0;
    let failed = 0;

    const auditResultPayload = [];

    window.MathCmsAuditView.setAuditStatus(`Starting ${mode} audit for ${total} concept(s)...`, "info");

    for (const ref of conceptRefs) {
        checked += 1;

        window.MathCmsAuditView.setAuditStatus(
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
            const auditResult =
                await window.MathCmsAuditConcept
                    .auditConcept(
                        concept,
                        API_ENDPOINT
                    );
            const rows = auditResult.rows || [];

            latestAuditRows.push(...rows);
            window.MathCmsAuditResultsView
                .renderAuditRows(
                    latestAuditRows
                );

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

            window.MathCmsAuditResultsView
                .renderAuditRows(
                    latestAuditRows
                );

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

            window.MathCmsAuditView.setAuditStatus(preSaveMessage, "info");

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

            window.MathCmsAuditResultsView
                .renderAuditRows(
                    latestAuditRows
                );
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

    window.MathCmsAuditView.setAuditStatus(
        finalMessage,
        latestAuditRows.length > 0 ? "warn" : "success"
    );

    saveLatestAuditSnapshot(finalMessage);
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
    window.MathCmsAuditResultsView
        .renderAuditRows(
            latestAuditRows
        );

    window.MathCmsAuditView.setAuditStatus(
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

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
