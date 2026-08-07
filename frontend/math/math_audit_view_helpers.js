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


window.MathCmsAuditView = {
    renderConceptLink,
    escapeHtml
};

})();
