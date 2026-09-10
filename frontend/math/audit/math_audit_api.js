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

async function fetchAuditConceptList(
    apiEndpoint,
    mode
) {
    const response =
        await fetch(
            `${apiEndpoint}/admin/math/concepts/audit-list?mode=${
                encodeURIComponent(mode)
            }`,
            {
                credentials: "include"
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
            || "Unable to load audit-list endpoint."
        );
    }

    return json;
}

window.MathCmsAuditApi = {
    batchSaveAuditRun,
    fetchConcept,
    fetchAuditConceptList
};

})();
