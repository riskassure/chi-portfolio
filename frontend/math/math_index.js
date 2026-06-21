// frontend/math/math_index.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";

let cachedClassifications = [];
let searchDebounceTimer = null;
let activeSearchAbortController = null;

const SEARCH_MIN_CHARS = 3;
const QUICK_CONCEPT_LIMIT = 6;
const QUICK_CLASSIFICATION_LIMIT = 4;

const MATCH_TYPE_LABELS = {
    title: "Concept",
    synonym: "Synonym",
    definition: "Defined term",
    classification: "MSC"
};

document.addEventListener("DOMContentLoaded", () => {
    bootClassificationHub();
    setupUnifiedSearchEngine();
});

// 1. Download data and fill out the initial directory grid.
async function bootClassificationHub() {
    const grid = document.getElementById("classCardGrid");

    try {
        const response = await fetch(`${API_ENDPOINT}/math/classifications`);
        const json = await response.json();

        if (json.status !== "success") {
            throw new Error(json.message || "Unable to load classifications.");
        }

        cachedClassifications = json.data;
        renderClassificationCards(cachedClassifications);

    } catch (err) {
        grid.innerHTML = `
            <div class="msg-box">
                Error loading subject index deck: ${escapeHtml(err.message)}
            </div>
        `;
    }
}

function renderClassificationCards(categories) {
    const grid = document.getElementById("classCardGrid");
    grid.innerHTML = "";

    if (categories.length === 0) {
        grid.innerHTML = `
            <div class="msg-box">
                No matching subject classifications found.
            </div>
        `;
        return;
    }

    categories.forEach(item => {
        const card = document.createElement("a");

        card.className = "classification-card";
        card.href = `list.html?classification=${encodeURIComponent(item.code.trim())}`;

        card.innerHTML = `
            <span class="class-card-code">${escapeHtml(item.code)}</span>
            <span class="class-card-text">${escapeHtml(item.text)}</span>
        `;

        grid.appendChild(card);
    });

    if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
        window.MathJax.typesetPromise();
    }
}

// 2. Quick-launch dropdown backed by /api/math/search.
function setupUnifiedSearchEngine() {
    const searchInput = document.getElementById("classSearch");
    const dropdownMenu = document.getElementById("searchDropdownMenu");

    if (!searchInput || !dropdownMenu) return;

    searchInput.placeholder = "Search concepts, synonyms, defined terms, or MSC categories...";

    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim();

        clearTimeout(searchDebounceTimer);
        abortActiveSearch();

        if (query.length < SEARCH_MIN_CHARS) {
            dropdownMenu.innerHTML = "";
            dropdownMenu.style.display = "none";
            return;
        }

        searchDebounceTimer = setTimeout(async () => {
            try {
                activeSearchAbortController = new AbortController();

                const url =
                    `${API_ENDPOINT}/math/search` +
                    `?q=${encodeURIComponent(query)}` +
                    `&concept_limit=${QUICK_CONCEPT_LIMIT}` +
                    `&classification_limit=${QUICK_CLASSIFICATION_LIMIT}`;

                const response = await fetch(url, {
                    signal: activeSearchAbortController.signal
                });

                const json = await response.json();
                const results = json.status === "success" ? json.data : [];

                renderUnifiedDropdownMenu(results, query, dropdownMenu);

            } catch (err) {
                if (err.name === "AbortError") return;

                console.error("Unified math search error:", err);

                dropdownMenu.innerHTML = `
                    <div class="dropdown-no-results" style="padding: 1rem; color: #b91c1c; font-style: italic; text-align: center;">
                        Search failed: ${escapeHtml(err.message)}
                    </div>
                `;
                dropdownMenu.style.display = "block";

            } finally {
                activeSearchAbortController = null;
            }
        }, 250);
    });

    searchInput.addEventListener("keydown", (e) => {
        if (e.key !== "Enter") return;

        const query = searchInput.value.trim();

        if (query.length >= SEARCH_MIN_CHARS) {
            window.location.href = buildSearchPageUrl(query);
        }
    });

    searchInput.addEventListener("focus", () => {
        if (dropdownMenu.innerHTML.trim()) {
            dropdownMenu.style.display = "block";
        }
    });

    // Close dropdown if user clicks outside search area.
    document.addEventListener("click", (e) => {
        if (e.target !== searchInput && !dropdownMenu.contains(e.target)) {
            dropdownMenu.style.display = "none";
        }
    });
}

