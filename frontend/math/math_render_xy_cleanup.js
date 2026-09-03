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

    window.MathCmsRenderXyCleanup = {
        stripXyMatrixSetupMacros,
        renderXyMatrixConnectorMath,
        normalizeXyMatrixHtmlArtifacts
    };
})();
