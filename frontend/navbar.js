/* ==========================================================================
   UNIVERSALLY ADAPTIVE PORTFOLIO NAVBAR COMPONENT
   ========================================================================== */

function loadUniversalNavbar() {
    // 1. DYNAMIC DEPTH CALCULATOR
    // We look at the URL path and see how many subfolders deep we are past the root dashboard.
    const pathName = window.location.pathname;
    
    // Split the path into segments and filter out empty strings
    const segments = pathName.split('/').filter(segment => segment.length > 0);
    
    // Find where "admin_dashboard.html" or "index.html" lives relative to your dev environment root.
    // We count how many folders exist after your root repository name to determine the upward prefix.
    let prefix = '';
    
    // If we are using a local development server (like Live Server), we look for subfolders.
    // If the path contains folders like /music/index.html, it will have more segments than the root index.html.
    if (segments.length > 1 && !pathName.endsWith('admin_dashboard.html') && !pathName.endsWith('index.html')) {
        // If the file is inside a folder (e.g., frontend/music/index.html), we need to climb up one level
        prefix = '../';
    }
    
    // For extreme safety: if you ever make deeply nested directories down the road (e.g., math/calculus/index.html)
    // you can count exactly how many steps to climb up like this:
    // let depth = segments.findIndex(s => s === 'music' || s === 'photography' || s === 'math');
    
    // 2. CONSTRUCT LINKS USING THE COMPUTED PREFIX
    const navbarHTML = `
        <nav class="navbar">
            <div class="nav-brand">Chi-Chih Woo</div>
            <ul class="nav-links">
                <li><a href="${prefix}index.html">Home</a></li>
                <li><a href="${prefix}bio.html">Biography</a></li>
                <li><a href="${prefix}resume.html">Resume</a></li>
                <li><a href="${prefix}music/index.html">Music</a></li>
                <li><a href="${prefix}math/index.html">Mathematics</a></li>
                <li><a href="${prefix}photography/index.html">Photography</a></li>
                
                <li id="admin-nav-item" class="admin-only-link"><a href="${prefix}admin_dashboard.html">Admin Control</a></li>
            </ul>
        </nav>
    `;

    // 3. Inject the navbar cleanly at the very top of the page body
    document.body.insertAdjacentHTML('afterbegin', navbarHTML);

    // 4. Run the background session security verification
    checkGlobalAdminStatus();
}

// 🟢 SECURITY ENGINE: Verify session token and reveal elements
async function checkGlobalAdminStatus() {
    try {
        const response = await fetch("http://127.0.0.1:5000/api/session-check");
        const session = await response.json();
        
        if (session.is_admin) {
            const adminLink = document.getElementById('admin-nav-item');
            if (adminLink) {
                adminLink.style.display = 'block';
            }
            
            // Fire page-specific admin layout configurations if they exist
            if (typeof unlockLocalPageControls === 'function') {
                unlockLocalPageControls();
            }
        }
    } catch (err) {
        console.log("System Status: Portfolio locked in visitor mode.");
    }
}

window.addEventListener('DOMContentLoaded', loadUniversalNavbar);