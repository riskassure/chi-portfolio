(() => {

async function copyAuditCsv(rows) {
    if (rows.length === 0) {
        window.MathCmsAuditView
            .setAuditStatus(
                "No audit rows to copy.",
                "error"
            );

        return;
    }

    const csv =
        window.MathCmsAuditCsv
            .rowsToCsv(
                rows
            );

    try {
        await navigator.clipboard
            .writeText(csv);

        window.MathCmsAuditView
            .setAuditStatus(
                "Copied audit CSV to clipboard.",
                "success"
            );

    } catch (err) {
        console.warn(err);

        window.MathCmsAuditView
            .setAuditStatus(
                "Unable to copy CSV automatically. Check console for CSV output.",
                "error"
            );

        console.log(csv);
    }
}


window.MathCmsAuditClipboard = {
    copyAuditCsv
};

})();
