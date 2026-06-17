let currentPage = 1;
const recordsPerPage = 25;
let masterMusicData = []; // Global scope for data access across helper functions

// Unified Column Metadata Registry
const FIELD_REGISTRY = {
    spotify_playlist: { label: "Source Playlist", isCore: true,  type: "string" },
    genre:            { label: "Genre",           isCore: true,  type: "string" },
    composition_name: { label: "Composition",     isCore: true,  type: "string" },
    track_name:       { label: "Track Name",      isCore: true,  type: "string" },
    composer:         { label: "Composer",        isCore: true,  type: "string" },
    performer:        { label: "Performer(s)",    isCore: true,  type: "string" },
    album_name:       { label: "Album Context",   isCore: true,  type: "string" },
    
    release_date:     { label: "Released",        isCore: false, type: "string", defaultOn: true },
    duration_string:  { label: "Length",          isCore: false, type: "string", defaultOn: true },
    popularity:       { label: "Popularity",      isCore: false, type: "number", defaultOn: false }
};

let activeOptionalColumns = Object.keys(FIELD_REGISTRY).filter(key => !FIELD_REGISTRY[key].isCore && FIELD_REGISTRY[key].defaultOn);

let activeFilters = {
    spotify_playlist: "all",
    searchQuery: ""
};

let sortSequence = [];
let isAdmin = false; // Managed dynamically via navbar.js hook

// Main Execution Initialization Hook
document.addEventListener("DOMContentLoaded", () => {
    setupEventListeners();
    loadMusicData(); 
});

// 🛠️ HOOK: Called automatically by navbar.js ONLY if authenticated!
function unlockLocalPageControls() {
    isAdmin = true;
    const adminDock = document.getElementById('admin-controls-dock');
    if (adminDock) {
        adminDock.style.display = 'flex'; // Reveals inline admin interface panel
    }
}

// Fetch live backend metrics
function loadMusicData() {
    fetch(`http://127.0.0.1:5000/api/music?page=${currentPage}&per_page=${recordsPerPage}`, {
        credentials: "include"
    })
        .then(response => response.json())
        .then(payload => {
            masterMusicData = payload.data; 
            buildColumnCheckboxes();
            populatePlaylistFilter(payload.data);
            processAndRenderTable();
            renderPaginationButtons(payload.total_pages, payload.page);
        })
        .catch(err => {
            console.error("Database connection failed:", err);
            document.getElementById("table-body").innerHTML = `<tr><td colspan="12" style="text-align:center; color:#e74c3c;">⚠️ Connection failed. Check app server logs.</td></tr>`;
        });
}

