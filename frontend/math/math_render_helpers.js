// frontend/math/math_render_helpers.js

(function () {
    const DEFAULT_API_ENDPOINT = "http://127.0.0.1:5000/api";

    window.MathCmsRender = {
        debugVersion: "displaymath-normalize-v1",
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
        return String(row || "")
            .split(/(?<!\\)&/g)
            .map(cell => cell.trim());
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
        return String(body || "")
            // Split LaTeX row separators, including optional spacing like \\[4pt].
            .split(/\\\\(?:\s*\[[^\]]*\])?/g)
            .map(row => row.trim())
            .filter(Boolean);
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

            const braceStart = findNextNonSpaceIndex(tex, matrixIndex + "\\xymatrix".length);

            if (braceStart === -1 || tex[braceStart] !== "{") {
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

        const arrowPattern = /\\ar(?:\s*\[([^\]]*)\])?((?:\s*[_^]\{[^{}]*\})*)/g;

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
        const match = String(modifierText || "").match(/[_^]\{([^{}]*)\}/);

        return match ? match[1].trim() : "";
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

    function cleanLaTeXEnvironments(tex) {
        if (!tex) return "";

        let clean = String(tex || "");

        // Normalize legacy display wrappers so MathJax can process their contents.
        clean = normalizeDisplayMathEnvironments(clean);

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