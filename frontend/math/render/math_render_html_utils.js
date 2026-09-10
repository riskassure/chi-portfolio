(() => {
    function escapeHtmlForMathCell(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    window.MathCmsRenderHtmlUtils = {
        escapeHtmlForMathCell
    };
})();
