// frontend/math/math_render_xy_sequences.js

(function () {
    function renderMixedXyMatrixWrapperContent(content) {
        const source = String(content || "");

        if (!/pm-xymatrix-table/.test(source)) {
            return source;
        }

        const tableRegex =
            /<table\b[^>]*class=["'][^"']*\bpm-xymatrix-table\b[^"']*["'][^>]*>[\s\S]*?<\/table>/gi;

        const tokens = [];

        const normalizeSequenceTableHtml = tableHtml =>
            String(tableHtml || "")
                .replace(
                    /margin\s*:\s*1rem\s+auto\s*;/i,
                    "margin:0;"
                )
                .replace(
                    /margin\s*:\s*1rem\s+0\.45rem\s*;/i,
                    "margin:0;"
                );

        const pushMathText = text => {
            const normalized = String(text || "")
                .replace(/\s+/g, " ")
                .trim();

            if (!normalized) {
                return;
            }
            /*
            * A connector between converted xymatrix tables will be placed
            * inside its own MathJax wrapper below. Remove the surrounding
            * TeX spacing commands now so the later legacy connector cleanup
            * does not replace HTML inside that MathJax wrapper.
            */
            const sequenceConnectorMatch = normalized.match(
                /^\\quad\s*\{\s*(:?=)\s*\}\s*\\quad$/i
            );

            if (sequenceConnectorMatch) {
                tokens.push({
                    type: "math",
                    core: sequenceConnectorMatch[1],
                    punctuation: ""
                });

                return;
            }

            /*
            * Preserve an explicit TeX gap between adjacent diagrams as a CSS
            * spacer rather than sending \hspace to MathJax.
            */
            const hspaceMatch = normalized.match(
                /^\\hspace\*?\s*\{\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:pt|pc|in|bp|cm|mm|dd|cc|sp|em|ex))\s*\}$/i
            );

            if (hspaceMatch) {
                tokens.push({
                    type: "spacer",
                    width: hspaceMatch[1]
                });
                return;
            }

            const punctuationMatch =
                normalized.match(/^(.*?)([.,;:!?])$/);

            const core = punctuationMatch
                ? punctuationMatch[1].trim()
                : normalized;

            const trailingPunctuation = punctuationMatch
                ? punctuationMatch[2]
                : "";

            if (core) {
                tokens.push({
                    type: "math",
                    core,
                    punctuation: trailingPunctuation
                });
                return;
            }

            /*
            * A punctuation-only fragment after the final table belongs
            * to that table:
            *
            *   table = table .
            *
            * It must not become the first character of the next paragraph.
            */
            if (trailingPunctuation) {
                const lastToken = tokens[tokens.length - 1];

                if (lastToken?.type === "table") {
                    lastToken.punctuation =
                        `${lastToken.punctuation || ""}${trailingPunctuation}`;
                    return;
                }

                tokens.push({
                    type: "punctuation",
                    text: trailingPunctuation
                });
            }
        };

        let cursor = 0;
        let match;

        while ((match = tableRegex.exec(source)) !== null) {
            pushMathText(source.slice(cursor, match.index));

            tokens.push({
                type: "table",
                html: match[0],
                punctuation: ""
            });

            cursor = match.index + match[0].length;
        }

        pushMathText(source.slice(cursor));

        const tableCount =
            tokens.filter(token => token.type === "table").length;

        const hasConnector =
            tokens.some(token => token.type === "math");

        const hasExplicitSpacer =
            tokens.some(token => token.type === "spacer");

        const hasAttachedPunctuation =
            tokens.some(
                token =>
                    token.type === "table"
                    && Boolean(token.punctuation)
            );

        const needsSequenceLayout =
            tableCount > 1
            || hasConnector
            || hasAttachedPunctuation
            || hasExplicitSpacer;

        const renderToken = token => {
            if (token.type === "math") {
                return `
                    <span
                        class="pm-xymatrix-connector"
                        style="
                            display:inline-block;
                            margin:0;
                            white-space:nowrap;
                        "
                    >\\({}${token.core}{}\\)${token.punctuation || ""}</span>
                `;
            }

            if (token.type === "spacer") {
                return `
                    <span
                        aria-hidden="true"
                        style="
                            display:block;
                            flex:0 0 ${token.width};
                            width:${token.width};
                            height:1px;
                        "
                    ></span>
                `;
            }

            if (token.type === "table") {
                const tableHtml = needsSequenceLayout
                    ? normalizeSequenceTableHtml(token.html)
                    : token.html;

                if (!token.punctuation) {
                    return tableHtml;
                }

                return `
                    <div style="
                        display:inline-flex;
                        align-items:center;
                        white-space:nowrap;
                    ">
                        ${tableHtml}
                        <span style="margin-left:0.08rem;">
                            ${token.punctuation}
                        </span>
                    </div>
                `;
            }

            return token.text || "";
        };

        const renderedTokens =
            tokens.map(renderToken).join("");

        if (!needsSequenceLayout) {
            return renderedTokens;
        }

        return `
            <div
                class="pm-xymatrix-sequence"
                style="
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    flex-wrap:wrap;
                    gap:${hasExplicitSpacer ? "0" : "0.55rem"};
                    margin:1rem 0;
                "
            >
                ${renderedTokens}
            </div>
        `;
    }

    function unwrapConvertedXyMatrixMathWrappers(value) {
        let output = String(value || "");

        const tablePattern =
            '<table\\b[^>]*class=["\'][^"\']*\\bpm-xymatrix-table\\b[^"\']*["\'][^>]*>[\\s\\S]*?<\\/table>';

        const containsConvertedXyMatrixTable = inner =>
            /\bpm-xymatrix-table\b/i.test(
                String(inner || "")
            );

        /*
        * Match each complete equation wrapper first.
        *
        * Only unwrap it when that exact wrapper contains a converted
        * xymatrix table. This prevents the regex from crossing an earlier
        * closing delimiter while searching for a table farther down.
        */
        output = output.replace(
            /\\begin\{(equation\*?)\}([\s\S]*?)\\end\{\1\}/gi,
            function(fullMatch, environmentName, inner) {
                if (!containsConvertedXyMatrixTable(inner)) {
                    return fullMatch;
                }

                return window.MathCmsRenderXySequences
                    .renderMixedXyMatrixWrapperContent(inner);
            }
        );

        /*
        * Apply the same nearest-wrapper rule to $$ ... $$ displays.
        */
        output = output.replace(
            /\$\$([\s\S]*?)\$\$/g,
            function(fullMatch, inner) {
                if (!containsConvertedXyMatrixTable(inner)) {
                    return fullMatch;
                }

                return window.MathCmsRenderXySequences
                    .renderMixedXyMatrixWrapperContent(inner);
            }
        );

        /*
        * Apply the same nearest-wrapper rule to \[ ... \] displays.
        */
        output = output.replace(
            /\\\[([\s\S]*?)\\\]/g,
            function(fullMatch, inner) {
                if (!containsConvertedXyMatrixTable(inner)) {
                    return fullMatch;
                }

                return window.MathCmsRenderXySequences
                    .renderMixedXyMatrixWrapperContent(inner);
            }
        );

        /*
        * Process each complete single-dollar wrapper independently.
        *
        * This supports both:
        *
        *   $table$
        *   $table = table$
        *
        * without searching beyond that wrapper into surrounding prose.
        */
        output = output.replace(
            /(^|[^\\$])\$(?!\$)((?:\\.|[^\\$])*)\$(?!\$)/g,
            function (
                fullMatch,
                prefix,
                inner
            ) {
                if (
                    !containsConvertedXyMatrixTable(
                        inner
                    )
                ) {
                    return fullMatch;
                }

                return (
                    prefix
                    + window.MathCmsRenderXySequences
                        .renderMixedXyMatrixWrapperContent(
                            inner
                        )
                );
            }
        );

        /*
        * Same narrow rule for \( ... \).
        */
        output = output.replace(
            new RegExp(
                `\\\\\\(\\s*(${tablePattern})\\s*([,.;:!?]?)\\s*\\\\\\)`,
                "gi"
            ),
            (_, tableHtml, punctuation) =>
                `${tableHtml}${punctuation || ""}`
        );

        return output;
    }

    window.MathCmsRenderXySequences = {
        renderMixedXyMatrixWrapperContent,
        unwrapConvertedXyMatrixMathWrappers
    };
})();
