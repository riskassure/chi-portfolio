// frontend/math/math_concept.js

const API_ENDPOINT = "http://127.0.0.1:5000/api";
const urlParams = new URLSearchParams(window.location.search);
const currentId = urlParams.get('id');
const currentSlug = urlParams.get('slug');

window.addEventListener("DOMContentLoaded", bootConceptView);

async function bootConceptView() {
    if (!currentId && !currentSlug) {
        document.getElementById("mathContentCanvas").innerHTML = "Error: No concept designated in query string parameters.";
        return;
    }

    try {
        // Fallback supports fetching details via either explicit numeric entry ID or clean text slug
        let fetchUrl = currentId ? `${API_ENDPOINT}/math/concepts/${currentId}` : `${API_ENDPOINT}/math/concepts/${currentSlug}`;
        
        const response = await fetch(fetchUrl);
        const json = await response.json();
        if (json.status !== "success") throw new Error(json.message);
        
        renderConceptPage(json.data);
    } catch (err) {
        console.error(err);
        document.getElementById("mathContentCanvas").innerHTML = `Failed to process content entry: ${err.message}`;
    }
}

async function renderConceptPage(concept) {
    try {
        // Set page metadata attributes
        document.title = `${concept.title || "Math Concept"} | Library`;
        document.getElementById("conceptTitle").innerText = concept.title || "Untitled Concept";
        document.getElementById("metaCreated").innerText = concept.created_at || "Unknown";
        document.getElementById("metaUpdated").innerText = concept.updated_at || "Unknown";

        // 1. #3 Document Types Badges Above
        const typesArr = concept.types || [];
        if (typesArr.length > 0) {
            document.getElementById("topTypes").innerHTML = typesArr
                .map(t => `<span class="math-tag tag-type">${t}</span>`).join('');
        } else {
            document.getElementById("topTypes").innerText = "None";
        }

        // 2. #3 Classifications
        const classTarget = document.getElementById("topClassifications");
        const classArray = concept.classifications || [];
        if (classArray.length > 0) {
            classTarget.innerHTML = classArray.map(item => {
                return `<span class="math-tag tag-msc" title="${item.text}">${item.code} (${item.text})</span>`;
            }).join(' ');
        } else {
            classTarget.innerText = "None assigned";
        }

        // 3. #4 Render Footers layout
        renderFooterArrays(concept);

        // 4. #1 & #2 Process TeX payload
        let rawTexContent = concept.cleaned_tex || "No textual mathematical content saved.";
        
        // --- START FIX: Prevent crash from unsupported pspicture ---
        // This strips out the pspicture blocks and places a placeholder instead
        let preProcessedTex = rawTexContent.replace(
            /\\begin\{pspicture\}.*?\\end\{pspicture\}/gs, 
            '<div class="img-placeholder" style="border: 1px dashed #ccc; padding: 10px; color: #666;"><em>[Diagram: Convert to SVG]</em></div>'
        );
        // --- END FIX ---

        const canvas = document.getElementById("mathContentCanvas");
        canvas.innerHTML = preProcessedTex;

        // --- CRITICAL: Trigger asynchronous MathJax 3 rendering ---
        if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
            // Clear previous MathJax rendering for this canvas
            if (typeof window.MathJax.typesetClear === "function") {
                window.MathJax.typesetClear([canvas]);
            }
            
            // Typeset the new content
            await window.MathJax.typesetPromise([canvas]);
        }

    } catch (renderError) {
        console.error("Crash during DOM parsing:", renderError);
        document.getElementById("mathContentCanvas").innerHTML = `Parsing Error: ${renderError.message}`;
    }
}

function cleanLaTeXEnvironments(tex) {
    if (!tex) return "";
    let clean = tex;

    // 1. Convert lists (\begin{enumerate} and \begin{itemize}) into clean HTML lists
    clean = clean.replace(/\\begin{enumerate}/gi, "<ol style='margin-top: 0.5rem; padding-left: 1.5rem;'>");
    clean = clean.replace(/\\end{enumerate}/gi, "</ol>");
    
    clean = clean.replace(/\\begin{itemize}/gi, "<ul style='margin-top: 0.5rem; padding-left: 1.5rem; list-style-type: disc;'>");
    clean = clean.replace(/\\end{itemize}/gi, "</ul>");

    // 2. Map structural text block list items safely
    clean = clean.replace(/\\item/gi, "<li style='margin-bottom: 0.25rem;'>");

    // 3. Translate inline text styling macros (\emph and \textbf) into browser-native HTML tags
    // This utilizes a regex pattern to safely extract text within curly braces without clipping math blocks
    clean = clean.replace(/\\emph\{([^}]+)\}/gi, "<em>$1</em>");
    clean = clean.replace(/\\textbf\{([^}]+)\}/gi, "<strong>$1</strong>");

    // 4. Convert \begin{thebibliography} layouts into dynamic bibliography wrappers
    clean = clean.replace(/\\begin{thebibliography}{[\s\S]*?}/gi, "<div style='margin-top: 1.5rem; border-top: 1px dashed #cbd5e1; padding-top: 1rem;'><strong>References & Bibliography:</strong><ul style='list-style-type: square; padding-left: 1.5rem;'>");
    clean = clean.replace(/\\end{thebibliography}/gi, "</ul></div>");

    return clean;
}

function renderFooterArrays(concept) {
    // 1. Synonyms Array Mapping
    const syns = concept.synonyms || [];
    document.getElementById("bottomSynonyms").innerHTML = syns.length > 0 ? syns.join(", ") : "None";

    // 2. Other Concepts Defined Here (Maps directly to your backend's 'definitions' property key)
    const defsCard = document.getElementById("bottomDefinedHere").parentElement;
    if (defsCard) defsCard.querySelector("h4").innerText = "Other Concepts Defined Here";
    
    const defs = concept.definitions || [];
    document.getElementById("bottomDefinedHere").innerHTML = defs.length > 0 ? defs.map(d => `<code>${d}</code>`).join(", ") : "None";

    // 3. Related Concepts (Backlinks calculation placeholder column)
    const relatedCard = document.getElementById("bottomRelated").parentElement;
    if (relatedCard) relatedCard.querySelector("h4").innerText = "Related Concepts";

    const related = concept.related_concepts || concept.links_referenced || [];
    if (related.length > 0) {
        document.getElementById("bottomRelated").innerHTML = related
            .map(r => {
                const targetSlug = r.slug || r;
                const targetTitle = r.title || r;
                return `<a href="concept.html?slug=${encodeURIComponent(targetSlug)}" class="math-autolink" style="margin-right:0.5rem; display:inline-block;">${targetTitle}</a>`;
            }).join('');
    } else {
        document.getElementById("bottomRelated").innerText = "None";
    }
}