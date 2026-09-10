// frontend/math/render/xy/math_render_xy_overlays.js

(function () {
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

    window.MathCmsRenderXyOverlays = {
        renderXyMatrixDiagonalOverlays
    };
})();
