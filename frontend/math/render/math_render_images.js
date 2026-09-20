(() => {

function normalizeLatexImageArtifacts(
    tex,
    escapeHtml,
    apiEndpoint,
    context = {}
) {
    if (!tex) return "";

    let output = String(tex || "");

    // The legacy filename automaton.eps is reused by several PlanetMath
    // articles for different figures. Give the simplified-automaton article
    // its own reconstruction without changing the diagrams in those articles.
    if (context.slug === "simplified-automaton") {
        output = output.replace(
            /(\\includegraphics(?:\[[^\]]*\])?\s*\{)automaton(?:\.eps)?(\})/gi,
            "$1simplified_automaton.eps$2"
        );
    }

    // Remove figure wrappers but keep their contents.
    output = output.replace(
        /\\begin\{figure\*?\}(?:\[[^\]]*\])?/gi,
        ""
    );

    output = output.replace(
        /\\end\{figure\*?\}/gi,
        ""
    );

    // LaTeX layout commands around old EPS images.
    output = output.replace(
        /\\centering\b/gi,
        ""
    );

    // \scalebox{0.8}{\includegraphics{file.eps}}
    output = output.replace(
        /\\scalebox\{[^{}]*\}\s*\{\s*\\includegraphics(?:\[[^\]]*\])?\s*\{([^{}]*)\}\s*\}/gi,
        function (_, filename) {
            return makeLatexImageOrPlaceholder(
                filename,
                escapeHtml,
                apiEndpoint
            );
        }
    );

    // Plain \includegraphics[scale=...]{file.eps}
    // or \includegraphics{file.eps}
    output = output.replace(
        /\\includegraphics(?:\[[^\]]*\])?\s*\{([^{}]*)\}/gi,
        function (_, filename) {
            return makeLatexImageOrPlaceholder(
                filename,
                escapeHtml,
                apiEndpoint
            );
        }
    );

    // The knot-theory entry stores its four opening examples as two legacy
    // LaTeX rows. Combine that exact sequence into one responsive grid.
    output = output.replace(
        /(<span\b[^>]*data-legacy-image="knot10_89"[^>]*>[\s\S]*?<\/span>\s*<\/span>)[\s\S]*?(<span\b[^>]*data-legacy-image="trefoil"[^>]*>[\s\S]*?<\/span>\s*<\/span>)[\s\S]*?(<span\b[^>]*data-legacy-image="nasty_unknot"[^>]*>[\s\S]*?<\/span>\s*<\/span>)[\s\S]*?(<span\b[^>]*data-legacy-image="unknot"[^>]*>[\s\S]*?<\/span>\s*<\/span>)/i,
        '<span class="pm-knot-grid mathjax-diagnostic-ignore">$1$2$3$4</span>'
    );

    output = groupReidemeisterPair(output, "twist", "untwist", "Type I");
    output = groupReidemeisterPair(output, "parallel", "passover", "Type II");
    output = groupReidemeisterPair(output, "r3", "r3", "Type III", true);

    // Preserve captions as readable prose.
    output = output.replace(
        /\\caption\{([^{}]*)\}/gi,
        function (_, caption) {
            const cleanCaption =
                cleanLatexImageLabelText(
                    caption
                );

            if (!cleanCaption) {
                return "";
            }

            return `
                <div class="pm-latex-image-caption mathjax-diagnostic-ignore" style="text-align:center; color:#64748b; font-size:0.92rem; margin:0.25rem 0 1rem;">
                    <em>${escapeHtml(cleanCaption)}</em>
                </div>
            `;
        }
    );

    return output;
}


function groupReidemeisterPair(
    output,
    leftStem,
    rightStem,
    label,
    rotateRight = false
) {
    const escapePattern = value => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const diagram = stem =>
        `(<span\\b[^>]*data-reidemeister-image="${escapePattern(stem)}"[^>]*>[\\s\\S]*?<\\/span>)`;
    const pairPattern = new RegExp(
        `${diagram(leftStem)}[\\s\\S]*?${diagram(rightStem)}`,
        "i"
    );

    return output.replace(pairPattern, function (_, left, right) {
        const rightDiagram = rotateRight
            ? right.replace(
                "pm-reidemeister-diagram",
                "pm-reidemeister-diagram pm-reidemeister-rotated"
            )
            : right;

        return `
            <span class="pm-reidemeister-row mathjax-diagnostic-ignore">
                <span class="pm-reidemeister-type">${label}</span>
                <span class="pm-reidemeister-pair">
                    ${left}
                    <span class="pm-reidemeister-arrow" aria-hidden="true">&#x27F7;</span>
                    ${rightDiagram}
                </span>
            </span>
        `;
    });
}


const availableLegacyImageStems = new Set([
    "adjacencymat_graph",
    "angle",
    "atomic_automata",
    "automaton",
    "automaton1",
    "automaton2",
    "automaton3",
    "automaton_mat",
    "bary",
    "bary2",
    "betweenness",
    "betweenness1",
    "cevian",
    "chisquared0",
    "construct.1",
    "dtree",
    "ecircuit",
    "epath",
    "fdist1",
    "fdist2",
    "hyp",
    "knot10_89",
    "median",
    "mealy",
    "moore",
    "nasty_unknot",
    "parallel",
    "passover",
    "polar_1",
    "polar_2",
    "polar_3",
    "polar_4",
    "polar_5",
    "sector",
    "semiautomaton",
    "simplified_automaton",
    "r3",
    "t_dist",
    "tdist",
    "trefoil",
    "triangle.1",
    "triangle.2",
    "tree",
    "tree1",
    "tree2",
    "twist",
    "untwist",
    "unknot"
]);

