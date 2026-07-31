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
                dom: "\\operatorname{dom}",
                sgn: "\\operatorname{sgn}",
                N: "\\mathbb{N}",
                NN: "\\mathbb{N}",
                bbZ: "\\mathbb{Z}",
                closure: ["\\overline{#1}", 1],
                hdots: "\\dots",
                ldot: "\\ldots",
                derive: "\\stackrel{*}{\\Rightarrow}",
                tmop: ["\\operatorname{#1}", 1],
                assign: ":=",
                mathbbm: ["#1", 1],
                mathbbmss: ["\\mathbb{#1}", 1],
                mathdd: ["\\mathbb{#1}", 1],
                Span: "\\operatorname{span}",
                Sp: "\\operatorname{span}",
                up: "\\uparrow\\!\\!",
                down: "\\downarrow\\!\\!",

                setOf: [
                    "\\left\\{#1\\;\\middle|\\;#2\\right\\}",
                    2
                ],

                gen: [
                    "\\left\\langle #1 \\right\\rangle",
                    1
                ],

                hom: "\\operatorname{Hom}",
                Hom: "\\operatorname{Hom}",
                Ker: "\\operatorname{Ker}",
                Univ: "\\mathscr{U}",
                liminv: "\\varprojlim",
                limdir: "\\varinjlim",
                Funct: "\\operatorname{Funct}",
                from: "\\leftarrow",

                Prob: "\\mathbb{P}",
                F: "\\mathcal{F}",
                T: "\\mathbb{T}",

                Yleft: "\\mathbin{-\\mkern-5mu\\mathord{<}}",
                Yright: "\\mathbin{\\mathord{>}\\mkern-5mu-}",

                ob: "\\operatorname{Ob}",
                op: "{\\mathrm{op}}",
                eqv: "\\simeq",
                Spec: "\\operatorname{Spec}",
                lra: "\\longrightarrow",
                res: "\\operatorname{res}",
                st: "\\mid",
                Aut: "\\operatorname{Aut}",

                grad: "\\nabla",
                curl: "\\operatorname{curl}",
                div: "\\operatorname{div}",
                real: "\\mathbb{R}",
                complex: "\\mathbb{C}",
                integer: "\\mathbb{Z}",
                integers: "\\mathbb{Z}",
                rational: "\\mathbb{Q}",
                rationals: "\\mathbb{Q}",

                // Harvested PlanetMath aliases:
                // direct symbols, operators, and named sets.
                symd: "\\triangle",
                GCD: "\\operatorname{GCD}",
                kernel: "\\operatorname{Ker}",
                rats: "\\mathbb{Q}",
                Oc: "\\mathbb{O}",
                Sub: "{\\mathrm{Sub}}",

                R: "\\mathbb{R}",
                C: "\\mathbb{C}",
                Z: "\\mathbb{Z}",
                sR: "\\mathbb{R}",
                reals: "\\mathbb{R}",
                RR: "\\mathbb{R}",
                rat: "\\mathbb{Q}",
                ints: "\\mathbb{Z}",
                bbP: "\\mathbb{P}",
                fp: "\\mathbb{F}_p",

                im: "\\operatorname{im}",
                image: "\\operatorname{Im}",
                coim: "\\operatorname{coim}",
                cok: "\\operatorname{cok}",
                rank: "\\operatorname{rank}",
                nullity: "\\operatorname{nullity}",
                card: "\\operatorname{card}",
                kard: "\\operatorname{kard}",
                LCM: "\\operatorname{LCM}",
                diam: "\\operatorname{diam}",
                rad: "\\operatorname{rad}",
                theory: "\\operatorname{Th}",
                Li: "\\operatorname{Li}",

                sech: "\\operatorname{sech}",
                csch: "\\operatorname{csch}",
                arsinh: "\\operatorname{arsinh}",
                arcosh: "\\operatorname{arcosh}",
                artanh: "\\operatorname{artanh}",
                arcoth: "\\operatorname{arcoth}",
                arccot: "\\operatorname{arccot}",
                arcsec: "\\operatorname{arcsec}",

                com: "\\operatorname{C}",
                dcom: "\\operatorname{D}",
                mcom: "\\operatorname{M}",

                Or: "\\vee",
                Iff: "\\Leftrightarrow",
                Implies: "\\Rightarrow",
                proves: "\\vdash",
                impl: "\\Rightarrow",
                Def: "\\overset{\\operatorname{def}}{:=}",

                sse: "\\subseteq",
                spse: "\\supseteq",
                co: "\\colon\\thinspace",
                ra: "\\rightarrow",
                eps: "\\epsilon",
                del: "\\partial",

                I: "\\mathcal{I}",
                val: "\\operatorname{Val}",
                h: "\\operatorname{ht}",
                cc: "\\mathfrak{c}",
                LL: "\\mathsf{L}",
                ser: "\\Sigma a_n",

                Quo: "{\\mathrm{Quo}}",

                D: "\\mathrm{D}",
                O: "\\mathcal{O}",
                A: "\\mathbb{A}",
                vv: "\\mathbf{v}",
                ve: "\\mathbf{e}",
                vx: "\\mathbf{x}",
                vy: "\\mathbf{y}",
                vz: "\\mathbf{z}",
                vw: "\\mathbf{w}",
                vu: "\\mathbf{u}",
                vp: "\\mathbf{p}",
                vs: "\\mathbf{s}",
                vt: "\\mathbf{t}",

                vi: "\\mathbf{i}",
                vj: "\\mathbf{j}",
                vk: "\\mathbf{k}",

                vA: "\\mathbf{A}",
                vB: "\\mathbf{B}",
                vC: "\\mathbf{C}",
                vF: "\\mathbf{F}",
                vG: "\\mathbf{G}",
                vH: "\\mathbf{H}",
                vX: "\\mathbf{X}",
                vY: "\\mathbf{Y}",
                vZ: "\\mathbf{Z}",

                norm: ["\\left\\lVert #1 \\right\\rVert", 1],
                abs: ["\\left\\lvert #1 \\right\\rvert", 1],
                ip: ["\\left\\langle #1 \\right\\rangle", 1],
                line: ["\\overleftrightarrow{#1}", 1],

                lp: "(",
                rp: ")",

                pdiff: ["\\frac{\\partial #1}{\\partial #2}", 2],

                infer: ["\\mathrel{\\mathop{\\frac{\\begin{aligned}#3\\end{aligned}}{#2}}\\limits^{#1}}", 3, ""],
                "infer*": ["\\mathrel{\\frac{\\begin{aligned}#2\\end{aligned}}{#1}}", 2],
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
        const visibleText = collectVisibleText(root);

        const leftovers = mergeAuditFindings(
            findVisibleLatexCommands(visibleText),
            findUndefinedMathJaxCommands(root),
            findLeakedMathPlaceholders(visibleText)
        );

        if (leftovers.length > 0) {
            console.warn(
                "Math rendering audit findings after MathJax typeset:",
                {
                    context,
                    leftovers
                }
            );

            root.dispatchEvent(
                new CustomEvent("mathjax-leftover-commands", {
                    detail: {
                        context,
                        leftovers
                    }
                })
            );
        }

        return leftovers;
    }

    function findUndefinedMathJaxCommands(root) {
        if (!root) {
            return [];
        }

        const commandPattern = /^\\[A-Za-z@]+(?:\*)?$/;
        const seen = new Map();

        root
            .querySelectorAll(
                'mjx-assistive-mml mtext[mathcolor="red"]'
            )
            .forEach(node => {
                const command =
                    String(node.textContent || "").trim();

                if (
                    !commandPattern.test(command) ||
                    shouldIgnoreCommand(command.replace(/^\\/, ""))
                ) {
                    return;
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
                    entry.examples.push(
                        `MathJax undefined command: ${command}`
                    );
                }
            });

        return Array.from(seen.values());
    }


    function findLeakedMathPlaceholders(text) {
        const normalized = String(text || "");
        const placeholderPattern =
            /PMMATHPROSEBLOCK\d+END/g;

        const matches = [];
        let match;

        while (
            (match = placeholderPattern.exec(normalized)) !== null
        ) {
            matches.push({
                value: match[0],
                index: match.index
            });
        }

        if (matches.length === 0) {
            return [];
        }

        return [{
            command: "[PMMATHPROSEBLOCK_LEAK]",
            count: matches.length,
            examples: matches
                .slice(0, 3)
                .map(item =>
                    makeTextSnippet(normalized, item.index)
                )
        }];
    }


    function mergeAuditFindings(...findingGroups) {
        const merged = new Map();

        findingGroups
            .flat()
            .filter(Boolean)
            .forEach(item => {
                const command =
                    String(item.command || "").trim();

                if (!command) {
                    return;
                }

                if (!merged.has(command)) {
                    merged.set(command, {
                        command,
                        count: 0,
                        examples: []
                    });
                }

                const target = merged.get(command);

                target.count += Number(item.count || 0);

                (item.examples || []).forEach(example => {
                    if (
                        example &&
                        target.examples.length < 3 &&
                        !target.examples.includes(example)
                    ) {
                        target.examples.push(example);
                    }
                });
            });

        return Array.from(merged.values());
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