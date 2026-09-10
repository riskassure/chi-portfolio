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

function protectMboxInsideMath(value) {
    let output = String(value || "");
    const values = [];

    const protectBody = body => String(body || "").replace(
        /\\(?:mbox|text)\s*\{([^{}]*)\}/gi,
        (match, content) => {
            const value = String(content || "");

            // Structured environments inside \mbox need their own conversion.
            // Do not treat them as ordinary prose placeholders.
            if (/\\begin\s*\{(?:tabular|array|cases|matrix|pmatrix|bmatrix)\}/i.test(value)) {
                return match;
            }

            const index = values.length;
            values.push(value);

            return `PMMATHTEXTTOKEN${index}END`;
        }
    );

    output = output.replace(
        /\\\[([\s\S]*?)\\\]/g,
        (_, body) => `\\[${protectBody(body)}\\]`
    );

    output = output.replace(
        /\\\(([\s\S]*?)\\\)/g,
        (_, body) => `\\(${protectBody(body)}\\)`
    );

    output = output.replace(
        /\$\$([\s\S]*?)\$\$/g,
        (_, body) => `$$${protectBody(body)}$$`
    );

    output = output.replace(
        /(?<!\\)(?<!\$)\$(?!\$)([\s\S]*?)(?<!\\)\$(?!\$)/g,
        (_, body) => `$${protectBody(body)}$`
    );

    return {
        text: output,
        values
    };
}

function restoreMboxInsideMath(value, values) {
    const items = Array.isArray(values) ? values : [];

    return String(value || "").replace(
        /PMMATHTEXTTOKEN(\d+)END/g,
        (match, indexText) => {
            const index = Number(indexText);

            if (!Number.isInteger(index) || index < 0 || index >= items.length) {
                return match;
            }

            return `\\text{${items[index]}}`;
        }
    );
}

function restoreUnderlineHtmlInsideMath(value) {
    let output = String(value || "");

    const restoreUnderline = body =>
        String(body || "").replace(
            /<u>\s*([\s\S]*?)\s*<\/u>/gi,
            function (_, inner) {
                return `\\underline{${String(inner || "").trim()}}`;
            }
        );

    // \[ ... \]
    output = output.replace(
        /\\\[([\s\S]*?)\\\]/g,
        (_, body) => `\\[${restoreUnderline(body)}\\]`
    );

    // \( ... \)
    output = output.replace(
        /\\\(([\s\S]*?)\\\)/g,
        (_, body) => `\\(${restoreUnderline(body)}\\)`
    );

    // $$ ... $$
    output = output.replace(
        /\$\$([\s\S]*?)\$\$/g,
        (_, body) => `$$${restoreUnderline(body)}$$`
    );

    // single-dollar inline math
    output = output.replace(
        /(^|[^\\$])\$((?:\\.|[^$])*?)\$/g,
        (_, prefix, body) => `${prefix}$${restoreUnderline(body)}$`
    );

    return output;
}

    function normalizeFormattedProseMathDelimiters(clean) {
        // Backend prose conversion can produce invalid constructs such as:
        //
        //   $<strong>CyclGrp</strong>$
        //
        // HTML tags cannot safely remain inside MathJax dollar delimiters.
        // Preserve the intended HTML formatting, but remove the math delimiters.
        clean = clean.replace(
            /\$\s*<(strong|em|b|i)>([^<>$]*)<\/\1>\s*\$/gi,
            "<$1>$2</$1>"
        );

        // Remove a stray dollar sign left immediately after backend-rendered
        // prose formatting at the end of a sentence:
        //
        //   <em>module homomorphism</em>$.</p>
        //   ->
        //   <em>module homomorphism</em>.</p>
        clean = clean.replace(
            /(<\/(?:em|strong|b|i)>)\s*\$(?=\s*[.,;:!?]\s*(?:<\/p>|<\/li>|<\/div>|$))/gi,
            "$1"
        );

        return clean;
    }

    function normalizeLegacyFontSizes(clean) {
        // PlanetMath font-size macros.
        // Keep braced footnotesize content, but strip unbraced size switches safely.
        clean = clean.replace(
            /\\footnotesize\{([\s\S]*?)\}/gi,
            '<span class="pm-tex-footnotesize">$1</span>'
        );

        clean = clean.replace(/\\footnotesize\b/gi, "");
        clean = clean.replace(/\\scriptsize\b/gi, "");
        clean = clean.replace(/\\small\b/gi, "");
        clean = clean.replace(/\\normalsize\b/gi, "");
        clean = clean.replace(/\\large\b/gi, "");
        clean = clean.replace(/\\Large\b/g, "");
        clean = clean.replace(/\\LARGE\b/g, "");
        clean = clean.replace(/\\huge\b/gi, "");
        clean = clean.replace(/\\Huge\b/g, "");

        return clean;
    }

    function normalizeProseUnderline(clean) {
        // Text-level underline used in PlanetMath prose.
        clean = clean.replace(/\\underline\{([^{}]+)\}/gi, "<u>$1</u>");

        return clean;
    }

    function normalizeMathConjunctionSpacing(clean) {
        // Preserve visible spacing around prose conjunctions inside math.
        // Plain "and" is treated as math identifiers, so its surrounding
        // spaces disappear after MathJax typesetting.
        clean = clean.replace(
            /\\(?:mbox|textrm|text)\{\s*and\s*\}/gi,
            "\\;\\mathrm{and}\\;"
        );

        return clean;
    }

    function normalizeLegacyTextFormatting(clean) {
        clean = clean.replace(/\\emph\{([^}]+)\}/gi, "<em>$1</em>");
        clean = clean.replace(/\\textsl\{([^}]+)\}/gi, "<em>$1</em>");
        clean = clean.replace(/\\textbf\{([^}]+)\}/gi, "<strong>$1</strong>");

        return clean;
    }

window.MathCmsRenderMathText = {
    normalizeTextBoldInsideMath,
    normalizeTextItalicInsideMath,
    protectMboxInsideMath,
    restoreMboxInsideMath,
    restoreUnderlineHtmlInsideMath,
    normalizeFormattedProseMathDelimiters,
    normalizeLegacyFontSizes,
    normalizeProseUnderline,
    normalizeMathConjunctionSpacing,
    normalizeLegacyTextFormatting
};

})();
