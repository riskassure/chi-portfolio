// frontend/photography/gallery.js

const API_URL = "http://127.0.0.1:5000/api/photography/current";
const SESSION_URL = "http://127.0.0.1:5000/api/session-check";
const UPDATE_URL = "http://127.0.0.1:5000/api/photography/update";
const galleryContainer = document.getElementById("photography-gallery");

let isAdmin = false;

// 1. Probe session tracking status
async function checkAdminStatus() {
    try {
        const response = await fetch(SESSION_URL, { credentials: "include" });
        if (response.ok) {
            const data = await response.json();
            isAdmin = data.is_admin;
        }
    } catch (err) {
        console.warn("Session authentication probe down:", err);
    }
}

// 2. Fetch and render cards dynamically
async function loadActivePhotos() {
    await checkAdminStatus();

    try {
        const response = await fetch(API_URL, { method: "GET" });
        if (!response.ok) throw new Error(`Status code: ${response.status}`);

        const jsonResponse = await response.json();
        const photoList = jsonResponse.data;

        galleryContainer.innerHTML = "";

        if (photoList.length === 0) {
            galleryContainer.innerHTML = `<p class="empty-msg">No active landscape assets selected.</p>`;
            return;
        }

        photoList.forEach(photo => {
            const imageSourcePath = `../${photo.file_path}`;
            
            const locationMarkup = isAdmin 
                ? `
                    <div class="admin-edit-panel" style="margin-top: 10px; background: #f9f9f9; padding: 10px; border-radius: 4px; border: 1px solid #ddd;">
                        <label style="display:block; font-size: 0.8rem; font-weight:bold; margin-bottom:2px;">Location:</label>
                        <input type="text" id="loc-${photo.image_id}" value="${photo.location_name || ''}" placeholder="e.g. Yosemite Valley, CA" style="width:90%; padding:4px; margin-bottom:8px;">
                        
                        <div style="display:flex; gap: 5px;">
                            <div>
                                <label style="display:block; font-size: 0.75rem;">Lat:</label>
                                <input type="number" step="any" id="lat-${photo.image_id}" value="${photo.latitude || ''}" placeholder="37.8651" style="width:70px; padding:2px;">
                            </div>
                            <div>
                                <label style="display:block; font-size: 0.75rem;">Lng:</label>
                                <input type="number" step="any" id="lng-${photo.image_id}" value="${photo.longitude || ''}" placeholder="-119.5383" style="width:70px; padding:2px;">
                            </div>
                        </div>
                        <button onclick="savePhotoEdits(${photo.image_id})" style="margin-top:10px; padding: 4px 10px; background: #007bff; color:white; border:none; border-radius:3px; cursor:pointer; font-size:0.8rem;">Save Details</button>
                        <span id="msg-${photo.image_id}" style="font-size:0.75rem; margin-left:5px;"></span>
                    </div>
                  `
                : `
                    <p style="color: #777; font-size: 0.9rem; margin-top: 5px;">
                        📍 ${photo.location_name || 'Unknown Location'}
                    </p>
                  `;

            const imgCard = `
                <div class="gallery-card" style="margin-bottom: 20px;">
                    <img src="${imageSourcePath}" alt="${photo.title}" class="gallery-photo">
                    <div class="card-info">
                        <h3>${photo.title}</h3>
                        ${locationMarkup}
                    </div>
                </div>
            `;
            galleryContainer.innerHTML += imgCard;
        });

    } catch (error) {
        console.error("Pipeline breakdown:", error);
        galleryContainer.innerHTML = `<p style="color:red;">⚠️ Failed to load catalog records.</p>`;
    }
}

// 3. Post updated values directly back to Flask
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

// Mount the listeners
window.addEventListener("DOMContentLoaded", loadActivePhotos);