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

let classificationChipPicker = null;
let typeChipPicker = null;
let relatedConceptChipPicker = null;

let classificationOptions = [];
let typeOptions = [];

document.addEventListener("DOMContentLoaded", () => {
    bootMathEditor();
});

async function bootMathEditor() {
    initializeChipPickers();

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
    const titleInput = document.getElementById("conceptTitleInput");
    const texInput = document.getElementById("cleanedTexInput");
    const cancelBtn = document.getElementById("cancelEditorBtn");
    const saveBtn = document.getElementById("saveEditorBtn");

    if (saveBtn) {
        saveBtn.addEventListener("click", async (e) => {
            e.preventDefault(); 
            // Optional: prevent bubbling just in case there are nested elements
            e.stopPropagation(); 
            
            console.log("SAVE BUTTON CLICK FIRED");
            
            // Add a try-catch here to see if the error is failing silently!
            try {
                await saveEditorPayload();
            } catch (err) {
                console.error("Save failed:", err);
                showStatus("Error saving: " + err.message, "error");
            }
        });
    } else {
        console.warn("saveEditorBtn not found");
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

function initializeChipPickers() {
    classificationChipPicker = createChipPicker({
        inputId: "classificationChipInput",
        chipListId: "classificationChipList",
        suggestionsId: "classificationSuggestions",
        hiddenInputId: "classificationsInput",
        getOptions: () => classificationOptions
    });

    typeChipPicker = createChipPicker({
        inputId: "typeChipInput",
        chipListId: "typeChipList",
        suggestionsId: "typeSuggestions",
        hiddenInputId: "typesInput",
        getOptions: () => typeOptions
    });

    relatedConceptChipPicker = createRelatedConceptChipPicker({
        inputId: "relatedConceptChipInput",
        chipListId: "relatedConceptChipList",
        suggestionsId: "relatedConceptSuggestions",
        hiddenInputId: "relatedConceptsInput"
    });
}

function normalizeClassificationOptions(raw) {
    const rows = Array.isArray(raw)
        ? raw
        : raw.classifications || raw.results || raw.data || [];

    return rows
        .map(item => {
            if (typeof item === "string") {
                return {
                    value: item,
                    label: item,
                    sublabel: ""
                };
            }

            const code =
                item.classification ||
                item.classification_code ||
                item.code ||
                item.name ||
                "";

            const title =
                item.classification_name ||
                item.classification_title ||
                item.title ||
                item.text ||
                item.description ||
                "";

            return {
                value: code,
                label: title ? `${code} — ${title}` : code,
                sublabel: title
            };
        })
        .filter(option => option.value);
}


function normalizeTypeOptions(raw) {
    const rows = Array.isArray(raw)
        ? raw
        : raw.types || raw.results || raw.data || [];

    return rows
        .map(item => {
            if (typeof item === "string") {
                return {
                    value: item,
                    label: item,
                    sublabel: ""
                };
            }

            const value =
                item.type_name ||
                item.type ||
                item.name ||
                item.title ||
                "";

            return {
                value,
                label: value,
                sublabel: item.description || ""
            };
        })
        .filter(option => option.value);
}

function createChipPicker(config) {
    const input = document.getElementById(config.inputId);
    const chipList = document.getElementById(config.chipListId);
    const suggestions = document.getElementById(config.suggestionsId);
    const hiddenInput = document.getElementById(config.hiddenInputId);

    let selectedValues = [];
    let activeSuggestionIndex = -1;
    let visibleSuggestions = [];

    function normalizeValue(value) {
        return String(value || "").trim();
    }

    function syncHiddenInput() {
        if (hiddenInput) {
            hiddenInput.value = selectedValues.join(", ");
        }
    }

    function renderChips() {
        chipList.innerHTML = "";

        selectedValues.forEach(value => {
            const chip = document.createElement("span");
            chip.className = "chip";

            const label = document.createElement("span");
            label.textContent = value;

            const removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "chip-remove";
            removeBtn.textContent = "×";
            removeBtn.setAttribute("aria-label", `Remove ${value}`);

            removeBtn.addEventListener("click", () => {
                selectedValues = selectedValues.filter(v => v !== value);
                renderChips();
                syncHiddenInput();
                input.focus();
            });

            chip.appendChild(label);
            chip.appendChild(removeBtn);
            chipList.appendChild(chip);
        });

        chipList.appendChild(input);
        syncHiddenInput();
    }

    function addValue(value) {
        const cleanValue = normalizeValue(value);

        if (!cleanValue) {
            return;
        }

        const alreadyExists = selectedValues.some(v => {
            return v.toLowerCase() === cleanValue.toLowerCase();
        });

        if (!alreadyExists) {
            selectedValues.push(cleanValue);
        }

        input.value = "";
        hideSuggestions();
        renderChips();
    }

    function hideSuggestions() {
        suggestions.style.display = "none";
        suggestions.innerHTML = "";
        activeSuggestionIndex = -1;
        visibleSuggestions = [];
    }

    function renderSuggestions() {
        const query = input.value.trim().toLowerCase();

        if (!query) {
            hideSuggestions();
            return;
        }

        const options = config.getOptions();

        visibleSuggestions = options
            .filter(option => {
                const value = String(option.value || "").toLowerCase();
                const label = String(option.label || "").toLowerCase();
                const sublabel = String(option.sublabel || "").toLowerCase();

                const alreadySelected = selectedValues.some(v => {
                    return v.toLowerCase() === String(option.value || "").toLowerCase();
                });

                return !alreadySelected && (
                    value.includes(query) ||
                    label.includes(query) ||
                    sublabel.includes(query)
                );
            })
            .slice(0, 12);

        if (visibleSuggestions.length === 0) {
            hideSuggestions();
            return;
        }

        suggestions.innerHTML = "";

        visibleSuggestions.forEach((option, index) => {
            const row = document.createElement("div");
            row.className = "chip-suggestion";

            if (index === activeSuggestionIndex) {
                row.classList.add("active");
            }

            const main = document.createElement("div");
            main.className = "chip-suggestion-main";
            main.textContent = option.label || option.value;

            row.appendChild(main);

            if (option.sublabel) {
                const sub = document.createElement("div");
                sub.className = "chip-suggestion-sub";
                sub.textContent = option.sublabel;
                row.appendChild(sub);
            }

            row.addEventListener("mousedown", event => {
                event.preventDefault();
                addValue(option.value);
            });

            suggestions.appendChild(row);
        });

        suggestions.style.display = "block";
    }

    input.addEventListener("input", () => {
        activeSuggestionIndex = -1;
        renderSuggestions();
    });

    input.addEventListener("keydown", event => {
        if (event.key === "ArrowDown") {
            event.preventDefault();

            if (visibleSuggestions.length > 0) {
                activeSuggestionIndex =
                    (activeSuggestionIndex + 1) % visibleSuggestions.length;
                renderSuggestions();
            }

            return;
        }

        if (event.key === "ArrowUp") {
            event.preventDefault();

            if (visibleSuggestions.length > 0) {
                activeSuggestionIndex =
                    activeSuggestionIndex <= 0
                        ? visibleSuggestions.length - 1
                        : activeSuggestionIndex - 1;
                renderSuggestions();
            }

            return;
        }

        if (event.key === "Enter") {
            event.preventDefault();

            if (
                activeSuggestionIndex >= 0 &&
                visibleSuggestions[activeSuggestionIndex]
            ) {
                addValue(visibleSuggestions[activeSuggestionIndex].value);
            } else if (visibleSuggestions.length === 1) {
                addValue(visibleSuggestions[0].value);
            } else {
                addValue(input.value);
            }

            return;
        }

        if (event.key === "," || event.key === "Tab") {
            if (input.value.trim()) {
                event.preventDefault();
                addValue(input.value);
            }

            return;
        }

        if (
            event.key === "Backspace" &&
            !input.value &&
            selectedValues.length > 0
        ) {
            selectedValues.pop();
            renderChips();
            syncHiddenInput();
        }
    });

    input.addEventListener("blur", () => {
        setTimeout(() => {
            hideSuggestions();
        }, 150);
    });

    return {
        setValues(values) {
            selectedValues = Array.from(new Set(
                (values || [])
                    .map(normalizeValue)
                    .filter(Boolean)
            ));

            renderChips();
        },

        getValues() {
            return [...selectedValues];
        },

        addValue,

        clear() {
            selectedValues = [];
            input.value = "";
            hideSuggestions();
            renderChips();
        }
    };
}


function createRelatedConceptChipPicker(config) {
    const input = document.getElementById(config.inputId);
    const chipList = document.getElementById(config.chipListId);
    const suggestions = document.getElementById(config.suggestionsId);
    const hiddenInput = document.getElementById(config.hiddenInputId);

    let selectedItems = [];
    let visibleSuggestions = [];
    let activeSuggestionIndex = -1;
    let searchTimer = null;

    function normalizeItem(item) {
        if (typeof item === "string") {
            return {
                id: null,
                title: item,
                canonical_name: item,
                slug: ""
            };
        }

        return {
            id: item.id || item.related_concept_id || null,
            title: item.title || item.related_canonical_name || item.canonical_name || "",
            canonical_name: item.canonical_name || item.related_canonical_name || item.title || "",
            slug: item.slug || ""
        };
    }

    function itemKey(item) {
        const normalized = normalizeItem(item);

        if (normalized.id) {
            return `id:${normalized.id}`;
        }

        return `name:${String(normalized.canonical_name || "").toLowerCase()}`;
    }

    function syncHiddenInput() {
        if (!hiddenInput) return;

        hiddenInput.value = selectedItems
            .map(item => item.canonical_name)
            .filter(Boolean)
            .join(", ");
    }

    function hideSuggestions() {
        suggestions.style.display = "none";
        suggestions.innerHTML = "";
        visibleSuggestions = [];
        activeSuggestionIndex = -1;
    }

    function renderChips() {
        chipList.innerHTML = "";

        selectedItems.forEach(item => {
            const chip = document.createElement("span");
            chip.className = "chip";

            const label = document.createElement("span");
            label.textContent = item.title || item.canonical_name || item.slug || "Untitled concept";

            const removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "chip-remove";
            removeBtn.textContent = "×";
            removeBtn.setAttribute("aria-label", `Remove ${label.textContent}`);

            removeBtn.addEventListener("click", () => {
                selectedItems = selectedItems.filter(existing => {
                    return itemKey(existing) !== itemKey(item);
                });

                renderChips();
                syncHiddenInput();
                input.focus();
            });

            chip.appendChild(label);
            chip.appendChild(removeBtn);
            chipList.appendChild(chip);
        });

        chipList.appendChild(input);
        syncHiddenInput();
    }

    function addItem(item) {
        const normalized = normalizeItem(item);

        if (!normalized.canonical_name && !normalized.title) {
            return;
        }

        const alreadyExists = selectedItems.some(existing => {
            return itemKey(existing) === itemKey(normalized);
        });

        if (!alreadyExists) {
            selectedItems.push(normalized);
        }

        input.value = "";
        hideSuggestions();
        renderChips();
    }

    async function fetchSuggestions(query) {
        const excludeId = document.getElementById("conceptIdInput")?.value || conceptId || "";

        const url =
            `${API_ENDPOINT}/admin/math/concepts/search?q=${encodeURIComponent(query)}` +
            `&exclude_id=${encodeURIComponent(excludeId)}`;

        const response = await fetch(url, {
            credentials: "include"
        });

        const json = await response.json();

        if (json.status !== "success") {
            return [];
        }

        return json.data || [];
    }

    async function renderSuggestions() {
        const query = input.value.trim();

        if (query.length < 2) {
            hideSuggestions();
            return;
        }

        try {
            const rows = await fetchSuggestions(query);

            const selectedKeys = new Set(selectedItems.map(itemKey));

            visibleSuggestions = rows
                .map(normalizeItem)
                .filter(item => !selectedKeys.has(itemKey(item)))
                .slice(0, 12);

            if (visibleSuggestions.length === 0) {
                hideSuggestions();
                return;
            }

            suggestions.innerHTML = "";

            visibleSuggestions.forEach((item, index) => {
                const row = document.createElement("div");
                row.className = "chip-suggestion";

                if (index === activeSuggestionIndex) {
                    row.classList.add("active");
                }

                const main = document.createElement("div");
                main.className = "chip-suggestion-main";
                main.textContent = item.title || item.canonical_name || "Untitled concept";

                const sub = document.createElement("div");
                sub.className = "chip-suggestion-sub";
                sub.textContent = item.canonical_name
                    ? `${item.canonical_name}${item.slug ? " · " + item.slug : ""}`
                    : item.slug || "";

                row.appendChild(main);

                if (sub.textContent) {
                    row.appendChild(sub);
                }

                row.addEventListener("mousedown", event => {
                    event.preventDefault();
                    addItem(item);
                });

                suggestions.appendChild(row);
            });

            suggestions.style.display = "block";

        } catch (err) {
            console.warn("Unable to search related concepts:", err);
            hideSuggestions();
        }
    }

    input.addEventListener("input", () => {
        clearTimeout(searchTimer);

        activeSuggestionIndex = -1;

        searchTimer = setTimeout(() => {
            renderSuggestions();
        }, 250);
    });

    input.addEventListener("keydown", event => {
        if (event.key === "ArrowDown") {
            event.preventDefault();

            if (visibleSuggestions.length > 0) {
                activeSuggestionIndex =
                    (activeSuggestionIndex + 1) % visibleSuggestions.length;
                renderSuggestions();
            }

            return;
        }

        if (event.key === "ArrowUp") {
            event.preventDefault();

            if (visibleSuggestions.length > 0) {
                activeSuggestionIndex =
                    activeSuggestionIndex <= 0
                        ? visibleSuggestions.length - 1
                        : activeSuggestionIndex - 1;
                renderSuggestions();
            }

            return;
        }

        if (event.key === "Enter") {
            event.preventDefault();

            if (
                activeSuggestionIndex >= 0 &&
                visibleSuggestions[activeSuggestionIndex]
            ) {
                addItem(visibleSuggestions[activeSuggestionIndex]);
            }

            return;
        }

        if (
            event.key === "Backspace" &&
            !input.value &&
            selectedItems.length > 0
        ) {
            selectedItems.pop();
            renderChips();
            syncHiddenInput();
        }
    });

    input.addEventListener("blur", () => {
        setTimeout(() => {
            hideSuggestions();
        }, 150);
    });

    return {
        setValues(values) {
            selectedItems = [];

            (values || []).forEach(item => {
                const normalized = normalizeItem(item);

                const alreadyExists = selectedItems.some(existing => {
                    return itemKey(existing) === itemKey(normalized);
                });

                if (!alreadyExists && (normalized.canonical_name || normalized.title)) {
                    selectedItems.push(normalized);
                }
            });

            renderChips();
        },

        getValues() {
            return selectedItems
                .map(item => item.canonical_name || item.title)
                .filter(Boolean);
        },

        getItems() {
            return [...selectedItems];
        },

        clear() {
            selectedItems = [];
            input.value = "";
            hideSuggestions();
            renderChips();
        }
    };
}


async function hydrateLookups() {
    try {
        const [classificationResponse, typeResponse] = await Promise.all([
            fetch(`${API_ENDPOINT}/math/classifications`),
            fetch(`${API_ENDPOINT}/admin/math/types`, {
                credentials: "include"
            })
        ]);

        const classificationJson = await classificationResponse.json();
        const typeJson = await typeResponse.json();

        if (classificationJson.status === "success") {
            classificationOptions = normalizeClassificationOptions(classificationJson);
        } else {
            classificationOptions = [];
        }

        if (typeJson.status === "success") {
            typeOptions = normalizeTypeOptions(typeJson);
        } else {
            typeOptions = [];
        }

    } catch (err) {
        console.warn("Unable to load chip picker suggestions:", err);
        classificationOptions = [];
        typeOptions = [];
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

    if (classificationChipPicker) {
        classificationChipPicker.setValues([]);
    }

    if (typeChipPicker) {
        typeChipPicker.setValues([]);
    }

    if (relatedConceptChipPicker) {
        relatedConceptChipPicker.setValues([]);
    }

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

        classificationChipPicker.setValues(
            (concept.classifications || []).map(item => {
                return item.code || item.classification_code || item.classification || item;
            })
        );

        typeChipPicker.setValues(concept.types || []);

        document.getElementById("synonymsInput").value = csvFromArray(concept.synonyms || []);
        document.getElementById("definitionsInput").value = csvFromArray(concept.definitions || []);

        relatedConceptChipPicker.setValues(concept.related_concepts || []);

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
    console.log("saveEditorPayload() reached");

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
        classifications: classificationChipPicker.getValues(),
        types: typeChipPicker.getValues(),
        synonyms: parseCsvInput("synonymsInput"),
        definitions: parseCsvInput("definitionsInput"),
        related_concepts: relatedConceptChipPicker.getValues(),
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

        let saveMessage = json.message || "Saved successfully.";

        if (json.save_mode) {
            saveMessage += ` Save mode: ${json.save_mode}.`;
        }

        if (json.diagram_compare) {
            saveMessage += ` Diagrams: ${json.diagram_compare.unchanged_count || 0} unchanged, ${json.diagram_compare.added_count || 0} added, ${json.diagram_compare.removed_count || 0} removed.`;
        }

        console.log("SAVE STATUS MESSAGE:", saveMessage);
        
        showStatus(saveMessage, "success");

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
    let statusBox = document.getElementById("editorStatus");

    if (!statusBox) {
        statusBox = document.createElement("div");
        statusBox.id = "editorStatus";
        document.body.appendChild(statusBox);
    }

    if (type === "clear") {
        console.log("STATUS CLEAR REQUESTED");

        statusBox.innerHTML = "";
        statusBox.style.display = "none";
        return;
    }

    if (!message) {
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
    statusBox.style.position = "fixed";
    statusBox.style.top = "5.25rem";
    statusBox.style.right = "1.25rem";
    statusBox.style.zIndex = "99999";
    statusBox.style.maxWidth = "520px";
    statusBox.style.background = palette.bg;
    statusBox.style.border = `1px solid ${palette.border}`;
    statusBox.style.color = palette.text;
    statusBox.style.padding = "0.85rem 1rem";
    statusBox.style.borderRadius = "10px";
    statusBox.style.boxShadow = "0 12px 30px rgba(15, 23, 42, 0.18)";
    statusBox.style.fontWeight = "700";
    statusBox.style.fontSize = "0.95rem";
    statusBox.style.lineHeight = "1.45";
    statusBox.innerText = message;

    console.log("STATUS SHOWN:", type, message);
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