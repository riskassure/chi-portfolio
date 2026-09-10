(() => {
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

    function normalizeStandardListEnvironments(clean) {
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

        return clean;
    }

    function normalizeBibliographyEnvironments(clean) {
        clean = clean.replace(
            /\\begin\{(?:the)?bibliography\}\{[\s\S]*?\}/gi,
            "<div style='margin-top: 1.5rem; border-top: 1px dashed #cbd5e1; padding-top: 1rem;'><strong>References & Bibliography:</strong><ul style='list-style-type: square; padding-left: 1.5rem;'>"
        );
        clean = clean.replace(/\\end\{(?:the)?bibliography\}/gi, "</ul></div>");

        return clean;
    }

    window.MathCmsRenderLegacyLists = {
        normalizeLegacyRomanList,
        normalizeStandardListEnvironments,
        normalizeBibliographyEnvironments
    };
})();
