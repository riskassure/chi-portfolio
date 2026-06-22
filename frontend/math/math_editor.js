// frontend/math/math_editor.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";

const urlParams = new URLSearchParams(window.location.search);
const editorMode = document.body.dataset.editorMode || "create";
const conceptId = urlParams.get("id");

let previewDebounceTimer = null;

let currentRawTex = "";
let currentRenderedTex = "";
let currentDiagramFailures = [];
let currentReferenceMode = "raw";

document.addEventListener("DOMContentLoaded", () => {
    bootMathEditor();
});

async function bootMathEditor() {
    wireEditorEvents();
    await hydrateLookups();

    if (editorMode === "edit") {
        if (!conceptId) {
            showStatus("Missing concept id in query string. Expected edit.html?id=123.", "error");
            disableEditor();
            return;
        }

        await hydrateConceptForEdit(conceptId);

    } else {
        setDefaultCreateState();
    }

    updatePreview();
}

function wireEditorEvents() {
    const form = document.getElementById("mathEditorForm");
    const titleInput = document.getElementById("conceptTitleInput");
    const texInput = document.getElementById("cleanedTexInput");
    const cancelBtn = document.getElementById("cancelEditorBtn");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            await saveEditorPayload();
        });
    }

    if (titleInput) {
        titleInput.addEventListener("input", () => {
            updateSlugPreview();
        });
    }

    if (texInput) {
        texInput.addEventListener("input", () => {
            clearTimeout(previewDebounceTimer);
            previewDebounceTimer = setTimeout(updatePreview, 300);
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            if (editorMode === "edit") {
                window.history.back();
            } else {
                window.location.href = "index.html";
            }
        });
    }

    document.querySelectorAll("[data-reference-source]").forEach(button => {
        button.addEventListener("click", () => {
            setReferenceView(button.dataset.referenceSource);
        });
    });

    const copyReferenceBtn = document.getElementById("copyReferenceBtn");
    if (copyReferenceBtn) {
        copyReferenceBtn.addEventListener("click", async () => {
            await copyReferenceText();
        });
    }
}

async function hydrateLookups() {
    await Promise.allSettled([
        hydrateTypeOptions(),
        hydrateClassificationOptions()
    ]);
}

async function hydrateTypeOptions() {
    const datalist = document.getElementById("typeOptions");
    if (!datalist) return;

    try {
        const response = await fetch(`${API_ENDPOINT}/admin/math/types`, {
            credentials: "include"
        });

        const json = await response.json();

        if (json.status !== "success") return;

        datalist.innerHTML = json.data
            .map(typeName => `<option value="${escapeHtml(typeName)}"></option>`)
            .join("");

    } catch (err) {
        console.warn("Unable to load math type suggestions:", err);
    }
}

async function hydrateClassificationOptions() {
    const datalist = document.getElementById("classificationOptions");
    if (!datalist) return;

    try {
        const response = await fetch(`${API_ENDPOINT}/math/classifications`);
        const json = await response.json();

        if (json.status !== "success") return;

        datalist.innerHTML = json.data
            .map(item => `<option value="${escapeHtml(item.code)}">${escapeHtml(item.text)}</option>`)
            .join("");

    } catch (err) {
        console.warn("Unable to load classification suggestions:", err);
    }
}

function setDefaultCreateState() {
    const pageTitle = document.getElementById("editorPageTitle");
    const saveBtn = document.getElementById("saveEditorBtn");
    const ownerInput = document.getElementById("ownerInput");
    const isCleanedInput = document.getElementById("isCleanedInput");

    if (pageTitle) pageTitle.innerText = "Create New Math Concept";
    if (saveBtn) saveBtn.innerText = "Create Concept";
    if (ownerInput) ownerInput.value = "CWoo";
    if (isCleanedInput) isCleanedInput.checked = false;

    currentRawTex = "";
    currentRenderedTex = "";
    currentDiagramFailures = [];

    updateSlugPreview();
    setReferenceView("raw");
    renderDiagramFailureSummary();
}

