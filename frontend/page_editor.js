/* Text-only editing: existing HTML, links and layout remain intact. */
(async () => {
    const page = location.pathname.endsWith('/resume.html') ? 'resume' : 'bio';
    const nodes = [...document.querySelectorAll('[data-page-text]')];
    const endpoint = `${window.PORTFOLIO_API_BASE}/pages/${page}`;
    let version = 0, editing = false;
    const toolbar = document.createElement('section');
    toolbar.className = 'page-editor'; toolbar.hidden = true;
    toolbar.setAttribute('aria-label', 'Page editing');
    toolbar.innerHTML = '<button type="button" data-action="edit">Edit page text</button><button type="button" data-action="save" hidden>Save changes</button><button type="button" data-action="cancel" hidden>Cancel</button><p role="status" aria-live="polite"></p>';
    document.querySelector('main').prepend(toolbar);
    const status = toolbar.querySelector('[role="status"]');
    const button = name => toolbar.querySelector(`[data-action="${name}"]`);
    let saved;
    const collect = () => Object.fromEntries(nodes.map(n => [n.dataset.pageText, n.textContent]));
    function toggle(active) {
        editing = active;
        for (const n of nodes) {
            if (active) { n.contentEditable = 'plaintext-only'; n.setAttribute('role','textbox'); }
            else { n.removeAttribute('contenteditable'); n.removeAttribute('role'); }
        }
        button('edit').hidden = active; button('save').hidden = !active; button('cancel').hidden = !active;
    }
    try {
        const response = await fetch(endpoint, {credentials:'include', cache:'no-store'});
        if (!response.ok) throw Error('Unable to load saved page text.');
        const data = await response.json(); version = data.version;
        for (const n of nodes) if (Object.hasOwn(data.fields,n.dataset.pageText)) n.textContent = data.fields[n.dataset.pageText];
        saved = collect();
        const session = await fetch(`${window.PORTFOLIO_API_BASE}/session-check`, {credentials:'include'}).then(r=>r.json());
        toolbar.hidden = !session.is_admin;
    } catch (error) {
        // Make failure visible rather than inviting edits based on stale content.
        toolbar.hidden = false; button('edit').hidden = true;
        status.textContent = 'Saved content could not be loaded. Please refresh; the original page text is shown.';
        return;
    }
    button('edit').onclick = () => { toggle(true); status.textContent = 'Click any outlined text to edit. Formatting and link destinations stay unchanged.'; nodes[0]?.focus(); };
    button('cancel').onclick = () => { for (const n of nodes) n.textContent = saved[n.dataset.pageText]; toggle(false); status.textContent = 'Changes discarded.'; };
    toolbar.addEventListener('click',e=>e.stopPropagation());
    document.querySelector('main').addEventListener('click', e => { if(editing && e.target.closest('a')) e.preventDefault(); });
    button('save').onclick = async () => {
        button('save').disabled = true; button('cancel').disabled = true;
        const fields = collect();
        for (const n of nodes) n.contentEditable = 'false';
        try {
            const response = await fetch(endpoint, {method:'PUT',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({version,fields})});
            const data = await response.json();
            if (!response.ok) throw Error(data.error || 'Save failed.');
            version = data.version; saved = fields; toggle(false); status.textContent = 'Saved. Visitors can now see these changes.';
        } catch (error) { toggle(true); status.textContent = error.message; }
        finally { button('save').disabled = false; button('cancel').disabled = false; }
    };
    window.addEventListener('beforeunload',e=>{if(editing && JSON.stringify(collect())!==JSON.stringify(saved)){e.preventDefault();e.returnValue='';}});
})();
