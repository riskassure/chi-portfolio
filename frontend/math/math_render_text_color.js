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


window.MathCmsRenderTextColor = {
    normalizeTextColorMacros
};

})();
