(() => {
    function convertSimpleDisplayMatricesToHtml(tex) {
        if (!tex) return "";

        let output = String(tex || "");

        // Display matrix environments with optional prefix/suffix:
        // \[ A=\begin{pmatrix} ... \end{pmatrix}. \]
        // Important: prefix/suffix must not cross a display boundary.
        output = output.replace(
            /\\\[\s*((?:(?!\\\])[\s\S])*?)\\begin\{(pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix)\}([\s\S]*?)\\end\{\2\}\s*((?:(?!\\\])[\s\S])*?)\\\]/gi,
            function(_, prefix, envName, body, suffix) {
                if (/\\begin\{(?:pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix|array)\}/i.test(suffix || "")) {
                    return _;
                }

                return window.MathCmsRenderMatrixAffixes
                    .buildDisplayMatrixHtmlWithAffixes(
                        envName,
                        prefix,
                        body,
                        suffix
                    );
            }
        );

        // Display array environments with optional prefix/suffix:
        // \[ \pi=\begin{array}{ccc} ... \end{array} \]
        output = output.replace(
            /\\\[\s*((?:(?!\\\])[\s\S])*?)\\begin\{array\}\{([^{}]*)\}([\s\S]*?)\\end\{array\}\s*((?:(?!\\\])[\s\S])*?)\\\]/gi,
            function(_, prefix, columnSpec, body, suffix) {
                if (/\\begin\{(?:pmatrix|bmatrix|Bmatrix|vmatrix|Vmatrix|matrix|smallmatrix|array)\}/i.test(suffix || "")) {
                    return _;
                }

                return window.MathCmsRenderMatrixAffixes
                    .buildDisplayMatrixHtmlWithAffixes(
                        "array",
                        prefix,
                        body,
                        suffix
                    );
            }
        );

        return output;
    }

    window.MathCmsRenderMatrixDisplay = {
        convertSimpleDisplayMatricesToHtml
    };
})();
