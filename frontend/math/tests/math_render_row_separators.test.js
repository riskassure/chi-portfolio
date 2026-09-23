// Run after structured_math, math_text, html_utils, delimiters and piecewise.
// These exercise the same text-protection/piecewise/restoration path as the page.
(() => {
    const assert = (ok, message) => { if (!ok) throw new Error(message); };
    const split = window.MathCmsRenderStructuredMath.splitEqnarrayRows;
    const fixtures = [
        [String.raw`a&b\cr c&d`, 2],
        [String.raw`a&b\\c&d`, 2],
        [String.raw`a&\substack{b\cr c}\cr d&e`, 2],
        [String.raw`\begin{pmatrix}a&b\cr c&d\end{pmatrix}&x\cr y&z`, 2],
        [String.raw`a&\cramped{x}`, 1],
    ];
    fixtures.forEach(([input, count]) => assert(split(input).length === count, input));

    for (const oddBranch of ['3n+1', '(3n+1)/2']) {
        const input = String.raw`\[F(n)=\begin{cases}n/2&\text{if }n\text{ is even},\cr ${oddBranch}&\text{if }n\text{ is odd}.\end{cases}\]`;
        const protectedText = window.MathCmsRenderMathText.protectMboxInsideMath(input);
        const converted = window.MathCmsRenderPiecewise.convertPiecewiseArraysToHtml(protectedText.text);
        const html = window.MathCmsRenderMathText.restoreMboxInsideMath(converted, protectedText.values);
        assert((html.match(/<tr>/g) || []).length === 2, 'Each Collatz map needs two rows');
        assert(html.includes(String.raw`\(${oddBranch}\)`), 'Odd formula must occupy its own cell');
        assert(html.includes(String.raw`\(\text{if }n\text{ is even},\)`), 'Even condition must remain balanced TeX');
        assert(html.includes(String.raw`\(\text{if }n\text{ is odd}.\)`), 'Odd condition must remain balanced TeX');
        assert(!html.includes('PMMATHTEXTTOKEN') && !html.includes(String.raw`\cr`), 'No unprocessed row separators or text tokens');
    }
})();
