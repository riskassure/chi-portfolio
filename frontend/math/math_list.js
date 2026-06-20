// frontend/math/math_list.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";
let currentCategoryCode = "";
let rawFilteredConcepts = [];
let queryMatchedConcepts = [];

// Option C Chunk Parameters
let currentRenderIndex = 0;
const CHUNK_SIZE = 25;

document.addEventListener("DOMContentLoaded", () => {
    // 1. Extract ?classification=CODE from URL query string parameters
    const urlParams = new URLSearchParams(window.location.search);
    currentCategoryCode = urlParams.get("classification");

    if (!currentCategoryCode) {
        document.getElementById("conceptListGrid").innerHTML = `<div class="msg-box">No valid classification parameter supplied.</div>`;
        return;
    }

    bootCategoryListView();
    setupListFilterEngine();
    document.getElementById("loadMoreBtn").addEventListener("click", () => appendNextConceptChunk());
});

// Open frontend/math/math_list.js and update this function block:

// Open frontend/math/math_list.js and replace your fetch logic block with this:

// frontend/math/math_list.js

async function bootCategoryListView() {
    const grid = document.getElementById("conceptListGrid");
    
    // Set baseline initial context header safely
    document.getElementById("listHeaderTitle").innerText = `Classification Sector: MSC ${currentCategoryCode.toUpperCase()}`;

    try {
        // 1. Fetch the concepts matching this classification code
        const response = await fetch(`${API_ENDPOINT}/math/concepts?classification=${encodeURIComponent(currentCategoryCode)}`);
        const json = await response.json();
        
        if (json.status !== "success") throw new Error(json.message);
        
        rawFilteredConcepts = json.data;
        queryMatchedConcepts = [...rawFilteredConcepts]; // Synchronize active filter array
        
        // 2. 🌟 NEW LOOKUP ENGINE: Fetch the master classification name from your lookup endpoint
        try {
            const classResponse = await fetch(`${API_ENDPOINT}/math/classifications`);
            const classJson = await classResponse.json();
            
            if (classJson.status === "success" && Array.isArray(classJson.data)) {
                // Find the master object where the code matches the URL parameter exactly
                const masterMatch = classJson.data.find(
                    item => item.code.trim().toLowerCase() === currentCategoryCode.trim().toLowerCase()
                );
                
                if (masterMatch && (masterMatch.text || masterMatch.name)) {
                    document.getElementById("listHeaderSubName").innerText = masterMatch.text || masterMatch.name;
                } else {
                    document.getElementById("listHeaderSubName").innerText = "Specialized Research Domain";
                }
            } else {
                document.getElementById("listHeaderSubName").innerText = "Specialized Research Domain";
            }
        } catch (lookupErr) {
            console.warn("Failed to fetch classification master text catalog:", lookupErr);
            document.getElementById("listHeaderSubName").innerText = "Specialized Research Domain";
        }
        
        // 3. Update descriptive counts
        document.getElementById("listHeaderDesc").innerText = `Found ${rawFilteredConcepts.length} specialized math entries associated with this group.`;
        
        // Trigger initial chunk card draw sequence
        resetAndDrawGridChunks();
    } catch (err) {
        grid.innerHTML = `<div class="msg-box">Failed to populate catalog list: ${err.message}</div>`;
    }
}

function resetAndDrawGridChunks() {
    currentRenderIndex = 0;
    document.getElementById("conceptListGrid").innerHTML = "";
    appendNextConceptChunk();
}

function appendNextConceptChunk() {
    const grid = document.getElementById("conceptListGrid");
    
    // Grab the next sliced segment from our matched data arrays
    const nextChunk = queryMatchedConcepts.slice(currentRenderIndex, currentRenderIndex + CHUNK_SIZE);
    
    if (nextChunk.length === 0 && currentRenderIndex === 0) {
        grid.innerHTML = `<div class="msg-box">No concepts found matching filter inputs.</div>`;
        document.getElementById("loadMoreContainer").style.display = "none";
        return;
    }

    nextChunk.forEach(item => {
        const card = document.createElement("a");
        card.className = "concept-card";
        card.href = `concept.html?slug=${item.slug}`;

        let tagsHtml = item.types.map(t => `<span class="math-tag tag-type">${t}</span>`).join("");
        tagsHtml += item.classification_codes.map(c => `<span class="math-tag tag-msc">${c}</span>`).join("");

        const formattedDate = item.updated_at ? item.updated_at.split(" ")[0] : "Legacy Source";

        card.innerHTML = `
            <div>
                <div class="card-title">${item.title}</div>
                <div class="card-tags">${tagsHtml}</div>
            </div>
            <div class="card-meta">
                <span>By ${item.owner || "CWoo"}</span>
                <span>Updated: ${formattedDate}</span>
            </div>
        `;
        grid.appendChild(card);
    });

    // Advance index bookmark position
    currentRenderIndex += nextChunk.length;

    // Toggle "Show More" visibility depending on whether more records remain in queue
    const loadMoreButtonContainer = document.getElementById("loadMoreContainer");
    if (currentRenderIndex < queryMatchedConcepts.length) {
        loadMoreButtonContainer.style.display = "block";
    } else {
        loadMoreButtonContainer.style.display = "none";
    }

    // Call MathJax typesetter promise over freshly injected nodes
    if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
        window.MathJax.typesetPromise();
    }
}

function setupListFilterEngine() {
    const filterInput = document.getElementById("conceptListSearch");
    
    filterInput.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase().trim();
        
        // Filter against the active category pool array
        queryMatchedConcepts = rawFilteredConcepts.filter(concept => {
            return concept.title.toLowerCase().includes(query) || 
                   concept.slug.toLowerCase().includes(query);
        });

        // Clear layout state and rebuild chunk cards dynamically
        resetAndDrawGridChunks();
    });
}