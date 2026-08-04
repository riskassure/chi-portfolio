function rowsToCsv(rows) {
    const headers = [
        "command",
        "count",
        "concept_id",
        "slug",
        "title",
        "example",
        "concept_url"
    ];

    const lines = [headers.join(",")];

    rows.forEach(row => {
        lines.push(
            headers
                .map(header => csvCell(row[header]))
                .join(",")
        );
    });

    return lines.join("\n");
}


function csvCell(value) {
    const text = String(value ?? "");

    if (/[",\n\r]/.test(text)) {
        return `"${text.replace(/"/g, '""')}"`;
    }

    return text;
}


window.MathCmsAuditCsv = {
    rowsToCsv,
    csvCell
};
