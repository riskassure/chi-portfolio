const endpoint = `${window.PORTFOLIO_API_BASE}/travel/places`;
const status = document.getElementById('city-status');
const container = document.getElementById('city-checklist');
const saveButton = document.getElementById('save-cities');
const remainingButton = document.getElementById('mark-remaining');
const downloadButton = document.getElementById('download-cities');
let dirty = false;
window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
try {
    const response = await fetch(endpoint, {credentials: 'include'});
    if (!response.ok) throw new Error('Could not load the city checklist.');
    let state = await response.json();
    const visits = new Map(state.cities.map(c => [c.id, state.data.cityVisits[c.id] || (c.previouslyExcluded ? 'not-visited' : '')]));
    const selects = new Map();
    function totals() {
        const counts = {'visited': 0, 'not-visited': 0, 'unsure': 0, '': 0};
        for (const value of visits.values()) counts[value]++;
        document.getElementById('city-summary').textContent = `${counts.visited} visited · ${counts['not-visited']} not visited · ${counts.unsure} unsure · ${counts['']} not reviewed`;
    }
    let group;
    let lastState;
    for (const city of state.cities) {
        if (city.state !== lastState) {
            group = document.createElement('section'); group.className = 'city-group';
            const heading = document.createElement('h2'); heading.textContent = city.state; group.append(heading);
            container.append(group); lastState = city.state;
        }
        const row = document.createElement('label'); row.className = 'city-row';
        row.dataset.search = `${city.name} ${city.state}`.toLowerCase();
        const name = document.createElement('span'); name.textContent = city.name;
        const select = document.createElement('select'); select.disabled = !state.editable;
        select.setAttribute('aria-label', `${city.name}, ${city.state} visit status`);
        for (const [value, label] of [['', 'Not reviewed'], ['visited', 'Visited'], ['not-visited', 'Not visited'], ['unsure', 'Unsure']]) {
            const option = document.createElement('option'); option.value = value; option.textContent = label; select.append(option);
        }
        select.value = visits.get(city.id); selects.set(city.id, select);
        select.addEventListener('change', () => { visits.set(city.id, select.value); dirty = true; totals(); });
        row.append(name, select); group.append(row);
    }
    totals(); downloadButton.disabled = false;
    saveButton.disabled = remainingButton.disabled = !state.editable;
    status.textContent = state.editable ? 'Your changes stay local until published.' : 'Sign in on the local website to edit this checklist, then reload this page.';
    document.getElementById('city-search').addEventListener('input', event => {
        const term = event.target.value.trim().toLowerCase();
        for (const row of container.querySelectorAll('.city-row')) row.hidden = !row.dataset.search.includes(term);
        for (const section of container.querySelectorAll('.city-group')) section.hidden = !section.querySelector('.city-row:not([hidden])');
    });
    remainingButton.addEventListener('click', () => {
        const count = [...visits.values()].filter(v => !v).length;
        if (!count || !confirm(`Mark all ${count} unreviewed cities as visited, including cities hidden by the search filter? Not visited and unsure choices will stay unchanged.`)) return;
        for (const [id, value] of visits) if (!value) { visits.set(id, 'visited'); selects.get(id).value = 'visited'; }
        dirty = true; totals(); status.textContent = 'Review the totals, then save to add visited-city pins.';
    });
    saveButton.addEventListener('click', async () => {
        saveButton.disabled = true;
        try {
            const response = await fetch(endpoint, {method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'cities', revision: state.revision, visits: Object.fromEntries([...visits].filter(([, v]) => v))})});
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Could not save.');
            state = result; dirty = false; status.textContent = 'Saved locally. Open the travel map to see your reviewed city pins.';
        } catch (error) { status.textContent = error.message; }
        finally { saveButton.disabled = !state.editable; }
    });
    downloadButton.addEventListener('click', () => {
        const lines = ['U.S. city travel checklist', '', ...state.cities.map(c => `${c.state} — ${c.name}: ${visits.get(c.id) || 'not reviewed'}`)];
        const url = URL.createObjectURL(new Blob([lines.join('\n')], {type: 'text/plain'}));
        const link = document.createElement('a'); link.href = url; link.download = 'us-city-checklist.txt'; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
} catch (error) { status.textContent = error.message; }
