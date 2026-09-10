// frontend/math/render/math_render_helpers.js

(function () {
    const DEFAULT_API_ENDPOINT = "http://127.0.0.1:5000/api";

    window.MathCmsRender = {
        debugVersion: "multline-protection-v1",
        getDisplayTex,
        prepareConceptHtml,
        cleanLaTeXEnvironments,
        normalizeDiagramImageUrls,
        renderXyMatrixDiagonalOverlays
    };

    function getDisplayTex(concept) {
        return (
            concept?.display_tex ||
            concept?.rendered_tex ||
            concept?.cleaned_tex ||
            "No textual mathematical content saved."
        );
    }

    function prepareConceptHtml(tex, options = {}) {
        const apiEndpoint =
            options.apiEndpoint ||
            window.MATH_CMS_API_ENDPOINT ||
            DEFAULT_API_ENDPOINT;

        let clean = tex || "";

        /*
        * Expand concept-local \newcommand definitions before the
        * ordinary rendering cleanup pipeline.
        */
        if (
            window.MathCmsLocalMacros &&
            typeof window.MathCmsLocalMacros.apply === "function"
        ) {
            clean = window.MathCmsLocalMacros.apply(
                clean,
                options.localMacroSource || "",
                options.context || {}
            );
        }

        clean = cleanLaTeXEnvironments(clean);
        clean =
            window.MathCmsRenderMathText
                .restoreUnderlineHtmlInsideMath(clean);
        clean = normalizeDiagramImageUrls(
            clean,
            apiEndpoint
        );

        return clean;
    }

    async function renderXyMatrixDiagonalOverlays(root = document) {
        return window.MathCmsRenderXyOverlays
            .renderXyMatrixDiagonalOverlays(root);
    }

    function cleanLaTeXEnvironments(tex) {
        if (!tex) return "";

        let clean = String(tex || "");

        const eqnarrayProtection =
            window.MathCmsRenderEqnarrayProtection.protectEqnarrayEnvironments(clean);
        clean = eqnarrayProtection.text;

        const verbProtection =
            window.MathCmsRenderVerbatim
                .protectLatexVerbCommands(clean);
        clean = verbProtection.text;

        clean =
            window.MathCmsRenderMboxTables
                .normalizeMboxTabularInsideMath(clean);

        clean =
            window.MathCmsRenderMboxTables
                .normalizeMboxHtmlTableInsideMath(clean);

        clean = window.MathCmsRenderHtmlMultirow
            .normalizeHtmlTableMultirows(clean);

        clean = window.MathCmsRenderAlgorithms.normalizeAlgorithmCodeBlocks(clean);

        const mboxProtection =
            window.MathCmsRenderMathText
                .protectMboxInsideMath(clean);
        clean = mboxProtection.text;

        clean = window.MathCmsRenderComments
            .removeLatexComments(clean);

        clean = window.MathCmsRenderMathText
            .normalizeFormattedProseMathDelimiters(clean);

        // Keep bold symbols inside math as TeX instead of later converting
        // them into invalid HTML tags inside MathJax delimiters.
        clean = window.MathCmsRenderMathText.normalizeTextBoldInsideMath(clean);
        clean = window.MathCmsRenderMathText.normalizeTextItalicInsideMath(clean);

        // Repair HTML paragraph artifacts inside cases/array environments before
        // literal < and > characters are protected for safe innerHTML insertion.
        clean =
            window.MathCmsRenderStructuredMath
                .normalizeStructuredMathHtmlArtifacts(clean);

        // Repair paragraph and line-break artifacts inside xymatrix bodies before
        // literal angle brackets inside math are protected as \lt and \gt.
        clean = window.MathCmsRenderXyCleanup
            .normalizeXyMatrixHtmlArtifacts(clean);

        clean = window.MathCmsRenderLegacyTex.normalizeLegacyOverFractions(clean);

        clean = window.MathCmsRenderLegacyTex
            .removeNoBreakCommands(clean);

        // Remove Xy-pic setup commands that have no visible page meaning.
        clean =
            window.MathCmsRenderXyCleanup
                .stripXyMatrixSetupMacros(clean);

        clean = window.MathCmsRenderXyConversion.convertUnderbracedXyMatrixToHtml(clean);
        clean = window.MathCmsRenderXyConversion.convertXyMatrixToHtml(clean);

        // Remove display wrappers left around generated Xy-pic HTML.
        clean = window.MathCmsRenderXySequences
            .unwrapConvertedXyMatrixMathWrappers(clean);

        // Render operators stranded between converted xymatrix blocks.
        clean =
            window.MathCmsRenderXyCleanup
                .renderXyMatrixConnectorMath(clean);

        const xyHtmlProtection = window.MathCmsRenderXyCleanup
            .protectXyMatrixHtml(clean);
        clean = xyHtmlProtection.text;

        clean =
            window.MathCmsRenderHtmlSensitiveMath
                .normalizeHtmlSensitiveMathCharacters(clean);

        clean = window.MathCmsRenderXyCleanup
            .restoreXyMatrixHtml(clean, xyHtmlProtection.blocks);

        // Normalize legacy display wrappers so MathJax can process their contents.
        clean =
            window.MathCmsRenderDisplayEnvironments
                .normalizeDisplayMathEnvironments(clean);
        clean = window.MathCmsRenderDollarDisplay.normalizeDollarDisplayMath(clean);

        // Convert common PlanetMath piecewise array blocks before MathJax typesetting.
        clean = window.MathCmsRenderPiecewise
            .convertPiecewiseArraysToHtml(clean);

        // Convert align/alignat blocks into HTML alignment tables.
        clean = window.MathCmsRenderAlign
            .convertAlignEnvironmentsToHtml(clean);

        // Convert simple display matrix/array blocks that MathJax often cannot recover
        // after PlanetMath row separators were lost.
        clean = window.MathCmsRenderMatrixDisplay
            .convertSimpleDisplayMatricesToHtml(clean);

        clean = window.MathCmsRenderTextColor
            .normalizeLegacyTableColors(clean);

        clean = window.MathCmsRenderMathText
            .normalizeLegacyFontSizes(clean);

        clean = window.MathCmsRenderMathText
            .normalizeProseUnderline(clean);

        clean = window.MathCmsRenderImages
            .normalizeStarredIncludeGraphics(clean);

        // Replace old LaTeX/EPS image commands with readable placeholders.
        clean = window.MathCmsRenderImages.normalizeLatexImageArtifacts(
            clean,
            window.MathCmsRenderHtmlUtils.escapeHtmlForMathCell
        );
        
        // Arrange related placeholders while legacy layout markers
        // such as \raisebox and \hskip are still present.
        clean = window.MathCmsRenderPlaceholderLayout
            .normalizePlaceholderImageLayouts(clean);

        clean = window.MathCmsRenderMathText
            .normalizeMathConjunctionSpacing(clean);

        // Convert TeX footnotes into visible note blocks while preserving
        // any MathJax expressions contained inside them.
        clean = window.MathCmsRenderFootnotes.normalizeFootnoteMacros(clean);

        // Convert legacy custom Roman-numbered lists before the generic
        // \item conversion later in this pipeline.
        clean =
            window.MathCmsRenderLegacyLists
                .normalizeLegacyRomanList(clean);

        // Prose layout cleanup must not remove legitimate commands such as
        // \quad, \text, or \mbox from inside MathJax expressions.
        const proseMathProtection =
            window.MathCmsRenderProseMath
                .protectMathForProseCleanup(clean);
        clean = proseMathProtection.text;

        clean =
            window.MathCmsRenderProseLayout
                .normalizeProseLayoutMacros(clean);

        clean =
            window.MathCmsRenderProseMath
                .restoreMathAfterProseCleanup(
                    clean,
                    proseMathProtection.blocks
                );

        // Convert inline matrices and expressions containing multiple matrices only
        // after prose wrappers outside math have been normalized.
        clean = window.MathCmsRenderMatrixSequences
            .convertRemainingMatrixMathSequencesToHtml(clean);

        // Restore protected eqnarray blocks only after prose and layout cleanup.
        // This keeps row separators and text commands intact for the converter.
        clean =
            window.MathCmsRenderEqnarrayProtection.restoreEqnarrayEnvironments(
                clean,
                eqnarrayProtection.blocks
            );

        // Normalize legacy eqnarray blocks before MathJax sees them.
        clean = window.MathCmsRenderEqnarray.convertEqnarrayToAligned(clean);

        // Convert the simple PSTricks deduction trees.
        clean = window.MathCmsRenderPstree
            .convertSimpleDeductionPstreeToHtml(clean);

        // Convert the larger fixed diagram used by "rooted-tree".
        clean = window.MathCmsRenderPstree
            .convertRootedTreePstreeToHtml(clean);

        clean = window.MathCmsRenderPstree
            .replaceUnsupportedPspictureEnvironments(clean);

        clean = window.MathCmsRenderLegacyLists
            .normalizeStandardListEnvironments(clean);

        clean = window.MathCmsRenderMathText
            .normalizeLegacyTextFormatting(clean);

        clean = window.MathCmsRenderLegacyLists
            .normalizeBibliographyEnvironments(clean);

        clean = window.MathCmsRenderTabular
            .convertTabularEnvironmentsToHtml(clean);

        clean = window.MathCmsRenderComments
            .removeLatexCommentRemnants(clean);

        // Restore protected \verb contents only after all structural parsing
        // and HTML-sensitive processing has completed.
        clean =
            window.MathCmsRenderVerbatim
                .restoreLatexVerbCommands(
                    clean,
                    verbProtection.verbValues
                );

        clean =
            window.MathCmsRenderMathText
                .restoreMboxInsideMath(
                    clean,
                    mboxProtection.values
                );

        clean = window.MathCmsRenderProofLayout
            .normalizeSketchProofHeading(clean);

        // Start proof-related lead labels in their own paragraphs when
        // backend HTML has flattened several TeX \par sections together.
        clean =
            window.MathCmsRenderProofLayout
                .splitProofLeadParagraphs(clean);

        // Remove theorem/definition wrappers whose bodies became empty
        clean =
            window.MathCmsRenderMathEnv
                .removeEmptyMathEnvironmentSections(clean);

        // Keep punctuation attached to the inline MathJax expression that
        // immediately precedes it.
        clean = window.MathCmsRenderInlineMath.preventInlineMathPunctuationWrap(clean);

        return clean;
    }

    function normalizeDiagramImageUrls(
        html,
        apiEndpoint = DEFAULT_API_ENDPOINT
    ) {
        return window.MathCmsRenderImages.normalizeDiagramImageUrls(
            html,
            apiEndpoint
        );
    }
})();