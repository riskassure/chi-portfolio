const base = '/api/photography/google';
const csrf = document.querySelector('meta[name="csrf"]').content;
const choose = document.getElementById('choose');
const progress = document.getElementById('progress');
const retry = document.getElementById('retry');
const cancel = document.getElementById('cancel');
const pickerLink = document.getElementById('picker-link');
let generation = 0;

async function api(path, data) {
    const response = await fetch(base + path, data === undefined ? {} : {
        method: 'POST', body: new URLSearchParams({ ...data, csrf })
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error || 'Request failed. Reload the page or reconnect Google Photos.');
    return result;
}

async function loadDrafts() {
    const { items } = await api('/drafts');
    const container = document.getElementById('drafts');
    container.replaceChildren();
    if (!items.length) container.textContent = 'No photos waiting for review.';
    for (const item of items) {
        const card = document.createElement('article');
        const img = document.createElement('img');
        img.src = `${base}/drafts/${item.digest}/image`;
        img.alt = item.title;
        img.loading = 'lazy';
        card.append(img);
        const fields = {};
        for (const [key, labelText] of [['title', 'Title'], ['location', 'Location']]) {
            const label = document.createElement('label');
            label.textContent = labelText;
            const input = document.createElement('input');
            input.value = item[key];
            input.maxLength = 200;
            fields[key] = input;
            label.append(input);
            card.append(label);
        }
        const publish = document.createElement('button');
        publish.textContent = 'Publish to gallery';
        const status = document.createElement('p');
        status.setAttribute('role', 'status');
        publish.onclick = async () => {
            publish.disabled = true;
            try {
                await api(`/drafts/${item.digest}/publish`, { title: fields.title.value, location: fields.location.value });
                status.textContent = 'Published. Refresh your gallery to see it.';
                publish.textContent = 'Published';
            } catch (error) { status.textContent = error.message; publish.disabled = false; }
        };
        card.append(publish, status);
        container.append(card);
    }
}

function duration(value, fallback) {
    const seconds = Number.parseFloat(value);
    return Number.isFinite(seconds) && seconds > 0 ? seconds * 1000 : fallback;
}

async function importSelection() {
    retry.hidden = true;
    choose.disabled = true;
    cancel.hidden = true;
    pickerLink.hidden = true;
    try {
        const { items } = await api('/picker/items');
        let imported = 0, duplicates = 0, skipped = 0, failed = 0;
        for (let i = 0; i < items.length; i++) {
            progress.textContent = `Importing ${i + 1} of ${items.length}: ${items[i].name}`;
            try {
                const result = await api('/picker/import', { id: items[i].id });
                imported += result.imported ? 1 : 0;
                duplicates += result.duplicate ? 1 : 0;
                skipped += result.skipped ? 1 : 0;
            } catch { failed++; }
        }
        await loadDrafts();
        progress.textContent = `${imported} imported, ${duplicates} already imported, ${skipped} videos skipped, ${failed} failed.`;
        if (failed) {
            retry.hidden = false;
            progress.textContent += ' Retry failed imports, or start a new selection if it has expired.';
        } else {
            await api('/picker/finish', {});
        }
    } catch (error) { progress.textContent = error.message; retry.hidden = false; }
    finally { choose.disabled = false; }
}

choose.onclick = async () => {
    const run = ++generation;
    // Open synchronously so browsers associate the new tab with the button click.
    const popup = window.open('about:blank', '_blank');
    if (popup) popup.opener = null;
    choose.disabled = true;
    retry.hidden = true;
    progress.textContent = 'Opening Google Photos…';
    try {
        const data = await api('/picker', {});
        pickerLink.href = data.pickerUri;
        pickerLink.hidden = false;
        if (popup) popup.location = data.pickerUri;
        cancel.hidden = false;
        progress.textContent = 'Choose photos in Google Photos and click Done. Keep this page open while they import.';
        let config = data.pollingConfig || {};
        let deadline = Date.now() + duration(config.timeoutIn, 600000);
        while (run === generation && Date.now() < deadline) {
            await new Promise(resolve => setTimeout(resolve, Math.max(1000, duration(config.pollInterval, 5000))));
            if (run !== generation) return;
            const state = await api('/picker');
            if (state.ready) { await importSelection(); return; }
            config = state.pollingConfig || config;
            if (config.timeoutIn) deadline = Math.min(deadline, Date.now() + duration(config.timeoutIn, 600000));
        }
        if (run === generation) {
            await api('/picker/finish', {}).catch(() => {});
            progress.textContent = 'Selection timed out. Click Add from Google Photos to try again.';
        }
    } catch (error) {
        try { if (popup && popup.location.href === 'about:blank') popup.close(); } catch { /* Google owns the picker tab. */ }
        progress.textContent = error.message;
    } finally {
        if (run === generation) { choose.disabled = false; cancel.hidden = true; pickerLink.hidden = true; }
    }
};
cancel.onclick = async () => {
    ++generation;
    cancel.hidden = true;
    pickerLink.hidden = true;
    try { await api('/picker/finish', {}); progress.textContent = 'Selection cancelled.'; }
    catch (error) { progress.textContent = error.message; }
    choose.disabled = false;
};
retry.onclick = importSelection;
loadDrafts().catch(error => { progress.textContent = error.message; });
