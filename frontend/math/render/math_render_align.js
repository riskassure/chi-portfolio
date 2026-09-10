(() => {
    function convertAlignEnvironmentsToHtml(tex) {
        if (!tex) return "";

        let output = String(tex || "");

        // Display-wrapped align / alignat:
        // \[\begin{align*} ... \end{align*}\]
        // \[\begin{alignat*}{2} ... \end{alignat*}\]
        output = output.replace(
            /\\\[\s*\\begin\{(align\*?|alignat\*?)\}\s*(?:\{[^{}]*\})?([\s\S]*?)\\end\{\1\}\s*\\\]/gi,
            function(_, envName, body) {
                return buildHtmlTableFromAlignBody(body);
            }
        );

        // Raw standalone align / alignat.
        output = output.replace(
            /\\begin\{(align\*?|alignat\*?)\}\s*(?:\{[^{}]*\})?([\s\S]*?)\\end\{\1\}/gi,
            function(_, envName, body) {
                return buildHtmlTableFromAlignBody(body);
            }
        );

        return output;
    }

    function buildHtmlTableFromAlignBody(body) {
        const normalizedBody = window.MathCmsRenderStructuredMath
            .normalizeEqnarrayHtmlArtifacts(body);

        const rows = window.MathCmsRenderAlignRows
            .splitAlignRows(normalizedBody)
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
                const align = window.MathCmsRenderAlignRows
                    .getAlignColumnAlign(index);

                const cleanCell = window.MathCmsRenderAlignRows
                    .normalizeAlignCell(cell);

                if (!cleanCell) {
                    return `<td style="padding:0.12rem 0.28rem; text-align:${align};"></td>`;
                }

                const renderedCell = window.MathCmsRenderMatrixSequences
                    .containsSimpleMatrixEnvironment(cleanCell)
                    ? window.MathCmsRenderMatrixSequences
                        .buildMatrixMathSequenceHtml(
                            cleanCell,
                            false
                        )
                    : `\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanCell)}\\)`;

                return `
                    <td style="
                        padding:0.12rem 0.28rem;
                        text-align:${align};
                        white-space:nowrap;
                        vertical-align:middle;
                    ">
                        ${renderedCell}
                    </td>
                `;
            }).join("");

            return `<tr>${htmlCells}</tr>`;
        }).join("");

        return `
            <table class="pm-align-table tex2jax_process" style="border-collapse:collapse; margin:1rem auto;">
                ${htmlRows}
            </table>
        `;
    }
    window.MathCmsRenderAlign = {
        convertAlignEnvironmentsToHtml
    };
})();
