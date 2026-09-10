(() => {
    function convertPiecewiseArraysToHtml(tex) {
        if (!tex) return "";

        let output = String(tex);

        // A display block may contain more than one piecewise array:
        //
        // \[
        //   t_1 := \left\{ ... \right.
        //   \hspace{1cm}
        //   t_2 := \left\{ ... \right.
        // \]
        //
        // Process the complete display body and extract each array separately.
        output = output.replace(
            /\\\[([\s\S]*?)\\\]/gi,
            function(fullMatch, body) {
                if (!containsPiecewiseArray(body)) {
                    return fullMatch;
                }

                return buildPiecewiseDisplaySequenceHtml(body);
            }
        );

        // Legacy $$ ... $$ display form.
        output = output.replace(
            /\$\$([\s\S]*?)\$\$/gi,
            function(fullMatch, body) {
                if (!containsPiecewiseArray(body)) {
                    return fullMatch;
                }

                return buildPiecewiseDisplaySequenceHtml(body);
            }
        );

        // Inline-dollar cases environment.
        //
        // Some list items contain constructs such as:
        //
        //   Mode $= \begin{cases} ... \end{cases}$
        //
        // Promote the complete inline fragment into the HTML piecewise renderer.
        // Inline-dollar cases environment.
        output = output.replace(
            /\$([^$]*?)\\begin\s*\{cases\}([\s\S]*?)\\end\s*\{cases\}\s*\$/gi,
            function(_, prefix, body) {
                return buildPiecewiseArrayHtml(
                    prefix,
                    body,
                    { inline: true }
                );
            }
        );

        // Display-wrapped cases environment.
        output = output.replace(
            /\\\[\s*((?:(?!\\\])[\s\S])*?)\\begin\s*\{cases\}([\s\S]*?)\\end\s*\{cases\}\s*\\\]/gi,
            function(_, prefix, body) {
                return buildPiecewiseArrayHtml(prefix, body);
            }
        );

        // Legacy $$-wrapped cases environment.
        output = output.replace(
            /\$\$\s*([\s\S]*?)\\begin\s*\{cases\}([\s\S]*?)\\end\s*\{cases\}\s*\$\$/gi,
            function(_, prefix, body) {
                return buildPiecewiseArrayHtml(prefix, body);
            }
        );

        return output;
    }

    function containsPiecewiseArray(value) {
        /*
        * Only intercept genuinely one-sided piecewise arrays:
        *
        *   \left\{ \begin{array} ... \end{array} \right.
        *
        * Paired arrays ending in \right\} belong to the ordinary matrix
        * sequence renderer, which can draw matching scalable braces.
        */
        return /\\left\s*(?:\\?\{|\\lbrace)\s*\\begin\s*\{array\}\s*\{[^{}]*\}[\s\S]*?\\end\s*\{array\}\s*\\right\s*\./i
            .test(String(value || ""));
    }

    function buildPiecewiseDisplaySequenceHtml(displayBody) {
        const source = String(displayBody || "");

        const piecewisePattern =
            /\\left\s*(?:\\?\{|\\lbrace)\s*\\begin\s*\{array\}\s*\{([^{}]*)\}([\s\S]*?)\\end\s*\{array\}\s*\\right\s*\./gi;

        const pieces = [];
        let cursor = 0;
        let match;

        while ((match = piecewisePattern.exec(source)) !== null) {
            let prefix = source.slice(cursor, match.index);

            // Spacing commands between adjacent piecewise definitions should
            // become visual spacing between the generated HTML blocks.
            prefix = prefix
                .replace(/\\hspace\s*\{[^{}]*\}/gi, " ")
                .replace(/\\qquad\b/gi, " ")
                .replace(/\\quad\b/gi, " ")
                .trim();

            pieces.push(
                buildPiecewiseArrayHtml(
                    prefix,
                    match[2]
                )
            );

            cursor = piecewisePattern.lastIndex;
        }

        const trailingMath = source.slice(cursor).trim();

        if (trailingMath) {
            pieces.push(
                `<span style="display:inline-block; vertical-align:middle;">\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(trailingMath)}\\)</span>`
            );
        }

        if (pieces.length === 0) {
            return `\\[${source}\\]`;
        }

        return `
            <div class="pm-piecewise-sequence tex2jax_process" style="
                display:flex;
                align-items:center;
                justify-content:center;
                flex-wrap:wrap;
                gap:2rem;
                margin:1rem 0;
            ">
                ${pieces.join("")}
            </div>
        `;
    }

    function buildPiecewiseArrayHtml(prefix, body, options = {}) {
        const isInline = options.inline === true;
        const cleanPrefix = normalizePiecewiseMathCell(prefix);
        const normalizedBody = window.MathCmsRenderStructuredMath
            .normalizeEqnarrayHtmlArtifacts(body);

        const rows = window.MathCmsRenderStructuredMath
            .splitEqnarrayRows(normalizedBody)
            .map(
                window.MathCmsRenderStructuredMath
                    .splitEqnarrayCells
            )
            .filter(cells => cells.some(cell => cell.trim().length > 0));

        if (rows.length === 0) {
            return cleanPrefix ? `\\[${cleanPrefix}\\]` : "";
        }

        const rowHtml = rows.map(cells => {
            const leftCell = normalizePiecewiseMathCell(cells[0] || "");
            const rightCell = normalizePiecewiseMathCell(
                cells.slice(1).join(" ") || ""
            );

            return `
                <tr>
                    <td style="
                        padding:0.12rem 0.35rem;
                        text-align:left;
                        white-space:nowrap;
                        vertical-align:middle;
                    ">\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(leftCell)}\\)</td>

                    <td style="
                        padding:0.12rem 0.35rem;
                        text-align:left;
                        white-space:nowrap;
                        vertical-align:middle;
                    ">
                        ${buildPiecewiseConditionHtml(rightCell)}
                    </td>
                </tr>
            `;
        }).join("");

        const prefixHtml = cleanPrefix
            ? `<span style="
                    display:inline-flex;
                    align-items:center;
                    align-self:center;
                    margin-right:0.18rem;
                ">\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanPrefix)}\\)</span>`
            : "";

        if (isInline) {
            const braceHtml = window.MathCmsRenderDelimiters
                .renderMatrixDelimiter("{", "left");

            return `
                <span
                    class="pm-piecewise-block pm-piecewise-inline tex2jax_process"
                    style="
                        display:inline-flex;
                        align-items:center;
                        vertical-align:middle;
                        margin-left:0.22rem;
                        margin-top:0.10rem;
                        margin-bottom:0.10rem;
                        white-space:nowrap;
                    "
                >
                    ${cleanPrefix
                        ? `
                            <span style="
                                display:inline-flex;
                                align-items:center;
                                margin-right:0.16rem;
                                white-space:nowrap;
                            ">
                                \\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanPrefix)}\\)
                            </span>
                        `
                        : ""
                    }

                    <span style="
                        display:inline-flex;
                        align-items:stretch;
                        align-self:stretch;
                        vertical-align:middle;
                        gap:0.06rem;
                    ">
                        ${braceHtml}

                        <table style="
                            display:inline-table;
                            align-self:center;
                            vertical-align:middle;
                            border-collapse:collapse;
                            text-align:left;
                        ">
                            ${rowHtml}
                        </table>
                    </span>
                </span>
            `;
        }

        return `
            <div
                class="pm-piecewise-block tex2jax_process"
                style="
                    display:flex;
                    align-items:stretch;
                    justify-content:center;
                    margin:1rem 0;
                "
            >
                ${prefixHtml}

                <span style="
                    display:inline-flex;
                    align-items:stretch;
                    align-self:stretch;
                    vertical-align:middle;
                    margin-right:0.10rem;
                ">
                    ${window.MathCmsRenderDelimiters
                        .renderMatrixDelimiter("{", "left")}
                </span>

                <table style="
                    display:inline-table;
                    vertical-align:middle;
                    border-collapse:collapse;
                    text-align:left;
                ">
                    ${rowHtml}
                </table>
            </div>
        `;
    }

    function buildPiecewiseConditionHtml(value) {
        let condition = String(value || "").trim();

        // Accept either the original TeX wrappers or plain prose left behind
        // by earlier normalization.
        condition = condition
        // Wrapper contains both prose and the following math:
        // \mbox{if \gamma>1}
        // \text{when x\le r}
        .replace(
            /^\\(?:mbox|text|textrm)\{\s*(if|when)\s+([\s\S]*?)\s*\}$/i,
            "$1 $2"
        )

        // Wrapper contains only prose:
        // \mbox{otherwise}
        .replace(
            /^\\(?:mbox|text|textrm)\{\s*(otherwise\.?)\s*\}$/i,
            "$1"
        )

        // Prose wrapper followed by math outside the braces:
        // \mbox{if }\gamma>1
        .replace(
            /^\\(?:mbox|text|textrm)\{\s*(if|when)\s*\}\s*/i,
            "$1 "
        )
        .replace(
            /^\\(?:mbox|text|textrm)\{\s*(otherwise\.?)\s*\}\s*/i,
            "$1 "
        )
        .trim();

        const proseMatch = condition.match(
            /^(if|when|otherwise\.?)\b\s*(.*)$/i
        );

        if (!proseMatch) {
            return `\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(condition)}\\)`;
        }

        const prose = proseMatch[1];
        const remainingMath = proseMatch[2].trim();

        const proseHtml = `<span style="font-style:normal;">${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(prose)}</span>`;

        if (!remainingMath) {
            return proseHtml;
        }

        return `
            <span style="
                display:inline-flex;
                align-items:baseline;
                column-gap:0.45rem;
                white-space:nowrap;
            ">
                ${proseHtml}

                <span style="display:inline-block;">
                    \\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(remainingMath)}\\)
                </span>
            </span>
        `;
    }

    function normalizePiecewiseMathCell(value) {
        return window.MathCmsRenderStructuredMath
            .normalizeEqnarrayHtmlArtifacts(value)
            .replace(/\\textrm\{([^{}]*)\}/gi, "\\text{$1}")
            .replace(/\\mbox\{([^{}]*)\}/gi, "\\text{$1}")
            .replace(/\s+/g, " ")
            .trim();
    }

    window.MathCmsRenderPiecewise = {
        convertPiecewiseArraysToHtml
    };
})();
