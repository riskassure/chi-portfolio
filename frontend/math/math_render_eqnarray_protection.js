(() => {

function protectEqnarrayEnvironments(value) {
    const protectedBlocks = [];
    let output = String(value || "");

    output = output.replace(
        /\\begin\{eqnarray\*?\}[\s\S]*?\\end\{eqnarray\*?\}/gi,
        function (block) {
            const token =
                `@@PM_EQNARRAY_BLOCK_${protectedBlocks.length}@@`;

            protectedBlocks.push(block);

            return token;
        }
    );

    return {
        text: output,
        blocks: protectedBlocks
    };
}


function restoreEqnarrayEnvironments(value, protectedBlocks) {
    let output = String(value || "");

    (protectedBlocks || []).forEach(function (block, index) {
        const token = `@@PM_EQNARRAY_BLOCK_${index}@@`;
        output = output.replace(token, block);
    });

    return output;
}


window.MathCmsRenderEqnarrayProtection = {
    protectEqnarrayEnvironments,
    restoreEqnarrayEnvironments
};

})();
