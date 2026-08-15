(() => {
    function normalizeEqnarrayHtmlArtifacts(value) {
        return String(value || "")
            // These artifacts can appear inside old rendered_tex equation arrays.
            // Treat paragraph breaks inside eqnarray as equation row breaks.
            .replace(/<br\s*\/?>\s*<\/p>\s*<p[^>]*>/gi, "\\\\")
            .replace(/<\/p>\s*<p[^>]*>/gi, "\\\\")
            .replace(/<br\s*\/?>/gi, "\\\\")

            // Remove any leftover paragraph wrappers.
            .replace(/<\/?p[^>]*>/gi, "")

            // Decode matrix/alignment separators that were HTML-escaped by the
            // backend renderer before reaching the frontend parser.
            .replace(/&amp;/gi, "&")

            // Common HTML whitespace artifact.
            .replace(/&nbsp;/gi, " ");
    }

    function normalizeStructuredMathHtmlArtifacts(value) {
        let output = String(value || "");

        const normalizeBody = body => String(body || "")
            // Paragraph breaks inside cases/arrays represent TeX rows.
            .replace(
                /<br\s*\/?>\s*<\/p>\s*<p[^>]*>/gi,
                "\\\\"
            )
            .replace(
                /<\/p>\s*<p[^>]*>/gi,
                "\\\\"
            )
            .replace(
                /<br\s*\/?>/gi,
                "\\\\"
            )

            // Remove any remaining paragraph wrappers.
            .replace(/<\/?p[^>]*>/gi, "")

            // A cases/array environment is already math. Nested dollar pairs,
            // often inherited from \mbox{if $x>0$}, must not remain inside it.
            .replace(/\$([^$]+)\$/g, "$1");

        output = output.replace(
            /\\begin\s*\{cases\}([\s\S]*?)\\end\s*\{cases\}/gi,
            (_, body) =>
                `\\begin{cases}${normalizeBody(body)}\\end{cases}`
        );

        output = output.replace(
            /\\begin\s*\{array\}\s*\{([^{}]*)\}([\s\S]*?)\\end\s*\{array\}/gi,
            (_, columnSpec, body) =>
                `\\begin{array}{${columnSpec}}${normalizeBody(body)}\\end{array}`
        );

        output = output.replace(
            /\\begin\s*\{(matrix|pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|smallmatrix)\}([\s\S]*?)\\end\s*\{\1\}/gi,
            (_, envName, body) =>
                `\\begin{${envName}}${normalizeBody(body)}\\end{${envName}}`
        );

        return output;
    }

    function splitEqnarrayCells(row) {
        const text = String(row || "");
        const cells = [];
        let start = 0;
        let nestedDepth = 0;

        for (let i = 0; i < text.length; i++) {
            const env = readLatexEnvironmentAt(text, i);

            if (env && isNestedLatexEnvironment(env.name)) {
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
                cells.push(text.slice(start, i).trim());
                start = i + 1;
            }
        }

        cells.push(text.slice(start).trim());

        return cells;
    }

    function padEqnarrayCells(cells, maxColumns) {
        const padded = [...cells];

        while (padded.length < maxColumns) {
            padded.push("");
        }

        return padded;
    }

    function splitEqnarrayRows(body) {
        const text = String(body || "");
        const rows = [];

        let start = 0;
        let nestedDepth = 0;
        let braceDepth = 0;

        for (
            let i = 0;
            i < text.length;
            i += 1
        ) {
            const env =
                readLatexEnvironmentAt(
                    text,
                    i
                );

            if (
                env
                && isNestedLatexEnvironment(
                    env.name
                )
            ) {
                if (env.type === "begin") {
                    nestedDepth += 1;
                } else {
                    nestedDepth =
                        Math.max(
                            0,
                            nestedDepth - 1
                        );
                }

                i =
                    env.endIndex - 1;

                continue;
            }

            /*
             * Escaped braces such as \{ and \} are TeX symbols,
             * not grouping braces.
             */
            if (text[i] === "\\") {
                if (
                    text[i + 1] === "{"
                    || text[i + 1] === "}"
                ) {
                    i += 1;
                    continue;
                }

            } else if (text[i] === "{") {
                braceDepth += 1;
                continue;

            } else if (text[i] === "}") {
                braceDepth =
                    Math.max(
                        0,
                        braceDepth - 1
                    );

                continue;
            }

            /*
             * Split only a genuine top-level eqnarray row.
             *
             * Do not split \\ inside grouped macro arguments such
             * as:
             *
             *   \substack{top \\ middle \\ bottom}
             */
            if (
                nestedDepth === 0
                && braceDepth === 0
                && text[i] === "\\"
                && text[i + 1] === "\\"
            ) {
                rows.push(
                    text
                        .slice(
                            start,
                            i
                        )
                        .trim()
                );

                i += 1;
                start = i + 1;
            }
        }

        rows.push(
            text
                .slice(start)
                .trim()
        );

        return rows.filter(
            row => row.length > 0
        );
    }

    function readLatexEnvironmentAt(text, index) {
        const source = String(text || "");
        const remainder = source.slice(index);

        const markerMatch = remainder.match(
            /^\\(begin|end)\s*\{\s*([^{}]+?)\s*\}/
        );

        if (!markerMatch) {
            return null;
        }

        return {
            type: markerMatch[1],
            name: markerMatch[2],
            endIndex: index + markerMatch[0].length
        };
    }

    function isNestedLatexEnvironment(name) {
        const normalized = String(name || "").replace(/\*$/, "");

        return [
            "array",
            "cases",
            "matrix",
            "pmatrix",
            "bmatrix",
            "Bmatrix",
            "vmatrix",
            "Vmatrix",
            "smallmatrix",
            "aligned",
            "alignedat",
            "split",
            "gathered",
            "subarray"
        ].includes(normalized);
    }

    window.MathCmsRenderStructuredMath = {
        normalizeEqnarrayHtmlArtifacts,
        normalizeStructuredMathHtmlArtifacts,
        splitEqnarrayRows,
        splitEqnarrayCells,
        padEqnarrayCells,
        readLatexEnvironmentAt,
        isNestedLatexEnvironment
    };
})();
