// frontend/math/math_render_helpers.js

(function () {
    const DEFAULT_API_ENDPOINT = "http://127.0.0.1:5000/api";

    window.MathCmsRender = {
        debugVersion: "rooted-tree-pstree-v1",
        getDisplayTex,
        prepareConceptHtml,
        cleanLaTeXEnvironments,
        normalizeDiagramImageUrls,
        renderXyMatrixDiagonalOverlays
    };

    function getDisplayTex(concept) {
        return (
            concept?.display_tex ||
            concept?.rendered_tex ||
            concept?.cleaned_tex ||
            "No textual mathematical content saved."
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

    function prepareConceptHtml(tex, options = {}) {
        const apiEndpoint =
            options.apiEndpoint ||
            window.MATH_CMS_API_ENDPOINT ||
            DEFAULT_API_ENDPOINT;

        let clean = tex || "";

        /*
        * Expand concept-local \newcommand definitions before the
        * ordinary rendering cleanup pipeline.
        */
        if (
            window.MathCmsLocalMacros &&
            typeof window.MathCmsLocalMacros.apply === "function"
        ) {
            clean = window.MathCmsLocalMacros.apply(
                clean,
                options.localMacroSource || "",
                options.context || {}
            );
        }

        clean = cleanLaTeXEnvironments(clean);
        clean = restoreUnderlineHtmlInsideMath(clean);
        clean = normalizeDiagramImageUrls(
            clean,
            apiEndpoint
        );

        return clean;
    }

    function protectMathForProseCleanup(value) {
        let output = String(value || "");
        const blocks = [];

        const protectBlock = block => {
            const index = blocks.length;
            blocks.push(block);
            return `PMMATHPROSEBLOCK${index}END`;
        };

        // Protect display forms before inline forms.
        output = output.replace(
            /\\\[[\s\S]*?\\\]/g,
            protectBlock
        );

        output = output.replace(
            /\$\$[\s\S]*?\$\$/g,
            protectBlock
        );

        output = output.replace(
            /\\\([\s\S]*?\\\)/g,
            protectBlock
        );

        // Protect ordinary single-dollar inline math.
        output = output.replace(
            /(^|[^\\$])\$((?:\\.|[^$])*?)\$/g,
            (match, prefix, body) => {
                return `${prefix}${protectBlock(`$${body}$`)}`;
            }
        );

        return {
            text: output,
            blocks
        };
    }

    function restoreMathAfterProseCleanup(value, blocks) {
        const items = Array.isArray(blocks) ? blocks : [];
        let output = String(value || "");

        /*
        * A protected outer math block can contain placeholders created earlier
        * for inner MathJax expressions, particularly in generated xymatrix HTML.
        * Restore repeatedly until no additional placeholders are exposed.
        */
        for (
            let pass = 0;
            pass <= items.length;
            pass += 1
        ) {
            const nextOutput = output.replace(
                /PMMATHPROSEBLOCK(\d+)END/g,
                (match, indexText) => {
                    const index = Number(indexText);

                    if (
                        !Number.isInteger(index)
                        || index < 0
                        || index >= items.length
                    ) {
                        return match;
                    }

                    return items[index];
                }
            );

            if (nextOutput === output) {
                break;
            }

            output = nextOutput;
        }

        return output;
    }

    function formatLegacyFontGroup(command, content) {
        const cleanContent =
            String(content || "").trim();

        if (!cleanContent) {
            return "";
        }

        switch (String(command || "").toLowerCase()) {
            case "em":
            case "it":
                return `<em>${cleanContent}</em>`;

            case "bf":
                return `<strong>${cleanContent}</strong>`;

            case "rm":
            case "sc":
            default:
                return cleanContent;
        }
    }

    function normalizeProseLayoutMacros(tex) {
        if (!tex) return "";

        let output = String(tex || "");

        // Preserve meaningful legend colors while removing raw
        // \textcolor commands and autolinks around color names.
        output = normalizeTextColorMacros(output);

        // Convert LaTeX \url{...} commands into safe external links.
        output = normalizeUrlMacros(output);

        /*
         * Legacy font commands may already be wrapped by the backend
         * autolinker:
         *
         *   {<span class="math-no-autolink">\rm</span>
         *      (Tychonoff's Theorem)}
         */
        output = output.replace(
            /\{\s*<span\b[^>]*class=["'][^"']*\bmath-no-autolink\b[^"']*["'][^>]*>\s*\\(rm|em|it|bf|sc)\s*<\/span>\s*((?:[^{}]|\{[^{}]*\})*)\}/gi,
            function (_, command, content) {
                return formatLegacyFontGroup(
                    command,
                    content
                );
            }
        );

        /*
         * Legacy font commands sometimes occur inside a PlanetMath escape:
         *
         *   {\PMlinkescapetext{\rm} (Tychonoff's Theorem)}
         *
         * Consume the entire construction before the generic escape rule
         * turns it into a visible {\rm ...} fragment.
         */
        output = output.replace(
            /\{\s*\\PMlinkescapetext\{\s*\\(?:bf|em|it|rm|sc)\s*\}\s*([^{}]*)\}/gi,
            "$1"
        );

        // PlanetMath link-ish macros that should not leak visibly.
        output = output.replace(/\\PMlinkescapetext\{([^{}]*)\}/gi, "$1");
        output = output.replace(/\\PMlinkname\{([^{}]*)\}\{[^{}]*\}/gi, "$1");
        output = output.replace(/\\PMlinkid\{([^{}]*)\}\{[^{}]*\}/gi, "$1");
        output = output.replace(/\\PMlinkID\{([^{}]*)\}\{[^{}]*\}/g, "$1");

        // Equation/reference commands. We do not currently resolve these to real anchors,
        // but we should not leak raw LaTeX commands into prose.
        output = output.replace(/\\label\{[^{}]*\}/gi, "");
        output = output.replace(/\\eqref\{([^{}]*)\}/gi, function(_, label) {
            const cleanLabel = String(label || "")
                .replace(/\s+/g, " ")
                .trim()
                .replace(/\s*-\s*/g, "-");

            return cleanLabel ? `(${cleanLabel})` : "";
        });

        output = output.replace(/\\ref\{([^{}]*)\}/gi, function(_, label) {
            const cleanLabel = String(label || "")
                .replace(/\s+/g, " ")
                .trim()
                .replace(/\s*-\s*/g, "-");

            return cleanLabel ? cleanLabel : "";
        });

        // Normalize backend citation placeholders:
        //   [citation: Newman] -> [Newman]
        output = output.replace(
            /\[\s*citation\s*:\s*([^\]]+?)\s*\]/gi,
            function (_, citationKey) {
                const cleanKey = String(citationKey || "")
                    .replace(/\s+/g, " ")
                    .trim();

                return cleanKey ? `[${cleanKey}]` : "";
            }
        );

        // Handle any surviving raw \cite commands.
        output = output.replace(
            /\\cite\s*\{([^{}]+)\}/gi,
            function (_, citationKeys) {
                const cleanKeys = String(citationKeys || "")
                    .split(",")
                    .map(key => key.trim())
                    .filter(Boolean)
                    .join(", ");

                return cleanKeys ? `[${cleanKeys}]` : "";
            }
        );

        // TeX nonbreaking spaces in visible prose.
        // Avoid changing tildes inside generated HTML tags or attributes.
        output = output.replace(
            /~(?![^<]*>)/g,
            "\u00A0"
        );

        // Remove setup/control commands that have no useful page meaning.
        output = output.replace(/\\setcounter\{[^{}]*\}\{[^{}]*\}/gi, "");
        output = output.replace(/\\newtheorem\{[^{}]*\}(?:\[[^\]]*\])?\{[^{}]*\}/gi, "");

        // Legacy PlanetMath theorem headings:
        //
        //   \theorem{}
        //   \theorem{The Reflector Law}
        //
        // Keep the following theorem statement in place. The block-level span
        // separates the heading visually from the preceding introductory prose.
        output = output.replace(
            /\\theorem\s*\{([^{}]*)\}/gi,
            function (_, title) {
                const cleanTitle =
                    String(title || "")
                        .replace(/\s+/g, " ")
                        .trim();

                const headingText = cleanTitle
                    ? `Theorem (${cleanTitle}).`
                    : "Theorem.";

                return `
                    <span
                        class="pm-legacy-theorem-heading"
                        style="
                            display:block;
                            margin:1rem 0 0.3rem;
                        "
                    >
                        <strong>${headingText}</strong>
                    </span>
                `;
            }
        );

        // Legacy PlanetMath proof marker:
        //
        //   \proof
        //
        // The proof contents remain in their existing paragraphs and blocks.
        output = output.replace(
            /\\proof\b/gi,
            `
                <span
                    class="pm-legacy-proof-heading"
                    style="
                        display:block;
                        margin:0.75rem 0 0.3rem;
                    "
                >
                    <em>Proof.</em>
                </span>
            `
        );

        // Remove document preamble commands that have no page meaning.
        output = output.replace(
            /\\documentclass(?:\[[^\]]*\])?\s*\{[^{}]*\}/gi,
            ""
        );

        output = output.replace(
            /\\usepackage(?:\[[^\]]*\])?\s*\{[^{}]*\}/gi,
            ""
        );

        output = output.replace(
            /\\pagestyle\s*\{[^{}]*\}/gi,
            ""
        );

        output = output.replace(/\\clearpage\b/gi, "");
        output = output.replace(/\\newpage\b/gi, "");
        output = output.replace(/\\pagebreak\b(?:\[[^\]]*\])?/gi, "");
        output = output.replace(/\\columnbreak\b/gi, "\n\n");

        // Paragraph / vertical layout commands.
        output = output.replace(/\\par\b/gi, "\n\n");
        output = output.replace(/\\(?:smallskip|medskip|bigskip)\b/gi, "\n\n");
        output = output.replace(/\\vspace\*?\s*\{[^{}]*\}/gi, "\n\n");

        // Remove leftover forced line-break slashes at the end of prose.
        output = output.replace(
            /\\+\s*(?=<\/p>|\r?\n|$)/gi,
            ""
        );

        // Horizontal layout commands.
        output = output.replace(/\\hspace\*?\s*\{[^{}]*\}/gi, " ");
        output = output.replace(/\\hfil\b/gi, " ");
        output = output.replace(/\\hfill\b/gi, " ");
        output = output.replace(/\\qquad\b/gi, " ");
        output = output.replace(/\\quad\b/gi, " ");

        // Old skip commands used around picture arrows.
        output = output.replace(/\\hskip\s+[^\s{}]+/gi, " ");

        // Old centered caption macro.
        output = output.replace(
            /\\centerline\s*\{([\s\S]*?)\}/gi,
            '<div class="math-center">$1</div>'
        );

        // Common old math dots variant.
        output = output.replace(/\\hdots\b/g, "\\dots");

        // Preserve the contents of legacy raisebox commands while discarding
        // their print-layout positioning.
        output = output.replace(
            /\\raisebox\s*\{[^{}]*\}\s*\{([^{}]*)\}/gi,
            "$1"
        );

        // TeX control space:
        //   Adv.\ Math. -> Adv. Math.
        output = output.replace(/\\(?=[ \t])/g, "");

        // PlanetMath prose dash macros.
        output = output.replace(/\s*\\(?:Ldash|Dash)\b\s*/g, " — ");

        // TeX sentence-spacing marker has no visible HTML equivalent.
        output = output.replace(/\\@/g, "");

        // Escaped percent signs outside protected MathJax expressions are
        // ordinary prose characters and should not display their backslash.
        output = output.replace(/\\%/g, "%");

        // TeX ellipsis used outside math.
        output = output.replace(/\\dots\b/g, "…");

        // Standard LaTeX logo command used in prose.
        output = output.replace(/\\LaTeX\b\s*\{\}/g, "LaTeX");
        output = output.replace(/\\LaTeX\b/g, "LaTeX");

        // End-of-proof marker used in prose.
        output = output.replace(/\\qed\b/gi, "∎");

        // Paired TeX prose quotation marks:
        //   ``quoted text'' -> “quoted text”
        output = output.replace(
            /``([^<>]*?)''/g,
            "“$1”"
        );

        // Some legacy PlanetMath prose starts a quotation with TeX
        // backticks but ends it with an ordinary double quote:
        //
        //   ``quoted text"
        //
        // Allow generated HTML inside the quotation, but do not cross
        // a paragraph boundary or consume another opening quote.
        output = output.replace(
            /``((?:(?!``|<\/p>)[\s\S])*?)"/g,
            "“$1”"
        );

        // Remove legacy PlanetMath canonical-name metadata attached to
        // formatted prose:
        //   \emph{...}{EpsilonTransitions} -> \emph{...}
        output = output.replace(
            /\\emph\s*\{([^{}]*)\}\s*\{[A-Za-z][A-Za-z0-9_-]*\}/g,
            "\\emph{$1}"
        );

        // Also handle the backend-rendered HTML form:
        //   <em>...</em>{EpsilonTransitions} -> <em>...</em>
        output = output.replace(
            /(<em\b[^>]*>[\s\S]*?<\/em>)\s*\{[A-Za-z][A-Za-z0-9_-]*\}/gi,
            "$1"
        );

        // Common text wrappers. Keep contents, drop LaTeX command.
        output = unwrapSimpleTextCommand(output, "mbox");
        output = unwrapSimpleTextCommand(output, "text");
        output = unwrapSimpleTextCommand(output, "textrm");
        output = unwrapSimpleTextCommand(output, "mathrm");
        output = unwrapSimpleTextCommand(output, "textnormal");
        output = unwrapSimpleTextCommand(output, "textsc");
        output = unwrapSimpleTextCommand(output, "textbf");
        output = unwrapSimpleTextCommand(output, "textit");
        output = unwrapSimpleTextCommand(output, "emph");

        // Common text accent / special-letter macros seen in references.
        output = normalizeCommonTextAccentMacros(output);

        // Some old-style font groups contain accent macros with braces, so run this
        // again after accent normalization.
        output = output.replace(
            /\{\s*\\(bf|em|it|rm|sc)\b\s*((?:[^{}]|\{[^{}]*\})*)\}/gi,
            function (_, command, content) {
                return formatLegacyFontGroup(
                    command,
                    content
                );
            }
        );
        output = output.replace(/\{\\em\s*\{([^{}]*)\}\}/gi, "$1");

        // Light cleanup around spaces introduced by removed layout commands.
        output = output.replace(/[ \t]{2,}/g, " ");

        // Light cleanup around spaces introduced by removed layout commands.
        output = output.replace(/[ \t]{2,}/g, " ");
        output = output.replace(/\n{3,}/g, "\n\n");

        return output;
    }

    function normalizeHtmlSensitiveMathCharacters(value) {
        let output = String(value || "");

        const normalizeMathBody = body => String(body || "")
            .replace(/</g, "\\lt ")
            .replace(/>/g, "\\gt ");

        // Display math: \[ ... \]
        output = output.replace(
            /\\\[([\s\S]*?)\\\]/g,
            (_, body) => `\\[${normalizeMathBody(body)}\\]`
        );

        // Inline math: \( ... \)
        output = output.replace(
            /\\\(([\s\S]*?)\\\)/g,
            (_, body) => `\\(${normalizeMathBody(body)}\\)`
        );

        // Display dollar math. This must run before the inline-dollar rule.
        output = output.replace(
            /\$\$([\s\S]*?)\$\$/g,
            (_, body) =>
                `$$${normalizeMathBody(body)}$$`
        );

        // Legacy inline dollar math. Display dollars have already been normalized.
        output = output.replace(
            /(^|[^\\$])\$((?:\\.|[^$])*?)\$/g,
            (_, prefix, body) =>
                `${prefix}$${normalizeMathBody(body)}$`
        );

        return output;
    }

    function unwrapSimpleTextCommand(text, commandName) {
        const pattern = new RegExp("\\\\" + commandName + "\\s*\\{([^{}]*)\\}", "gi");

        return String(text || "").replace(pattern, function(_, content) {
            return String(content || "").trim();
        });
    }

    function normalizeCommonTextAccentMacros(tex) {
        let output = String(tex || "");

        // Special case caused by \text{\L}ukasiewicz becoming \Lukasiewicz
        // after text-wrapper cleanup.
        output = output.replace(/\\Lukasiewicz/g, "Łukasiewicz");

        // Polish / Scandinavian / German / French common prose letters.
        output = output.replace(/\\L\b/g, "Ł");
        output = output.replace(/\\l\b/g, "ł");
        output = output.replace(/\\aa\s*\{\}/gi, "å");
        output = output.replace(/\\AA\s*\{\}/g, "Å");
        output = output.replace(/\\o\b/g, "ø");
        output = output.replace(/\\O\b/g, "Ø");
        output = output.replace(/\\ae\b/g, "æ");
        output = output.replace(/\\AE\b/g, "Æ");
        output = output.replace(/\\oe\b/g, "œ");
        output = output.replace(/\\OE\b/g, "Œ");
        output = output.replace(/\\ss\b/g, "ß");

        // Text prime used in transliterated names.
        output = output.replace(/\\cprime\b/g, "′");

        // A few accent forms that appear in bibliography prose.
        output = output.replace(/\\"a/g, "ä");
        output = output.replace(/\\"o/g, "ö");
        output = output.replace(/\\"u/g, "ü");
        output = output.replace(/\\"A/g, "Ä");
        output = output.replace(/\\"O/g, "Ö");
        output = output.replace(/\\"U/g, "Ü");

        output = output.replace(/\\'e/g, "é");
        output = output.replace(/\\'a/g, "á");
        output = output.replace(/\\'i/g, "í");
        output = output.replace(/\\'o/g, "ó");
        output = output.replace(/\\'u/g, "ú");

        output = output.replace(/\\`e/g, "è");
        output = output.replace(/\\`a/g, "à");
        output = output.replace(/\\`i/g, "ì");
        output = output.replace(/\\`o/g, "ò");
        output = output.replace(/\\`u/g, "ù");

        output = output.replace(/\\H\{o\}/g, "ő");
        output = output.replace(/\\H\{O\}/g, "Ő");

        output = output.replace(/\\v\{c\}/g, "č");
        output = output.replace(/\\v\{C\}/g, "Č");
        output = output.replace(/\\v\{s\}/g, "š");
        output = output.replace(/\\v\{S\}/g, "Š");
        output = output.replace(/\\v\{z\}/g, "ž");
        output = output.replace(/\\v\{Z\}/g, "Ž");

        // Braced umlaut forms used in bibliography prose.
        output = output.replace(/\\"\{a\}/g, "ä");
        output = output.replace(/\\"\{o\}/g, "ö");
        output = output.replace(/\\"\{u\}/g, "ü");
        output = output.replace(/\\"\{A\}/g, "Ä");
        output = output.replace(/\\"\{O\}/g, "Ö");
        output = output.replace(/\\"\{U\}/g, "Ü");

        // Unbraced forms.
        output = output.replace(/\\"a/g, "ä");
        output = output.replace(/\\"o/g, "ö");
        output = output.replace(/\\"u/g, "ü");
        output = output.replace(/\\"A/g, "Ä");
        output = output.replace(/\\"O/g, "Ö");
        output = output.replace(/\\"U/g, "Ü");

        // TeX circumflex accents used in prose and bibliography text:
        //   C\^{o}nes -> Cônes
        const circumflexCharacters = {
            A: "Â",
            C: "Ĉ",
            E: "Ê",
            I: "Î",
            O: "Ô",
            U: "Û",
            a: "â",
            c: "ĉ",
            e: "ê",
            i: "î",
            o: "ô",
            u: "û"
        };

        output = output.replace(
            /\\\^\s*\{([ACEIOUaceiou])\}/g,
            function (_, letter) {
                return circumflexCharacters[letter] || letter;
            }
        );

        // Also support the unbraced TeX form: \^o
        output = output.replace(
            /\\\^\s*([ACEIOUaceiou])/g,
            function (_, letter) {
                return circumflexCharacters[letter] || letter;
            }
        );

        return output;
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

            // Decode matrix/alignment separators that were HTML-escaped by the
            // backend renderer before reaching the frontend parser.
            .replace(/&amp;/gi, "&")

            // Common HTML whitespace artifact.
            .replace(/&nbsp;/gi, " ");
    }

    function normalizeStructuredMathHtmlArtifacts(value) {
        let output = String(value || "");

        const normalizeBody = body => String(body || "")
            // Paragraph breaks inside cases/arrays represent TeX rows.
            .replace(
                /<br\s*\/?>\s*<\/p>\s*<p[^>]*>/gi,
                "\\\\"
            )
            .replace(
                /<\/p>\s*<p[^>]*>/gi,
                "\\\\"
            )
            .replace(
                /<br\s*\/?>/gi,
                "\\\\"
            )

            // Remove any remaining paragraph wrappers.
            .replace(/<\/?p[^>]*>/gi, "")

            // A cases/array environment is already math. Nested dollar pairs,
            // often inherited from \mbox{if $x>0$}, must not remain inside it.
            .replace(/\$([^$]+)\$/g, "$1");

        output = output.replace(
            /\\begin\s*\{cases\}([\s\S]*?)\\end\s*\{cases\}/gi,
            (_, body) =>
                `\\begin{cases}${normalizeBody(body)}\\end{cases}`
        );

        output = output.replace(
            /\\begin\s*\{array\}\s*\{([^{}]*)\}([\s\S]*?)\\end\s*\{array\}/gi,
            (_, columnSpec, body) =>
                `\\begin{array}{${columnSpec}}${normalizeBody(body)}\\end{array}`
        );

        output = output.replace(
            /\\begin\s*\{(matrix|pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|smallmatrix)\}([\s\S]*?)\\end\s*\{\1\}/gi,
            (_, envName, body) =>
                `\\begin{${envName}}${normalizeBody(body)}\\end{${envName}}`
        );

        return output;
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

            const braceStart = findXyMatrixBodyStart(
                source,
                matrixIndex + "\\xymatrix".length
            );

            if (braceStart === -1) {
                result += source.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            const braceEnd = findMatchingBrace(source, braceStart);

            if (braceEnd === -1) {
                result += source.slice(cursor);
                break;
            }

            const body = source.slice(braceStart + 1, braceEnd);

            const normalizedBody = normalizeEqnarrayHtmlArtifacts(body);

            result += source.slice(cursor, braceStart + 1);
            result += normalizedBody;
            result += "}";

            cursor = braceEnd + 1;
        }

        return result;
    }

    function normalizeLegacyOverFractions(value) {
        let output = String(value || "");

        // Common PlanetMath form:
        //   {n \over 2^k}
        //   {a+b \over c}
        //
        // Intentionally limited to simple, non-nested brace groups.
        output = output.replace(
            /\{\s*([^{}]+?)\s+\\over\s+([^{}]+?)\s*\}/g,
            (_, numerator, denominator) =>
                `\\frac{${numerator.trim()}}{${denominator.trim()}}`
        );

        return output;
    }

    function normalizeFootnoteMacros(value) {
        const source = String(value || "");

        if (!/\\footnote\s*\{/.test(source)) {
            return source;
        }

        const footnotePattern = /\\footnote\s*\{/g;

        let output = "";
        let cursor = 0;
        let match;

        while (
            (match = footnotePattern.exec(source)) !== null
        ) {
            const commandStart = match.index;
            const contentStart = footnotePattern.lastIndex;

            let depth = 1;
            let index = contentStart;

            while (index < source.length && depth > 0) {
                const character = source[index];
                const nextCharacter = source[index + 1];

                // Do not treat escaped braces as grouping braces.
                if (
                    character === "\\"
                    && (
                        nextCharacter === "{"
                        || nextCharacter === "}"
                    )
                ) {
                    index += 2;
                    continue;
                }

                if (character === "{") {
                    depth += 1;
                } else if (character === "}") {
                    depth -= 1;
                }

                index += 1;
            }

            // Leave malformed source untouched.
            if (depth !== 0) {
                break;
            }

            const contentEnd = index - 1;

            let replacementStart = commandStart;
            let replacementEnd = index;

            /*
            * Also consume an optional wrapper:
            *
            *   {\footnote{...}}
            */
            let leftIndex = commandStart - 1;

            while (
                leftIndex >= cursor
                && /\s/.test(source[leftIndex])
            ) {
                leftIndex -= 1;
            }

            let rightIndex = index;

            while (
                rightIndex < source.length
                && /\s/.test(source[rightIndex])
            ) {
                rightIndex += 1;
            }

            if (
                source[leftIndex] === "{"
                && source[rightIndex] === "}"
            ) {
                replacementStart = leftIndex;
                replacementEnd = rightIndex + 1;
            }

            const content = source
                .slice(contentStart, contentEnd)
                .trim();

            output += source.slice(
                cursor,
                replacementStart
            );

            if (content) {
                output += `
                    <span class="pm-footnote tex2jax_process">
                        <span class="pm-footnote-label">Note.</span>
                        ${content}
                    </span>
                `;
            }

            cursor = replacementEnd;
            footnotePattern.lastIndex = replacementEnd;
        }

        output += source.slice(cursor);

        return output;
    }

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
        const normalizedBody = normalizeEqnarrayHtmlArtifacts(body);

        const rows = splitAlignRows(normalizedBody)
            .map(splitEqnarrayCells)
            .filter(cells => cells.some(cell => cell.trim().length > 0));

        if (rows.length === 0) {
            return "";
        }

        const maxColumns = Math.max(...rows.map(cells => cells.length));

        const htmlRows = rows.map(cells => {
            const paddedCells = padEqnarrayCells(cells, maxColumns);

            const htmlCells = paddedCells.map((cell, index) => {
                const align = getAlignColumnAlign(index);
                const cleanCell = normalizeAlignCell(cell);

                if (!cleanCell) {
                    return `<td style="padding:0.12rem 0.28rem; text-align:${align};"></td>`;
                }

                const renderedCell = containsSimpleMatrixEnvironment(cleanCell)
                    ? buildMatrixMathSequenceHtml(cleanCell, false)
                    : `\\(${escapeHtmlForMathCell(cleanCell)}\\)`;

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

    function splitProofLeadParagraphs(value) {
        const source = String(value || "");

        if (
            !/<strong\b/i.test(source)
            && !source.includes("∎")
        ) {
            return source;
        }

        const template = document.createElement("template");
        template.innerHTML = source;

        const proofLeadPattern =
            /^(?:Statement|Existential proof|Constructive proof):$/i;

        function hasMeaningfulContentBefore(element) {
            let sibling = element.previousSibling;

            while (sibling) {
                if (
                    sibling.nodeType === Node.TEXT_NODE
                    && String(sibling.nodeValue || "").trim()
                ) {
                    return true;
                }

                if (
                    sibling.nodeType === Node.ELEMENT_NODE
                    && String(sibling.textContent || "").trim()
                ) {
                    return true;
                }

                sibling = sibling.previousSibling;
            }

            return false;
        }

        /*
        * Move startNode and all following siblings from paragraph into
        * a newly inserted paragraph.
        */
        function splitParagraphAtNode(paragraph, startNode) {
            const newParagraph =
                document.createElement("p");

            let node = startNode;

            while (node) {
                const nextNode = node.nextSibling;
                newParagraph.appendChild(node);
                node = nextNode;
            }

            paragraph.after(newParagraph);

            return newParagraph;
        }

        /*
        * Split flattened proof lead-ins:
        *
        *   preceding prose. <strong>Statement:</strong> ...
        *
        * becomes two paragraphs.
        */
        template.content
            .querySelectorAll("p")
            .forEach(originalParagraph => {
                let paragraph = originalParagraph;

                while (paragraph) {
                    const proofLead = Array.from(
                        paragraph.children
                    ).find(element =>
                        element.tagName === "STRONG"
                        && proofLeadPattern.test(
                            String(element.textContent || "").trim()
                        )
                        && hasMeaningfulContentBefore(element)
                    );

                    if (!proofLead) {
                        break;
                    }

                    paragraph = splitParagraphAtNode(
                        paragraph,
                        proofLead
                    );
                }
            });

        /*
        * Split prose that follows a QED marker:
        *
        *   ... proof text. ∎ Notice, ...
        *
        * becomes:
        *
        *   ... proof text. ∎
        *   Notice, ...
        */
        template.content
            .querySelectorAll("p")
            .forEach(originalParagraph => {
                let paragraph = originalParagraph;

                while (paragraph) {
                    const markerNode = Array.from(
                        paragraph.childNodes
                    ).find(node => {
                        if (node.nodeType !== Node.TEXT_NODE) {
                            return false;
                        }

                        const text =
                            String(node.nodeValue || "");

                        const markerIndex =
                            text.indexOf("∎");

                        if (markerIndex < 0) {
                            return false;
                        }

                        const trailingText =
                            text.slice(markerIndex + 1).trim();

                        return (
                            Boolean(trailingText)
                            || Boolean(node.nextSibling)
                        );
                    });

                    if (!markerNode) {
                        break;
                    }

                    const markerText =
                        String(markerNode.nodeValue || "");

                    const markerIndex =
                        markerText.indexOf("∎");

                    const proofEnding =
                        markerText
                            .slice(0, markerIndex + 1)
                            .replace(/\s+$/g, "");

                    const followingText =
                        markerText
                            .slice(markerIndex + 1)
                            .replace(/^\s+/g, "");

                    markerNode.nodeValue = proofEnding;

                    const newParagraph =
                        document.createElement("p");

                    if (followingText) {
                        newParagraph.appendChild(
                            document.createTextNode(followingText)
                        );
                    }

                    let sibling = markerNode.nextSibling;

                    while (sibling) {
                        const nextSibling = sibling.nextSibling;
                        newParagraph.appendChild(sibling);
                        sibling = nextSibling;
                    }

                    if (
                        String(newParagraph.textContent || "").trim()
                        || newParagraph.children.length
                    ) {
                        paragraph.after(newParagraph);
                        paragraph = newParagraph;
                    } else {
                        break;
                    }
                }
            });

        return template.innerHTML;
    }

    function splitAlignRows(body) {
        const normalized = String(body || "").trim();

        if (!normalized) {
            return [];
        }

        const slashRows = splitEqnarrayRows(normalized);

        if (slashRows.length > 1) {
            return slashRows;
        }

        // If there is only one top-level alignment marker, the physical
        // line breaks are just source formatting for one long equation.
        if (countTopLevelAlignmentMarkers(normalized) <= 1) {
            return slashRows;
        }

        // Some PlanetMath align blocks lost explicit \\ row separators and
        // retain only physical line breaks. Split those line breaks only at
        // top level; line breaks inside matrices, arrays, cases, etc. belong
        // to the nested environment and must remain intact.
        const newlineRows = splitTopLevelNewlineRows(normalized);

        if (newlineRows.length > 1) {
            return newlineRows;
        }

        return slashRows;
    }

    function countTopLevelAlignmentMarkers(body) {
        const text = String(body || "");
        let nestedDepth = 0;
        let count = 0;

        for (let i = 0; i < text.length; i += 1) {
            const env = readLatexEnvironmentAt(text, i);

            if (env && isNestedLatexEnvironment(env.name)) {
                if (env.type === "begin") {
                    nestedDepth += 1;
                } else {
                    nestedDepth = Math.max(0, nestedDepth - 1);
                }

                i = env.endIndex - 1;
                continue;
            }

            if (
                nestedDepth === 0 &&
                text[i] === "&" &&
                text[i - 1] !== "\\"
            ) {
                count += 1;
            }
        }

        return count;
    }

    function splitTopLevelNewlineRows(body) {
        const text = String(body || "");
        const rows = [];

        let start = 0;
        let nestedDepth = 0;

        for (let i = 0; i < text.length; i += 1) {
            const env = readLatexEnvironmentAt(text, i);

            if (env && isNestedLatexEnvironment(env.name)) {
                if (env.type === "begin") {
                    nestedDepth += 1;
                } else {
                    nestedDepth = Math.max(0, nestedDepth - 1);
                }

                i = env.endIndex - 1;
                continue;
            }

            if (
                nestedDepth === 0 &&
                (text[i] === "\n" || text[i] === "\r")
            ) {
                const row = text.slice(start, i).trim();

                if (row) {
                    rows.push(row);
                }

                if (text[i] === "\r" && text[i + 1] === "\n") {
                    i += 1;
                }

                while (
                    i + 1 < text.length &&
                    (text[i + 1] === "\n" || text[i + 1] === "\r")
                ) {
                    i += 1;
                }

                start = i + 1;
            }
        }

        const finalRow = text.slice(start).trim();

        if (finalRow) {
            rows.push(finalRow);
        }

        return rows;
    }

    function getAlignColumnAlign(index) {
        // align/alignat cells naturally alternate:
        // left expression & aligned relation/right expression
        if (index % 2 === 0) {
            return "right";
        }

        return "left";
    }

    function normalizeAlignCell(cell) {
        return normalizeEqnarrayHtmlArtifacts(cell)
            .replace(/\s+/g, " ")
            .trim();
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
        const normalizedBody = normalizeEqnarrayHtmlArtifacts(body)
            .replace(/\\cr\b/gi, "\\\\");

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

                return `<td style="
                    padding:0.15rem 0.35rem;
                    text-align:${align};
                    white-space:nowrap;
                ">\\(${escapeHtmlForMathCell(cleanCell)}\\)</td>`;
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

    function splitEqnarrayCells(row) {
        const text = String(row || "");
        const cells = [];
        let start = 0;
        let nestedDepth = 0;

        for (let i = 0; i < text.length; i++) {
            const env = readLatexEnvironmentAt(text, i);

            if (env && isNestedLatexEnvironment(env.name)) {
                if (env.type === "begin") {
                    nestedDepth += 1;
                } else {
                    nestedDepth = Math.max(0, nestedDepth - 1);
                }

                i = env.endIndex - 1;
                continue;
            }

            if (
                nestedDepth === 0 &&
                text[i] === "&" &&
                text[i - 1] !== "\\"
            ) {
                cells.push(text.slice(start, i).trim());
                start = i + 1;
            }
        }

        cells.push(text.slice(start).trim());

        return cells;
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
        const text = String(body || "");
        const rows = [];

        let start = 0;
        let nestedDepth = 0;
        let braceDepth = 0;

        for (
            let i = 0;
            i < text.length;
            i += 1
        ) {
            const env =
                readLatexEnvironmentAt(
                    text,
                    i
                );

            if (
                env
                && isNestedLatexEnvironment(
                    env.name
                )
            ) {
                if (env.type === "begin") {
                    nestedDepth += 1;
                } else {
                    nestedDepth =
                        Math.max(
                            0,
                            nestedDepth - 1
                        );
                }

                i =
                    env.endIndex - 1;

                continue;
            }

            /*
            * Escaped braces such as \{ and \} are TeX symbols,
            * not grouping braces.
            */
            if (text[i] === "\\") {
                if (
                    text[i + 1] === "{"
                    || text[i + 1] === "}"
                ) {
                    i += 1;
                    continue;
                }

            } else if (text[i] === "{") {
                braceDepth += 1;
                continue;

            } else if (text[i] === "}") {
                braceDepth =
                    Math.max(
                        0,
                        braceDepth - 1
                    );

                continue;
            }

            /*
            * Split only a genuine top-level eqnarray row.
            *
            * Do not split \\ inside grouped macro arguments such
            * as:
            *
            *   \substack{top \\ middle \\ bottom}
            */
            if (
                nestedDepth === 0
                && braceDepth === 0
                && text[i] === "\\"
                && text[i + 1] === "\\"
            ) {
                rows.push(
                    text
                        .slice(
                            start,
                            i
                        )
                        .trim()
                );

                i += 1;
                start = i + 1;
            }
        }

        rows.push(
            text
                .slice(start)
                .trim()
        );

        return rows.filter(
            row => row.length > 0
        );
    }

    function readLatexEnvironmentAt(text, index) {
        const source = String(text || "");
        const remainder = source.slice(index);

        const markerMatch = remainder.match(
            /^\\(begin|end)\s*\{\s*([^{}]+?)\s*\}/
        );

        if (!markerMatch) {
            return null;
        }

        return {
            type: markerMatch[1],
            name: markerMatch[2],
            endIndex: index + markerMatch[0].length
        };
    }

    function isNestedLatexEnvironment(name) {
        const normalized = String(name || "").replace(/\*$/, "");

        return [
            "array",
            "cases",
            "matrix",
            "pmatrix",
            "bmatrix",
            "Bmatrix",
            "vmatrix",
            "Vmatrix",
            "smallmatrix",
            "aligned",
            "alignedat",
            "split",
            "gathered",
            "subarray"
        ].includes(normalized);
    }

    function normalizeEqnarrayCell(cell) {
        return normalizeEqnarrayHtmlArtifacts(cell)
            .replace(/\s+/g, " ")

            // A malformed or partially normalized eqnarray row separator can
            // leave one trailing backslash in the final cell. If retained, it
            // combines with the generated closing \) delimiter and produces \\),
            // which MathJax cannot recognize as an inline-math closing delimiter.
            .replace(/\\+\s*$/, "")

            .trim();
    }

    function escapeHtmlForMathCell(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

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

    function convertUnderbracedXyMatrixToHtml(tex) {
        const source = String(tex || "");

        let result = "";
        let cursor = 0;

        while (cursor < source.length) {
            const underbraceIndex = source.indexOf("\\underbrace", cursor);

            if (underbraceIndex === -1) {
                result += source.slice(cursor);
                break;
            }

            const contentStart = findNextNonSpaceIndex(
                source,
                underbraceIndex + "\\underbrace".length
            );

            if (contentStart === -1 || source[contentStart] !== "{") {
                result += source.slice(cursor, underbraceIndex + "\\underbrace".length);
                cursor = underbraceIndex + "\\underbrace".length;
                continue;
            }

            const contentEnd = findMatchingBrace(source, contentStart);

            if (contentEnd === -1) {
                result += source.slice(cursor);
                break;
            }

            const content = source.slice(contentStart + 1, contentEnd).trim();

            if (!content.startsWith("\\xymatrix")) {
                result += source.slice(cursor, contentEnd + 1);
                cursor = contentEnd + 1;
                continue;
            }

            const subscriptMatch = source
                .slice(contentEnd + 1)
                .match(/^\s*_\s*\{/);

            if (!subscriptMatch) {
                result += source.slice(cursor, contentEnd + 1);
                cursor = contentEnd + 1;
                continue;
            }

            const labelStart =
                contentEnd + 1 +
                subscriptMatch[0].lastIndexOf("{");

            const labelEnd = findMatchingBrace(source, labelStart);

            if (labelEnd === -1) {
                result += source.slice(cursor);
                break;
            }

            const matrixStart = content.indexOf("\\xymatrix");
            const matrixBraceStart = findXyMatrixBodyStart(
                content,
                matrixStart + "\\xymatrix".length
            );

            const matrixBraceEnd =
                matrixBraceStart === -1
                    ? -1
                    : findMatchingBrace(content, matrixBraceStart);

            if (matrixBraceEnd === -1) {
                result += source.slice(cursor, labelEnd + 1);
                cursor = labelEnd + 1;
                continue;
            }

            const matrixBody = content.slice(
                matrixBraceStart + 1,
                matrixBraceEnd
            );

            const rawLabel = source.slice(labelStart + 1, labelEnd);

            const cleanLabel = rawLabel
                .replace(/\\displaystyle\s*/gi, "")
                .replace(/\\mbox\s*\{([^{}]*)\}/gi, "\\text{$1}")
                .trim();

            const html = `
                <figure class="pm-underbraced-xymatrix tex2jax_process" style="
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    width:max-content;
                    max-width:100%;
                    margin:1rem auto;
                ">
                    ${buildHtmlTableFromXyMatrixBody(matrixBody)}

                    <div aria-hidden="true" style="
                        width:100%;
                        height:0.55rem;
                        border-bottom:1.5px solid currentColor;
                        border-left:1.5px solid currentColor;
                        border-right:1.5px solid currentColor;
                        border-radius:0 0 45% 45%;
                        margin-top:-0.7rem;
                    "></div>

                    <figcaption style="margin-top:0.2rem;">
                        \\(${escapeHtmlForMathCell(cleanLabel)}\\)
                    </figcaption>
                </figure>
            `;

            let replaceStart = underbraceIndex;
            let replaceEnd = labelEnd + 1;

            const before = source.slice(0, underbraceIndex);

            // Support either \[ ... \] or $$ ... $$.
            const latexDisplayStartMatch = before.match(/\\\[\s*$/);
            const dollarDisplayStartMatch = before.match(/\$\$\s*$/);

            let displayWrapper = "";

            if (latexDisplayStartMatch) {
                replaceStart =
                    underbraceIndex - latexDisplayStartMatch[0].length;
                displayWrapper = "latex";
            } else if (dollarDisplayStartMatch) {
                replaceStart =
                    underbraceIndex - dollarDisplayStartMatch[0].length;
                displayWrapper = "dollar";
            }

            if (displayWrapper === "latex") {
                const displayEndMatch = source
                    .slice(replaceEnd)
                    .match(/^\s*\\\]/);

                if (displayEndMatch) {
                    replaceEnd += displayEndMatch[0].length;
                }
            } else if (displayWrapper === "dollar") {
                const displayEndMatch = source
                    .slice(replaceEnd)
                    .match(/^\s*\$\$/);

                if (displayEndMatch) {
                    replaceEnd += displayEndMatch[0].length;
                }
            }

            result += source.slice(cursor, replaceStart);
            result += html;

            cursor = replaceEnd;
        }

        return result;
    }

    function convertXyMatrixToHtml(tex) {
        if (!tex) return "";

        let result = "";
        let cursor = 0;

        while (cursor < tex.length) {
            const matrixIndex = tex.indexOf("\\xymatrix", cursor);

            if (matrixIndex === -1) {
                result += tex.slice(cursor);
                break;
            }

            const braceStart = findXyMatrixBodyStart(
                tex,
                matrixIndex + "\\xymatrix".length
            );

            if (braceStart === -1) {
                result += tex.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            const braceEnd = findMatchingBrace(tex, braceStart);

            if (braceEnd === -1) {
                result += tex.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            let replaceStart = matrixIndex;
            let replaceEnd = braceEnd + 1;

            const before = tex.slice(0, matrixIndex);
            const after = tex.slice(replaceEnd);

            const displayStartMatch =
                before.match(/\\\[\s*$/);

            const inlineStartMatch =
                displayStartMatch
                    ? null
                    : before.match(/\$([^$\r\n]*)$/);

            const inlineEndMatch =
                inlineStartMatch
                    ? after.match(/^\s*\$/)
                    : null;

            let leadingInlineMath = "";

            if (displayStartMatch) {
                replaceStart =
                    matrixIndex - displayStartMatch[0].length;

            } else if (
                inlineStartMatch
                && inlineEndMatch
            ) {
                replaceStart =
                    matrixIndex - inlineStartMatch[0].length;

                replaceEnd += inlineEndMatch[0].length;

                leadingInlineMath =
                    String(inlineStartMatch[1] || "").trim();
            }

            // A display xymatrix commonly ends with punctuation:
            //
            //   \xymatrix{...}.
            //   \xymatrix{...},
            //
            // Consume that punctuation together with the closing display delimiter,
            // then restore it outside the generated diagram HTML.
            const displayEndMatch = after.match(
                /^(\s*[.,;:]?)\s*\\\]/
            );

            let trailingDisplayPunctuation = "";

            if (displayEndMatch) {
                trailingDisplayPunctuation = displayEndMatch[1].trim();
                replaceEnd += displayEndMatch[0].length;
            }

            const body =
                tex.slice(braceStart + 1, braceEnd);

            const matrixHtml =
                buildHtmlTableFromXyMatrixBody(body);

            let html;

            if (leadingInlineMath) {
                /*
                * Source forms such as:
                *
                *   $P:\xymatrix{...}$
                *
                * place the label directly beside the diagram. Remove the matrix's
                * ordinary standalone margin and center the combined unit.
                */
                const compactMatrixHtml =
                    matrixHtml.replace(
                        "margin:1rem auto;",
                        "margin:0;"
                    );

                html = `
                    <div
                        class="pm-xymatrix-labeled-display tex2jax_process"
                        style="
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            gap:1.00rem;
                            margin:1rem 0;
                        "
                    >
                        <span style="white-space:nowrap;">
                            \\(${escapeHtmlForMathCell(leadingInlineMath)}\\)
                        </span>

                        ${compactMatrixHtml}
                    </div>

                    ${trailingDisplayPunctuation}
                `;

            } else {
                html =
                    matrixHtml +
                    trailingDisplayPunctuation;
            }

            result += tex.slice(cursor, replaceStart);
            result += html;

            cursor = replaceEnd;
        }

        return result;
    }

    function findXyMatrixBodyStart(text, startIndex) {
        let i = findNextNonSpaceIndex(text, startIndex);

        if (i === -1) {
            return -1;
        }

        // Ordinary case:
        // \xymatrix{...}
        if (text[i] === "{") {
            return i;
        }

        // Extended PlanetMath / Xy-pic option cases:
        // \xymatrix@C=1.5cm{...}
        // \xymatrix@R-=2pt{...}
        // \xymatrix@+=1.5cm{...}
        // \xymatrix@1{...}
        // \xymatrix @R=1pt @C=1.5cm {...}
        // \xymatrix @!=1pt {...}
        if (text[i] !== "@") {
            return -1;
        }

        const limit = Math.min(text.length, i + 180);

        while (i < limit) {
            while (i < limit && /\s/.test(text[i])) {
                i += 1;
            }

            if (i >= limit) {
                return -1;
            }

            if (text[i] === "{" && text[i - 1] !== "\\") {
                return i;
            }

            if (text[i] !== "@") {
                return -1;
            }

            // Consume one @ option token.
            // Examples:
            //   @C=1.5cm
            //   @R-=2pt
            //   @+=3pc
            //   @1
            //   @!
            //   @!=1pt
            //   @-2ex
            i += 1;

            while (i < limit) {
                if (text[i] === "{" && text[i - 1] !== "\\") {
                    return i;
                }

                if (/\s/.test(text[i]) || text[i] === "@") {
                    break;
                }

                i += 1;
            }
        }

        return -1;
    }

    function findNextNonSpaceIndex(text, startIndex) {
        for (let i = startIndex; i < text.length; i += 1) {
            if (!/\s/.test(text[i])) {
                return i;
            }
        }

        return -1;
    }

    function findMatchingBrace(text, openIndex) {
        const source = String(text || "");
        let depth = 0;

        for (let i = openIndex; i < source.length; i += 1) {
            const char = source[i];

            if (char !== "{" && char !== "}") {
                continue;
            }

            // A brace is escaped only when preceded by an odd number of
            // consecutive backslashes.
            //
            //   \{    escaped brace
            //   \\{   xymatrix row break followed by a real opening brace
            let backslashCount = 0;

            for (let j = i - 1; j >= 0 && source[j] === "\\"; j -= 1) {
                backslashCount += 1;
            }

            const isEscaped = backslashCount % 2 === 1;

            if (isEscaped) {
                continue;
            }

            if (char === "{") {
                depth += 1;
                continue;
            }

            depth -= 1;

            if (depth === 0) {
                return i;
            }
        }

        return -1;
    }

    function calculateXyMatrixArrowLayout(sourceRows) {
        let maxHorizontalLabelLength = 0;
        let maxVerticalLabelLength = 0;

        sourceRows.forEach(row => {
            row.forEach(cell => {
                (cell.arrows || []).forEach(arrow => {
                    const labelLength = estimateTexLabelLength(arrow.label || "");

                    if (arrow.direction === "r" || arrow.direction === "l") {
                        maxHorizontalLabelLength = Math.max(maxHorizontalLabelLength, labelLength);
                    }

                    if (arrow.direction === "u" || arrow.direction === "d") {
                        maxVerticalLabelLength = Math.max(maxVerticalLabelLength, labelLength);
                    }
                });
            });
        });

        return {
            // Same width for every horizontal arrow in this xymatrix.
            horizontalWidthEm: Math.max(3.6, 3.2 + maxHorizontalLabelLength * 0.56),

            // Same height for every vertical arrow in this xymatrix.
            verticalHeightEm: Math.max(2.7, 2.5 + maxVerticalLabelLength * 0.08),

            // Wider vertical arrow cell only when labels need room.
            verticalWidthEm: Math.max(2.4, 1.8 + maxVerticalLabelLength * 0.32)
        };
    }

    function estimateTexLabelLength(label) {
        return String(label || "")
            .replace(/\\[A-Za-z]+/g, "X")
            .replace(/[{}_^]/g, "")
            .trim()
            .length;
    }

    function getXyMatrixCellPadding(rowIndex, colIndex) {
        const isObjectRow = rowIndex % 2 === 0;
        const isObjectCol = colIndex % 2 === 0;

        if (isObjectRow && isObjectCol) {
            return "0.06rem 0.08rem";
        }

        if (isObjectRow && !isObjectCol) {
            return "0.02rem 0.02rem";
        }

        if (!isObjectRow && isObjectCol) {
            return "0.02rem 0.08rem";
        }

        return "0";
    }

    const XY_PLAIN_HORIZONTAL_LINE = "__PM_XY_PLAIN_HORIZONTAL_LINE__";

    const XY_VERTICAL_ROWSPAN_COVERED = "__PM_XY_VERTICAL_ROWSPAN_COVERED__";

    function recoverLostXyMatrixRowSeparators(value) {
        let source = String(value || "");

        /*
        * Some legacy xymatrix row separators arrive as one backslash
        * immediately before a physical newline:
        *
        *     ... \ar[d] \ 
        *     NextRow
        *
        * Recover that lone slash as the intended TeX row separator.
        */
        source = source.replace(
            /\\[ \t]*\r?\n(?=[ \t]*\S)/g,
            "\\\\\n"
        );

        /*
        * Other legacy rows lose both the second slash and the physical
        * newline, commonly before a new \mathcal object:
        *
        *     ... \ \mathcal{C}
        */
        source = source.replace(
            /\\\s+(?=\\mathcal\s*\{)/g,
            "\\\\ "
        );

        return source;
    }

    function buildHtmlTableFromXyMatrixBody(body) {
        const normalizedBody = recoverLostXyMatrixRowSeparators(
            normalizeEqnarrayHtmlArtifacts(body)
        );

        const sourceRows = splitEqnarrayRows(normalizedBody)
            .map(row => splitEqnarrayCells(row).map(parseXyMatrixCell))
            .filter(row => row.length > 0);

        const hasLegacyTwoCell = sourceRows
            .flat()
            .some(cell => cell.legacyTwoCell);

        if (sourceRows.length === 0) {
            return makeUnsupportedXyMatrixPlaceholder(body);
        }

        const sourceColumnCount = Math.max(...sourceRows.map(row => row.length));
        const arrowLayout = calculateXyMatrixArrowLayout(sourceRows);

        const hasNamedReferenceTwoCell = sourceRows
            .flat()
            .some(cell => Boolean(cell.twoCellLabel));

        /*
        * Preserve the existing cell-based renderer for specialized
        * two-cell diagrams. Ordinary xymatrix diagonals use the new
        * table-level SVG overlay.
        */
        const useDiagonalOverlay =
            !hasLegacyTwoCell
            && !hasNamedReferenceTwoCell;

        const diagonalArrows = [];

        if (useDiagonalOverlay) {
            sourceRows.forEach((row, sourceRow) => {
                row.forEach((cell, sourceCol) => {
                    (cell.arrows || []).forEach(arrow => {
                        if (!isXyDiagonalDirection(arrow.direction)) {
                            return;
                        }

                        const {
                            rowDelta,
                            colDelta
                        } = getXyArrowCoordinateDelta(
                            arrow.directionText
                        );

                        const targetRow =
                            sourceRow + rowDelta;

                        const targetCol =
                            sourceCol + colDelta;

                        if (
                            targetRow < 0
                            || targetRow >= sourceRows.length
                            || targetCol < 0
                            || targetCol >= sourceColumnCount
                        ) {
                            return;
                        }

                        diagonalArrows.push({
                            sourceRow,
                            sourceCol,
                            targetRow,
                            targetCol,

                            label:
                                arrow.label || "",

                            labelPosition:
                                arrow.labelPosition || "center",

                            style:
                                arrow.style || "->",

                            curveSide:
                                arrow.curveSide || "",

                            curveAmount:
                                arrow.curveAmount || ""
                        });
                    });
                });
            });
        }

        const diagonalDataAttribute =
            diagonalArrows.length > 0
                ? (
                    ` data-pm-diagonal-arrows="`
                    + encodeURIComponent(
                        JSON.stringify(diagonalArrows)
                    )
                    + `"`
                )
                : "";

        /*
        * Long diagonals such as [lld] and [rrd] cross empty inter-object
        * columns. Reserve those column gaps so the SVG overlays remain inside
        * the measured xymatrix width and neighboring object labels do not
        * collapse together.
        */
        const hasWideDiagonal =
            !useDiagonalOverlay
            && sourceRows
            .flat()
            .some(cell =>
                (cell.arrows || []).some(arrow =>
                    (
                        arrow.direction === "dl"
                        || arrow.direction === "dr"
                        || arrow.direction === "ul"
                        || arrow.direction === "ur"
                    )
                    && getXyArrowHorizontalSpan(arrow.directionText) > 1
                )
            );

        const wideDiagonalGapWidthEm = Math.max(
            arrowLayout.horizontalWidthEm || 3.6,
            4.2
        );

        const expandedRowCount = sourceRows.length * 2 - 1;
        const expandedColumnCount = sourceColumnCount * 2 - 1;

        const grid = Array.from({ length: expandedRowCount }, () => {
            return Array.from({ length: expandedColumnCount }, () => "");
        });

        sourceRows.forEach((row, rowIndex) => {
            row.forEach((cell, colIndex) => {
                const gridRow = rowIndex * 2;
                const gridCol = colIndex * 2;

                const selfLoops = cell.arrows.filter(
                    arrow => arrow.isSelfLoop
                );

                const objectHtml = renderXyObjectCell(
                    cell.objectTex,
                    cell.objectFrame,
                    selfLoops,
                    cell.overlayLabel
                );

                const hasVisibleObject =
                    String(cell.objectTex || "").trim() !== ""
                    || String(cell.overlayLabel || "").trim() !== ""
                    || Boolean(cell.objectFrame)
                    || selfLoops.length > 0;

                /*
                * Do not let an empty source cell overwrite part of a spanning arrow
                * that was placed earlier by an arrow from a preceding row.
                *
                * Example:
                *
                *   C\ar[dd]_h\\
                *   &A\\
                *   K
                *
                * The empty cell before A occupies the middle of the C-to-K arrow.
                */
                if (hasVisibleObject || !grid[gridRow][gridCol]) {
                    grid[gridRow][gridCol] = objectHtml;
                }

                if (
                    cell.twoCellLabel
                    && gridRow >= 1
                    && gridCol >= 2
                ) {
                    /*
                    * Named-reference two-cells such as:
                    *
                    *   \ar@{=>}"1";"2"_{\eta}
                    *
                    * occur in the lower-right source cell, while the two named
                    * diagonal arrows occupy the expanded cells above-left and
                    * above-right. Place the transformation in the center between them.
                    */
                    setGridCellIfInBounds(
                        grid,
                        gridRow - 1,
                        gridCol - 2,
                        renderNamedReferenceTwoCell(cell.twoCellLabel)
                    );
                }

                if (cell.legacyTwoCell) {
                    const middleArrow = cell.arrows.find(
                        arrow =>
                            !arrow.isSelfLoop
                            && arrow.direction === "r"
                            && arrow.span === 1
                    );

                    grid[gridRow][gridCol + 1] =
                        renderLegacyTwoCellArrowGroup(
                            cell.legacyTwoCell,
                            middleArrow?.label || "",
                            arrowLayout
                        );

                    cell.arrows
                        .filter(
                            arrow =>
                                arrow !== middleArrow
                                && !arrow.isSelfLoop
                        )
                        .forEach(arrow => {
                            applyXyArrowToGrid(
                                grid,
                                gridRow,
                                gridCol,
                                arrow,
                                arrowLayout
                            );
                        });
                } else {
                    cell.arrows
                        .filter(arrow =>
                            !arrow.isSelfLoop
                            && !(
                                useDiagonalOverlay
                                && isXyDiagonalDirection(
                                    arrow.direction
                                )
                            )
                        )
                        .forEach(arrow => {
                            applyXyArrowToGrid(
                                grid,
                                gridRow,
                                gridCol,
                                arrow,
                                arrowLayout
                            );
                        });
                }
            });
        });

        const htmlRows = grid.map((row, rowIndex) => {
            const htmlCells = [];
            let colIndex = 0;

            while (colIndex < row.length) {
                const cellHtml = row[colIndex];

                if (cellHtml === XY_VERTICAL_ROWSPAN_COVERED) {
                    colIndex += 1;
                    continue;
                }

                if (cellHtml === XY_PLAIN_HORIZONTAL_LINE) {
                    let runEnd = colIndex + 1;

                    while (
                        runEnd < row.length &&
                        row[runEnd] === XY_PLAIN_HORIZONTAL_LINE
                    ) {
                        runEnd += 1;
                    }

                    const colspan = runEnd - colIndex;

                    htmlCells.push(`
                        <td
                            colspan="${colspan}"
                            aria-hidden="true"
                            style="
                                padding:0;
                                height:1.2em;
                                vertical-align:middle;
                            "
                        >
                            <div style="
                                width:100%;
                                border-top:1.5px solid currentColor;
                            "></div>
                        </td>
                    `);

                    colIndex = runEnd;
                    continue;
                }

                const isVerticalSegmentCell =
                    /\bpm-xymatrix-vertical-segment\b/.test(cellHtml);

                const padding = isVerticalSegmentCell
                    ? "0"
                    : getXyMatrixCellPadding(rowIndex, colIndex);

                const cellLineHeight = isVerticalSegmentCell
                    ? "line-height:0;"
                    : "";

                const isArrowSpaceColumn =
                    colIndex % 2 === 1;

                const reservedGapStyle =
                    hasWideDiagonal && isArrowSpaceColumn
                        ? `
                            width:${wideDiagonalGapWidthEm}em;
                            min-width:${wideDiagonalGapWidthEm}em;
                        `
                        : "";

                const reservedGapHtml =
                    hasWideDiagonal
                    && isArrowSpaceColumn
                    && !cellHtml
                        ? `
                            <span
                                aria-hidden="true"
                                style="
                                    display:block;
                                    width:${wideDiagonalGapWidthEm}em;
                                    height:1px;
                                "
                            ></span>
                        `
                        : cellHtml;

                const verticalRowSpanMatch =
                    String(cellHtml || "").match(
                        /\bdata-pm-rowspan="(\d+)"/
                    );

                const verticalRowSpan =
                    verticalRowSpanMatch
                        ? Math.max(Number(verticalRowSpanMatch[1]) || 1, 1)
                        : 1;

                const rowSpanAttribute =
                    verticalRowSpan > 1
                        ? ` rowspan="${verticalRowSpan}"`
                        : "";
                
                const sourceCoordinateAttributes =
                    rowIndex % 2 === 0
                    && colIndex % 2 === 0
                        ? (
                            ` data-pm-source-row="${rowIndex / 2}"`
                            + ` data-pm-source-col="${colIndex / 2}"`
                        )
                        : "";

                htmlCells.push(`
                    <td${rowSpanAttribute}${sourceCoordinateAttributes} style="
                        padding:${padding};
                        text-align:center;
                        vertical-align:middle;
                        white-space:nowrap;
                        ${cellLineHeight}
                        ${reservedGapStyle}
                    ">
                        ${reservedGapHtml}
                    </td>
                `);

                colIndex += 1;
            }

            return `<tr>${htmlCells.join("")}</tr>`;
        }).join("");

        return `
            <table${diagonalDataAttribute}
                class="pm-xymatrix-table tex2jax_process${hasLegacyTwoCell ? " pm-xymatrix-two-cell-table" : ""}"
                style="
                    border-collapse:collapse;
                    ${hasLegacyTwoCell
                        ? "display:inline-table; vertical-align:middle; margin:1rem 0.45rem;"
                        : "margin:1rem auto;"
                    }
                "
            >
                ${htmlRows}
            </table>
        `;
    }

    let xyMatrixOverlayMarkerSerial = 0;

    function parseXyCurveAmountToPixels(value, element) {
        const text =
            String(value || "").trim();

        const fontSize =
            Number.parseFloat(
                window.getComputedStyle(element).fontSize
            ) || 16;

        if (!text) {
            return fontSize * 0.5;
        }

        const match = text.match(
            /^([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(ex|em|px|pt|pc|cm|mm|in)?$/i
        );

        if (!match) {
            return fontSize * 0.5;
        }

        const amount =
            Number(match[1]) || 0;

        const unit =
            String(match[2] || "ex").toLowerCase();

        switch (unit) {
            case "px":
                return amount;

            case "em":
                return amount * fontSize;

            case "pt":
                return amount * 96 / 72;

            case "pc":
                return amount * 16;

            case "cm":
                return amount * 96 / 2.54;

            case "mm":
                return amount * 96 / 25.4;

            case "in":
                return amount * 96;

            case "ex":
            default:
                return amount * fontSize * 0.5;
        }
    }

    function getXyRectangleBoundaryDistance(
        rect,
        unitX,
        unitY
    ) {
        const halfWidth =
            Math.max(rect.width / 2, 1);

        const halfHeight =
            Math.max(rect.height / 2, 1);

        const horizontalDistance =
            Math.abs(unitX) > 0.0001
                ? halfWidth / Math.abs(unitX)
                : Number.POSITIVE_INFINITY;

        const verticalDistance =
            Math.abs(unitY) > 0.0001
                ? halfHeight / Math.abs(unitY)
                : Number.POSITIVE_INFINITY;

        return Math.min(
            horizontalDistance,
            verticalDistance
        );
    }

    function createXyOverlayArrowMarker(
        svg,
        markerId
    ) {
        const namespace =
            "http://www.w3.org/2000/svg";

        let defs =
            svg.querySelector("defs");

        if (!defs) {
            defs =
                document.createElementNS(
                    namespace,
                    "defs"
                );

            svg.appendChild(defs);
        }

        const marker =
            document.createElementNS(
                namespace,
                "marker"
            );

        marker.setAttribute("id", markerId);
        marker.setAttribute("markerWidth", "5.5");
        marker.setAttribute("markerHeight", "5.5");
        marker.setAttribute("refX", "5.1");
        marker.setAttribute("refY", "2.75");
        marker.setAttribute("orient", "auto");
        marker.setAttribute(
            "markerUnits",
            "strokeWidth"
        );

        const markerPath =
            document.createElementNS(
                namespace,
                "path"
            );

        markerPath.setAttribute(
            "d",
            "M0,0 L5.5,2.75 L0,5.5 Z"
        );

        markerPath.setAttribute(
            "fill",
            "currentColor"
        );

        marker.appendChild(markerPath);
        defs.appendChild(marker);
    }

    function getXyOverlayObjectAnchor(cell) {
        if (!cell) {
            return null;
        }

        /*
        * After MathJax typesets a plain object, its mjx-container is
        * normally the direct child of the coordinate <td>.
        *
        * Framed objects and self-loop objects use our own wrappers.
        */
        return (
            cell.querySelector(
                ":scope > .pm-xymatrix-object-with-loops,"
                + ":scope > .pm-xymatrix-state,"
                + ":scope > mjx-container"
            )
            || cell
        );
    }

    function getXyOverlayCoordinateKey(row, col) {
        return `${Number(row)}:${Number(col)}`;
    }

    async function renderXyMatrixDiagonalOverlays(
        root = document
    ) {
        const scope =
            root && typeof root.querySelectorAll === "function"
                ? root
                : document;

        const tables = Array.from(
            scope.querySelectorAll(
                "table.pm-xymatrix-table"
                + "[data-pm-diagonal-arrows]"
            )
        );

        const labelsToTypeset = [];

        for (const table of tables) {
            let arrows = [];

            try {
                arrows = JSON.parse(
                    decodeURIComponent(
                        table.getAttribute(
                            "data-pm-diagonal-arrows"
                        ) || ""
                    )
                );
            } catch (error) {
                console.warn(
                    "Unable to decode xymatrix diagonal metadata:",
                    error
                );

                continue;
            }

            if (!Array.isArray(arrows) || arrows.length === 0) {
                continue;
            }

            /*
            * Identify an outer universal-property node such as Z.
            *
            * In the pullback and pushout diagrams, Z participates in three
            * diagonal arrows:
            *
            *     h together with r and s
            *     h together with u and v
            *
            * Move that actual rendered object slightly outside the original
            * commutative square, without changing the table's layout.
            */
            const objectCells = Array.from(
                table.querySelectorAll(
                    "td[data-pm-source-row][data-pm-source-col]"
                )
            );

            const sourceRows = objectCells.map(cell =>
                Number(
                    cell.getAttribute("data-pm-source-row")
                )
            );

            const sourceCols = objectCells.map(cell =>
                Number(
                    cell.getAttribute("data-pm-source-col")
                )
            );

            const minSourceRow =
                Math.min(...sourceRows);

            const maxSourceRow =
                Math.max(...sourceRows);

            const minSourceCol =
                Math.min(...sourceCols);

            const maxSourceCol =
                Math.max(...sourceCols);

            const diagonalDegree = new Map();

            arrows.forEach(arrow => {
                const sourceKey =
                    getXyOverlayCoordinateKey(
                        arrow.sourceRow,
                        arrow.sourceCol
                    );

                const targetKey =
                    getXyOverlayCoordinateKey(
                        arrow.targetRow,
                        arrow.targetCol
                    );

                diagonalDegree.set(
                    sourceKey,
                    (diagonalDegree.get(sourceKey) || 0) + 1
                );

                diagonalDegree.set(
                    targetKey,
                    (diagonalDegree.get(targetKey) || 0) + 1
                );
            });

            /*
            * Reset earlier positioning first. This matters when the overlay
            * function is called again after previewing or resizing.
            */
            objectCells.forEach(cell => {
                const anchor =
                    getXyOverlayObjectAnchor(cell);

                if (!anchor) {
                    return;
                }

                anchor.style.position = "relative";
                anchor.style.left = "0px";
                anchor.style.top = "0px";
            });

            objectCells.forEach(cell => {
                const row =
                    Number(
                        cell.getAttribute("data-pm-source-row")
                    );

                const col =
                    Number(
                        cell.getAttribute("data-pm-source-col")
                    );

                const key =
                    getXyOverlayCoordinateKey(row, col);

                /*
                * Ordinary square corners participate in at most one overlay
                * diagonal. The external Z participates in three.
                */
                if ((diagonalDegree.get(key) || 0) < 3) {
                    return;
                }

                let shiftX = 0;
                let shiftY = 0;

                if (col === minSourceCol) {
                    shiftX = -26;
                } else if (col === maxSourceCol) {
                    shiftX = 26;
                }

                if (row === minSourceRow) {
                    shiftY = -18;
                } else if (row === maxSourceRow) {
                    shiftY = 18;
                }

                const anchor =
                    getXyOverlayObjectAnchor(cell);

                if (!anchor) {
                    return;
                }

                anchor.style.position = "relative";
                anchor.style.left = `${shiftX}px`;
                anchor.style.top = `${shiftY}px`;
            });

            let wrapper =
                table.parentElement
                && table.parentElement.classList.contains(
                    "pm-xymatrix-overlay-wrapper"
                )
                    ? table.parentElement
                    : null;

            if (!wrapper) {
                wrapper =
                    document.createElement("div");

                wrapper.className =
                    "pm-xymatrix-overlay-wrapper";

                const isInlineSequence =
                    Boolean(
                        table.closest(
                            ".pm-xymatrix-sequence"
                        )
                    );

                wrapper.style.position = "relative";
                wrapper.style.display =
                    isInlineSequence
                        ? "inline-block"
                        : "block";

                wrapper.style.width = "max-content";
                wrapper.style.maxWidth = "100%";
                wrapper.style.verticalAlign = "middle";
                wrapper.style.overflow = "visible";
                wrapper.style.margin =
                    isInlineSequence
                        ? "0"
                        : "1rem auto";

                table.parentNode.insertBefore(
                    wrapper,
                    table
                );

                wrapper.appendChild(table);

                /*
                * The wrapper now owns the outer margin.
                */
                table.style.margin = "0";
            }

            wrapper
                .querySelectorAll(
                    ":scope > .pm-xymatrix-diagonal-overlay,"
                    + ":scope > .pm-xymatrix-diagonal-label"
                )
                .forEach(node => node.remove());

            const tableRect =
                table.getBoundingClientRect();

            const wrapperRect =
                wrapper.getBoundingClientRect();

            const namespace =
                "http://www.w3.org/2000/svg";

            const svg =
                document.createElementNS(
                    namespace,
                    "svg"
                );

            svg.classList.add(
                "pm-xymatrix-diagonal-overlay"
            );

            svg.setAttribute(
                "viewBox",
                `0 0 ${tableRect.width} ${tableRect.height}`
            );

            svg.setAttribute(
                "width",
                String(tableRect.width)
            );

            svg.setAttribute(
                "height",
                String(tableRect.height)
            );

            svg.style.position = "absolute";
            svg.style.left =
                `${tableRect.left - wrapperRect.left}px`;

            svg.style.top =
                `${tableRect.top - wrapperRect.top}px`;

            svg.style.width =
                `${tableRect.width}px`;

            svg.style.height =
                `${tableRect.height}px`;

            svg.style.overflow = "visible";
            svg.style.pointerEvents = "none";
            svg.style.zIndex = "2";
            svg.style.color = "currentColor";

            wrapper.appendChild(svg);

            const orderedArrows = [...arrows].sort(
                (leftArrow, rightArrow) => {
                    const leftIsDotted =
                        String(leftArrow.style || "")
                            .includes(".");

                    const rightIsDotted =
                        String(rightArrow.style || "")
                            .includes(".");

                    /*
                    * Solid arrows first; dotted universal arrow h last.
                    */
                    return (
                        Number(leftIsDotted)
                        - Number(rightIsDotted)
                    );
                }
            );

            orderedArrows.forEach(arrow => {
                const sourceCell =
                    table.querySelector(
                        `td[data-pm-source-row="${arrow.sourceRow}"]`
                        + `[data-pm-source-col="${arrow.sourceCol}"]`
                    );

                const targetCell =
                    table.querySelector(
                        `td[data-pm-source-row="${arrow.targetRow}"]`
                        + `[data-pm-source-col="${arrow.targetCol}"]`
                    );

                if (!sourceCell || !targetCell) {
                    return;
                }

                const sourceAnchor =
                    getXyOverlayObjectAnchor(sourceCell);

                const targetAnchor =
                    getXyOverlayObjectAnchor(targetCell);

                if (!sourceAnchor || !targetAnchor) {
                    return;
                }

                const sourceRect =
                    sourceAnchor.getBoundingClientRect();

                const targetRect =
                    targetAnchor.getBoundingClientRect();

                const sourceCenterX =
                    sourceRect.left
                    + sourceRect.width / 2
                    - tableRect.left;

                const sourceCenterY =
                    sourceRect.top
                    + sourceRect.height / 2
                    - tableRect.top;

                const targetCenterX =
                    targetRect.left
                    + targetRect.width / 2
                    - tableRect.left;

                const targetCenterY =
                    targetRect.top
                    + targetRect.height / 2
                    - tableRect.top;

                const deltaX =
                    targetCenterX - sourceCenterX;

                const deltaY =
                    targetCenterY - sourceCenterY;

                const length =
                    Math.hypot(deltaX, deltaY);

                if (length < 1) {
                    return;
                }

                const unitX =
                    deltaX / length;

                const unitY =
                    deltaY / length;

                const sourceBoundary =
                    getXyRectangleBoundaryDistance(
                        sourceRect,
                        unitX,
                        unitY
                    );

                const targetBoundary =
                    getXyRectangleBoundaryDistance(
                        targetRect,
                        unitX,
                        unitY
                    );

                const sourceKey =
                    getXyOverlayCoordinateKey(
                        arrow.sourceRow,
                        arrow.sourceCol
                    );

                const targetKey =
                    getXyOverlayCoordinateKey(
                        arrow.targetRow,
                        arrow.targetCol
                    );

                /*
                * The outer universal-property node Z participates in three
                * diagonal arrows. Give arrows slightly more breathing room
                * where they meet that node.
                */
                const sourceEndpointPadding =
                    (diagonalDegree.get(sourceKey) || 0) >= 3
                        ? 6
                        : 3;

                const targetEndpointPadding =
                    (diagonalDegree.get(targetKey) || 0) >= 3
                        ? 6
                        : 3;

                const startX =
                    sourceCenterX
                    + unitX * (
                        sourceBoundary
                        + sourceEndpointPadding
                    );

                const startY =
                    sourceCenterY
                    + unitY * (
                        sourceBoundary
                        + sourceEndpointPadding
                    );

                const endX =
                    targetCenterX
                    - unitX * (
                        targetBoundary
                        + targetEndpointPadding
                    );

                const endY =
                    targetCenterY
                    - unitY * (
                        targetBoundary
                        + targetEndpointPadding
                    );

                const normalX = -unitY;
                const normalY = unitX;

                const curveSign =
                    arrow.curveSide === "^"
                        ? -1
                        : arrow.curveSide === "_"
                            ? 1
                            : 0;

                const curveAmount =
                    curveSign === 0
                        ? 0
                        : parseXyCurveAmountToPixels(
                            arrow.curveAmount,
                            table
                        );

                const controlX =
                    (startX + endX) / 2
                    + normalX
                        * curveAmount
                        * curveSign;

                const controlY =
                    (startY + endY) / 2
                    + normalY
                        * curveAmount
                        * curveSign;

                const style =
                    String(arrow.style || "->");

                const isInvisible =
                    style === "";

                const isPlainLine =
                    style === "-";

                const isDotted =
                    style.includes(".");

                const isDashed =
                    style.includes("--");

                if (!isInvisible) {
                    const path =
                        document.createElementNS(
                            namespace,
                            "path"
                        );

                    path.setAttribute(
                        "d",
                        curveSign === 0
                            ? (
                                `M ${startX} ${startY}`
                                + ` L ${endX} ${endY}`
                            )
                            : (
                                `M ${startX} ${startY}`
                                + ` Q ${controlX} ${controlY}`
                                + ` ${endX} ${endY}`
                            )
                    );

                    path.setAttribute("fill", "none");
                    path.setAttribute(
                        "stroke",
                        "currentColor"
                    );

                    path.setAttribute(
                        "stroke-width",
                        isDotted ? "1.9" : "1.6"
                    );

                    path.setAttribute(
                        "vector-effect",
                        "non-scaling-stroke"
                    );

                    if (isDotted) {
                        path.setAttribute(
                            "stroke-dasharray",
                            "2 4"
                        );
                    } else if (isDashed) {
                        path.setAttribute(
                            "stroke-dasharray",
                            "7 5"
                        );
                    }

                    if (!isPlainLine) {
                        const markerId =
                            `pm-xymatrix-overlay-head-`
                            + (
                                ++xyMatrixOverlayMarkerSerial
                            );

                        createXyOverlayArrowMarker(
                            svg,
                            markerId
                        );

                        path.setAttribute(
                            "marker-end",
                            `url(#${markerId})`
                        );
                    }

                    svg.appendChild(path);
                }

                if (!arrow.label) {
                    return;
                }

                /*
                * Quadratic Bézier midpoint at t = 0.5.
                */
                const pathMidX =
                    0.25 * startX
                    + 0.5 * controlX
                    + 0.25 * endX;

                const pathMidY =
                    0.25 * startY
                    + 0.5 * controlY
                    + 0.25 * endY;

                const labelSide =
                    arrow.labelPosition === "above"
                        ? -1
                        : arrow.labelPosition === "below"
                            ? 1
                            : 0;

                const labelOffset =
                    labelSide * 11;

                const label =
                    document.createElement("div");

                label.className =
                    "pm-xymatrix-diagonal-label tex2jax_process";

                label.style.position = "absolute";

                label.style.left =
                    `${
                        tableRect.left
                        - wrapperRect.left
                        + pathMidX
                        + normalX * labelOffset
                    }px`;

                label.style.top =
                    `${
                        tableRect.top
                        - wrapperRect.top
                        + pathMidY
                        + normalY * labelOffset
                    }px`;

                label.style.transform =
                    "translate(-50%, -50%)";

                label.style.padding = "0 0.12em";
                label.style.background =
                    "var(--bs-body-bg, white)";

                label.style.whiteSpace = "nowrap";
                label.style.lineHeight = "1";
                label.style.pointerEvents = "none";
                label.style.zIndex = "3";

                label.textContent =
                    `\\({\\scriptstyle ${arrow.label}}\\)`;

                wrapper.appendChild(label);
                labelsToTypeset.push(label);
            });
        }

        if (
            labelsToTypeset.length > 0
            && window.MathJax
            && typeof window.MathJax.typesetPromise === "function"
        ) {
            await window.MathJax.typesetPromise(
                labelsToTypeset
            );
        }
    }

    function normalizeLegacyTwoCellArrowLabel(value) {
        let label = String(value || "").trim();

        // \stackrel{R}{}  -> R
        // \stackrel{}{T}  -> T
        const stackrelMatch = label.match(
            /^\\stackrel\s*\{([^{}]*)\}\s*\{([^{}]*)\}$/
        );

        if (stackrelMatch) {
            label = (
                String(stackrelMatch[1] || "").trim()
                || String(stackrelMatch[2] || "").trim()
            );
        }

        return label;
    }


    function normalizeLegacyTwoCellInnerLabel(value) {
        let label = String(value || "").trim();

        if (/^\\omit\b/i.test(label)) {
            return "";
        }

        // Remove Xy-pic positioning prefix:
        //   <0>_{\quad \tau}
        //   <-2.5>_{\mbox{ } \tau}
        //   <2.5>^{\mbox{ } \eta}
        label = label.replace(/^<[^>]*>\s*/, "");

        const positionedMatch = label.match(
            /^[_^]\s*\{([\s\S]*)\}$/
        );

        if (positionedMatch) {
            label = positionedMatch[1].trim();
        }

        label = label
            .replace(/\\(?:quad|qquad)\b/g, " ")
            .replace(/\\mbox\s*\{([^{}]*)\}/g, "$1")
            .replace(/\s+/g, " ")
            .trim();

        return label;
    }


    function parseLegacyTwoCellCommandAt(text, commandIndex, commandName) {
        const source = String(text || "");
        const command = `\\${commandName}`;

        if (!source.startsWith(command, commandIndex)) {
            return null;
        }

        let cursor = commandIndex + command.length;

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        // Optional Xy-pic offset such as <4.5>, <-5>, or <9>.
        if (source[cursor] === "<") {
            const offsetEnd = source.indexOf(">", cursor + 1);

            if (offsetEnd === -1) {
                return null;
            }

            cursor = offsetEnd + 1;
        }

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        // Upper commands use ^{...}; lower commands use _{...}.
        if (source[cursor] !== "^" && source[cursor] !== "_") {
            return null;
        }

        cursor += 1;

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        if (source[cursor] !== "{") {
            return null;
        }

        const arrowLabelEnd = findMatchingBrace(source, cursor);

        if (arrowLabelEnd === -1) {
            return null;
        }

        const rawArrowLabel = source.slice(cursor + 1, arrowLabelEnd);
        cursor = arrowLabelEnd + 1;

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        if (source[cursor] !== "{") {
            return null;
        }

        const innerLabelEnd = findMatchingBrace(source, cursor);

        if (innerLabelEnd === -1) {
            return null;
        }

        const rawInnerLabel = source.slice(cursor + 1, innerLabelEnd);

        return {
            commandName,
            start: commandIndex,
            end: innerLabelEnd + 1,
            arrowLabel: normalizeLegacyTwoCellArrowLabel(rawArrowLabel),
            innerLabel: normalizeLegacyTwoCellInnerLabel(rawInnerLabel)
        };
    }


    function extractLegacyTwoCellCommands(value) {
        const source = String(value || "");
        const commands = [];

        let cursor = 0;

        while (cursor < source.length) {
            const upperIndex = source.indexOf("\\ruppertwocell", cursor);
            const lowerIndex = source.indexOf("\\rlowertwocell", cursor);

            const candidateIndexes = [upperIndex, lowerIndex]
                .filter(index => index !== -1);

            if (candidateIndexes.length === 0) {
                break;
            }

            const commandIndex = Math.min(...candidateIndexes);
            const commandName =
                commandIndex === upperIndex
                    ? "ruppertwocell"
                    : "rlowertwocell";

            const parsed = parseLegacyTwoCellCommandAt(
                source,
                commandIndex,
                commandName
            );

            if (!parsed) {
                cursor = commandIndex + 1;
                continue;
            }

            commands.push(parsed);
            cursor = parsed.end;
        }

        let cleanText = source;

        [...commands]
            .sort((left, right) => right.start - left.start)
            .forEach(command => {
                cleanText =
                    cleanText.slice(0, command.start)
                    + cleanText.slice(command.end);
            });

        const upper = commands.find(
            command => command.commandName === "ruppertwocell"
        );

        const lower = commands.find(
            command => command.commandName === "rlowertwocell"
        );

        return {
            text: cleanText,
            legacyTwoCell: upper || lower
                ? {
                    upperArrowLabel: upper?.arrowLabel || "",
                    upperInnerLabel: upper?.innerLabel || "",
                    lowerArrowLabel: lower?.arrowLabel || "",
                    lowerInnerLabel: lower?.innerLabel || ""
                }
                : null
        };
    }

    function parseXyMatrixCell(rawCell) {
        const legacyTwoCellResult = extractLegacyTwoCellCommands(rawCell);

        let text = legacyTwoCellResult.text.trim();
        const legacyTwoCell = legacyTwoCellResult.legacyTwoCell;

        const arrows = [];
        let twoCellLabel = "";
        let objectFrame = null;
        let overlayLabel = "";

        /*
        * Legacy Xy-pic crossing-gap marker:
        *
        *   \ar@{-}[rd]|!{"2,1";"1,2"}\hole
        *
        * The HTML/SVG converter already renders the underlying arrow. Remove
        * the placement suffix so it cannot leak into the visible object text
        * or reach MathJax as an undefined command.
        */
        text = text.replace(
            /\|\s*!\s*\{[^{}]*\}\s*\\hole\b/g,
            ""
        );

        /*
        * Legacy Xy-pic saved text object:
        *
        *   \save *\txt{the decimal point} \restore \ar[u]
        *
        * Preserve the visible text and following arrow, but discard the
        * Xy-pic save/restore positioning wrappers.
        */
        text = text.replace(
            /\\save\s*\*\s*\\txt\s*\{([^{}]*)\}\s*\\restore\b/g,
            (_, label) => {
                overlayLabel = String(label || "").trim();
                return "";
            }
        );

        /*
        * Xy-pic framed automaton states:
        *
        *   *+[o][F-]{0}   single-circle state
        *   *++[o][F=]{2}  double-circle accepting state
        */
        text = text.replace(
            /^\s*\*\+*\[o\]\[F([-=])\]\s*\{([^{}]*)\}/,
            function (_, frameStyle, objectLabel) {
                objectFrame = {
                    shape: "circle",
                    doubleBorder: frameStyle === "="
                };

                return String(objectLabel || "").trim();
            }
        );

        // Invisible Xy-pic arrow used to place a relation between two
        // previously named arrows:
        //
        //   \ar@{}"1";"2"|-{=}
        //
        // Preserve the visible relation label, but remove the Xy-pic
        // reference syntax so it cannot leak into the object text.
        text = text.replace(
            /\\ar@\{\}\s*"[^"]+"\s*;\s*"[^"]+"\s*\|\s*-\s*\{([^{}]*)\}/g,
            function (_, relationLabel) {
                twoCellLabel = String(relationLabel || "").trim();
                return "";
            }
        );

        // Xy-pic 2-cell between two previously named arrows:
        //
        //   \ar@{=>}"1";"2"_{\tau}
        //
        // Capture its label separately so the reference syntax does not leak
        // into the rendered object text.
        text = text.replace(
            /\\ar@\{=>\}\s*"[^"]+"\s*;\s*"[^"]+"\s*(?:[_^]\s*(?:\{([^{}]*)\}|(\\?[A-Za-z0-9]+)))?/g,
            function (_, bracedLabel, unbracedLabel) {
                twoCellLabel = String(
                    bracedLabel || unbracedLabel || ""
                ).trim();

                return "";
            }
        );

        // Supports common Xy-pic variants:
        //   \ar[r]
        //   \ar[d]^f
        //   \ar[r]^{F(x)}
        //   \ar@<0.5ex>[r]^f
        //   \ar@<-0.5ex>[r]_g
        //   \ar@{->}[rd]
        //   \ar@{}[dr]|{=}
        //   \ar@/^1ex/[ddr]
        //
        // Also consume optional named-arrow suffixes:
        //   ="1"
        //   ="2"
        const arrowPattern =
            /\\ar(?:@\{[^{}]*\}|@<[^>]*>|@[^\s\[\]&{}]+)*(?:\s*\[([^\]]*)\])?((?:\s*(?:[_^](?:[-+])?\s*[<>]*\s*(?:\{(?:[^{}]|\{[^{}]*\})*\}|\\?[A-Za-z0-9]+)|\|(?:\{(?:[^{}]|\{[^{}]*\})*\}|\\?[A-Za-z0-9=+\-]+)))*)\s*(?:=\s*"[^"]+")?/g;

        let match;

        while ((match = arrowPattern.exec(text)) !== null) {
            const directionText = match[1] || "r";

            const styleMatch =
                match[0].match(/@\{([^{}]*)\}/);

            const curveMatch =
                match[0].match(
                    /@\/\s*([_^])\s*([^/]*)\//i
                );

            const labelInfo =
                extractXyArrowLabel(match[2] || "");

                        const selfLoopMatch = match[0].match(
                /@\(\s*([rl])\s*,\s*([ud])\s*\)/i
            );

            arrows.push({
                direction: normalizeXyArrowDirection(directionText),
                directionText,
                span: getXyArrowSpan(directionText),
                style: styleMatch ? styleMatch[1] : "->",
                label: labelInfo.text,
                labelPosition: labelInfo.position,

                curveSide:
                    curveMatch
                        ? curveMatch[1]
                        : "",

                curveAmount:
                    curveMatch
                        ? String(curveMatch[2] || "").trim()
                        : "",

                isSelfLoop: Boolean(selfLoopMatch),

                loopSide:
                    selfLoopMatch
                    && selfLoopMatch[1].toLowerCase() === "l"
                        ? "left"
                        : "right",

                loopPlacement:
                    selfLoopMatch
                    && selfLoopMatch[2].toLowerCase() === "d"
                        ? "below"
                        : "above"
            });
        }

        const objectTex = text
            .replace(arrowPattern, "")
            .replace(/\s+/g, " ")

            /*
            * A recovered or partially preserved xymatrix row separator can
            * leave one or more backslashes in an otherwise empty object cell.
            *
            * Without this cleanup, renderXyObjectCell() wraps that residue in
            * generated \( ... \) delimiters, which can display literally.
            */
            .replace(/\\+\s*$/, "")

            .trim();

        return {
            objectTex,
            objectFrame,
            overlayLabel,
            arrows,
            twoCellLabel,
            legacyTwoCell
        };
    }

    function normalizeXyArrowDirection(direction) {
        const clean = String(direction || "r")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        // Preserve diagonal directions before testing single directions.
        if (clean.includes("d") && clean.includes("l")) return "dl";
        if (clean.includes("d") && clean.includes("r")) return "dr";
        if (clean.includes("u") && clean.includes("l")) return "ul";
        if (clean.includes("u") && clean.includes("r")) return "ur";

        if (clean.includes("d")) return "d";
        if (clean.includes("u")) return "u";
        if (clean.includes("l")) return "l";

        return "r";
    }

    function getXyArrowSpan(directionText) {
        const clean = String(directionText || "r")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        return Math.max(clean.length, 1);
    }

    function getXyArrowHorizontalSpan(directionText) {
        const clean = String(directionText || "")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        const horizontalSteps =
            (clean.match(/[lr]/g) || []).length;

        return Math.max(horizontalSteps, 1);
    }

    function isXyDiagonalDirection(direction) {
        return (
            direction === "dl"
            || direction === "dr"
            || direction === "ul"
            || direction === "ur"
        );
    }

    function getXyArrowCoordinateDelta(directionText) {
        const clean = String(directionText || "")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        return {
            rowDelta:
                (clean.match(/d/g) || []).length
                - (clean.match(/u/g) || []).length,

            colDelta:
                (clean.match(/r/g) || []).length
                - (clean.match(/l/g) || []).length
        };
    }

    function extractXyArrowLabel(modifierText) {
        const text = String(modifierText || "");

        const bracedMatch = text.match(
            /([_^|])(?:[-+])?\s*[<>]*\s*\{((?:[^{}]|\{[^{}]*\})*)\}/
        );

        if (bracedMatch) {
            return {
                text: bracedMatch[2].trim(),
                position:
                    bracedMatch[1] === "_"
                        ? "below"
                        : bracedMatch[1] === "^"
                            ? "above"
                            : "center"
            };
        }

        const unbracedMatch = text.match(
            /([_^|])(?:[-+])?\s*[<>]*\s*(\\?[A-Za-z0-9=+\-]+)/
        );

        if (unbracedMatch) {
            return {
                text: unbracedMatch[2].trim(),
                position:
                    unbracedMatch[1] === "_"
                        ? "below"
                        : unbracedMatch[1] === "^"
                            ? "above"
                            : "center"
            };
        }

        return {
            text: "",
            position: "above"
        };
    }

    function setGridCellIfInBounds(grid, row, col, value) {
        if (
            row < 0 ||
            col < 0 ||
            row >= grid.length ||
            col >= grid[row].length
        ) {
            return;
        }

        grid[row][col] = value;
    }

    function applyXyPlainHorizontalLineToGrid(
        grid,
        gridRow,
        gridCol,
        direction,
        span
    ) {
        const sourceSpan = Math.max(Number(span) || 1, 1);
        const step = direction === "left" ? -1 : 1;

        // Expanded Xy grid:
        // object, arrow-space, object, arrow-space, object...
        //
        // A source span of 1 occupies 1 expanded cell.
        // A source span of 8 occupies 15 expanded cells.
        const expandedCellCount = sourceSpan * 2 - 1;

        for (let offset = 1; offset <= expandedCellCount; offset += 1) {
            setGridCellIfInBounds(
                grid,
                gridRow,
                gridCol + step * offset,
                XY_PLAIN_HORIZONTAL_LINE
            );
        }
    }

    function renderDiagonalArrow(
        label,
        direction = "dr",
        arrowLayout = {},
        options = {}
    ) {
        const safeLabel = escapeHtmlForMathCell(label || "");

        const baseWidthEm = Math.max(
            arrowLayout.horizontalWidthEm || 3.6,
            4.2
        );

        const horizontalSpan =
            Math.max(Number(options.horizontalSpan) || 1, 1);

        /*
        * A wide diagonal such as [lld] or [rrd] crosses more than one
        * source-column gap. Keep the owning table cell at zero width so the
        * long SVG can overflow across neighboring cells without stretching
        * the xymatrix column layout.
        */
        const widthEm =
            baseWidthEm * horizontalSpan
            + Math.max(horizontalSpan - 1, 0) * 0.9;

        const layoutWidthEm =
            horizontalSpan > 1
                ? 0
                : widthEm;

        const heightEm = Math.max(
            arrowLayout.verticalHeightEm || 2.7,
            3.2
        );

        const isDashed = options.isDashed === true;

        const showArrowHead =
            options.showArrowHead !== false;

        const labelPosition =
            options.labelPosition || "center";

        const goesRight =
            direction === "dr" || direction === "ur";

        const goesDown =
            direction === "dr" || direction === "dl";

        const startX = goesRight ? 4 : 96;
        const endX = goesRight ? 96 : 4;

        const startY = goesDown ? 4 : 96;
        const endY = goesDown ? 96 : 4;

        let labelTopPercent = 50;
        let labelLeftPercent = 50;

        if (labelPosition === "above") {
            labelTopPercent -= 13;
        } else if (labelPosition === "below") {
            labelTopPercent += 13;
        }

        if (direction === "dl" || direction === "ur") {
            labelLeftPercent +=
                labelPosition === "above" ? 7
                    : labelPosition === "below" ? -7
                        : 0;
        } else {
            labelLeftPercent +=
                labelPosition === "above" ? -7
                    : labelPosition === "below" ? 7
                        : 0;
        }

        const labelHtml = safeLabel
            ? `
                <div style="
                    position:absolute;
                    left:${labelLeftPercent}%;
                    top:${labelTopPercent}%;
                    transform:translate(-50%, -50%);
                    padding:0 0.12em;
                    background:var(--bs-body-bg, white);
                    white-space:nowrap;
                    line-height:1;
                    z-index:2;
                ">
                    \\({\\scriptstyle ${safeLabel}}\\)
                </div>
            `
            : "";

        const markerId =
            `pm-xymatrix-diagonal-head-${direction}-${horizontalSpan}-${isDashed ? "dashed" : "solid"}`;

        const markerDefinition = showArrowHead
            ? `
                <defs>
                    <marker
                        id="${markerId}"
                        markerWidth="8"
                        markerHeight="8"
                        refX="7"
                        refY="4"
                        orient="auto"
                        markerUnits="strokeWidth"
                    >
                        <path
                            d="M0,0 L8,4 L0,8 Z"
                            fill="currentColor"
                        ></path>
                    </marker>
                </defs>
            `
            : "";

        const markerAttribute = showArrowHead
            ? `marker-end="url(#${markerId})"`
            : "";

        return `
            <div class="pm-xymatrix-diagonal-arrow" style="
                position:relative;
                width:${layoutWidthEm}em;
                height:${heightEm}em;
                min-width:${layoutWidthEm}em;
                min-height:${heightEm}em;
                display:inline-block;
                vertical-align:middle;
                overflow:visible;
            ">
                <div style="
                    position:absolute;
                    left:50%;
                    top:0;
                    width:${widthEm}em;
                    height:100%;
                    transform:translateX(-50%);
                    overflow:visible;
                ">
                    <svg
                        aria-hidden="true"
                        viewBox="0 0 100 100"
                        preserveAspectRatio="none"
                        style="
                            position:absolute;
                            inset:0;
                            width:100%;
                            height:100%;
                            overflow:visible;
                        "
                    >
                        ${markerDefinition}

                        <line
                            x1="${startX}"
                            y1="${startY}"
                            x2="${endX}"
                            y2="${endY}"
                            stroke="currentColor"
                            stroke-width="1.8"
                            vector-effect="non-scaling-stroke"
                            ${isDashed
                                ? 'stroke-dasharray="6 5"'
                                : ""
                            }
                            ${markerAttribute}
                        ></line>
                    </svg>

                    ${labelHtml}
                </div>
            </div>
        `;
    }

    function applySpanningVerticalArrowToGrid(
        grid,
        gridRow,
        gridCol,
        label,
        direction,
        span,
        arrowLayout,
        options = {}
    ) {
        const sourceSpan = Math.max(Number(span) || 1, 1);

        /*
        * One source-row jump occupies one expanded arrow row.
        * Additional jumps also cross the intervening object rows.
        *
        *   span 1 -> rowspan 1
        *   span 2 -> rowspan 3
        *   span 3 -> rowspan 5
        */
        const rowSpan = sourceSpan * 2 - 1;

        const startRow =
            direction === "up"
                ? gridRow - rowSpan
                : gridRow + 1;

        const ordinaryArrowHeight =
            arrowLayout.verticalHeightEm || 2.7;

        const intermediateObjectHeight = 1.25;

        const totalHeightEm =
            sourceSpan * ordinaryArrowHeight
            + (sourceSpan - 1) * intermediateObjectHeight;

        setGridCellIfInBounds(
            grid,
            startRow,
            gridCol,
            renderVerticalArrow(
                label,
                direction,
                arrowLayout,
                {
                    rowSpan,
                    heightEm: totalHeightEm,
                    showArrowHead:
                        options.showArrowHead !== false,
                    extendLine: false
                }
            )
        );

        /*
        * These grid positions are occupied by the rowspan cell and must
        * not produce their own table cells.
        */
        for (let offset = 1; offset < rowSpan; offset += 1) {
            setGridCellIfInBounds(
                grid,
                startRow + offset,
                gridCol,
                XY_VERTICAL_ROWSPAN_COVERED
            );
        }
    }

    function applyXyArrowToGrid(grid, gridRow, gridCol, arrow, arrowLayout) {
        const label = arrow.label || "";
        const direction = arrow.direction || "r";
        const span = arrow.span || 1;
        const isPlainLine = arrow.style === "-";
        const isDashed =
            String(arrow.style || "").includes("--");

        if (direction === "r") {
            if (isPlainLine) {
                applyXyPlainHorizontalLineToGrid(
                    grid,
                    gridRow,
                    gridCol,
                    "right",
                    span
                );
                return;
            }

            setGridCellIfInBounds(
                grid,
                gridRow,
                gridCol + 1,
                renderHorizontalArrow(
                    label,
                    "right",
                    arrowLayout,
                    {
                        labelPosition: arrow.labelPosition
                    }
                )
            );
            return;
        }

        if (direction === "l") {
            if (isPlainLine) {
                applyXyPlainHorizontalLineToGrid(
                    grid,
                    gridRow,
                    gridCol,
                    "left",
                    span
                );
                return;
            }

            setGridCellIfInBounds(
                grid,
                gridRow,
                gridCol - 1,
                renderHorizontalArrow(
                    label,
                    "left",
                    arrowLayout,
                    {
                        labelPosition: arrow.labelPosition
                    }
                )
            );
            return;
        }

        if (
            direction === "dl"
            || direction === "dr"
            || direction === "ul"
            || direction === "ur"
        ) {
            const rowOffset =
                direction.includes("d")
                    ? 1
                    : -1;

            const horizontalSpan =
                getXyArrowHorizontalSpan(
                    arrow.directionText
                );

            const colOffset =
                direction.includes("r")
                    ? horizontalSpan
                    : -horizontalSpan;

            setGridCellIfInBounds(
                grid,
                gridRow + rowOffset,
                gridCol + colOffset,
                renderDiagonalArrow(
                    label,
                    direction,
                    arrowLayout,
                    {
                        isDashed,
                        showArrowHead: !isPlainLine,
                        horizontalSpan,
                        labelPosition:
                            arrow.labelPosition
                    }
                )
            );

            return;
        }

        if (direction === "d") {
            applySpanningVerticalArrowToGrid(
                grid,
                gridRow,
                gridCol,
                label,
                "down",
                span,
                arrowLayout,
                {
                    showArrowHead: !isPlainLine
                }
            );
            return;
        }

        if (direction === "u") {
            applySpanningVerticalArrowToGrid(
                grid,
                gridRow,
                gridCol,
                label,
                "up",
                span,
                arrowLayout,
                {
                    showArrowHead: !isPlainLine
                }
            );
        }
    }

    function renderLegacyTwoCellArrowGroup(
        legacyTwoCell,
        middleArrowLabel = "",
        arrowLayout = {}
    ) {
        if (!legacyTwoCell) {
            return "";
        }

        const upperArrowLabel =
            legacyTwoCell.upperArrowLabel || "";

        const upperInnerLabel =
            legacyTwoCell.upperInnerLabel || "";

        const lowerArrowLabel =
            legacyTwoCell.lowerArrowLabel || "";

        const lowerInnerLabel =
            legacyTwoCell.lowerInnerLabel || "";

        const widthEm =
            Math.max(arrowLayout.horizontalWidthEm || 3.2, 4.6);

        const renderLine = (
            label,
            verticalOffsetEm,
            labelPosition = "above"
        ) => {
            const safeLabel = escapeHtmlForMathCell(label);

            const labelPositionStyle =
                labelPosition === "below"
                    ? "top:0.28em;"
                    : "bottom:0.28em;";

            return `
                <div style="
                    position:absolute;
                    left:0;
                    top:${verticalOffsetEm}em;
                    width:${widthEm}em;
                    height:0;
                    border-top:1.5px solid currentColor;
                ">
                    <span aria-hidden="true" style="
                        position:absolute;
                        right:-0.02em;
                        top:-0.31em;
                        width:0;
                        height:0;
                        border-top:0.30em solid transparent;
                        border-bottom:0.30em solid transparent;
                        border-left:0.48em solid currentColor;
                    "></span>

                    ${
                        safeLabel
                            ? `
                                <span style="
                                    position:absolute;
                                    left:50%;
                                    ${labelPositionStyle}
                                    transform:translateX(-50%);
                                    white-space:nowrap;
                                    line-height:1;
                                ">
                                    \\({\\scriptstyle ${safeLabel}}\\)
                                </span>
                            `
                            : ""
                    }
                </div>
            `;
        };

        const transformationLabels = [
            upperInnerLabel,
            lowerInnerLabel
        ].filter(Boolean);

        const transformationHtml = transformationLabels.length
            ? `
                <div style="
                    position:absolute;
                    left:50%;
                    top:50%;
                    transform:translate(-50%, -50%);
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    gap:0.32em;
                    white-space:nowrap;
                    line-height:1;
                    background:var(--bs-body-bg, white);
                    padding:0 0.18em;
                ">
                    ${transformationLabels.map(label => `
                        <span>
                            \\({\\scriptstyle ${escapeHtmlForMathCell(label)}}\\)
                        </span>
                    `).join("")}
                </div>
            `
            : "";

        const middleArrowHtml = middleArrowLabel
            ? `
                <div style="
                    position:absolute;
                    left:0;
                    top:50%;
                    width:${widthEm}em;
                    height:0;
                    border-top:1.5px solid currentColor;
                    transform:translateY(-50%);
                ">
                    <span aria-hidden="true" style="
                        position:absolute;
                        right:-0.02em;
                        top:-0.31em;
                        width:0;
                        height:0;
                        border-top:0.30em solid transparent;
                        border-bottom:0.30em solid transparent;
                        border-left:0.48em solid currentColor;
                    "></span>

                    <span style="
                        position:absolute;
                        left:50%;
                        bottom:0.22em;
                        transform:translateX(-50%);
                        white-space:nowrap;
                        line-height:1;
                    ">
                        \\({\\scriptstyle ${escapeHtmlForMathCell(
                            middleArrowLabel
                        )}}\\)
                    </span>
                </div>
            `
            : "";

        return `
            <div class="pm-xymatrix-two-cell" style="
                position:relative;
                width:${widthEm}em;
                height:4.8em;
                min-width:${widthEm}em;
            ">
                ${renderLine(upperArrowLabel, 0.70, "above")}
                ${middleArrowHtml}
                ${renderLine(lowerArrowLabel, 4.10, "below")}
                ${transformationHtml}
            </div>
        `;
    }

    function renderNamedReferenceTwoCell(label) {
        const safeLabel = escapeHtmlForMathCell(label || "");

        if (!safeLabel) {
            return "";
        }

        return `
            <div class="pm-xymatrix-named-two-cell" style="
                display:inline-flex;
                align-items:center;
                justify-content:center;
                min-width:2.8em;
                min-height:2.2em;
                white-space:nowrap;
            ">
                \\(\\overset{${safeLabel}}{\\Rightarrow}\\)
            </div>
        `;
    }

    function renderXySelfLoop(arrow) {
        const placement =
            arrow?.loopPlacement === "below"
                ? "below"
                : "above";

        const side =
            arrow?.loopSide === "left"
                ? "left"
                : "right";

        const safeLabel =
            escapeHtmlForMathCell(arrow?.label || "");

        const isAbove = placement === "above";
        const isLeft = side === "left";

        /*
         * Draw from left to right for a right-side loop and from right
         * to left for a left-side loop. The arrowhead is placed at endX.
         */
        const startX = isLeft ? 80 : 20;
        const endX = isLeft ? 20 : 80;

        const anchorY = isAbove ? 52 : 8;
        const controlY = isAbove ? 6 : 54;

        /*
         * The polygon overlaps the final section of the curve, so the
         * arrowhead and arc appear to be one continuous stroke.
         */
        const arrowTipY = isAbove ? 59 : 1;
        const arrowBaseY = isAbove ? 47 : 13;

        const arrowPoints = [
            `${endX},${arrowTipY}`,
            `${endX - 6},${arrowBaseY}`,
            `${endX + 6},${arrowBaseY}`
        ].join(" ");

        const wrapperPosition = isAbove
            ? "top:0;"
            : "bottom:0;";

        const labelPosition = isAbove
            ? "top:0.7em;"
            : "bottom:0.7em;";

        return `
            <span
                class="
                    pm-xymatrix-self-loop
                    pm-xymatrix-self-loop-${placement}
                "
                style="
                    position:absolute;
                    left:50%;
                    ${wrapperPosition}
                    transform:translateX(-50%);
                    width:3.6em;
                    height:2.2em;
                    pointer-events:none;
                    overflow:visible;
                    z-index:1;
                "
            >
                <svg
                    aria-hidden="true"
                    viewBox="0 0 100 60"
                    preserveAspectRatio="xMidYMid meet"
                    style="
                        position:absolute;
                        inset:0;
                        width:100%;
                        height:100%;
                        overflow:visible;
                    "
                >
                    <path
                        d="
                            M ${startX} ${anchorY}
                            C ${startX} ${controlY},
                              ${endX} ${controlY},
                              ${endX} ${anchorY}
                        "
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                        stroke-linecap="round"
                        vector-effect="non-scaling-stroke"
                    ></path>

                    <polygon
                        points="${arrowPoints}"
                        fill="currentColor"
                    ></polygon>
                </svg>

                ${
                    safeLabel
                        ? `
                            <span style="
                                position:absolute;
                                left:50%;
                                ${labelPosition}
                                transform:translateX(-50%);
                                white-space:nowrap;
                                line-height:1;
                                z-index:2;
                            ">
                                \\({\\scriptstyle ${safeLabel}}\\)
                            </span>
                        `
                        : ""
                }
            </span>
        `;
    }

    function renderXyObjectCell(
        tex,
        frame = null,
        selfLoops = [],
        overlayLabel = ""
    ) {
        const cleanOverlayLabel =
            String(overlayLabel || "").trim();

        if (!tex && !cleanOverlayLabel) {
            return "";
        }

        /*
        * Xy-pic \save ... \restore text is positioned without contributing
        * to the width of its matrix column.
        */
        if (cleanOverlayLabel) {
            const labelMathHtml =
                `\\(\\text{${escapeHtmlForMathCell(cleanOverlayLabel)}}\\)`;

            return `
                <span
                    class="pm-xymatrix-overlay-label"
                    style="
                        position:relative;
                        display:inline-block;
                        width:0;
                        height:1.35em;
                        overflow:visible;
                        vertical-align:middle;
                    "
                >
                    <span style="
                        position:absolute;
                        top:0;
                        left:50%;
                        transform:translateX(-50%);
                        white-space:nowrap;
                    ">
                        ${labelMathHtml}
                    </span>
                </span>
            `;
        }

        const mathHtml =
            `\\(${escapeHtmlForMathCell(tex)}\\)`;

        let objectHtml;

        if (!frame || frame.shape !== "circle") {
            objectHtml = mathHtml;
        } else if (frame.doubleBorder) {
            objectHtml = `
                <span
                    class="pm-xymatrix-state pm-xymatrix-state-accepting"
                    style="
                        display:inline-flex;
                        align-items:center;
                        justify-content:center;
                        width:2.25em;
                        height:2.25em;
                        border:1.5px solid currentColor;
                        border-radius:50%;
                        box-sizing:border-box;
                    "
                >
                    <span style="
                        display:inline-flex;
                        align-items:center;
                        justify-content:center;
                        width:1.76em;
                        height:1.76em;
                        border:1.5px solid currentColor;
                        border-radius:50%;
                        box-sizing:border-box;
                    ">
                        ${mathHtml}
                    </span>
                </span>
            `;
        } else {
            objectHtml = `
                <span
                    class="pm-xymatrix-state"
                    style="
                        display:inline-flex;
                        align-items:center;
                        justify-content:center;
                        width:2.05em;
                        height:2.05em;
                        border:1.5px solid currentColor;
                        border-radius:50%;
                        box-sizing:border-box;
                    "
                >
                    ${mathHtml}
                </span>
            `;
        }

        const loops = Array.isArray(selfLoops)
            ? selfLoops.filter(
                arrow => arrow?.isSelfLoop
            )
            : [];

        if (loops.length === 0) {
            return objectHtml;
        }

        const hasAboveLoop = loops.some(
            arrow => arrow.loopPlacement !== "below"
        );

        const hasBelowLoop = loops.some(
            arrow => arrow.loopPlacement === "below"
        );

        return `
            <span
                class="pm-xymatrix-object-with-loops"
                style="
                    position:relative;
                    display:inline-flex;
                    align-items:center;
                    justify-content:center;
                    padding-top:${hasAboveLoop ? "2.55em" : "0"};
                    padding-bottom:${hasBelowLoop ? "2.55em" : "0"};
                "
            >
                <span style="
                    position:relative;
                    display:inline-flex;
                    z-index:2;
                ">
                    ${objectHtml}
                </span>

                ${loops.map(renderXySelfLoop).join("")}
            </span>
        `;
    }

    function renderHorizontalArrow(
        label,
        direction = "right",
        arrowLayout = {},
        options = {}
    ) {
        const safeLabel = escapeHtmlForMathCell(label || "");
        const showArrowHead = options.showArrowHead !== false;

        const labelPosition =
            options.labelPosition || "above";

        const widthEm =
            arrowLayout.horizontalWidthEm || 3.2;

        const labelVerticalStyle =
            labelPosition === "below"
                ? "top:0.72em;"
                : labelPosition === "center"
                    ? "top:50%; transform:translate(-50%, -50%);"
                    : "top:-0.65em;";

        const labelTransform =
            labelPosition === "center"
                ? ""
                : "transform:translateX(-50%);";

        const labelHtml = safeLabel
            ? `<div style="
                    position:absolute;
                    left:50%;
                    ${labelVerticalStyle}
                    ${labelTransform}
                    white-space:nowrap;
                    line-height:1;
                ">\\({\\scriptstyle ${safeLabel}}\\)</div>`
            : "";

        let arrowHead = "";

        if (showArrowHead) {
            arrowHead =
                direction === "left"
                    ? `<span style="
                            position:absolute;
                            left:0;
                            top:50%;
                            transform:translateY(-50%);
                            width:0;
                            height:0;
                            border-top:0.30em solid transparent;
                            border-bottom:0.30em solid transparent;
                            border-right:0.48em solid currentColor;
                        "></span>`
                    : `<span style="
                            position:absolute;
                            right:0;
                            top:50%;
                            transform:translateY(-50%);
                            width:0;
                            height:0;
                            border-top:0.30em solid transparent;
                            border-bottom:0.30em solid transparent;
                            border-left:0.48em solid currentColor;
                        "></span>`;
        }

        return `
            <div style="
                position:relative;
                width:${widthEm}em;
                height:1.8em;
                display:inline-block;
                vertical-align:middle;
                z-index:1;
            ">
                <span style="
                    position:absolute;
                    left:0;
                    right:0;
                    top:50%;
                    transform:translateY(-50%);
                    border-top:1.5px solid currentColor;
                "></span>

                ${arrowHead}
                ${labelHtml}
            </div>
        `;
    }

    function renderVerticalArrow(
        label,
        direction = "down",
        arrowLayout = {},
        options = {}
    ) {
        const safeLabel = escapeHtmlForMathCell(label || "");

        const heightEm =
            Number(options.heightEm)
            || arrowLayout.verticalHeightEm
            || 2.7;

        const widthEm =
            arrowLayout.verticalWidthEm
            || 2.4;

        const showArrowHead =
            options.showArrowHead !== false;

        const rowSpan =
            Math.max(Number(options.rowSpan) || 1, 1);

        const rowSpanAttribute =
            rowSpan > 1
                ? ` data-pm-rowspan="${rowSpan}"`
                : "";

        const wrapperClass =
            rowSpan > 1
                ? "pm-xymatrix-vertical-segment pm-xymatrix-vertical-span"
                : "pm-xymatrix-vertical-segment";

        const lineEdge =
            options.extendLine === true
                ? "-0.22rem"
                : "0";

        const labelHtml = safeLabel
            ? `<div style="
                    position:absolute;
                    left:calc(50% + 0.38em);
                    top:0;
                    bottom:0;
                    display:flex;
                    align-items:center;
                    white-space:nowrap;
                    line-height:1;
                ">\\({\\scriptstyle ${safeLabel}}\\)</div>`
            : "";

        let arrowHead = "";

        if (showArrowHead) {
            arrowHead =
                direction === "up"
                    ? `<span style="
                            position:absolute;
                            left:50%;
                            top:${lineEdge};
                            transform:translateX(-50%);
                            width:0;
                            height:0;
                            border-left:0.30em solid transparent;
                            border-right:0.30em solid transparent;
                            border-bottom:0.48em solid currentColor;
                        "></span>`
                    : `<span style="
                            position:absolute;
                            left:50%;
                            bottom:${lineEdge};
                            transform:translateX(-50%);
                            width:0;
                            height:0;
                            border-left:0.30em solid transparent;
                            border-right:0.30em solid transparent;
                            border-top:0.48em solid currentColor;
                        "></span>`;
        }

        return `
            <div class="${wrapperClass}"${rowSpanAttribute} style="
                position:relative;
                width:${widthEm}em;
                height:${heightEm}em;
                display:inline-block;
                vertical-align:middle;
            ">
                <span style="
                    position:absolute;
                    left:50%;
                    top:${lineEdge};
                    bottom:${lineEdge};
                    transform:translateX(-50%);
                    border-left:1.5px solid currentColor;
                "></span>

                ${arrowHead}
                ${labelHtml}
            </div>
        `;
    }

    function renderMixedXyMatrixWrapperContent(content) {
        const source = String(content || "");

        if (!/pm-xymatrix-table/.test(source)) {
            return source;
        }

        const tableRegex =
            /<table\b[^>]*class=["'][^"']*\bpm-xymatrix-table\b[^"']*["'][^>]*>[\s\S]*?<\/table>/gi;

        const tokens = [];

        const normalizeSequenceTableHtml = tableHtml =>
            String(tableHtml || "")
                .replace(
                    /margin\s*:\s*1rem\s+auto\s*;/i,
                    "margin:0;"
                )
                .replace(
                    /margin\s*:\s*1rem\s+0\.45rem\s*;/i,
                    "margin:0;"
                );

        const pushMathText = text => {
            const normalized = String(text || "")
                .replace(/\s+/g, " ")
                .trim();

            if (!normalized) {
                return;
            }
            
            /*
            * A connector between converted xymatrix tables will be placed
            * inside its own MathJax wrapper below. Remove the surrounding
            * TeX spacing commands now so the later legacy connector cleanup
            * does not replace HTML inside that MathJax wrapper.
            */
            const sequenceConnectorMatch = normalized.match(
                /^\\quad\s*\{\s*(:?=)\s*\}\s*\\quad$/i
            );

            if (sequenceConnectorMatch) {
                tokens.push({
                    type: "math",
                    core: sequenceConnectorMatch[1],
                    punctuation: ""
                });

                return;
            }

            /*
            * Preserve an explicit TeX gap between adjacent diagrams as a CSS
            * spacer rather than sending \hspace to MathJax.
            */
            const hspaceMatch = normalized.match(
                /^\\hspace\*?\s*\{\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:pt|pc|in|bp|cm|mm|dd|cc|sp|em|ex))\s*\}$/i
            );

            if (hspaceMatch) {
                tokens.push({
                    type: "spacer",
                    width: hspaceMatch[1]
                });
                return;
            }

            const punctuationMatch =
                normalized.match(/^(.*?)([.,;:!?])$/);

            const core = punctuationMatch
                ? punctuationMatch[1].trim()
                : normalized;

            const trailingPunctuation = punctuationMatch
                ? punctuationMatch[2]
                : "";

            if (core) {
                tokens.push({
                    type: "math",
                    core,
                    punctuation: trailingPunctuation
                });
                return;
            }

            /*
            * A punctuation-only fragment after the final table belongs
            * to that table:
            *
            *   table = table .
            *
            * It must not become the first character of the next paragraph.
            */
            if (trailingPunctuation) {
                const lastToken = tokens[tokens.length - 1];

                if (lastToken?.type === "table") {
                    lastToken.punctuation =
                        `${lastToken.punctuation || ""}${trailingPunctuation}`;
                    return;
                }

                tokens.push({
                    type: "punctuation",
                    text: trailingPunctuation
                });
            }
        };

        let cursor = 0;
        let match;

        while ((match = tableRegex.exec(source)) !== null) {
            pushMathText(source.slice(cursor, match.index));

            tokens.push({
                type: "table",
                html: match[0],
                punctuation: ""
            });

            cursor = match.index + match[0].length;
        }

        pushMathText(source.slice(cursor));

        const tableCount =
            tokens.filter(token => token.type === "table").length;

        const hasConnector =
            tokens.some(token => token.type === "math");

        const hasExplicitSpacer =
            tokens.some(token => token.type === "spacer");

        const hasAttachedPunctuation =
            tokens.some(
                token =>
                    token.type === "table"
                    && Boolean(token.punctuation)
            );

        const needsSequenceLayout =
            tableCount > 1
            || hasConnector
            || hasAttachedPunctuation
            || hasExplicitSpacer;

        const renderToken = token => {
            if (token.type === "math") {
                return `
                    <span
                        class="pm-xymatrix-connector"
                        style="
                            display:inline-block;
                            margin:0;
                            white-space:nowrap;
                        "
                    >\\({}${token.core}{}\\)${token.punctuation || ""}</span>
                `;
            }

            if (token.type === "spacer") {
                return `
                    <span
                        aria-hidden="true"
                        style="
                            display:block;
                            flex:0 0 ${token.width};
                            width:${token.width};
                            height:1px;
                        "
                    ></span>
                `;
            }

            if (token.type === "table") {
                const tableHtml = needsSequenceLayout
                    ? normalizeSequenceTableHtml(token.html)
                    : token.html;

                if (!token.punctuation) {
                    return tableHtml;
                }

                return `
                    <div style="
                        display:inline-flex;
                        align-items:center;
                        white-space:nowrap;
                    ">
                        ${tableHtml}
                        <span style="margin-left:0.08rem;">
                            ${token.punctuation}
                        </span>
                    </div>
                `;
            }

            return token.text || "";
        };

        const renderedTokens =
            tokens.map(renderToken).join("");

        if (!needsSequenceLayout) {
            return renderedTokens;
        }

        return `
            <div
                class="pm-xymatrix-sequence"
                style="
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    flex-wrap:wrap;
                    gap:${hasExplicitSpacer ? "0" : "0.55rem"};
                    margin:1rem 0;
                "
            >
                ${renderedTokens}
            </div>
        `;
    }

    function unwrapConvertedXyMatrixMathWrappers(value) {
        let output = String(value || "");

        const tablePattern =
            '<table\\b[^>]*class=["\'][^"\']*\\bpm-xymatrix-table\\b[^"\']*["\'][^>]*>[\\s\\S]*?<\\/table>';

        const containsConvertedXyMatrixTable = inner =>
            /\bpm-xymatrix-table\b/i.test(
                String(inner || "")
            );

        /*
        * Match each complete equation wrapper first.
        *
        * Only unwrap it when that exact wrapper contains a converted
        * xymatrix table. This prevents the regex from crossing an earlier
        * closing delimiter while searching for a table farther down.
        */
        output = output.replace(
            /\\begin\{(equation\*?)\}([\s\S]*?)\\end\{\1\}/gi,
            function(fullMatch, environmentName, inner) {
                if (!containsConvertedXyMatrixTable(inner)) {
                    return fullMatch;
                }

                return renderMixedXyMatrixWrapperContent(inner);
            }
        );

        /*
        * Apply the same nearest-wrapper rule to $$ ... $$ displays.
        */
        output = output.replace(
            /\$\$([\s\S]*?)\$\$/g,
            function(fullMatch, inner) {
                if (!containsConvertedXyMatrixTable(inner)) {
                    return fullMatch;
                }

                return renderMixedXyMatrixWrapperContent(inner);
            }
        );

        /*
        * Apply the same nearest-wrapper rule to \[ ... \] displays.
        */
        output = output.replace(
            /\\\[([\s\S]*?)\\\]/g,
            function(fullMatch, inner) {
                if (!containsConvertedXyMatrixTable(inner)) {
                    return fullMatch;
                }

                return renderMixedXyMatrixWrapperContent(inner);
            }
        );

        /*
        * Inline dollar wrappers must contain only one converted table,
        * plus optional punctuation. Do not search broadly through prose
        * for a later xymatrix table.
        */
        output = output.replace(
            new RegExp(
                `(^|[^\\\\$])\\$(?!\\$)\\s*(${tablePattern})\\s*([,.;:!?]?)\\s*\\$(?!\\$)`,
                "gi"
            ),
            (_, prefix, tableHtml, punctuation) =>
                `${prefix}${tableHtml}${punctuation || ""}`
        );

        /*
        * Same narrow rule for \( ... \).
        */
        output = output.replace(
            new RegExp(
                `\\\\\\(\\s*(${tablePattern})\\s*([,.;:!?]?)\\s*\\\\\\)`,
                "gi"
            ),
            (_, tableHtml, punctuation) =>
                `${tableHtml}${punctuation || ""}`
        );

        return output;
    }

    function makeUnsupportedXyMatrixPlaceholder(body) {
        return `
            <div class="mathjax-diagnostic-ignore" style="margin:1rem 0; padding:0.75rem; border:1px dashed #cbd5e1; border-radius:6px; background:#f8fafc; color:#64748b;">
                Unsupported xymatrix diagram:
                <code>${escapeHtmlForMathCell(body)}</code>
            </div>
        `;
    }

    function normalizeLatexImageArtifacts(tex) {
        if (!tex) return "";

        let output = String(tex || "");

        // Remove figure wrappers but keep their contents.
        output = output.replace(/\\begin\{figure\*?\}(?:\[[^\]]*\])?/gi, "");
        output = output.replace(/\\end\{figure\*?\}/gi, "");

        // LaTeX layout commands around old EPS images.
        output = output.replace(/\\centering\b/gi, "");

        // \scalebox{0.8}{\includegraphics{file.eps}}
        output = output.replace(
            /\\scalebox\{[^{}]*\}\s*\{\s*\\includegraphics(?:\[[^\]]*\])?\s*\{([^{}]*)\}\s*\}/gi,
            function(_, filename) {
                return makeLatexImagePlaceholder(filename);
            }
        );

        // Plain \includegraphics[scale=...]{file.eps} or \includegraphics{file.eps}
        output = output.replace(
            /\\includegraphics(?:\[[^\]]*\])?\s*\{([^{}]*)\}/gi,
            function(_, filename) {
                return makeLatexImagePlaceholder(filename);
            }
        );

        // Preserve captions as readable prose.
        output = output.replace(
            /\\caption\{([^{}]*)\}/gi,
            function(_, caption) {
                const cleanCaption = cleanLatexImageLabelText(caption);

                if (!cleanCaption) {
                    return "";
                }

                return `
                    <div class="pm-latex-image-caption mathjax-diagnostic-ignore" style="text-align:center; color:#64748b; font-size:0.92rem; margin:0.25rem 0 1rem;">
                        <em>${escapeHtmlForMathCell(cleanCaption)}</em>
                    </div>
                `;
            }
        );

        return output;
    }


    function makeLatexImagePlaceholder(filename) {
        const cleanFilename = cleanLatexImageLabelText(filename);

        const label = cleanFilename
            ? `Image placeholder: ${escapeHtmlForMathCell(cleanFilename)}`
            : "Image placeholder";

        return `
            <div class="pm-latex-image-placeholder mathjax-diagnostic-ignore" style="margin:1rem auto; padding:0.75rem; max-width:28rem; border:1px dashed #cbd5e1; border-radius:6px; background:#f8fafc; color:#64748b; text-align:center;">
                <em>[${label}]</em>
            </div>
        `;
    }

    function cleanLatexImageLabelText(value) {
        return String(value || "")
            // If the backend autolinker already linked text inside an image filename/caption,
            // keep only the visible linked text.
            .replace(/<a\b[^>]*>([\s\S]*?)<\/a>/gi, "$1")

            // Remove any other accidental HTML tags from placeholder labels.
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

    function convertSimpleDisplayMatricesToHtml(tex) {
        if (!tex) return "";

        let output = String(tex || "");

        // Display matrix environments with optional prefix/suffix:
        // \[ A=\begin{pmatrix} ... \end{pmatrix}. \]
        // Important: prefix/suffix must not cross a display boundary.
        output = output.replace(
            /\\\[\s*((?:(?!\\\])[\s\S])*?)\\begin\{(pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix)\}([\s\S]*?)\\end\{\2\}\s*((?:(?!\\\])[\s\S])*?)\\\]/gi,
            function(_, prefix, envName, body, suffix) {
                if (/\\begin\{(?:pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix|array)\}/i.test(suffix || "")) {
                    return _;
                }

                return buildDisplayMatrixHtmlWithAffixes(envName, prefix, body, suffix);
            }
        );

        // Display array environments with optional prefix/suffix:
        // \[ \pi=\begin{array}{ccc} ... \end{array} \]
        output = output.replace(
            /\\\[\s*((?:(?!\\\])[\s\S])*?)\\begin\{array\}\{([^{}]*)\}([\s\S]*?)\\end\{array\}\s*((?:(?!\\\])[\s\S])*?)\\\]/gi,
            function(_, prefix, columnSpec, body, suffix) {
                if (/\\begin\{(?:pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix|array)\}/i.test(suffix || "")) {
                    return _;
                }

                return buildDisplayMatrixHtmlWithAffixes("array", prefix, body, suffix);
            }
        );

        return output;
    }

    function convertRemainingMatrixMathSequencesToHtml(tex) {
        if (!tex) return "";

        let output = String(tex || "");

        // Remaining display expressions containing one or more matrices.
        //
        // The earlier display-affix converter handles the common single-matrix
        // case. This pass handles expressions such as:
        //
        // \[
        //   \begin{pmatrix} A & O \\ O & B \end{pmatrix}
        //   =
        //   \begin{pmatrix} 3 & -1 & 0 & 0 \\ ... \end{pmatrix}
        // \]
        output = output.replace(
            /\\\[([\s\S]*?)\\\]/g,
            function(fullMatch, body) {
                if (!containsSimpleMatrixEnvironment(body)) {
                    return fullMatch;
                }

                return buildMatrixMathSequenceHtml(body, true);
            }
        );

        // Explicit inline MathJax delimiters:
        // \( ... \)
        output = output.replace(
            /\\\(([\s\S]*?)\\\)/g,
            function(fullMatch, body) {
                if (!containsSimpleMatrixEnvironment(body)) {
                    return fullMatch;
                }

                return buildMatrixMathSequenceHtml(body, false);
            }
        );

        // Legacy single-dollar inline math:
        // $ ... $
        //
        // Dollar-display math has already been normalized earlier, so this
        // intentionally handles only remaining single-dollar pairs.
        output = output.replace(
            /(^|[^\\$])\$((?:\\.|[^$])*?)\$/g,
            function(fullMatch, leadingCharacter, body) {
                if (!containsSimpleMatrixEnvironment(body)) {
                    return fullMatch;
                }

                return (
                    leadingCharacter +
                    buildMatrixMathSequenceHtml(body, false)
                );
            }
        );

        return output;
    }


    function containsSimpleMatrixEnvironment(value) {
        return /\\begin\s*\{(?:pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix|array)\}/i
            .test(String(value || ""));
    }


    function buildMatrixMathSequenceHtml(body, isDisplay) {
        const source = String(body || "");

        const matrixPattern =
            /(?:\\left\s*(\(|\[|\||\\\{)\s*)?\\begin\s*\{(pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix|array)\}\s*(?:\{([^{}]*)\})?([\s\S]*?)\\end\s*\{\2\}(?:\s*\\right\s*(\.|\)|\]|\||\\\}))?/gi;

        const pieces = [];
        let cursor = 0;
        let match;

        while ((match = matrixPattern.exec(source)) !== null) {
            const mathBefore = source.slice(cursor, match.index);

            appendMatrixSequenceMathPiece(pieces, mathBefore);

            const explicitLeft = match[1] || "";
            const envName = match[2];
            const arraySpec = match[3] || "";
            const matrixBody = match[4];
            const explicitRight = match[5] || "";

            const hasExplicitLeft = explicitLeft.length > 0;
            const hasExplicitRight = explicitRight.length > 0;

            const delimiterOverride =
                (hasExplicitLeft || hasExplicitRight)
                    ? {
                        left: hasExplicitLeft
                            ? normalizeExplicitMatrixDelimiter(explicitLeft)
                            : "",
                        right: hasExplicitRight
                            ? normalizeExplicitMatrixDelimiter(explicitRight)
                            : ""
                    }
                    : null;

            const matrixHtml = buildMatrixEnvironmentHtml(
                envName,
                matrixBody,
                delimiterOverride,
                arraySpec
            );

            let nextCursor = matrixPattern.lastIndex;

            // Attach an immediately following exponent to the matrix itself:
            //
            //   \begin{pmatrix} ... \end{pmatrix}^n
            //   \begin{pmatrix} ... \end{pmatrix}^{n+1}
            const exponentMatch = source.slice(nextCursor).match(
                /^\s*\^\s*(?:\{([^{}]+)\}|([A-Za-z0-9]+))/
            );

            if (exponentMatch) {
                const exponent =
                    exponentMatch[1] ||
                    exponentMatch[2] ||
                    "";

                pieces.push(`
                    <span class="pm-matrix-with-exponent" style="
                        display:inline-flex;
                        align-items:flex-start;
                        vertical-align:middle;
                        white-space:nowrap;
                    ">
                        ${matrixHtml}

                        <span style="
                            display:inline-block;
                            margin-left:0.06rem;
                            margin-top:-0.12rem;
                            font-size:0.78em;
                            line-height:1;
                        ">
                            \\(${escapeHtmlForMathCell(exponent)}\\)
                        </span>
                    </span>
                `);

                nextCursor += exponentMatch[0].length;
            } else {
                pieces.push(matrixHtml);
            }

            cursor = nextCursor;
        }

        appendMatrixSequenceMathPiece(
            pieces,
            source.slice(cursor)
        );

        if (pieces.length === 0) {
            return isDisplay
                ? `\\[${source}\\]`
                : `\\(${source}\\)`;
        }

        const wrapperTag = isDisplay ? "div" : "span";
        const wrapperClass = isDisplay
            ? "pm-matrix-display pm-matrix-sequence tex2jax_process"
            : "pm-matrix-inline pm-matrix-sequence tex2jax_process";

        const wrapperStyle = isDisplay
            ? `
                display:flex;
                align-items:center;
                justify-content:center;
                flex-wrap:wrap;
                gap:0.25rem;
                margin:1rem 0;
                text-align:center;
            `
            : `
                display:inline-flex;
                align-items:center;
                flex-wrap:nowrap;
                gap:0.18rem;
                vertical-align:middle;
                white-space:nowrap;
            `;

        return `
            <${wrapperTag} class="${wrapperClass}" style="${wrapperStyle}">
                ${pieces.join("")}
            </${wrapperTag}>
        `;
    }

    function normalizeExplicitMatrixDelimiter(delimiter) {
        const value = String(delimiter || "").trim();

        if (value === "\\{") {
            return "{";
        }

        if (value === "\\}") {
            return "}";
        }

        if (value === ".") {
            return "";
        }

        return value;
    }

    function appendMatrixSequenceMathPiece(pieces, value) {
        const cleanValue = normalizeMatrixSequenceMath(value);

        if (!cleanValue) {
            return;
        }

        if (/^[.,;:]+$/.test(cleanValue)) {
            pieces.push(
                `<span style="display:inline-block;">${escapeHtmlForMathCell(cleanValue)}</span>`
            );
            return;
        }

        pieces.push(
            `<span style="display:inline-block; vertical-align:middle;">\\(${escapeHtmlForMathCell(cleanValue)}\\)</span>`
        );
    }


    function normalizeMatrixSequenceMath(value) {
        return normalizeEqnarrayHtmlArtifacts(value)
            .replace(/\s+/g, " ")

            // Plain prose words inside math mode lose ordinary whitespace.
            // Put "where" back into MathJax text mode and add explicit spacing.
            .replace(
                /(^|[.,;:])\s*where\s*/gi,
                function(_, punctuation) {
                    return `${punctuation}\\;\\text{where}\\;`;
                }
            )

            .trim();
    }

    function buildDisplayMatrixHtml(envName, body, trailingPunctuation = "") {
        const matrixHtml = buildMatrixEnvironmentHtml(envName, body);
        const punctuationHtml = trailingPunctuation
            ? `<span style="display:inline-block; vertical-align:middle; margin-left:0.08rem;">${escapeHtmlForMathCell(trailingPunctuation)}</span>`
            : "";

        return `
            <div class="pm-matrix-display tex2jax_process" style="text-align:center; margin:1rem 0;">
                ${matrixHtml}${punctuationHtml}
            </div>
        `;
    }

    function buildDisplayMatrixHtmlWithAffixes(envName, prefix, body, suffix = "") {
        const affixInfo = extractMatrixAffixDelimiters(prefix, suffix, envName);

        const cleanPrefix = normalizeDetachedMatrixAffix(
            normalizeMatrixAffix(affixInfo.prefix)
        );

        const cleanSuffix = normalizeDetachedMatrixAffix(
            normalizeMatrixAffix(affixInfo.suffix)
        );

        const prefixHtml = cleanPrefix
            ? `<span style="display:inline-block; vertical-align:middle; margin-right:0.25rem;">\\(${escapeHtmlForMathCell(cleanPrefix)}\\)</span>`
            : "";

        let suffixHtml = "";

        if (cleanSuffix) {
            if (/^[.,;:]$/.test(cleanSuffix)) {
                suffixHtml = `<span style="display:inline-block; vertical-align:middle; margin-left:0.08rem;">${escapeHtmlForMathCell(cleanSuffix)}</span>`;
            } else {
                suffixHtml = `<span style="display:inline-block; vertical-align:middle; margin-left:0.25rem;">\\(${escapeHtmlForMathCell(cleanSuffix)}\\)</span>`;
            }
        }

        return `
            <div class="pm-matrix-display tex2jax_process" style="text-align:center; margin:1rem 0;">
                ${prefixHtml}${buildMatrixEnvironmentHtml(envName, body, affixInfo.delimiters)}${suffixHtml}
            </div>
        `;
    }

    function extractMatrixAffixDelimiters(prefix, suffix, envName) {
        let cleanPrefix = String(prefix || "");
        let cleanSuffix = String(suffix || "");

        let delimiters = getMatrixDelimiters(envName);

        const leftMatch = cleanPrefix.match(
            /\\left\s*(\.|\(|\[|\{|\||\\\{|\\lbrace|\\vert|\\lvert|\\Vert|\\lVert)\s*$/i
        );

        const rightMatch = cleanSuffix.match(
            /^\s*\\right\s*(\.|\)|\]|\}|\||\\\}|\\rbrace|\\vert|\\rvert|\\Vert|\\rVert)/i
        );

        if (leftMatch && rightMatch) {
            const leftDelimiter = latexMatrixDelimiterTokenToText(leftMatch[1], "left");
            const rightDelimiter = latexMatrixDelimiterTokenToText(rightMatch[1], "right");

            delimiters = {
                left: leftDelimiter,
                right: rightDelimiter
            };

            cleanPrefix = cleanPrefix.slice(0, leftMatch.index);
            cleanSuffix = cleanSuffix.slice(rightMatch[0].length);
        }

        return {
            prefix: cleanPrefix,
            suffix: cleanSuffix,
            delimiters
        };
    }

    function normalizeDetachedMatrixAffix(value) {
        return String(value || "")
            // Opening delimiters that no longer have a matching \right
            // in the same MathJax expression.
            .replace(/\\left\s*\\\{/g, "\\lbrace")
            .replace(/\\left\s*\\\[/g, "\\lbrack")
            .replace(/\\left\s*\(/g, "(")
            .replace(/\\left\s*\./g, "")

            // Closing or middle delimiters that no longer have a matching
            // \left in the same MathJax expression.
            .replace(/\\right\s*\\\}/g, "\\rbrace")
            .replace(/\\right\s*\\\]/g, "\\rbrack")
            .replace(/\\right\s*\)/g, ")")
            .replace(/\\right\s*\|/g, "\\mid")
            .replace(/\\right\s*\\vert/g, "\\mid")
            .replace(/\\right\s*\./g, "");
    }

    function latexMatrixDelimiterTokenToText(token, side = "left") {
        const clean = String(token || "").trim();

        if (!clean || clean === ".") {
            return "";
        }

        if (clean === "(" || clean === "\\(") {
            return "(";
        }

        if (clean === ")" || clean === "\\)") {
            return ")";
        }

        if (clean === "[" || clean === "\\[") {
            return "[";
        }

        if (clean === "]" || clean === "\\]") {
            return "]";
        }

        if (
            clean === "{" ||
            clean === "\\{" ||
            clean === "\\lbrace"
        ) {
            return "{";
        }

        if (
            clean === "}" ||
            clean === "\\}" ||
            clean === "\\rbrace"
        ) {
            return "}";
        }

        if (
            clean === "|" ||
            clean === "\\vert" ||
            clean === "\\lvert" ||
            clean === "\\rvert"
        ) {
            return "|";
        }

        if (
            clean === "\\Vert" ||
            clean === "\\lVert" ||
            clean === "\\rVert"
        ) {
            return "‖";
        }

        return side === "left" ? "" : "";
    }

    function normalizeMatrixAffix(value) {
        return normalizeEqnarrayHtmlArtifacts(value)
            .replace(/\s+/g, " ")
            .trim();
    }

    function renderMatrixDelimiter(delimiter, side = "left") {
        if (!delimiter) {
            return "";
        }

        const cleanDelimiter = String(delimiter || "");
        const cleanSide = side === "right" ? "right" : "left";

        const wrapperStyle = `
            align-self:stretch;
            display:flex;
            align-items:stretch;
            justify-content:center;
            flex:0 0 auto;
            width:0.88rem;
            color:currentColor;
        `;

        if (cleanDelimiter === "(" || cleanDelimiter === ")") {
            const path =
                cleanSide === "left"
                    ? "M24 2 C8 18 8 82 24 98"
                    : "M6 2 C22 18 22 82 6 98";

            return `
                <span class="pm-matrix-delimiter pm-matrix-paren-${cleanSide}" style="${wrapperStyle}">
                    <svg viewBox="0 0 30 100" preserveAspectRatio="none" style="display:block; width:100%; height:100%; min-height:2.4rem;">
                        <path d="${path}" stroke="currentColor" stroke-width="4.2" fill="none" stroke-linecap="round"></path>
                    </svg>
                </span>
            `;
        }

        if (cleanDelimiter === "[" || cleanDelimiter === "]") {
            const path =
                cleanSide === "left"
                    ? "M25 2 H8 V98 H25"
                    : "M5 2 H22 V98 H5";

            return `
                <span class="pm-matrix-delimiter pm-matrix-bracket-${cleanSide}" style="${wrapperStyle}">
                    <svg viewBox="0 0 30 100" preserveAspectRatio="none" style="display:block; width:100%; height:100%; min-height:2.4rem;">
                        <path d="${path}" stroke="currentColor" stroke-width="4" fill="none" stroke-linecap="square" stroke-linejoin="miter"></path>
                    </svg>
                </span>
            `;
        }

        if (cleanDelimiter === "{" || cleanDelimiter === "}") {
            const path =
                cleanSide === "left"
                    ? "M27 2 C14 2 15 22 15 32 C15 43 7 44 6 50 C7 56 15 57 15 68 C15 78 14 98 27 98"
                    : "M7 2 C20 2 19 22 19 32 C19 43 27 44 28 50 C27 56 19 57 19 68 C19 78 20 98 7 98";

            return `
                <span class="pm-matrix-delimiter pm-matrix-brace-${cleanSide}" style="${wrapperStyle}">
                    <svg viewBox="0 0 34 100" preserveAspectRatio="none" style="display:block; width:100%; height:100%; min-height:2.4rem;">
                        <path d="${path}" stroke="currentColor" stroke-width="3.4" fill="none" stroke-linecap="round"></path>
                    </svg>
                </span>
            `;
        }

        if (cleanDelimiter === "|") {
            return `
                <span class="pm-matrix-delimiter pm-matrix-vertical-${cleanSide}" style="${wrapperStyle}; width:0.36rem;">
                    <span style="display:block; height:100%; border-left:3px solid currentColor;"></span>
                </span>
            `;
        }

        if (cleanDelimiter === "‖") {
            return `
                <span class="pm-matrix-delimiter pm-matrix-double-vertical-${cleanSide}" style="${wrapperStyle}; width:0.50rem; gap:0.10rem;">
                    <span style="display:block; height:100%; border-left:2.4px solid currentColor;"></span>
                    <span style="display:block; height:100%; border-left:2.4px solid currentColor;"></span>
                </span>
            `;
        }

        return `<span style="${wrapperStyle}; align-items:center;">${escapeHtmlForMathCell(cleanDelimiter)}</span>`;
    }

    function buildMatrixEnvironmentHtml(envName, body, delimiterOverride = null, arraySpec = "") {
        const normalizedBody = normalizeEqnarrayHtmlArtifacts(body);

        const rows = splitMatrixBodyRows(normalizedBody)
            .map(splitEqnarrayCells)
            .filter(cells => cells.some(cell => cell.trim().length > 0));

        if (rows.length === 0) {
            return "";
        }

        const maxColumns = Math.max(...rows.map(cells => cells.length));
        const delimiters = delimiterOverride || getMatrixDelimiters(envName);

        const htmlCells = rows.map(cells => {
            const paddedCells = padEqnarrayCells(cells, maxColumns);

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
                    ">\\(${escapeHtmlForMathCell(cleanCell)}\\)</span>
                `;
            }).join("");
        }).join("");

        const leftDelimiter = renderMatrixDelimiter(delimiters.left, "left");
        const rightDelimiter = renderMatrixDelimiter(delimiters.right, "right");

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

        const slashRows = splitEqnarrayRows(normalized);

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
        return normalizeEqnarrayHtmlArtifacts(cell)
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

    function normalizeDisplayMathEnvironments(tex) {
        if (!tex) return "";

        /*
        * Math environments are already in math mode. Repair legacy source
        * that embeds another $...$ expression inside \text{...}:
        *
        *   \text{for all vectors $\vv \in \real^n$.}
        *
        * becomes:
        *
        *   \text{for all vectors }\vv \in \real^n\text{.}
        */
        const normalizeBody = body =>
            String(body || "").replace(
                /\\(?:text|mbox|textrm)\s*\{([^{}$]*?)\$([^$]+)\$([^{}$]*?)\}/gi,
                function (_, beforeText, mathBody, afterText) {
                    return (
                        (beforeText
                            ? `\\text{${beforeText}}`
                            : ""
                        ) +
                        String(mathBody || "").trim() +
                        (afterText
                            ? `\\text{${afterText}}`
                            : ""
                        )
                    );
                }
            );

        return String(tex)
            .replace(
                /\\begin\{displaymath\}([\s\S]*?)\\end\{displaymath\}/gi,
                (_, body) => `\\[${normalizeBody(body)}\\]`
            )
            .replace(
                /\\begin\{equation\*\}([\s\S]*?)\\end\{equation\*\}/gi,
                (_, body) => `\\[${normalizeBody(body)}\\]`
            )
            .replace(
                /\\begin\{equation\}([\s\S]*?)\\end\{equation\}/gi,
                (_, body) => `\\[${normalizeBody(body)}\\]`
            );
    }

    function normalizeDollarDisplayMath(tex) {
        if (!tex) return "";

        return String(tex || "").replace(
            /\$\$([\s\S]*?)\$\$/g,
            function(_, body) {
                return `\\[${body}\\]`;
            }
        );
    }

    function normalizePlaceholderImageLayouts(value) {
        const source = String(value || "");

        if (!source.includes("pm-latex-image-placeholder")) {
            return source;
        }

        const template = document.createElement("template");
        template.innerHTML = source;

        function isPlaceholderBlock(node) {
            if (
                !node
                || node.nodeType !== Node.ELEMENT_NODE
            ) {
                return false;
            }

            if (
                node.classList.contains(
                    "pm-latex-image-placeholder"
                )
            ) {
                return true;
            }

            /*
            * Accept a simple wrapper around one placeholder, but do not
            * treat a larger container holding several placeholders as
            * one image block.
            */
            return (
                node.querySelectorAll(
                    ".pm-latex-image-placeholder"
                ).length === 1
            );
        }

        function isEmptyParagraph(node) {
            return (
                node &&
                node.nodeType === Node.ELEMENT_NODE &&
                node.tagName === "P" &&
                !String(node.textContent || "").trim()
            );
        }

        function isPlaceholderArrow(node) {
            if (!node) {
                return false;
            }

            const text = String(
                node.nodeType === Node.TEXT_NODE
                    ? node.nodeValue
                    : node.textContent
            ).trim();

            return (
                (
                    node.nodeType === Node.ELEMENT_NODE
                    && node.classList.contains("pm-image-arrow")
                )
                || /\\raisebox\b/i.test(text)
                || /\\longleftrightarrow\b/i.test(text)
                || text.includes("↔")
            );
        }

        function isOnlyHfilParagraph(node) {
            return (
                node &&
                node.nodeType === Node.ELEMENT_NODE &&
                node.tagName === "P" &&
                /^\\hfil\s*$/i.test(String(node.textContent || "").trim())
            );
        }

        function isArrowParagraph(node) {
            const text = String(node?.textContent || "").trim();
            return (
                node &&
                node.nodeType === Node.ELEMENT_NODE &&
                node.tagName === "P" &&
                /\\raisebox/i.test(text) &&
                /\\longleftrightarrow/i.test(text)
            );
        }

        // Remove raw \hfil-only paragraphs.
        Array.from(template.content.querySelectorAll("p")).forEach(p => {
            if (isOnlyHfilParagraph(p)) {
                p.remove();
            }
        });

        // Convert raw \centerline{...} paragraph to a real centered caption.
        Array.from(template.content.querySelectorAll("p")).forEach(p => {
            const text = String(p.textContent || "");
            const match = text.match(/\\centerline\s*\{([\s\S]*?)\}/i);

            if (!match) return;

            const div = document.createElement("div");
            div.className = "math-center pm-image-caption";
            div.innerHTML = match[1];
            p.replaceWith(div);
        });

        // Convert raw arrow paragraph to a clean centered arrow.
        Array.from(template.content.querySelectorAll("p")).forEach(p => {
            if (!isArrowParagraph(p)) return;

            const div = document.createElement("div");
            div.className = "math-center pm-image-arrow";
            div.innerHTML = "\\(\\longleftrightarrow\\)";
            p.replaceWith(div);
        });

        // Wrap consecutive placeholder blocks into centered rows.
        const container = document.createElement("div");
        container.appendChild(template.content.cloneNode(true));

        function isIgnorablePlaceholderLayoutNode(node) {
            if (!node) {
                return false;
            }

            if (node.nodeType === Node.TEXT_NODE) {
                const text = String(node.nodeValue || "")
                    .replace(/\\(?:hfil|hfill)\b/gi, "")
                    .trim();

                return !text;
            }

            if (node.nodeType !== Node.ELEMENT_NODE) {
                return false;
            }

            if (isEmptyParagraph(node)) {
                return true;
            }

            const text = String(node.textContent || "")
                .replace(/\\(?:hfil|hfill)\b/gi, "")
                .trim();

            return (
                !text
                && !isPlaceholderBlock(node)
            );
        }

        function collectPlaceholderRuns(parent) {
            const nodes = Array.from(parent.childNodes);
            const runs = [];

            let current = [];

            function flush() {
                const placeholders =
                    current.filter(isPlaceholderBlock);

                if (placeholders.length >= 2) {
                    runs.push(current);
                }

                current = [];
            }

            nodes.forEach(node => {
                if (
                    isPlaceholderBlock(node)
                    || isIgnorablePlaceholderLayoutNode(node)
                ) {
                    current.push(node);
                    return;
                }

                flush();
            });

            flush();

            return runs;
        }

        function nextMeaningfulSibling(node) {
            let sibling = node?.nextSibling || null;

            while (
                sibling
                && isIgnorablePlaceholderLayoutNode(sibling)
            ) {
                sibling = sibling.nextSibling;
            }

            return sibling;
        }

        function groupPlaceholderArrowPairs(parent) {
            let node = parent.firstChild;

            while (node) {
                if (!isPlaceholderBlock(node)) {
                    node = node.nextSibling;
                    continue;
                }

                const arrow =
                    nextMeaningfulSibling(node);

                const rightPlaceholder =
                    nextMeaningfulSibling(arrow);

                if (
                    !isPlaceholderArrow(arrow)
                    || !isPlaceholderBlock(rightPlaceholder)
                ) {
                    node = node.nextSibling;
                    continue;
                }

                const nextNode =
                    rightPlaceholder.nextSibling;

                // Remember all nodes between the two images so leftover
                // empty paragraphs can be removed too.
                const consumedNodes = [];
                let consumedNode = node;

                while (consumedNode) {
                    consumedNodes.push(consumedNode);

                    if (consumedNode === rightPlaceholder) {
                        break;
                    }

                    consumedNode =
                        consumedNode.nextSibling;
                }

                const row =
                    document.createElement("div");

                row.className =
                    "pm-placeholder-row pm-placeholder-arrow-row";

                row.style.display = "grid";
                row.style.gridTemplateColumns =
                    "minmax(0, 1fr) auto minmax(0, 1fr)";
                row.style.alignItems = "center";
                row.style.gap = "1rem";
                row.style.margin = "1rem auto";
                row.style.maxWidth = "44rem";

                const leftItem =
                    document.createElement("div");

                leftItem.className =
                    "pm-placeholder-item";

                const rightItem =
                    document.createElement("div");

                rightItem.className =
                    "pm-placeholder-item";

                parent.insertBefore(row, node);

                leftItem.appendChild(node);
                row.appendChild(leftItem);

                row.appendChild(arrow);

                rightItem.appendChild(rightPlaceholder);
                row.appendChild(rightItem);

                consumedNodes.forEach(consumed => {
                    if (
                        consumed !== node
                        && consumed !== arrow
                        && consumed !== rightPlaceholder
                    ) {
                        consumed.remove();
                    }
                });

                node = nextNode;
            }
        }

        container
            .querySelectorAll(".math-center")
            .forEach(parent => {
                groupPlaceholderArrowPairs(parent);
            });

        const placeholderParents = [
            container,
            ...container.querySelectorAll(".math-center")
        ];

        placeholderParents.forEach(parent => {
            collectPlaceholderRuns(parent).forEach(run => {
                const placeholders =
                    run.filter(isPlaceholderBlock);

                /*
                * Build rows of at most two placeholders. This turns four
                * consecutive knot examples into two rows rather than one
                * oversized four-item row.
                */
                const rows = [];

                for (
                    let index = 0;
                    index < placeholders.length;
                    index += 2
                ) {
                    rows.push(
                        placeholders.slice(index, index + 2)
                    );
                }

                const firstNode = run[0];
                const insertionParent = firstNode.parentNode;

                if (!insertionParent) {
                    return;
                }

                rows.forEach(items => {
                    const row = document.createElement("div");

                    row.className = "pm-placeholder-row";
                    row.style.display = "flex";
                    row.style.justifyContent = "center";
                    row.style.alignItems = "center";
                    row.style.gap = "1rem";
                    row.style.flexWrap = "wrap";
                    row.style.margin = "1rem 0";

                    items.forEach(block => {
                        const item =
                            document.createElement("div");

                        item.className =
                            "pm-placeholder-item";

                        item.style.flex = "0 1 18rem";
                        item.appendChild(
                            block.cloneNode(true)
                        );

                        row.appendChild(item);
                    });

                    insertionParent.insertBefore(
                        row,
                        firstNode
                    );
                });

                run.forEach(node => node.remove());
            });
        });

        return container.innerHTML;
    }

    function convertPiecewiseArraysToHtml(tex) {
        if (!tex) return "";

        let output = String(tex);

        // A display block may contain more than one piecewise array:
        //
        // \[
        //   t_1 := \left\{ ... \right.
        //   \hspace{1cm}
        //   t_2 := \left\{ ... \right.
        // \]
        //
        // Process the complete display body and extract each array separately.
        output = output.replace(
            /\\\[([\s\S]*?)\\\]/gi,
            function(fullMatch, body) {
                if (!containsPiecewiseArray(body)) {
                    return fullMatch;
                }

                return buildPiecewiseDisplaySequenceHtml(body);
            }
        );

        // Legacy $$ ... $$ display form.
        output = output.replace(
            /\$\$([\s\S]*?)\$\$/gi,
            function(fullMatch, body) {
                if (!containsPiecewiseArray(body)) {
                    return fullMatch;
                }

                return buildPiecewiseDisplaySequenceHtml(body);
            }
        );

        // Inline-dollar cases environment.
        //
        // Some list items contain constructs such as:
        //
        //   Mode $= \begin{cases} ... \end{cases}$
        //
        // Promote the complete inline fragment into the HTML piecewise renderer.
        // Inline-dollar cases environment.
        output = output.replace(
            /\$([^$]*?)\\begin\s*\{cases\}([\s\S]*?)\\end\s*\{cases\}\s*\$/gi,
            function(_, prefix, body) {
                return buildPiecewiseArrayHtml(
                    prefix,
                    body,
                    { inline: true }
                );
            }
        );

        // Display-wrapped cases environment.
        output = output.replace(
            /\\\[\s*((?:(?!\\\])[\s\S])*?)\\begin\s*\{cases\}([\s\S]*?)\\end\s*\{cases\}\s*\\\]/gi,
            function(_, prefix, body) {
                return buildPiecewiseArrayHtml(prefix, body);
            }
        );

        // Legacy $$-wrapped cases environment.
        output = output.replace(
            /\$\$\s*([\s\S]*?)\\begin\s*\{cases\}([\s\S]*?)\\end\s*\{cases\}\s*\$\$/gi,
            function(_, prefix, body) {
                return buildPiecewiseArrayHtml(prefix, body);
            }
        );

        return output;
    }

    function containsPiecewiseArray(value) {
        /*
        * Only intercept genuinely one-sided piecewise arrays:
        *
        *   \left\{ \begin{array} ... \end{array} \right.
        *
        * Paired arrays ending in \right\} belong to the ordinary matrix
        * sequence renderer, which can draw matching scalable braces.
        */
        return /\\left\s*(?:\\?\{|\\lbrace)\s*\\begin\s*\{array\}\s*\{[^{}]*\}[\s\S]*?\\end\s*\{array\}\s*\\right\s*\./i
            .test(String(value || ""));
    }

    function buildPiecewiseDisplaySequenceHtml(displayBody) {
        const source = String(displayBody || "");

        const piecewisePattern =
            /\\left\s*(?:\\?\{|\\lbrace)\s*\\begin\s*\{array\}\s*\{([^{}]*)\}([\s\S]*?)\\end\s*\{array\}\s*\\right\s*\./gi;

        const pieces = [];
        let cursor = 0;
        let match;

        while ((match = piecewisePattern.exec(source)) !== null) {
            let prefix = source.slice(cursor, match.index);

            // Spacing commands between adjacent piecewise definitions should
            // become visual spacing between the generated HTML blocks.
            prefix = prefix
                .replace(/\\hspace\s*\{[^{}]*\}/gi, " ")
                .replace(/\\qquad\b/gi, " ")
                .replace(/\\quad\b/gi, " ")
                .trim();

            pieces.push(
                buildPiecewiseArrayHtml(
                    prefix,
                    match[2]
                )
            );

            cursor = piecewisePattern.lastIndex;
        }

        const trailingMath = source.slice(cursor).trim();

        if (trailingMath) {
            pieces.push(
                `<span style="display:inline-block; vertical-align:middle;">\\(${escapeHtmlForMathCell(trailingMath)}\\)</span>`
            );
        }

        if (pieces.length === 0) {
            return `\\[${source}\\]`;
        }

        return `
            <div class="pm-piecewise-sequence tex2jax_process" style="
                display:flex;
                align-items:center;
                justify-content:center;
                flex-wrap:wrap;
                gap:2rem;
                margin:1rem 0;
            ">
                ${pieces.join("")}
            </div>
        `;
    }

    function buildPiecewiseArrayHtml(prefix, body, options = {}) {
        const isInline = options.inline === true;
        const cleanPrefix = normalizePiecewiseMathCell(prefix);
        const normalizedBody = normalizeEqnarrayHtmlArtifacts(body);

        const rows = splitEqnarrayRows(normalizedBody)
            .map(splitEqnarrayCells)
            .filter(cells => cells.some(cell => cell.trim().length > 0));

        if (rows.length === 0) {
            return cleanPrefix ? `\\[${cleanPrefix}\\]` : "";
        }

        const rowHtml = rows.map(cells => {
            const leftCell = normalizePiecewiseMathCell(cells[0] || "");
            const rightCell = normalizePiecewiseMathCell(
                cells.slice(1).join(" ") || ""
            );

            return `
                <tr>
                    <td style="
                        padding:0.12rem 0.35rem;
                        text-align:left;
                        white-space:nowrap;
                        vertical-align:middle;
                    ">\\(${escapeHtmlForMathCell(leftCell)}\\)</td>

                    <td style="
                        padding:0.12rem 0.35rem;
                        text-align:left;
                        white-space:nowrap;
                        vertical-align:middle;
                    ">
                        ${buildPiecewiseConditionHtml(rightCell)}
                    </td>
                </tr>
            `;
        }).join("");

        const prefixHtml = cleanPrefix
            ? `<span style="
                    display:inline-flex;
                    align-items:center;
                    align-self:center;
                    margin-right:0.18rem;
                ">\\(${escapeHtmlForMathCell(cleanPrefix)}\\)</span>`
            : "";

        if (isInline) {
            const braceHtml = renderMatrixDelimiter("{", "left");

            return `
                <span
                    class="pm-piecewise-block pm-piecewise-inline tex2jax_process"
                    style="
                        display:inline-flex;
                        align-items:center;
                        vertical-align:middle;
                        margin-left:0.22rem;
                        margin-top:0.10rem;
                        margin-bottom:0.10rem;
                        white-space:nowrap;
                    "
                >
                    ${cleanPrefix
                        ? `
                            <span style="
                                display:inline-flex;
                                align-items:center;
                                margin-right:0.16rem;
                                white-space:nowrap;
                            ">
                                \\(${escapeHtmlForMathCell(cleanPrefix)}\\)
                            </span>
                        `
                        : ""
                    }

                    <span style="
                        display:inline-flex;
                        align-items:stretch;
                        align-self:stretch;
                        vertical-align:middle;
                        gap:0.06rem;
                    ">
                        ${braceHtml}

                        <table style="
                            display:inline-table;
                            align-self:center;
                            vertical-align:middle;
                            border-collapse:collapse;
                            text-align:left;
                        ">
                            ${rowHtml}
                        </table>
                    </span>
                </span>
            `;
        }

        return `
            <div
                class="pm-piecewise-block tex2jax_process"
                style="
                    display:flex;
                    align-items:stretch;
                    justify-content:center;
                    margin:1rem 0;
                "
            >
                ${prefixHtml}

                <span style="
                    display:inline-flex;
                    align-items:stretch;
                    align-self:stretch;
                    vertical-align:middle;
                    margin-right:0.10rem;
                ">
                    ${renderMatrixDelimiter("{", "left")}
                </span>

                <table style="
                    display:inline-table;
                    vertical-align:middle;
                    border-collapse:collapse;
                    text-align:left;
                ">
                    ${rowHtml}
                </table>
            </div>
        `;
    }

    function buildPiecewiseConditionHtml(value) {
        let condition = String(value || "").trim();

        // Accept either the original TeX wrappers or plain prose left behind
        // by earlier normalization.
        condition = condition
        // Wrapper contains both prose and the following math:
        // \mbox{if \gamma>1}
        // \text{when x\le r}
        .replace(
            /^\\(?:mbox|text|textrm)\{\s*(if|when)\s+([\s\S]*?)\s*\}$/i,
            "$1 $2"
        )

        // Wrapper contains only prose:
        // \mbox{otherwise}
        .replace(
            /^\\(?:mbox|text|textrm)\{\s*(otherwise\.?)\s*\}$/i,
            "$1"
        )

        // Prose wrapper followed by math outside the braces:
        // \mbox{if }\gamma>1
        .replace(
            /^\\(?:mbox|text|textrm)\{\s*(if|when)\s*\}\s*/i,
            "$1 "
        )
        .replace(
            /^\\(?:mbox|text|textrm)\{\s*(otherwise\.?)\s*\}\s*/i,
            "$1 "
        )
        .trim();

        const proseMatch = condition.match(
            /^(if|when|otherwise\.?)\b\s*(.*)$/i
        );

        if (!proseMatch) {
            return `\\(${escapeHtmlForMathCell(condition)}\\)`;
        }

        const prose = proseMatch[1];
        const remainingMath = proseMatch[2].trim();

        const proseHtml = `<span style="font-style:normal;">${escapeHtmlForMathCell(prose)}</span>`;

        if (!remainingMath) {
            return proseHtml;
        }

        return `
            <span style="
                display:inline-flex;
                align-items:baseline;
                column-gap:0.45rem;
                white-space:nowrap;
            ">
                ${proseHtml}

                <span style="display:inline-block;">
                    \\(${escapeHtmlForMathCell(remainingMath)}\\)
                </span>
            </span>
        `;
    }

    function normalizePiecewiseMathCell(value) {
        return normalizeEqnarrayHtmlArtifacts(value)
            .replace(/\\textrm\{([^{}]*)\}/gi, "\\text{$1}")
            .replace(/\\mbox\{([^{}]*)\}/gi, "\\text{$1}")
            .replace(/\s+/g, " ")
            .trim();
    }

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

    function normalizeUrlMacros(value) {
        const source = String(value || "");

        if (!/\\url\s*\{/i.test(source)) {
            return source;
        }

        return source.replace(
            /\\url\s*\{([^{}]+)\}/gi,
            function (_, rawUrl) {
                const url = String(rawUrl || "").trim();

                if (!url) {
                    return "";
                }

                // Only create links for ordinary web URLs.
                if (!/^https?:\/\//i.test(url)) {
                    return url;
                }

                const anchor = document.createElement("a");

                anchor.href = url;
                anchor.textContent = url;
                anchor.className = "pm-external-url";
                anchor.target = "_blank";
                anchor.rel = "noopener noreferrer";

                return anchor.outerHTML;
            }
        );
    }

    function normalizeTextColorMacros(value) {
        const source = String(value || "");

        if (!/\\textcolor\s*\{/i.test(source)) {
            return source;
        }

        const supportedColors = new Set([
            "red",
            "blue",
            "green",
            "magenta"
        ]);

        return source.replace(
            /\\textcolor\s*\{\s*(?:<a\b[^>]*>\s*)?([a-z]+)(?:\s*<\/a>)?\s*\}\s*\{([^{}]*)\}/gi,
            function (original, rawColor, content) {
                const color =
                    String(rawColor || "").trim().toLowerCase();

                if (!supportedColors.has(color)) {
                    return original;
                }

                return `
                    <span
                        class="pm-textcolor pm-textcolor-${color} tex2jax_process"
                    >${content}</span>
                `;
            }
        );
    }

    function protectEqnarrayEnvironments(value) {
        const protectedBlocks = [];
        let output = String(value || "");

        output = output.replace(
            /\\begin\{eqnarray\*?\}[\s\S]*?\\end\{eqnarray\*?\}/gi,
            function (block) {
                const token = `@@PM_EQNARRAY_BLOCK_${protectedBlocks.length}@@`;
                protectedBlocks.push(block);
                return token;
            }
        );

        return {
            text: output,
            blocks: protectedBlocks
        };
    }


    function restoreEqnarrayEnvironments(value, protectedBlocks) {
        let output = String(value || "");

        (protectedBlocks || []).forEach(function (block, index) {
            const token = `@@PM_EQNARRAY_BLOCK_${index}@@`;
            output = output.replace(token, block);
        });

        return output;
    }

    function normalizeLegacyRomanList(value) {
        const source = String(value || "");

        if (
            !source.includes("math-generic-list")
            || !source.includes("\\roman")
            || !source.includes("\\addtocounter")
        ) {
            return source;
        }

        const template = document.createElement("template");
        template.innerHTML = source;

        template.content
            .querySelectorAll("ol.math-generic-list")
            .forEach(list => {
                const firstItem = Array.from(list.children)
                    .find(element =>
                        element.tagName === "LI"
                    );

                if (!firstItem) {
                    return;
                }

                const firstItemText =
                    String(firstItem.textContent || "");

                if (
                    !firstItemText.includes("\\roman")
                    || !firstItemText.includes("\\addtocounter")
                ) {
                    return;
                }

                // The backend turned the legacy list-label definition into
                // a bogus first list item. Remove it and style the remaining
                // eight real items as lower-Roman numerals.
                firstItem.remove();

                list.classList.add("pm-roman-list");
                list.setAttribute("type", "i");
                list.style.listStyleType = "lower-roman";
            });

        return template.innerHTML;
    }

    function preventInlineMathPunctuationWrap(value) {
        let output = String(value || "");

        // MathJax inline form:
        //   \(x\). -> <span ...>\(x\).</span>
        output = output.replace(
            /(\\\((?:[^\\]|\\(?!\)))*?\\\))([.,;:!?])/g,
            function (_, math, punctuation) {
                return `
                    <span
                        class="pm-inline-math-punctuation"
                        style="white-space:nowrap;"
                    >${math}${punctuation}</span>
                `;
            }
        );

        /*
        * Process every legitimate single-dollar expression from left to right,
        * even when it has no trailing punctuation.
        *
        * Making punctuation optional prevents the closing dollar of one
        * expression from being mistaken for the opening dollar of the next:
        *
        *   $u\leftarrow v$ ($:=v\to u$),
        */
        output = output.replace(
            /(?<!\\)(?<!\$)(\$(?!\$)(?:\\[^\r\n]|[^\\$\r\n])*?(?<!\\)\$(?!\$))([.,;:!?])?/g,
            function (_, math, punctuation) {
                if (!punctuation) {
                    return math;
                }

                return `
                    <span
                        class="pm-inline-math-punctuation"
                        style="white-space:nowrap;"
                    >${math}${punctuation}</span>
                `;
            }
        );

        return output;
    }

    function convertSimpleDeductionPstreeToHtml(tex) {
        if (!tex) {
            return "";
        }

        const renderNode = value => {
            const cleanValue =
                String(value || "").trim();

            return `
                <span
                    class="pm-pstree-node"
                    style="
                        display:inline-flex;
                        align-items:center;
                        justify-content:center;
                        min-width:2.2rem;
                        min-height:1.75rem;
                        padding:0.08rem 0.42rem;
                        border:1px solid #666;
                        border-radius:0.2rem;
                        background:#fff;
                    "
                >
                    \\(${escapeHtmlForMathCell(cleanValue)}\\)
                </span>
            `;
        };

        const renderTwoLeafTree = (
            rootLabel,
            middleLabel,
            leftLabel,
            rightLabel
        ) => {
            return `
                <div
                    class="pm-pstree-display tex2jax_process"
                    style="
                        display:flex;
                        justify-content:center;
                        margin:1rem 0;
                    "
                >
                    <div style="
                        display:flex;
                        flex-direction:column;
                        align-items:center;
                    ">
                        <div style="
                            display:flex;
                            justify-content:center;
                            align-items:center;
                            gap:2rem;
                        ">
                            ${renderNode(leftLabel)}
                            ${renderNode(rightLabel)}
                        </div>

                        <svg
                            aria-hidden="true"
                            width="150"
                            height="30"
                            viewBox="0 0 150 30"
                            style="
                                display:block;
                                overflow:visible;
                            "
                        >
                            <line
                                x1="36"
                                y1="0"
                                x2="75"
                                y2="30"
                                stroke="currentColor"
                                stroke-width="1.5"
                            ></line>

                            <line
                                x1="114"
                                y1="0"
                                x2="75"
                                y2="30"
                                stroke="currentColor"
                                stroke-width="1.5"
                            ></line>
                        </svg>

                        ${renderNode(middleLabel)}

                        <div
                            aria-hidden="true"
                            style="
                                height:1rem;
                                border-left:1.5px solid currentColor;
                            "
                        ></div>

                        ${renderNode(rootLabel)}
                    </div>
                </div>
            `;
        };

        const renderThreeLevelTree = (
            rootLabel,
            upperMiddleLabel,
            lowerMiddleLabel,
            leftLabel,
            rightLabel
        ) => {
            return `
                <div
                    class="pm-pstree-display tex2jax_process"
                    style="
                        display:flex;
                        justify-content:center;
                        margin:1rem 0;
                    "
                >
                    <div style="
                        display:flex;
                        flex-direction:column;
                        align-items:center;
                    ">
                        <div style="
                            display:flex;
                            justify-content:center;
                            align-items:center;
                            gap:2rem;
                        ">
                            ${renderNode(leftLabel)}
                            ${renderNode(rightLabel)}
                        </div>

                        <svg
                            aria-hidden="true"
                            width="150"
                            height="30"
                            viewBox="0 0 150 30"
                            style="
                                display:block;
                                overflow:visible;
                            "
                        >
                            <line
                                x1="36"
                                y1="0"
                                x2="75"
                                y2="30"
                                stroke="currentColor"
                                stroke-width="1.5"
                            ></line>

                            <line
                                x1="114"
                                y1="0"
                                x2="75"
                                y2="30"
                                stroke="currentColor"
                                stroke-width="1.5"
                            ></line>
                        </svg>

                        ${renderNode(lowerMiddleLabel)}

                        <div
                            aria-hidden="true"
                            style="
                                height:1rem;
                                border-left:1.5px solid currentColor;
                            "
                        ></div>

                        ${renderNode(upperMiddleLabel)}

                        <div
                            aria-hidden="true"
                            style="
                                height:1rem;
                                border-left:1.5px solid currentColor;
                            "
                        ></div>

                        ${renderNode(rootLabel)}
                    </div>
                </div>
            `;
        };

        let output = String(tex);

        /*
        * Narrow PSTree v1:
        *
        *   \pstree[...]
        *   {\Tr{Z}}{
        *       \pstree{\Tr{Y}}
        *       {\Tr{X_1}\Tr{X_2}}
        *   }
        *
        * Used by the "deduction" concept.
        */
        const simplePattern =
            /\\\[\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\Tr\s*\{([^{}]+)\}\s*\}\s*\{\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\Tr\s*\{([^{}]+)\}\s*\}\s*\{\s*\\Tr\s*\{([^{}]+)\}\s*\\Tr\s*\{([^{}]+)\}\s*\}\s*\}\s*\\\]/gi;

        output = output.replace(
            simplePattern,
            function (
                _match,
                rootLabel,
                middleLabel,
                leftLabel,
                rightLabel
            ) {
                return renderTwoLeafTree(
                    rootLabel,
                    middleLabel,
                    leftLabel,
                    rightLabel
                );
            }
        );

        /*
        * Narrow PSTree v2:
        *
        *   \pstree[...]{\Tc{...}~[...]{A\to A}}{
        *       \pstree{\TC~[...]{A}}{
        *           \pstree{\TC~[...]{A\land A}}{
        *               \TC~[...]{A}
        *               \TC~[...]{A}
        *           }
        *       }
        *   }
        *
        * Used by "derivations-in-natural-deduction".
        */
        const derivationPattern =
            /\\\[\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\Tc\s*\{[^{}]*\}\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\}\s*\{\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\TC\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\}\s*\{\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\TC\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\}\s*\{\s*\\TC\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\\TC\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\}\s*\}\s*\}\s*\\\]/gi;

        output = output.replace(
            derivationPattern,
            function (
                _match,
                rootLabel,
                upperMiddleLabel,
                lowerMiddleLabel,
                leftLabel,
                rightLabel
            ) {
                return renderThreeLevelTree(
                    rootLabel,
                    upperMiddleLabel,
                    lowerMiddleLabel,
                    leftLabel,
                    rightLabel
                );
            }
        );

        return output;
    }

    function convertRootedTreePstreeToHtml(tex) {
        if (!tex) {
            return "";
        }

        /*
        * Narrow converter for the PSTricks diagram used by "rooted-tree".
        *
        * Tree structure:
        *
        *                 a       b   c   d
        *                 |        \ | /
        *                 e   f   g   h
        *                  \ /     \ /
        *                   i       j
        *                    \     /
        *                       k
        */
        const rootedTreePattern =
            /\\\[\s*\\pstree[\s\S]*?\\Tc\s*\{3pt\}[\s\S]*?\{\s*\$k\$\s*\}[\s\S]*?\\TC[\s\S]*?\{\s*\$d\$\s*\}[\s\S]*?\\\]/gi;

        return String(tex).replace(
            rootedTreePattern,
            `
                <div
                    class="pm-rooted-tree-display mathjax-diagnostic-ignore"
                    style="
                        display:flex;
                        justify-content:center;
                        max-width:100%;
                        overflow-x:auto;
                        margin:1rem 0;
                    "
                >
                    <svg
                        role="img"
                        aria-label="Rooted tree with root k"
                        width="640"
                        height="335"
                        viewBox="0 0 640 335"
                        preserveAspectRatio="xMidYMid meet"
                        style="
                            display:block;
                            width:min(100%, 640px);
                            height:auto;
                            overflow:visible;
                        "
                    >
                        <g
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.5"
                            vector-effect="non-scaling-stroke"
                        >
                            <!-- root to first level -->
                            <line x1="320" y1="295" x2="220" y2="220"></line>
                            <line x1="320" y1="295" x2="420" y2="220"></line>

                            <!-- i branch -->
                            <line x1="220" y1="220" x2="150" y2="140"></line>
                            <line x1="220" y1="220" x2="270" y2="140"></line>
                            <line x1="150" y1="140" x2="100" y2="60"></line>

                            <!-- j branch -->
                            <line x1="420" y1="220" x2="370" y2="140"></line>
                            <line x1="420" y1="220" x2="500" y2="140"></line>

                            <!-- h children -->
                            <line x1="500" y1="140" x2="430" y2="60"></line>
                            <line x1="500" y1="140" x2="500" y2="60"></line>
                            <line x1="500" y1="140" x2="570" y2="60"></line>
                        </g>

                        <!-- filled ordinary vertices -->
                        <g fill="currentColor">
                            <circle cx="100" cy="60" r="4"></circle>
                            <circle cx="430" cy="60" r="4"></circle>
                            <circle cx="500" cy="60" r="4"></circle>
                            <circle cx="570" cy="60" r="4"></circle>

                            <circle cx="150" cy="140" r="4"></circle>
                            <circle cx="270" cy="140" r="4"></circle>
                            <circle cx="370" cy="140" r="4"></circle>
                            <circle cx="500" cy="140" r="4"></circle>

                            <circle cx="220" cy="220" r="4"></circle>
                            <circle cx="420" cy="220" r="4"></circle>
                        </g>

                        <!-- open root vertex -->
                        <circle
                            cx="320"
                            cy="295"
                            r="5"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.5"
                            vector-effect="non-scaling-stroke"
                        ></circle>

                        <!-- vertex labels -->
                        <g
                            fill="currentColor"
                            font-family="serif"
                            font-size="21"
                            font-style="italic"
                            dominant-baseline="middle"
                        >
                            <text x="112" y="60">a</text>

                            <text
                                x="418"
                                y="60"
                                text-anchor="end"
                            >b</text>

                            <text x="512" y="60">c</text>
                            <text x="582" y="60">d</text>

                            <text
                                x="138"
                                y="140"
                                text-anchor="end"
                            >e</text>

                            <text x="282" y="140">f</text>

                            <text
                                x="358"
                                y="140"
                                text-anchor="end"
                            >g</text>

                            <text x="512" y="140">h</text>

                            <text
                                x="208"
                                y="220"
                                text-anchor="end"
                            >i</text>

                            <text x="432" y="220">j</text>

                            <text
                                x="320"
                                y="318"
                                text-anchor="middle"
                            >k</text>
                        </g>
                    </svg>
                </div>
            `
        );
    }

    function cleanLaTeXEnvironments(tex) {
        if (!tex) return "";

        let clean = String(tex || "");

        const eqnarrayProtection = protectEqnarrayEnvironments(clean);
        clean = eqnarrayProtection.text;

        const verbProtection = protectLatexVerbCommands(clean);
        clean = verbProtection.text;

        clean = normalizeMboxTabularInsideMath(clean);
        clean = normalizeMboxHtmlTableInsideMath(clean);

        clean = normalizeHtmlTableMultirows(clean);

        clean = normalizeAlgorithmCodeBlocks(clean);

        const mboxProtection = protectMboxInsideMath(clean);
        clean = mboxProtection.text;

        // Remove TeX comment/separator paragraphs and standalone lines that
        // survived backend rendering.
        clean = clean.replace(
            /<p[^>]*>\s*(?:%+\s*)+<\/p>/gi,
            ""
        );

        /*
        * The backend can combine a commented legacy heading with live content
        * inside the same paragraph:
        *
        *   <p>%<strong>Differential identities..</strong>
        *   <h2>Differential identities</h2>
        *   Several properties ...
        *
        * Remove only the commented legacy heading. Preserve the paragraph and
        * everything following it so structural environments such as align*
        * retain their opening marker and first row.
        */
        clean = clean.replace(
            /(<p\b[^>]*>)\s*%+\s*<strong\b[^>]*>[\s\S]*?<\/strong>\s*/gi,
            "$1"
        );

        /*
        * The backend may wrap an entire commented TeX line in an HTML
        * paragraph before the frontend receives it:
        *
        *   <p>%At this point ...</p>
        *   <p>%&= \lim_{h\to 0} ...</p>
        *
        * Since the first non-whitespace source character is %, the entire
        * paragraph is a TeX comment and must be discarded.
        *
        * Escaped percentages such as \% do not match this rule.
        */
        clean = clean.replace(
            /<p\b[^>]*>\s*%[\s\S]*?<\/p>/gi,
            ""
        );

        // In TeX, a line whose first non-whitespace character is %
        // is entirely commented out and must not reach the rendered page.
        clean = clean.replace(/^[ \t]*%.*(?:\r?\n|$)/gm, "");

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

        // Keep bold symbols inside math as TeX instead of later converting
        // them into invalid HTML tags inside MathJax delimiters.
        clean = normalizeTextBoldInsideMath(clean);
        clean = normalizeTextItalicInsideMath(clean);

        // Repair HTML paragraph artifacts inside cases/array environments before
        // literal < and > characters are protected for safe innerHTML insertion.
        clean = normalizeStructuredMathHtmlArtifacts(clean);

        // Repair paragraph and line-break artifacts inside xymatrix bodies before
        // literal angle brackets inside math are protected as \lt and \gt.
        clean = normalizeXyMatrixHtmlArtifacts(clean);

        clean = normalizeLegacyOverFractions(clean);

        // TeX line-break control has no visible HTML or MathJax meaning.
        clean = clean.replace(/\\nobreak\b/g, "");

        // Remove Xy-pic setup commands that have no visible page meaning.
        clean = stripXyMatrixSetupMacros(clean);

        clean = convertUnderbracedXyMatrixToHtml(clean);
        clean = convertXyMatrixToHtml(clean);

        // Remove display wrappers left around generated Xy-pic HTML.
        clean = unwrapConvertedXyMatrixMathWrappers(clean);

        // Render operators stranded between converted xymatrix blocks.
        clean = renderXyMatrixConnectorMath(clean);

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

        clean = normalizeHtmlSensitiveMathCharacters(clean);

        // Restore the generated HTML after TeX angle-bracket normalization.
        clean = clean.replace(
            /PMXYMATRIXHTMLPLACEHOLDER(\d+)END/g,
            (match, indexText) => {
                const index = Number(indexText);
                return xymatrixHtmlBlocks[index] ?? match;
            }
        );

        // Normalize legacy display wrappers so MathJax can process their contents.
        clean = normalizeDisplayMathEnvironments(clean);
        clean = normalizeDollarDisplayMath(clean);

        // Convert common PlanetMath piecewise array blocks before MathJax typesetting.
        clean = convertPiecewiseArraysToHtml(clean);

        // Convert align/alignat blocks into HTML alignment tables.
        clean = convertAlignEnvironmentsToHtml(clean);

        // Convert simple display matrix/array blocks that MathJax often cannot recover
        // after PlanetMath row separators were lost.
        clean = convertSimpleDisplayMatricesToHtml(clean);

        // PlanetMath table color macros.
        // These commonly appear as \red0.01, \blue0.20, or \red{0.01}.
        clean = clean.replace(/\\red\{([^{}]*)\}/gi, '<span class="pm-tex-red">$1</span>');
        clean = clean.replace(/\\blue\{([^{}]*)\}/gi, '<span class="pm-tex-blue">$1</span>');

        clean = clean.replace(/\\red\s*([+-]?\d+(?:\.\d+)?)/gi, '<span class="pm-tex-red">$1</span>');
        clean = clean.replace(/\\blue\s*([+-]?\d+(?:\.\d+)?)/gi, '<span class="pm-tex-blue">$1</span>');

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

        // Text-level underline used in PlanetMath prose.
        clean = clean.replace(/\\underline\{([^{}]+)\}/gi, "<u>$1</u>");

        // Normalize the starred legacy form so the existing image converter
        // handles both \includegraphics and \includegraphics*.
        clean = clean.replace(
            /\\includegraphics\*/gi,
            "\\includegraphics"
        );

        // Replace old LaTeX/EPS image commands with readable placeholders.
        clean = normalizeLatexImageArtifacts(clean);
        
        // Arrange related placeholders while legacy layout markers
        // such as \raisebox and \hskip are still present.
        clean = normalizePlaceholderImageLayouts(clean);

        // Preserve visible spacing around prose conjunctions inside math.
        // Plain "and" is treated as math identifiers, so its surrounding
        // spaces disappear after MathJax typesetting.
        clean = clean.replace(
            /\\(?:mbox|textrm|text)\{\s*and\s*\}/gi,
            "\\;\\mathrm{and}\\;"
        );

        // Convert TeX footnotes into visible note blocks while preserving
        // any MathJax expressions contained inside them.
        clean = normalizeFootnoteMacros(clean);

        // Convert legacy custom Roman-numbered lists before the generic
        // \item conversion later in this pipeline.
        clean = normalizeLegacyRomanList(clean);

        // Prose layout cleanup must not remove legitimate commands such as
        // \quad, \text, or \mbox from inside MathJax expressions.
        const proseMathProtection = protectMathForProseCleanup(clean);
        clean = proseMathProtection.text;

        clean = normalizeProseLayoutMacros(clean);

        clean = restoreMathAfterProseCleanup(
            clean,
            proseMathProtection.blocks
        );

        // Convert inline matrices and expressions containing multiple matrices only
        // after prose wrappers outside math have been normalized.
        clean = convertRemainingMatrixMathSequencesToHtml(clean);

        // Restore protected eqnarray blocks only after prose and layout cleanup.
        // This keeps row separators and text commands intact for the converter.
        clean = restoreEqnarrayEnvironments(
            clean,
            eqnarrayProtection.blocks
        );

        // Normalize legacy eqnarray blocks before MathJax sees them.
        clean = convertEqnarrayToAligned(clean);

        // Convert the simple PSTricks deduction trees.
        clean = convertSimpleDeductionPstreeToHtml(clean);

        // Convert the larger fixed diagram used by "rooted-tree".
        clean = convertRootedTreePstreeToHtml(clean);

        // existing pspicture/list/etc cleanup continues below...
        clean = clean.replace(
            /\\begin\{pspicture\}[\s\S]*?\\end\{pspicture\}/gi,
            `<div class="img-placeholder mathjax-diagnostic-ignore"><em>[PSTricks diagram placeholder]</em></div>`
        );

        clean = clean.replace(
            /\\begin{enumerate}/gi,
            "<ol class='pm-tex-list' style='margin:0.65rem 0 0.9rem; padding-left:1.75rem;'>"
        );
        clean = clean.replace(/\\end{enumerate}/gi, "</ol>");

        clean = clean.replace(
            /\\begin{itemize}/gi,
            "<ul class='pm-tex-list' style='margin:0.65rem 0 0.9rem; padding-left:1.75rem; list-style-type:disc;'>"
        );
        clean = clean.replace(/\\end{itemize}/gi, "</ul>");

        clean = clean.replace(
            /\\item/gi,
            "<li style='margin-bottom:0.6rem; padding-block:0.06rem; line-height:1.5;'>"
        );

        clean = clean.replace(/\\emph\{([^}]+)\}/gi, "<em>$1</em>");
        clean = clean.replace(/\\textsl\{([^}]+)\}/gi, "<em>$1</em>");
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

        // Final cleanup for TeX separator/comment remnants after all HTML
        // transformations have completed. Some malformed source paragraphs can
        // be restructured by the browser-oriented rendering pipeline, so clean
        // both wrapped and unwrapped percent-only remnants here.
        clean = clean.replace(
            /<p[^>]*>\s*(?:%+\s*(?:<br\s*\/?>)?\s*)+<\/p>/gi,
            ""
        );

        clean = clean.replace(
            /(^|>\s*)%+(?:\s*%+)*(?=\s*(?:<|$))/gmi,
            "$1"
        );

        // Restore protected \verb contents only after all structural parsing
        // and HTML-sensitive processing has completed.
        clean = restoreLatexVerbCommands(
            clean,
            verbProtection.verbValues
        );

        clean = restoreMboxInsideMath(
            clean,
            mboxProtection.values
        );

        /*
        * A TeX \par before "Sketch of proof." can be flattened inside the
        * current list item. Keep the proof in that item, but start its heading
        * on a new visual line.
        */
        clean = clean.replace(
            /<strong\b([^>]*)>\s*Sketch of proof\.\s*<\/strong>/gi,
            `<strong$1 style="
                display:block;
                margin-top:0.75rem;
                margin-bottom:0.2rem;
            ">Sketch of proof.</strong>`
        );

        // Start proof-related lead labels in their own paragraphs when
        // backend HTML has flattened several TeX \par sections together.
        clean = splitProofLeadParagraphs(clean);

        // Remove theorem/definition wrappers whose bodies became empty
        clean = removeEmptyMathEnvironmentSections(clean);

        // Keep punctuation attached to the inline MathJax expression that
        // immediately precedes it.
        clean = preventInlineMathPunctuationWrap(clean);

        return clean;
    }

    function parseHtmlTableMultirowCell(value) {
        const source = String(value || "").trim();
        const command = "\\multirow";

        if (!source.startsWith(command)) {
            return null;
        }

        let cursor = command.length;

        const readBracedArgument = () => {
            while (cursor < source.length && /\s/.test(source[cursor])) {
                cursor += 1;
            }

            if (source[cursor] !== "{") {
                return null;
            }

            const end = findMatchingBrace(source, cursor);

            if (end === -1) {
                return null;
            }

            const content = source.slice(cursor + 1, end);
            cursor = end + 1;

            return content;
        };

        const rowCountText = readBracedArgument();
        const widthArgument = readBracedArgument();
        const cellContent = readBracedArgument();

        if (
            rowCountText === null
            || widthArgument === null
            || cellContent === null
        ) {
            return null;
        }

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        if (cursor !== source.length) {
            return null;
        }

        const rowspan = Number(rowCountText.trim());

        if (!Number.isInteger(rowspan) || rowspan < 1) {
            return null;
        }

        return {
            rowspan,
            content: cellContent.trim()
        };
    }


    function normalizeHtmlTableMultirows(value) {
        const source = String(value || "");

        if (
            !source.includes("\\multirow")
            || !/<table\b/i.test(source)
        ) {
            return source;
        }

        return source.replace(
            /<table\b[^>]*>[\s\S]*?<\/table>/gi,
            tableHtml => {
                if (!tableHtml.includes("\\multirow")) {
                    return tableHtml;
                }

                const template = document.createElement("template");
                template.innerHTML = tableHtml.trim();

                const table = template.content.querySelector("table");

                if (!table) {
                    return tableHtml;
                }

                /*
                 * Each entry stores the number of following rows still occupied
                 * by a rowspan at that logical column.
                 */
                const activeRowspans = [];

                Array.from(table.rows).forEach(row => {
                    const sourceCells = Array.from(row.cells);

                    let physicalIndex = 0;
                    let logicalColumn = 0;

                    while (physicalIndex < sourceCells.length) {
                        /*
                         * Skip columns occupied by a rowspan originating in a
                         * previous row. Legacy generated tables commonly retain
                         * an empty placeholder cell in these positions.
                         */
                        while ((activeRowspans[logicalColumn] || 0) > 0) {
                            const candidate = sourceCells[physicalIndex];

                            if (
                                candidate
                                && candidate.textContent.trim() === ""
                            ) {
                                candidate.remove();
                                physicalIndex += 1;
                            }

                            activeRowspans[logicalColumn] -= 1;
                            logicalColumn += 1;
                        }

                        const cell = sourceCells[physicalIndex];

                        if (!cell) {
                            break;
                        }

                        const multirow = parseHtmlTableMultirowCell(
                            cell.innerHTML
                        );

                        if (multirow) {
                            cell.rowSpan = multirow.rowspan;
                            cell.innerHTML = multirow.content;

                            cell.style.textAlign = "center";
                            cell.style.verticalAlign = "middle";

                            activeRowspans[logicalColumn] =
                                multirow.rowspan - 1;
                        }

                        const colspan = Math.max(
                            1,
                            Number(cell.colSpan) || 1
                        );

                        logicalColumn += colspan;
                        physicalIndex += 1;
                    }

                    /*
                     * Account for active rowspans whose following row omitted
                     * the corresponding placeholder cell entirely.
                     */
                    while (logicalColumn < activeRowspans.length) {
                        if ((activeRowspans[logicalColumn] || 0) > 0) {
                            activeRowspans[logicalColumn] -= 1;
                        }

                        logicalColumn += 1;
                    }
                });

                return template.innerHTML;
            }
        );
    }

    function normalizeAlgorithmHtmlFragment(value) {
        return String(value || "")
            .replace(/\\label\s*\{[^{}]*\}/gi, "")
            .replace(/\r?\n/g, " ")
            .replace(/[ \t]{2,}/g, " ")
            .trim();
    }

    function removeEmptyMathEnvironmentSections(value) {
        const source = String(value || "");

        if (!source.includes("math-env")) {
            return source;
        }

        const template = document.createElement("template");
        template.innerHTML = source;

        const meaningfulSelector = [
            "img",
            "svg",
            "table",
            "figure",
            "canvas",
            "iframe",
            "video",
            "audio",
            "pre",
            "code",
            "ul",
            "ol",
            "mjx-container",
            "math"
        ].join(",");

        template.content
            .querySelectorAll("section.math-env")
            .forEach(section => {
                const body = Array.from(section.children).find(
                    child =>
                        child.classList
                        && child.classList.contains("math-env-body")
                );

                if (!body) {
                    return;
                }

                const visibleText = String(body.textContent || "")
                    .replace(/\u00a0/g, " ")
                    .trim();

                const hasMeaningfulElement =
                    Boolean(body.querySelector(meaningfulSelector));

                if (!visibleText && !hasMeaningfulElement) {
                    section.remove();
                }
            });

        return template.innerHTML;
    }

    function normalizeAlgorithmCodeBlocks(value) {
        const source = String(value || "");

        const decodeBackslashEntities = text =>
            String(text || "")
                .replace(/&#(?:0*92|x0*5c);/gi, "\\")
                .replace(/&bsol;/gi, "\\");

        const detectableSource =
            decodeBackslashEntities(source);

        if (
            !source.includes("math-code-block-alg")
            || !/\\begin\s*\{description\}/i.test(
                detectableSource
            )
        ) {
            return source;
        }

        return source.replace(
            /<pre\b[^>]*class=["'][^"']*\bmath-code-block-alg\b[^"']*["'][^>]*>\s*<code\b[^>]*>([\s\S]*?)<\/code>\s*<\/pre>/gi,
            function (originalHtml, codeHtml) {
                const cleanCode =
                    decodeBackslashEntities(codeHtml)
                        .replace(
                            /\\label\s*\{[^{}]*\}/gi,
                            ""
                        )
                        .trim();

                const descriptionMatch = cleanCode.match(
                    /^([\s\S]*?)\\begin\s*\{description\}([\s\S]*?)\\end\s*\{description\}([\s\S]*)$/i
                );

                if (!descriptionMatch) {
                    return originalHtml;
                }

                const introduction = normalizeAlgorithmHtmlFragment(
                    descriptionMatch[1]
                );

                const descriptionBody = String(
                    descriptionMatch[2] || ""
                );

                const trailingContent = normalizeAlgorithmHtmlFragment(
                    descriptionMatch[3]
                );

                const items = [];
                const itemPattern =
                    /\\item\s*\[([^\]]+)\]([\s\S]*?)(?=\\item\s*\[[^\]]+\]|$)/gi;

                let itemMatch;

                while (
                    (itemMatch = itemPattern.exec(descriptionBody)) !== null
                ) {
                    const label = String(itemMatch[1] || "").trim();
                    const content = normalizeAlgorithmHtmlFragment(
                        itemMatch[2]
                    );

                    if (!label || !content) {
                        continue;
                    }

                    items.push({
                        label,
                        content
                    });
                }

                if (items.length === 0) {
                    return originalHtml;
                }

                const itemRows = items.map(item => `
                    <div style="
                        display:grid;
                        grid-template-columns:minmax(5.5rem, max-content) minmax(0, 1fr);
                        gap:0.35rem 0.85rem;
                        align-items:start;
                        margin-top:0.55rem;
                    ">
                        <strong>${escapeHtmlForMathCell(item.label)}</strong>
                        <div>${item.content}</div>
                    </div>
                `).join("");

                return `
                    <section
                        class="pm-algorithm-block tex2jax_process"
                        style="
                            margin:1rem 0;
                            padding:1rem 1.1rem;
                            border-left:3px solid #cbd5e1;
                            background:#f8fafc;
                            line-height:1.55;
                        "
                    >
                        <div style="
                            font-weight:700;
                            margin-bottom:0.65rem;
                        ">
                            Algorithm.
                        </div>

                        ${introduction
                            ? `<div style="margin-bottom:0.75rem;">${introduction}</div>`
                            : ""
                        }

                        <div>
                            ${itemRows}
                        </div>

                        ${trailingContent
                            ? `<div style="margin-top:0.75rem;">${trailingContent}</div>`
                            : ""
                        }
                    </section>
                `;
            }
        );
    }

    function normalizeMboxHtmlTableInsideMath(value) {
        let output = String(value || "");

        const decodeHtmlEntities = text => {
            const textarea = document.createElement("textarea");
            textarea.innerHTML = String(text || "");
            return textarea.value;
        };

        const convertRow = rowHtml => {
            const source = decodeHtmlEntities(
                String(rowHtml || "")
                    .replace(/<br\s*\/?>/gi, " ")
                    .replace(/<[^>]+>/g, "")
            ).trim();

            if (!source) {
                return "";
            }

            let result = "";
            let cursor = 0;

            source.replace(
                /\$([^$]*?)\$/g,
                (match, mathBody, offset) => {
                    const prose = source.slice(cursor, offset);

                    if (prose.trim()) {
                        result += `\\mbox{${prose}}`;
                    }

                    result += String(mathBody || "");
                    cursor = offset + match.length;

                    return match;
                }
            );

            const remainder = source.slice(cursor);

            if (remainder.trim()) {
                result += `\\mbox{${remainder}}`;
            }

            return result;
        };

        output = output.replace(
            /\\mbox\s*\{\s*(<div\b[^>]*class=["'][^"']*\bmath-table-wrapper\b[^"']*["'][^>]*>[\s\S]*?<\/div>)\s*\}/gi,
            (match, wrapperHtml) => {
                const rows = [];

                String(wrapperHtml || "").replace(
                    /<tr\b[^>]*>\s*<td\b[^>]*>([\s\S]*?)<\/td>\s*<\/tr>/gi,
                    (rowMatch, cellHtml) => {
                        const row = convertRow(cellHtml);

                        if (row) {
                            rows.push(row);
                        }

                        return rowMatch;
                    }
                );

                if (!rows.length) {
                    return match;
                }

                return (
                    "\\begin{array}{l}" +
                    rows.join(" \\\\ ") +
                    "\\end{array}"
                );
            }
        );

        return output;
    }

    function normalizeMboxTabularInsideMath(value) {
        let output = String(value || "");

        const convertRow = row => {
            const source = String(row || "").trim();

            if (!source) {
                return "";
            }

            let result = "";
            let cursor = 0;

            // Preserve embedded $...$ as mathematics and wrap the surrounding
            // prose in \text{...}.
            source.replace(
                /\$([^$]*?)\$/g,
                (match, mathBody, offset) => {
                    const prose = source.slice(cursor, offset);

                    if (prose) {
                        result += `\\text{${prose}}`;
                    }

                    result += mathBody;
                    cursor = offset + match.length;

                    return match;
                }
            );

            const remainder = source.slice(cursor);

            if (remainder) {
                result += `\\text{${remainder}}`;
            }

            return result;
        };

        output = output.replace(
            /\\mbox\s*\{\s*\\begin\s*\{tabular\}\s*\{[^{}]*\}([\s\S]*?)\\end\s*\{tabular\}\s*\}/gi,
            (match, tableBody) => {
                const rows = String(tableBody || "")
                    .split(/\\\\/)
                    .map(convertRow)
                    .filter(Boolean);

                if (!rows.length) {
                    return "";
                }

                return `\\begin{array}{l}${rows.join(" \\\\ ")}\\end{array}`;
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

    function protectLatexVerbCommands(value) {
        const source = String(value || "");
        const verbValues = [];

        // LaTeX \verb uses the character immediately following \verb
        // as its delimiter:
        //
        //   \verb.<.
        //   \verb.|.
        //   \verb=aa*b=
        //
        // The starred form \verb* is handled as well.
        const text = source.replace(
            /\\verb\*?([^\w\s])([\s\S]*?)\1/g,
            (match, delimiter, contents) => {
                const index = verbValues.length;
                verbValues.push(contents);

                return `PMVERBATIMTOKEN${index}END`;
            }
        );

        return {
            text,
            verbValues
        };
    }

    function restoreLatexVerbCommands(value, verbValues) {
        let output = String(value || "");
        const values = Array.isArray(verbValues) ? verbValues : [];

        const restoreToken = (match, indexText, insideMath = false) => {
            const index = Number(indexText);

            if (
                !Number.isInteger(index) ||
                index < 0 ||
                index >= values.length
            ) {
                return match;
            }

            let contents = String(values[index] || "");

            if (insideMath) {
                const mathContents = Array.from(contents)
                    .map(character => {
                        switch (character) {
                            case "\\":
                                return "\\backslash ";
                            case "{":
                                return "\\{";
                            case "}":
                                return "\\}";
                            case "&":
                                return "\\&";
                            case "%":
                                return "\\%";
                            case "#":
                                return "\\#";
                            case "_":
                                return "\\_";
                            case "<":
                                return "\\lt ";
                            case ">":
                                return "\\gt ";
                            case " ":
                                return "\\;";
                            default:
                                return character;
                        }
                    })
                    .join("");

                return `\\mathtt{${mathContents}}`;
            }

            const htmlContents = contents
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");

            return `
                <code class="pm-inline-verbatim" style="
                    padding:0;
                    border:0;
                    background:transparent;
                    color:inherit;
                    font-size:0.95em;
                    white-space:nowrap;
                ">${htmlContents}</code>
            `;
        };

        const restoreInsideMathChunk = (chunk) => {
            return String(chunk || "").replace(
                /PMVERBATIMTOKEN(\d+)END/g,
                (match, indexText) =>
                    restoreToken(match, indexText, true)
            );
        };

        // Restore tokens inside MathJax expressions first.
        output = output.replace(
            /\\\[[\s\S]*?\\\]/g,
            restoreInsideMathChunk
        );

        output = output.replace(
            /\\\([\s\S]*?\\\)/g,
            restoreInsideMathChunk
        );

        output = output.replace(
            /\$\$[\s\S]*?\$\$/g,
            restoreInsideMathChunk
        );

        output = output.replace(
            /(^|[^$])\$([^$\n]*?)\$(?!\$)/g,
            (match, prefix, body) => {
                return `${prefix}$${restoreInsideMathChunk(body)}$`;
            }
        );

        // Restore any remaining prose-mode verbatim tokens.
        output = output.replace(
            /PMVERBATIMTOKEN(\d+)END/g,
            (match, indexText) =>
                restoreToken(match, indexText, false)
        );

        return output;
    }

    function normalizeDiagramImageUrls(html, apiEndpoint = DEFAULT_API_ENDPOINT) {
        if (!html) return "";

        return html.replace(
            /src=(["'])\/api\/math\/diagrams\//gi,
            `src=$1${apiEndpoint}/math/diagrams/`
        );
    }
})();