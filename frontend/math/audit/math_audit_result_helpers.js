(() => {

function getIssueCount(rows) {
    return rows.reduce(
        (total, row) =>
            total + Number(row.count || 0),
        0
    );
}


function summarizeRowsForConcept(rows) {
    if (!rows || rows.length === 0) {
        return "";
    }

    const summary = {};

    rows.forEach(row => {
        const command =
            row.command || "[unknown]";

        summary[command] =
            (summary[command] || 0)
            + Number(row.count || 0);
    });

    return JSON.stringify(summary);
}


async function hashText(text) {
    const normalized =
        String(text || "");

    if (
        window.crypto
        && window.crypto.subtle
        && typeof TextEncoder !== "undefined"
    ) {
        const encoder =
            new TextEncoder();

        const buffer =
            await window.crypto.subtle.digest(
                "SHA-256",
                encoder.encode(normalized)
            );

        return Array.from(
            new Uint8Array(buffer)
        )
            .map(
                byte =>
                    byte
                        .toString(16)
                        .padStart(2, "0")
            )
            .join("");
    }

    // Fallback for older/insecure browser contexts.
    let hash = 0;

    for (
        let i = 0;
        i < normalized.length;
        i += 1
    ) {
        hash =
            ((hash << 5) - hash)
            + normalized.charCodeAt(i);

        hash |= 0;
    }

    return `fallback-${Math.abs(hash)}`;
}


window.MathCmsAuditResults = {
    getIssueCount,
    summarizeRowsForConcept,
    hashText
};

})();
