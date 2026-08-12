(() => {
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

    window.MathCmsRenderVerbatim = {
        protectLatexVerbCommands,
        restoreLatexVerbCommands
    };
})();
