(() => {
    function splitAlignRows(body) {
        const normalized = String(body || "").trim();

        if (!normalized) {
            return [];
        }

        const slashRows = window.MathCmsRenderStructuredMath
            .splitEqnarrayRows(normalized);

        if (slashRows.length > 1) {
            return slashRows;
        }

        // If there is only one top-level alignment marker, the physical
        // line breaks are just source formatting for one long equation.
        if (countTopLevelAlignmentMarkers(normalized) <= 1) {
            return slashRows;
        }

        // Some PlanetMath align blocks lost explicit \\ row separators and
        // retain only physical line breaks. Split those line breaks only at
        // top level; line breaks inside matrices, arrays, cases, etc. belong
        // to the nested environment and must remain intact.
        const newlineRows = splitTopLevelNewlineRows(normalized);

        if (newlineRows.length > 1) {
            return newlineRows;
        }

        return slashRows;
    }

    function countTopLevelAlignmentMarkers(body) {
        const text = String(body || "");
        let nestedDepth = 0;
        let count = 0;

        for (let i = 0; i < text.length; i += 1) {
            const env = window.MathCmsRenderStructuredMath
                .readLatexEnvironmentAt(text, i);

            if (env && window.MathCmsRenderStructuredMath
                .isNestedLatexEnvironment(env.name)) {
                if (env.type === "begin") {
                    nestedDepth += 1;
                } else {
                    nestedDepth = Math.max(0, nestedDepth - 1);
                }

                i = env.endIndex - 1;
                continue;
            }

            if (
                nestedDepth === 0 &&
                text[i] === "&" &&
                text[i - 1] !== "\\"
            ) {
                count += 1;
            }
        }

        return count;
    }

    function splitTopLevelNewlineRows(body) {
        const text = String(body || "");
        const rows = [];

        let start = 0;
        let nestedDepth = 0;

        for (let i = 0; i < text.length; i += 1) {
            const env = window.MathCmsRenderStructuredMath
                .readLatexEnvironmentAt(text, i);

            if (env && window.MathCmsRenderStructuredMath
                .isNestedLatexEnvironment(env.name)) {
                if (env.type === "begin") {
                    nestedDepth += 1;
                } else {
                    nestedDepth = Math.max(0, nestedDepth - 1);
                }

                i = env.endIndex - 1;
                continue;
            }

            if (
                nestedDepth === 0 &&
                (text[i] === "\n" || text[i] === "\r")
            ) {
                const row = text.slice(start, i).trim();

                if (row) {
                    rows.push(row);
                }

                if (text[i] === "\r" && text[i + 1] === "\n") {
                    i += 1;
                }

                while (
                    i + 1 < text.length &&
                    (text[i + 1] === "\n" || text[i + 1] === "\r")
                ) {
                    i += 1;
                }

                start = i + 1;
            }
        }

        const finalRow = text.slice(start).trim();

        if (finalRow) {
            rows.push(finalRow);
        }

        return rows;
    }

    window.MathCmsRenderAlignRows = {
        splitAlignRows
    };
})();
