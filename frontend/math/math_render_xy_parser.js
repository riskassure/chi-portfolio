// frontend/math/math_render_xy_parser.js

(function () {
    function findXyMatrixBodyStart(text, startIndex) {
        let i = findNextNonSpaceIndex(text, startIndex);

        if (i === -1) {
            return -1;
        }

        // Ordinary case:
        // \xymatrix{...}
        if (text[i] === "{") {
            return i;
        }

        // Extended PlanetMath / Xy-pic option cases:
        // \xymatrix@C=1.5cm{...}
        // \xymatrix@R-=2pt{...}
        // \xymatrix@+=1.5cm{...}
        // \xymatrix@1{...}
        // \xymatrix @R=1pt @C=1.5cm {...}
        // \xymatrix @!=1pt {...}
        if (text[i] !== "@") {
            return -1;
        }

        const limit = Math.min(text.length, i + 180);

        while (i < limit) {
            while (i < limit && /\s/.test(text[i])) {
                i += 1;
            }

            if (i >= limit) {
                return -1;
            }

            if (text[i] === "{" && text[i - 1] !== "\\") {
                return i;
            }

            if (text[i] !== "@") {
                return -1;
            }

            // Consume one @ option token.
            // Examples:
            //   @C=1.5cm
            //   @R-=2pt
            //   @+=3pc
            //   @1
            //   @!
            //   @!=1pt
            //   @-2ex
            i += 1;

            while (i < limit) {
                if (text[i] === "{" && text[i - 1] !== "\\") {
                    return i;
                }

                if (/\s/.test(text[i]) || text[i] === "@") {
                    break;
                }

                i += 1;
            }
        }

        return -1;
    }

    function findNextNonSpaceIndex(text, startIndex) {
        for (let i = startIndex; i < text.length; i += 1) {
            if (!/\s/.test(text[i])) {
                return i;
            }
        }

        return -1;
    }

    function recoverLostXyMatrixRowSeparators(value) {
        let source = String(value || "");

        /*
        * Some legacy xymatrix row separators arrive as one backslash
        * immediately before a physical newline:
        *
        *     ... \ar[d] \
        *     NextRow
        *
        * Recover that lone slash as the intended TeX row separator.
        */
        source = source.replace(
            /\\[ \t]*\r?\n(?=[ \t]*\S)/g,
            "\\\\\n"
        );

        /*
        * Other legacy rows lose both the second slash and the physical
        * newline, commonly before a new \mathcal object:
        *
        *     ... \ \mathcal{C}
        */
        source = source.replace(
            /\\\s+(?=\\mathcal\s*\{)/g,
            "\\\\ "
        );

        return source;
    }

    function normalizeLegacyTwoCellArrowLabel(value) {
        let label = String(value || "").trim();

        // \stackrel{R}{}  -> R
        // \stackrel{}{T}  -> T
        const stackrelMatch = label.match(
            /^\\stackrel\s*\{([^{}]*)\}\s*\{([^{}]*)\}$/
        );

        if (stackrelMatch) {
            label = (
                String(stackrelMatch[1] || "").trim()
                || String(stackrelMatch[2] || "").trim()
            );
        }

        return label;
    }


    function normalizeLegacyTwoCellInnerLabel(value) {
        let label = String(value || "").trim();

        if (/^\\omit\b/i.test(label)) {
            return "";
        }

        // Remove Xy-pic positioning prefix:
        //   <0>_{\quad \tau}
        //   <-2.5>_{\mbox{ } \tau}
        //   <2.5>^{\mbox{ } \eta}
        label = label.replace(/^<[^>]*>\s*/, "");

        const positionedMatch = label.match(
            /^[_^]\s*\{([\s\S]*)\}$/
        );

        if (positionedMatch) {
            label = positionedMatch[1].trim();
        }

        label = label
            .replace(/\\(?:quad|qquad)\b/g, " ")
            .replace(/\\mbox\s*\{([^{}]*)\}/g, "$1")
            .replace(/\s+/g, " ")
            .trim();

        return label;
    }


    function parseLegacyTwoCellCommandAt(text, commandIndex, commandName) {
        const source = String(text || "");
        const command = `\\${commandName}`;

        if (!source.startsWith(command, commandIndex)) {
            return null;
        }

        let cursor = commandIndex + command.length;

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        // Optional Xy-pic offset such as <4.5>, <-5>, or <9>.
        if (source[cursor] === "<") {
            const offsetEnd = source.indexOf(">", cursor + 1);

            if (offsetEnd === -1) {
                return null;
            }

            cursor = offsetEnd + 1;
        }

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        // Upper commands use ^{...}; lower commands use _{...}.
        if (source[cursor] !== "^" && source[cursor] !== "_") {
            return null;
        }

        cursor += 1;

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        if (source[cursor] !== "{") {
            return null;
        }

        const arrowLabelEnd = window.MathCmsRenderStructuredMath
            .findMatchingBrace(source, cursor);

        if (arrowLabelEnd === -1) {
            return null;
        }

        const rawArrowLabel = source.slice(cursor + 1, arrowLabelEnd);
        cursor = arrowLabelEnd + 1;

        while (cursor < source.length && /\s/.test(source[cursor])) {
            cursor += 1;
        }

        if (source[cursor] !== "{") {
            return null;
        }

        const innerLabelEnd = window.MathCmsRenderStructuredMath
            .findMatchingBrace(source, cursor);

        if (innerLabelEnd === -1) {
            return null;
        }

        const rawInnerLabel = source.slice(cursor + 1, innerLabelEnd);

        return {
            commandName,
            start: commandIndex,
            end: innerLabelEnd + 1,
            arrowLabel: normalizeLegacyTwoCellArrowLabel(rawArrowLabel),
            innerLabel: normalizeLegacyTwoCellInnerLabel(rawInnerLabel)
        };
    }


    function extractLegacyTwoCellCommands(value) {
        const source = String(value || "");
        const commands = [];

        let cursor = 0;

        while (cursor < source.length) {
            const upperIndex = source.indexOf("\\ruppertwocell", cursor);
            const lowerIndex = source.indexOf("\\rlowertwocell", cursor);

            const candidateIndexes = [upperIndex, lowerIndex]
                .filter(index => index !== -1);

            if (candidateIndexes.length === 0) {
                break;
            }

            const commandIndex = Math.min(...candidateIndexes);
            const commandName =
                commandIndex === upperIndex
                    ? "ruppertwocell"
                    : "rlowertwocell";

            const parsed = parseLegacyTwoCellCommandAt(
                source,
                commandIndex,
                commandName
            );

            if (!parsed) {
                cursor = commandIndex + 1;
                continue;
            }

            commands.push(parsed);
            cursor = parsed.end;
        }

        let cleanText = source;

        [...commands]
            .sort((left, right) => right.start - left.start)
            .forEach(command => {
                cleanText =
                    cleanText.slice(0, command.start)
                    + cleanText.slice(command.end);
            });

        const upper = commands.find(
            command => command.commandName === "ruppertwocell"
        );

        const lower = commands.find(
            command => command.commandName === "rlowertwocell"
        );

        return {
            text: cleanText,
            legacyTwoCell: upper || lower
                ? {
                    upperArrowLabel: upper?.arrowLabel || "",
                    upperInnerLabel: upper?.innerLabel || "",
                    lowerArrowLabel: lower?.arrowLabel || "",
                    lowerInnerLabel: lower?.innerLabel || ""
                }
                : null
        };
    }

    function parseXyMatrixCell(rawCell) {
        const legacyTwoCellResult = extractLegacyTwoCellCommands(rawCell);

        let text = legacyTwoCellResult.text.trim();
        const legacyTwoCell = legacyTwoCellResult.legacyTwoCell;

        const arrows = [];
        let twoCellLabel = "";
        let objectFrame = null;
        let overlayLabel = "";

        /*
        * Legacy Xy-pic crossing-gap marker:
        *
        *   \ar@{-}[rd]|!{"2,1";"1,2"}\hole
        *
        * The HTML/SVG converter already renders the underlying arrow. Remove
        * the placement suffix so it cannot leak into the visible object text
        * or reach MathJax as an undefined command.
        */
        text = text.replace(
            /\|\s*!\s*\{[^{}]*\}\s*\\hole\b/g,
            ""
        );

        /*
        * Legacy Xy-pic saved text object:
        *
        *   \save *\txt{the decimal point} \restore \ar[u]
        *
        * Preserve the visible text and following arrow, but discard the
        * Xy-pic save/restore positioning wrappers.
        */
        text = text.replace(
            /\\save\s*\*\s*\\txt\s*\{([^{}]*)\}\s*\\restore\b/g,
            (_, label) => {
                overlayLabel = String(label || "").trim();
                return "";
            }
        );

        /*
        * Xy-pic framed automaton states:
        *
        *   *+[o][F-]{0}   single-circle state
        *   *++[o][F=]{2}  double-circle accepting state
        */
        text = text.replace(
            /^\s*\*\+*\[o\]\[F([-=])\]\s*\{([^{}]*)\}/,
            function (_, frameStyle, objectLabel) {
                objectFrame = {
                    shape: "circle",
                    doubleBorder: frameStyle === "="
                };

                return String(objectLabel || "").trim();
            }
        );

        // Invisible Xy-pic arrow used to place a relation between two
        // previously named arrows:
        //
        //   \ar@{}"1";"2"|-{=}
        //
        // Preserve the visible relation label, but remove the Xy-pic
        // reference syntax so it cannot leak into the object text.
        text = text.replace(
            /\\ar@\{\}\s*"[^"]+"\s*;\s*"[^"]+"\s*\|\s*-\s*\{([^{}]*)\}/g,
            function (_, relationLabel) {
                twoCellLabel = String(relationLabel || "").trim();
                return "";
            }
        );

        // Xy-pic 2-cell between two previously named arrows:
        //
        //   \ar@{=>}"1";"2"_{\tau}
        //
        // Capture its label separately so the reference syntax does not leak
        // into the rendered object text.
        text = text.replace(
            /\\ar@\{=>\}\s*"[^"]+"\s*;\s*"[^"]+"\s*(?:[_^]\s*(?:\{([^{}]*)\}|(\\?[A-Za-z0-9]+)))?/g,
            function (_, bracedLabel, unbracedLabel) {
                twoCellLabel = String(
                    bracedLabel || unbracedLabel || ""
                ).trim();

                return "";
            }
        );

        // Supports common Xy-pic variants:
        //   \ar[r]
        //   \ar[d]^f
        //   \ar[r]^{F(x)}
        //   \ar@<0.5ex>[r]^f
        //   \ar@<-0.5ex>[r]_g
        //   \ar@{->}[rd]
        //   \ar@{}[dr]|{=}
        //   \ar@/^1ex/[ddr]
        //
        // Also consume optional named-arrow suffixes:
        //   ="1"
        //   ="2"
        const arrowPattern =
            /\\ar(?:@(?:[+-]?(?:\d+(?:\.\d+)?|\.\d+))?\{[^{}]*\}|@<[^>]*>|@[^\s\[\]&{}]+)*(?:\s*\[([^\]]*)\])?((?:\s*(?:[_^](?:[-+])?\s*[<>]*\s*(?:\{(?:[^{}]|\{[^{}]*\})*\}|\\?[A-Za-z0-9]+)|\|(?:\{(?:[^{}]|\{[^{}]*\})*\}|\\?[A-Za-z0-9=+\-]+)))*)\s*(?:=\s*"[^"]+")?/g;

        let match;

        while ((match = arrowPattern.exec(text)) !== null) {
            const directionText = match[1] || "r";

            const styleMatch =
                match[0].match(
                    /@([+-]?(?:\d+(?:\.\d+)?|\.\d+))?\{([^{}]*)\}/
                );

            const styleVariant =
                styleMatch
                    ? String(styleMatch[1] || "").trim()
                    : "";

            const styleLineCount =
                styleVariant === "3"
                    ? 3
                    : styleVariant === "2"
                        ? 2
                        : 1;

            const curveMatch =
                match[0].match(
                    /@\/\s*([_^])\s*([^/]*)\//i
                );

            const labelInfo =
                extractXyArrowLabel(match[2] || "");

                        const selfLoopMatch = match[0].match(
                /@\(\s*([rl])\s*,\s*([ud])\s*\)/i
            );

            arrows.push({
                direction: normalizeXyArrowDirection(directionText),
                directionText,
                span: getXyArrowSpan(directionText),
                style: styleMatch ? styleMatch[2] : "->",
                lineCount: styleLineCount,
                label: labelInfo.text,
                labelPosition: labelInfo.position,

                curveSide:
                    curveMatch
                        ? curveMatch[1]
                        : "",

                curveAmount:
                    curveMatch
                        ? String(curveMatch[2] || "").trim()
                        : "",

                isSelfLoop: Boolean(selfLoopMatch),

                loopSide:
                    selfLoopMatch
                    && selfLoopMatch[1].toLowerCase() === "l"
                        ? "left"
                        : "right",

                loopPlacement:
                    selfLoopMatch
                    && selfLoopMatch[2].toLowerCase() === "d"
                        ? "below"
                        : "above"
            });
        }

        const objectTex = text
            .replace(arrowPattern, "")
            .replace(/\s+/g, " ")

            /*
            * A recovered or partially preserved xymatrix row separator can
            * leave one or more backslashes in an otherwise empty object cell.
            *
            * Without this cleanup, renderXyObjectCell() wraps that residue in
            * generated \( ... \) delimiters, which can display literally.
            */
            .replace(/\\+\s*$/, "")

            .trim();

        return {
            objectTex,
            objectFrame,
            overlayLabel,
            arrows,
            twoCellLabel,
            legacyTwoCell
        };
    }

    function normalizeXyArrowDirection(direction) {
        const clean = String(direction || "r")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        // Preserve diagonal directions before testing single directions.
        if (clean.includes("d") && clean.includes("l")) return "dl";
        if (clean.includes("d") && clean.includes("r")) return "dr";
        if (clean.includes("u") && clean.includes("l")) return "ul";
        if (clean.includes("u") && clean.includes("r")) return "ur";

        if (clean.includes("d")) return "d";
        if (clean.includes("u")) return "u";
        if (clean.includes("l")) return "l";

        return "r";
    }

    function getXyArrowSpan(directionText) {
        const clean = String(directionText || "r")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        return Math.max(clean.length, 1);
    }

    function getXyArrowHorizontalSpan(directionText) {
        const clean = String(directionText || "")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        const horizontalSteps =
            (clean.match(/[lr]/g) || []).length;

        return Math.max(horizontalSteps, 1);
    }

    function isXyDiagonalDirection(direction) {
        return (
            direction === "dl"
            || direction === "dr"
            || direction === "ul"
            || direction === "ur"
        );
    }

    function getXyArrowCoordinateDelta(directionText) {
        const clean = String(directionText || "")
            .toLowerCase()
            .replace(/[^rlud]/g, "");

        return {
            rowDelta:
                (clean.match(/d/g) || []).length
                - (clean.match(/u/g) || []).length,

            colDelta:
                (clean.match(/r/g) || []).length
                - (clean.match(/l/g) || []).length
        };
    }

    function extractXyArrowLabel(modifierText) {
        const text = String(modifierText || "");

        const bracedMatch = text.match(
            /([_^|])(?:[-+])?\s*[<>]*\s*\{((?:[^{}]|\{[^{}]*\})*)\}/
        );

        if (bracedMatch) {
            return {
                text: bracedMatch[2].trim(),
                position:
                    bracedMatch[1] === "_"
                        ? "below"
                        : bracedMatch[1] === "^"
                            ? "above"
                            : "center"
            };
        }

        const unbracedMatch = text.match(
            /([_^|])(?:[-+])?\s*[<>]*\s*(\\?[A-Za-z0-9=+\-]+)/
        );

        if (unbracedMatch) {
            return {
                text: unbracedMatch[2].trim(),
                position:
                    unbracedMatch[1] === "_"
                        ? "below"
                        : unbracedMatch[1] === "^"
                            ? "above"
                            : "center"
            };
        }

        return {
            text: "",
            position: "above"
        };
    }

    window.MathCmsRenderXyParser = {
        findXyMatrixBodyStart,
        findNextNonSpaceIndex,
        recoverLostXyMatrixRowSeparators,
        parseXyMatrixCell,
        getXyArrowHorizontalSpan,
        isXyDiagonalDirection,
        getXyArrowCoordinateDelta
    };
})();
