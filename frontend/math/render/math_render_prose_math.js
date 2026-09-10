(() => {
    function protectMathForProseCleanup(value) {
        let output = String(value || "");
        const blocks = [];

        const protectBlock = block => {
            const index = blocks.length;
            blocks.push(block);
            return `PMMATHPROSEBLOCK${index}END`;
        };

        /*
         * Raw multline environments are already display math.
         * Protect their \\ row separators from prose cleanup,
         * including the TeX control-space rule.
         */
        output = output.replace(
            /\\begin\s*\{(multline\*?)\}[\s\S]*?\\end\s*\{\1\}/gi,
            protectBlock
        );

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

    window.MathCmsRenderProseMath = {
        protectMathForProseCleanup,
        restoreMathAfterProseCleanup
    };
})();
