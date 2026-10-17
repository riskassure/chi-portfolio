// Manual updates use the same locked worker and retry rules as the scheduled task.
document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("admin-update-music");
    const message = document.getElementById("admin-update-message");
    if (!button || !message) return;
    button.addEventListener("click", async () => {
        button.disabled = true;
        message.textContent = "Refreshing your Spotify top tracks...";
        const base = `${window.PORTFOLIO_API_BASE}/music/spotify`;
        try {
            const status = await fetch(`${base}/status`, {credentials: "include", cache: "no-store"});
            if (!status.ok) throw new Error("Please sign in as admin again, then retry.");
            const {update_csrf: csrf} = await status.json();
            const response = await fetch(`${base}/refresh`, {
                method: "POST", credentials: "include",
                headers: {"Content-Type": "application/json"}, body: JSON.stringify({csrf})
            });
            if (response.status === 403) throw new Error("Please sign in as admin again, then retry.");
            const result = await response.json();
            if (!response.ok) {
                const retry = result.retry_at ? ` Retry after ${new Date(result.retry_at).toLocaleString()}.` : "";
                throw new Error((result.message || "Update failed. The previous catalog is retained.") + retry);
            }
            message.textContent = result.message || 'Your Spotify ranking is up to date.';
            loadMusicData();
        } catch (error) {
            message.textContent = error.message || "Could not reach the backend. Please try again.";
        } finally {
            button.disabled = false;
        }
    });
});
