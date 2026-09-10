(() => {
    function buildMatrixEnvironmentHtml(envName, body, delimiterOverride = null, arraySpec = "") {
        const normalizedBody = window.MathCmsRenderStructuredMath
            .normalizeEqnarrayHtmlArtifacts(body);

        const rows = splitMatrixBodyRows(normalizedBody)
            .map(
                window.MathCmsRenderStructuredMath
                    .splitEqnarrayCells
            )
            .filter(cells => cells.some(cell => cell.trim().length > 0));

        if (rows.length === 0) {
            return "";
        }

        const maxColumns = Math.max(...rows.map(cells => cells.length));
        const delimiters = delimiterOverride || getMatrixDelimiters(envName);

        const htmlCells = rows.map(cells => {
            const paddedCells = window.MathCmsRenderStructuredMath
                .padEqnarrayCells(cells, maxColumns);

            return paddedCells.map(cell => {
                const cleanCell = normalizeMatrixCell(cell);

                if (!cleanCell) {
                    return `
                        <span style="
                            display:block;
                            padding:0.10rem 0.35rem;
                            text-align:center;
                            white-space:nowrap;
                        "></span>
                    `;
                }

                return `
                    <span style="
                        display:block;
                        padding:0.10rem 0.35rem;
                        text-align:center;
                        white-space:nowrap;
                    ">\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanCell)}\\)</span>
                `;
            }).join("");
        }).join("");

        const leftDelimiter = window.MathCmsRenderDelimiters
            .renderMatrixDelimiter(delimiters.left, "left");
        const rightDelimiter = window.MathCmsRenderDelimiters
            .renderMatrixDelimiter(delimiters.right, "right");

        return `
            <span class="pm-matrix-render" style="display:inline-flex; align-items:stretch; justify-content:center; gap:0.06rem; vertical-align:middle; line-height:1;">
                ${leftDelimiter}
                <span class="pm-matrix-grid" style="
                    display:inline-grid;
                    grid-template-columns:repeat(${maxColumns}, max-content);
                    align-self:center;
                    vertical-align:middle;
                    margin:0.08rem 0;
                ">
                    ${htmlCells}
                </span>
                ${rightDelimiter}
            </span>
        `;
    }

    function splitMatrixBodyRows(body) {
        const normalized = String(body || "").trim();

        if (!normalized) {
            return [];
        }

        const slashRows = window.MathCmsRenderStructuredMath
            .splitEqnarrayRows(normalized);

        if (slashRows.length > 1) {
            return slashRows;
        }

        // Many PlanetMath matrix rows lost their LaTeX \\ row separators
        // but still have actual line breaks in rendered_tex.
        const newlineRows = normalized
            .split(/\r?\n+/)
            .map(row => row.trim())
            .filter(row => row.length > 0);

        if (newlineRows.length > 1) {
            return newlineRows;
        }

        return slashRows;
    }

    function normalizeMatrixCell(cell) {
        return window.MathCmsRenderStructuredMath
            .normalizeEqnarrayHtmlArtifacts(cell)
            .replace(/\s+/g, " ")
            .trim();
    }

    function getMatrixDelimiters(envName) {
        const name = String(envName || "");

        if (name === "pmatrix") {
            return { left: "(", right: ")" };
        }

        if (name === "bmatrix") {
            return { left: "[", right: "]" };
        }

        if (name === "Bmatrix") {
            return { left: "{", right: "}" };
        }

        if (name === "vmatrix") {
            return { left: "|", right: "|" };
        }

        if (name === "Vmatrix") {
            return { left: "‖", right: "‖" };
        }

        return { left: "", right: "" };
    }

    window.MathCmsRenderMatrixCore = {
        buildMatrixEnvironmentHtml,
        getMatrixDelimiters
    };
})();
