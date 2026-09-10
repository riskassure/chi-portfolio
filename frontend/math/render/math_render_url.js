(() => {

function normalizeUrlMacros(value) {
    const source = String(value || "");

    if (!/\\url\s*\{/i.test(source)) {
        return source;
    }

    return source.replace(
        /\\url\s*\{([^{}]+)\}/gi,
        function (_, rawUrl) {
            const url = String(rawUrl || "").trim();

            if (!url) {
                return "";
            }

            // Only create links for ordinary web URLs.
            if (!/^https?:\/\//i.test(url)) {
                return url;
            }

            const anchor = document.createElement("a");

            anchor.href = url;
            anchor.textContent = url;
            anchor.className = "pm-external-url";
            anchor.target = "_blank";
            anchor.rel = "noopener noreferrer";

            return anchor.outerHTML;
        }
    );
}


window.MathCmsRenderUrl = {
    normalizeUrlMacros
};

})();
