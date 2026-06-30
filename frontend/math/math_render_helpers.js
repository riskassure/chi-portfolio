// frontend/math/math_render_helpers.js

(function () {
    const DEFAULT_API_ENDPOINT = "http://127.0.0.1:5000/api";

    window.MathCmsRender = {
        debugVersion: "eqnarray-html-table-v1",
        getDisplayTex,
        prepareConceptHtml,
        cleanLaTeXEnvironments,
        normalizeDiagramImageUrls
    };

    function getDisplayTex(concept) {
        return (
            concept?.display_tex ||
            concept?.rendered_tex ||
            concept?.cleaned_tex ||
            "No textual mathematical content saved."
        );
    }

    function prepareConceptHtml(tex, options = {}) {
        const apiEndpoint =
            options.apiEndpoint ||
            window.MATH_CMS_API_ENDPOINT ||
            DEFAULT_API_ENDPOINT;

        let clean = tex || "";

        clean = cleanLaTeXEnvironments(clean);
        clean = normalizeDiagramImageUrls(clean, apiEndpoint);

        return clean;
    }

    function normalizeEqnarrayHtmlArtifacts(value) {
        return String(value || "")
            // These artifacts can appear inside old rendered_tex equation arrays.
            // Treat paragraph breaks inside eqnarray as equation row breaks.
            .replace(/<br\s*\/?>\s*<\/p>\s*<p[^>]*>/gi, "\\\\")
            .replace(/<\/p>\s*<p[^>]*>/gi, "\\\\")
            .replace(/<br\s*\/?>/gi, "\\\\")

            // Remove any leftover paragraph wrappers.
            .replace(/<\/?p[^>]*>/gi, "")

            // Common HTML whitespace artifact.
            .replace(/&nbsp;/gi, " ");
    }

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
        const normalizedBody = normalizeEqnarrayHtmlArtifacts(body);

        const rows = splitEqnarrayRows(normalizedBody)
            .map(splitEqnarrayCells)
            .filter(cells => cells.some(cell => cell.trim().length > 0));

        if (rows.length === 0) {
            return "";
        }

        const maxColumns = Math.max(...rows.map(cells => cells.length));

        const htmlRows = rows.map(cells => {
            const paddedCells = padEqnarrayCells(cells, maxColumns);

            const htmlCells = paddedCells.map((cell, index) => {
                const align = getEqnarrayColumnAlign(index);
                const cleanCell = normalizeEqnarrayCell(cell);

                if (!cleanCell) {
                    return `<td style="padding:0.15rem 0.35rem; text-align:${align};"></td>`;
                }

                return `<td style="padding:0.15rem 0.35rem; text-align:${align}; white-space:nowrap;">\\(${escapeHtmlForMathCell(cleanCell)}\\)</td>`;
            }).join("");

            return `<tr>${htmlCells}</tr>`;
        }).join("");

        return `
            <table class="pm-eqnarray-table tex2jax_process" style="border-collapse:collapse; margin:1rem auto;">
                ${htmlRows}
            </table>
        `;
    }

    function splitEqnarrayCells(row) {
        return String(row || "")
            .split(/(?<!\\)&/g)
            .map(cell => cell.trim());
    }

    function padEqnarrayCells(cells, maxColumns) {
        const padded = [...cells];

        while (padded.length < maxColumns) {
            padded.push("");
        }

        return padded;
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

    function splitEqnarrayRows(body) {
        return String(body || "")
            // Split LaTeX row separators, including optional spacing like \\[4pt].
            .split(/\\\\(?:\s*\[[^\]]*\])?/g)
            .map(row => row.trim())
            .filter(Boolean);
    }

    function normalizeEqnarrayCell(cell) {
        return normalizeEqnarrayHtmlArtifacts(cell)
            .replace(/\s+/g, " ")
            .trim();
    }

    function escapeHtmlForMathCell(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function cleanLaTeXEnvironments(tex) {
        if (!tex) return "";

        let clean = tex;

        // Text-level underline used in PlanetMath prose.
        clean = clean.replace(/\\underline\{([^{}]+)\}/gi, "<u>$1</u>");

        // Normalize legacy eqnarray blocks before MathJax sees them.
        clean = convertEqnarrayToAligned(clean);

        // existing pspicture/list/etc cleanup continues below...
        clean = clean.replace(
            /\\begin\{pspicture\}[\s\S]*?\\end\{pspicture\}/gi,
            `<div class="img-placeholder mathjax-diagnostic-ignore"><em>[PSTricks diagram placeholder]</em></div>`
        );

        clean = clean.replace(/\\begin{enumerate}/gi, "<ol style='margin-top: 0.5rem; padding-left: 1.5rem;'>");
        clean = clean.replace(/\\end{enumerate}/gi, "</ol>");

        clean = clean.replace(/\\begin{itemize}/gi, "<ul style='margin-top: 0.5rem; padding-left: 1.5rem; list-style-type: disc;'>");
        clean = clean.replace(/\\end{itemize}/gi, "</ul>");

        clean = clean.replace(/\\item/gi, "<li style='margin-bottom: 0.25rem;'>");

        clean = clean.replace(/\\emph\{([^}]+)\}/gi, "<em>$1</em>");
        clean = clean.replace(/\\textbf\{([^}]+)\}/gi, "<strong>$1</strong>");

        clean = clean.replace(
            /\\begin\{(?:the)?bibliography\}\{[\s\S]*?\}/gi,
            "<div style='margin-top: 1.5rem; border-top: 1px dashed #cbd5e1; padding-top: 1rem;'><strong>References & Bibliography:</strong><ul style='list-style-type: square; padding-left: 1.5rem;'>"
        );
        clean = clean.replace(/\\end\{(?:the)?bibliography\}/gi, "</ul></div>");

        clean = clean.replace(/\\begin\{tabular\}\{[^}]*\}([\s\S]*?)\\end\{tabular\}/gi, function(_, body) {
            const rows = body
                .replace(/\\hline/g, "")
                .trim()
                .split(/\\\\/)
                .map(row => row.trim())
                .filter(row => row.length > 0);

            const htmlRows = rows.map((row, rowIndex) => {
                const cells = row.split("&").map(cell => cell.trim());
                const tag = rowIndex === 0 ? "th" : "td";

                return `<tr>` + cells.map(cell =>
                    `<${tag} style="border:1px solid #cbd5e1; padding:0.4rem 0.6rem;">${cell}</${tag}>`
                ).join("") + `</tr>`;
            }).join("");

            return `
                <table style="border-collapse:collapse; margin:1rem 0; width:100%;">
                    ${htmlRows}
                </table>
            `;
        });

        return clean;
    }

    function normalizeDiagramImageUrls(html, apiEndpoint = DEFAULT_API_ENDPOINT) {
        if (!html) return "";

        return html.replace(
            /src=(["'])\/api\/math\/diagrams\//gi,
            `src=$1${apiEndpoint}/math/diagrams/`
        );
    }
})();