async function hydrateConceptForEdit(id) {
    showStatus("Loading concept editor data...", "info");

    try {
        const response = await fetch(`${API_ENDPOINT}/admin/math/concepts/${encodeURIComponent(id)}`, {
            credentials: "include"
        });

        const json = await response.json();

        if (json.status !== "success") {
            throw new Error(json.message || "Failed to load concept.");
        }

        const concept = json.data;

        document.title = `Edit ${concept.title || "Math Concept"}`;

        document.getElementById("editorPageTitle").innerText = `Edit: ${concept.title}`;
        document.getElementById("saveEditorBtn").innerText = "Save Changes";

        document.getElementById("conceptIdInput").value = concept.id;
        document.getElementById("conceptTitleInput").value = concept.title || "";
        document.getElementById("ownerInput").value = concept.owner || "";
        document.getElementById("cleanedTexInput").value = concept.cleaned_tex || "";
        document.getElementById("isCleanedInput").checked = Number(concept.is_cleaned || 0) === 1;

        document.getElementById("classificationsInput").value = csvFromArray(
            (concept.classifications || []).map(item => item.code)
        );

        document.getElementById("typesInput").value = csvFromArray(concept.types || []);
        document.getElementById("synonymsInput").value = csvFromArray(concept.synonyms || []);
        document.getElementById("definitionsInput").value = csvFromArray(concept.definitions || []);
        document.getElementById("relatedConceptsInput").value = csvFromArray(
            (concept.related_concepts || []).map(item => {
                return item.related_canonical_name || item.canonical_name || item.title || "";
            })
        );

        currentRawTex = concept.raw_tex || "";
        currentRenderedTex = concept.rendered_tex || "";
        currentDiagramFailures = concept.diagram_failures || [];

        const sourceFileNameEl = document.getElementById("sourceFileName");
        if (sourceFileNameEl) {
            sourceFileNameEl.innerText = concept.source_file_name || "--";
        }

        const diagramFailureCount = currentDiagramFailures.length;
        const failureBadge = diagramFailureCount > 0
            ? `&nbsp; | &nbsp; <strong style="color:#b91c1c;">Diagram failures:</strong> ${diagramFailureCount}`
            : "";

        const createdText = concept.created_at || "--";
        const updatedText = concept.updated_at || "--";

        document.getElementById("editorMetadata").innerHTML = `
            <strong>ID:</strong> ${escapeHtml(concept.id)}
            &nbsp; | &nbsp;
            <strong>Slug:</strong> ${escapeHtml(concept.slug || "--")}
            &nbsp; | &nbsp;
            <strong>Created:</strong> ${escapeHtml(createdText)}
            &nbsp; | &nbsp;
            <strong>Updated:</strong> ${escapeHtml(updatedText)}
            ${failureBadge}
        `;

        updateSlugPreview(concept.slug);
        renderDiagramFailureSummary();

        if (diagramFailureCount > 0) {
            setReferenceView("diagnostics");
        } else {
            setReferenceView("raw");
        }

        showStatus("", "clear");

    } catch (err) {
        console.error(err);
        showStatus(`Unable to load concept: ${err.message}`, "error");
        disableEditor();
    }
}

