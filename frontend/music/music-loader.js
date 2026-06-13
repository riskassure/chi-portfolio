document.addEventListener("DOMContentLoaded", () => {
    // Single Source of Truth
    let masterMusicData = [];
    
    // 1. Unified Column Metadata Registry
    const FIELD_REGISTRY = {
        // --- CORE COLUMNS (Permanently Frozen in Grid) ---
        spotify_playlist: { label: "Source Playlist", isCore: true,  type: "string" },
        genre:            { label: "Genre",           isCore: true,  type: "string" },
        composition_name: { label: "Composition",     isCore: true,  type: "string" },
        track_name:       { label: "Track Name",      isCore: true,  type: "string" },
        composer:         { label: "Composer",        isCore: true,  type: "string" },
        performer:        { label: "Performer(s)",    isCore: true,  type: "string" },
        album_name:       { label: "Album Context",   isCore: true,  type: "string" },
        
        // --- ANALYTICS COLUMNS (Toggleable by User) ---
        release_date:     { label: "Released",        isCore: false, type: "string", defaultOn: true },
        duration_string:  { label: "Length",          isCore: false, type: "string", defaultOn: true },
        popularity:       { label: "Popularity",      isCore: false, type: "number", defaultOn: false }
    };

    // Tracks which optional column keys are currently active
    let activeOptionalColumns = Object.keys(FIELD_REGISTRY).filter(key => !FIELD_REGISTRY[key].isCore && FIELD_REGISTRY[key].defaultOn);

    // Active Filters Matrix
    let activeFilters = {
        spotify_playlist: "all",
        searchQuery: ""
    };

    // Sequential Sorting Array Queue
    let sortSequence = [];

    // Fetch live backend metrics
    fetch("http://127.0.0.1:5000/api/music")
        .then(response => response.json())
        .then(data => {
            masterMusicData = data;
            buildColumnCheckboxes();
            populatePlaylistFilter(data);
            processAndRenderTable();
            setupEventListeners();
        })
        .catch(err => {
            console.error("Error connecting to database gateway:", err);
            document.getElementById("table-body").innerHTML = `<tr><td colspan="12" style="text-align:center; color:#e74c3c; padding:20px;">⚠️ Connection to local backend database failed. Check your app server configuration.</td></tr>`;
        });

    // Generate option switches for optional analysis trackers
    function buildColumnCheckboxes() {
        const dock = document.getElementById("column-checkboxes");
        dock.innerHTML = "";

        Object.keys(FIELD_REGISTRY).forEach(key => {
            const config = FIELD_REGISTRY[key];
            if (config.isCore) return; // Skip core items

            const labelEl = document.createElement("label");
            labelEl.style.cursor = "pointer";
            labelEl.style.display = "flex";
            labelEl.style.alignItems = "center";
            labelEl.style.gap = "5px";

            const chk = document.createElement("input");
            chk.type = "checkbox";
            chk.value = key;
            chk.checked = config.defaultOn;

            chk.addEventListener("change", (e) => {
                if (e.target.checked) {
                    if (!activeOptionalColumns.includes(key)) activeOptionalColumns.push(key);
                } else {
                    activeOptionalColumns = activeOptionalColumns.filter(k => k !== key);
                    // Drop from active sort criteria if hidden
                    sortSequence = sortSequence.filter(rule => rule.column !== key);
                }
                processAndRenderTable();
            });

            labelEl.appendChild(chk);
            labelEl.appendChild(document.createTextNode(config.label));
            dock.appendChild(labelEl);
        });
    }

    function populatePlaylistFilter(data) {
        const select = document.getElementById("filter-playlist");
        const uniquePlaylists = [...new Set(data.map(item => item.spotify_playlist).filter(Boolean))];
        uniquePlaylists.sort().forEach(p => {
            const opt = document.createElement("option");
            opt.value = p; opt.textContent = p;
            select.appendChild(opt);
        });
    }

    // Return complete array mapping of active viewport columns
    function getActiveViewportColumns() {
        const coreKeys = Object.keys(FIELD_REGISTRY).filter(k => FIELD_REGISTRY[k].isCore);
        return [...coreKeys, ...activeOptionalColumns];
    }

    // 2. The Core Pipeline Engine
    function processAndRenderTable() {
        const currentFields = getActiveViewportColumns();

        // --- GENERALIZED STAGE 1: FILTER RUNNEL ---
        let processedData = masterMusicData.filter(item => {
            if (activeFilters.spotify_playlist !== "all" && item.spotify_playlist !== activeFilters.spotify_playlist) {
                return false;
            }
            
            if (activeFilters.searchQuery) {
                const query = activeFilters.searchQuery.toLowerCase();
                
                // Scan only the visible subset of layout cells
                const matchFound = currentFields.some(fieldKey => {
                    const val = item[fieldKey];
                    return val && val.toString().toLowerCase().includes(query);
                });
                
                if (!matchFound) return false;
            }
            return true;
        });

        // --- GENERALIZED STAGE 2: TYPE-AWARE SEQUENTIAL SORT ---
        if (sortSequence.length > 0) {
            processedData.sort((a, b) => {
                for (let sortRule of sortSequence) {
                    const col = sortRule.column;
                    const dir = sortRule.direction === "asc" ? 1 : -1;
                    const dataType = FIELD_REGISTRY[col]?.type || "string";

                    let valA = a[col] !== null && a[col] !== undefined ? a[col] : "";
                    let valB = b[col] !== null && b[col] !== undefined ? b[col] : "";

                    if (dataType === "number") {
                        if (Number(valA) !== Number(valB)) {
                            return (Number(valA) - Number(valB)) * dir;
                        }
                    } else {
                        let strA = valA.toString().toLowerCase();
                        let strB = valB.toString().toLowerCase();
                        if (strA < strB) return -1 * dir;
                        if (strA > strB) return 1 * dir;
                    }
                }
                return 0;
            });
        }

        // --- STAGE 3: OUTPUT GENERATION ---
        generateTableHeaders(currentFields);
        renderTableBody(processedData, currentFields);
        updateSortUI();
    }

    // 3. Dynamic Structural DOM Manipulation
    function generateTableHeaders(fields) {
        const headerRow = document.getElementById("table-headers");
        headerRow.innerHTML = "";

        fields.forEach(fieldKey => {
            const config = FIELD_REGISTRY[fieldKey];
            const th = document.createElement("th");
            th.className = "sortable-header";
            th.setAttribute("data-column", fieldKey);
            th.style.padding = "12px";
            th.style.border = "1px solid #34495e";
            th.style.cursor = "pointer";
            th.style.userSelect = "none";
            th.innerHTML = `${config.label} <span class="sort-icon">↕</span>`;
            
            // Re-bind click event hookups to dynamically generated elements
            th.addEventListener("click", () => handleHeaderClick(fieldKey));
            headerRow.appendChild(th);
        });

        // Append explicit trailing Link column header
        const linkTh = document.createElement("th");
        linkTh.style.padding = "12px";
        linkTh.style.border = "1px solid #34495e";
        linkTh.textContent = "Link";
        headerRow.appendChild(linkTh);
    }

    function renderTableBody(dataList, fields) {
        const tableBody = document.getElementById("table-body");
        tableBody.innerHTML = "";
        const totalColumnsSpan = fields.length + 1;

        if (dataList.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="${totalColumnsSpan}" style="text-align:center; color:#7f8c8d; padding:20px;">No music records matched those parameters.</td></tr>`;
            return;
        }

        dataList.forEach(item => {
            const row = document.createElement("tr");
            let innerCellsHTML = "";

            // Loop strictly through active fields registry list to populate cells orderly
            fields.forEach(fieldKey => {
                let cellValue = item[fieldKey];
                
                // Apply fallback representations for blank curated values
                if (cellValue === null || cellValue === undefined || cellValue === "") {
                    cellValue = '<span style="color:#bbb;">--</span>';
                }

                // Add styling variations based on layout classes
                if (fieldKey === 'composition_name') {
                    innerCellsHTML += `<td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>${cellValue}</strong> <small style="color:#7f8c8d;">${item.unit_name || ''}</small></td>`;
                } else if (fieldKey === 'spotify_playlist') {
                    innerCellsHTML += `<td style="padding: 10px; border-bottom: 1px solid #ddd; color: #7f8c8d; font-size: 0.9em;">${cellValue}</td>`;
                } else if (fieldKey === 'popularity' && typeof item[fieldKey] === 'number') {
                    innerCellsHTML += `
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                            <div style="background: #eee; width: 50px; border-radius: 3px; overflow: hidden;">
                                <div style="background: #3498db; height: 6px; width: ${item[fieldKey]}%"></div>
                            </div>
                        </td>`;
                } else {
                    innerCellsHTML += `<td style="padding: 10px; border-bottom: 1px solid #ddd;">${cellValue}</td>`;
                }
            });

            // Handle track URLs on the fly
            const secureSpotifyUrl = item.track_id ? `https://open.spotify.com/track/${item.track_id}` : "#";
            // Locate where you handle track URLs inside dataList.forEach loop:
            const linkTag = item.track_id 
                ? `<button onclick="playTrackInline('${item.track_id}')" style="background: #1ed760; color: white; border: none; padding: 6px 12px; border-radius: 20px; font-weight: bold; cursor: pointer; font-size: 0.85em; transition: transform 0.1s;">Load Player 🎧</button>` 
                : `<span style="color:#ccc;">Unavailable</span>`;

            innerCellsHTML += `<td style="padding: 10px; border-bottom: 1px solid #ddd;">${linkTag}</td>`;
            row.innerHTML = innerCellsHTML;
            tableBody.appendChild(row);
        });
    }

    // 4. Input Listener Management
    function handleHeaderClick(column) {
        let existingIndex = sortSequence.findIndex(rule => rule.column === column);

        if (existingIndex === -1) {
            sortSequence.push({ column: column, direction: "asc" });
        } else if (sortSequence[existingIndex].direction === "asc") {
            sortSequence[existingIndex].direction = "desc";
        } else {
            sortSequence.splice(existingIndex, 1);
        }
        processAndRenderTable();
    }

    function setupEventListeners() {
        document.getElementById("filter-playlist").addEventListener("change", (e) => {
            activeFilters.spotify_playlist = e.target.value;
            processAndRenderTable();
        });

        document.getElementById("search-bar").addEventListener("input", (e) => {
            activeFilters.searchQuery = e.target.value;
            processAndRenderTable();
        });

        document.getElementById("reset-filters").addEventListener("click", () => {
            activeFilters = { spotify_playlist: "all", searchQuery: "" };
            sortSequence = [];
            
            // Restore default optional configuration arrays
            activeOptionalColumns = Object.keys(FIELD_REGISTRY).filter(key => !FIELD_REGISTRY[key].isCore && FIELD_REGISTRY[key].defaultOn);
            
            document.getElementById("filter-playlist").value = "all";
            document.getElementById("search-bar").value = "";
            
            buildColumnCheckboxes();
            processAndRenderTable();
        });
    }

    function updateSortUI() {
        document.querySelectorAll(".sortable-header").forEach(header => {
            const column = header.getAttribute("data-column");
            const iconSpan = header.querySelector(".sort-icon");
            if (!iconSpan) return;

            let sequenceIndex = sortSequence.findIndex(rule => rule.column === column);

            if (sequenceIndex === -1) {
                iconSpan.innerHTML = "↕";
                header.style.color = "white";
            } else {
                const rule = sortSequence[sequenceIndex];
                const arrow = rule.direction === "asc" ? "↑" : "↓";
                iconSpan.innerHTML = `${arrow} <sub>(${sequenceIndex + 1})</sub>`;
                header.style.color = "#1ed760"; 
            }
        });
    }
});

// Global execution function to swap tracks inside the sticky widget dock
window.playTrackInline = function(trackId) {
    const dock = document.getElementById("spotify-player-dock");
    
    // Set up the standard modern responsive Spotify Embed URL string
    const embedUrl = `https://open.spotify.com/embed/track/${trackId}?utm_source=generator&theme=0`;
    
    // Inject the native secure player iframe block code
    dock.innerHTML = `
        <iframe 
            src="${embedUrl}" 
            width="100%" 
            height="90" 
            frameBorder="0" 
            allowfullscreen="" 
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" 
            loading="lazy"
            style="border-radius: 12px;">
        </iframe>
    `;
    
    // Smoothly slide the interactive audio dock up onto the user's screen layout
    dock.style.bottom = "20px";
};