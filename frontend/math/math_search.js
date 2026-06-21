// frontend/math/math_search.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";

const SEARCH_MIN_CHARS = 2;
const FULL_CONCEPT_LIMIT = 100;
const FULL_CLASSIFICATION_LIMIT = 100;

const MATCH_TYPE_LABELS = {
    title: "Concept title",
    synonym: "Synonym",
    definition: "Defined term",
    classification: "MSC classification"
};

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("searchPageForm");
    const input = document.getElementById("searchPageInput");

    const initialQuery = new URLSearchParams(window.location.search).get("q") || "";
    input.value = initialQuery;

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const query = input.value.trim();

        if (query.length < SEARCH_MIN_CHARS) {
            renderMessage(`Type at least ${SEARCH_MIN_CHARS} characters to search.`);
            return;
        }

        const nextUrl = `search.html?q=${encodeURIComponent(query)}`;

        window.history.pushState({ query }, "", nextUrl);
        runFullSearch(query);
    });

    window.addEventListener("popstate", () => {
        const q = new URLSearchParams(window.location.search).get("q") || "";

        input.value = q;
        runFullSearch(q);
    });

    if (initialQuery.trim().length >= SEARCH_MIN_CHARS) {
        runFullSearch(initialQuery.trim());
    }
});

async function runFullSearch(query) {
    const summary = document.getElementById("searchSummary");
    const container = document.getElementById("searchResultsContainer");

    if (!query || query.trim().length < SEARCH_MIN_CHARS) {
        renderMessage(`Type at least ${SEARCH_MIN_CHARS} characters to search.`);
        return;
    }

    summary.innerText = `Searching for “${query}”...`;
    container.innerHTML = `<div class="msg-box">Querying math search index...</div>`;

    try {
        const url =
            `${API_ENDPOINT}/math/search` +
            `?q=${encodeURIComponent(query)}` +
            `&concept_limit=${FULL_CONCEPT_LIMIT}` +
            `&classification_limit=${FULL_CLASSIFICATION_LIMIT}`;

        const response = await fetch(url);
        const json = await response.json();

        if (json.status !== "success") {
            throw new Error(json.message || "Search failed.");
        }

        renderFullResults(query, json.data || []);

    } catch (err) {
        summary.innerText = "";
        container.innerHTML = `
            <div class="msg-box" style="color: #b91c1c;">
                Search failed: ${escapeHtml(err.message)}
            </div>
        `;
    }
}

function renderFullResults(query, results) {
    const summary = document.getElementById("searchSummary");
    const container = document.getElementById("searchResultsContainer");

    const conceptResults = results.filter(item => item.kind === "concept");
    const classificationResults = results.filter(item => item.kind === "classification");

    const titleMatches = conceptResults.filter(item => item.match_type === "title");
    const synonymMatches = conceptResults.filter(item => item.match_type === "synonym");
    const definitionMatches = conceptResults.filter(item => item.match_type === "definition");

    const totalCount = conceptResults.length + classificationResults.length;

    summary.innerText = `${totalCount} result${totalCount === 1 ? "" : "s"} for “${query}”`;

    if (totalCount === 0) {
        container.innerHTML = `
            <div class="msg-box">
                No results found for “${escapeHtml(query)}”.
            </div>
        `;
        return;
    }

    const chunks = [];

    if (titleMatches.length > 0) {
        chunks.push(renderConceptSection("Concept title matches", titleMatches));
    }

    if (synonymMatches.length > 0) {
        chunks.push(renderConceptSection("Synonym matches", synonymMatches));
    }

    if (definitionMatches.length > 0) {
        chunks.push(renderConceptSection("Defined-term matches", definitionMatches));
    }

    if (classificationResults.length > 0) {
        chunks.push(renderClassificationSection("MSC classification matches", classificationResults));
    }

    container.innerHTML = chunks.join("");
}

function renderConceptSection(title, items) {
    return `
        <section style="margin-bottom: 1.5rem;">
            ${renderSectionHeader(title, items.length)}

            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem;">
                ${items.map(renderConceptCard).join("")}
            </div>
        </section>
    `;
}

function renderClassificationSection(title, items) {
    return `
        <section style="margin-bottom: 1.5rem;">
            ${renderSectionHeader(title, items.length)}

            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem;">
                ${items.map(renderClassificationCard).join("")}
            </div>
        </section>
    `;
}

function renderSectionHeader(title, count) {
    return `
        <div style="display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; margin: 0 0 0.75rem 0;">
            <h2 style="font-size: 1.15rem; color: #0f172a; margin: 0; font-weight: 800;">
                ${escapeHtml(title)}
            </h2>

            <span style="font-size: 0.85rem; color: #64748b; font-weight: 700;">
                ${count}
            </span>
        </div>
    `;
}

function renderConceptCard(item) {
    const href = `concept.html?slug=${encodeURIComponent(item.slug)}`;
    const matchLabel = MATCH_TYPE_LABELS[item.match_type] || "Concept";

    const classificationBadges = Array.isArray(item.classification_codes)
        ? item.classification_codes
            .map(code => `
                <span class="math-tag tag-msc" style="font-size: 0.75rem;">
                    ${escapeHtml(code)}
                </span>
            `)
            .join(" ")
        : "";

    const matchLine = item.matched_text
        ? `
            <p style="margin: 0.35rem 0 0 0; color: #64748b; font-size: 0.9rem;">
                Matched ${escapeHtml(matchLabel.toLowerCase())}:
                <em>${escapeHtml(item.matched_text)}</em>
            </p>
        `
        : `
            <p style="margin: 0.35rem 0 0 0; color: #64748b; font-size: 0.9rem;">
                ${escapeHtml(matchLabel)}
            </p>
        `;

    return `
        <a href="${href}" style="display: block; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; text-decoration: none; color: #1e293b; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);">
            <div style="font-weight: 800; color: #0f172a; font-size: 1rem; line-height: 1.35;">
                ${escapeHtml(item.title || item.label || "Untitled concept")}
            </div>

            ${matchLine}

            ${
                classificationBadges
                    ? `
                        <div style="margin-top: 0.75rem; display: flex; gap: 0.35rem; flex-wrap: wrap;">
                            ${classificationBadges}
                        </div>
                    `
                    : ""
            }
        </a>
    `;
}

function renderClassificationCard(item) {
    const href = `list.html?classification=${encodeURIComponent(item.code.trim())}`;

    const description = item.description
        ? `
            <p style="margin: 0.6rem 0 0 0; color: #64748b; font-size: 0.9rem; line-height: 1.45;">
                ${escapeHtml(item.description)}
            </p>
        `
        : "";

    return `
        <a href="${href}" style="display: block; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; text-decoration: none; color: #1e293b; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);">
            <div style="display: flex; justify-content: space-between; gap: 1rem; align-items: start;">
                <div style="font-weight: 800; color: #0f172a; line-height: 1.35;">
                    ${escapeHtml(item.text || item.label || "Untitled classification")}
                </div>

                <span class="math-tag tag-msc" style="font-size: 0.75rem; white-space: nowrap;">
                    ${escapeHtml(item.code)}
                </span>
            </div>

            <p style="margin: 0.35rem 0 0 0; color: #64748b; font-size: 0.9rem;">
                MSC classification
            </p>

            ${description}
        </a>
    `;
}

function renderMessage(message) {
    document.getElementById("searchSummary").innerText = "";

    document.getElementById("searchResultsContainer").innerHTML = `
        <div class="msg-box">
            ${escapeHtml(message)}
        </div>
    `;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}