async function saveEditorPayload() {
    const title = document.getElementById("conceptTitleInput").value.trim();
    const cleanedTex = document.getElementById("cleanedTexInput").value.trim();

    if (!title) {
        showStatus("Title is required.", "error");
        return;
    }

    if (!cleanedTex) {
        showStatus("LaTeX body is required.", "error");
        return;
    }

    const payload = {
        title,
        owner: document.getElementById("ownerInput").value.trim() || "CWoo",
        cleaned_tex: cleanedTex,
        classifications: parseCsvInput("classificationsInput"),
        types: parseCsvInput("typesInput"),
        synonyms: parseCsvInput("synonymsInput"),
        definitions: parseCsvInput("definitionsInput"),
        related_concepts: parseCsvInput("relatedConceptsInput"),
        is_cleaned: document.getElementById("isCleanedInput").checked ? 1 : 0
    };

    let url = `${API_ENDPOINT}/admin/math/create`;

    if (editorMode === "edit") {
        payload.id = Number(document.getElementById("conceptIdInput").value || conceptId);
        url = `${API_ENDPOINT}/admin/math/update`;
    }

    showStatus("Saving...", "info");
    setSavingState(true);

    try {
        const response = await fetch(url, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const json = await response.json();

        if (!response.ok || json.success !== true) {
            throw new Error(json.message || json.error || "Save failed.");
        }

        showStatus(json.message || "Saved successfully.", "success");

        const targetSlug = json.slug;

        if (editorMode === "create" && targetSlug) {
            setTimeout(() => {
                window.location.href = `concept.html?slug=${encodeURIComponent(targetSlug)}`;
            }, 600);
        }

    } catch (err) {
        console.error(err);
        showStatus(`Save failed: ${err.message}`, "error");

    } finally {
        setSavingState(false);
    }
}

function updateSlugPreview(existingSlug = null) {
    const slugTarget = document.getElementById("slugPreview");
    const titleInput = document.getElementById("conceptTitleInput");

    if (!slugTarget || !titleInput) return;

    if (editorMode === "edit" && existingSlug) {
        slugTarget.innerText = existingSlug;
        return;
    }

    const title = titleInput.value.trim();

    slugTarget.innerText = title
        ? generateSlug(title.replace(/\s+/g, ""))
        : "--";
}

async function updatePreview() {
    const preview = document.getElementById("editorPreviewCanvas");
    const texInput = document.getElementById("cleanedTexInput");

    if (!preview || !texInput) return;

    const tex = texInput.value || "";

    if (!tex.trim()) {
        preview.innerHTML = `
            <div style="color: #64748b; font-style: italic;">
                Preview will appear here...
            </div>
        `;
        return;
    }

    const cleaned = cleanEditorPreviewTex(tex);
    preview.innerHTML = cleaned;

    if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
        try {
            if (typeof window.MathJax.typesetClear === "function") {
                window.MathJax.typesetClear([preview]);
            }

            await window.MathJax.typesetPromise([preview]);

        } catch (err) {
            console.warn("Preview MathJax render warning:", err);
        }
    }
}

function cleanEditorPreviewTex(tex) {
    let clean = tex || "";

    clean = clean.replace(
        /\\begin\{pspicture\}[\s\S]*?\\end\{pspicture\}/gi,
        `<div class="img-placeholder"><em>[PSTricks diagram preview will be generated by pipeline]</em></div>`
    );

    clean = clean.replace(/\\begin{enumerate}/gi, "<ol style='margin-top: 0.5rem; padding-left: 1.5rem;'>");
    clean = clean.replace(/\\end{enumerate}/gi, "</ol>");

    clean = clean.replace(/\\begin{itemize}/gi, "<ul style='margin-top: 0.5rem; padding-left: 1.5rem; list-style-type: disc;'>");
    clean = clean.replace(/\\end{itemize}/gi, "</ul>");

    clean = clean.replace(/\\item/gi, "<li style='margin-bottom: 0.25rem;'>");

    clean = clean.replace(/\\emph\{([^}]+)\}/gi, "<em>$1</em>");
    clean = clean.replace(/\\textbf\{([^}]+)\}/gi, "<strong>$1</strong>");

    clean = clean.replace(/\\begin\{tabular\}\{[^}]*\}([\s\S]*?)\\end\{tabular\}/gi, function(_, body) {
        const rows = body
            .replace(/\\hline/g, "")
            .trim()
            .split(/\\\\/)
            .map(row => row.trim())
            .filter(row => row.length > 0);

        const htmlRows = rows.map((row, rowIndex) => {
            const cells = row.split("&").map(cell => cell.trim());
            const tag = rowIndex === 0 ? "th" : "td";

            return `<tr>` + cells.map(cell =>
                `<${tag} style="border:1px solid #cbd5e1; padding:0.4rem 0.6rem;">${cell}</${tag}>`
            ).join("") + `</tr>`;
        }).join("");

        return `
            <table style="border-collapse:collapse; margin:1rem 0; width:100%;">
                ${htmlRows}
            </table>
        `;
    });

    return clean;
}

