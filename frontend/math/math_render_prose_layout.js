(() => {
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

    function unwrapSimpleTextCommand(text, commandName) {
        const pattern = new RegExp("\\\\" + commandName + "\\s*\\{([^{}]*)\\}", "gi");

        return String(text || "").replace(pattern, function(_, content) {
            return String(content || "").trim();
        });
    }

    function normalizeProseLayoutMacros(tex) {
        if (!tex) return "";

        let output = String(tex || "");

        // Preserve meaningful legend colors while removing raw
        // \textcolor commands and autolinks around color names.
        output = window.MathCmsRenderTextColor.normalizeTextColorMacros(output);

        // Convert LaTeX \url{...} commands into safe external links.
        output = window.MathCmsRenderUrl.normalizeUrlMacros(output);

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
        output = window.MathCmsRenderLegacyTex.normalizeCommonTextAccentMacros(output);

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

    window.MathCmsRenderProseLayout = {
        normalizeProseLayoutMacros
    };
})();
