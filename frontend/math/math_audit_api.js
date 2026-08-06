(() => {

async function batchSaveAuditRun(
    apiEndpoint,
    auditVersion,
    mode,
    results
) {
    const response =
        await fetch(
            `${apiEndpoint}/admin/math/audit-runs/batch-save`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type":
                        "application/json"
                },
                body: JSON.stringify({
                    mode,
                    audit_version:
                        auditVersion,
                    results
                })
            }
        );

    const json =
        await response.json();

    if (
        !response.ok
        || json.status !== "success"
    ) {
        throw new Error(
            json.message
            || json.error
            || `Unable to batch-save audit run. HTTP ${response.status}`
        );
    }

    return json;
}


async function fetchConcept(
    apiEndpoint,
    identifier
) {
    const response =
        await fetch(
            `${apiEndpoint}/math/concepts/${
                encodeURIComponent(identifier)
            }`
        );

    const json =
        await response.json();

    if (
        !response.ok
        || json.status !== "success"
    ) {
        throw new Error(
            json.message
            || `Failed to fetch concept ${identifier}.`
        );
    }

    return json.data;
}


window.MathCmsAuditApi = {
    batchSaveAuditRun,
    fetchConcept
};

})();