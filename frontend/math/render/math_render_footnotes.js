(() => {

function normalizeFootnoteMacros(value) {
    const source = String(value || "");

    if (!/\\footnote\s*\{/.test(source)) {
        return source;
    }

    const footnotePattern = /\\footnote\s*\{/g;

    let output = "";
    let cursor = 0;
    let match;

    while (
        (match = footnotePattern.exec(source)) !== null
    ) {
        const commandStart = match.index;
        const contentStart = footnotePattern.lastIndex;

        let depth = 1;
        let index = contentStart;

        while (index < source.length && depth > 0) {
            const character = source[index];
            const nextCharacter = source[index + 1];

            // Do not treat escaped braces as grouping braces.
            if (
                character === "\\"
                && (
                    nextCharacter === "{"
                    || nextCharacter === "}"
                )
            ) {
                index += 2;
                continue;
            }

            if (character === "{") {
                depth += 1;
            } else if (character === "}") {
                depth -= 1;
            }

            index += 1;
        }

        // Leave malformed source untouched.
        if (depth !== 0) {
            break;
        }

        const contentEnd = index - 1;

        let replacementStart = commandStart;
        let replacementEnd = index;

        /*
        * Also consume an optional wrapper:
        *
        *   {\footnote{...}}
        */
        let leftIndex = commandStart - 1;

        while (
            leftIndex >= cursor
            && /\s/.test(source[leftIndex])
        ) {
            leftIndex -= 1;
        }

        let rightIndex = index;

        while (
            rightIndex < source.length
            && /\s/.test(source[rightIndex])
        ) {
            rightIndex += 1;
        }

        if (
            source[leftIndex] === "{"
            && source[rightIndex] === "}"
        ) {
            replacementStart = leftIndex;
            replacementEnd = rightIndex + 1;
        }

        const content = source
            .slice(contentStart, contentEnd)
            .trim();

        output += source.slice(
            cursor,
            replacementStart
        );

        if (content) {
            output += `
                <span class="pm-footnote tex2jax_process">
                    <span class="pm-footnote-label">Note.</span>
                    ${content}
                </span>
            `;
        }

        cursor = replacementEnd;
        footnotePattern.lastIndex = replacementEnd;
    }

    output += source.slice(cursor);

    return output;
}


window.MathCmsRenderFootnotes = {
    normalizeFootnoteMacros
};

})();
