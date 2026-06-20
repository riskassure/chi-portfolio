// frontend/math/math_catalog.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";
let cachedConcepts = [];
let targetCategoryCode = null;

document.addEventListener("DOMContentLoaded", () => {
    bootMathArchive();
    attachQueryHandlers();
});

function attachQueryHandlers() {
    document.getElementById("clearFilter").addEventListener("click", () => resetMathFilters());
    
    // Wire up reactive directory type-searching
    document.getElementById("archiveSearch").addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase().trim();
        
        let baseline = cachedConcepts;
        if (targetCategoryCode) {
            baseline = baseline.filter(item => item.classification_codes.includes(targetCategoryCode));
        }

        const hits = baseline.filter(concept => {
            return concept.title.toLowerCase().includes(query) || 
                   concept.slug.toLowerCase().includes(query);
        });

        drawConceptGrid(hits);
    });
}

async function bootMathArchive() {
    try {
        await Promise.all([
            loadMscSidebar(),
            loadConceptPayloads()
        ]);
    } catch (err) {
        console.error("Archive sync error:", err);
    }
}

async function loadMscSidebar() {
    const list = document.getElementById("mscList");
    try {
        const response = await fetch(`${API_ENDPOINT}/math/classifications`);
        const json = await response.json();
        
        if (json.status !== "success") throw new Error(json.message);
        
        list.innerHTML = "";
        json.data.forEach(item => {
            const li = document.createElement("li");
            li.className = "msc-item";
            li.dataset.code = item.code;
            li.innerHTML = `<span class="msc-code">${item.code}</span> <span class="msc-text">${item.text}</span>`;
            
            li.addEventListener("click", () => selectMscCategory(item.code));
            list.appendChild(li);
        });
    } catch (err) {
        list.innerHTML = `<div class="msg-box">Error loading subject indices.</div>`;
    }
}

async function loadConceptPayloads(mscFilter = null) {
    const grid = document.getElementById("conceptGrid");
    let targetUrl = `${API_ENDPOINT}/math/concepts`;
    
    if (mscFilter) {
        targetUrl += `?classification=${encodeURIComponent(mscFilter)}`;
    }

    try {
        const response = await fetch(targetUrl);
        const json = await response.json();
        
        if (json.status !== "success") throw new Error(json.message);
        
        // Cache master results on baseline launch for clean text search fallback
        if (!mscFilter) {
            cachedConcepts = json.data;
        }
        
        drawConceptGrid(json.data);
    } catch (err) {
        grid.innerHTML = `<div class="msg-box">Error reading concept assets: ${err.message}</div>`;
    }
}

function drawConceptGrid(arrayData) {
    const grid = document.getElementById("conceptGrid");
    grid.innerHTML = "";

    if (arrayData.length === 0) {
        grid.innerHTML = `<div class="msg-box">No archived data matches matching metrics.</div>`;
        return;
    }

    arrayData.forEach(item => {
        const card = document.createElement("a");
        card.className = "concept-card";
        // Target subview file localized under the math/ subfolder context
        card.href = `concept.html?slug=${item.slug}`;

        let labelTags = item.types.map(t => `<span class="math-tag tag-type">${t}</span>`).join("");
        labelTags += item.classification_codes.map(c => `<span class="math-tag tag-msc">${c}</span>`).join("");

        const updatedDate = item.updated_at ? item.updated_at.split(" ")[0] : "Legacy Source";

        card.innerHTML = `
            <div>
                <div class="card-title">${item.title}</div>
                <div class="card-tags">${labelTags}</div>
            </div>
            <div class="card-meta">
                <span>Ref: ${item.owner || "CWoo"}</span>
                <span>Updated: ${updatedDate}</span>
            </div>
        `;

        grid.appendChild(card);
    });

    // Re-verify MathJax engine states for layout rendering
    if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
        window.MathJax.typesetPromise();
    }
}

function selectMscCategory(code) {
    targetCategoryCode = code;
    
    document.querySelectorAll(".msc-item").forEach(el => {
        el.classList.toggle("active", el.dataset.code === code);
    });

    const banner = document.getElementById("filterBanner");
    document.getElementById("filterLabel").innerText = `Subject Sector Category: MSC ${code}`;
    banner.style.display = "flex";

    loadConceptPayloads(code);
}

function resetMathFilters() {
    targetCategoryCode = null;
    document.getElementById("filterBanner").style.display = "none";
    document.getElementById("archiveSearch").value = "";
    
    document.querySelectorAll(".msc-item").forEach(el => el.classList.remove("active"));
    drawConceptGrid(cachedConcepts);
}