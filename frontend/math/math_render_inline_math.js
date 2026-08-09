(() => {

function preventInlineMathPunctuationWrap(value) {
    let output = String(value || "");

    // MathJax inline form:
    //   \(x\). -> <span ...>\(x\).</span>
    output = output.replace(
        /(\\\((?:[^\\]|\\(?!\)))*?\\\))([.,;:!?])/g,
        function (_, math, punctuation) {
            return `
                <span
                    class="pm-inline-math-punctuation"
                    style="white-space:nowrap;"
                >${math}${punctuation}</span>
            `;
        }
    );

    /*
    * Process every legitimate single-dollar expression from left to right,
    * even when it has no trailing punctuation.
    *
    * Making punctuation optional prevents the closing dollar of one
    * expression from being mistaken for the opening dollar of the next:
    *
    *   $u\leftarrow v$ ($:=v\to u$),
    */
    output = output.replace(
        /(?<!\\)(?<!\$)(\$(?!\$)(?:\\[^\r\n]|[^\\$\r\n])*?(?<!\\)\$(?!\$))([.,;:!?])?/g,
        function (_, math, punctuation) {
            if (!punctuation) {
                return math;
            }

            return `
                <span
                    class="pm-inline-math-punctuation"
                    style="white-space:nowrap;"
                >${math}${punctuation}</span>
            `;
        }
    );

    return output;
}


window.MathCmsRenderInlineMath = {
    preventInlineMathPunctuationWrap
};

})();
