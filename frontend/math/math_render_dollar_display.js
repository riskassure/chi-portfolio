(() => {
    function normalizeDollarDisplayMath(tex) {
        if (!tex) return "";

        return String(tex || "").replace(
            /\$\$([\s\S]*?)\$\$/g,
            function(_, body) {
                return `\\[${body}\\]`;
            }
        );
    }

    window.MathCmsRenderDollarDisplay = {
        normalizeDollarDisplayMath
    };
})();
