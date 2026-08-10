(() => {
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

    window.MathCmsRenderHtmlSensitiveMath = {
        normalizeHtmlSensitiveMathCharacters
    };
})();
