// frontend/math/math_render_helpers.js

(function () {
    const DEFAULT_API_ENDPOINT = "http://127.0.0.1:5000/api";

    window.MathCmsRender = {
        debugVersion: "xymatrix-options-v1",
        getDisplayTex,
        prepareConceptHtml,
        cleanLaTeXEnvironments,
        normalizeDiagramImageUrls
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

        clean = cleanLaTeXEnvironments(clean);
        clean = normalizeDiagramImageUrls(clean, apiEndpoint);

        return clean;
    }

    function normalizeEqnarrayHtmlArtifacts(value) {
        return String(value || "")
            // These artifacts can appear inside old rendered_tex equation arrays.
            // Treat paragraph breaks inside eqnarray as equation row breaks.
            .replace(/<br\s*\/?>\s*<\/p>\s*<p[^>]*>/gi, "\\\\")
            .replace(/<\/p>\s*<p[^>]*>/gi, "\\\\")
            .replace(/<br\s*\/?>/gi, "\\\\")

            // Remove any leftover paragraph wrappers.
            .replace(/<\/?p[^>]*>/gi, "")

            // Common HTML whitespace artifact.
            .replace(/&nbsp;/gi, " ");
    }

    function convertEqnarrayToAligned(tex) {
        if (!tex) return "";

        let output = tex;

        // Case 1: already wrapped as \[ \begin{eqnarray} ... \end{eqnarray} \]
        output = output.replace(
            /\\\[\s*\\begin\{(eqnarray\*?)\}([\s\S]*?)\\end\{\1\}\s*\\\]/gi,
            function(_, envName, body) {
                return buildHtmlTableFromEqnarrayBody(body);
            }
        );

        // Case 2: raw standalone \begin{eqnarray} ... \end{eqnarray}
        output = output.replace(
            /\\begin\{(eqnarray\*?)\}([\s\S]*?)\\end\{\1\}/gi,
            function(_, envName, body) {
                return buildHtmlTableFromEqnarrayBody(body);
            }
        );

        return output;
    }

    function buildHtmlTableFromEqnarrayBody(body) {
        const normalizedBody = normalizeEqnarrayHtmlArtifacts(body);

        const rows = splitEqnarrayRows(normalizedBody)
            .map(splitEqnarrayCells)
            .filter(cells => cells.some(cell => cell.trim().length > 0));

        if (rows.length === 0) {
            return "";
        }

        const maxColumns = Math.max(...rows.map(cells => cells.length));

        const htmlRows = rows.map(cells => {
            const paddedCells = padEqnarrayCells(cells, maxColumns);

            const htmlCells = paddedCells.map((cell, index) => {
                const align = getEqnarrayColumnAlign(index);
                const cleanCell = normalizeEqnarrayCell(cell);

                if (!cleanCell) {
                    return `<td style="padding:0.15rem 0.35rem; text-align:${align};"></td>`;
                }

                return `<td style="padding:0.15rem 0.35rem; text-align:${align}; white-space:nowrap;">\\(${escapeHtmlForMathCell(cleanCell)}\\)</td>`;
            }).join("");

            return `<tr>${htmlCells}</tr>`;
        }).join("");

        return `
            <table class="pm-eqnarray-table tex2jax_process" style="border-collapse:collapse; margin:1rem auto;">
                ${htmlRows}
            </table>
        `;
    }

    function splitEqnarrayCells(row) {
        const text = String(row || "");
        const cells = [];
        let start = 0;
        let nestedDepth = 0;

        for (let i = 0; i < text.length; i++) {
            const env = readLatexEnvironmentAt(text, i);

            if (env && isNestedLatexEnvironment(env.name)) {
                if (env.type === "begin") {
                    nestedDepth += 1;
                } else {
                    nestedDepth = Math.max(0, nestedDepth - 1);
                }

                i = env.endIndex - 1;
                continue;
            }

            if (
                nestedDepth === 0 &&
                text[i] === "&" &&
                text[i - 1] !== "\\"
            ) {
                cells.push(text.slice(start, i).trim());
                start = i + 1;
            }
        }

        cells.push(text.slice(start).trim());

        return cells;
    }

    function padEqnarrayCells(cells, maxColumns) {
        const padded = [...cells];

        while (padded.length < maxColumns) {
            padded.push("");
        }

        return padded;
    }

    function getEqnarrayColumnAlign(index) {
        if (index === 0) {
            return "right";
        }

        if (index % 2 === 1) {
            return "center";
        }

        return "left";
    }

    function splitEqnarrayRows(body) {
        const text = String(body || "");
        const rows = [];
        let start = 0;
        let nestedDepth = 0;

        for (let i = 0; i < text.length; i++) {
            const env = readLatexEnvironmentAt(text, i);

            if (env && isNestedLatexEnvironment(env.name)) {
                if (env.type === "begin") {
                    nestedDepth += 1;
                } else {
                    nestedDepth = Math.max(0, nestedDepth - 1);
                }

                i = env.endIndex - 1;
                continue;
            }

            if (
                nestedDepth === 0 &&
                text[i] === "\\" &&
                text[i + 1] === "\\"
            ) {
                rows.push(text.slice(start, i).trim());
                i += 1;
                start = i + 1;
            }
        }

        rows.push(text.slice(start).trim());

        return rows.filter(row => row.length > 0);
    }

    function readLatexEnvironmentAt(text, index) {
        const beginMarker = "\\begin{";
        const endMarker = "\\end{";

        let type = null;
        let marker = null;

        if (text.startsWith(beginMarker, index)) {
            type = "begin";
            marker = beginMarker;
        } else if (text.startsWith(endMarker, index)) {
            type = "end";
            marker = endMarker;
        } else {
            return null;
        }

        const nameStart = index + marker.length;
        const nameEnd = text.indexOf("}", nameStart);

        if (nameEnd === -1) {
            return null;
        }

        return {
            type,
            name: text.slice(nameStart, nameEnd),
            endIndex: nameEnd + 1
        };
    }

    function isNestedLatexEnvironment(name) {
        const normalized = String(name || "").replace(/\*$/, "");

        return [
            "array",
            "cases",
            "matrix",
            "pmatrix",
            "bmatrix",
            "Bmatrix",
            "vmatrix",
            "Vmatrix",
            "smallmatrix",
            "aligned",
            "alignedat",
            "split",
            "gathered",
            "subarray"
        ].includes(normalized);
    }

    function normalizeEqnarrayCell(cell) {
        return normalizeEqnarrayHtmlArtifacts(cell)
            .replace(/\s+/g, " ")
            .trim();
    }

    function escapeHtmlForMathCell(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
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

            const braceStart = findXyMatrixBodyStart(
                tex,
                matrixIndex + "\\xymatrix".length
            );

            if (braceStart === -1) {
                result += tex.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            const braceEnd = findMatchingBrace(tex, braceStart);

            if (braceEnd === -1) {
                result += tex.slice(cursor, matrixIndex + "\\xymatrix".length);
                cursor = matrixIndex + "\\xymatrix".length;
                continue;
            }

            let replaceStart = matrixIndex;
            let replaceEnd = braceEnd + 1;

            const before = tex.slice(0, matrixIndex);
            const displayStartMatch = before.match(/\\\[\s*$/);

            if (displayStartMatch) {
                replaceStart = matrixIndex - displayStartMatch[0].length;
            }

            const after = tex.slice(replaceEnd);
            const displayEndMatch = after.match(/^\s*\\\]/);

            if (displayEndMatch) {
                replaceEnd += displayEndMatch[0].length;
            }

            const body = tex.slice(braceStart + 1, braceEnd);
            const html = buildHtmlTableFromXyMatrixBody(body);

            result += tex.slice(cursor, replaceStart);
            result += html;

            cursor = replaceEnd;
        }

        return result;
    }

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

    function findMatchingBrace(text, openIndex) {
        let depth = 0;

        for (let i = openIndex; i < text.length; i += 1) {
            const char = text[i];
            const prev = text[i - 1];

            if (char === "{" && prev !== "\\") {
                depth += 1;
            } else if (char === "}" && prev !== "\\") {
                depth -= 1;

                if (depth === 0) {
                    return i;
                }
            }
        }

        return -1;
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
            horizontalWidthEm: Math.max(3.2, 2.8 + maxHorizontalLabelLength * 0.38),

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

    function buildHtmlTableFromXyMatrixBody(body) {
        const normalizedBody = normalizeEqnarrayHtmlArtifacts(body);

        const sourceRows = splitEqnarrayRows(normalizedBody)
            .map(row => splitEqnarrayCells(row).map(parseXyMatrixCell))
            .filter(row => row.length > 0);

        if (sourceRows.length === 0) {
            return makeUnsupportedXyMatrixPlaceholder(body);
        }

        const sourceColumnCount = Math.max(...sourceRows.map(row => row.length));
        const arrowLayout = calculateXyMatrixArrowLayout(sourceRows);

        const expandedRowCount = sourceRows.length * 2 - 1;
        const expandedColumnCount = sourceColumnCount * 2 - 1;

        const grid = Array.from({ length: expandedRowCount }, () => {
            return Array.from({ length: expandedColumnCount }, () => "");
        });

        sourceRows.forEach((row, rowIndex) => {
            row.forEach((cell, colIndex) => {
                const gridRow = rowIndex * 2;
                const gridCol = colIndex * 2;

                grid[gridRow][gridCol] = renderXyObjectCell(cell.objectTex);

                cell.arrows.forEach(arrow => {
                    applyXyArrowToGrid(grid, gridRow, gridCol, arrow, arrowLayout);
                });
            });
        });

        const htmlRows = grid.map((row, rowIndex) => {
            const htmlCells = row.map((cellHtml, colIndex) => {
                const padding = getXyMatrixCellPadding(rowIndex, colIndex);

                return `<td style="padding:${padding}; text-align:center; vertical-align:middle; white-space:nowrap;">${cellHtml}</td>`;
            }).join("");

            return `<tr>${htmlCells}</tr>`;
        }).join("");

        return `
            <table class="pm-xymatrix-table tex2jax_process" style="border-collapse:collapse; margin:1rem auto;">
                ${htmlRows}
            </table>
        `;
    }

    function parseXyMatrixCell(rawCell) {
        const text = String(rawCell || "").trim();
        const arrows = [];

        // Supports common Xy-pic variants:
        //   \ar[r]
        //   \ar[d]^f
        //   \ar[r]^{F(x)}
        //   \ar@<0.5ex>[r]^f
        //   \ar@<-0.5ex>[r]_g
        //   \ar@{->}[rd]
        //   \ar@{}[dr]|{=}
        //   \ar@/^1ex/[ddr]
        const arrowPattern =
            /\\ar(?:@\{[^{}]*\}|@<[^>]*>|@[^\s\[\]&{}]+)*(?:\s*\[([^\]]*)\])?((?:\s*(?:[_^](?:[-+])?(?:\{[^{}]*\}|\\?[A-Za-z0-9]+)|\|(?:\{[^{}]*\}|\\?[A-Za-z0-9=+\-]+)))*)/g;

        let match;

        while ((match = arrowPattern.exec(text)) !== null) {
            arrows.push({
                direction: normalizeXyArrowDirection(match[1] || "r"),
                label: extractXyArrowLabel(match[2] || "")
            });
        }

        const objectTex = text
            .replace(arrowPattern, "")
            .replace(/\s+/g, " ")
            .trim();

        return {
            objectTex,
            arrows
        };
    }

    function normalizeXyArrowDirection(direction) {
        const clean = String(direction || "r").toLowerCase();

        if (clean.includes("d")) return "d";
        if (clean.includes("u")) return "u";
        if (clean.includes("l")) return "l";

        return "r";
    }

    function extractXyArrowLabel(modifierText) {
        const text = String(modifierText || "");

        const bracedMatch = text.match(
            /(?:[_^](?:[-+])?|\|)\{([^{}]*)\}/
        );

        if (bracedMatch) {
            return bracedMatch[1].trim();
        }

        const unbracedMatch = text.match(
            /(?:[_^](?:[-+])?|\|)\s*(\\?[A-Za-z0-9=+\-]+)/
        );

        return unbracedMatch ? unbracedMatch[1].trim() : "";
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

    function applyXyArrowToGrid(grid, gridRow, gridCol, arrow, arrowLayout) {
        const label = arrow.label || "";
        const direction = arrow.direction || "r";

        if (direction === "r") {
            setGridCellIfInBounds(
                grid,
                gridRow,
                gridCol + 1,
                renderHorizontalArrow(label, "right", arrowLayout)
            );
            return;
        }

        if (direction === "l") {
            setGridCellIfInBounds(
                grid,
                gridRow,
                gridCol - 1,
                renderHorizontalArrow(label, "left", arrowLayout)
            );
            return;
        }

        if (direction === "d") {
            setGridCellIfInBounds(
                grid,
                gridRow + 1,
                gridCol,
                renderVerticalArrow(label, "down", arrowLayout)
            );
            return;
        }

        if (direction === "u") {
            setGridCellIfInBounds(
                grid,
                gridRow - 1,
                gridCol,
                renderVerticalArrow(label, "up", arrowLayout)
            );
            return;
        }
    }

    function renderXyObjectCell(tex) {
        if (!tex) {
            return "";
        }

        return `\\(${escapeHtmlForMathCell(tex)}\\)`;
    }

    function renderHorizontalArrow(label, direction = "right", arrowLayout = {}) {
        const safeLabel = escapeHtmlForMathCell(label || "");
        const widthEm = arrowLayout.horizontalWidthEm || 3.2;

        const labelHtml = safeLabel
            ? `<div style="
                    position:absolute;
                    left:50%;
                    top:-0.65em;
                    transform:translateX(-50%);
                    white-space:nowrap;
                    line-height:1;
                ">\\({\\scriptstyle ${safeLabel}}\\)</div>`
            : "";

        const arrowHead =
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

        return `
            <div style="
                position:relative;
                width:${widthEm}em;
                height:1.8em;
                display:inline-block;
                vertical-align:middle;
            ">
                <span style="
                    position:absolute;
                    left:0;
                    right:0;
                    top:50%;
                    transform:translateY(-50%);
                    border-top:1.5px solid currentColor;
                "></span>
                ${arrowHead}
                ${labelHtml}
            </div>
        `;
    }

    function renderVerticalArrow(label, direction = "down", arrowLayout = {}) {
        const safeLabel = escapeHtmlForMathCell(label || "");
        const heightEm = arrowLayout.verticalHeightEm || 2.7;
        const widthEm = arrowLayout.verticalWidthEm || 2.4;

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

        const arrowHead =
            direction === "up"
                ? `<span style="
                        position:absolute;
                        left:50%;
                        top:0;
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
                        bottom:0;
                        transform:translateX(-50%);
                        width:0;
                        height:0;
                        border-left:0.30em solid transparent;
                        border-right:0.30em solid transparent;
                        border-top:0.48em solid currentColor;
                    "></span>`;

        return `
            <div style="
                position:relative;
                width:${widthEm}em;
                height:${heightEm}em;
                display:inline-block;
                vertical-align:middle;
            ">
                <span style="
                    position:absolute;
                    left:50%;
                    top:0;
                    bottom:0;
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
                <code>${escapeHtmlForMathCell(body)}</code>
            </div>
        `;
    }

    function normalizeDisplayMathEnvironments(tex) {
        if (!tex) return "";

        return String(tex)
            .replace(/\\begin\{displaymath\}([\s\S]*?)\\end\{displaymath\}/gi, "\\[$1\\]")
            .replace(/\\begin\{equation\*\}([\s\S]*?)\\end\{equation\*\}/gi, "\\[$1\\]")
            .replace(/\\begin\{equation\}([\s\S]*?)\\end\{equation\}/gi, "\\[$1\\]");
    }

    function convertPiecewiseArraysToHtml(tex) {
        if (!tex) return "";

        let output = String(tex);

        // Display-wrapped piecewise arrays:
        // \[ prefix \left\{ \begin{array}{ll} ... \end{array} \right. \]
        // Also catches \left \lbrace and \left\lbrace.
        output = output.replace(
            /\\\[\s*([\s\S]*?)\\left\s*(?:\\?\{|\\lbrace)\s*\\begin\{array\}\{([^{}]*)\}([\s\S]*?)\\end\{array\}\s*\\right\s*\.?\s*\\\]/gi,
            function(_, prefix, columnSpec, body) {
                return buildPiecewiseArrayHtml(prefix, body);
            }
        );

        // $$-wrapped piecewise arrays.
        output = output.replace(
            /\$\$\s*([\s\S]*?)\\left\s*(?:\\?\{|\\lbrace)\s*\\begin\{array\}\{([^{}]*)\}([\s\S]*?)\\end\{array\}\s*\\right\s*\.?\s*\$\$/gi,
            function(_, prefix, columnSpec, body) {
                return buildPiecewiseArrayHtml(prefix, body);
            }
        );

        // Bare piecewise arrays without a clean display wrapper.
        // We intentionally do not try to capture a prefix here, to avoid eating prose before the formula.
        // output = output.replace(
        //     /\\left\s*(?:\\?\{|\\lbrace)\s*\\begin\{array\}\{([^{}]*)\}([\s\S]*?)\\end\{array\}\s*\\right\s*\.?/gi,
        //     function(_, columnSpec, body) {
        //         return buildPiecewiseArrayHtml("", body);
        //     }
        // );

        // Display-wrapped cases environment:
        // \[ prefix \begin{cases} ... \end{cases} \]
        output = output.replace(
            /\\\[\s*([\s\S]*?)\\begin\{cases\}([\s\S]*?)\\end\{cases\}\s*\\\]/gi,
            function(_, prefix, body) {
                return buildPiecewiseArrayHtml(prefix, body);
            }
        );

        // $$-wrapped cases environment.
        output = output.replace(
            /\$\$\s*([\s\S]*?)\\begin\{cases\}([\s\S]*?)\\end\{cases\}\s*\$\$/gi,
            function(_, prefix, body) {
                return buildPiecewiseArrayHtml(prefix, body);
            }
        );

        // Bare cases environment.
        // output = output.replace(
        //     /\\begin\{cases\}([\s\S]*?)\\end\{cases\}/gi,
        //     function(_, body) {
        //         return buildPiecewiseArrayHtml("", body);
        //     }
        // );

        return output;
    }

    function buildPiecewiseArrayHtml(prefix, body) {
        const cleanPrefix = normalizePiecewiseMathCell(prefix);
        const normalizedBody = normalizeEqnarrayHtmlArtifacts(body);

        const rows = splitEqnarrayRows(normalizedBody)
            .map(splitEqnarrayCells)
            .filter(cells => cells.some(cell => cell.trim().length > 0));

        const braceFontSizeRem = Math.max(2.8, rows.length * 1.48);

        if (rows.length === 0) {
            return cleanPrefix ? `\\[${cleanPrefix}\\]` : "";
        }

        const rowHtml = rows.map(cells => {
            const leftCell = normalizePiecewiseMathCell(cells[0] || "");
            const rightCell = normalizePiecewiseMathCell(cells.slice(1).join(" ") || "");

            return `
                <tr>
                    <td style="padding:0.12rem 0.35rem; text-align:left; white-space:nowrap;">\\(${escapeHtmlForMathCell(leftCell)}\\)</td>
                    <td style="padding:0.12rem 0.35rem; text-align:left;">\\(${escapeHtmlForMathCell(rightCell)}\\)</td>
                </tr>
            `;
        }).join("");

        const prefixHtml = cleanPrefix
            ? `<span style="
                    display:inline-block;
                    vertical-align:middle;
                    margin-right:0.35rem;
                    transform:translateY(0.16em);
                ">\\(${escapeHtmlForMathCell(cleanPrefix)}\\)</span>`
            : "";

        return `
            <div class="pm-piecewise-block tex2jax_process" style="text-align:center; margin:1rem 0;">
                ${prefixHtml}
                <span style="
                    display:inline-block;
                    vertical-align:middle;
                    font-size:${braceFontSizeRem.toFixed(2)}rem;
                    line-height:0.9;
                ">{</span>
                <table style="display:inline-table; vertical-align:middle; border-collapse:collapse; text-align:left;">
                    ${rowHtml}
                </table>
            </div>
        `;
    }

    function normalizePiecewiseMathCell(value) {
        return normalizeEqnarrayHtmlArtifacts(value)
            .replace(/\\textrm\{([^{}]*)\}/gi, "\\text{$1}")
            .replace(/\\mbox\{([^{}]*)\}/gi, "\\text{$1}")
            .replace(/\s+/g, " ")
            .trim();
    }

    function cleanLaTeXEnvironments(tex) {
        if (!tex) return "";

        let clean = String(tex || "");

        // Normalize legacy display wrappers so MathJax can process their contents.
        clean = normalizeDisplayMathEnvironments(clean);

        // Convert common PlanetMath piecewise array blocks before MathJax typesetting.
        clean = convertPiecewiseArraysToHtml(clean);

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

        // Normalize legacy eqnarray blocks before MathJax sees them.
        clean = convertEqnarrayToAligned(clean);

        // Convert simple Xy-pic xymatrix diagrams into HTML tables.
        clean = convertXyMatrixToHtml(clean);

        // existing pspicture/list/etc cleanup continues below...
        clean = clean.replace(
            /\\begin\{pspicture\}[\s\S]*?\\end\{pspicture\}/gi,
            `<div class="img-placeholder mathjax-diagnostic-ignore"><em>[PSTricks diagram placeholder]</em></div>`
        );

        clean = clean.replace(/\\begin{enumerate}/gi, "<ol style='margin-top: 0.5rem; padding-left: 1.5rem;'>");
        clean = clean.replace(/\\end{enumerate}/gi, "</ol>");

        clean = clean.replace(/\\begin{itemize}/gi, "<ul style='margin-top: 0.5rem; padding-left: 1.5rem; list-style-type: disc;'>");
        clean = clean.replace(/\\end{itemize}/gi, "</ul>");

        clean = clean.replace(/\\item/gi, "<li style='margin-bottom: 0.25rem;'>");

        clean = clean.replace(/\\emph\{([^}]+)\}/gi, "<em>$1</em>");
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

        return clean;
    }

    function normalizeDiagramImageUrls(html, apiEndpoint = DEFAULT_API_ENDPOINT) {
        if (!html) return "";

        return html.replace(
            /src=(["'])\/api\/math\/diagrams\//gi,
            `src=$1${apiEndpoint}/math/diagrams/`
        );
    }
})();