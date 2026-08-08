(() => {

function normalizeTextBoldInsideMath(value) {
    let output = String(value || "");

    const normalizeBody = body => String(body || "")
        // AMS-style bold math symbols.
        .replace(
            /\\boldsymbol\s*\{([^{}]*)\}/gi,
            "\\mathbf{$1}"
        )

        // Original TeX bold symbols.
        .replace(
            /\\textbf\s*\{([^{}]*)\}/gi,
            "\\mathbf{$1}"
        )

        // Bold HTML already produced by backend rendered_tex/display_tex.
        // HTML cannot remain inside MathJax delimiters.
        .replace(
            /<(strong|b)\b[^>]*>([\s\S]*?)<\/\1>/gi,
            (_, tagName, content) =>
                `\\mathbf{${String(content || "").trim()}}`
        );

    output = output.replace(
        /\\\[([\s\S]*?)\\\]/g,
        (_, body) => `\\[${normalizeBody(body)}\\]`
    );

    output = output.replace(
        /\\\(([\s\S]*?)\\\)/g,
        (_, body) => `\\(${normalizeBody(body)}\\)`
    );

    output = output.replace(
        /\$\$([\s\S]*?)\$\$/g,
        (_, body) => `$$${normalizeBody(body)}$$`
    );

    output = output.replace(
        /(?<!\\)(?<!\$)\$(?!\$)([\s\S]*?)(?<!\\)\$(?!\$)/g,
        (_, body) => `$${normalizeBody(body)}$`
    );

    return output;
}


function normalizeTextItalicInsideMath(value) {
    let output = String(value || "");

    const normalizeChunk = (chunk) => {
        return String(chunk || "")
            // TeX italic text inside mathematics should remain TeX.
            .replace(
                /\\textit\s*\{([^{}]*)\}/gi,
                "\\mathit{$1}"
            )

            // Protect italic HTML that may already have been generated.
            .replace(
                /<(?:em|i)\b[^>]*>([\s\S]*?)<\/(?:em|i)>/gi,
                "\\mathit{$1}"
            );
    };

    // Display math: \[ ... \]
    output = output.replace(
        /\\\[[\s\S]*?\\\]/g,
        normalizeChunk
    );

    // Explicit inline math: \( ... \)
    output = output.replace(
        /\\\([\s\S]*?\\\)/g,
        normalizeChunk
    );

    // Display-dollar math: $$ ... $$
    output = output.replace(
        /\$\$[\s\S]*?\$\$/g,
        normalizeChunk
    );

    // Ordinary inline-dollar math.
    output = output.replace(
        /(^|[^$])\$([^$\n]*?)\$(?!\$)/g,
        (match, prefix, body) => {
            return `${prefix}$${normalizeChunk(body)}$`;
        }
    );

    // Math environments that may not have surrounding dollar delimiters.
    output = output.replace(
        /\\begin\{(eqnarray\*?|align\*?|alignat\*?|array|cases|matrix|pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix)\}([\s\S]*?)\\end\{\1\}/gi,
        (match, environmentName, body) => {
            return (
                `\\begin{${environmentName}}` +
                normalizeChunk(body) +
                `\\end{${environmentName}}`
            );
        }
    );

    return output;
}


window.MathCmsRenderMathText = {
    normalizeTextBoldInsideMath,
    normalizeTextItalicInsideMath
};

})();
