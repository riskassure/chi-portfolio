// frontend/math/math_render_helpers.js

(function () {
    const DEFAULT_API_ENDPOINT = "http://127.0.0.1:5000/api";

    window.MathCmsRender = {
        debugVersion: "multline-protection-v1",
        getDisplayTex,
        prepareConceptHtml,
        cleanLaTeXEnvironments,
        normalizeDiagramImageUrls,
        renderXyMatrixDiagonalOverlays
    };

    function getDisplayTex(concept) {
        return (
            concept?.display_tex ||
            concept?.rendered_tex ||
            concept?.cleaned_tex ||
            "No textual mathematical content saved."
        );
    }

    function prepareConceptHtml(tex, options = {}) {
        const apiEndpoint =
            options.apiEndpoint ||
            window.MATH_CMS_API_ENDPOINT ||
            DEFAULT_API_ENDPOINT;

        let clean = tex || "";

        /*
        * Expand concept-local \newcommand definitions before the
        * ordinary rendering cleanup pipeline.
        */
        if (
            window.MathCmsLocalMacros &&
            typeof window.MathCmsLocalMacros.apply === "function"
        ) {
            clean = window.MathCmsLocalMacros.apply(
                clean,
                options.localMacroSource || "",
                options.context || {}
            );
        }

        clean = cleanLaTeXEnvironments(clean);
        clean =
            window.MathCmsRenderMathText
                .restoreUnderlineHtmlInsideMath(clean);
        clean = normalizeDiagramImageUrls(
            clean,
            apiEndpoint
        );

        return clean;
    }

    function convertUnderbracedXyMatrixToHtml(tex) {
        const source = String(tex || "");

        let result = "";
        let cursor = 0;

        while (cursor < source.length) {
            const underbraceIndex = source.indexOf("\\underbrace", cursor);

            if (underbraceIndex === -1) {
                result += source.slice(cursor);
                break;
            }

            const contentStart =
                window.MathCmsRenderXyParser
                    .findNextNonSpaceIndex(
                        source,
                        underbraceIndex + "\\underbrace".length
                    );

            if (contentStart === -1 || source[contentStart] !== "{") {
                result += source.slice(cursor, underbraceIndex + "\\underbrace".length);
                cursor = underbraceIndex + "\\underbrace".length;
                continue;
            }

            const contentEnd = window.MathCmsRenderStructuredMath
                .findMatchingBrace(source, contentStart);

            if (contentEnd === -1) {
                result += source.slice(cursor);
                break;
            }

            const content = source.slice(contentStart + 1, contentEnd).trim();

            if (!content.startsWith("\\xymatrix")) {
                result += source.slice(cursor, contentEnd + 1);
                cursor = contentEnd + 1;
                continue;
            }

            const subscriptMatch = source
                .slice(contentEnd + 1)
                .match(/^\s*_\s*\{/);

            if (!subscriptMatch) {
                result += source.slice(cursor, contentEnd + 1);
                cursor = contentEnd + 1;
                continue;
            }

            const labelStart =
                contentEnd + 1 +
                subscriptMatch[0].lastIndexOf("{");

            const labelEnd = window.MathCmsRenderStructuredMath
                .findMatchingBrace(source, labelStart);

            if (labelEnd === -1) {
                result += source.slice(cursor);
                break;
            }

            const matrixStart = content.indexOf("\\xymatrix");
            const matrixBraceStart =
                window.MathCmsRenderXyParser
                    .findXyMatrixBodyStart(
                        content,
                        matrixStart + "\\xymatrix".length
                    );

            const matrixBraceEnd =
                matrixBraceStart === -1
                    ? -1
                    : window.MathCmsRenderStructuredMath
                        .findMatchingBrace(content, matrixBraceStart);

            if (matrixBraceEnd === -1) {
                result += source.slice(cursor, labelEnd + 1);
                cursor = labelEnd + 1;
                continue;
            }

            const matrixBody = content.slice(
                matrixBraceStart + 1,
                matrixBraceEnd
            );

            const rawLabel = source.slice(labelStart + 1, labelEnd);

            const cleanLabel = rawLabel
                .replace(/\\displaystyle\s*/gi, "")
                .replace(/\\mbox\s*\{([^{}]*)\}/gi, "\\text{$1}")
                .trim();

            const html = `
                <figure class="pm-underbraced-xymatrix tex2jax_process" style="
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    width:max-content;
                    max-width:100%;
                    margin:1rem auto;
                ">
                    ${buildHtmlTableFromXyMatrixBody(matrixBody)}

                    <div aria-hidden="true" style="
                        width:100%;
                        height:0.55rem;
                        border-bottom:1.5px solid currentColor;
                        border-left:1.5px solid currentColor;
                        border-right:1.5px solid currentColor;
                        border-radius:0 0 45% 45%;
                        margin-top:-0.7rem;
                    "></div>

                    <figcaption style="margin-top:0.2rem;">
                        \\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanLabel)}\\)
                    </figcaption>
                </figure>
            `;

            let replaceStart = underbraceIndex;
            let replaceEnd = labelEnd + 1;

            const before = source.slice(0, underbraceIndex);

            // Support either \[ ... \] or $$ ... $$.
            const latexDisplayStartMatch = before.match(/\\\[\s*$/);
            const dollarDisplayStartMatch = before.match(/\$\$\s*$/);

            let displayWrapper = "";

            if (latexDisplayStartMatch) {
                replaceStart =
                    underbraceIndex - latexDisplayStartMatch[0].length;
                displayWrapper = "latex";
            } else if (dollarDisplayStartMatch) {
                replaceStart =
                    underbraceIndex - dollarDisplayStartMatch[0].length;
                displayWrapper = "dollar";
            }

            if (displayWrapper === "latex") {
                const displayEndMatch = source
                    .slice(replaceEnd)
                    .match(/^\s*\\\]/);

                if (displayEndMatch) {
                    replaceEnd += displayEndMatch[0].length;
                }
            } else if (displayWrapper === "dollar") {
                const displayEndMatch = source
                    .slice(replaceEnd)
                    .match(/^\s*\$\$/);

                if (displayEndMatch) {
                    replaceEnd += displayEndMatch[0].length;
                }
            }

            result += source.slice(cursor, replaceStart);
            result += html;

            cursor = replaceEnd;
        }

        return result;
    }

    function convertXyMatrixToHtml(tex) {
        if (!tex) return "";

        let result = "";
        let cursor = 0;

        while (cursor < tex.length) {
            const matrixIndex = tex.indexOf("\\xymatrix", cursor);

            if (matrixIndex === -1) {
                result += tex.slice(cursor);
                break;
            }

            const braceStart =
                window.MathCmsRenderXyParser
                    .findXyMatrixBodyStart(
                        tex,
                        matrixIndex + "\\xymatrix".length
                    );

            if (braceStart === -1) {
                result += tex.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            const braceEnd = window.MathCmsRenderStructuredMath
                .findMatchingBrace(tex, braceStart);

            if (braceEnd === -1) {
                result += tex.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            let replaceStart = matrixIndex;
            let replaceEnd = braceEnd + 1;

            const before = tex.slice(0, matrixIndex);
            const after = tex.slice(replaceEnd);

            const displayStartMatch =
                before.match(/\\\[\s*$/);

            const inlineStartCandidate =
                displayStartMatch
                    ? null
                    : before.match(/\$([^$\r\n]*)$/);

            const inlineStartMatch =
                inlineStartCandidate
                && !String(
                    inlineStartCandidate[1] || ""
                ).includes("\\xymatrix")
                    ? inlineStartCandidate
                    : null;

            const inlineEndMatch =
                inlineStartMatch
                    ? after.match(/^\s*\$/)
                    : null;

            let leadingInlineMath = "";

            if (displayStartMatch) {
                replaceStart =
                    matrixIndex - displayStartMatch[0].length;

            } else if (
                inlineStartMatch
                && inlineEndMatch
            ) {
                replaceStart =
                    matrixIndex - inlineStartMatch[0].length;

                replaceEnd += inlineEndMatch[0].length;

                leadingInlineMath =
                    String(inlineStartMatch[1] || "").trim();
            }

            // A display xymatrix commonly ends with punctuation:
            //
            //   \xymatrix{...}.
            //   \xymatrix{...},
            //
            // Consume that punctuation together with the closing display delimiter,
            // then restore it outside the generated diagram HTML.
            const displayEndMatch = after.match(
                /^(\s*[.,;:]?)\s*\\\]/
            );

            let trailingDisplayPunctuation = "";

            if (displayEndMatch) {
                trailingDisplayPunctuation = displayEndMatch[1].trim();
                replaceEnd += displayEndMatch[0].length;
            }

            const body =
                tex.slice(braceStart + 1, braceEnd);

            const matrixHtml =
                buildHtmlTableFromXyMatrixBody(body);

            let html;

            if (leadingInlineMath) {
                /*
                * Source forms such as:
                *
                *   $P:\xymatrix{...}$
                *
                * place the label directly beside the diagram. Remove the matrix's
                * ordinary standalone margin and center the combined unit.
                */
                const compactMatrixHtml =
                    matrixHtml.replace(
                        "margin:1rem auto;",
                        "margin:0;"
                    );

                html = `
                    <div
                        class="pm-xymatrix-labeled-display tex2jax_process"
                        style="
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            gap:1.00rem;
                            margin:1rem 0;
                        "
                    >
                        <span style="white-space:nowrap;">
                            \\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(leadingInlineMath)}\\)
                        </span>

                        ${compactMatrixHtml}
                    </div>

                    ${trailingDisplayPunctuation}
                `;

            } else {
                html =
                    matrixHtml +
                    trailingDisplayPunctuation;
            }

            result += tex.slice(cursor, replaceStart);
            result += html;

            cursor = replaceEnd;
        }

        return result;
    }

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

    function recoverLostXyMatrixRowSeparators(value) {
        let source = String(value || "");

        /*
        * Some legacy xymatrix row separators arrive as one backslash
        * immediately before a physical newline:
        *
        *     ... \ar[d] \ 
        *     NextRow
        *
        * Recover that lone slash as the intended TeX row separator.
        */
        source = source.replace(
            /\\[ \t]*\r?\n(?=[ \t]*\S)/g,
            "\\\\\n"
        );

        /*
        * Other legacy rows lose both the second slash and the physical
        * newline, commonly before a new \mathcal object:
        *
        *     ... \ \mathcal{C}
        */
        source = source.replace(
            /\\\s+(?=\\mathcal\s*\{)/g,
            "\\\\ "
        );

        return source;
    }

    function buildHtmlTableFromXyMatrixBody(body) {
        const normalizedBody = recoverLostXyMatrixRowSeparators(
            window.MathCmsRenderStructuredMath
                .normalizeEqnarrayHtmlArtifacts(body)
        );

        const sourceRows = window.MathCmsRenderStructuredMath
            .splitEqnarrayRows(normalizedBody)
            .map(row => window.MathCmsRenderStructuredMath
                .splitEqnarrayCells(row).map(parseXyMatrixCell))
            .filter(row => row.length > 0);

        const hasLegacyTwoCell = sourceRows
            .flat()
            .some(cell => cell.legacyTwoCell);

        if (sourceRows.length === 0) {
            return makeUnsupportedXyMatrixPlaceholder(body);
        }

        const sourceColumnCount = Math.max(...sourceRows.map(row => row.length));
        const arrowLayout = calculateXyMatrixArrowLayout(sourceRows);

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
                        if (!isXyDiagonalDirection(arrow.direction)) {
                            return;
                        }

                        const {
                            rowDelta,
                            colDelta
                        } = getXyArrowCoordinateDelta(
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
                    && getXyArrowHorizontalSpan(arrow.directionText) > 1
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

                const objectHtml = renderXyObjectCell(
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
                        renderNamedReferenceTwoCell(cell.twoCellLabel)
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
                        renderLegacyTwoCellArrowGroup(
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
                                && isXyDiagonalDirection(
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
                        estimateTexLabelLength(label);

                    const lineWidthEm =
                        label
                            ? Math.max(
                                2.4,
                                1.0 + labelLength * 0.38
                            )
                            : 2.4;

                    const lineHtml =
                        renderHorizontalArrow(
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
                    : getXyMatrixCellPadding(rowIndex, colIndex);

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

    let xyMatrixOverlayMarkerSerial = 0;

    function parseXyCurveAmountToPixels(value, element) {
        const text =
            String(value || "").trim();

        const fontSize =
            Number.parseFloat(
                window.getComputedStyle(element).fontSize
            ) || 16;

        if (!text) {
            return fontSize * 0.5;
        }

        const match = text.match(
            /^([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(ex|em|px|pt|pc|cm|mm|in)?$/i
        );

        if (!match) {
            return fontSize * 0.5;
        }

        const amount =
            Number(match[1]) || 0;

        const unit =
            String(match[2] || "ex").toLowerCase();

        switch (unit) {
            case "px":
                return amount;

            case "em":
                return amount * fontSize;

            case "pt":
                return amount * 96 / 72;

            case "pc":
                return amount * 16;

            case "cm":
                return amount * 96 / 2.54;

            case "mm":
                return amount * 96 / 25.4;

            case "in":
                return amount * 96;

            case "ex":
            default:
                return amount * fontSize * 0.5;
        }
    }

    function getXyRectangleBoundaryDistance(
        rect,
        unitX,
        unitY
    ) {
        const halfWidth =
            Math.max(rect.width / 2, 1);

        const halfHeight =
            Math.max(rect.height / 2, 1);

        const horizontalDistance =
            Math.abs(unitX) > 0.0001
                ? halfWidth / Math.abs(unitX)
                : Number.POSITIVE_INFINITY;

        const verticalDistance =
            Math.abs(unitY) > 0.0001
                ? halfHeight / Math.abs(unitY)
                : Number.POSITIVE_INFINITY;

        return Math.min(
            horizontalDistance,
            verticalDistance
        );
    }

    function createXyOverlayArrowMarker(
        svg,
        markerId
    ) {
        const namespace =
            "http://www.w3.org/2000/svg";

        let defs =
            svg.querySelector("defs");

        if (!defs) {
            defs =
                document.createElementNS(
                    namespace,
                    "defs"
                );

            svg.appendChild(defs);
        }

        const marker =
            document.createElementNS(
                namespace,
                "marker"
            );

        marker.setAttribute("id", markerId);
        marker.setAttribute("markerWidth", "5.5");
        marker.setAttribute("markerHeight", "5.5");
        marker.setAttribute("refX", "5.1");
        marker.setAttribute("refY", "2.75");
        marker.setAttribute("orient", "auto");
        marker.setAttribute(
            "markerUnits",
            "strokeWidth"
        );

        const markerPath =
            document.createElementNS(
                namespace,
                "path"
            );

        markerPath.setAttribute(
            "d",
            "M0,0 L5.5,2.75 L0,5.5 Z"
        );

        markerPath.setAttribute(
            "fill",
            "currentColor"
        );

        marker.appendChild(markerPath);
        defs.appendChild(marker);
    }

    function getXyOverlayObjectAnchor(cell) {
        if (!cell) {
            return null;
        }

        /*
        * After MathJax typesets a plain object, its mjx-container is
        * normally the direct child of the coordinate <td>.
        *
        * Framed objects and self-loop objects use our own wrappers.
        */
        return (
            cell.querySelector(
                ":scope > .pm-xymatrix-object-with-loops,"
                + ":scope > .pm-xymatrix-state,"
                + ":scope > mjx-container"
            )
            || cell
        );
    }

    function getXyOverlayCoordinateKey(row, col) {
        return `${Number(row)}:${Number(col)}`;
    }

    function wrapScrollableXyMatrixTables(
        root = document
    ) {
        const scope =
            root
            && typeof root.querySelectorAll === "function"
                ? root
                : document;

        const tables = Array.from(
            scope.querySelectorAll(
                "table.pm-xymatrix-table"
                + ":not([data-pm-diagonal-arrows])"
            )
        );

        tables.forEach(table => {
            /*
            * Preserve specialized layouts that already manage their own
            * positioning or participate in a larger inline construction.
            */
            if (
                table.classList.contains(
                    "pm-xymatrix-two-cell-table"
                )
                || table.closest(
                    ".pm-xymatrix-labeled-display,"
                    + ".pm-xymatrix-sequence,"
                    + ".pm-underbraced-xymatrix,"
                    + ".pm-xymatrix-scroll"
                )
            ) {
                return;
            }

            if (!table.parentNode) {
                return;
            }

            const wrapper =
                document.createElement("div");

            wrapper.className =
                "pm-xymatrix-scroll";

            wrapper.style.display = "block";
            wrapper.style.width = "100%";
            wrapper.style.maxWidth = "100%";
            wrapper.style.overflowX = "auto";
            wrapper.style.boxSizing = "border-box";
            wrapper.style.margin = "1rem 0";
            wrapper.style.paddingBottom = "0.35rem";

            table.parentNode.insertBefore(
                wrapper,
                table
            );

            wrapper.appendChild(table);

            /*
            * The wrapper now owns the vertical margin. Keep the mathematical
            * chain at its natural one-line width inside the scroll area.
            */
            table.style.margin = "0 auto";
            table.style.width = "max-content";
            table.style.maxWidth = "none";
        });

        const sequences = Array.from(
            scope.querySelectorAll(
                ".pm-xymatrix-sequence"
            )
        );

        sequences.forEach(sequence => {
            /*
            * A mixed Xy-matrix sequence is already one semantic mathematical
            * chain. Keep its pieces on one line and scroll the whole sequence
            * when it is wider than the concept column.
            */
            sequence.style.width = "100%";
            sequence.style.maxWidth = "100%";
            sequence.style.flexWrap = "nowrap";
            sequence.style.overflowX = "auto";
            sequence.style.overflowY = "hidden";
            sequence.style.boxSizing = "border-box";
            sequence.style.paddingBottom = "0.35rem";

            /*
            * Start overflowing chains at the left edge so their beginning
            * remains visible. Continue centering chains that already fit.
            */
            sequence.style.justifyContent = "flex-start";

            if (
                sequence.scrollWidth
                <= sequence.clientWidth + 1
            ) {
                sequence.style.justifyContent = "center";
            }
        });
    }

    async function renderXyMatrixDiagonalOverlays(
        root = document
    ) {
        const scope =
            root && typeof root.querySelectorAll === "function"
                ? root
                : document;

        const tables = Array.from(
            scope.querySelectorAll(
                "table.pm-xymatrix-table"
                + "[data-pm-diagonal-arrows]"
            )
        );

        const labelsToTypeset = [];

        for (const table of tables) {
            let arrows = [];

            try {
                arrows = JSON.parse(
                    decodeURIComponent(
                        table.getAttribute(
                            "data-pm-diagonal-arrows"
                        ) || ""
                    )
                );
            } catch (error) {
                console.warn(
                    "Unable to decode xymatrix diagonal metadata:",
                    error
                );

                continue;
            }

            if (!Array.isArray(arrows) || arrows.length === 0) {
                continue;
            }

            /*
            * Identify an outer universal-property node such as Z.
            *
            * In the pullback and pushout diagrams, Z participates in three
            * diagonal arrows:
            *
            *     h together with r and s
            *     h together with u and v
            *
            * Move that actual rendered object slightly outside the original
            * commutative square, without changing the table's layout.
            */
            const objectCells = Array.from(
                table.querySelectorAll(
                    "td[data-pm-source-row][data-pm-source-col]"
                )
            );

            const sourceRows = objectCells.map(cell =>
                Number(
                    cell.getAttribute("data-pm-source-row")
                )
            );

            const sourceCols = objectCells.map(cell =>
                Number(
                    cell.getAttribute("data-pm-source-col")
                )
            );

            const minSourceRow =
                Math.min(...sourceRows);

            const maxSourceRow =
                Math.max(...sourceRows);

            const minSourceCol =
                Math.min(...sourceCols);

            const maxSourceCol =
                Math.max(...sourceCols);

            const diagonalDegree = new Map();

            arrows.forEach(arrow => {
                const sourceKey =
                    getXyOverlayCoordinateKey(
                        arrow.sourceRow,
                        arrow.sourceCol
                    );

                const targetKey =
                    getXyOverlayCoordinateKey(
                        arrow.targetRow,
                        arrow.targetCol
                    );

                diagonalDegree.set(
                    sourceKey,
                    (diagonalDegree.get(sourceKey) || 0) + 1
                );

                diagonalDegree.set(
                    targetKey,
                    (diagonalDegree.get(targetKey) || 0) + 1
                );
            });

            /*
            * Reset earlier positioning first. This matters when the overlay
            * function is called again after previewing or resizing.
            */
            objectCells.forEach(cell => {
                const anchor =
                    getXyOverlayObjectAnchor(cell);

                if (!anchor) {
                    return;
                }

                anchor.style.position = "relative";
                anchor.style.left = "0px";
                anchor.style.top = "0px";
            });

            objectCells.forEach(cell => {
                const row =
                    Number(
                        cell.getAttribute("data-pm-source-row")
                    );

                const col =
                    Number(
                        cell.getAttribute("data-pm-source-col")
                    );

                const key =
                    getXyOverlayCoordinateKey(row, col);

                /*
                * Ordinary square corners participate in at most one overlay
                * diagonal. The external Z participates in three.
                */
                if ((diagonalDegree.get(key) || 0) < 3) {
                    return;
                }

                let shiftX = 0;
                let shiftY = 0;

                if (col === minSourceCol) {
                    shiftX = -26;
                } else if (col === maxSourceCol) {
                    shiftX = 26;
                }

                if (row === minSourceRow) {
                    shiftY = -18;
                } else if (row === maxSourceRow) {
                    shiftY = 18;
                }

                const anchor =
                    getXyOverlayObjectAnchor(cell);

                if (!anchor) {
                    return;
                }

                anchor.style.position = "relative";
                anchor.style.left = `${shiftX}px`;
                anchor.style.top = `${shiftY}px`;
            });

            let wrapper =
                table.parentElement
                && table.parentElement.classList.contains(
                    "pm-xymatrix-overlay-wrapper"
                )
                    ? table.parentElement
                    : null;

            if (!wrapper) {
                wrapper =
                    document.createElement("div");

                wrapper.className =
                    "pm-xymatrix-overlay-wrapper";

                const isInlineSequence =
                    Boolean(
                        table.closest(
                            ".pm-xymatrix-sequence"
                        )
                    );

                wrapper.style.position = "relative";
                wrapper.style.display =
                    isInlineSequence
                        ? "inline-block"
                        : "block";

                wrapper.style.width = "max-content";
                wrapper.style.maxWidth = "100%";
                wrapper.style.verticalAlign = "middle";
                wrapper.style.overflow = "visible";
                wrapper.style.margin =
                    isInlineSequence
                        ? "0"
                        : "1rem auto";

                table.parentNode.insertBefore(
                    wrapper,
                    table
                );

                wrapper.appendChild(table);

                /*
                * The wrapper now owns the outer margin.
                */
                table.style.margin = "0";
            }

            wrapper
                .querySelectorAll(
                    ":scope > .pm-xymatrix-diagonal-overlay,"
                    + ":scope > .pm-xymatrix-diagonal-label"
                )
                .forEach(node => node.remove());

            const tableRect =
                table.getBoundingClientRect();

            const wrapperRect =
                wrapper.getBoundingClientRect();

            const namespace =
                "http://www.w3.org/2000/svg";

            const svg =
                document.createElementNS(
                    namespace,
                    "svg"
                );

            svg.classList.add(
                "pm-xymatrix-diagonal-overlay"
            );

            svg.setAttribute(
                "viewBox",
                `0 0 ${tableRect.width} ${tableRect.height}`
            );

            svg.setAttribute(
                "width",
                String(tableRect.width)
            );

            svg.setAttribute(
                "height",
                String(tableRect.height)
            );

            svg.style.position = "absolute";
            svg.style.left =
                `${tableRect.left - wrapperRect.left}px`;

            svg.style.top =
                `${tableRect.top - wrapperRect.top}px`;

            svg.style.width =
                `${tableRect.width}px`;

            svg.style.height =
                `${tableRect.height}px`;

            svg.style.overflow = "visible";
            svg.style.pointerEvents = "none";
            svg.style.zIndex = "2";
            svg.style.color = "currentColor";

            wrapper.appendChild(svg);

            const orderedArrows = [...arrows].sort(
                (leftArrow, rightArrow) => {
                    const leftIsDotted =
                        String(leftArrow.style || "")
                            .includes(".");

                    const rightIsDotted =
                        String(rightArrow.style || "")
                            .includes(".");

                    /*
                    * Solid arrows first; dotted universal arrow h last.
                    */
                    return (
                        Number(leftIsDotted)
                        - Number(rightIsDotted)
                    );
                }
            );

            orderedArrows.forEach(arrow => {
                const sourceCell =
                    table.querySelector(
                        `td[data-pm-source-row="${arrow.sourceRow}"]`
                        + `[data-pm-source-col="${arrow.sourceCol}"]`
                    );

                const targetCell =
                    table.querySelector(
                        `td[data-pm-source-row="${arrow.targetRow}"]`
                        + `[data-pm-source-col="${arrow.targetCol}"]`
                    );

                if (!sourceCell || !targetCell) {
                    return;
                }

                const sourceAnchor =
                    getXyOverlayObjectAnchor(sourceCell);

                const targetAnchor =
                    getXyOverlayObjectAnchor(targetCell);

                if (!sourceAnchor || !targetAnchor) {
                    return;
                }

                const sourceRect =
                    sourceAnchor.getBoundingClientRect();

                const targetRect =
                    targetAnchor.getBoundingClientRect();

                const sourceCenterX =
                    sourceRect.left
                    + sourceRect.width / 2
                    - tableRect.left;

                const sourceCenterY =
                    sourceRect.top
                    + sourceRect.height / 2
                    - tableRect.top;

                const targetCenterX =
                    targetRect.left
                    + targetRect.width / 2
                    - tableRect.left;

                const targetCenterY =
                    targetRect.top
                    + targetRect.height / 2
                    - tableRect.top;

                const deltaX =
                    targetCenterX - sourceCenterX;

                const deltaY =
                    targetCenterY - sourceCenterY;

                const length =
                    Math.hypot(deltaX, deltaY);

                if (length < 1) {
                    return;
                }

                const unitX =
                    deltaX / length;

                const unitY =
                    deltaY / length;

                const sourceBoundary =
                    getXyRectangleBoundaryDistance(
                        sourceRect,
                        unitX,
                        unitY
                    );

                const targetBoundary =
                    getXyRectangleBoundaryDistance(
                        targetRect,
                        unitX,
                        unitY
                    );

                const sourceKey =
                    getXyOverlayCoordinateKey(
                        arrow.sourceRow,
                        arrow.sourceCol
                    );

                const targetKey =
                    getXyOverlayCoordinateKey(
                        arrow.targetRow,
                        arrow.targetCol
                    );

                /*
                * The outer universal-property node Z participates in three
                * diagonal arrows. Give arrows slightly more breathing room
                * where they meet that node.
                */
                const sourceEndpointPadding =
                    (diagonalDegree.get(sourceKey) || 0) >= 3
                        ? 6
                        : 3;

                const targetEndpointPadding =
                    (diagonalDegree.get(targetKey) || 0) >= 3
                        ? 6
                        : 3;

                const startX =
                    sourceCenterX
                    + unitX * (
                        sourceBoundary
                        + sourceEndpointPadding
                    );

                const startY =
                    sourceCenterY
                    + unitY * (
                        sourceBoundary
                        + sourceEndpointPadding
                    );

                const endX =
                    targetCenterX
                    - unitX * (
                        targetBoundary
                        + targetEndpointPadding
                    );

                const endY =
                    targetCenterY
                    - unitY * (
                        targetBoundary
                        + targetEndpointPadding
                    );

                const normalX = -unitY;
                const normalY = unitX;

                const curveSign =
                    arrow.curveSide === "^"
                        ? -1
                        : arrow.curveSide === "_"
                            ? 1
                            : 0;

                const curveAmount =
                    curveSign === 0
                        ? 0
                        : parseXyCurveAmountToPixels(
                            arrow.curveAmount,
                            table
                        );

                const controlX =
                    (startX + endX) / 2
                    + normalX
                        * curveAmount
                        * curveSign;

                const controlY =
                    (startY + endY) / 2
                    + normalY
                        * curveAmount
                        * curveSign;

                const style =
                    String(arrow.style || "->");

                const isInvisible =
                    style === "";

                const isPlainLine =
                    style === "-";

                const isDotted =
                    style.includes(".");

                const isDashed =
                    style.includes("--");

                if (!isInvisible) {
                    const path =
                        document.createElementNS(
                            namespace,
                            "path"
                        );

                    path.setAttribute(
                        "d",
                        curveSign === 0
                            ? (
                                `M ${startX} ${startY}`
                                + ` L ${endX} ${endY}`
                            )
                            : (
                                `M ${startX} ${startY}`
                                + ` Q ${controlX} ${controlY}`
                                + ` ${endX} ${endY}`
                            )
                    );

                    path.setAttribute("fill", "none");
                    path.setAttribute(
                        "stroke",
                        "currentColor"
                    );

                    path.setAttribute(
                        "stroke-width",
                        isDotted ? "1.9" : "1.6"
                    );

                    path.setAttribute(
                        "vector-effect",
                        "non-scaling-stroke"
                    );

                    if (isDotted) {
                        path.setAttribute(
                            "stroke-dasharray",
                            "2 4"
                        );
                    } else if (isDashed) {
                        path.setAttribute(
                            "stroke-dasharray",
                            "7 5"
                        );
                    }

                    if (!isPlainLine) {
                        const markerId =
                            `pm-xymatrix-overlay-head-`
                            + (
                                ++xyMatrixOverlayMarkerSerial
                            );

                        createXyOverlayArrowMarker(
                            svg,
                            markerId
                        );

                        path.setAttribute(
                            "marker-end",
                            `url(#${markerId})`
                        );
                    }

                    svg.appendChild(path);
                }

                if (!arrow.label) {
                    return;
                }

                /*
                * Quadratic Bézier midpoint at t = 0.5.
                */
                const pathMidX =
                    0.25 * startX
                    + 0.5 * controlX
                    + 0.25 * endX;

                const pathMidY =
                    0.25 * startY
                    + 0.5 * controlY
                    + 0.25 * endY;

                const labelSide =
                    arrow.labelPosition === "above"
                        ? -1
                        : arrow.labelPosition === "below"
                            ? 1
                            : 0;

                const labelOffset =
                    labelSide * 11;

                const label =
                    document.createElement("div");

                label.className =
                    "pm-xymatrix-diagonal-label tex2jax_process";

                label.style.position = "absolute";

                label.style.left =
                    `${
                        tableRect.left
                        - wrapperRect.left
                        + pathMidX
                        + normalX * labelOffset
                    }px`;

                label.style.top =
                    `${
                        tableRect.top
                        - wrapperRect.top
                        + pathMidY
                        + normalY * labelOffset
                    }px`;

                label.style.transform =
                    "translate(-50%, -50%)";

                label.style.padding = "0 0.12em";
                label.style.background =
                    "var(--bs-body-bg, white)";

                label.style.whiteSpace = "nowrap";
                label.style.lineHeight = "1";
                label.style.pointerEvents = "none";
                label.style.zIndex = "3";

                label.textContent =
                    `\\({\\scriptstyle ${arrow.label}}\\)`;

                wrapper.appendChild(label);
                labelsToTypeset.push(label);
            });
        }

        if (
            labelsToTypeset.length > 0
            && window.MathJax
            && typeof window.MathJax.typesetPromise === "function"
        ) {
            await window.MathJax.typesetPromise(
                labelsToTypeset
            );
        }

        wrapScrollableXyMatrixTables(scope);
    }

    function normalizeLegacyTwoCellArrowLabel(value) {
        let label = String(value || "").trim();

        // \stackrel{R}{}  -> R
        // \stackrel{}{T}  -> T
        const stackrelMatch = label.match(
            /^\\stackrel\s*\{([^{}]*)\}\s*\{([^{}]*)\}$/
        );

        if (stackrelMatch) {
            label = (
                String(stackrelMatch[1] || "").trim()
                || String(stackrelMatch[2] || "").trim()
            );
        }

        return label;
    }


    function normalizeLegacyTwoCellInnerLabel(value) {
        let label = String(value || "").trim();

        if (/^\\omit\b/i.test(label)) {
            return "";
        }

        // Remove Xy-pic positioning prefix:
        //   <0>_{\quad \tau}
        //   <-2.5>_{\mbox{ } \tau}
        //   <2.5>^{\mbox{ } \eta}
        label = label.replace(/^<[^>]*>\s*/, "");

        const positionedMatch = label.match(
            /^[_^]\s*\{([\s\S]*)\}$/
        );

        if (positionedMatch) {
            label = positionedMatch[1].trim();
        }

        label = label
            .replace(/\\(?:quad|qquad)\b/g, " ")
            .replace(/\\mbox\s*\{([^{}]*)\}/g, "$1")
            .replace(/\s+/g, " ")
            .trim();

        return label;
    }


    function parseLegacyTwoCellCommandAt(text, commandIndex, commandName) {
        const source = String(text || "");
        const command = `\\${commandName}`;

        if (!source.startsWith(command, commandIndex)) {
            return null;
        }

        let cursor = commandIndex + command.length;

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        // Optional Xy-pic offset such as <4.5>, <-5>, or <9>.
        if (source[cursor] === "<") {
            const offsetEnd = source.indexOf(">", cursor + 1);

            if (offsetEnd === -1) {
                return null;
            }

            cursor = offsetEnd + 1;
        }

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        // Upper commands use ^{...}; lower commands use _{...}.
        if (source[cursor] !== "^" && source[cursor] !== "_") {
            return null;
        }

        cursor += 1;

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        if (source[cursor] !== "{") {
            return null;
        }

        const arrowLabelEnd = window.MathCmsRenderStructuredMath
            .findMatchingBrace(source, cursor);

        if (arrowLabelEnd === -1) {
            return null;
        }

        const rawArrowLabel = source.slice(cursor + 1, arrowLabelEnd);
        cursor = arrowLabelEnd + 1;

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        if (source[cursor] !== "{") {
            return null;
        }

        const innerLabelEnd = window.MathCmsRenderStructuredMath
            .findMatchingBrace(source, cursor);

        if (innerLabelEnd === -1) {
            return null;
        }

        const rawInnerLabel = source.slice(cursor + 1, innerLabelEnd);

        return {
            commandName,
            start: commandIndex,
            end: innerLabelEnd + 1,
            arrowLabel: normalizeLegacyTwoCellArrowLabel(rawArrowLabel),
            innerLabel: normalizeLegacyTwoCellInnerLabel(rawInnerLabel)
        };
    }


    function extractLegacyTwoCellCommands(value) {
        const source = String(value || "");
        const commands = [];

        let cursor = 0;

        while (cursor < source.length) {
            const upperIndex = source.indexOf("\\ruppertwocell", cursor);
            const lowerIndex = source.indexOf("\\rlowertwocell", cursor);

            const candidateIndexes = [upperIndex, lowerIndex]
                .filter(index => index !== -1);

            if (candidateIndexes.length === 0) {
                break;
            }

            const commandIndex = Math.min(...candidateIndexes);
            const commandName =
                commandIndex === upperIndex
                    ? "ruppertwocell"
                    : "rlowertwocell";

            const parsed = parseLegacyTwoCellCommandAt(
                source,
                commandIndex,
                commandName
            );

            if (!parsed) {
                cursor = commandIndex + 1;
                continue;
            }

            commands.push(parsed);
            cursor = parsed.end;
        }

        let cleanText = source;

        [...commands]
            .sort((left, right) => right.start - left.start)
            .forEach(command => {
                cleanText =
                    cleanText.slice(0, command.start)
                    + cleanText.slice(command.end);
            });

        const upper = commands.find(
            command => command.commandName === "ruppertwocell"
        );

        const lower = commands.find(
            command => command.commandName === "rlowertwocell"
        );

        return {
            text: cleanText,
            legacyTwoCell: upper || lower
                ? {
                    upperArrowLabel: upper?.arrowLabel || "",
                    upperInnerLabel: upper?.innerLabel || "",
                    lowerArrowLabel: lower?.arrowLabel || "",
                    lowerInnerLabel: lower?.innerLabel || ""
                }
                : null
        };
    }

    function parseXyMatrixCell(rawCell) {
        const legacyTwoCellResult = extractLegacyTwoCellCommands(rawCell);

        let text = legacyTwoCellResult.text.trim();
        const legacyTwoCell = legacyTwoCellResult.legacyTwoCell;

        const arrows = [];
        let twoCellLabel = "";
        let objectFrame = null;
        let overlayLabel = "";

        /*
        * Legacy Xy-pic crossing-gap marker:
        *
        *   \ar@{-}[rd]|!{"2,1";"1,2"}\hole
        *
        * The HTML/SVG converter already renders the underlying arrow. Remove
        * the placement suffix so it cannot leak into the visible object text
        * or reach MathJax as an undefined command.
        */
        text = text.replace(
            /\|\s*!\s*\{[^{}]*\}\s*\\hole\b/g,
            ""
        );

        /*
        * Legacy Xy-pic saved text object:
        *
        *   \save *\txt{the decimal point} \restore \ar[u]
        *
        * Preserve the visible text and following arrow, but discard the
        * Xy-pic save/restore positioning wrappers.
        */
        text = text.replace(
            /\\save\s*\*\s*\\txt\s*\{([^{}]*)\}\s*\\restore\b/g,
            (_, label) => {
                overlayLabel = String(label || "").trim();
                return "";
            }
        );

        /*
        * Xy-pic framed automaton states:
        *
        *   *+[o][F-]{0}   single-circle state
        *   *++[o][F=]{2}  double-circle accepting state
        */
        text = text.replace(
            /^\s*\*\+*\[o\]\[F([-=])\]\s*\{([^{}]*)\}/,
            function (_, frameStyle, objectLabel) {
                objectFrame = {
                    shape: "circle",
                    doubleBorder: frameStyle === "="
                };

                return String(objectLabel || "").trim();
            }
        );

        // Invisible Xy-pic arrow used to place a relation between two
        // previously named arrows:
        //
        //   \ar@{}"1";"2"|-{=}
        //
        // Preserve the visible relation label, but remove the Xy-pic
        // reference syntax so it cannot leak into the object text.
        text = text.replace(
            /\\ar@\{\}\s*"[^"]+"\s*;\s*"[^"]+"\s*\|\s*-\s*\{([^{}]*)\}/g,
            function (_, relationLabel) {
                twoCellLabel = String(relationLabel || "").trim();
                return "";
            }
        );

        // Xy-pic 2-cell between two previously named arrows:
        //
        //   \ar@{=>}"1";"2"_{\tau}
        //
        // Capture its label separately so the reference syntax does not leak
        // into the rendered object text.
        text = text.replace(
            /\\ar@\{=>\}\s*"[^"]+"\s*;\s*"[^"]+"\s*(?:[_^]\s*(?:\{([^{}]*)\}|(\\?[A-Za-z0-9]+)))?/g,
            function (_, bracedLabel, unbracedLabel) {
                twoCellLabel = String(
                    bracedLabel || unbracedLabel || ""
                ).trim();

                return "";
            }
        );

        // Supports common Xy-pic variants:
        //   \ar[r]
        //   \ar[d]^f
        //   \ar[r]^{F(x)}
        //   \ar@<0.5ex>[r]^f
        //   \ar@<-0.5ex>[r]_g
        //   \ar@{->}[rd]
        //   \ar@{}[dr]|{=}
        //   \ar@/^1ex/[ddr]
        //
        // Also consume optional named-arrow suffixes:
        //   ="1"
        //   ="2"
        const arrowPattern =
            /\\ar(?:@(?:[+-]?(?:\d+(?:\.\d+)?|\.\d+))?\{[^{}]*\}|@<[^>]*>|@[^\s\[\]&{}]+)*(?:\s*\[([^\]]*)\])?((?:\s*(?:[_^](?:[-+])?\s*[<>]*\s*(?:\{(?:[^{}]|\{[^{}]*\})*\}|\\?[A-Za-z0-9]+)|\|(?:\{(?:[^{}]|\{[^{}]*\})*\}|\\?[A-Za-z0-9=+\-]+)))*)\s*(?:=\s*"[^"]+")?/g;

        let match;

        while ((match = arrowPattern.exec(text)) !== null) {
            const directionText = match[1] || "r";

            const styleMatch =
                match[0].match(
                    /@([+-]?(?:\d+(?:\.\d+)?|\.\d+))?\{([^{}]*)\}/
                );

            const styleVariant =
                styleMatch
                    ? String(styleMatch[1] || "").trim()
                    : "";

            const styleLineCount =
                styleVariant === "3"
                    ? 3
                    : styleVariant === "2"
                        ? 2
                        : 1;

            const curveMatch =
                match[0].match(
                    /@\/\s*([_^])\s*([^/]*)\//i
                );

            const labelInfo =
                extractXyArrowLabel(match[2] || "");

                        const selfLoopMatch = match[0].match(
                /@\(\s*([rl])\s*,\s*([ud])\s*\)/i
            );

            arrows.push({
                direction: normalizeXyArrowDirection(directionText),
                directionText,
                span: getXyArrowSpan(directionText),
                style: styleMatch ? styleMatch[2] : "->",
                lineCount: styleLineCount,
                label: labelInfo.text,
                labelPosition: labelInfo.position,

                curveSide:
                    curveMatch
                        ? curveMatch[1]
                        : "",

                curveAmount:
                    curveMatch
                        ? String(curveMatch[2] || "").trim()
                        : "",

                isSelfLoop: Boolean(selfLoopMatch),

                loopSide:
                    selfLoopMatch
                    && selfLoopMatch[1].toLowerCase() === "l"
                        ? "left"
                        : "right",

                loopPlacement:
                    selfLoopMatch
                    && selfLoopMatch[2].toLowerCase() === "d"
                        ? "below"
                        : "above"
            });
        }

        const objectTex = text
            .replace(arrowPattern, "")
            .replace(/\s+/g, " ")

            /*
            * A recovered or partially preserved xymatrix row separator can
            * leave one or more backslashes in an otherwise empty object cell.
            *
            * Without this cleanup, renderXyObjectCell() wraps that residue in
            * generated \( ... \) delimiters, which can display literally.
            */
            .replace(/\\+\s*$/, "")

            .trim();

        return {
            objectTex,
            objectFrame,
            overlayLabel,
            arrows,
            twoCellLabel,
            legacyTwoCell
        };
    }

    function normalizeXyArrowDirection(direction) {
        const clean = String(direction || "r")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        // Preserve diagonal directions before testing single directions.
        if (clean.includes("d") && clean.includes("l")) return "dl";
        if (clean.includes("d") && clean.includes("r")) return "dr";
        if (clean.includes("u") && clean.includes("l")) return "ul";
        if (clean.includes("u") && clean.includes("r")) return "ur";

        if (clean.includes("d")) return "d";
        if (clean.includes("u")) return "u";
        if (clean.includes("l")) return "l";

        return "r";
    }

    function getXyArrowSpan(directionText) {
        const clean = String(directionText || "r")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        return Math.max(clean.length, 1);
    }

    function getXyArrowHorizontalSpan(directionText) {
        const clean = String(directionText || "")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        const horizontalSteps =
            (clean.match(/[lr]/g) || []).length;

        return Math.max(horizontalSteps, 1);
    }

    function isXyDiagonalDirection(direction) {
        return (
            direction === "dl"
            || direction === "dr"
            || direction === "ul"
            || direction === "ur"
        );
    }

    function getXyArrowCoordinateDelta(directionText) {
        const clean = String(directionText || "")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        return {
            rowDelta:
                (clean.match(/d/g) || []).length
                - (clean.match(/u/g) || []).length,

            colDelta:
                (clean.match(/r/g) || []).length
                - (clean.match(/l/g) || []).length
        };
    }

    function extractXyArrowLabel(modifierText) {
        const text = String(modifierText || "");

        const bracedMatch = text.match(
            /([_^|])(?:[-+])?\s*[<>]*\s*\{((?:[^{}]|\{[^{}]*\})*)\}/
        );

        if (bracedMatch) {
            return {
                text: bracedMatch[2].trim(),
                position:
                    bracedMatch[1] === "_"
                        ? "below"
                        : bracedMatch[1] === "^"
                            ? "above"
                            : "center"
            };
        }

        const unbracedMatch = text.match(
            /([_^|])(?:[-+])?\s*[<>]*\s*(\\?[A-Za-z0-9=+\-]+)/
        );

        if (unbracedMatch) {
            return {
                text: unbracedMatch[2].trim(),
                position:
                    unbracedMatch[1] === "_"
                        ? "below"
                        : unbracedMatch[1] === "^"
                            ? "above"
                            : "center"
            };
        }

        return {
            text: "",
            position: "above"
        };
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

    function renderDiagonalArrow(
        label,
        direction = "dr",
        arrowLayout = {},
        options = {}
    ) {
        const safeLabel = window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(label || "");

        const baseWidthEm = Math.max(
            arrowLayout.horizontalWidthEm || 3.6,
            4.2
        );

        const horizontalSpan =
            Math.max(Number(options.horizontalSpan) || 1, 1);

        /*
        * A wide diagonal such as [lld] or [rrd] crosses more than one
        * source-column gap. Keep the owning table cell at zero width so the
        * long SVG can overflow across neighboring cells without stretching
        * the xymatrix column layout.
        */
        const widthEm =
            baseWidthEm * horizontalSpan
            + Math.max(horizontalSpan - 1, 0) * 0.9;

        const layoutWidthEm =
            horizontalSpan > 1
                ? 0
                : widthEm;

        const heightEm = Math.max(
            arrowLayout.verticalHeightEm || 2.7,
            3.2
        );

        const isDashed = options.isDashed === true;

        const showArrowHead =
            options.showArrowHead !== false;

        const labelPosition =
            options.labelPosition || "center";

        const goesRight =
            direction === "dr" || direction === "ur";

        const goesDown =
            direction === "dr" || direction === "dl";

        const startX = goesRight ? 4 : 96;
        const endX = goesRight ? 96 : 4;

        const startY = goesDown ? 4 : 96;
        const endY = goesDown ? 96 : 4;

        let labelTopPercent = 50;
        let labelLeftPercent = 50;

        if (labelPosition === "above") {
            labelTopPercent -= 13;
        } else if (labelPosition === "below") {
            labelTopPercent += 13;
        }

        if (direction === "dl" || direction === "ur") {
            labelLeftPercent +=
                labelPosition === "above" ? 7
                    : labelPosition === "below" ? -7
                        : 0;
        } else {
            labelLeftPercent +=
                labelPosition === "above" ? -7
                    : labelPosition === "below" ? 7
                        : 0;
        }

        const labelHtml = safeLabel
            ? `
                <div style="
                    position:absolute;
                    left:${labelLeftPercent}%;
                    top:${labelTopPercent}%;
                    transform:translate(-50%, -50%);
                    padding:0 0.12em;
                    background:var(--bs-body-bg, white);
                    white-space:nowrap;
                    line-height:1;
                    z-index:2;
                ">
                    \\({\\scriptstyle ${safeLabel}}\\)
                </div>
            `
            : "";

        const markerId =
            `pm-xymatrix-diagonal-head-${direction}-${horizontalSpan}-${isDashed ? "dashed" : "solid"}`;

        const markerDefinition = showArrowHead
            ? `
                <defs>
                    <marker
                        id="${markerId}"
                        markerWidth="8"
                        markerHeight="8"
                        refX="7"
                        refY="4"
                        orient="auto"
                        markerUnits="strokeWidth"
                    >
                        <path
                            d="M0,0 L8,4 L0,8 Z"
                            fill="currentColor"
                        ></path>
                    </marker>
                </defs>
            `
            : "";

        const markerAttribute = showArrowHead
            ? `marker-end="url(#${markerId})"`
            : "";

        return `
            <div class="pm-xymatrix-diagonal-arrow" style="
                position:relative;
                width:${layoutWidthEm}em;
                height:${heightEm}em;
                min-width:${layoutWidthEm}em;
                min-height:${heightEm}em;
                display:inline-block;
                vertical-align:middle;
                overflow:visible;
            ">
                <div style="
                    position:absolute;
                    left:50%;
                    top:0;
                    width:${widthEm}em;
                    height:100%;
                    transform:translateX(-50%);
                    overflow:visible;
                ">
                    <svg
                        aria-hidden="true"
                        viewBox="0 0 100 100"
                        preserveAspectRatio="none"
                        style="
                            position:absolute;
                            inset:0;
                            width:100%;
                            height:100%;
                            overflow:visible;
                        "
                    >
                        ${markerDefinition}

                        <line
                            x1="${startX}"
                            y1="${startY}"
                            x2="${endX}"
                            y2="${endY}"
                            stroke="currentColor"
                            stroke-width="1.8"
                            vector-effect="non-scaling-stroke"
                            ${isDashed
                                ? 'stroke-dasharray="6 5"'
                                : ""
                            }
                            ${markerAttribute}
                        ></line>
                    </svg>

                    ${labelHtml}
                </div>
            </div>
        `;
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
            renderVerticalArrow(
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
                renderHorizontalArrow(
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
                renderHorizontalArrow(
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
                getXyArrowHorizontalSpan(
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
                renderDiagonalArrow(
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

    function renderLegacyTwoCellArrowGroup(
        legacyTwoCell,
        middleArrowLabel = "",
        arrowLayout = {}
    ) {
        if (!legacyTwoCell) {
            return "";
        }

        const upperArrowLabel =
            legacyTwoCell.upperArrowLabel || "";

        const upperInnerLabel =
            legacyTwoCell.upperInnerLabel || "";

        const lowerArrowLabel =
            legacyTwoCell.lowerArrowLabel || "";

        const lowerInnerLabel =
            legacyTwoCell.lowerInnerLabel || "";

        const widthEm =
            Math.max(arrowLayout.horizontalWidthEm || 3.2, 4.6);

        const renderLine = (
            label,
            verticalOffsetEm,
            labelPosition = "above"
        ) => {
            const safeLabel = window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(label);

            const labelPositionStyle =
                labelPosition === "below"
                    ? "top:0.28em;"
                    : "bottom:0.28em;";

            return `
                <div style="
                    position:absolute;
                    left:0;
                    top:${verticalOffsetEm}em;
                    width:${widthEm}em;
                    height:0;
                    border-top:1.5px solid currentColor;
                ">
                    <span aria-hidden="true" style="
                        position:absolute;
                        right:-0.02em;
                        top:-0.31em;
                        width:0;
                        height:0;
                        border-top:0.30em solid transparent;
                        border-bottom:0.30em solid transparent;
                        border-left:0.48em solid currentColor;
                    "></span>

                    ${
                        safeLabel
                            ? `
                                <span style="
                                    position:absolute;
                                    left:50%;
                                    ${labelPositionStyle}
                                    transform:translateX(-50%);
                                    white-space:nowrap;
                                    line-height:1;
                                ">
                                    \\({\\scriptstyle ${safeLabel}}\\)
                                </span>
                            `
                            : ""
                    }
                </div>
            `;
        };

        const transformationLabels = [
            upperInnerLabel,
            lowerInnerLabel
        ].filter(Boolean);

        const transformationHtml = transformationLabels.length
            ? `
                <div style="
                    position:absolute;
                    left:50%;
                    top:50%;
                    transform:translate(-50%, -50%);
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    gap:0.32em;
                    white-space:nowrap;
                    line-height:1;
                    background:var(--bs-body-bg, white);
                    padding:0 0.18em;
                ">
                    ${transformationLabels.map(label => `
                        <span>
                            \\({\\scriptstyle ${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(label)}}\\)
                        </span>
                    `).join("")}
                </div>
            `
            : "";

        const middleArrowHtml = middleArrowLabel
            ? `
                <div style="
                    position:absolute;
                    left:0;
                    top:50%;
                    width:${widthEm}em;
                    height:0;
                    border-top:1.5px solid currentColor;
                    transform:translateY(-50%);
                ">
                    <span aria-hidden="true" style="
                        position:absolute;
                        right:-0.02em;
                        top:-0.31em;
                        width:0;
                        height:0;
                        border-top:0.30em solid transparent;
                        border-bottom:0.30em solid transparent;
                        border-left:0.48em solid currentColor;
                    "></span>

                    <span style="
                        position:absolute;
                        left:50%;
                        bottom:0.22em;
                        transform:translateX(-50%);
                        white-space:nowrap;
                        line-height:1;
                    ">
                        \\({\\scriptstyle ${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(
                            middleArrowLabel
                        )}}\\)
                    </span>
                </div>
            `
            : "";

        return `
            <div class="pm-xymatrix-two-cell" style="
                position:relative;
                width:${widthEm}em;
                height:4.8em;
                min-width:${widthEm}em;
            ">
                ${renderLine(upperArrowLabel, 0.70, "above")}
                ${middleArrowHtml}
                ${renderLine(lowerArrowLabel, 4.10, "below")}
                ${transformationHtml}
            </div>
        `;
    }

    function renderNamedReferenceTwoCell(label) {
        const safeLabel = window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(label || "");

        if (!safeLabel) {
            return "";
        }

        return `
            <div class="pm-xymatrix-named-two-cell" style="
                display:inline-flex;
                align-items:center;
                justify-content:center;
                min-width:2.8em;
                min-height:2.2em;
                white-space:nowrap;
            ">
                \\(\\overset{${safeLabel}}{\\Rightarrow}\\)
            </div>
        `;
    }

    function renderXySelfLoop(arrow) {
        const placement =
            arrow?.loopPlacement === "below"
                ? "below"
                : "above";

        const side =
            arrow?.loopSide === "left"
                ? "left"
                : "right";

        const safeLabel =
            window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(arrow?.label || "");

        const isAbove = placement === "above";
        const isLeft = side === "left";

        /*
         * Draw from left to right for a right-side loop and from right
         * to left for a left-side loop. The arrowhead is placed at endX.
         */
        const startX = isLeft ? 80 : 20;
        const endX = isLeft ? 20 : 80;

        const anchorY = isAbove ? 52 : 8;
        const controlY = isAbove ? 6 : 54;

        /*
         * The polygon overlaps the final section of the curve, so the
         * arrowhead and arc appear to be one continuous stroke.
         */
        const arrowTipY = isAbove ? 59 : 1;
        const arrowBaseY = isAbove ? 47 : 13;

        const arrowPoints = [
            `${endX},${arrowTipY}`,
            `${endX - 6},${arrowBaseY}`,
            `${endX + 6},${arrowBaseY}`
        ].join(" ");

        const wrapperPosition = isAbove
            ? "top:0;"
            : "bottom:0;";

        const labelPosition = isAbove
            ? "top:0.7em;"
            : "bottom:0.7em;";

        return `
            <span
                class="
                    pm-xymatrix-self-loop
                    pm-xymatrix-self-loop-${placement}
                "
                style="
                    position:absolute;
                    left:50%;
                    ${wrapperPosition}
                    transform:translateX(-50%);
                    width:3.6em;
                    height:2.2em;
                    pointer-events:none;
                    overflow:visible;
                    z-index:1;
                "
            >
                <svg
                    aria-hidden="true"
                    viewBox="0 0 100 60"
                    preserveAspectRatio="xMidYMid meet"
                    style="
                        position:absolute;
                        inset:0;
                        width:100%;
                        height:100%;
                        overflow:visible;
                    "
                >
                    <path
                        d="
                            M ${startX} ${anchorY}
                            C ${startX} ${controlY},
                              ${endX} ${controlY},
                              ${endX} ${anchorY}
                        "
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                        stroke-linecap="round"
                        vector-effect="non-scaling-stroke"
                    ></path>

                    <polygon
                        points="${arrowPoints}"
                        fill="currentColor"
                    ></polygon>
                </svg>

                ${
                    safeLabel
                        ? `
                            <span style="
                                position:absolute;
                                left:50%;
                                ${labelPosition}
                                transform:translateX(-50%);
                                white-space:nowrap;
                                line-height:1;
                                z-index:2;
                            ">
                                \\({\\scriptstyle ${safeLabel}}\\)
                            </span>
                        `
                        : ""
                }
            </span>
        `;
    }

    function renderXyObjectCell(
        tex,
        frame = null,
        selfLoops = [],
        overlayLabel = ""
    ) {
        const cleanOverlayLabel =
            String(overlayLabel || "").trim();

        if (!tex && !cleanOverlayLabel) {
            return "";
        }

        /*
        * Xy-pic \save ... \restore text is positioned without contributing
        * to the width of its matrix column.
        */
        if (cleanOverlayLabel) {
            const labelMathHtml =
                `\\(\\text{${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanOverlayLabel)}}\\)`;

            return `
                <span
                    class="pm-xymatrix-overlay-label"
                    style="
                        position:relative;
                        display:inline-block;
                        width:0;
                        height:1.35em;
                        overflow:visible;
                        vertical-align:middle;
                    "
                >
                    <span style="
                        position:absolute;
                        top:0;
                        left:50%;
                        transform:translateX(-50%);
                        white-space:nowrap;
                    ">
                        ${labelMathHtml}
                    </span>
                </span>
            `;
        }

        const mathHtml =
            `\\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(tex)}\\)`;

        let objectHtml;

        if (!frame || frame.shape !== "circle") {
            objectHtml = mathHtml;
        } else if (frame.doubleBorder) {
            objectHtml = `
                <span
                    class="pm-xymatrix-state pm-xymatrix-state-accepting"
                    style="
                        display:inline-flex;
                        align-items:center;
                        justify-content:center;
                        width:2.25em;
                        height:2.25em;
                        border:1.5px solid currentColor;
                        border-radius:50%;
                        box-sizing:border-box;
                    "
                >
                    <span style="
                        display:inline-flex;
                        align-items:center;
                        justify-content:center;
                        width:1.76em;
                        height:1.76em;
                        border:1.5px solid currentColor;
                        border-radius:50%;
                        box-sizing:border-box;
                    ">
                        ${mathHtml}
                    </span>
                </span>
            `;
        } else {
            objectHtml = `
                <span
                    class="pm-xymatrix-state"
                    style="
                        display:inline-flex;
                        align-items:center;
                        justify-content:center;
                        width:2.05em;
                        height:2.05em;
                        border:1.5px solid currentColor;
                        border-radius:50%;
                        box-sizing:border-box;
                    "
                >
                    ${mathHtml}
                </span>
            `;
        }

        const loops = Array.isArray(selfLoops)
            ? selfLoops.filter(
                arrow => arrow?.isSelfLoop
            )
            : [];

        if (loops.length === 0) {
            return objectHtml;
        }

        const hasAboveLoop = loops.some(
            arrow => arrow.loopPlacement !== "below"
        );

        const hasBelowLoop = loops.some(
            arrow => arrow.loopPlacement === "below"
        );

        return `
            <span
                class="pm-xymatrix-object-with-loops"
                style="
                    position:relative;
                    display:inline-flex;
                    align-items:center;
                    justify-content:center;
                    padding-top:${hasAboveLoop ? "2.55em" : "0"};
                    padding-bottom:${hasBelowLoop ? "2.55em" : "0"};
                "
            >
                <span style="
                    position:relative;
                    display:inline-flex;
                    z-index:2;
                ">
                    ${objectHtml}
                </span>

                ${loops.map(renderXySelfLoop).join("")}
            </span>
        `;
    }

    function renderHorizontalArrow(
        label,
        direction = "right",
        arrowLayout = {},
        options = {}
    ) {
        const safeLabel = window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(label || "");
        const showArrowHead = options.showArrowHead !== false;

        const lineCount =
            options.lineCount === 3
                ? 3
                : options.lineCount === 2
                    ? 2
                    : 1;

        const labelPosition =
            options.labelPosition || "above";

        const widthEm =
            arrowLayout.horizontalWidthEm || 3.2;

        const labelVerticalStyle =
            labelPosition === "below"
                ? "top:0.72em;"
                : labelPosition === "center"
                    ? "top:50%; transform:translate(-50%, -50%);"
                    : showArrowHead
                        ? "top:-0.65em;"
                        : "top:0.02em;";

        const labelTransform =
            labelPosition === "center"
                ? ""
                : "transform:translateX(-50%);";

        const labelHtml = safeLabel
            ? `<div style="
                    position:absolute;
                    left:50%;
                    ${labelVerticalStyle}
                    ${labelTransform}
                    white-space:nowrap;
                    line-height:1;
                ">\\({\\scriptstyle ${safeLabel}}\\)</div>`
            : "";

        const lineOffsets =
            lineCount === 3
                ? [-0.16, 0, 0.16]
                : lineCount === 2
                    ? [-0.09, 0.09]
                    : [0];

        /*
        * Ordinary arrows remain vertically centered. Arrowhead-free labeled
        * relations reserve the upper part of the box for the label and place
        * their parallel lines lower.
        */
        const lineCenterPercent =
            showArrowHead
                ? 50
                : 82;

        const lineHtml =
            lineOffsets
                .map(offset => `
                    <span style="
                        position:absolute;
                        left:0;
                        right:0;
                        top:calc(${lineCenterPercent}% + ${offset}em);
                        transform:translateY(-50%);
                        border-top:1.35px solid currentColor;
                    "></span>
                `)
                .join("");

        let arrowHead = "";

        if (showArrowHead) {
            arrowHead =
                direction === "left"
                    ? `<span style="
                            position:absolute;
                            left:0;
                            top:50%;
                            transform:translateY(-50%);
                            width:0;
                            height:0;
                            border-top:0.30em solid transparent;
                            border-bottom:0.30em solid transparent;
                            border-right:0.48em solid currentColor;
                        "></span>`
                    : `<span style="
                            position:absolute;
                            right:0;
                            top:50%;
                            transform:translateY(-50%);
                            width:0;
                            height:0;
                            border-top:0.30em solid transparent;
                            border-bottom:0.30em solid transparent;
                            border-left:0.48em solid currentColor;
                        "></span>`;
        }

        return `
            <div style="
                position:relative;
                width:${widthEm}em;
                height:1.8em;
                display:inline-block;
                vertical-align:middle;
                z-index:1;
            ">
                ${lineHtml}

                ${arrowHead}
                ${labelHtml}
            </div>
        `;
    }

    function renderVerticalArrow(
        label,
        direction = "down",
        arrowLayout = {},
        options = {}
    ) {
        const safeLabel = window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(label || "");

        const heightEm =
            Number(options.heightEm)
            || arrowLayout.verticalHeightEm
            || 2.7;

        const widthEm =
            arrowLayout.verticalWidthEm
            || 2.4;

        const showArrowHead =
            options.showArrowHead !== false;

        const rowSpan =
            Math.max(Number(options.rowSpan) || 1, 1);

        const rowSpanAttribute =
            rowSpan > 1
                ? ` data-pm-rowspan="${rowSpan}"`
                : "";

        const wrapperClass =
            rowSpan > 1
                ? "pm-xymatrix-vertical-segment pm-xymatrix-vertical-span"
                : "pm-xymatrix-vertical-segment";

        const lineEdge =
            options.extendLine === true
                ? "-0.22rem"
                : "0";

        const labelHtml = safeLabel
            ? `<div style="
                    position:absolute;
                    left:calc(50% + 0.38em);
                    top:0;
                    bottom:0;
                    display:flex;
                    align-items:center;
                    white-space:nowrap;
                    line-height:1;
                ">\\({\\scriptstyle ${safeLabel}}\\)</div>`
            : "";

        let arrowHead = "";

        if (showArrowHead) {
            arrowHead =
                direction === "up"
                    ? `<span style="
                            position:absolute;
                            left:50%;
                            top:${lineEdge};
                            transform:translateX(-50%);
                            width:0;
                            height:0;
                            border-left:0.30em solid transparent;
                            border-right:0.30em solid transparent;
                            border-bottom:0.48em solid currentColor;
                        "></span>`
                    : `<span style="
                            position:absolute;
                            left:50%;
                            bottom:${lineEdge};
                            transform:translateX(-50%);
                            width:0;
                            height:0;
                            border-left:0.30em solid transparent;
                            border-right:0.30em solid transparent;
                            border-top:0.48em solid currentColor;
                        "></span>`;
        }

        return `
            <div class="${wrapperClass}"${rowSpanAttribute} style="
                position:relative;
                width:${widthEm}em;
                height:${heightEm}em;
                display:inline-block;
                vertical-align:middle;
            ">
                <span style="
                    position:absolute;
                    left:50%;
                    top:${lineEdge};
                    bottom:${lineEdge};
                    transform:translateX(-50%);
                    border-left:1.5px solid currentColor;
                "></span>

                ${arrowHead}
                ${labelHtml}
            </div>
        `;
    }

    function makeUnsupportedXyMatrixPlaceholder(body) {
        return `
            <div class="mathjax-diagnostic-ignore" style="margin:1rem 0; padding:0.75rem; border:1px dashed #cbd5e1; border-radius:6px; background:#f8fafc; color:#64748b;">
                Unsupported xymatrix diagram:
                <code>${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(body)}</code>
            </div>
        `;
    }

    function cleanLaTeXEnvironments(tex) {
        if (!tex) return "";

        let clean = String(tex || "");

        const eqnarrayProtection =
            window.MathCmsRenderEqnarrayProtection.protectEqnarrayEnvironments(clean);
        clean = eqnarrayProtection.text;

        const verbProtection =
            window.MathCmsRenderVerbatim
                .protectLatexVerbCommands(clean);
        clean = verbProtection.text;

        clean =
            window.MathCmsRenderMboxTables
                .normalizeMboxTabularInsideMath(clean);

        clean =
            window.MathCmsRenderMboxTables
                .normalizeMboxHtmlTableInsideMath(clean);

        clean = window.MathCmsRenderHtmlMultirow
            .normalizeHtmlTableMultirows(clean);

        clean = window.MathCmsRenderAlgorithms.normalizeAlgorithmCodeBlocks(clean);

        const mboxProtection =
            window.MathCmsRenderMathText
                .protectMboxInsideMath(clean);
        clean = mboxProtection.text;

        // Remove TeX comment/separator paragraphs and standalone lines that
        // survived backend rendering.
        clean = clean.replace(
            /<p[^>]*>\s*(?:%+\s*)+<\/p>/gi,
            ""
        );

        /*
        * The backend can combine a commented legacy heading with live content
        * inside the same paragraph:
        *
        *   <p>%<strong>Differential identities..</strong>
        *   <h2>Differential identities</h2>
        *   Several properties ...
        *
        * Remove only the commented legacy heading. Preserve the paragraph and
        * everything following it so structural environments such as align*
        * retain their opening marker and first row.
        */
        clean = clean.replace(
            /(<p\b[^>]*>)\s*%+\s*<strong\b[^>]*>[\s\S]*?<\/strong>\s*/gi,
            "$1"
        );

        /*
        * The backend may wrap an entire commented TeX line in an HTML
        * paragraph before the frontend receives it:
        *
        *   <p>%At this point ...</p>
        *   <p>%&= \lim_{h\to 0} ...</p>
        *
        * Since the first non-whitespace source character is %, the entire
        * paragraph is a TeX comment and must be discarded.
        *
        * Escaped percentages such as \% do not match this rule.
        */
        clean = clean.replace(
            /<p\b[^>]*>\s*%[\s\S]*?<\/p>/gi,
            ""
        );

        // In TeX, a line whose first non-whitespace character is %
        // is entirely commented out and must not reach the rendered page.
        clean = clean.replace(/^[ \t]*%.*(?:\r?\n|$)/gm, "");

        // Backend prose conversion can produce invalid constructs such as:
        //
        //   $<strong>CyclGrp</strong>$
        //
        // HTML tags cannot safely remain inside MathJax dollar delimiters.
        // Preserve the intended HTML formatting, but remove the math delimiters.
        clean = clean.replace(
            /\$\s*<(strong|em|b|i)>([^<>$]*)<\/\1>\s*\$/gi,
            "<$1>$2</$1>"
        );

        // Remove a stray dollar sign left immediately after backend-rendered
        // prose formatting at the end of a sentence:
        //
        //   <em>module homomorphism</em>$.</p>
        //   ->
        //   <em>module homomorphism</em>.</p>
        clean = clean.replace(
            /(<\/(?:em|strong|b|i)>)\s*\$(?=\s*[.,;:!?]\s*(?:<\/p>|<\/li>|<\/div>|$))/gi,
            "$1"
        );

        // Keep bold symbols inside math as TeX instead of later converting
        // them into invalid HTML tags inside MathJax delimiters.
        clean = window.MathCmsRenderMathText.normalizeTextBoldInsideMath(clean);
        clean = window.MathCmsRenderMathText.normalizeTextItalicInsideMath(clean);

        // Repair HTML paragraph artifacts inside cases/array environments before
        // literal < and > characters are protected for safe innerHTML insertion.
        clean =
            window.MathCmsRenderStructuredMath
                .normalizeStructuredMathHtmlArtifacts(clean);

        // Repair paragraph and line-break artifacts inside xymatrix bodies before
        // literal angle brackets inside math are protected as \lt and \gt.
        clean = window.MathCmsRenderXyCleanup
            .normalizeXyMatrixHtmlArtifacts(clean);

        clean = window.MathCmsRenderLegacyTex.normalizeLegacyOverFractions(clean);

        // TeX line-break control has no visible HTML or MathJax meaning.
        clean = clean.replace(/\\nobreak\b/g, "");

        // Remove Xy-pic setup commands that have no visible page meaning.
        clean =
            window.MathCmsRenderXyCleanup
                .stripXyMatrixSetupMacros(clean);

        clean = convertUnderbracedXyMatrixToHtml(clean);
        clean = convertXyMatrixToHtml(clean);

        // Remove display wrappers left around generated Xy-pic HTML.
        clean = window.MathCmsRenderXySequences
            .unwrapConvertedXyMatrixMathWrappers(clean);

        // Render operators stranded between converted xymatrix blocks.
        clean =
            window.MathCmsRenderXyCleanup
                .renderXyMatrixConnectorMath(clean);

        // Temporarily protect generated xymatrix HTML while literal angle brackets
        // in the remaining TeX are normalized.
        const xymatrixHtmlBlocks = [];

        // Protect the entire underbraced xymatrix wrapper first.
        clean = clean.replace(
            /<figure\b[^>]*class=["'][^"']*\bpm-underbraced-xymatrix\b[^"']*["'][^>]*>[\s\S]*?<\/figure>/gi,
            (figureHtml) => {
                const index = xymatrixHtmlBlocks.length;
                xymatrixHtmlBlocks.push(figureHtml);
                return `PMXYMATRIXHTMLPLACEHOLDER${index}END`;
            }
        );

        // Protect ordinary generated xymatrix tables.
        clean = clean.replace(
            /<table\b[^>]*class=["'][^"']*\bpm-xymatrix-table\b[^"']*["'][^>]*>[\s\S]*?<\/table>/gi,
            (tableHtml) => {
                const index = xymatrixHtmlBlocks.length;
                xymatrixHtmlBlocks.push(tableHtml);
                return `PMXYMATRIXHTMLPLACEHOLDER${index}END`;
            }
        );

        clean =
            window.MathCmsRenderHtmlSensitiveMath
                .normalizeHtmlSensitiveMathCharacters(clean);

        // Restore the generated HTML after TeX angle-bracket normalization.
        clean = clean.replace(
            /PMXYMATRIXHTMLPLACEHOLDER(\d+)END/g,
            (match, indexText) => {
                const index = Number(indexText);
                return xymatrixHtmlBlocks[index] ?? match;
            }
        );

        // Normalize legacy display wrappers so MathJax can process their contents.
        clean =
            window.MathCmsRenderDisplayEnvironments
                .normalizeDisplayMathEnvironments(clean);
        clean = window.MathCmsRenderDollarDisplay.normalizeDollarDisplayMath(clean);

        // Convert common PlanetMath piecewise array blocks before MathJax typesetting.
        clean = window.MathCmsRenderPiecewise
            .convertPiecewiseArraysToHtml(clean);

        // Convert align/alignat blocks into HTML alignment tables.
        clean = window.MathCmsRenderAlign
            .convertAlignEnvironmentsToHtml(clean);

        // Convert simple display matrix/array blocks that MathJax often cannot recover
        // after PlanetMath row separators were lost.
        clean = window.MathCmsRenderMatrixDisplay
            .convertSimpleDisplayMatricesToHtml(clean);

        // PlanetMath table color macros.
        // These commonly appear as \red0.01, \blue0.20, or \red{0.01}.
        clean = clean.replace(/\\red\{([^{}]*)\}/gi, '<span class="pm-tex-red">$1</span>');
        clean = clean.replace(/\\blue\{([^{}]*)\}/gi, '<span class="pm-tex-blue">$1</span>');

        clean = clean.replace(/\\red\s*([+-]?\d+(?:\.\d+)?)/gi, '<span class="pm-tex-red">$1</span>');
        clean = clean.replace(/\\blue\s*([+-]?\d+(?:\.\d+)?)/gi, '<span class="pm-tex-blue">$1</span>');

        // PlanetMath font-size macros.
        // Keep braced footnotesize content, but strip unbraced size switches safely.
        clean = clean.replace(
            /\\footnotesize\{([\s\S]*?)\}/gi,
            '<span class="pm-tex-footnotesize">$1</span>'
        );

        clean = clean.replace(/\\footnotesize\b/gi, "");
        clean = clean.replace(/\\scriptsize\b/gi, "");
        clean = clean.replace(/\\small\b/gi, "");
        clean = clean.replace(/\\normalsize\b/gi, "");
        clean = clean.replace(/\\large\b/gi, "");
        clean = clean.replace(/\\Large\b/g, "");
        clean = clean.replace(/\\LARGE\b/g, "");
        clean = clean.replace(/\\huge\b/gi, "");
        clean = clean.replace(/\\Huge\b/g, "");

        // Text-level underline used in PlanetMath prose.
        clean = clean.replace(/\\underline\{([^{}]+)\}/gi, "<u>$1</u>");

        // Normalize the starred legacy form so the existing image converter
        // handles both \includegraphics and \includegraphics*.
        clean = clean.replace(
            /\\includegraphics\*/gi,
            "\\includegraphics"
        );

        // Replace old LaTeX/EPS image commands with readable placeholders.
        clean = window.MathCmsRenderImages.normalizeLatexImageArtifacts(
            clean,
            window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell
        );
        
        // Arrange related placeholders while legacy layout markers
        // such as \raisebox and \hskip are still present.
        clean = window.MathCmsRenderPlaceholderLayout
            .normalizePlaceholderImageLayouts(clean);

        // Preserve visible spacing around prose conjunctions inside math.
        // Plain "and" is treated as math identifiers, so its surrounding
        // spaces disappear after MathJax typesetting.
        clean = clean.replace(
            /\\(?:mbox|textrm|text)\{\s*and\s*\}/gi,
            "\\;\\mathrm{and}\\;"
        );

        // Convert TeX footnotes into visible note blocks while preserving
        // any MathJax expressions contained inside them.
        clean = window.MathCmsRenderFootnotes.normalizeFootnoteMacros(clean);

        // Convert legacy custom Roman-numbered lists before the generic
        // \item conversion later in this pipeline.
        clean =
            window.MathCmsRenderLegacyLists
                .normalizeLegacyRomanList(clean);

        // Prose layout cleanup must not remove legitimate commands such as
        // \quad, \text, or \mbox from inside MathJax expressions.
        const proseMathProtection =
            window.MathCmsRenderProseMath
                .protectMathForProseCleanup(clean);
        clean = proseMathProtection.text;

        clean =
            window.MathCmsRenderProseLayout
                .normalizeProseLayoutMacros(clean);

        clean =
            window.MathCmsRenderProseMath
                .restoreMathAfterProseCleanup(
                    clean,
                    proseMathProtection.blocks
                );

        // Convert inline matrices and expressions containing multiple matrices only
        // after prose wrappers outside math have been normalized.
        clean = window.MathCmsRenderMatrixSequences
            .convertRemainingMatrixMathSequencesToHtml(clean);

        // Restore protected eqnarray blocks only after prose and layout cleanup.
        // This keeps row separators and text commands intact for the converter.
        clean =
            window.MathCmsRenderEqnarrayProtection.restoreEqnarrayEnvironments(
                clean,
                eqnarrayProtection.blocks
            );

        // Normalize legacy eqnarray blocks before MathJax sees them.
        clean = window.MathCmsRenderEqnarray.convertEqnarrayToAligned(clean);

        // Convert the simple PSTricks deduction trees.
        clean = window.MathCmsRenderPstree
            .convertSimpleDeductionPstreeToHtml(clean);

        // Convert the larger fixed diagram used by "rooted-tree".
        clean = window.MathCmsRenderPstree
            .convertRootedTreePstreeToHtml(clean);

        // existing pspicture/list/etc cleanup continues below...
        clean = clean.replace(
            /\\begin\{pspicture\}[\s\S]*?\\end\{pspicture\}/gi,
            `<div class="img-placeholder mathjax-diagnostic-ignore"><em>[PSTricks diagram placeholder]</em></div>`
        );

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

        clean = clean.replace(/\\emph\{([^}]+)\}/gi, "<em>$1</em>");
        clean = clean.replace(/\\textsl\{([^}]+)\}/gi, "<em>$1</em>");
        clean = clean.replace(/\\textbf\{([^}]+)\}/gi, "<strong>$1</strong>");

        clean = clean.replace(
            /\\begin\{(?:the)?bibliography\}\{[\s\S]*?\}/gi,
            "<div style='margin-top: 1.5rem; border-top: 1px dashed #cbd5e1; padding-top: 1rem;'><strong>References & Bibliography:</strong><ul style='list-style-type: square; padding-left: 1.5rem;'>"
        );
        clean = clean.replace(/\\end\{(?:the)?bibliography\}/gi, "</ul></div>");

        clean = clean.replace(/\\begin\{tabular\}\{[^}]*\}([\s\S]*?)\\end\{tabular\}/gi, function(_, body) {
            const rows = body
                .replace(/\\hline/g, "")
                .trim()
                .split(/\\\\/)
                .map(row => row.trim())
                .filter(row => row.length > 0);

            const htmlRows = rows.map((row, rowIndex) => {
                const cells = row.split("&").map(cell => cell.trim());
                const tag = rowIndex === 0 ? "th" : "td";

                return `<tr>` + cells.map(cell =>
                    `<${tag} style="border:1px solid #cbd5e1; padding:0.4rem 0.6rem;">${cell}</${tag}>`
                ).join("") + `</tr>`;
            }).join("");

            return `
                <table style="border-collapse:collapse; margin:1rem 0; width:100%;">
                    ${htmlRows}
                </table>
            `;
        });

        // Final cleanup for TeX separator/comment remnants after all HTML
        // transformations have completed. Some malformed source paragraphs can
        // be restructured by the browser-oriented rendering pipeline, so clean
        // both wrapped and unwrapped percent-only remnants here.
        clean = clean.replace(
            /<p[^>]*>\s*(?:%+\s*(?:<br\s*\/?>)?\s*)+<\/p>/gi,
            ""
        );

        clean = clean.replace(
            /(^|>\s*)%+(?:\s*%+)*(?=\s*(?:<|$))/gmi,
            "$1"
        );

        // Restore protected \verb contents only after all structural parsing
        // and HTML-sensitive processing has completed.
        clean =
            window.MathCmsRenderVerbatim
                .restoreLatexVerbCommands(
                    clean,
                    verbProtection.verbValues
                );

        clean =
            window.MathCmsRenderMathText
                .restoreMboxInsideMath(
                    clean,
                    mboxProtection.values
                );

        /*
        * A TeX \par before "Sketch of proof." can be flattened inside the
        * current list item. Keep the proof in that item, but start its heading
        * on a new visual line.
        */
        clean = clean.replace(
            /<strong\b([^>]*)>\s*Sketch of proof\.\s*<\/strong>/gi,
            `<strong$1 style="
                display:block;
                margin-top:0.75rem;
                margin-bottom:0.2rem;
            ">Sketch of proof.</strong>`
        );

        // Start proof-related lead labels in their own paragraphs when
        // backend HTML has flattened several TeX \par sections together.
        clean =
            window.MathCmsRenderProofLayout
                .splitProofLeadParagraphs(clean);

        // Remove theorem/definition wrappers whose bodies became empty
        clean =
            window.MathCmsRenderMathEnv
                .removeEmptyMathEnvironmentSections(clean);

        // Keep punctuation attached to the inline MathJax expression that
        // immediately precedes it.
        clean = window.MathCmsRenderInlineMath.preventInlineMathPunctuationWrap(clean);

        return clean;
    }

    function normalizeDiagramImageUrls(
        html,
        apiEndpoint = DEFAULT_API_ENDPOINT
    ) {
        return window.MathCmsRenderImages.normalizeDiagramImageUrls(
            html,
            apiEndpoint
        );
    }
})();