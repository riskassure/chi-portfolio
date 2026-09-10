(() => {

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function renderConceptLink(row) {
    const title =
        escapeHtml(
            row.title
            || row.slug
            || row.concept_id
            || "Open concept"
        );

    if (!row.concept_url) {
        return title;
    }

    return `<a href="${escapeHtml(
        row.concept_url
    )}" target="_blank" rel="noopener noreferrer">${title}</a>`;
}


function setAuditStatus(message, type = "info") {
    const status =
        document.getElementById(
            "auditStatus"
        );

    if (!status) return;

    const colors = {
        info: "#334155",
        success: "#047857",
        warn: "#92400e",
        error: "#b91c1c"
    };

    status.style.color =
        colors[type] || colors.info;

    status.innerText = message;
}


window.MathCmsAuditView = {
    renderConceptLink,
    escapeHtml,
    setAuditStatus
};

})();
