(() => {
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

    window.MathCmsRenderDisplayEnvironments = {
        normalizeDisplayMathEnvironments
    };
})();
