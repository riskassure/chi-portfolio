// frontend/math/render/xy/math_render_xy_conversion.js

(function () {
    function convertUnderbracedXyMatrixToHtml(tex) {
        const source = String(tex || "");

        let result = "";
        let cursor = 0;

        while (cursor < source.length) {
            const underbraceIndex = source.indexOf("\\underbrace", cursor);

            if (underbraceIndex === -1) {
                result += source.slice(cursor);
                break;
            }

            const contentStart =
                window.MathCmsRenderXyParser
                    .findNextNonSpaceIndex(
                        source,
                        underbraceIndex + "\\underbrace".length
                    );

            if (contentStart === -1 || source[contentStart] !== "{") {
                result += source.slice(cursor, underbraceIndex + "\\underbrace".length);
                cursor = underbraceIndex + "\\underbrace".length;
                continue;
            }

            const contentEnd = window.MathCmsRenderStructuredMath
                .findMatchingBrace(source, contentStart);

            if (contentEnd === -1) {
                result += source.slice(cursor);
                break;
            }

            const content = source.slice(contentStart + 1, contentEnd).trim();

            if (!content.startsWith("\\xymatrix")) {
                result += source.slice(cursor, contentEnd + 1);
                cursor = contentEnd + 1;
                continue;
            }

            const subscriptMatch = source
                .slice(contentEnd + 1)
                .match(/^\s*_\s*\{/);

            if (!subscriptMatch) {
                result += source.slice(cursor, contentEnd + 1);
                cursor = contentEnd + 1;
                continue;
            }

            const labelStart =
                contentEnd + 1 +
                subscriptMatch[0].lastIndexOf("{");

            const labelEnd = window.MathCmsRenderStructuredMath
                .findMatchingBrace(source, labelStart);

            if (labelEnd === -1) {
                result += source.slice(cursor);
                break;
            }

            const matrixStart = content.indexOf("\\xymatrix");
            const matrixBraceStart =
                window.MathCmsRenderXyParser
                    .findXyMatrixBodyStart(
                        content,
                        matrixStart + "\\xymatrix".length
                    );

            const matrixBraceEnd =
                matrixBraceStart === -1
                    ? -1
                    : window.MathCmsRenderStructuredMath
                        .findMatchingBrace(content, matrixBraceStart);

            if (matrixBraceEnd === -1) {
                result += source.slice(cursor, labelEnd + 1);
                cursor = labelEnd + 1;
                continue;
            }

            const matrixBody = content.slice(
                matrixBraceStart + 1,
                matrixBraceEnd
            );

            const rawLabel = source.slice(labelStart + 1, labelEnd);

            const cleanLabel = rawLabel
                .replace(/\\displaystyle\s*/gi, "")
                .replace(/\\mbox\s*\{([^{}]*)\}/gi, "\\text{$1}")
                .trim();

            const html = `
                <figure class="pm-underbraced-xymatrix tex2jax_process" style="
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    width:max-content;
                    max-width:100%;
                    margin:1rem auto;
                ">
                    ${window.MathCmsRenderXyTable.buildHtmlTableFromXyMatrixBody(matrixBody)}

                    <div aria-hidden="true" style="
                        width:100%;
                        height:0.55rem;
                        border-bottom:1.5px solid currentColor;
                        border-left:1.5px solid currentColor;
                        border-right:1.5px solid currentColor;
                        border-radius:0 0 45% 45%;
                        margin-top:-0.7rem;
                    "></div>

                    <figcaption style="margin-top:0.2rem;">
                        \\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanLabel)}\\)
                    </figcaption>
                </figure>
            `;

            let replaceStart = underbraceIndex;
            let replaceEnd = labelEnd + 1;

            const before = source.slice(0, underbraceIndex);

            // Support either \[ ... \] or $$ ... $$.
            const latexDisplayStartMatch = before.match(/\\\[\s*$/);
            const dollarDisplayStartMatch = before.match(/\$\$\s*$/);

            let displayWrapper = "";

            if (latexDisplayStartMatch) {
                replaceStart =
                    underbraceIndex - latexDisplayStartMatch[0].length;
                displayWrapper = "latex";
            } else if (dollarDisplayStartMatch) {
                replaceStart =
                    underbraceIndex - dollarDisplayStartMatch[0].length;
                displayWrapper = "dollar";
            }

            if (displayWrapper === "latex") {
                const displayEndMatch = source
                    .slice(replaceEnd)
                    .match(/^\s*\\\]/);

                if (displayEndMatch) {
                    replaceEnd += displayEndMatch[0].length;
                }
            } else if (displayWrapper === "dollar") {
                const displayEndMatch = source
                    .slice(replaceEnd)
                    .match(/^\s*\$\$/);

                if (displayEndMatch) {
                    replaceEnd += displayEndMatch[0].length;
                }
            }

            result += source.slice(cursor, replaceStart);
            result += html;

            cursor = replaceEnd;
        }

        return result;
    }

    function convertXyMatrixToHtml(tex) {
        if (!tex) return "";

        let result = "";
        let cursor = 0;

        while (cursor < tex.length) {
            const matrixIndex = tex.indexOf("\\xymatrix", cursor);

            if (matrixIndex === -1) {
                result += tex.slice(cursor);
                break;
            }

            const braceStart =
                window.MathCmsRenderXyParser
                    .findXyMatrixBodyStart(
                        tex,
                        matrixIndex + "\\xymatrix".length
                    );

            if (braceStart === -1) {
                result += tex.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            const braceEnd = window.MathCmsRenderStructuredMath
                .findMatchingBrace(tex, braceStart);

            if (braceEnd === -1) {
                result += tex.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            let replaceStart = matrixIndex;
            let replaceEnd = braceEnd + 1;

            const before = tex.slice(0, matrixIndex);
            const after = tex.slice(replaceEnd);

            const displayStartMatch =
                before.match(/\\\[\s*$/);

            const inlineStartCandidate =
                displayStartMatch
                    ? null
                    : before.match(/\$([^$\r\n]*)$/);

            const inlineStartMatch =
                inlineStartCandidate
                && !String(
                    inlineStartCandidate[1] || ""
                ).includes("\\xymatrix")
                    ? inlineStartCandidate
                    : null;

            const inlineEndMatch =
                inlineStartMatch
                    ? after.match(/^\s*\$/)
                    : null;

            let leadingInlineMath = "";

            if (displayStartMatch) {
                replaceStart =
                    matrixIndex - displayStartMatch[0].length;

            } else if (
                inlineStartMatch
                && inlineEndMatch
            ) {
                replaceStart =
                    matrixIndex - inlineStartMatch[0].length;

                replaceEnd += inlineEndMatch[0].length;

                leadingInlineMath =
                    String(inlineStartMatch[1] || "").trim();
            }

            // A display xymatrix commonly ends with punctuation:
            //
            //   \xymatrix{...}.
            //   \xymatrix{...},
            //
            // Consume that punctuation together with the closing display delimiter,
            // then restore it outside the generated diagram HTML.
            const displayEndMatch = after.match(
                /^(\s*[.,;:]?)\s*\\\]/
            );

            let trailingDisplayPunctuation = "";

            if (displayEndMatch) {
                trailingDisplayPunctuation = displayEndMatch[1].trim();
                replaceEnd += displayEndMatch[0].length;
            }

            const body =
                tex.slice(braceStart + 1, braceEnd);

            const matrixHtml =
                window.MathCmsRenderXyTable.buildHtmlTableFromXyMatrixBody(body);

            let html;

            if (leadingInlineMath) {
                /*
                * Source forms such as:
                *
                *   $P:\xymatrix{...}$
                *
                * place the label directly beside the diagram. Remove the matrix's
                * ordinary standalone margin and center the combined unit.
                */
                const compactMatrixHtml =
                    matrixHtml.replace(
                        "margin:1rem auto;",
                        "margin:0;"
                    );

                html = `
                    <div
                        class="pm-xymatrix-labeled-display tex2jax_process"
                        style="
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            gap:1.00rem;
                            margin:1rem 0;
                        "
                    >
                        <span style="white-space:nowrap;">
                            \\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(leadingInlineMath)}\\)
                        </span>

                        ${compactMatrixHtml}
                    </div>

                    ${trailingDisplayPunctuation}
                `;

            } else {
                html =
                    matrixHtml +
                    trailingDisplayPunctuation;
            }

            result += tex.slice(cursor, replaceStart);
            result += html;

            cursor = replaceEnd;
        }

        return result;
    }

    window.MathCmsRenderXyConversion = {
        convertUnderbracedXyMatrixToHtml,
        convertXyMatrixToHtml
    };
})();
