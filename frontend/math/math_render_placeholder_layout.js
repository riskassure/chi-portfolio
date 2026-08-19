(() => {
    function normalizePlaceholderImageLayouts(value) {
        const source = String(value || "");

        if (!source.includes("pm-latex-image-placeholder")) {
            return source;
        }

        const template = document.createElement("template");
        template.innerHTML = source;

        function isPlaceholderBlock(node) {
            if (
                !node
                || node.nodeType !== Node.ELEMENT_NODE
            ) {
                return false;
            }

            if (
                node.classList.contains(
                    "pm-latex-image-placeholder"
                )
            ) {
                return true;
            }

            /*
            * Accept a simple wrapper around one placeholder, but do not
            * treat a larger container holding several placeholders as
            * one image block.
            */
            return (
                node.querySelectorAll(
                    ".pm-latex-image-placeholder"
                ).length === 1
            );
        }

        function isEmptyParagraph(node) {
            return (
                node &&
                node.nodeType === Node.ELEMENT_NODE &&
                node.tagName === "P" &&
                !String(node.textContent || "").trim()
            );
        }

        function isPlaceholderArrow(node) {
            if (!node) {
                return false;
            }

            const text = String(
                node.nodeType === Node.TEXT_NODE
                    ? node.nodeValue
                    : node.textContent
            ).trim();

            return (
                (
                    node.nodeType === Node.ELEMENT_NODE
                    && node.classList.contains("pm-image-arrow")
                )
                || /\\raisebox\b/i.test(text)
                || /\\longleftrightarrow\b/i.test(text)
                || text.includes("↔")
            );
        }

        function isOnlyHfilParagraph(node) {
            return (
                node &&
                node.nodeType === Node.ELEMENT_NODE &&
                node.tagName === "P" &&
                /^\\hfil\s*$/i.test(String(node.textContent || "").trim())
            );
        }

        function isArrowParagraph(node) {
            const text = String(node?.textContent || "").trim();
            return (
                node &&
                node.nodeType === Node.ELEMENT_NODE &&
                node.tagName === "P" &&
                /\\raisebox/i.test(text) &&
                /\\longleftrightarrow/i.test(text)
            );
        }

        // Remove raw \hfil-only paragraphs.
        Array.from(template.content.querySelectorAll("p")).forEach(p => {
            if (isOnlyHfilParagraph(p)) {
                p.remove();
            }
        });

        // Convert raw \centerline{...} paragraph to a real centered caption.
        Array.from(template.content.querySelectorAll("p")).forEach(p => {
            const text = String(p.textContent || "");
            const match = text.match(/\\centerline\s*\{([\s\S]*?)\}/i);

            if (!match) return;

            const div = document.createElement("div");
            div.className = "math-center pm-image-caption";
            div.innerHTML = match[1];
            p.replaceWith(div);
        });

        // Convert raw arrow paragraph to a clean centered arrow.
        Array.from(template.content.querySelectorAll("p")).forEach(p => {
            if (!isArrowParagraph(p)) return;

            const div = document.createElement("div");
            div.className = "math-center pm-image-arrow";
            div.innerHTML = "\\(\\longleftrightarrow\\)";
            p.replaceWith(div);
        });

        // Wrap consecutive placeholder blocks into centered rows.
        const container = document.createElement("div");
        container.appendChild(template.content.cloneNode(true));

        function isIgnorablePlaceholderLayoutNode(node) {
            if (!node) {
                return false;
            }

            if (node.nodeType === Node.TEXT_NODE) {
                const text = String(node.nodeValue || "")
                    .replace(/\\(?:hfil|hfill)\b/gi, "")
                    .trim();

                return !text;
            }

            if (node.nodeType !== Node.ELEMENT_NODE) {
                return false;
            }

            if (isEmptyParagraph(node)) {
                return true;
            }

            const text = String(node.textContent || "")
                .replace(/\\(?:hfil|hfill)\b/gi, "")
                .trim();

            return (
                !text
                && !isPlaceholderBlock(node)
            );
        }

        function collectPlaceholderRuns(parent) {
            const nodes = Array.from(parent.childNodes);
            const runs = [];

            let current = [];

            function flush() {
                const placeholders =
                    current.filter(isPlaceholderBlock);

                if (placeholders.length >= 2) {
                    runs.push(current);
                }

                current = [];
            }

            nodes.forEach(node => {
                if (
                    isPlaceholderBlock(node)
                    || isIgnorablePlaceholderLayoutNode(node)
                ) {
                    current.push(node);
                    return;
                }

                flush();
            });

            flush();

            return runs;
        }

        function nextMeaningfulSibling(node) {
            let sibling = node?.nextSibling || null;

            while (
                sibling
                && isIgnorablePlaceholderLayoutNode(sibling)
            ) {
                sibling = sibling.nextSibling;
            }

            return sibling;
        }

        function groupPlaceholderArrowPairs(parent) {
            let node = parent.firstChild;

            while (node) {
                if (!isPlaceholderBlock(node)) {
                    node = node.nextSibling;
                    continue;
                }

                const arrow =
                    nextMeaningfulSibling(node);

                const rightPlaceholder =
                    nextMeaningfulSibling(arrow);

                if (
                    !isPlaceholderArrow(arrow)
                    || !isPlaceholderBlock(rightPlaceholder)
                ) {
                    node = node.nextSibling;
                    continue;
                }

                const nextNode =
                    rightPlaceholder.nextSibling;

                // Remember all nodes between the two images so leftover
                // empty paragraphs can be removed too.
                const consumedNodes = [];
                let consumedNode = node;

                while (consumedNode) {
                    consumedNodes.push(consumedNode);

                    if (consumedNode === rightPlaceholder) {
                        break;
                    }

                    consumedNode =
                        consumedNode.nextSibling;
                }

                const row =
                    document.createElement("div");

                row.className =
                    "pm-placeholder-row pm-placeholder-arrow-row";

                row.style.display = "grid";
                row.style.gridTemplateColumns =
                    "minmax(0, 1fr) auto minmax(0, 1fr)";
                row.style.alignItems = "center";
                row.style.gap = "1rem";
                row.style.margin = "1rem auto";
                row.style.maxWidth = "44rem";

                const leftItem =
                    document.createElement("div");

                leftItem.className =
                    "pm-placeholder-item";

                const rightItem =
                    document.createElement("div");

                rightItem.className =
                    "pm-placeholder-item";

                parent.insertBefore(row, node);

                leftItem.appendChild(node);
                row.appendChild(leftItem);

                row.appendChild(arrow);

                rightItem.appendChild(rightPlaceholder);
                row.appendChild(rightItem);

                consumedNodes.forEach(consumed => {
                    if (
                        consumed !== node
                        && consumed !== arrow
                        && consumed !== rightPlaceholder
                    ) {
                        consumed.remove();
                    }
                });

                node = nextNode;
            }
        }

        container
            .querySelectorAll(".math-center")
            .forEach(parent => {
                groupPlaceholderArrowPairs(parent);
            });

        const placeholderParents = [
            container,
            ...container.querySelectorAll(".math-center")
        ];

        placeholderParents.forEach(parent => {
            collectPlaceholderRuns(parent).forEach(run => {
                const placeholders =
                    run.filter(isPlaceholderBlock);

                /*
                * Build rows of at most two placeholders. This turns four
                * consecutive knot examples into two rows rather than one
                * oversized four-item row.
                */
                const rows = [];

                for (
                    let index = 0;
                    index < placeholders.length;
                    index += 2
                ) {
                    rows.push(
                        placeholders.slice(index, index + 2)
                    );
                }

                const firstNode = run[0];
                const insertionParent = firstNode.parentNode;

                if (!insertionParent) {
                    return;
                }

                rows.forEach(items => {
                    const row = document.createElement("div");

                    row.className = "pm-placeholder-row";
                    row.style.display = "flex";
                    row.style.justifyContent = "center";
                    row.style.alignItems = "center";
                    row.style.gap = "1rem";
                    row.style.flexWrap = "wrap";
                    row.style.margin = "1rem 0";

                    items.forEach(block => {
                        const item =
                            document.createElement("div");

                        item.className =
                            "pm-placeholder-item";

                        item.style.flex = "0 1 18rem";
                        item.appendChild(
                            block.cloneNode(true)
                        );

                        row.appendChild(item);
                    });

                    insertionParent.insertBefore(
                        row,
                        firstNode
                    );
                });

                run.forEach(node => node.remove());
            });
        });

        return container.innerHTML;
    }

    window.MathCmsRenderPlaceholderLayout = {
        normalizePlaceholderImageLayouts
    };
})();
