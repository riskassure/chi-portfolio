// frontend/math/math_index.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";
let cachedClassifications = [];
let searchDebounceTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    bootClassificationHub();
    setupUnifiedSearchEngine();
});

// 1. Download data and fill out the initial directory grid (Stays permanently fixed)
async function bootClassificationHub() {
    const grid = document.getElementById("classCardGrid");
    try {
        const response = await fetch(`${API_ENDPOINT}/math/classifications`);
        const json = await response.json();
        
        if (json.status !== "success") throw new Error(json.message);
        
        cachedClassifications = json.data;
        renderClassificationCards(cachedClassifications);
    } catch (err) {
        grid.innerHTML = `<div class="msg-box">Error loading subject index deck: ${err.message}</div>`;
    }
}

function renderClassificationCards(categories) {
    const grid = document.getElementById("classCardGrid");
    grid.innerHTML = "";

    if (categories.length === 0) {
        grid.innerHTML = `<div class="msg-box">No matching subject classifications found.</div>`;
        return;
    }

    categories.forEach(item => {
        const card = document.createElement("a");
        card.className = "classification-card";
        card.href = `list.html?classification=${encodeURIComponent(item.code.trim())}`;

        card.innerHTML = `
            <span class="class-card-code">${item.code}</span>
            <span class="class-card-text">${item.text}</span>
        `;

        grid.appendChild(card);
    });

    if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
        window.MathJax.typesetPromise();
    }
}

// 2. The Isolated Unified Search Engine
function setupUnifiedSearchEngine() {
    const searchInput = document.getElementById("classSearch");
    const dropdownMenu = document.getElementById("searchDropdownMenu");

    if (!searchInput || !dropdownMenu) return;

    searchInput.addEventListener("input", (e) => {
        const rawValue = e.target.value;
        const query = rawValue.trim().toLowerCase();

        clearTimeout(searchDebounceTimer);

        if (query.length < 3) {
            dropdownMenu.innerHTML = "";
            dropdownMenu.style.display = "none";
            return;
        }

        // Wait 250ms after the user pauses typing
        searchDebounceTimer = setTimeout(async () => {
            try {
                // A. Instant Local Memory Search: Find matching Categories
                const matchedClassifications = cachedClassifications.filter(c => 
                    c.code.toLowerCase().includes(query) || 
                    c.text.toLowerCase().includes(query)
                );

                // B. Backend Search: Find matching specific mathematical Concepts
                const response = await fetch(`${API_ENDPOINT}/math/concepts?q=${encodeURIComponent(rawValue.trim())}`);
                const json = await response.json();
                const matchedConcepts = json.status === "success" ? json.data : [];

                // C. Render both into the isolated drop-down menu
                renderUnifiedDropdownMenu(matchedConcepts, matchedClassifications, rawValue.trim(), dropdownMenu);

            } catch (err) {
                console.error("Instant search tracking error:", err);
            }
        }, 250);
    });

    // Close the dropdown overlay window if user clicks blank space
    document.addEventListener("click", (e) => {
        if (e.target !== searchInput && !dropdownMenu.contains(e.target)) {
            dropdownMenu.style.display = "none";
        }
    });
}

// 3. Dropdown Section Builder
function renderUnifiedDropdownMenu(concepts, classifications, query, container) {
    container.innerHTML = ""; 
    let combinedHtml = "";

    // Empty state fallback
    if (concepts.length === 0 && classifications.length === 0) {
        container.innerHTML = `<div class="dropdown-no-results" style="padding: 1rem; color: #64748b; font-style: italic; text-align: center;">No matches found for "${query}"</div>`;
        container.style.display = "block";
        return;
    }

    // SECTION 1: Matched Concepts
    if (concepts.length > 0) {
        combinedHtml += `
            <div style="background: #f8fafc; padding: 0.5rem 1rem; font-size: 0.75rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #e2e8f0;">
                Concepts
            </div>`;
            
        concepts.forEach(concept => {
            const primaryCode = concept.classification_codes.length > 0 ? concept.classification_codes[0] : null;
            const metaBadge = primaryCode ? `<span class="dropdown-row-meta">${primaryCode}</span>` : "";
            
            combinedHtml += `
                <a href="concept.html?slug=${concept.slug}" class="dropdown-item-row" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; text-decoration: none; color: #1e293b; border-bottom: 1px solid #f1f5f9;">
                    <span class="dropdown-row-title" style="font-weight: 500;">${concept.title}</span>
                    ${metaBadge}
                </a>`;
        });
    }

    // SECTION 2: Matched Classifications
    if (classifications.length > 0) {
        // Only draw a top border on the header if Concepts existed above it
        const borderTop = concepts.length > 0 ? 'border-top: 1px solid #e2e8f0;' : '';
        
        combinedHtml += `
            <div style="background: #f8fafc; padding: 0.5rem 1rem; font-size: 0.75rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #e2e8f0; ${borderTop}">
                Subject Directory
            </div>`;
            
        classifications.forEach(cls => {
            combinedHtml += `
                <a href="list.html?classification=${encodeURIComponent(cls.code.trim())}" class="dropdown-item-row" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; text-decoration: none; color: #1e293b; border-bottom: 1px solid #f1f5f9;">
                    <span class="dropdown-row-title" style="font-weight: 500;">${cls.text}</span>
                    <span class="dropdown-row-meta" style="font-family: monospace;">${cls.code}</span>
                </a>`;
        });
    }

    container.innerHTML = combinedHtml;
    container.style.display = "block";
}