(() => {
    function convertEqnarrayToAligned(tex) {
        if (!tex) return "";

        let output = tex;

        // Case 1: already wrapped as \[ \begin{eqnarray} ... \end{eqnarray} \]
        output = output.replace(
            /\\\[\s*\\begin\{(eqnarray\*?)\}([\s\S]*?)\\end\{\1\}\s*\\\]/gi,
            function(_, envName, body) {
                return buildHtmlTableFromEqnarrayBody(body);
            }
        );

        // Case 2: raw standalone \begin{eqnarray} ... \end{eqnarray}
        output = output.replace(
            /\\begin\{(eqnarray\*?)\}([\s\S]*?)\\end\{\1\}/gi,
            function(_, envName, body) {
                return buildHtmlTableFromEqnarrayBody(body);
            }
        );

        return output;
    }

    function buildHtmlTableFromEqnarrayBody(body) {
        const normalizedBody = window.MathCmsRenderStructuredMath
            .normalizeEqnarrayHtmlArtifacts(body)
            .replace(/\\cr\b/gi, "\\\\");

        const rows = window.MathCmsRenderStructuredMath
            .splitEqnarrayRows(normalizedBody)
            .map(window.MathCmsRenderStructuredMath.splitEqnarrayCells)
            .filter(cells => cells.some(cell => cell.trim().length > 0));

        if (rows.length === 0) {
            return "";
        }

        const maxColumns = Math.max(...rows.map(cells => cells.length));

        const htmlRows = rows.map(cells => {
            const paddedCells = window.MathCmsRenderStructuredMath
                .padEqnarrayCells(cells, maxColumns);

            const htmlCells = paddedCells.map((cell, index) => {
                const align = getEqnarrayColumnAlign(index);
                const cleanCell = normalizeEqnarrayCell(cell);

                if (!cleanCell) {
                    return `<td style="padding:0.15rem 0.35rem; text-align:${align};"></td>`;
                }

                return `<td style="
                    padding:0.15rem 0.35rem;
                    text-align:${align};
                    white-space:nowrap;
                ">\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanCell)}\\)</td>`;
            }).join("");

            return `<tr>${htmlCells}</tr>`;
        }).join("");

        return `
            <div style="max-width:100%; overflow-x:auto;">
                <table class="pm-eqnarray-table tex2jax_process"
                    style="border-collapse:collapse; margin:1rem auto; width:max-content;">
                    ${htmlRows}
                </table>
            </div>
        `;
    }

    function getEqnarrayColumnAlign(index) {
        if (index === 0) {
            return "right";
        }

        if (index % 2 === 1) {
            return "center";
        }

        return "left";
    }

    function normalizeEqnarrayCell(cell) {
        return window.MathCmsRenderStructuredMath
            .normalizeEqnarrayHtmlArtifacts(cell)
            .replace(/\s+/g, " ")
            // A malformed or partially normalized eqnarray row separator can
            // leave one trailing backslash in the final cell. If retained, it
            // combines with the generated closing \) delimiter and produces \\),
            // which MathJax cannot recognize as an inline-math closing delimiter.
            .replace(/\\+\s*$/, "")
            .trim();
    }

    window.MathCmsRenderEqnarray = {
        convertEqnarrayToAligned
    };
})();
