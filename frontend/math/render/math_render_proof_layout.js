(() => {
    function splitProofLeadParagraphs(value) {
        const source = String(value || "");

        if (
            !/<strong\b/i.test(source)
            && !source.includes("∎")
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
                            text.indexOf("∎");

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
                        markerText.indexOf("∎");

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

    window.MathCmsRenderProofLayout = {
        splitProofLeadParagraphs,
        normalizeSketchProofHeading
    };
})();