function abortActiveSearch() {
    if (activeSearchAbortController) {
        activeSearchAbortController.abort();
        activeSearchAbortController = null;
    }
}

// 3. Dropdown section builder.
function renderUnifiedDropdownMenu(results, query, container) {
    container.innerHTML = "";

    const conceptResults = results.filter(item => item.kind === "concept");
    const classificationResults = results.filter(item => item.kind === "classification");

    if (conceptResults.length === 0 && classificationResults.length === 0) {
        container.innerHTML = `
            <div class="dropdown-no-results" style="padding: 1rem; color: #64748b; font-style: italic; text-align: center;">
                No quick matches found for "${escapeHtml(query)}"
            </div>
            ${renderViewAllRow(query)}
        `;
        container.style.display = "block";
        return;
    }

    let combinedHtml = "";

    if (conceptResults.length > 0) {
        combinedHtml += buildDropdownSectionHeader("Quick Concept Matches");
        combinedHtml += conceptResults.map(renderConceptSearchRow).join("");
    }

    if (classificationResults.length > 0) {
        const borderTop = conceptResults.length > 0
            ? "border-top: 1px solid #e2e8f0;"
            : "";

        combinedHtml += buildDropdownSectionHeader("Quick Subject Matches", borderTop);
        combinedHtml += classificationResults.map(renderClassificationSearchRow).join("");
    }

    combinedHtml += renderViewAllRow(query);

    container.innerHTML = combinedHtml;
    container.style.display = "block";
}

function buildDropdownSectionHeader(label, extraStyle = "") {
    return `
        <div style="background: #f8fafc; padding: 0.5rem 1rem; font-size: 0.75rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #e2e8f0; ${extraStyle}">
            ${escapeHtml(label)}
        </div>
    `;
}

function renderConceptSearchRow(item) {
    const href = `concept.html?slug=${encodeURIComponent(item.slug)}`;
    const matchLabel = MATCH_TYPE_LABELS[item.match_type] || "Concept";

    const primaryCode =
        Array.isArray(item.classification_codes) && item.classification_codes.length > 0
            ? item.classification_codes[0]
            : null;

    const matchedText = item.matched_text
        ? `
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;">
                Matched ${escapeHtml(matchLabel.toLowerCase())}:
                <em>${escapeHtml(item.matched_text)}</em>
            </div>
        `
        : `
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;">
                ${escapeHtml(matchLabel)}
            </div>
        `;

    const metaBadge = primaryCode
        ? `<span class="dropdown-row-meta">${escapeHtml(primaryCode)}</span>`
        : `<span class="dropdown-row-meta">${escapeHtml(matchLabel)}</span>`;

    return `
        <a href="${href}" class="dropdown-item-row" style="display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 0.75rem 1rem; text-decoration: none; color: #1e293b; border-bottom: 1px solid #f1f5f9;">
            <span style="min-width: 0;">
                <span class="dropdown-row-title" style="font-weight: 500; display: block;">
                    ${escapeHtml(item.title || item.label || "Untitled concept")}
                </span>
                ${matchedText}
            </span>
            ${metaBadge}
        </a>
    `;
}

function renderClassificationSearchRow(item) {
    const href = `list.html?classification=${encodeURIComponent(item.code.trim())}`;

    return `
        <a href="${href}" class="dropdown-item-row" style="display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 0.75rem 1rem; text-decoration: none; color: #1e293b; border-bottom: 1px solid #f1f5f9;">
            <span style="min-width: 0;">
                <span class="dropdown-row-title" style="font-weight: 500; display: block;">
                    ${escapeHtml(item.text || item.label || "Untitled classification")}
                </span>
                <span style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem; display: block;">
                    MSC classification
                </span>
            </span>
            <span class="dropdown-row-meta" style="font-family: monospace;">
                ${escapeHtml(item.code)}
            </span>
        </a>
    `;
}

function renderViewAllRow(query) {
    return `
        <a href="${buildSearchPageUrl(query)}" class="dropdown-item-row" style="display: block; padding: 0.85rem 1rem; text-decoration: none; color: #2563eb; font-weight: 700; background: #eff6ff; border-top: 1px solid #dbeafe;">
            View all results for “${escapeHtml(query)}” →
        </a>
    `;
}

function buildSearchPageUrl(query) {
    return `search.html?q=${encodeURIComponent(query)}`;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}