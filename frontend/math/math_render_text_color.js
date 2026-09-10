(() => {

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


    function normalizeLegacyTableColors(clean) {
        // PlanetMath table color macros.
        // These commonly appear as \red0.01, \blue0.20, or \red{0.01}.
        clean = clean.replace(/\\red\{([^{}]*)\}/gi, '<span class="pm-tex-red">$1</span>');
        clean = clean.replace(/\\blue\{([^{}]*)\}/gi, '<span class="pm-tex-blue">$1</span>');

        clean = clean.replace(/\\red\s*([+-]?\d+(?:\.\d+)?)/gi, '<span class="pm-tex-red">$1</span>');
        clean = clean.replace(/\\blue\s*([+-]?\d+(?:\.\d+)?)/gi, '<span class="pm-tex-blue">$1</span>');

        return clean;
    }

window.MathCmsRenderTextColor = {
    normalizeTextColorMacros,
    normalizeLegacyTableColors
};

})();
