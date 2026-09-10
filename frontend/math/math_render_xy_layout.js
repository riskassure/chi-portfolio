// frontend/math/math_render_xy_layout.js

(function () {
    function calculateXyMatrixArrowLayout(sourceRows) {
        let maxHorizontalLabelLength = 0;
        let maxVerticalLabelLength = 0;

        sourceRows.forEach(row => {
            row.forEach(cell => {
                (cell.arrows || []).forEach(arrow => {
                    const labelLength = estimateTexLabelLength(arrow.label || "");

                    if (arrow.direction === "r" || arrow.direction === "l") {
                        maxHorizontalLabelLength = Math.max(maxHorizontalLabelLength, labelLength);
                    }

                    if (arrow.direction === "u" || arrow.direction === "d") {
                        maxVerticalLabelLength = Math.max(maxVerticalLabelLength, labelLength);
                    }
                });
            });
        });

        return {
            // Same width for every horizontal arrow in this xymatrix.
            horizontalWidthEm: Math.max(3.6, 3.2 + maxHorizontalLabelLength * 0.56),

            // Same height for every vertical arrow in this xymatrix.
            verticalHeightEm: Math.max(2.7, 2.5 + maxVerticalLabelLength * 0.08),

            // Wider vertical arrow cell only when labels need room.
            verticalWidthEm: Math.max(2.4, 1.8 + maxVerticalLabelLength * 0.32)
        };
    }

    function estimateTexLabelLength(label) {
        return String(label || "")
            .replace(/\\[A-Za-z]+/g, "X")
            .replace(/[{}_^]/g, "")
            .trim()
            .length;
    }

    function getXyMatrixCellPadding(rowIndex, colIndex) {
        const isObjectRow = rowIndex % 2 === 0;
        const isObjectCol = colIndex % 2 === 0;

        if (isObjectRow && isObjectCol) {
            return "0.06rem 0.08rem";
        }

        if (isObjectRow && !isObjectCol) {
            return "0.02rem 0.02rem";
        }

        if (!isObjectRow && isObjectCol) {
            return "0.02rem 0.08rem";
        }

        return "0";
    }

    window.MathCmsRenderXyLayout = {
        calculateXyMatrixArrowLayout,
        estimateTexLabelLength,
        getXyMatrixCellPadding
    };
})();
