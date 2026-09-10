(() => {
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

    window.MathCmsRenderMathEnv = {
        removeEmptyMathEnvironmentSections
    };
})();
