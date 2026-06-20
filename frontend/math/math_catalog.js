// frontend/math/math_catalog.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";
let cachedClassifications = [];

document.addEventListener("DOMContentLoaded", () => {
    bootClassificationHub();
    setupClassificationSearch();
});

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
        // Generate classification card anchor linking out to the item list view
        const card = document.createElement("a");
        card.className = "classification-card";
        card.href = `list.html?classification=${encodeURIComponent(item.code)}`;

        card.innerHTML = `
            <span class="class-card-code">${item.code}</span>
            <span class="class-card-text">${item.text}</span>
        `;

        grid.appendChild(card);
    });

    // Invoke MathJax in case any classification description text strings utilize TeX strings
    if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
        window.MathJax.typesetPromise();
    }
}

function setupClassificationSearch() {
    const searchInput = document.getElementById("classSearch");
    
    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase().trim();
        
        const filtered = cachedClassifications.filter(item => {
            return item.code.toLowerCase().includes(query) || 
                   item.text.toLowerCase().includes(query);
        });

        renderClassificationCards(filtered);
    });
}