function setReferenceView(mode) {
    currentReferenceMode = mode || "raw";

    const viewer = document.getElementById("referenceTexViewer");
    const label = document.getElementById("referenceTexLabel");

    if (!viewer) return;

    viewer.style.display = "block";

    if (currentReferenceMode === "rendered") {
        viewer.value = currentRenderedTex || "[No rendered_tex currently stored for this concept.]";

        if (label) {
            label.innerText = "Rendered TeX / Generated Display Source";
        }

    } else if (currentReferenceMode === "diagnostics") {
        viewer.value = buildDiagnosticsText();

        if (label) {
            label.innerText = "Diagram Diagnostics";
        }

    } else {
        viewer.value = currentRawTex || "[No raw TeX source stored for this concept.]";

        if (label) {
            label.innerText = "Raw TeX Source";
        }
    }

    updateReferenceButtonStyles();
}

function updateReferenceButtonStyles() {
    document.querySelectorAll("[data-reference-source]").forEach(button => {
        const isActive = button.dataset.referenceSource === currentReferenceMode;

        button.style.background = isActive ? "#2563eb" : "#ffffff";
        button.style.color = isActive ? "#ffffff" : "#334155";
        button.style.border = isActive ? "1px solid #2563eb" : "1px solid #cbd5e1";
    });
}

function buildDiagnosticsText() {
    if (!currentDiagramFailures || currentDiagramFailures.length === 0) {
        return "[No diagram conversion failures recorded for this concept.]";
    }

    return currentDiagramFailures.map((failure, index) => {
        return [
            `==============================`,
            `Failure ${index + 1} — PSTricks block #${failure.block_index || "?"}`,
            `==============================`,
            `Block index: ${failure.block_index || "--"}`,
            `Hash: ${failure.source_hash || "--"}`,
            `Stage: ${failure.failure_stage || "--"}`,
            `Created: ${failure.created_at || "--"}`,
            `Temp TeX path: ${failure.tex_temp_path || "--"}`,
            ``,
            `----- Failed PSTricks Source -----`,
            failure.source_tex || "[No source_tex captured]",
            ``,
            `----- Error Output -----`,
            failure.error_output || "[No error output captured]",
            ``
        ].join("\n");
    }).join("\n\n");
}

