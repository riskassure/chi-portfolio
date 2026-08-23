// frontend/math/math_render_xy_parser.js

(function () {
    function findXyMatrixBodyStart(text, startIndex) {
        let i = findNextNonSpaceIndex(text, startIndex);

        if (i === -1) {
            return -1;
        }

        // Ordinary case:
        // \xymatrix{...}
        if (text[i] === "{") {
            return i;
        }

        // Extended PlanetMath / Xy-pic option cases:
        // \xymatrix@C=1.5cm{...}
        // \xymatrix@R-=2pt{...}
        // \xymatrix@+=1.5cm{...}
        // \xymatrix@1{...}
        // \xymatrix @R=1pt @C=1.5cm {...}
        // \xymatrix @!=1pt {...}
        if (text[i] !== "@") {
            return -1;
        }

        const limit = Math.min(text.length, i + 180);

        while (i < limit) {
            while (i < limit && /\s/.test(text[i])) {
                i += 1;
            }

            if (i >= limit) {
                return -1;
            }

            if (text[i] === "{" && text[i - 1] !== "\\") {
                return i;
            }

            if (text[i] !== "@") {
                return -1;
            }

            // Consume one @ option token.
            // Examples:
            //   @C=1.5cm
            //   @R-=2pt
            //   @+=3pc
            //   @1
            //   @!
            //   @!=1pt
            //   @-2ex
            i += 1;

            while (i < limit) {
                if (text[i] === "{" && text[i - 1] !== "\\") {
                    return i;
                }

                if (/\s/.test(text[i]) || text[i] === "@") {
                    break;
                }

                i += 1;
            }
        }

        return -1;
    }

    function findNextNonSpaceIndex(text, startIndex) {
        for (let i = startIndex; i < text.length; i += 1) {
            if (!/\s/.test(text[i])) {
                return i;
            }
        }

        return -1;
    }

    window.MathCmsRenderXyParser = {
        findXyMatrixBodyStart,
        findNextNonSpaceIndex
    };
})();
