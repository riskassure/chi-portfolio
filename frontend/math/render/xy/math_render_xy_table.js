// frontend/math/render/xy/math_render_xy_table.js

(function () {
    const XY_PLAIN_HORIZONTAL_LINE = "__PM_XY_PLAIN_HORIZONTAL_LINE__";

    function isXyPlainHorizontalLineCell(value) {
        return (
            value === XY_PLAIN_HORIZONTAL_LINE
            || (
                value
                && typeof value === "object"
                && value.type === "plain-horizontal-line"
            )
        );
    }

    const XY_VERTICAL_ROWSPAN_COVERED = "__PM_XY_VERTICAL_ROWSPAN_COVERED__";

    function buildHtmlTableFromXyMatrixBody(body) {
        const normalizedBody = window.MathCmsRenderXyParser.recoverLostXyMatrixRowSeparators(
            window.MathCmsRenderStructuredMath
                .normalizeEqnarrayHtmlArtifacts(body)
        );

        const sourceRows = window.MathCmsRenderStructuredMath
            .splitEqnarrayRows(normalizedBody)
            .map(row => window.MathCmsRenderStructuredMath
                .splitEqnarrayCells(row).map(window.MathCmsRenderXyParser.parseXyMatrixCell))
            .filter(row => row.length > 0);

        const hasLegacyTwoCell = sourceRows
            .flat()
            .some(cell => cell.legacyTwoCell);

        if (sourceRows.length === 0) {
            return window.MathCmsRenderXyCells.makeUnsupportedXyMatrixPlaceholder(body);
        }

        const sourceColumnCount = Math.max(...sourceRows.map(row => row.length));
        const arrowLayout = window.MathCmsRenderXyLayout.calculateXyMatrixArrowLayout(sourceRows);

        const hasNamedReferenceTwoCell = sourceRows
            .flat()
            .some(cell => Boolean(cell.twoCellLabel));

        /*
        * Preserve the existing cell-based renderer for specialized
        * two-cell diagrams. Ordinary xymatrix diagonals use the new
        * table-level SVG overlay.
        */
        const useDiagonalOverlay =
            !hasLegacyTwoCell
            && !hasNamedReferenceTwoCell;

        const diagonalArrows = [];

        if (useDiagonalOverlay) {
            sourceRows.forEach((row, sourceRow) => {
                row.forEach((cell, sourceCol) => {
                    (cell.arrows || []).forEach(arrow => {
                        if (!window.MathCmsRenderXyParser.isXyDiagonalDirection(arrow.direction)) {
                            return;
                        }

                        const {
                            rowDelta,
                            colDelta
                        } = window.MathCmsRenderXyParser.getXyArrowCoordinateDelta(
                            arrow.directionText
                        );

                        const targetRow =
                            sourceRow + rowDelta;

                        const targetCol =
                            sourceCol + colDelta;

                        if (
                            targetRow < 0
                            || targetRow >= sourceRows.length
                            || targetCol < 0
                            || targetCol >= sourceColumnCount
                        ) {
                            return;
                        }

                        diagonalArrows.push({
                            sourceRow,
                            sourceCol,
                            targetRow,
                            targetCol,

                            label:
                                arrow.label || "",

                            labelPosition:
                                arrow.labelPosition || "center",

                            style:
                                arrow.style || "->",

                            curveSide:
                                arrow.curveSide || "",

                            curveAmount:
                                arrow.curveAmount || ""
                        });
                    });
                });
            });
        }

        const diagonalDataAttribute =
            diagonalArrows.length > 0
                ? (
                    ` data-pm-diagonal-arrows="`
                    + encodeURIComponent(
                        JSON.stringify(diagonalArrows)
                    )
                    + `"`
                )
                : "";

        /*
        * Long diagonals such as [lld] and [rrd] cross empty inter-object
        * columns. Reserve those column gaps so the SVG overlays remain inside
        * the measured xymatrix width and neighboring object labels do not
        * collapse together.
        */
        const hasWideDiagonal =
            !useDiagonalOverlay
            && sourceRows
            .flat()
            .some(cell =>
                (cell.arrows || []).some(arrow =>
                    (
                        arrow.direction === "dl"
                        || arrow.direction === "dr"
                        || arrow.direction === "ul"
                        || arrow.direction === "ur"
                    )
                    && window.MathCmsRenderXyParser.getXyArrowHorizontalSpan(arrow.directionText) > 1
                )
            );

        const wideDiagonalGapWidthEm = Math.max(
            arrowLayout.horizontalWidthEm || 3.6,
            4.2
        );

        const expandedRowCount = sourceRows.length * 2 - 1;
        const expandedColumnCount = sourceColumnCount * 2 - 1;

        const grid = Array.from({ length: expandedRowCount }, () => {
            return Array.from({ length: expandedColumnCount }, () => "");
        });

        sourceRows.forEach((row, rowIndex) => {
            row.forEach((cell, colIndex) => {
                const gridRow = rowIndex * 2;
                const gridCol = colIndex * 2;

                const selfLoops = cell.arrows.filter(
                    arrow => arrow.isSelfLoop
                );

                const objectHtml = window.MathCmsRenderXyCells.renderXyObjectCell(
                    cell.objectTex,
                    cell.objectFrame,
                    selfLoops,
                    cell.overlayLabel
                );

                const hasVisibleObject =
                    String(cell.objectTex || "").trim() !== ""
                    || String(cell.overlayLabel || "").trim() !== ""
                    || Boolean(cell.objectFrame)
                    || selfLoops.length > 0;

                /*
                * Do not let an empty source cell overwrite part of a spanning arrow
                * that was placed earlier by an arrow from a preceding row.
                *
                * Example:
                *
                *   C\ar[dd]_h\\
                *   &A\\
                *   K
                *
                * The empty cell before A occupies the middle of the C-to-K arrow.
                */
                if (hasVisibleObject || !grid[gridRow][gridCol]) {
                    grid[gridRow][gridCol] = objectHtml;
                }

                if (
                    cell.twoCellLabel
                    && gridRow >= 1
                    && gridCol >= 2
                ) {
                    /*
                    * Named-reference two-cells such as:
                    *
                    *   \ar@{=>}"1";"2"_{\eta}
                    *
                    * occur in the lower-right source cell, while the two named
                    * diagonal arrows occupy the expanded cells above-left and
                    * above-right. Place the transformation in the center between them.
                    */
                    setGridCellIfInBounds(
                        grid,
                        gridRow - 1,
                        gridCol - 2,
                        window.MathCmsRenderXyCells.renderNamedReferenceTwoCell(cell.twoCellLabel)
                    );
                }

                if (cell.legacyTwoCell) {
                    const middleArrow = cell.arrows.find(
                        arrow =>
                            !arrow.isSelfLoop
                            && arrow.direction === "r"
                            && arrow.span === 1
                    );

                    grid[gridRow][gridCol + 1] =
                        window.MathCmsRenderXyCells.renderLegacyTwoCellArrowGroup(
                            cell.legacyTwoCell,
                            middleArrow?.label || "",
                            arrowLayout
                        );

                    cell.arrows
                        .filter(
                            arrow =>
                                arrow !== middleArrow
                                && !arrow.isSelfLoop
                        )
                        .forEach(arrow => {
                            applyXyArrowToGrid(
                                grid,
                                gridRow,
                                gridCol,
                                arrow,
                                arrowLayout
                            );
                        });
                } else {
                    cell.arrows
                        .filter(arrow =>
                            !arrow.isSelfLoop
                            && !(
                                useDiagonalOverlay
                                && window.MathCmsRenderXyParser.isXyDiagonalDirection(
                                    arrow.direction
                                )
                            )
                        )
                        .forEach(arrow => {
                            applyXyArrowToGrid(
                                grid,
                                gridRow,
                                gridCol,
                                arrow,
                                arrowLayout
                            );
                        });
                }
            });
        });

        const htmlRows = grid.map((row, rowIndex) => {
            const htmlCells = [];
            let colIndex = 0;

            while (colIndex < row.length) {
                const cellHtml = row[colIndex];

                if (cellHtml === XY_VERTICAL_ROWSPAN_COVERED) {
                    colIndex += 1;
                    continue;
                }

                if (isXyPlainHorizontalLineCell(cellHtml)) {
                    let runEnd = colIndex + 1;

                    while (
                        runEnd < row.length
                        && isXyPlainHorizontalLineCell(
                            row[runEnd]
                        )
                    ) {
                        runEnd += 1;
                    }

                    const runCells =
                        row.slice(colIndex, runEnd);

                    const labeledLineCell =
                        runCells.find(value => (
                            value
                            && typeof value === "object"
                            && value.type === "plain-horizontal-line"
                        )) || null;

                    const label =
                        String(
                            labeledLineCell?.label || ""
                        ).trim();

                    const labelPosition =
                        labeledLineCell?.labelPosition
                        || "above";

                    const lineCount =
                        labeledLineCell?.lineCount === 3
                            ? 3
                            : labeledLineCell?.lineCount === 2
                                ? 2
                                : 1;

                    const colspan =
                        runEnd - colIndex;

                    /*
                    * Match the relation width closely to its visible label.
                    *
                    * The [r] or [rr] direction determines the destination cell, but
                    * should not artificially stretch this congruence symbol.
                    */
                    const labelLength =
                        window.MathCmsRenderXyLayout.estimateTexLabelLength(label);

                    const lineWidthEm =
                        label
                            ? Math.max(
                                2.4,
                                1.0 + labelLength * 0.38
                            )
                            : 2.4;

                    const lineHtml =
                        window.MathCmsRenderXyCells.renderHorizontalArrow(
                            label,
                            "right",
                            {
                                horizontalWidthEm: lineWidthEm
                            },
                            {
                                showArrowHead: false,
                                labelPosition,
                                lineCount
                            }
                        );

                    htmlCells.push(`
                        <td
                            colspan="${colspan}"
                            style="
                                padding:0 0.18em;
                                height:1.8em;
                                text-align:center;
                                vertical-align:middle;
                                white-space:nowrap;
                            "
                        >
                            ${lineHtml}
                        </td>
                    `);

                    colIndex = runEnd;
                    continue;
                }

                const isVerticalSegmentCell =
                    /\bpm-xymatrix-vertical-segment\b/.test(cellHtml);

                const padding = isVerticalSegmentCell
                    ? "0"
                    : window.MathCmsRenderXyLayout.getXyMatrixCellPadding(rowIndex, colIndex);

                const cellLineHeight = isVerticalSegmentCell
                    ? "line-height:0;"
                    : "";

                const isArrowSpaceColumn =
                    colIndex % 2 === 1;

                const reservedGapStyle =
                    hasWideDiagonal && isArrowSpaceColumn
                        ? `
                            width:${wideDiagonalGapWidthEm}em;
                            min-width:${wideDiagonalGapWidthEm}em;
                        `
                        : "";

                const reservedGapHtml =
                    hasWideDiagonal
                    && isArrowSpaceColumn
                    && !cellHtml
                        ? `
                            <span
                                aria-hidden="true"
                                style="
                                    display:block;
                                    width:${wideDiagonalGapWidthEm}em;
                                    height:1px;
                                "
                            ></span>
                        `
                        : cellHtml;

                const verticalRowSpanMatch =
                    String(cellHtml || "").match(
                        /\bdata-pm-rowspan="(\d+)"/
                    );

                const verticalRowSpan =
                    verticalRowSpanMatch
                        ? Math.max(Number(verticalRowSpanMatch[1]) || 1, 1)
                        : 1;

                const rowSpanAttribute =
                    verticalRowSpan > 1
                        ? ` rowspan="${verticalRowSpan}"`
                        : "";

                const sourceCoordinateAttributes =
                    rowIndex % 2 === 0
                    && colIndex % 2 === 0
                        ? (
                            ` data-pm-source-row="${rowIndex / 2}"`
                            + ` data-pm-source-col="${colIndex / 2}"`
                        )
                        : "";

                htmlCells.push(`
                    <td${rowSpanAttribute}${sourceCoordinateAttributes} style="
                        padding:${padding};
                        text-align:center;
                        vertical-align:middle;
                        white-space:nowrap;
                        ${cellLineHeight}
                        ${reservedGapStyle}
                    ">
                        ${reservedGapHtml}
                    </td>
                `);

                colIndex += 1;
            }

            return `<tr>${htmlCells.join("")}</tr>`;
        }).join("");

        return `
            <table${diagonalDataAttribute}
                class="pm-xymatrix-table tex2jax_process${hasLegacyTwoCell ? " pm-xymatrix-two-cell-table" : ""}"
                style="
                    border-collapse:collapse;
                    ${hasLegacyTwoCell
                        ? "display:inline-table; vertical-align:middle; margin:1rem 0.45rem;"
                        : "margin:1rem auto;"
                    }
                "
            >
                ${htmlRows}
            </table>
        `;
    }

    function setGridCellIfInBounds(grid, row, col, value) {
        if (
            row < 0 ||
            col < 0 ||
            row >= grid.length ||
            col >= grid[row].length
        ) {
            return;
        }

        grid[row][col] = value;
    }

    function applyXyPlainHorizontalLineToGrid(
        grid,
        gridRow,
        gridCol,
        direction,
        span,
        label = "",
        labelPosition = "above",
        lineCount = 1
    ) {
        const sourceSpan =
            Math.max(Number(span) || 1, 1);

        const step =
            direction === "left"
                ? -1
                : 1;

        /*
        * Expanded Xy grid:
        *
        * object, arrow-space, object, arrow-space, object...
        *
        * A source span of 1 occupies 1 expanded cell.
        * A source span of 2 occupies 3 expanded cells.
        */
        const expandedCellCount =
            sourceSpan * 2 - 1;

        const cleanLabel =
            String(label || "").trim();

        const cleanLineCount =
            lineCount === 3
                ? 3
                : lineCount === 2
                    ? 2
                    : 1;

        const labelOffset =
            Math.ceil(expandedCellCount / 2);

        for (
            let offset = 1;
            offset <= expandedCellCount;
            offset += 1
        ) {
            const cellValue =
                cleanLabel && offset === labelOffset
                    ? {
                        type: "plain-horizontal-line",
                        label: cleanLabel,
                        labelPosition:
                            labelPosition || "above",
                        lineCount: cleanLineCount
                    }
                    : XY_PLAIN_HORIZONTAL_LINE;

            setGridCellIfInBounds(
                grid,
                gridRow,
                gridCol + step * offset,
                cellValue
            );
        }
    }

    function applySpanningVerticalArrowToGrid(
        grid,
        gridRow,
        gridCol,
        label,
        direction,
        span,
        arrowLayout,
        options = {}
    ) {
        const sourceSpan = Math.max(Number(span) || 1, 1);

        /*
        * One source-row jump occupies one expanded arrow row.
        * Additional jumps also cross the intervening object rows.
        *
        *   span 1 -> rowspan 1
        *   span 2 -> rowspan 3
        *   span 3 -> rowspan 5
        */
        const rowSpan = sourceSpan * 2 - 1;

        const startRow =
            direction === "up"
                ? gridRow - rowSpan
                : gridRow + 1;

        const ordinaryArrowHeight =
            arrowLayout.verticalHeightEm || 2.7;

        const intermediateObjectHeight = 1.25;

        const totalHeightEm =
            sourceSpan * ordinaryArrowHeight
            + (sourceSpan - 1) * intermediateObjectHeight;

        setGridCellIfInBounds(
            grid,
            startRow,
            gridCol,
            window.MathCmsRenderXyCells.renderVerticalArrow(
                label,
                direction,
                arrowLayout,
                {
                    rowSpan,
                    heightEm: totalHeightEm,
                    showArrowHead:
                        options.showArrowHead !== false,
                    extendLine: false
                }
            )
        );

        /*
        * These grid positions are occupied by the rowspan cell and must
        * not produce their own table cells.
        */
        for (let offset = 1; offset < rowSpan; offset += 1) {
            setGridCellIfInBounds(
                grid,
                startRow + offset,
                gridCol,
                XY_VERTICAL_ROWSPAN_COVERED
            );
        }
    }

    function applyXyArrowToGrid(grid, gridRow, gridCol, arrow, arrowLayout) {
        const label = arrow.label || "";
        const direction = arrow.direction || "r";
        const span = arrow.span || 1;
        const isPlainLine = arrow.style === "-";
        const isDashed =
            String(arrow.style || "").includes("--");

        if (direction === "r") {
            if (isPlainLine) {
                applyXyPlainHorizontalLineToGrid(
                    grid,
                    gridRow,
                    gridCol,
                    "right",
                    span,
                    label,
                    arrow.labelPosition,
                    arrow.lineCount
                );
                return;
            }

            setGridCellIfInBounds(
                grid,
                gridRow,
                gridCol + 1,
                window.MathCmsRenderXyCells.renderHorizontalArrow(
                    label,
                    "right",
                    arrowLayout,
                    {
                        labelPosition: arrow.labelPosition
                    }
                )
            );
            return;
        }

        if (direction === "l") {
            if (isPlainLine) {
                applyXyPlainHorizontalLineToGrid(
                    grid,
                    gridRow,
                    gridCol,
                    "left",
                    span,
                    label,
                    arrow.labelPosition,
                    arrow.lineCount
                );
                return;
            }

            setGridCellIfInBounds(
                grid,
                gridRow,
                gridCol - 1,
                window.MathCmsRenderXyCells.renderHorizontalArrow(
                    label,
                    "left",
                    arrowLayout,
                    {
                        labelPosition: arrow.labelPosition
                    }
                )
            );
            return;
        }

        if (
            direction === "dl"
            || direction === "dr"
            || direction === "ul"
            || direction === "ur"
        ) {
            const rowOffset =
                direction.includes("d")
                    ? 1
                    : -1;

            const horizontalSpan =
                window.MathCmsRenderXyParser.getXyArrowHorizontalSpan(
                    arrow.directionText
                );

            const colOffset =
                direction.includes("r")
                    ? horizontalSpan
                    : -horizontalSpan;

            setGridCellIfInBounds(
                grid,
                gridRow + rowOffset,
                gridCol + colOffset,
                window.MathCmsRenderXyCells.renderDiagonalArrow(
                    label,
                    direction,
                    arrowLayout,
                    {
                        isDashed,
                        showArrowHead: !isPlainLine,
                        horizontalSpan,
                        labelPosition:
                            arrow.labelPosition
                    }
                )
            );

            return;
        }

        if (direction === "d") {
            applySpanningVerticalArrowToGrid(
                grid,
                gridRow,
                gridCol,
                label,
                "down",
                span,
                arrowLayout,
                {
                    showArrowHead: !isPlainLine
                }
            );
            return;
        }

        if (direction === "u") {
            applySpanningVerticalArrowToGrid(
                grid,
                gridRow,
                gridCol,
                label,
                "up",
                span,
                arrowLayout,
                {
                    showArrowHead: !isPlainLine
                }
            );
        }
    }

    window.MathCmsRenderXyTable = {
        buildHtmlTableFromXyMatrixBody
    };
})();