function renderDiagramFailureSummary() {
    const box = document.getElementById("diagramFailureSummary");
    const diagnosticsBtn = document.querySelector('[data-reference-source="diagnostics"]');

    if (!box) return;

    const count = currentDiagramFailures ? currentDiagramFailures.length : 0;

    if (diagnosticsBtn) {
        diagnosticsBtn.style.display = count > 0 ? "inline-block" : "none";
    }

    if (count === 0) {
        box.innerHTML = `
            <div style="color: #047857; background: #ecfdf5; border: 1px solid #bbf7d0; border-radius: 8px; padding: 0.7rem 0.85rem;">
                No diagram conversion failures recorded for this concept.
            </div>
        `;
        return;
    }

    const rows = currentDiagramFailures.map((failure, index) => {
        return `
            <div style="padding: 0.65rem 0; border-top: ${index === 0 ? "none" : "1px solid #fecaca"};">
                <div style="font-weight: 800; color: #7f1d1d;">
                    Failure ${index + 1}: PSTricks block #${escapeHtml(failure.block_index || "?")}
                </div>

                <div style="font-size: 0.85rem; color: #991b1b; margin-top: 0.2rem;">
                    Stage: <code>${escapeHtml(failure.failure_stage || "unknown")}</code>
                </div>

                <div style="font-size: 0.85rem; color: #991b1b; margin-top: 0.2rem;">
                    Hash: <code>${escapeHtml(failure.source_hash || "--")}</code>
                </div>

                <div style="font-size: 0.85rem; color: #991b1b; margin-top: 0.2rem;">
                    Temp file: <code>${escapeHtml(failure.tex_temp_path || "--")}</code>
                </div>
            </div>
        `;
    }).join("");

    box.innerHTML = `
        <div style="color: #7f1d1d; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 0.85rem;">
            <div style="font-weight: 900; margin-bottom: 0.4rem;">
                ${count} diagram conversion failure${count === 1 ? "" : "s"} recorded.
            </div>

            <div style="font-size: 0.9rem; margin-bottom: 0.5rem;">
                Open the <strong>Diagram Diagnostics</strong> tab in the reference pane to inspect the failed PSTricks block and error output.
            </div>

            ${rows}
        </div>
    `;
}

async function copyReferenceText() {
    const viewer = document.getElementById("referenceTexViewer");

    if (!viewer) return;

    try {
        await navigator.clipboard.writeText(viewer.value || "");
        showStatus("Copied reference pane text to clipboard.", "success");

    } catch (err) {
        viewer.select();
        document.execCommand("copy");
        showStatus("Copied reference pane text to clipboard.", "success");
    }
}

function parseCsvInput(elementId) {
    const value = document.getElementById(elementId).value || "";

    return value
        .split(",")
        .map(x => x.trim())
        .filter(Boolean);
}

function csvFromArray(arr) {
    return Array.isArray(arr)
        ? arr.filter(Boolean).join(", ")
        : "";
}

function generateSlug(canonicalName) {
    if (!canonicalName) return "";

    const s1 = canonicalName.replace(/(.)([A-Z][a-z]+)/g, "$1-$2");
    const s2 = s1.replace(/([a-z0-9])([A-Z])/g, "$1-$2");

    return s2
        .toLowerCase()
        .replace(/_/g, "-")
        .replace(/--+/g, "-");
}

function showStatus(message, type = "info") {
    const statusBox = document.getElementById("editorStatus");

    if (!statusBox) return;

    if (!message || type === "clear") {
        statusBox.innerHTML = "";
        statusBox.style.display = "none";
        return;
    }

    const colors = {
        info: {
            bg: "#eff6ff",
            border: "#bfdbfe",
            text: "#1d4ed8"
        },
        success: {
            bg: "#ecfdf5",
            border: "#bbf7d0",
            text: "#047857"
        },
        error: {
            bg: "#fef2f2",
            border: "#fecaca",
            text: "#b91c1c"
        }
    };

    const palette = colors[type] || colors.info;

    statusBox.style.display = "block";
    statusBox.style.background = palette.bg;
    statusBox.style.border = `1px solid ${palette.border}`;
    statusBox.style.color = palette.text;
    statusBox.style.padding = "0.75rem 1rem";
    statusBox.style.borderRadius = "8px";
    statusBox.style.marginBottom = "1rem";
    statusBox.style.fontWeight = "600";
    statusBox.innerText = message;
}

function setSavingState(isSaving) {
    const saveBtn = document.getElementById("saveEditorBtn");

    if (!saveBtn) return;

    saveBtn.disabled = isSaving;
    saveBtn.style.opacity = isSaving ? "0.65" : "1";
    saveBtn.style.cursor = isSaving ? "not-allowed" : "pointer";
}

function disableEditor() {
    document
        .querySelectorAll("#mathEditorForm input, #mathEditorForm textarea, #mathEditorForm button")
        .forEach(el => {
            el.disabled = true;
        });
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}