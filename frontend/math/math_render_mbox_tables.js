(() => {
    function normalizeMboxHtmlTableInsideMath(value) {
        let output = String(value || "");

        const decodeHtmlEntities = text => {
            const textarea = document.createElement("textarea");
            textarea.innerHTML = String(text || "");
            return textarea.value;
        };

        const convertRow = rowHtml => {
            const source = decodeHtmlEntities(
                String(rowHtml || "")
                    .replace(/<br\s*\/?>/gi, " ")
                    .replace(/<[^>]+>/g, "")
            ).trim();

            if (!source) {
                return "";
            }

            let result = "";
            let cursor = 0;

            source.replace(
                /\$([^$]*?)\$/g,
                (match, mathBody, offset) => {
                    const prose = source.slice(cursor, offset);

                    if (prose.trim()) {
                        result += `\\mbox{${prose}}`;
                    }

                    result += String(mathBody || "");
                    cursor = offset + match.length;

                    return match;
                }
            );

            const remainder = source.slice(cursor);

            if (remainder.trim()) {
                result += `\\mbox{${remainder}}`;
            }

            return result;
        };

        output = output.replace(
            /\\mbox\s*\{\s*(<div\b[^>]*class=["'][^"']*\bmath-table-wrapper\b[^"']*["'][^>]*>[\s\S]*?<\/div>)\s*\}/gi,
            (match, wrapperHtml) => {
                const rows = [];

                String(wrapperHtml || "").replace(
                    /<tr\b[^>]*>\s*<td\b[^>]*>([\s\S]*?)<\/td>\s*<\/tr>/gi,
                    (rowMatch, cellHtml) => {
                        const row = convertRow(cellHtml);

                        if (row) {
                            rows.push(row);
                        }

                        return rowMatch;
                    }
                );

                if (!rows.length) {
                    return match;
                }

                return (
                    "\\begin{array}{l}" +
                    rows.join(" \\\\ ") +
                    "\\end{array}"
                );
            }
        );

        return output;
    }

    function normalizeMboxTabularInsideMath(value) {
        let output = String(value || "");

        const convertRow = row => {
            const source = String(row || "").trim();

            if (!source) {
                return "";
            }

            let result = "";
            let cursor = 0;

            // Preserve embedded $...$ as mathematics and wrap the surrounding
            // prose in \text{...}.
            source.replace(
                /\$([^$]*?)\$/g,
                (match, mathBody, offset) => {
                    const prose = source.slice(cursor, offset);

                    if (prose) {
                        result += `\\text{${prose}}`;
                    }

                    result += mathBody;
                    cursor = offset + match.length;

                    return match;
                }
            );

            const remainder = source.slice(cursor);

            if (remainder) {
                result += `\\text{${remainder}}`;
            }

            return result;
        };

        output = output.replace(
            /\\mbox\s*\{\s*\\begin\s*\{tabular\}\s*\{[^{}]*\}([\s\S]*?)\\end\s*\{tabular\}\s*\}/gi,
            (match, tableBody) => {
                const rows = String(tableBody || "")
                    .split(/\\\\/)
                    .map(convertRow)
                    .filter(Boolean);

                if (!rows.length) {
                    return "";
                }

                return `\\begin{array}{l}${rows.join(" \\\\ ")}\\end{array}`;
            }
        );

        return output;
    }

    window.MathCmsRenderMboxTables = {
        normalizeMboxHtmlTableInsideMath,
        normalizeMboxTabularInsideMath
    };
})();
