(() => {

const AUDIT_ROWS_STORAGE_KEY =
    "mathCmsLatestAuditRows";

const AUDIT_STATUS_STORAGE_KEY =
    "mathCmsLatestAuditStatus";

const AUDIT_SAVED_AT_STORAGE_KEY =
    "mathCmsLatestAuditSavedAt";


function saveAuditSnapshot(
    rows,
    statusMessage = ""
) {
    try {
        sessionStorage.setItem(
            AUDIT_ROWS_STORAGE_KEY,
            JSON.stringify(rows || [])
        );

        sessionStorage.setItem(
            AUDIT_STATUS_STORAGE_KEY,
            statusMessage || ""
        );

        sessionStorage.setItem(
            AUDIT_SAVED_AT_STORAGE_KEY,
            new Date().toLocaleString()
        );

    } catch (err) {
        console.warn(
            "Unable to save audit snapshot to sessionStorage.",
            err
        );
    }
}


function readAuditSnapshot() {
    try {
        const rawRows =
            sessionStorage.getItem(
                AUDIT_ROWS_STORAGE_KEY
            );

        if (!rawRows) {
            return null;
        }

        const rows = JSON.parse(rawRows);

        if (
            !Array.isArray(rows)
            || rows.length === 0
        ) {
            return null;
        }

        return {
            rows,
            statusMessage:
                sessionStorage.getItem(
                    AUDIT_STATUS_STORAGE_KEY
                ) || "",
            savedAt:
                sessionStorage.getItem(
                    AUDIT_SAVED_AT_STORAGE_KEY
                ) || ""
        };

    } catch (err) {
        console.warn(
            "Unable to restore audit snapshot from sessionStorage.",
            err
        );

        return null;
    }
}


function clearAuditSnapshot() {
    try {
        sessionStorage.removeItem(
            AUDIT_ROWS_STORAGE_KEY
        );

        sessionStorage.removeItem(
            AUDIT_STATUS_STORAGE_KEY
        );

        sessionStorage.removeItem(
            AUDIT_SAVED_AT_STORAGE_KEY
        );

    } catch (err) {
        console.warn(
            "Unable to clear audit snapshot from sessionStorage.",
            err
        );
    }
}


window.MathCmsAuditSnapshot = {
    saveAuditSnapshot,
    readAuditSnapshot,
    clearAuditSnapshot
};

})();
