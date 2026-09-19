// Prevent the audit interface from being shown outside an authenticated admin session.
(async function guardMathAdminPage() {
    try {
        const response = await fetch("http://127.0.0.1:5000/api/session-check", {
            credentials: "include"
        });

        if (!response.ok) {
            throw new Error("Session check failed with status " + response.status);
        }

        const session = await response.json();
        if (!session.is_admin) {
            window.location.replace("index.html");
            return;
        }

        document.body.hidden = false;
    } catch (error) {
        console.warn("Math admin page unavailable:", error);
        window.location.replace("index.html");
    }
})();