// Generate option switches for optional analysis trackers
function buildColumnCheckboxes() {
    const dock = document.getElementById("column-checkboxes");
    if (!dock) return;
    dock.innerHTML = "";

    Object.keys(FIELD_REGISTRY).forEach(key => {
        const config = FIELD_REGISTRY[key];
        if (config.isCore) return;

        const labelEl = document.createElement("label");
        labelEl.style.cssText = "cursor: pointer; display: flex; align-items: center; gap: 5px;";

        const chk = document.createElement("input");
        chk.type = "checkbox";
        chk.value = key;
        chk.checked = activeOptionalColumns.includes(key);

        chk.addEventListener("change", (e) => {
            if (e.target.checked) {
                if (!activeOptionalColumns.includes(key)) activeOptionalColumns.push(key);
            } else {
                activeOptionalColumns = activeOptionalColumns.filter(k => k !== key);
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
    if (!select || select.options.length > 1) return; 
    
    const uniquePlaylists = [...new Set(data.map(item => item.spotify_playlist).filter(Boolean))];
    uniquePlaylists.sort().forEach(p => {
        const opt = document.createElement("option");
        opt.value = p; 
        opt.textContent = p;
        select.appendChild(opt);
    });
}

function getActiveViewportColumns() {
    const coreKeys = Object.keys(FIELD_REGISTRY).filter(k => FIELD_REGISTRY[k].isCore);
    return [...coreKeys, ...activeOptionalColumns];
}

function processAndRenderTable() {
    const currentFields = getActiveViewportColumns();

    // STAGE 1: FILTER RUNNEL
    let processedData = masterMusicData.filter(item => {
        if (activeFilters.spotify_playlist !== "all" && item.spotify_playlist !== activeFilters.spotify_playlist) {
            return false;
        }
        if (activeFilters.searchQuery) {
            const query = activeFilters.searchQuery.toLowerCase();
            const matchFound = currentFields.some(fieldKey => {
                const val = item[fieldKey];
                return val && val.toString().toLowerCase().includes(query);
            });
            if (!matchFound) return false;
        }
        return true;
    });

    // STAGE 2: TYPE-AWARE SEQUENTIAL SORT
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

    // STAGE 3: OUTPUT GENERATION
    generateTableHeaders(currentFields);
    renderTableBody(processedData, currentFields);
    updateSortUI();
}

function generateTableHeaders(fields) {
    const headerRow = document.getElementById("table-headers");
    if (!headerRow) return;
    headerRow.innerHTML = "";

    fields.forEach(fieldKey => {
        const config = FIELD_REGISTRY[fieldKey];
        const th = document.createElement("th");
        th.className = "sortable-header";
        th.setAttribute("data-column", fieldKey);
        th.style.cssText = "padding: 12px; border: 1px solid #34495e; cursor: pointer; user-select: none;";
        th.innerHTML = `${config.label} <span class="sort-icon">↕</span>`;
        
        th.addEventListener("click", () => handleHeaderClick(fieldKey));
        headerRow.appendChild(th);
    });

    const linkTh = document.createElement("th");
    linkTh.style.cssText = "padding: 12px; border: 1px solid #34495e;";
    linkTh.textContent = "Link";
    headerRow.appendChild(linkTh);
}

function renderTableBody(dataList, fields) {
    const tableBody = document.getElementById("table-body");
    if (!tableBody) return;
    tableBody.innerHTML = "";
    const totalColumnsSpan = fields.length + 1;

    if (dataList.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="${totalColumnsSpan}" style="text-align:center; color:#7f8c8d; padding:20px;">No music records matched those parameters.</td></tr>`;
        return;
    }

    dataList.forEach(item => {
        const row = document.createElement("tr");
        if (item.track_id) row.setAttribute("data-id", item.track_id);
        
        let innerCellsHTML = "";

        fields.forEach(fieldKey => {
            let cellValue = item[fieldKey];
            if (cellValue === null || cellValue === undefined || cellValue === "") {
                cellValue = '<span style="color:#bbb;">--</span>';
            }

            if (fieldKey === 'composition_name') {
                innerCellsHTML += `<td data-field="composition_name" style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>${cellValue}</strong> <small style="color:#7f8c8d;">${item.unit_name || ''}</small></td>`;
            } else if (fieldKey === 'spotify_playlist') {
                innerCellsHTML += `<td data-field="spotify_playlist" style="padding: 10px; border-bottom: 1px solid #ddd; color: #7f8c8d; font-size: 0.9em;">${cellValue}</td>`;
            } else if (fieldKey === 'popularity' && typeof item[fieldKey] === 'number') {
                innerCellsHTML += `
                    <td data-field="popularity" style="padding: 10px; border-bottom: 1px solid #ddd;">
                        <div style="background: #eee; width: 50px; border-radius: 3px; overflow: hidden;">
                            <div style="background: #3498db; height: 6px; width: ${item[fieldKey]}%"></div>
                        </div>
                    </td>`;
            } else {
                innerCellsHTML += `<td data-field="${fieldKey}" style="padding: 10px; border-bottom: 1px solid #ddd;">${cellValue}</td>`;
            }
        });

        const linkTag = item.track_id 
            ? `<button onclick="playTrackInline('${item.track_id}')" style="background: #1ed760; color: white; border: none; padding: 6px 12px; border-radius: 20px; font-weight: bold; cursor: pointer; font-size: 0.85em;">Load Player 🎧</button>` 
            : `<span style="color:#ccc;">Unavailable</span>`;

        innerCellsHTML += `<td style="padding: 10px; border-bottom: 1px solid #ddd;">${linkTag}</td>`;
        row.innerHTML = innerCellsHTML;
        tableBody.appendChild(row);
    });
}

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
    const playlistFilter = document.getElementById("filter-playlist");
    playlistFilter?.addEventListener("change", (e) => {
        activeFilters.spotify_playlist = e.target.value;
        processAndRenderTable();
    });

    const searchBar = document.getElementById("search-bar");
    searchBar?.addEventListener("input", (e) => {
        activeFilters.searchQuery = e.target.value;
        processAndRenderTable();
    });

    document.getElementById("reset-filters")?.addEventListener("click", () => {
        activeFilters = { spotify_playlist: "all", searchQuery: "" };
        sortSequence = [];
        activeOptionalColumns = Object.keys(FIELD_REGISTRY).filter(key => !FIELD_REGISTRY[key].isCore && FIELD_REGISTRY[key].defaultOn);
        
        if (playlistFilter) playlistFilter.value = "all";
        if (searchBar) searchBar.value = "";
        
        buildColumnCheckboxes();
        processAndRenderTable();
    });

    // Wire up Action Buttons directly
    document.getElementById("admin-edit-btn")?.addEventListener("click", enterTableEditMode);
    document.getElementById("admin-cancel-btn")?.addEventListener("click", () => exitTableEditMode(false));
    document.getElementById("admin-save-btn")?.addEventListener("click", saveTableChanges);
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
            iconSpan.innerHTML = `${rule.direction === "asc" ? "↑" : "↓"} <sub>(${sequenceIndex + 1})</sub>`;
            header.style.color = "#1ed760"; 
        }
    });
}

window.playTrackInline = function(trackId) {
    const dock = document.getElementById("spotify-player-dock");
    if (!dock) return;
    
    dock.innerHTML = `
        <iframe src="https://open.spotify.com/embed/track/$${trackId}?utm_source=generator&theme=0" 
                width="100%" height="90" frameBorder="0" allowfullscreen="" 
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"
                style="border-radius: 12px;">
        </iframe>`;
    dock.style.bottom = "20px";
};

function renderPaginationButtons(totalPages, activePage) {
    const controlsContainer = document.getElementById("pagination-controls");
    if (!controlsContainer) return;
    controlsContainer.innerHTML = "";
    
    const prevBtn = document.createElement("button");
    prevBtn.innerText = "◀ Prev";
    prevBtn.disabled = activePage === 1;
    prevBtn.style.cssText = "padding: 6px 12px; font-weight: bold; cursor: pointer; border-radius: 4px; border: 1px solid #ccc; background: white;";
    if (!prevBtn.disabled) prevBtn.onclick = () => { currentPage--; loadMusicData(); };
    controlsContainer.appendChild(prevBtn);
    
    let startPage = Math.max(1, activePage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);

    for (let i = startPage; i <= endPage; i++) {
        if (i < 1 || i > totalPages) continue;
        const pageBtn = document.createElement("button");
        pageBtn.innerText = i;
        pageBtn.style.cssText = `padding: 6px 12px; border-radius: 4px; border: 1px solid #ccc; cursor: pointer; ${i === activePage ? 'background: #3498db; color: white; font-weight: bold;' : 'background: white;'}`;
        pageBtn.onclick = () => { currentPage = i; loadMusicData(); };
        controlsContainer.appendChild(pageBtn);
    }
    
    const nextBtn = document.createElement("button");
    nextBtn.innerText = "Next ▶";
    nextBtn.disabled = activePage === totalPages;
    nextBtn.style.cssText = "padding: 6px 12px; font-weight: bold; cursor: pointer; border-radius: 4px; border: 1px solid #ccc; background: white;";
    if (!nextBtn.disabled) nextBtn.onclick = () => { currentPage++; loadMusicData(); };
    controlsContainer.appendChild(nextBtn);
}

// ==========================================================================
// TRANSFORMATION AND DATABASE COMMIT ENGINES
// ==========================================================================

let originalRowDataBackup = [];

function enterTableEditMode() {
    const tableBody = document.getElementById("table-body");
    if (!tableBody) return;

    document.getElementById("admin-edit-btn").style.display = "none";
    document.getElementById("admin-save-btn").style.display = "inline-block";
    document.getElementById("admin-cancel-btn").style.display = "inline-block";

    originalRowDataBackup = [];
    const editableColumns = ["genre", "composition_name", "track_name", "composer", "performer"];

    const rows = tableBody.getElementsByTagName("tr");
    for (let row