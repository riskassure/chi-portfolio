(() => {
    function splitProofLeadParagraphs(value) {
        const source = String(value || "");

        if (
            !/<strong\b/i.test(source)
            && !source.includes("\u220E")
            && !source.includes("\u25A1")
        ) {
            return source;
        }

        const template = document.createElement("template");
        template.innerHTML = source;

        const proofLeadPattern =
            /^(?:Statement|Existential proof|Constructive proof):$/i;

        function hasMeaningfulContentBefore(element) {
            let sibling = element.previousSibling;

            while (sibling) {
                if (
                    sibling.nodeType === Node.TEXT_NODE
                    && String(sibling.nodeValue || "").trim()
                ) {
                    return true;
                }

                if (
                    sibling.nodeType === Node.ELEMENT_NODE
                    && String(sibling.textContent || "").trim()
                ) {
                    return true;
                }

                sibling = sibling.previousSibling;
            }

            return false;
        }

        /*
        * Move startNode and all following siblings from paragraph into
        * a newly inserted paragraph.
        */
        function splitParagraphAtNode(paragraph, startNode) {
            const newParagraph =
                document.createElement("p");

            let node = startNode;

            while (node) {
                const nextNode = node.nextSibling;
                newParagraph.appendChild(node);
                node = nextNode;
            }

            paragraph.after(newParagraph);

            return newParagraph;
        }

        /*
        * Split flattened proof lead-ins:
        *
        *   preceding prose. <strong>Statement:</strong> ...
        *
        * becomes two paragraphs.
        */
        template.content
            .querySelectorAll("p")
            .forEach(originalParagraph => {
                let paragraph = originalParagraph;

                while (paragraph) {
                    const proofLead = Array.from(
                        paragraph.children
                    ).find(element =>
                        element.tagName === "STRONG"
                        && proofLeadPattern.test(
                            String(element.textContent || "").trim()
                        )
                        && hasMeaningfulContentBefore(element)
                    );

                    if (!proofLead) {
                        break;
                    }

                    paragraph = splitParagraphAtNode(
                        paragraph,
                        proofLead
                    );
                }
            });

        /*
        * Split prose that follows a QED marker:
        *
        *   ... proof text. ∎ Notice, ...
        *
        * becomes:
        *
        *   ... proof text. ∎
        *   Notice, ...
        */
        template.content
            .querySelectorAll("p")
            .forEach(originalParagraph => {
                let paragraph = originalParagraph;

                while (paragraph) {
                    const markerNode = Array.from(
                        paragraph.childNodes
                    ).find(node => {
                        if (node.nodeType !== Node.TEXT_NODE) {
                            return false;
                        }

                        const text =
                            String(node.nodeValue || "");

                        const markerIndex =
                            findProofMarkerIndex(text);

                        if (markerIndex < 0) {
                            return false;
                        }

                        const trailingText =
                            text.slice(markerIndex + 1).trim();

                        return (
                            Boolean(trailingText)
                            || Boolean(node.nextSibling)
                        );
                    });

                    if (!markerNode) {
                        break;
                    }

                    const markerText =
                        String(markerNode.nodeValue || "");

                    const markerIndex =
                        findProofMarkerIndex(markerText);

                    const proofEnding =
                        markerText
                            .slice(0, markerIndex + 1)
                            .replace(/\s+$/g, "");

                    const followingText =
                        markerText
                            .slice(markerIndex + 1)
                            .replace(/^\s+/g, "");

                    markerNode.nodeValue = proofEnding;

                    const newParagraph =
                        document.createElement("p");

                    if (followingText) {
                        newParagraph.appendChild(
                            document.createTextNode(followingText)
                        );
                    }

                    let sibling = markerNode.nextSibling;

                    while (sibling) {
                        const nextSibling = sibling.nextSibling;
                        newParagraph.appendChild(sibling);
                        sibling = nextSibling;
                    }

                    if (
                        String(newParagraph.textContent || "").trim()
                        || newParagraph.children.length
                    ) {
                        paragraph.after(newParagraph);
                        paragraph = newParagraph;
                    } else {
                        break;
                    }
                }
            });

        return template.innerHTML;
    }

    function normalizeSketchProofHeading(clean) {
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

        return clean;
    }

    function standardizeProofEndings(value) {
        const source = String(value || "");

        if (
            !source.includes("math-env-proof")
            && !source.includes("pm-legacy-proof-heading")
            && !/<strong\b[^>]*>\s*Proof\.?\s*<\/strong>/i.test(source)
        ) {
            return source;
        }

        const template = document.createElement("template");
        template.innerHTML = source;

        template.content
            .querySelectorAll(".math-env-proof .math-env-body")
            .forEach(body => {
                body.querySelectorAll(".math-proof-end").forEach(node => node.remove());
                stripTerminalProofMarker(body);
                body.appendChild(makeProofEndMarker());
            });

        template.content
            .querySelectorAll(".pm-legacy-proof-heading")
            .forEach(heading => standardizeLegacyProofEnding(heading));

        template.content
            .querySelectorAll("strong")
            .forEach(heading => {
                if (
                    /^Proof\.?$/i.test(String(heading.textContent || "").trim())
                    && isStandaloneProofHeading(heading)
                ) {
                    const normalizedHeading = document.createElement("em");
                    normalizedHeading.className = "pm-detected-proof-heading";
                    normalizedHeading.textContent = "Proof.";
                    heading.replaceWith(normalizedHeading);
                    standardizeLooseProofEnding(
                        normalizedHeading,
                        template.content
                    );
                }
            });

        return template.innerHTML;
    }

    function findProofMarkerIndex(value) {
        const text = String(value || "");
        const indexes = ["\u220E", "\u25A1"]
            .map(marker => text.indexOf(marker))
            .filter(index => index >= 0);

        return indexes.length ? Math.min(...indexes) : -1;
    }

    function proofMarkerPattern(flags = "i") {
        return new RegExp(
            "(?:Q\\.?\\s*E\\.?\\s*D\\.?"
                + "|[\\u25A1\\u25A0\\u220E]"
                + "|\\\\(?:qed|QED|Box|square|blacksquare))",
            flags
        );
    }

    function meaningfulTextNodes(root) {
        const walker = document.createTreeWalker(
            root,
            NodeFilter.SHOW_TEXT
        );
        const nodes = [];
        let node = walker.nextNode();

        while (node) {
            if (String(node.nodeValue || "").trim()) {
                nodes.push(node);
            }
            node = walker.nextNode();
        }

        return nodes;
    }

    function stripTerminalProofMarker(root) {
        const nodes = meaningfulTextNodes(root);
        const terminalPattern = new RegExp(
            "(?:\\$|\\\\\\)|\\\\\\])?\\s*"
                + proofMarkerPattern().source
                + "\\s*(?:\\$|\\\\\\)|\\\\\\])?\\s*\\.?\\s*$",
            "i"
        );

        for (let index = nodes.length - 1; index >= 0; index -= 1) {
            const node = nodes[index];
            const original = String(node.nodeValue || "");

            if (terminalPattern.test(original)) {
                node.nodeValue = original.replace(terminalPattern, "").replace(/\s+$/g, "");
                return true;
            }

            if (original.trim()) {
                return false;
            }
        }

        return false;
    }

    function makeProofEndMarker() {
        const marker = document.createElement("span");
        marker.className = "math-proof-end mathjax-diagnostic-ignore";
        marker.setAttribute("role", "img");
        marker.setAttribute("aria-label", "End of proof");
        marker.textContent = "\u25A1";
        return marker;
    }

    function standardizeLegacyProofEnding(heading) {
        const headingBlock = heading.closest("p") || heading;
        let sibling = headingBlock.nextSibling;
        let lastTextNode = null;

        while (sibling) {
            if (
                sibling.nodeType === Node.ELEMENT_NODE
                && (
                    sibling.matches(".math-env")
                    || sibling.matches(
                        ".pm-legacy-proof-heading, .pm-legacy-theorem-heading"
                    )
                    || sibling.querySelector(
                        ".pm-legacy-proof-heading, .pm-legacy-theorem-heading"
                    )
                )
            ) {
                break;
            }

            const nodes = meaningfulTextNodes(sibling);

            for (const node of nodes) {
                const text = String(node.nodeValue || "");
                const markerPattern = new RegExp(
                    "(?:^|\\s)" + proofMarkerPattern().source + "\\s*\\.?",
                    "i"
                );
                const match = markerPattern.exec(text);

                if (!match) {
                    if (text.trim()) {
                        lastTextNode = node;
                    }
                    continue;
                }

                const before = text.slice(0, match.index);
                const after = text.slice(match.index + match[0].length);
                const marker = makeProofEndMarker();

                if (before) {
                    node.parentNode.insertBefore(
                        document.createTextNode(before),
                        node
                    );
                }
                node.parentNode.insertBefore(marker, node);
                if (after.trim()) {
                    node.parentNode.insertBefore(
                        document.createTextNode(after.replace(/^\s+/, "")),
                        node
                    );
                }
                node.remove();
                return;
            }

            sibling = sibling.nextSibling;
        }

        appendProofEndAfter(lastTextNode);
    }

    function isStandaloneProofHeading(heading) {
        const paragraph = heading.closest("p");

        if (!paragraph) {
            return false;
        }

        let sibling = heading.previousSibling;

        while (sibling) {
            if (
                sibling.nodeType === Node.TEXT_NODE
                && String(sibling.nodeValue || "").trim()
            ) {
                return false;
            }

            if (
                sibling.nodeType === Node.ELEMENT_NODE
                && String(sibling.textContent || "").trim()
            ) {
                return false;
            }

            sibling = sibling.previousSibling;
        }

        return true;
    }

    function appendProofEndAfter(lastTextNode) {
        if (!lastTextNode || !lastTextNode.parentNode) {
            return;
        }

        const block = lastTextNode.parentElement.closest(
            "p, li, .math-env-body"
        );

        (block || lastTextNode.parentNode).appendChild(makeProofEndMarker());
    }

    function isLooseProofBoundary(element, trigger) {
        if (!element || element === trigger || element.contains(trigger)) {
            return false;
        }

        if (
            element.matches(
                ".pm-legacy-proof-heading, .pm-legacy-theorem-heading, .math-env"
            )
        ) {
            return true;
        }

        if (element.tagName !== "STRONG") {
            return false;
        }

        return /^(?:Proof|Theorem|Proposition|Lemma|Corollary|Definition|Remark|Example)\b/i
            .test(String(element.textContent || "").trim());
    }

    function replaceMarkerInTextNode(node, match) {
        const text = String(node.nodeValue || "");
        const before = text.slice(0, match.index).replace(/\s+$/g, "");
        const after = text
            .slice(match.index + match[0].length)
            .replace(/^\s+/, "");
        const marker = makeProofEndMarker();

        if (before) {
            node.parentNode.insertBefore(document.createTextNode(before), node);
        }
        node.parentNode.insertBefore(marker, node);
        if (after) {
            node.parentNode.insertBefore(document.createTextNode(after), node);
        }
        node.remove();
    }

    function standardizeLooseProofEnding(trigger, root) {
        const walker = document.createTreeWalker(
            root,
            NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT
        );
        const markerPattern = new RegExp(
            "(?:^|\\s)" + proofMarkerPattern().source + "\\s*\\.?",
            "i"
        );
        let started = false;
        let lastTextNode = null;
        let node = walker.nextNode();

        while (node) {
            if (node === trigger) {
                started = true;
                node = walker.nextNode();
                continue;
            }

            if (!started) {
                node = walker.nextNode();
                continue;
            }

            if (
                node.nodeType === Node.ELEMENT_NODE
                && isLooseProofBoundary(node, trigger)
            ) {
                break;
            }

            if (node.nodeType === Node.TEXT_NODE) {
                const text = String(node.nodeValue || "");
                const match = markerPattern.exec(text);

                if (match) {
                    replaceMarkerInTextNode(node, match);
                    return;
                }

                if (text.trim()) {
                    lastTextNode = node;
                }
            }

            node = walker.nextNode();
        }

        appendProofEndAfter(lastTextNode);
    }

    window.MathCmsRenderProofLayout = {
        splitProofLeadParagraphs,
        normalizeSketchProofHeading,
        standardizeProofEndings
    };
})();
