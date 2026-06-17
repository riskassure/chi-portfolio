/* ==========================================================================
   ISOLATED ADMIN SWITCHBOARD CONTROLLER ENGINE
   ========================================================================== */

const API_BASE = "http://127.0.0.1:5000/api";

// Instantly run session diagnostic check when page mounts
window.addEventListener('DOMContentLoaded', () => {
    verifySystemSession();
});

// 🟢 DIAGNOSTIC: Check if browser already has access
async function verifySystemSession() {
    try {
        // 🛠️ FIXED: Added credentials configuration block
        const response = await fetch(`${API_BASE}/session-check`, {
            credentials: 'include'
        });
        const session = await response.json();
        
        if (session.is_admin) {
            hydrateAdminEnvironment();
        } else {
            isolateEnvironment();
        }
    } catch (err) {
        console.error("Backend server offline.");
        isolateEnvironment();
    }
}

// 🔵 MUTATION: Attempt Authentication
async function attemptLogin() {
    const passwordInput = document.getElementById('password');
    const errorBox = document.getElementById('error-box');
    errorBox.style.display = 'none';

    try {
        // 🛠️ FIXED: Added credentials configuration block
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: passwordInput.value }),
            credentials: 'include' 
        });

        const outcome = await response.json();

        if (response.ok && outcome.success) {
            passwordInput.value = '';
            hydrateAdminEnvironment();
        } else {
            errorBox.textContent = outcome.message || "Access Denied.";
            errorBox.style.display = 'block';
        }
    } catch (err) {
        errorBox.textContent = "Gateway communication broken.";
        errorBox.style.display = 'block';
    }
}

// 🔴 MUTATION: Terminate Session
async function attemptLogout() {
    try {
        // 🛠️ FIXED: Added credentials configuration block
        const response = await fetch(`${API_BASE}/logout`, { 
            method: 'POST',
            credentials: 'include'
        });
        if (response.ok) {
            isolateEnvironment();
        }
    } catch (err) {
        console.error("Logout frame dropped.");
        isolateEnvironment();
    }
}

// --- ENVIRONMENT RENDERING ENGINES ---
function hydrateAdminEnvironment() {
    // 🛠️ FIXED: Added safe null guards to prevent script crashes on subpages
    const universalNav = document.getElementById('universal-nav');
    if (universalNav) {
        universalNav.classList.remove('hidden');
    }
    
    const loginCard = document.getElementById('login-card');
    if (loginCard) {
        loginCard.classList.add('hidden');
    }

    const welcomeCard = document.getElementById('welcome-card');
    if (welcomeCard) {
        welcomeCard.classList.remove('hidden');
    }
}

function isolateEnvironment() {
    // 1. Safe check for navbar wrapper
    const universalNav = document.getElementById('universal-nav');
    if (universalNav) {
        universalNav.classList.add('hidden');
    }
    
    // 2. Safe check for login management cards
    const welcomeCard = document.getElementById('welcome-card');
    if (welcomeCard) {
        welcomeCard.classList.add('hidden');
    }

    const loginCard = document.getElementById('login-card');
    if (loginCard) {
        loginCard.classList.remove('hidden');
    }
}