const legacyReidemeisterStems = new Set([
    "parallel",
    "passover",
    "r3",
    "twist",
    "untwist"
]);

const legacyImageExtensions = new Map([
    ["knot10_89", "png"],
    ["nasty_unknot", "jpg"],
    ["trefoil", "png"],
    ["unknot", "png"]
]);

const legacyKnotLabels = new Map([
    ["knot10_89", "Knot 10₈₉"],
    ["trefoil", "Trefoil knot (3₁)"],
    ["nasty_unknot", "Nasty unknot (7 crossings)"],
    ["unknot", "Goeritz unknot (11 crossings)"]
]);


function makeLatexImageOrPlaceholder(
    filename,
    escapeHtml,
    apiEndpoint
) {
    const cleanFilename = cleanLatexImageLabelText(filename);
    const stem = cleanFilename
        .replace(/\.(?:eps|ps|pdf|svg|png|jpe?g|gif)$/i, "")
        .toLowerCase();

    if (!availableLegacyImageStems.has(stem)) {
        return makeLatexImagePlaceholder(filename, escapeHtml);
    }

    const baseEndpoint = String(apiEndpoint || "http://127.0.0.1:5000/api")
        .replace(/\/$/, "");
    const extension = legacyImageExtensions.get(stem) || "svg";
    const src = `${baseEndpoint}/math/diagrams/legacy/${encodeURIComponent(stem)}.${extension}`;

    if (legacyImageExtensions.has(stem)) {
        const knotLabel = legacyKnotLabels.get(stem) || cleanFilename;
        return `
            <span class="pm-latex-image pm-reconstructed-image pm-knot-example mathjax-diagnostic-ignore" data-legacy-image="${escapeHtml(stem)}">
                <img src="${escapeHtml(src)}" alt="Knot diagram: ${escapeHtml(cleanFilename)}" loading="lazy" />
                <span class="pm-knot-label">${escapeHtml(knotLabel)}</span>
            </span>
        `;
    }

    if (legacyReidemeisterStems.has(stem)) {
        return `
            <span class="pm-latex-image pm-reconstructed-image pm-reidemeister-diagram mathjax-diagnostic-ignore" data-reidemeister-image="${escapeHtml(stem)}">
                <img src="${escapeHtml(src)}" alt="Reidemeister move diagram: ${escapeHtml(cleanFilename)}" loading="lazy" />
            </span>
        `;
    }

    return `
        <div class="pm-latex-image pm-reconstructed-image mathjax-diagnostic-ignore" style="margin:1.25rem auto; text-align:center;">
            <img src="${escapeHtml(src)}" alt="Reconstructed mathematical diagram: ${escapeHtml(cleanFilename)}" loading="lazy" style="display:block; width:auto; max-width:100%; max-height:28rem; margin:0 auto;" />
        </div>
    `;
}


function makeLatexImagePlaceholder(
    filename,
    escapeHtml
) {
    const cleanFilename =
        cleanLatexImageLabelText(
            filename
        );

    const label =
        cleanFilename
            ? `Image placeholder: ${escapeHtml(cleanFilename)}`
            : "Image placeholder";

    return `
        <div class="pm-latex-image-placeholder mathjax-diagnostic-ignore" style="margin:1rem auto; padding:0.75rem; max-width:28rem; border:1px dashed #cbd5e1; border-radius:6px; background:#f8fafc; color:#64748b; text-align:center;">
            <em>[${label}]</em>
        </div>
    `;
}


function cleanLatexImageLabelText(value) {
    return String(value || "")
        // If the backend autolinker already linked text inside an
        // image filename/caption, keep only the visible linked text.
        .replace(
            /<a\b[^>]*>([\s\S]*?)<\/a>/gi,
            "$1"
        )

        // Remove any other accidental HTML tags from
        // placeholder labels.
        .replace(/<[^>]*>/g, "")

        // Basic entity cleanup.
        .replace(/&nbsp;/gi, " ")
        .replace(/&amp;/gi, "&")
        .replace(/&lt;/gi, "<")
        .replace(/&gt;/gi, ">")
        .replace(/&quot;/gi, '"')

        .replace(/\s+/g, " ")
        .trim();
}


function normalizeDiagramImageUrls(
    html,
    apiEndpoint
) {
    if (!html) return "";

    return html.replace(
        /src=(["'])\/api\/math\/diagrams\//gi,
        `src=$1${apiEndpoint}/math/diagrams/`
    );
}


    function normalizeStarredIncludeGraphics(clean) {
        // Normalize the starred legacy form so the existing image converter
        // handles both \includegraphics and \includegraphics*.
        clean = clean.replace(
            /\\includegraphics\*/gi,
            "\\includegraphics"
        );

        return clean;
    }

window.MathCmsRenderImages = {
    normalizeLatexImageArtifacts,
    normalizeDiagramImageUrls,
    normalizeStarredIncludeGraphics
};

})();
