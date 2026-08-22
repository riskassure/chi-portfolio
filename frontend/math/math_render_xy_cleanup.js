// frontend/math/math_render_xy_cleanup.js

(function () {
    function stripXyMatrixSetupMacros(tex) {
        if (!tex) return "";

        return String(tex)
            .replace(/\\UseAllTwocells\b/g, "")
            .replace(/\\UseComputerModernTips\b/g, "");
    }

    function renderXyMatrixConnectorMath(tex) {
        if (!tex) return "";

        return String(tex)
            .replace(
                /\\quad\s*\{:=\}\s*\\quad/g,
                '<span class="pm-xymatrix-connector" style="display:inline-block; margin:0 0.55rem;">\\({:=}\\)</span>'
            )
            .replace(
                /\\quad\s*\{=\}\s*\\quad/g,
                '<span class="pm-xymatrix-connector" style="display:inline-block; margin:0 0.55rem;">\\({=}\\)</span>'
            );
    }

    window.MathCmsRenderXyCleanup = {
        stripXyMatrixSetupMacros,
        renderXyMatrixConnectorMath
    };
})();
