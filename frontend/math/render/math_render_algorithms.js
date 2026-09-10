(() => {
    function normalizeAlgorithmHtmlFragment(value) {
        return String(value || "")
            .replace(/\\label\s*\{[^{}]*\}/gi, "")
            .replace(/\r?\n/g, " ")
            .replace(/[ \t]{2,}/g, " ")
            .trim();
    }

    function normalizeAlgorithmCodeBlocks(value) {
        const source = String(value || "");

        const decodeBackslashEntities = text =>
            String(text || "")
                .replace(/&#(?:0*92|x0*5c);/gi, "\\")
                .replace(/&bsol;/gi, "\\");

        const detectableSource =
            decodeBackslashEntities(source);

        if (
            !source.includes("math-code-block-alg")
            || !/\\begin\s*\{description\}/i.test(
                detectableSource
            )
        ) {
            return source;
        }

        return source.replace(
            /<pre\b[^>]*class=["'][^"']*\bmath-code-block-alg\b[^"']*["'][^>]*>\s*<code\b[^>]*>([\s\S]*?)<\/code>\s*<\/pre>/gi,
            function (originalHtml, codeHtml) {
                const cleanCode =
                    decodeBackslashEntities(codeHtml)
                        .replace(
                            /\\label\s*\{[^{}]*\}/gi,
                            ""
                        )
                        .trim();

                const descriptionMatch = cleanCode.match(
                    /^([\s\S]*?)\\begin\s*\{description\}([\s\S]*?)\\end\s*\{description\}([\s\S]*)$/i
                );

                if (!descriptionMatch) {
                    return originalHtml;
                }

                const introduction = normalizeAlgorithmHtmlFragment(
                    descriptionMatch[1]
                );

                const descriptionBody = String(
                    descriptionMatch[2] || ""
                );

                const trailingContent = normalizeAlgorithmHtmlFragment(
                    descriptionMatch[3]
                );

                const items = [];
                const itemPattern =
                    /\\item\s*\[([^\]]+)\]([\s\S]*?)(?=\\item\s*\[[^\]]+\]|$)/gi;

                let itemMatch;

                while (
                    (itemMatch = itemPattern.exec(descriptionBody)) !== null
                ) {
                    const label = String(itemMatch[1] || "").trim();
                    const content = normalizeAlgorithmHtmlFragment(
                        itemMatch[2]
                    );

                    if (!label || !content) {
                        continue;
                    }

                    items.push({
                        label,
                        content
                    });
                }

                if (items.length === 0) {
                    return originalHtml;
                }

                const itemRows = items.map(item => `
                    <div style="
                        display:grid;
                        grid-template-columns:minmax(5.5rem, max-content) minmax(0, 1fr);
                        gap:0.35rem 0.85rem;
                        align-items:start;
                        margin-top:0.55rem;
                    ">
                        <strong>${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(item.label)}</strong>
                        <div>${item.content}</div>
                    </div>
                `).join("");

                return `
                    <section
                        class="pm-algorithm-block tex2jax_process"
                        style="
                            margin:1rem 0;
                            padding:1rem 1.1rem;
                            border-left:3px solid #cbd5e1;
                            background:#f8fafc;
                            line-height:1.55;
                        "
                    >
                        <div style="
                            font-weight:700;
                            margin-bottom:0.65rem;
                        ">
                            Algorithm.
                        </div>

                        ${introduction
                            ? `<div style="margin-bottom:0.75rem;">${introduction}</div>`
                            : ""
                        }

                        <div>
                            ${itemRows}
                        </div>

                        ${trailingContent
                            ? `<div style="margin-top:0.75rem;">${trailingContent}</div>`
                            : ""
                        }
                    </section>
                `;
            }
        );
    }

    window.MathCmsRenderAlgorithms = {
        normalizeAlgorithmCodeBlocks
    };
})();
