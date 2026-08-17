(() => {
    function renderMatrixDelimiter(delimiter, side = "left") {
        if (!delimiter) {
            return "";
        }

        const cleanDelimiter = String(delimiter || "");
        const cleanSide = side === "right" ? "right" : "left";

        const wrapperStyle = `
            align-self:stretch;
            display:flex;
            align-items:stretch;
            justify-content:center;
            flex:0 0 auto;
            width:0.88rem;
            color:currentColor;
        `;

        if (cleanDelimiter === "(" || cleanDelimiter === ")") {
            const path =
                cleanSide === "left"
                    ? "M24 2 C8 18 8 82 24 98"
                    : "M6 2 C22 18 22 82 6 98";

            return `
                <span class="pm-matrix-delimiter pm-matrix-paren-${cleanSide}" style="${wrapperStyle}">
                    <svg viewBox="0 0 30 100" preserveAspectRatio="none" style="display:block; width:100%; height:100%; min-height:2.4rem;">
                        <path d="${path}" stroke="currentColor" stroke-width="4.2" fill="none" stroke-linecap="round"></path>
                    </svg>
                </span>
            `;
        }

        if (cleanDelimiter === "[" || cleanDelimiter === "]") {
            const path =
                cleanSide === "left"
                    ? "M25 2 H8 V98 H25"
                    : "M5 2 H22 V98 H5";

            return `
                <span class="pm-matrix-delimiter pm-matrix-bracket-${cleanSide}" style="${wrapperStyle}">
                    <svg viewBox="0 0 30 100" preserveAspectRatio="none" style="display:block; width:100%; height:100%; min-height:2.4rem;">
                        <path d="${path}" stroke="currentColor" stroke-width="4" fill="none" stroke-linecap="square" stroke-linejoin="miter"></path>
                    </svg>
                </span>
            `;
        }

        if (cleanDelimiter === "{" || cleanDelimiter === "}") {
            const path =
                cleanSide === "left"
                    ? "M27 2 C14 2 15 22 15 32 C15 43 7 44 6 50 C7 56 15 57 15 68 C15 78 14 98 27 98"
                    : "M7 2 C20 2 19 22 19 32 C19 43 27 44 28 50 C27 56 19 57 19 68 C19 78 20 98 7 98";

            return `
                <span class="pm-matrix-delimiter pm-matrix-brace-${cleanSide}" style="${wrapperStyle}">
                    <svg viewBox="0 0 34 100" preserveAspectRatio="none" style="display:block; width:100%; height:100%; min-height:2.4rem;">
                        <path d="${path}" stroke="currentColor" stroke-width="3.4" fill="none" stroke-linecap="round"></path>
                    </svg>
                </span>
            `;
        }

        if (cleanDelimiter === "|") {
            return `
                <span class="pm-matrix-delimiter pm-matrix-vertical-${cleanSide}" style="${wrapperStyle}; width:0.36rem;">
                    <span style="display:block; height:100%; border-left:3px solid currentColor;"></span>
                </span>
            `;
        }

        if (cleanDelimiter === "‖") {
            return `
                <span class="pm-matrix-delimiter pm-matrix-double-vertical-${cleanSide}" style="${wrapperStyle}; width:0.50rem; gap:0.10rem;">
                    <span style="display:block; height:100%; border-left:2.4px solid currentColor;"></span>
                    <span style="display:block; height:100%; border-left:2.4px solid currentColor;"></span>
                </span>
            `;
        }

        return `<span style="${wrapperStyle}; align-items:center;">${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanDelimiter)}</span>`;
    }

    window.MathCmsRenderDelimiters = {
        renderMatrixDelimiter
    };
})();
