// frontend/math/math_local_macros.js

(function (root) {
    "use strict";

    const MAX_ARGUMENTS = 9;
    const MAX_EXPANSION_PASSES = 12;
    const MAX_TOTAL_EXPANSIONS = 10000;

    root.MathCmsLocalMacros = {
        debugVersion: "local-newcommand-v3",
        apply,
        inspect: parseLocalMacroPrelude
    };


    /**
     * Expand concept-local macros without registering them with MathJax.
     *
     * content:
     *     The display_tex/rendered_tex/cleaned_tex selected for display.
     *
     * macroSource:
     *     The concept's cleaned_tex, where the local definitions live.
     */
    function apply(
        content,
        macroSource = "",
        context = {}
    ) {
        const parsed =
            parseLocalMacroPrelude(macroSource);

        reportWarnings(
            parsed.warnings,
            context
        );

        if (parsed.macros.length === 0) {
            return String(content || "");
        }

        const contentText =
            String(content || "");

        /*
         * When cleaned_tex itself is the display payload, remove its
         * definition prelude before rendering the article body.
         *
         * When rendered_tex is the display payload, the definitions
         * may already be absent.
         */
        const contentPrelude =
            parseLocalMacroPrelude(contentText);

        const body =
            contentPrelude.macros.length > 0
                ? contentPrelude.body
                : contentText;

        const protectedResult =
            protectLiteralRegions(body);

        const expanded =
            expandText(
                protectedResult.text,
                parsed.macros,
                context
            );

        const restored =
            restoreProtectedRegions(
                expanded,
                protectedResult.blocks
            );

        console.debug(
            "Applied concept-local macros.",
            {
                context,

                macros: parsed.macros.map(
                    macro => ({
                        command: macro.token,
                        argumentCount:
                            macro.argumentCount,
                        replacement:
                            macro.replacement
                    })
                )
            }
        );

        return restored;
    }


    /**
     * Read consecutive \newcommand definitions from the beginning
     * of cleaned_tex.
     *
     * Version 1 supports:
     *
     *   \newcommand{\foo}{replacement}
     *   \newcommand{\foo}[1]{replacement using #1}
     *   \newcommand{\foo}[2]{replacement using #1 and #2}
     *
     * The unbraced command-name form is also accepted:
     *
     *   \newcommand\foo[1]{replacement using #1}
     */
    function parseLocalMacroPrelude(source) {
        const text =
            String(source || "")
                .replace(/^\uFEFF/, "");

        const macros = [];
        const warnings = [];

        let cursor = 0;
        let sawDefinition = false;

        while (cursor < text.length) {
            cursor =
                skipPreludeTrivia(
                    text,
                    cursor
                );

            if (
                !text.startsWith(
                    "\\newcommand",
                    cursor
                )
            ) {
                const unsupported =
                    readUnsupportedDefinitionName(
                        text,
                        cursor
                    );

                if (unsupported) {
                    warnings.push(
                        `Unsupported local macro definition `
                        + `\\${unsupported} at offset ${cursor}.`
                    );
                }

                break;
            }

            const parsed =
                parseNewCommand(
                    text,
                    cursor
                );

            if (!parsed) {
                warnings.push(
                    `Unable to parse local \\newcommand `
                    + `at offset ${cursor}.`
                );

                break;
            }

            sawDefinition = true;
            cursor = parsed.end;

            const priorIndex =
                macros.findIndex(
                    item =>
                        item.name
                        === parsed.macro.name
                );

            if (priorIndex !== -1) {
                warnings.push(
                    `Duplicate local macro `
                    + `${parsed.macro.token}; `
                    + `the later definition is used.`
                );

                macros.splice(
                    priorIndex,
                    1
                );
            }

            macros.push(
                parsed.macro
            );
        }

        return {
            macros,
            warnings,

            body: sawDefinition
                ? text
                    .slice(cursor)
                    .replace(/^\s+/, "")
                : text
        };
    }


    function parseNewCommand(
        text,
        start
    ) {
        let cursor =
            start
            + "\\newcommand".length;

        /*
         * Accept \newcommand* as equivalent for our supported
         * semantic subset.
         */
        if (text[cursor] === "*") {
            cursor += 1;
        }

        cursor =
            skipSpacesAndComments(
                text,
                cursor
            );

        const command =
            readNewCommandName(
                text,
                cursor
            );

        if (!command) {
            return null;
        }

        cursor = command.end;

        cursor =
            skipSpacesAndComments(
                text,
                cursor
            );

        let argumentCount = 0;

        if (text[cursor] === "[") {
            const countGroup =
                readBracketGroup(
                    text,
                    cursor
                );

            if (!countGroup) {
                return null;
            }

            const countText =
                countGroup.content.trim();

            if (!/^[0-9]$/.test(countText)) {
                return null;
            }

            argumentCount =
                Number(countText);

            if (
                argumentCount < 0
                || argumentCount
                    > MAX_ARGUMENTS
            ) {
                return null;
            }

            cursor =
                skipSpacesAndComments(
                    text,
                    countGroup.end
                );

            /*
             * This form has an optional first-argument default:
             *
             *   \newcommand{\foo}[2][default]{...}
             *
             * We deliberately reject it in version 1 rather than
             * interpreting it incorrectly.
             */
            if (text[cursor] === "[") {
                return null;
            }
        }

        if (text[cursor] !== "{") {
            return null;
        }

        const replacementGroup =
            readBalancedGroup(
                text,
                cursor
            );

        if (!replacementGroup) {
            return null;
        }

        return {
            macro: {
                name:
                    command.name,

                token:
                    `\\${command.name}`,

                argumentCount,

                replacement:
                    replacementGroup.content
            },

            end:
                replacementGroup.end
        };
    }


    function readNewCommandName(
        text,
        start
    ) {
        /*
         * Braced form:
         *
         *   {\conj}
         */
        if (text[start] === "{") {
            const group =
                readBalancedGroup(
                    text,
                    start
                );

            if (!group) {
                return null;
            }

            const commandText =
                group.content.trim();

            const match =
                commandText.match(
                    /^\\([A-Za-z@]+)$/
                );

            if (!match) {
                return null;
            }

            return {
                name: match[1],
                end: group.end
            };
        }

        /*
         * Unbraced form:
         *
         *   \conj
         */
        return readControlSequence(
            text,
            start
        );
    }


    function readControlSequence(
        text,
        start
    ) {
        if (text[start] !== "\\") {
            return null;
        }

        const match =
            text
                .slice(start + 1)
                .match(/^[A-Za-z@]+/);

        if (!match) {
            return null;
        }

        return {
            name: match[0],

            end:
                start
                + 1
                + match[0].length
        };
    }


    /**
     * Read a balanced {...} group, including nested braces.
     */
    function readBalancedGroup(
        text,
        start
    ) {
        if (text[start] !== "{") {
            return null;
        }

        let depth = 0;

        for (
            let cursor = start;
            cursor < text.length;
            cursor += 1
        ) {
            const char =
                text[cursor];

            /*
             * Skip an escaped character such as \{ or \}.
             */
            if (char === "\\") {
                cursor += 1;
                continue;
            }

            if (char === "{") {
                depth += 1;
                continue;
            }

            if (char === "}") {
                depth -= 1;

                if (depth === 0) {
                    return {
                        content:
                            text.slice(
                                start + 1,
                                cursor
                            ),

                        end:
                            cursor + 1
                    };
                }
            }
        }

        return null;
    }


    function readBracketGroup(
        text,
        start
    ) {
        if (text[start] !== "[") {
            return null;
        }

        let depth = 0;

        for (
            let cursor = start;
            cursor < text.length;
            cursor += 1
        ) {
            const char =
                text[cursor];

            if (char === "\\") {
                cursor += 1;
                continue;
            }

            if (char === "[") {
                depth += 1;
                continue;
            }

            if (char === "]") {
                depth -= 1;

                if (depth === 0) {
                    return {
                        content:
                            text.slice(
                                start + 1,
                                cursor
                            ),

                        end:
                            cursor + 1
                    };
                }
            }
        }

        return null;
    }


    /**
     * Allow blank lines and full-line comments before and between
     * definitions in the prelude.
     */
    function skipPreludeTrivia(
        text,
        start
    ) {
        let cursor = start;

        while (cursor < text.length) {
            const before = cursor;

            cursor =
                skipWhitespace(
                    text,
                    cursor
                );

            if (text[cursor] === "%") {
                cursor =
                    skipComment(
                        text,
                        cursor
                    );
            }

            if (cursor === before) {
                break;
            }
        }

        return cursor;
    }


    function skipSpacesAndComments(
        text,
        start
    ) {
        let cursor = start;

        while (cursor < text.length) {
            const before = cursor;

            cursor =
                skipWhitespace(
                    text,
                    cursor
                );

            if (text[cursor] === "%") {
                cursor =
                    skipComment(
                        text,
                        cursor
                    );
            }

            if (cursor === before) {
                break;
            }
        }

        return cursor;
    }


    function skipWhitespace(
        text,
        start
    ) {
        let cursor = start;

        while (
            cursor < text.length
            && /\s/.test(text[cursor])
        ) {
            cursor += 1;
        }

        return cursor;
    }


    function skipComment(
        text,
        start
    ) {
        let cursor = start;

        while (
            cursor < text.length
            && text[cursor] !== "\n"
        ) {
            cursor += 1;
        }

        return cursor;
    }


    /**
     * Recognize likely definition forms that are not yet supported.
     * They remain visible to diagnostics instead of being silently
     * interpreted as \newcommand.
     */
    function readUnsupportedDefinitionName(
        text,
        start
    ) {
        const match =
            text
                .slice(start)
                .match(
                    /^\\(renewcommand|providecommand|DeclareMathOperator|def)\b/
                );

        return match
            ? match[1]
            : "";
    }


    /**
     * Protect literal examples so documentation concepts can show:
     *
     *   \newcommand{\foo}{...}
     *   \foo{x}
     *
     * without the example source itself being expanded.
     */
    function protectLiteralRegions(text) {
        const blocks = [];
        let output =
            String(text || "");

        const protect = value => {
            const index =
                blocks.length;

            blocks.push(value);

            return (
                `PMLOCALMACROPROTECTED`
                + `${index}END`
            );
        };

        output = output.replace(
            /<!--([\s\S]*?)-->/g,
            protect
        );

        output = output.replace(
            /<(pre|code|textarea|script|style)\b[^>]*>[\s\S]*?<\/\1>/gi,
            protect
        );

        output = output.replace(
            /\\begin\{verbatim\*?\}[\s\S]*?\\end\{verbatim\*?\}/gi,
            protect
        );

        output = output.replace(
            /\\verb\*?([^A-Za-z0-9\s])[\s\S]*?\1/g,
            protect
        );

        /*
         * Do not expand commands inside generated HTML tags or
         * attributes.
         */
        output = output.replace(
            /<[^>]+>/g,
            protect
        );

        /*
         * TeX comments outside protected HTML.
         */
        output = output.replace(
            /(^|[^\\])%[^\r\n]*/gm,
            (match, prefix) => {
                const comment =
                    match.slice(
                        prefix.length
                    );

                return (
                    prefix
                    + protect(comment)
                );
            }
        );

        return {
            text: output,
            blocks
        };
    }


    function restoreProtectedRegions(
        text,
        blocks
    ) {
        return String(text || "")
            .replace(
                /PMLOCALMACROPROTECTED(\d+)END/g,
                (match, indexText) => {
                    const index =
                        Number(indexText);

                    return (
                        blocks[index]
                        ?? match
                    );
                }
            );
    }


    /**
     * Multiple passes allow nested calls:
     *
     *   \conj{\conj{a}}
     *
     * First pass:
     *
     *   \overline{\conj{a}}
     *
     * Second pass:
     *
     *   \overline{\overline{a}}
     */
    function expandText(
        text,
        macros,
        context
    ) {
        let output =
            String(text || "");

        let totalExpansions = 0;

        for (
            let pass = 0;
            pass < MAX_EXPANSION_PASSES;
            pass += 1
        ) {
            const result =
                expandTextPass(
                    output,
                    macros,
                    MAX_TOTAL_EXPANSIONS
                        - totalExpansions
                );

            output =
                result.text;

            totalExpansions +=
                result.count;

            if (
                totalExpansions
                >= MAX_TOTAL_EXPANSIONS
            ) {
                console.warn(
                    "Concept-local macro expansion limit reached.",
                    {
                        context,
                        totalExpansions
                    }
                );

                return output;
            }

            if (result.count === 0) {
                return output;
            }
        }

        console.warn(
            "Concept-local macro expansion pass limit reached.",
            {
                context,
                passes:
                    MAX_EXPANSION_PASSES
            }
        );

        return output;
    }


    /**
     * Expand one left-to-right pass through the current text.
     *
     * Replacement text is revisited on the next pass. This preserves
     * an unbraced control sequence as one argument before that control
     * sequence itself is expanded:
     *
     *   \GL n\C
     */
    function expandTextPass(
        text,
        macros,
        remainingLimit
    ) {
        let output = "";
        let cursor = 0;
        let count = 0;

        while (
            cursor < text.length
            && count < remainingLimit
        ) {
            const found =
                findNextExpandableMacro(
                    text,
                    macros,
                    cursor
                );

            if (!found) {
                output +=
                    text.slice(cursor);

                cursor =
                    text.length;

                break;
            }

            output +=
                text.slice(
                    cursor,
                    found.start
                );

            output +=
                buildMacroReplacement(
                    found.macro,
                    found.values
                );

            cursor =
                found.end;

            count += 1;
        }

        if (cursor < text.length) {
            output +=
                text.slice(cursor);
        }

        return {
            text: output,
            count
        };
    }


    /**
     * Find the earliest complete, expandable local macro call.
     *
     * Malformed parameterized calls remain untouched, while later valid
     * calls can still be expanded.
     */
    function findNextExpandableMacro(
        text,
        macros,
        start
    ) {
        let earliest = null;

        for (const macro of macros) {
            let found =
                findMacroToken(
                    text,
                    macro.token,
                    start
                );

            while (found !== -1) {
                const argumentStart =
                    found
                    + macro.token.length;

                let values = [];
                let end =
                    argumentStart;

                if (macro.argumentCount > 0) {
                    const parsedArguments =
                        readMacroArguments(
                            text,
                            argumentStart,
                            macro.argumentCount
                        );

                    if (!parsedArguments) {
                        found =
                            findMacroToken(
                                text,
                                macro.token,
                                argumentStart
                            );

                        continue;
                    }

                    values =
                        parsedArguments.values;

                    end =
                        parsedArguments.end;
                }

                if (
                    earliest === null
                    || found < earliest.start
                ) {
                    earliest = {
                        macro,
                        start: found,
                        end,
                        values
                    };
                }

                break;
            }
        }

        return earliest;
    }


    function buildMacroReplacement(
        macro,
        values
    ) {
        let replacement =
            macro.replacement;

        values.forEach(
            (value, index) => {
                replacement =
                    replacement
                        .split(
                            `#${index + 1}`
                        )
                        .join(value);
            }
        );

        return replacement;
    }


    /**
     * Match a complete TeX control word.
     *
     * For example, \Q must not match the beginning of \Quo.
     */
    function findMacroToken(
        text,
        token,
        start
    ) {
        let cursor =
            text.indexOf(
                token,
                start
            );

        while (cursor !== -1) {
            const previous =
                text[cursor - 1]
                || "";

            const next =
                text[
                    cursor
                    + token.length
                ]
                || "";

            if (
                previous !== "\\"
                && !/[A-Za-z@]/.test(next)
            ) {
                return cursor;
            }

            cursor =
                text.indexOf(
                    token,
                    cursor
                        + token.length
                );
        }

        return -1;
    }


    /**
     * Read ordinary TeX undelimited macro arguments.
     *
     * Each argument may be:
     *
     *   {a grouped argument}
     *   \ControlSequence
     *   \%
     *   x
     *
     * Braces group multiple tokens but are not included in the
     * replacement value.
     */
    function readMacroArguments(
        text,
        start,
        argumentCount
    ) {
        const values = [];
        let cursor = start;

        for (
            let index = 0;
            index < argumentCount;
            index += 1
        ) {
            cursor =
                skipSpacesAndComments(
                    text,
                    cursor
                );

            if (cursor >= text.length) {
                return null;
            }

            /*
            * Braced argument:
            *
            *   {x+y}
            */
            if (text[cursor] === "{") {
                const group =
                    readBalancedGroup(
                        text,
                        cursor
                    );

                if (!group) {
                    return null;
                }

                values.push(
                    group.content
                );

                cursor =
                    group.end;

                continue;
            }

            /*
            * Control-word argument:
            *
            *   \C
            *   \mathbb
            */
            if (text[cursor] === "\\") {
                const command =
                    readControlSequence(
                        text,
                        cursor
                    );

                if (command) {
                    values.push(
                        text.slice(
                            cursor,
                            command.end
                        )
                    );

                    cursor =
                        command.end;

                    continue;
                }

                /*
                * Control-symbol argument:
                *
                *   \%
                *   \{
                *   \,
                */
                if (
                    cursor + 1
                    >= text.length
                ) {
                    return null;
                }

                values.push(
                    text.slice(
                        cursor,
                        cursor + 2
                    )
                );

                cursor += 2;

                continue;
            }

            /*
            * Ordinary single-character argument:
            *
            *   x
            *   n
            *   2
            */
            values.push(
                text[cursor]
            );

            cursor += 1;
        }

        return {
            values,
            end: cursor
        };
    }


    function reportWarnings(
        warnings,
        context
    ) {
        if (
            !warnings
            || warnings.length === 0
        ) {
            return;
        }

        console.warn(
            "Concept-local macro prelude warnings.",
            {
                context,
                warnings
            }
        );
    }
})(
    typeof window !== "undefined"
        ? window
        : globalThis
);