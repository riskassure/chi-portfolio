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

    window.MathCmsRenderLegacyLists = {
        normalizeLegacyRomanList
    };
})();
