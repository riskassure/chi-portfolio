(() => {

async function auditConcept(
    concept,
    apiEndpoint
) {
    const canvas = document.getElementById("auditCanvas");

    if (!canvas) {
        throw new Error("Audit canvas was not found.");
    }

    canvas.classList.add("tex2jax_process");

    const rawTex =
        window.MathCmsRender.getDisplayTex(concept);

    const localMacroSource =
        concept.cleaned_tex || "";

    /*
    * Local macro definitions affect the final rendering, so include
    * cleaned_tex in the audit hash as well.
    */
    const renderedTexHash =
        await window.MathCmsAuditResults
            .hashText(
                [
                    rawTex || "",
                    "PMLOCAL-SOURCE:",
                    localMacroSource
                ].join("\n")
            );

    const html =
        window.MathCmsRender.prepareConceptHtml(
            rawTex,
            {
                apiEndpoint,

                localMacroSource,

                context: {
                    page: "mathjax_audit",
                    concept_id: concept.id || null,
                    slug: concept.slug || null,
                    title: concept.title || null
                }
            }
        );

    // Important for full-audit mode:
    // MathJax keeps internal references to previously typeset nodes.
    // Clear those references before replacing the reused audit canvas HTML.
    if (
        window.MathJax &&
        typeof window.MathJax.typesetClear === "function"
    ) {
        window.MathJax.typesetClear([canvas]);
    }

    canvas.innerHTML = html;

    let leftovers = [];

    if (
        window.MathCmsMathJax &&
        typeof window.MathCmsMathJax.typesetElement === "function"
    ) {
        leftovers =
            await window.MathCmsMathJax
                .typesetElement(
                    canvas,
                    {
                        page: "mathjax_audit",
                        concept_id:
                            concept.id || null,
                        slug:
                            concept.slug || null,
                        title:
                            concept.title || null
                    }
                );
    } else {
        throw new Error(
            "MathCmsMathJax.typesetElement is not available."
        );
    }

    /*
     * Give MathJax and the generated diagram wrappers two browser
     * layout frames to settle before measuring their rendered widths.
     */
    await new Promise(resolve => {
        window.requestAnimationFrame(() => {
            window.requestAnimationFrame(resolve);
        });
    });

    const overflowFindings =
        window.MathCmsOverflowAudit
            .collectHorizontalOverflowFindings(
                canvas
            );

    const findings = [
        ...(
            Array.isArray(leftovers)
                ? leftovers
                : []
        ),
        ...overflowFindings
    ];

    return {
        rendered_tex_hash:
            renderedTexHash,

        rows:
            findings.map(item => ({
                command:
                    item.command,

                count:
                    item.count,

                concept_id:
                    concept.id || "",

                slug:
                    concept.slug || "",

                title:
                    concept.title || "",

                example:
                    (item.examples || [])[0] || "",

                concept_url:
                    concept.slug
                        ? `concept.html?slug=${encodeURIComponent(concept.slug)}`
                        : concept.id
                            ? `concept.html?id=${encodeURIComponent(concept.id)}`
                            : ""
            }))
    };
}


window.MathCmsAuditConcept = {
    auditConcept
};

})();
