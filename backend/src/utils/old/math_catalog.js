// frontend/math/math_catalog.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";

document.addEventListener("DOMContentLoaded", () => {
    bootClassificationHub();
});

async function bootClassificationHub() {
    const grid = document.getElementById("classCardGrid");
    try {
        const response = await fetch(`${API_ENDPOINT}/math/classifications`);
        const json = await response.json();
        
        if (json.status !== "success") throw new Error(json.message);
        
        renderClassificationCards(json.data);
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
        // Clean URL parameter handoff
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