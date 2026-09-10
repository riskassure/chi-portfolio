(() => {
    function buildDisplayMatrixHtmlWithAffixes(envName, prefix, body, suffix = "") {
        const affixInfo = extractMatrixAffixDelimiters(prefix, suffix, envName);

        const cleanPrefix = normalizeDetachedMatrixAffix(
            normalizeMatrixAffix(affixInfo.prefix)
        );

        const cleanSuffix = normalizeDetachedMatrixAffix(
            normalizeMatrixAffix(affixInfo.suffix)
        );

        const prefixHtml = cleanPrefix
            ? `<span style="display:inline-block; vertical-align:middle; margin-right:0.25rem;">\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanPrefix)}\\)</span>`
            : "";

        let suffixHtml = "";

        if (cleanSuffix) {
            if (/^[.,;:]$/.test(cleanSuffix)) {
                suffixHtml = `<span style="display:inline-block; vertical-align:middle; margin-left:0.08rem;">${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanSuffix)}</span>`;
            } else {
                suffixHtml = `<span style="display:inline-block; vertical-align:middle; margin-left:0.25rem;">\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanSuffix)}\\)</span>`;
            }
        }

        return `
            <div class="pm-matrix-display tex2jax_process" style="text-align:center; margin:1rem 0;">
                ${prefixHtml}${window.MathCmsRenderMatrixCore
                    .buildMatrixEnvironmentHtml(
                        envName,
                        body,
                        affixInfo.delimiters
                    )}${suffixHtml}
            </div>
        `;
    }

    function extractMatrixAffixDelimiters(prefix, suffix, envName) {
        let cleanPrefix = String(prefix || "");
        let cleanSuffix = String(suffix || "");

        let delimiters = window.MathCmsRenderMatrixCore
            .getMatrixDelimiters(envName);

        const leftMatch = cleanPrefix.match(
            /\\left\s*(\.|\(|\[|\{|\||\\\{|\\lbrace|\\vert|\\lvert|\\Vert|\\lVert)\s*$/i
        );

        const rightMatch = cleanSuffix.match(
            /^\s*\\right\s*(\.|\)|\]|\}|\||\\\}|\\rbrace|\\vert|\\rvert|\\Vert|\\rVert)/i
        );

        if (leftMatch && rightMatch) {
            const leftDelimiter = latexMatrixDelimiterTokenToText(leftMatch[1], "left");
            const rightDelimiter = latexMatrixDelimiterTokenToText(rightMatch[1], "right");

            delimiters = {
                left: leftDelimiter,
                right: rightDelimiter
            };

            cleanPrefix = cleanPrefix.slice(0, leftMatch.index);
            cleanSuffix = cleanSuffix.slice(rightMatch[0].length);
        }

        return {
            prefix: cleanPrefix,
            suffix: cleanSuffix,
            delimiters
        };
    }

    function normalizeDetachedMatrixAffix(value) {
        return String(value || "")
            // Opening delimiters that no longer have a matching \right
            // in the same MathJax expression.
            .replace(/\\left\s*\\\{/g, "\\lbrace")
            .replace(/\\left\s*\\\[/g, "\\lbrack")
            .replace(/\\left\s*\(/g, "(")
            .replace(/\\left\s*\./g, "")

            // Closing or middle delimiters that no longer have a matching
            // \left in the same MathJax expression.
            .replace(/\\right\s*\\\}/g, "\\rbrace")
            .replace(/\\right\s*\\\]/g, "\\rbrack")
            .replace(/\\right\s*\)/g, ")")
            .replace(/\\right\s*\|/g, "\\mid")
            .replace(/\\right\s*\\vert/g, "\\mid")
            .replace(/\\right\s*\./g, "");
    }

    function latexMatrixDelimiterTokenToText(token, side = "left") {
        const clean = String(token || "").trim();

        if (!clean || clean === ".") {
            return "";
        }

        if (clean === "(" || clean === "\\(") {
            return "(";
        }

        if (clean === ")" || clean === "\\)") {
            return ")";
        }

        if (clean === "[" || clean === "\\[") {
            return "[";
        }

        if (clean === "]" || clean === "\\]") {
            return "]";
        }

        if (
            clean === "{" ||
            clean === "\\{" ||
            clean === "\\lbrace"
        ) {
            return "{";
        }

        if (
            clean === "}" ||
            clean === "\\}" ||
            clean === "\\rbrace"
        ) {
            return "}";
        }

        if (
            clean === "|" ||
            clean === "\\vert" ||
            clean === "\\lvert" ||
            clean === "\\rvert"
        ) {
            return "|";
        }

        if (
            clean === "\\Vert" ||
            clean === "\\lVert" ||
            clean === "\\rVert"
        ) {
            return "‖";
        }

        return side === "left" ? "" : "";
    }

    function normalizeMatrixAffix(value) {
        return window.MathCmsRenderStructuredMath
            .normalizeEqnarrayHtmlArtifacts(value)
            .replace(/\s+/g, " ")
            .trim();
    }

    window.MathCmsRenderMatrixAffixes = {
        buildDisplayMatrixHtmlWithAffixes
    };
})();
