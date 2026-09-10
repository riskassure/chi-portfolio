// frontend/math/math_render_xy_cleanup.js

(function () {
    function stripXyMatrixSetupMacros(tex) {
        if (!tex) return "";

        return String(tex)
            .replace(/\\UseAllTwocells\b/g, "")
            .replace(/\\UseComputerModernTips\b/g, "");
    }

    function renderXyMatrixConnectorMath(tex) {
        if (!tex) return "";

        return String(tex)
            .replace(
                /\\quad\s*\{:=\}\s*\\quad/g,
                '<span class="pm-xymatrix-connector" style="display:inline-block; margin:0 0.55rem;">\\({:=}\\)</span>'
            )
            .replace(
                /\\quad\s*\{=\}\s*\\quad/g,
                '<span class="pm-xymatrix-connector" style="display:inline-block; margin:0 0.55rem;">\\({=}\\)</span>'
            );
    }

    function normalizeXyMatrixHtmlArtifacts(value) {
        const source = String(value || "");

        let result = "";
        let cursor = 0;

        while (cursor < source.length) {
            const matrixIndex = source.indexOf("\\xymatrix", cursor);

            if (matrixIndex === -1) {
                result += source.slice(cursor);
                break;
            }

            const braceStart =
                window.MathCmsRenderXyParser
                    .findXyMatrixBodyStart(
                        source,
                        matrixIndex + "\\xymatrix".length
                    );

            if (braceStart === -1) {
                result += source.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            const braceEnd = window.MathCmsRenderStructuredMath
                .findMatchingBrace(source, braceStart);

            if (braceEnd === -1) {
                result += source.slice(cursor);
                break;
            }

            const body = source.slice(braceStart + 1, braceEnd);

            const normalizedBody =
                window.MathCmsRenderStructuredMath
                    .normalizeEqnarrayHtmlArtifacts(body);

            result += source.slice(cursor, braceStart + 1);
            result += normalizedBody;
            result += "}";

            cursor = braceEnd + 1;
        }

        return result;
    }

    function protectXyMatrixHtml(clean) {
        // Temporarily protect generated xymatrix HTML while literal angle brackets
        // in the remaining TeX are normalized.
        const xymatrixHtmlBlocks = [];

        // Protect the entire underbraced xymatrix wrapper first.
        clean = clean.replace(
            /<figure\b[^>]*class=["'][^"']*\bpm-underbraced-xymatrix\b[^"']*["'][^>]*>[\s\S]*?<\/figure>/gi,
            (figureHtml) => {
                const index = xymatrixHtmlBlocks.length;
                xymatrixHtmlBlocks.push(figureHtml);
                return `PMXYMATRIXHTMLPLACEHOLDER${index}END`;
            }
        );

        // Protect ordinary generated xymatrix tables.
        clean = clean.replace(
            /<table\b[^>]*class=["'][^"']*\bpm-xymatrix-table\b[^"']*["'][^>]*>[\s\S]*?<\/table>/gi,
            (tableHtml) => {
                const index = xymatrixHtmlBlocks.length;
                xymatrixHtmlBlocks.push(tableHtml);
                return `PMXYMATRIXHTMLPLACEHOLDER${index}END`;
            }
        );

        return { text: clean, blocks: xymatrixHtmlBlocks };
    }

    function restoreXyMatrixHtml(clean, xymatrixHtmlBlocks) {
        // Restore the generated HTML after TeX angle-bracket normalization.
        clean = clean.replace(
            /PMXYMATRIXHTMLPLACEHOLDER(\d+)END/g,
            (match, indexText) => {
                const index = Number(indexText);
                return xymatrixHtmlBlocks[index] ?? match;
            }
        );

        return clean;
    }

    window.MathCmsRenderXyCleanup = {
        stripXyMatrixSetupMacros,
        renderXyMatrixConnectorMath,
        normalizeXyMatrixHtmlArtifacts,
        protectXyMatrixHtml,
        restoreXyMatrixHtml
    };
})();
