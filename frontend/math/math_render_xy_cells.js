// frontend/math/math_render_xy_cells.js

(function () {
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

    window.MathCmsRenderXyCells = {
        renderDiagonalArrow,
        renderLegacyTwoCellArrowGroup,
        renderNamedReferenceTwoCell,
        renderXyObjectCell,
        renderHorizontalArrow,
        renderVerticalArrow,
        makeUnsupportedXyMatrixPlaceholder
    };
})();
