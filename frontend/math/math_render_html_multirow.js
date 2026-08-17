(() => {
    function parseHtmlTableMultirowCell(value) {
        const source = String(value || "").trim();
        const command = "\\multirow";

        if (!source.startsWith(command)) {
            return null;
        }

        let cursor = command.length;

        const readBracedArgument = () => {
            while (cursor < source.length && /\s/.test(source[cursor])) {
                cursor += 1;
            }

            if (source[cursor] !== "{") {
                return null;
            }

            const end = window.MathCmsRenderStructuredMath
                .findMatchingBrace(source, cursor);

            if (end === -1) {
                return null;
            }

            const content = source.slice(cursor + 1, end);
            cursor = end + 1;

            return content;
        };

        const rowCountText = readBracedArgument();
        const widthArgument = readBracedArgument();
        const cellContent = readBracedArgument();

        if (
            rowCountText === null
            || widthArgument === null
            || cellContent === null
        ) {
            return null;
        }

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        if (cursor !== source.length) {
            return null;
        }

        const rowspan = Number(rowCountText.trim());

        if (!Number.isInteger(rowspan) || rowspan < 1) {
            return null;
        }

        return {
            rowspan,
            content: cellContent.trim()
        };
    }


    function normalizeHtmlTableMultirows(value) {
        const source = String(value || "");

        if (
            !source.includes("\\multirow")
            || !/<table\b/i.test(source)
        ) {
            return source;
        }

        return source.replace(
            /<table\b[^>]*>[\s\S]*?<\/table>/gi,
            tableHtml => {
                if (!tableHtml.includes("\\multirow")) {
                    return tableHtml;
                }

                const template = document.createElement("template");
                template.innerHTML = tableHtml.trim();

                const table = template.content.querySelector("table");

                if (!table) {
                    return tableHtml;
                }

                /*
                 * Each entry stores the number of following rows still occupied
                 * by a rowspan at that logical column.
                 */
                const activeRowspans = [];

                Array.from(table.rows).forEach(row => {
                    const sourceCells = Array.from(row.cells);

                    let physicalIndex = 0;
                    let logicalColumn = 0;

                    while (physicalIndex < sourceCells.length) {
                        /*
                         * Skip columns occupied by a rowspan originating in a
                         * previous row. Legacy generated tables commonly retain
                         * an empty placeholder cell in these positions.
                         */
                        while ((activeRowspans[logicalColumn] || 0) > 0) {
                            const candidate = sourceCells[physicalIndex];

                            if (
                                candidate
                                && candidate.textContent.trim() === ""
                            ) {
                                candidate.remove();
                                physicalIndex += 1;
                            }

                            activeRowspans[logicalColumn] -= 1;
                            logicalColumn += 1;
                        }

                        const cell = sourceCells[physicalIndex];

                        if (!cell) {
                            break;
                        }

                        const multirow = parseHtmlTableMultirowCell(
                            cell.innerHTML
                        );

                        if (multirow) {
                            cell.rowSpan = multirow.rowspan;
                            cell.innerHTML = multirow.content;

                            cell.style.textAlign = "center";
                            cell.style.verticalAlign = "middle";

                            activeRowspans[logicalColumn] =
                                multirow.rowspan - 1;
                        }

                        const colspan = Math.max(
                            1,
                            Number(cell.colSpan) || 1
                        );

                        logicalColumn += colspan;
                        physicalIndex += 1;
                    }

                    /*
                     * Account for active rowspans whose following row omitted
                     * the corresponding placeholder cell entirely.
                     */
                    while (logicalColumn < activeRowspans.length) {
                        if ((activeRowspans[logicalColumn] || 0) > 0) {
                            activeRowspans[logicalColumn] -= 1;
                        }

                        logicalColumn += 1;
                    }
                });

                return template.innerHTML;
            }
        );
    }

    window.MathCmsRenderHtmlMultirow = {
        normalizeHtmlTableMultirows
    };
})();
