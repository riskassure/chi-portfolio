document.addEventListener("DOMContentLoaded", () => {
    // State variables to track our single source of truth
    let masterMusicData = [];
    
    // Tracks active filters: { column_name: selected_value }
    let activeFilters = {
        genre: "all",
        period: "all",
        type: "all"
    };

    // Tracks multi-column sort sequence: [ { column: "composer", direction: "asc" }, { column: "piece", direction: "desc" } ]
    let sortSequence = [];

    // 1. Fetch the data from our vault
    fetch("music-data.json")
        .then(response => response.json())
        .then(data => {
            masterMusicData = data;
            processAndRenderTable(); // Initial draw of the table
            setupEventListeners();   // Wire up user interactions
        })
        .catch(err => console.error("Error loading music database:", err));

    // 2. The Core Pipeline Engine
    function processAndRenderTable() {
        // --- STAGE 1: MULTI-COLUMN FILTERING ---
        let processedData = masterMusicData.filter(item => {
            for (let key in activeFilters) {
                if (activeFilters[key] !== "all" && item[key] !== activeFilters[key]) {
                    return false; // Drops the song if it fails any active filter
                }
            }
            return true;
        });

        // --- STAGE 2: MULTI-COLUMN SEQUENTIAL SORTING ---
        if (sortSequence.length > 0) {
            processedData.sort((a, b) => {
                // Loop through our sorting sequence layer by layer
                for (let sortRule of sortSequence) {
                    const col = sortRule.column;
                    const dir = sortRule.direction === "asc" ? 1 : -1;

                    // Standard string comparison
                    let valA = a[col].toString().toLowerCase();
                    let valB = b[col].toString().toLowerCase();

                    if (valA < valB) return -1 * dir;
                    if (valA > valB) return 1 * dir;
                    
                    // If it's a tie, the loop continues to the next sortRule in line
                }
                return 0; // Absolute tie across all sequenced columns
            });
        }

        // --- STAGE 3: RENDER TO SCREEN ---
        renderTable(processedData);
        updateSortUI();
    }

    // 3. Render HTML Rows
    function renderTable(dataList) {
        const tableBody = document.getElementById("table-body");
        tableBody.innerHTML = "";

        if (dataList.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:#7f8c8d; padding:20px;">No pieces match the selected criteria.</td></tr>`;
            return;
        }

        dataList.forEach(item => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${item.genre}</td>
                <td>${item.period}</td>
                <td>${item.type}</td>
                <td>${item.subtype}</td>
                <td><strong>${item.piece}</strong></td>
                <td>${item.composer}</td>
                <td>${item.performer}</td>
                <td><a href="${item.spotify}" target="_blank" class="spotify-link">Listen 🎧</a></td>
            `;
            tableBody.appendChild(row);
        });
    }

    // 4. Setup Event Listeners for Filters and Table Headers
    function setupEventListeners() {
        // Dropdown Filters
        document.getElementById("filter-genre").addEventListener("change", (e) => {
            activeFilters.genre = e.target.value;
            processAndRenderTable();
        });
        document.getElementById("filter-period").addEventListener("change", (e) => {
            activeFilters.period = e.target.value;
            processAndRenderTable();
        });
        document.getElementById("filter-type").addEventListener("change", (e) => {
            activeFilters.type = e.target.value;
            processAndRenderTable();
        });

        // Clear All Button
        document.getElementById("reset-filters").addEventListener("click", () => {
            activeFilters = { genre: "all", period: "all", type: "all" };
            sortSequence = [];
            
            // Reset physical dropdown menus
            document.getElementById("filter-genre").value = "all";
            document.getElementById("filter-period").value = "all";
            document.getElementById("filter-type").value = "all";
            
            processAndRenderTable();
        });

        // Clickable Table Headers (Multi-Column Logic)
        document.querySelectorAll(".sortable-header").forEach(header => {
            header.addEventListener("click", () => {
                const column = header.getAttribute("data-column");
                
                // Check if this column is already part of our active sort sequence
                let existingIndex = sortSequence.findIndex(rule => rule.column === column);

                if (existingIndex === -1) {
                    // Step A: First time clicking column -> Add to the end of the sorting sequence queue (Ascending)
                    sortSequence.push({ column: column, direction: "asc" });
                } else if (sortSequence[existingIndex].direction === "asc") {
                    // Step B: Second click -> Toggle to Descending
                    sortSequence[existingIndex].direction = "desc";
                } else {
                    // Step C: Third click -> Remove from sort sequence entirely (Neutral)
                    sortSequence.splice(existingIndex, 1);
                }

                processAndRenderTable();
            });
        });
    }

    // 5. Update Header Icons and Numbers to Show Sequence
    function updateSortUI() {
        document.querySelectorAll(".sortable-header").forEach(header => {
            const column = header.getAttribute("data-column");
            const iconSpan = header.querySelector(".sort-icon");
            
            let sequenceIndex = sortSequence.findIndex(rule => rule.column === column);

            if (sequenceIndex === -1) {
                iconSpan.innerHTML = "↕";
                header.style.color = "white";
            } else {
                const rule = sortSequence[sequenceIndex];
                const arrow = rule.direction === "asc" ? "↑" : "↓";
                // Show direction along with sequence level (e.g., 1st sort, 2nd sort)
                iconSpan.innerHTML = `${arrow} <sub>(${sequenceIndex + 1})</sub>`;
                header.style.color = "#1ed760"; // Highlight active sorted headers in Spotify green
            }
        });
    }
});