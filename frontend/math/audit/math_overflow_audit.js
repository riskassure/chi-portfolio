function collectHorizontalOverflowFindings(root) {
    if (!root) {
        return [];
    }

    const tolerance = 2;

    const candidateSelector = [
        'mjx-container[display="true"]',
        ".pm-xymatrix-sequence",
        ".pm-xymatrix-labeled-display",
        ".pm-underbraced-xymatrix",
        ".pm-matrix-display",
        ".pm-align-table",
        ".pm-eqnarray-table",
        "table",
        "pre",
        "figure",
        "img",
        "svg"
    ].join(",");

    const rootRect =
        root.getBoundingClientRect();

    const findings = [];

    Array.from(
        root.querySelectorAll(candidateSelector)
    ).forEach(element => {
        const style =
            window.getComputedStyle(element);

        const rect =
            element.getBoundingClientRect();

        if (
            style.display === "none"
            || style.visibility === "hidden"
            || rect.width <= 0
            || rect.height <= 0
        ) {
            return;
        }

        const clientWidth =
            Number(element.clientWidth || 0);

        const scrollWidth =
            Number(element.scrollWidth || 0);

        const leftOverflow =
            Math.max(
                0,
                rootRect.left - rect.left
            );

        const rightOverflow =
            Math.max(
                0,
                rect.right - rootRect.right
            );

        /*
         * scrollWidth may exceed clientWidth slightly without escaping
         * the page canvas. Project that internal width from the element's
         * left edge and report it only when it crosses the root boundary.
         */
        const projectedRightEdge =
            rect.left
            + Math.max(
                rect.width,
                scrollWidth
            );

        const projectedRightOverflow =
            Math.max(
                0,
                projectedRightEdge
                - rootRect.right
            );

        const overflowPixels =
            Math.max(
                leftOverflow,
                rightOverflow,
                projectedRightOverflow
            );

        if (overflowPixels <= tolerance) {
            return;
        }

        const scrollContainer =
            findSafeHorizontalScrollContainer(
                element,
                root,
                tolerance
            );

        /*
         * Content inside a genuine horizontal scroll container
         * is already safely contained and is not an audit finding.
         */
        if (scrollContainer) {
            return;
        }

        findings.push({
            element,
            clientWidth,
            scrollWidth,
            overflowPixels
        });
    });

    return findings
        .sort(
            (a, b) =>
                b.overflowPixels
                - a.overflowPixels
        )
        .slice(0, 5)
        .map(finding => ({
            command: "[HORIZONTAL_OVERFLOW]",
            count: 1,
            examples: [
                [
                    describeAuditElement(
                        finding.element
                    ),
                    `clientWidth=${Math.round(
                        finding.clientWidth
                    )}`,
                    `scrollWidth=${Math.round(
                        finding.scrollWidth
                    )}`,
                    `overflow=${Math.round(
                        finding.overflowPixels
                    )}px`,
                    "contained=no"
                ].join("; ")
            ]
        }));
}


function findSafeHorizontalScrollContainer(
    element,
    root,
    tolerance
) {
    let current = element;

    while (
        current
        && current !== root
    ) {
        const style =
            window.getComputedStyle(current);

        const overflowX =
            String(style.overflowX || "")
                .toLowerCase();

        if (
            ["auto", "scroll", "overlay"]
                .includes(overflowX)
            && current.scrollWidth
                > current.clientWidth + tolerance
        ) {
            return current;
        }

        current = current.parentElement;
    }

    return null;
}


function describeAuditElement(element) {
    if (!element) {
        return "[unknown-element]";
    }

    const tagName =
        String(element.tagName || "element")
            .toLowerCase();

    const idPart =
        element.id
            ? `#${element.id}`
            : "";

    const classPart =
        Array.from(element.classList || [])
            .slice(0, 4)
            .map(className => `.${className}`)
            .join("");

    return `${tagName}${idPart}${classPart}`;
}

window.MathCmsOverflowAudit = {
    collectHorizontalOverflowFindings
};