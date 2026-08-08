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


window.MathCmsRenderLegacyTex = {
    normalizeLegacyOverFractions
};

})();
