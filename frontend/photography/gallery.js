// frontend/photography/gallery.js

const API_URL = "http://127.0.0.1:5000/api/photography/current";
const ROTATE_URL = "http://127.0.0.1:5000/api/photography/rotate";
const UPDATE_URL = "http://127.0.0.1:5000/api/photography/update";
const galleryContainer = document.getElementById("photography-gallery");

// Global mutable view states for runtime configuration
let isAdmin = false;
let photoPageSize = 3;         // Curation Grid Density limit variable
let refreshIntervalMinutes = 5; // Museum cycle execution pace anchor
let rotationTimerId = null;    // Tracks the background window interval loop

// 🛠️ HOOK: Called automatically by navbar.js ONLY if authenticated!
function unlockLocalPageControls() {
    isAdmin = true; // Flip the local layout state switch to enable editing cards
    
    const adminDock = document.getElementById('admin-controls-dock');
    if (!adminDock) return;
    
    // Force the admin controls bar to remain completely STICKY at the top of the viewport
    adminDock.style.cssText = "display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; min-height: 45px; background-color: #34495e; position: sticky; top: 0; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.15);";

    // Safeguard - if control panel already exists, do NOT duplicate it
    if (document.getElementById('admin-gallery-controls')) {
        const sizeSelect = document.getElementById('photo-size-select');
        if (sizeSelect) {
            sizeSelect.value = photoPageSize.toString();
        }
        return;
    }

    // Build the dynamic curation control module deck panel
    const controlDeck = document.createElement('div');
    controlDeck.id = 'admin-gallery-controls';
    controlDeck.style.cssText = "display: flex; align-items: center; gap: 24px; margin-left: auto; font-family: Arial, sans-serif; font-size: 14px; font-weight: bold;";

    controlDeck.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #ffffff !important; display: inline-block; white-space: nowrap; font-weight: bold; font-size: 14px;">Grid Density Limit:</span>
            <select id="photo-size-select" style="padding: 6px 10px; border-radius: 4px; background: #2c3e50; color: white; border: 1px solid #1abc9c; cursor: pointer; font-weight: bold; font-size: 13px;">
                <option value="3">3 Photos</option>
                <option value="6">6 Photos</option>
                <option value="9">9 Photos</option>
                <option value="12">12 Photos</option>
            </select>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #ffffff !important; display: inline-block; white-space: nowrap; font-weight: bold; font-size: 14px;">Exhibition Cycle Pace:</span>
            <div style="display: flex; align-items: center; gap: 6px;">
                <input type="number" id="photo-refresh-input" value="${refreshIntervalMinutes}" min="1" max="60" style="width: 55px; padding: 5px; border-radius: 4px; border: 1px solid #1abc9c; background: #2c3e50; color: white; text-align: center; font-weight: bold; font-size: 13px;">
                <span style="font-size: 13px; color: #bdc3c7; font-weight: normal; white-space: nowrap;">minutes</span>
            </div>
        </div>
    `;

    adminDock.appendChild(controlDeck);

    // Sync dropdown layout view state to global state memory baseline
    const sizeSelect = document.getElementById('photo-size-select');
    if (sizeSelect) {
        sizeSelect.value = photoPageSize.toString();
    }

    // Wire listeners up to synchronize memory metrics on user changes
    sizeSelect.addEventListener('change', (e) => {
        photoPageSize = parseInt(e.target.value, 10);
        triggerSmoothExhibitionRefresh(true); // Mutate on manual selection change
    });

    document.getElementById('photo-refresh-input').addEventListener('input', (e) => {
        let val = parseInt(e.target.value, 10);
        if (isNaN(val) || val < 1) val = 1;
        refreshIntervalMinutes = val;
        initializeMuseumExhibitionLoop(); 
    });

    // 🛡️ RE-RENDER STEP: Redraw the cards we already have to append the editor input panels
    // without making any network calls or mutating database records.
    triggerSmoothExhibitionRefresh(false);
}

// Helper to construct the dynamic cards on the page from a list of records
function renderGalleryCards(photoList) {
    galleryContainer.innerHTML = "";

    // 🎯 VISUAL DROPDOWN LOCK: Explicitly force the control dropdown 
    // to match the actual number of photo cards rendered on the screen.
    const sizeSelect = document.getElementById('photo-size-select');
    if (sizeSelect && photoList && photoList.length > 0) {
        sizeSelect.value = photoList.length.toString();
    }

    if (!photoList || photoList.length === 0) {
        galleryContainer.innerHTML = `<p class="empty-msg" style="color: #7f8c8d; text-align:center; grid-column: 1/-1; padding: 40px;">No active landscape assets selected.</p>`;
        return;
    }

    photoList.forEach(photo => {
        try {
            const imageSourcePath = `../${photo.file_path || ''}`;
            const photoTitleClean = photo.title || 'Untitled Landscape';
            
            const locationMarkup = isAdmin 
                ? `
                    <div class="admin-edit-panel" style="margin-top: 14px; background: #f8fafc; padding: 12px; border-radius: 4px; border: 1px solid #e2e8f0; width: 100%; box-sizing: border-box;">
                        <label style="display:block; font-size: 0.8rem; font-weight:bold; margin-bottom:4px; color:#34495e;">Location Context:</label>
                        <input type="text" id="loc-${photo.image_id}" value="${photo.location_name || ''}" placeholder="e.g. Yosemite Valley, CA" style="width:100%; padding:5px; margin-bottom:8px; border:1px solid #ccc; border-radius:3px; box-sizing: border-box;">
                        
                        <div style="display:flex; gap: 8px;">
                            <div style="flex:1;">
                                <label style="display:block; font-size: 0.75rem; color:#7f8c8d;">Latitude:</label>
                                <input type="number" step="any" id="lat-${photo.image_id}" value="${photo.latitude || ''}" placeholder="37.8651" style="width:100%; padding:4px; border:1px solid #ccc; border-radius:3px; box-sizing: border-box;">
                            </div>
                            <div style="flex:1;">
                                <label style="display:block; font-size: 0.75rem; color:#7f8c8d;">Longitude:</label>
                                <input type="number" step="any" id="lng-${photo.image_id}" value="${photo.longitude || ''}" placeholder="-119.5383" style="width:100%; padding:4px; border:1px solid #ccc; border-radius:3px; box-sizing: border-box;">
                            </div>
                        </div>
                        <button onclick="savePhotoEdits(${photo.image_id})" style="margin-top:12px; padding: 6px 12px; background: #3498db; color:white; border:none; border-radius:4px; cursor:pointer; font-size:0.8rem; font-weight:bold; width:100%;">Save Details</button>
                        <span id="msg-${photo.image_id}" style="display:block; font-size:0.75rem; text-align:center; margin-top:5px;"></span>
                    </div>
                  `
                : `
                    <p class="photo-location">
                        📍 ${photo.location_name || 'Unknown Location'}
                    </p>
                  `;

            const imgCard = document.createElement('div');
            imgCard.className = 'photo-card';
            
            imgCard.innerHTML = `
                <div class="photo-frame-wrapper">
                    <img src="${imageSourcePath}" alt="${photoTitleClean}">
                </div>
                <div class="photo-metadata" style="width: 100%;">
                    <div class="photo-title">${photoTitleClean}</div>
                    ${locationMarkup}
                </div>
            `;
            galleryContainer.appendChild(imgCard);
        } catch (innerErr) {
            console.error("Skipped malformed card compilation iteration:", innerErr);
        }
    });
}

// 1. Fetch and render cards on page load (Strict Read Mode)
async function loadActivePhotos() {
    try {
        const response = await fetch(API_URL, { method: "GET" });
        if (!response.ok) throw new Error(`Status code: ${response.status}`);

        const jsonResponse = await response.json();
        renderGalleryCards(jsonResponse.data);
    } catch (error) {
        console.error("Pipeline breakdown:", error);
        galleryContainer.innerHTML = `<p style="color:#e74c3c; text-align:center; grid-column:1/-1;">⚠️ Failed to load landscape catalog records.</p>`;
    }
}

// 2. Triggers an explicit transition refresh
async function triggerSmoothExhibitionRefresh(mutateDatabase = false) {
    const activeCards = galleryContainer.querySelectorAll('.photo-card');
    
    if (activeCards.length > 0) {
        activeCards.forEach(card => card.classList.add('photo-gallery-fade-out'));
        await new Promise(resolve => setTimeout(resolve, 600));
    }

    if (mutateDatabase) {
        try {
            const response = await fetch(ROTATE_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ limit: photoPageSize })
            });
            const jsonResponse = await response.json();
            renderGalleryCards(jsonResponse.data);
        } catch (err) {
            console.error("Database mutation execution failed:", err);
            loadActivePhotos();
        }
    } else {
        await loadActivePhotos();
    }
}

// 3. Automated rotation cycle running in background
function initializeMuseumExhibitionLoop() {
    if (rotationTimerId) {
        clearInterval(rotationTimerId); 
    }

    const intervalMilliseconds = refreshIntervalMinutes * 60 * 1000;
    rotationTimerId = setInterval(() => {
        console.log(`⏰ Exhibition clock tick: Cycling current landscape portfolio view...`);
        triggerSmoothExhibitionRefresh(true); 
    }, intervalMilliseconds);
}

// 4. Post updated values directly back to Flask
async function savePhotoEdits(imageId) {
    const locationName = document.getElementById(`loc-${imageId}`).value;
    const latitude = document.getElementById(`lat-${imageId}`).value;
    const longitude = document.getElementById(`lng-${imageId}`).value;
    const statusSpan = document.getElementById(`msg-${imageId}`);

    statusSpan.innerText = "⏳ Saving...";
    statusSpan.style.color = "#666";

    try {
        const response = await fetch(UPDATE_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                image_id: imageId,
                location_name: locationName,
                latitude: latitude,
                longitude: longitude
            }),
            credentials: "include" 
        });

        const result = await response.json();
        if (result.success) {
            statusSpan.innerText = "💾 Saved!";
            statusSpan.style.color = "green";
            setTimeout(() => { statusSpan.innerText = ""; }, 3000);
        } else {
            statusSpan.innerText = "❌ Failed";
            statusSpan.style.color = "red";
        }
    } catch (err) {
        console.error("Error saving:", err);
        statusSpan.innerText = "💥 Server Error";
        statusSpan.style.color = "red";
    }
}

// Mount startup routines
window.addEventListener("DOMContentLoaded", () => {
    // 🛡️ SAFE PASSIVE READ BASELINE: Load whatever assets are currently flagged as 
    // display active without triggering any database modifications or sequence loops.
    loadActivePhotos();
    initializeMuseumExhibitionLoop(); 
});