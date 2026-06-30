// frontend/math/mathjax_config.js

(function () {
    window.MathJax = {
        loader: {
            load: [
                "[tex]/ams",
                "[tex]/noerrors",
                "[tex]/noundefined",
                "[tex]/textmacros"
            ]
        },

        tex: {
            inlineMath: [["$", "$"], ["\\(", "\\)"]],
            displayMath: [["$$", "$$"], ["\\[", "\\]"]],
            processEscapes: true,
            packages: {
                "[+]": ["ams", "noerrors", "noundefined", "textmacros"]
            },

            // PlanetMath compatibility aliases.
            // Add newly discovered macros here as smoke tests reveal them.
            macros: {
                down: "{\\mathord{\\downarrow}}",
                dom: "\\operatorname{dom}"
            }
        },

        options: {
            ignoreHtmlClass: "tex2jax_ignore",
            processHtmlClass: "tex2jax_process"
        }
    };

    window.MathCmsMathJax = {
        async typesetElement(element, context = {}) {
            if (!element) {
                return [];
            }

            const ready = await waitForMathJaxReady();

            if (!ready) {
                console.warn("MathJax was not ready before timeout.", context);
                return [];
            }

            if (typeof window.MathJax.typesetClear === "function") {
                window.MathJax.typesetClear([element]);
            }

            await window.MathJax.typesetPromise([element]);

            return reportVisibleLatexCommands(element, context);
        },

        reportVisibleLatexCommands
    };

    async function waitForMathJaxReady(timeoutMs = 8000) {
        const startedAt = Date.now();

        while (Date.now() - startedAt < timeoutMs) {
            if (
                window.MathJax &&
                typeof window.MathJax.typesetPromise === "function"
            ) {
                if (window.MathJax.startup && window.MathJax.startup.promise) {
                    await window.MathJax.startup.promise;
                }

                return true;
            }

            await sleep(50);
        }

        return false;
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function reportVisibleLatexCommands(root, context = {}) {
        const text = collectVisibleText(root);
        const leftovers = findVisibleLatexCommands(text);

        if (leftovers.length > 0) {
            console.warn("Visible unresolved LaTeX commands after MathJax typeset:", {
                context,
                leftovers
            });

            root.dispatchEvent(new CustomEvent("mathjax-leftover-commands", {
                detail: {
                    context,
                    leftovers
                }
            }));
        }

        return leftovers;
    }

    function collectVisibleText(root) {
        const chunks = [];

        const walker = document.createTreeWalker(
            root,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode(node) {
                    const parent = node.parentElement;

                    if (!parent) {
                        return NodeFilter.FILTER_REJECT;
                    }

                    if (
                        parent.closest(
                            [
                                "script",
                                "style",
                                "textarea",
                                "pre",
                                "code",
                                "mjx-assistive-mml",
                                "annotation",
                                "semantics",
                                ".mathjax-diagnostic-ignore"
                            ].join(", ")
                        )
                    ) {
                        return NodeFilter.FILTER_REJECT;
                    }

                    const style = window.getComputedStyle(parent);

                    if (
                        style.display === "none" ||
                        style.visibility === "hidden"
                    ) {
                        return NodeFilter.FILTER_REJECT;
                    }

                    const rect = parent.getBoundingClientRect();

                    if (
                        rect.width === 0 ||
                        rect.height === 0 ||
                        style.opacity === "0" ||
                        style.clipPath !== "none"
                    ) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        while (walker.nextNode()) {
            chunks.push(walker.currentNode.nodeValue || "");
        }

        return chunks.join(" ");
    }

    function findVisibleLatexCommands(text) {
        const commandPattern = /\\[A-Za-z@]+(?:\*)?/g;
        const seen = new Map();

        let match;

        while ((match = commandPattern.exec(text)) !== null) {
            const command = match[0];
            const bareCommand = command.replace(/^\\/, "");

            if (shouldIgnoreCommand(bareCommand)) {
                continue;
            }

            if (!seen.has(command)) {
                seen.set(command, {
                    command,
                    count: 0,
                    examples: []
                });
            }

            const entry = seen.get(command);
            entry.count += 1;

            if (entry.examples.length < 3) {
                entry.examples.push(makeTextSnippet(text, match.index));
            }
        }

        return Array.from(seen.values());
    }

    function shouldIgnoreCommand(command) {
        const ignored = new Set([
            "n",
            "t"
        ]);

        return ignored.has(command);
    }

    function makeTextSnippet(text, index, radius = 45) {
        const start = Math.max(0, index - radius);
        const end = Math.min(text.length, index + radius);

        return text
            .slice(start, end)
            .replace(/\s+/g, " ")
            .trim();
    }
})();