// frontend/math/render/math_render_comments.js

(function () {
    function removeLatexComments(clean) {
        // Remove TeX comment/separator paragraphs and standalone lines that
        // survived backend rendering.
        clean = clean.replace(
            /<p[^>]*>\s*(?:%+\s*)+<\/p>/gi,
            ""
        );

        /*
        * The backend can combine a commented legacy heading with live content
        * inside the same paragraph:
        *
        *   <p>%<strong>Differential identities..</strong>
        *   <h2>Differential identities</h2>
        *   Several properties ...
        *
        * Remove only the commented legacy heading. Preserve the paragraph and
        * everything following it so structural environments such as align*
        * retain their opening marker and first row.
        */
        clean = clean.replace(
            /(<p\b[^>]*>)\s*%+\s*<strong\b[^>]*>[\s\S]*?<\/strong>\s*/gi,
            "$1"
        );

        /*
        * The backend may wrap an entire commented TeX line in an HTML
        * paragraph before the frontend receives it:
        *
        *   <p>%At this point ...</p>
        *   <p>%&= \lim_{h\to 0} ...</p>
        *
        * Since the first non-whitespace source character is %, the entire
        * paragraph is a TeX comment and must be discarded.
        *
        * Escaped percentages such as \% do not match this rule.
        */
        clean = clean.replace(
            /<p\b[^>]*>\s*%[\s\S]*?<\/p>/gi,
            ""
        );

        // In TeX, a line whose first non-whitespace character is %
        // is entirely commented out and must not reach the rendered page.
        clean = clean.replace(/^[ \t]*%.*(?:\r?\n|$)/gm, "");

        return clean;
    }

    function removeLatexCommentRemnants(clean) {
        // Final cleanup for TeX separator/comment remnants after all HTML
        // transformations have completed. Some malformed source paragraphs can
        // be restructured by the browser-oriented rendering pipeline, so clean
        // both wrapped and unwrapped percent-only remnants here.
        clean = clean.replace(
            /<p[^>]*>\s*(?:%+\s*(?:<br\s*\/?>)?\s*)+<\/p>/gi,
            ""
        );

        clean = clean.replace(
            /(^|>\s*)%+(?:\s*%+)*(?=\s*(?:<|$))/gmi,
            "$1"
        );

        return clean;
    }

    window.MathCmsRenderComments = {
        removeLatexComments,
        removeLatexCommentRemnants
    };
})();
