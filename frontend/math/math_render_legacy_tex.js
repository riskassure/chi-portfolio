(() => {

function normalizeLegacyOverFractions(value) {
    let output = String(value || "");

    // Common PlanetMath form:
    //   {n \over 2^k}
    //   {a+b \over c}
    //
    // Intentionally limited to simple, non-nested brace groups.
    output = output.replace(
        /\{\s*([^{}]+?)\s+\\over\s+([^{}]+?)\s*\}/g,
        (_, numerator, denominator) =>
            `\\frac{${numerator.trim()}}{${denominator.trim()}}`
    );

    return output;
}

function normalizeCommonTextAccentMacros(tex) {
    let output = String(tex || "");

    // Special case caused by \text{\L}ukasiewicz becoming \Lukasiewicz
    // after text-wrapper cleanup.
    output = output.replace(/\\Lukasiewicz/g, "Łukasiewicz");

    // Polish / Scandinavian / German / French common prose letters.
    output = output.replace(/\\L\b/g, "Ł");
    output = output.replace(/\\l\b/g, "ł");
    output = output.replace(/\\aa\s*\{\}/gi, "å");
    output = output.replace(/\\AA\s*\{\}/g, "Å");
    output = output.replace(/\\o\b/g, "ø");
    output = output.replace(/\\O\b/g, "Ø");
    output = output.replace(/\\ae\b/g, "æ");
    output = output.replace(/\\AE\b/g, "Æ");
    output = output.replace(/\\oe\b/g, "œ");
    output = output.replace(/\\OE\b/g, "Œ");
    output = output.replace(/\\ss\b/g, "ß");

    // Text prime used in transliterated names.
    output = output.replace(/\\cprime\b/g, "′");

    // A few accent forms that appear in bibliography prose.
    output = output.replace(/\\"a/g, "ä");
    output = output.replace(/\\"o/g, "ö");
    output = output.replace(/\\"u/g, "ü");
    output = output.replace(/\\"A/g, "Ä");
    output = output.replace(/\\"O/g, "Ö");
    output = output.replace(/\\"U/g, "Ü");

    output = output.replace(/\\'e/g, "é");
    output = output.replace(/\\'a/g, "á");
    output = output.replace(/\\'i/g, "í");
    output = output.replace(/\\'o/g, "ó");
    output = output.replace(/\\'u/g, "ú");

    output = output.replace(/\\`e/g, "è");
    output = output.replace(/\\`a/g, "à");
    output = output.replace(/\\`i/g, "ì");
    output = output.replace(/\\`o/g, "ò");
    output = output.replace(/\\`u/g, "ù");

    output = output.replace(/\\H\{o\}/g, "ő");
    output = output.replace(/\\H\{O\}/g, "Ő");

    output = output.replace(/\\v\{c\}/g, "č");
    output = output.replace(/\\v\{C\}/g, "Č");
    output = output.replace(/\\v\{s\}/g, "š");
    output = output.replace(/\\v\{S\}/g, "Š");
    output = output.replace(/\\v\{z\}/g, "ž");
    output = output.replace(/\\v\{Z\}/g, "Ž");

    // Braced umlaut forms used in bibliography prose.
    output = output.replace(/\\"\{a\}/g, "ä");
    output = output.replace(/\\"\{o\}/g, "ö");
    output = output.replace(/\\"\{u\}/g, "ü");
    output = output.replace(/\\"\{A\}/g, "Ä");
    output = output.replace(/\\"\{O\}/g, "Ö");
    output = output.replace(/\\"\{U\}/g, "Ü");

    // Unbraced forms.
    output = output.replace(/\\"a/g, "ä");
    output = output.replace(/\\"o/g, "ö");
    output = output.replace(/\\"u/g, "ü");
    output = output.replace(/\\"A/g, "Ä");
    output = output.replace(/\\"O/g, "Ö");
    output = output.replace(/\\"U/g, "Ü");

    // TeX circumflex accents used in prose and bibliography text:
    //   C\^{o}nes -> Cônes
    const circumflexCharacters = {
        A: "Â",
        C: "Ĉ",
        E: "Ê",
        I: "Î",
        O: "Ô",
        U: "Û",
        a: "â",
        c: "ĉ",
        e: "ê",
        i: "î",
        o: "ô",
        u: "û"
    };

    output = output.replace(
        /\\\^\s*\{([ACEIOUaceiou])\}/g,
        function (_, letter) {
            return circumflexCharacters[letter] || letter;
        }
    );

    // Also support the unbraced TeX form: \^o
    output = output.replace(
        /\\\^\s*([ACEIOUaceiou])/g,
        function (_, letter) {
            return circumflexCharacters[letter] || letter;
        }
    );

    return output;
}

window.MathCmsRenderLegacyTex = {
    normalizeLegacyOverFractions,
    normalizeCommonTextAccentMacros
};

})();
