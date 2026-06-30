// frontend/math/math_render_helpers.js

(function () {
    const DEFAULT_API_ENDPOINT = "http://127.0.0.1:5000/api";

    window.MathCmsRender = {
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

    function cleanLaTeXEnvironments(tex) {
        if (!tex) return "";

        let clean = tex;

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