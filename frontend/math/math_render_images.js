(() => {

function normalizeLatexImageArtifacts(
    tex,
    escapeHtml
) {
    if (!tex) return "";

    let output = String(tex || "");

    // Remove figure wrappers but keep their contents.
    output = output.replace(
        /\\begin\{figure\*?\}(?:\[[^\]]*\])?/gi,
        ""
    );

    output = output.replace(
        /\\end\{figure\*?\}/gi,
        ""
    );

    // LaTeX layout commands around old EPS images.
    output = output.replace(
        /\\centering\b/gi,
        ""
    );

    // \scalebox{0.8}{\includegraphics{file.eps}}
    output = output.replace(
        /\\scalebox\{[^{}]*\}\s*\{\s*\\includegraphics(?:\[[^\]]*\])?\s*\{([^{}]*)\}\s*\}/gi,
        function (_, filename) {
            return makeLatexImagePlaceholder(
                filename,
                escapeHtml
            );
        }
    );

    // Plain \includegraphics[scale=...]{file.eps}
    // or \includegraphics{file.eps}
    output = output.replace(
        /\\includegraphics(?:\[[^\]]*\])?\s*\{([^{}]*)\}/gi,
        function (_, filename) {
            return makeLatexImagePlaceholder(
                filename,
                escapeHtml
            );
        }
    );

    // Preserve captions as readable prose.
    output = output.replace(
        /\\caption\{([^{}]*)\}/gi,
        function (_, caption) {
            const cleanCaption =
                cleanLatexImageLabelText(
                    caption
                );

            if (!cleanCaption) {
                return "";
            }

            return `
                <div class="pm-latex-image-caption mathjax-diagnostic-ignore" style="text-align:center; color:#64748b; font-size:0.92rem; margin:0.25rem 0 1rem;">
                    <em>${escapeHtml(cleanCaption)}</em>
                </div>
            `;
        }
    );

    return output;
}


function makeLatexImagePlaceholder(
    filename,
    escapeHtml
) {
    const cleanFilename =
        cleanLatexImageLabelText(
            filename
        );

    const label =
        cleanFilename
            ? `Image placeholder: ${escapeHtml(cleanFilename)}`
            : "Image placeholder";

    return `
        <div class="pm-latex-image-placeholder mathjax-diagnostic-ignore" style="margin:1rem auto; padding:0.75rem; max-width:28rem; border:1px dashed #cbd5e1; border-radius:6px; background:#f8fafc; color:#64748b; text-align:center;">
            <em>[${label}]</em>
        </div>
    `;
}


function cleanLatexImageLabelText(value) {
    return String(value || "")
        // If the backend autolinker already linked text inside an
        // image filename/caption, keep only the visible linked text.
        .replace(
            /<a\b[^>]*>([\s\S]*?)<\/a>/gi,
            "$1"
        )

        // Remove any other accidental HTML tags from
        // placeholder labels.
        .replace(/<[^>]*>/g, "")

        // Basic entity cleanup.
        .replace(/&nbsp;/gi, " ")
        .replace(/&amp;/gi, "&")
        .replace(/&lt;/gi, "<")
        .replace(/&gt;/gi, ">")
        .replace(/&quot;/gi, '"')

        .replace(/\s+/g, " ")
        .trim();
}


function normalizeDiagramImageUrls(
    html,
    apiEndpoint
) {
    if (!html) return "";

    return html.replace(
        /src=(["'])\/api\/math\/diagrams\//gi,
        `src=$1${apiEndpoint}/math/diagrams/`
    );
}


window.MathCmsRenderImages = {
    normalizeLatexImageArtifacts,
    normalizeDiagramImageUrls
};

})();
