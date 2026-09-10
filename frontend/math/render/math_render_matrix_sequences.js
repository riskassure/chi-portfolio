(() => {
    function convertRemainingMatrixMathSequencesToHtml(tex) {
        if (!tex) return "";

        let output = String(tex || "");

        // Remaining display expressions containing one or more matrices.
        //
        // The earlier display-affix converter handles the common single-matrix
        // case. This pass handles expressions such as:
        //
        // \[
        //   \begin{pmatrix} A & O \\ O & B \end{pmatrix}
        //   =
        //   \begin{pmatrix} 3 & -1 & 0 & 0 \\ ... \end{pmatrix}
        // \]
        output = output.replace(
            /\\\[([\s\S]*?)\\\]/g,
            function(fullMatch, body) {
                if (!containsSimpleMatrixEnvironment(body)) {
                    return fullMatch;
                }

                return buildMatrixMathSequenceHtml(body, true);
            }
        );

        // Explicit inline MathJax delimiters:
        // \( ... \)
        output = output.replace(
            /\\\(([\s\S]*?)\\\)/g,
            function(fullMatch, body) {
                if (!containsSimpleMatrixEnvironment(body)) {
                    return fullMatch;
                }

                return buildMatrixMathSequenceHtml(body, false);
            }
        );

        // Legacy single-dollar inline math:
        // $ ... $
        //
        // Dollar-display math has already been normalized earlier, so this
        // intentionally handles only remaining single-dollar pairs.
        output = output.replace(
            /(^|[^\\$])\$((?:\\.|[^$])*?)\$/g,
            function(fullMatch, leadingCharacter, body) {
                if (!containsSimpleMatrixEnvironment(body)) {
                    return fullMatch;
                }

                return (
                    leadingCharacter +
                    buildMatrixMathSequenceHtml(body, false)
                );
            }
        );

        return output;
    }

    function containsSimpleMatrixEnvironment(value) {
        return /\\begin\s*\{(?:pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix|array)\}/i
            .test(String(value || ""));
    }

    function buildMatrixMathSequenceHtml(body, isDisplay) {
        const source = String(body || "");

        const matrixPattern =
            /(?:\\left\s*(\(|\[|\||\\\{)\s*)?\\begin\s*\{(pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix|array)\}\s*(?:\{([^{}]*)\})?([\s\S]*?)\\end\s*\{\2\}(?:\s*\\right\s*(\.|\)|\]|\||\\\}))?/gi;

        const pieces = [];
        let cursor = 0;
        let match;

        while ((match = matrixPattern.exec(source)) !== null) {
            const mathBefore = source.slice(cursor, match.index);

            appendMatrixSequenceMathPiece(pieces, mathBefore);

            const explicitLeft = match[1] || "";
            const envName = match[2];
            const arraySpec = match[3] || "";
            const matrixBody = match[4];
            const explicitRight = match[5] || "";

            const hasExplicitLeft = explicitLeft.length > 0;
            const hasExplicitRight = explicitRight.length > 0;

            const delimiterOverride =
                (hasExplicitLeft || hasExplicitRight)
                    ? {
                        left: hasExplicitLeft
                            ? normalizeExplicitMatrixDelimiter(explicitLeft)
                            : "",
                        right: hasExplicitRight
                            ? normalizeExplicitMatrixDelimiter(explicitRight)
                            : ""
                    }
                    : null;

            const matrixHtml = window.MathCmsRenderMatrixCore
                .buildMatrixEnvironmentHtml(
                    envName,
                    matrixBody,
                    delimiterOverride,
                    arraySpec
                );

            let nextCursor = matrixPattern.lastIndex;

            // Attach an immediately following exponent to the matrix itself:
            //
            //   \begin{pmatrix} ... \end{pmatrix}^n
            //   \begin{pmatrix} ... \end{pmatrix}^{n+1}
            const exponentMatch = source.slice(nextCursor).match(
                /^\s*\^\s*(?:\{([^{}]+)\}|([A-Za-z0-9]+))/
            );

            if (exponentMatch) {
                const exponent =
                    exponentMatch[1] ||
                    exponentMatch[2] ||
                    "";

                pieces.push(`
                    <span class="pm-matrix-with-exponent" style="
                        display:inline-flex;
                        align-items:flex-start;
                        vertical-align:middle;
                        white-space:nowrap;
                    ">
                        ${matrixHtml}

                        <span style="
                            display:inline-block;
                            margin-left:0.06rem;
                            margin-top:-0.12rem;
                            font-size:0.78em;
                            line-height:1;
                        ">
                            \\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(exponent)}\\)
                        </span>
                    </span>
                `);

                nextCursor += exponentMatch[0].length;
            } else {
                pieces.push(matrixHtml);
            }

            cursor = nextCursor;
        }

        appendMatrixSequenceMathPiece(
            pieces,
            source.slice(cursor)
        );

        if (pieces.length === 0) {
            return isDisplay
                ? `\\[${source}\\]`
                : `\\(${source}\\)`;
        }

        const wrapperTag = isDisplay ? "div" : "span";
        const wrapperClass = isDisplay
            ? "pm-matrix-display pm-matrix-sequence tex2jax_process"
            : "pm-matrix-inline pm-matrix-sequence tex2jax_process";

        const wrapperStyle = isDisplay
            ? `
                display:flex;
                align-items:center;
                justify-content:center;
                flex-wrap:wrap;
                gap:0.25rem;
                margin:1rem 0;
                text-align:center;
            `
            : `
                display:inline-flex;
                align-items:center;
                flex-wrap:nowrap;
                gap:0.18rem;
                vertical-align:middle;
                white-space:nowrap;
            `;

        return `
            <${wrapperTag} class="${wrapperClass}" style="${wrapperStyle}">
                ${pieces.join("")}
            </${wrapperTag}>
        `;
    }

    function normalizeExplicitMatrixDelimiter(delimiter) {
        const value = String(delimiter || "").trim();

        if (value === "\\{") {
            return "{";
        }

        if (value === "\\}") {
            return "}";
        }

        if (value === ".") {
            return "";
        }

        return value;
    }

    function appendMatrixSequenceMathPiece(pieces, value) {
        const cleanValue = normalizeMatrixSequenceMath(value);

        if (!cleanValue) {
            return;
        }

        if (/^[.,;:]+$/.test(cleanValue)) {
            pieces.push(
                `<span style="display:inline-block;">${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanValue)}</span>`
            );
            return;
        }

        pieces.push(
            `<span style="display:inline-block; vertical-align:middle;">\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanValue)}\\)</span>`
        );
    }

    function normalizeMatrixSequenceMath(value) {
        return window.MathCmsRenderStructuredMath
            .normalizeEqnarrayHtmlArtifacts(value)
            .replace(/\s+/g, " ")

            // Plain prose words inside math mode lose ordinary whitespace.
            // Put "where" back into MathJax text mode and add explicit spacing.
            .replace(
                /(^|[.,;:])\s*where\s*/gi,
                function(_, punctuation) {
                    return `${punctuation}\\;\\text{where}\\;`;
                }
            )

            .trim();
    }

    window.MathCmsRenderMatrixSequences = {
        convertRemainingMatrixMathSequencesToHtml,
        containsSimpleMatrixEnvironment,
        buildMatrixMathSequenceHtml
    };
})();
