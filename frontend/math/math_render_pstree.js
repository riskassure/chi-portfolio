(() => {
    function convertSimpleDeductionPstreeToHtml(tex) {
        if (!tex) {
            return "";
        }

        const renderNode = value => {
            const cleanValue =
                String(value || "").trim();

            return `
                <span
                    class="pm-pstree-node"
                    style="
                        display:inline-flex;
                        align-items:center;
                        justify-content:center;
                        min-width:2.2rem;
                        min-height:1.75rem;
                        padding:0.08rem 0.42rem;
                        border:1px solid #666;
                        border-radius:0.2rem;
                        background:#fff;
                    "
                >
                    \\(${window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell(cleanValue)}\\)
                </span>
            `;
        };

        const renderTwoLeafTree = (
            rootLabel,
            middleLabel,
            leftLabel,
            rightLabel
        ) => {
            return `
                <div
                    class="pm-pstree-display tex2jax_process"
                    style="
                        display:flex;
                        justify-content:center;
                        margin:1rem 0;
                    "
                >
                    <div style="
                        display:flex;
                        flex-direction:column;
                        align-items:center;
                    ">
                        <div style="
                            display:flex;
                            justify-content:center;
                            align-items:center;
                            gap:2rem;
                        ">
                            ${renderNode(leftLabel)}
                            ${renderNode(rightLabel)}
                        </div>

                        <svg
                            aria-hidden="true"
                            width="150"
                            height="30"
                            viewBox="0 0 150 30"
                            style="
                                display:block;
                                overflow:visible;
                            "
                        >
                            <line
                                x1="36"
                                y1="0"
                                x2="75"
                                y2="30"
                                stroke="currentColor"
                                stroke-width="1.5"
                            ></line>

                            <line
                                x1="114"
                                y1="0"
                                x2="75"
                                y2="30"
                                stroke="currentColor"
                                stroke-width="1.5"
                            ></line>
                        </svg>

                        ${renderNode(middleLabel)}

                        <div
                            aria-hidden="true"
                            style="
                                height:1rem;
                                border-left:1.5px solid currentColor;
                            "
                        ></div>

                        ${renderNode(rootLabel)}
                    </div>
                </div>
            `;
        };

        const renderThreeLevelTree = (
            rootLabel,
            upperMiddleLabel,
            lowerMiddleLabel,
            leftLabel,
            rightLabel
        ) => {
            return `
                <div
                    class="pm-pstree-display tex2jax_process"
                    style="
                        display:flex;
                        justify-content:center;
                        margin:1rem 0;
                    "
                >
                    <div style="
                        display:flex;
                        flex-direction:column;
                        align-items:center;
                    ">
                        <div style="
                            display:flex;
                            justify-content:center;
                            align-items:center;
                            gap:2rem;
                        ">
                            ${renderNode(leftLabel)}
                            ${renderNode(rightLabel)}
                        </div>

                        <svg
                            aria-hidden="true"
                            width="150"
                            height="30"
                            viewBox="0 0 150 30"
                            style="
                                display:block;
                                overflow:visible;
                            "
                        >
                            <line
                                x1="36"
                                y1="0"
                                x2="75"
                                y2="30"
                                stroke="currentColor"
                                stroke-width="1.5"
                            ></line>

                            <line
                                x1="114"
                                y1="0"
                                x2="75"
                                y2="30"
                                stroke="currentColor"
                                stroke-width="1.5"
                            ></line>
                        </svg>

                        ${renderNode(lowerMiddleLabel)}

                        <div
                            aria-hidden="true"
                            style="
                                height:1rem;
                                border-left:1.5px solid currentColor;
                            "
                        ></div>

                        ${renderNode(upperMiddleLabel)}

                        <div
                            aria-hidden="true"
                            style="
                                height:1rem;
                                border-left:1.5px solid currentColor;
                            "
                        ></div>

                        ${renderNode(rootLabel)}
                    </div>
                </div>
            `;
        };

        let output = String(tex);

        /*
        * Narrow PSTree v1:
        *
        *   \pstree[...]
        *   {\Tr{Z}}{
        *       \pstree{\Tr{Y}}
        *       {\Tr{X_1}\Tr{X_2}}
        *   }
        *
        * Used by the "deduction" concept.
        */
        const simplePattern =
            /\\\[\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\Tr\s*\{([^{}]+)\}\s*\}\s*\{\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\Tr\s*\{([^{}]+)\}\s*\}\s*\{\s*\\Tr\s*\{([^{}]+)\}\s*\\Tr\s*\{([^{}]+)\}\s*\}\s*\}\s*\\\]/gi;

        output = output.replace(
            simplePattern,
            function (
                _match,
                rootLabel,
                middleLabel,
                leftLabel,
                rightLabel
            ) {
                return renderTwoLeafTree(
                    rootLabel,
                    middleLabel,
                    leftLabel,
                    rightLabel
                );
            }
        );

        /*
        * Narrow PSTree v2:
        *
        *   \pstree[...]{\Tc{...}~[...]{A\to A}}{
        *       \pstree{\TC~[...]{A}}{
        *           \pstree{\TC~[...]{A\land A}}{
        *               \TC~[...]{A}
        *               \TC~[...]{A}
        *           }
        *       }
        *   }
        *
        * Used by "derivations-in-natural-deduction".
        */
        const derivationPattern =
            /\\\[\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\Tc\s*\{[^{}]*\}\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\}\s*\{\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\TC\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\}\s*\{\s*\\pstree(?:\s*\[[^\]]*\])?\s*\{\s*\\TC\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\}\s*\{\s*\\TC\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\\TC\s*~\s*\[[^\]]*\]\s*\{([^{}]+)\}\s*\}\s*\}\s*\}\s*\\\]/gi;

        output = output.replace(
            derivationPattern,
            function (
                _match,
                rootLabel,
                upperMiddleLabel,
                lowerMiddleLabel,
                leftLabel,
                rightLabel
            ) {
                return renderThreeLevelTree(
                    rootLabel,
                    upperMiddleLabel,
                    lowerMiddleLabel,
                    leftLabel,
                    rightLabel
                );
            }
        );

        return output;
    }

    function convertRootedTreePstreeToHtml(tex) {
        if (!tex) {
            return "";
        }

        /*
        * Narrow converter for the PSTricks diagram used by "rooted-tree".
        *
        * Tree structure:
        *
        *                 a       b   c   d
        *                 |        \ | /
        *                 e   f   g   h
        *                  \ /     \ /
        *                   i       j
        *                    \     /
        *                       k
        */
        const rootedTreePattern =
            /\\\[\s*\\pstree[\s\S]*?\\Tc\s*\{3pt\}[\s\S]*?\{\s*\$k\$\s*\}[\s\S]*?\\TC[\s\S]*?\{\s*\$d\$\s*\}[\s\S]*?\\\]/gi;

        return String(tex).replace(
            rootedTreePattern,
            `
                <div
                    class="pm-rooted-tree-display mathjax-diagnostic-ignore"
                    style="
                        display:flex;
                        justify-content:center;
                        max-width:100%;
                        overflow-x:auto;
                        margin:1rem 0;
                    "
                >
                    <svg
                        role="img"
                        aria-label="Rooted tree with root k"
                        width="640"
                        height="335"
                        viewBox="0 0 640 335"
                        preserveAspectRatio="xMidYMid meet"
                        style="
                            display:block;
                            width:min(100%, 640px);
                            height:auto;
                            overflow:visible;
                        "
                    >
                        <g
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.5"
                            vector-effect="non-scaling-stroke"
                        >
                            <!-- root to first level -->
                            <line x1="320" y1="295" x2="220" y2="220"></line>
                            <line x1="320" y1="295" x2="420" y2="220"></line>

                            <!-- i branch -->
                            <line x1="220" y1="220" x2="150" y2="140"></line>
                            <line x1="220" y1="220" x2="270" y2="140"></line>
                            <line x1="150" y1="140" x2="100" y2="60"></line>

                            <!-- j branch -->
                            <line x1="420" y1="220" x2="370" y2="140"></line>
                            <line x1="420" y1="220" x2="500" y2="140"></line>

                            <!-- h children -->
                            <line x1="500" y1="140" x2="430" y2="60"></line>
                            <line x1="500" y1="140" x2="500" y2="60"></line>
                            <line x1="500" y1="140" x2="570" y2="60"></line>
                        </g>

                        <!-- filled ordinary vertices -->
                        <g fill="currentColor">
                            <circle cx="100" cy="60" r="4"></circle>
                            <circle cx="430" cy="60" r="4"></circle>
                            <circle cx="500" cy="60" r="4"></circle>
                            <circle cx="570" cy="60" r="4"></circle>

                            <circle cx="150" cy="140" r="4"></circle>
                            <circle cx="270" cy="140" r="4"></circle>
                            <circle cx="370" cy="140" r="4"></circle>
                            <circle cx="500" cy="140" r="4"></circle>

                            <circle cx="220" cy="220" r="4"></circle>
                            <circle cx="420" cy="220" r="4"></circle>
                        </g>

                        <!-- open root vertex -->
                        <circle
                            cx="320"
                            cy="295"
                            r="5"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="1.5"
                            vector-effect="non-scaling-stroke"
                        ></circle>

                        <!-- vertex labels -->
                        <g
                            fill="currentColor"
                            font-family="serif"
                            font-size="21"
                            font-style="italic"
                            dominant-baseline="middle"
                        >
                            <text x="112" y="60">a</text>

                            <text
                                x="418"
                                y="60"
                                text-anchor="end"
                            >b</text>

                            <text x="512" y="60">c</text>
                            <text x="582" y="60">d</text>

                            <text
                                x="138"
                                y="140"
                                text-anchor="end"
                            >e</text>

                            <text x="282" y="140">f</text>

                            <text
                                x="358"
                                y="140"
                                text-anchor="end"
                            >g</text>

                            <text x="512" y="140">h</text>

                            <text
                                x="208"
                                y="220"
                                text-anchor="end"
                            >i</text>

                            <text x="432" y="220">j</text>

                            <text
                                x="320"
                                y="318"
                                text-anchor="middle"
                            >k</text>
                        </g>
                    </svg>
                </div>
            `
        );
    }

    window.MathCmsRenderPstree = {
        convertSimpleDeductionPstreeToHtml,
        convertRootedTreePstreeToHtml
    };
})();
