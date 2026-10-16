export function createEditor(state, photos) {
    const panel = document.getElementById('map-editor');
    const form = document.getElementById('place-form');
    const photoSelect = document.getElementById('edit-photo');
    const name = document.getElementById('edit-place-name');
    const lat = document.getElementById('edit-latitude');
    const lon = document.getElementById('edit-longitude');
    const id = document.getElementById('edit-place-id');
    const preview = document.getElementById('edit-photo-preview');
    const status = document.getElementById('edit-status');
    let picking = false;
    const editor = {get picking() {return picking;}, choose(point) {
        lat.value = point.latitude.toFixed(6); lon.value = point.longitude.toFixed(6);
        picking = false; status.textContent = 'Point selected. Review it, then save locally.';
        panel.scrollIntoView({block: 'nearest', behavior: 'smooth'});
    }, edit(place) {
        form.reset(); id.value = place.id; name.value = place.name;
        preview.hidden = true; picking = false;
        lat.value = place.latitude; lon.value = place.longitude; name.readOnly = false;
        panel.scrollIntoView({block: 'center', behavior: 'smooth'});
    }, async remove(place) {
        if (!confirm(`Remove â€œ${place.name}â€ from your local places?`)) return;
        await save({action: 'delete', id: place.id});
    }};
    if (!state?.editable) return null;
    panel.hidden = false;
    const regionForm = document.getElementById('region-form');
    const regionStatus = document.getElementById('region-status');
    const regionInputs = {};
    for (const [group, title] of [['US', 'U.S. states'], ['CA', 'Canadian provinces & territories'], ['countries', 'Countries & territories']]) {
        const section = document.createElement('details');
        const summary = document.createElement('summary'); section.append(summary);
        const filter = document.createElement('input'); filter.type = 'search';
        filter.placeholder = `Find ${title.toLowerCase()}`; filter.setAttribute('aria-label', filter.placeholder); section.append(filter);
        const options = document.createElement('div'); options.className = 'region-options'; section.append(options);
        regionInputs[group] = [];
        function count() { summary.textContent = `${title} (${regionInputs[group].filter(input => input.checked).length})`; }
        for (const region of state.regionOptions[group]) {
            const label = document.createElement('label'); const input = document.createElement('input');
            input.type = 'checkbox'; input.value = region.code; input.name = group;
            input.checked = state.regions[group].includes(region.code);
            input.addEventListener('change', () => {count(); regionStatus.textContent = 'Unsaved region changes.';});
            label.append(input, document.createTextNode(region.name)); options.append(label); regionInputs[group].push(input);
        }
        filter.addEventListener('input', () => {
            for (const label of options.children) label.hidden = !label.textContent.toLowerCase().includes(filter.value.trim().toLowerCase());
        });
        count(); document.getElementById('region-groups').append(section);
    }
    regionForm.addEventListener('submit', async event => {
        event.preventDefault();
        const button = regionForm.querySelector('button'); button.disabled = true;
        regionStatus.textContent = 'Saving regions...';
        try {
            const regions = Object.fromEntries(Object.entries(regionInputs).map(([key, inputs]) => [key, inputs.filter(input => input.checked).map(input => input.value)]));
            const response = await fetch(`${window.PORTFOLIO_API_BASE}/travel/places`, {method: 'POST', credentials: 'include',
                headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'regions', regions, revision: state.revision})});
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Could not save regions.');
            location.reload();
        } catch (error) {regionStatus.textContent = error.message; button.disabled = false;}
    });
    for (const photo of photos) {
        const option = document.createElement('option'); option.value = photo.file_path;
        option.textContent = `${photo.title || 'Photo'} â€” ${photo.map_location_name || photo.location_name || 'Unknown location'}${photo.located ? '' : ' (unplaced)'}`;
        photoSelect.append(option);
    }
    function pickPhoto(path) {
        const photo = photos.find(p => p.file_path === path);
        form.reset(); id.value = ''; picking = false; photoSelect.value = path;
        name.value = photo ? (photo.map_location_name || (photo.location_name === 'Unknown Location' ? '' : photo.location_name) || '') : '';
        name.placeholder = 'Enter the place name';
        name.readOnly = false;
        preview.hidden = !photo;
        if (photo) { preview.src = `../${photo.file_path}`; preview.alt = photo.title || 'Photo being placed'; }
        lat.value = photo?.latitude ?? ''; lon.value = photo?.longitude ?? '';
        status.textContent = photo ? "Name this photo location and choose its point. This name appears on the map and the photo's map link." : '';
    }
    photoSelect.addEventListener('change', () => pickPhoto(photoSelect.value));
    document.getElementById('pick-map-point').addEventListener('click', () => {
        picking = true; status.textContent = 'Click the desired point on the map, then save locally.';
        document.getElementById('travel-map').scrollIntoView({block: 'center', behavior: 'smooth'});
    });
    document.getElementById('cancel-map-edit').addEventListener('click', () => pickPhoto(''));
    async function save(body) {
        status.textContent = 'Savingâ€¦';
        try {
            const response = await fetch(`${window.PORTFOLIO_API_BASE}/travel/places`, {method: 'POST', credentials: 'include',
                headers: {'Content-Type': 'application/json'}, body: JSON.stringify({...body, revision: state.revision})});
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Could not save.');
            const url = new URL(location.href); url.searchParams.delete('edit');
            if (body.action === 'photo') url.searchParams.set('photo', body.file_path);
            else url.searchParams.delete('photo');
            location.assign(url);
        } catch (error) { status.textContent = error.message; }
    }
    form.addEventListener('submit', event => {
        event.preventDefault();
        const photo = photos.find(p => p.file_path === photoSelect.value);
        save({action: photo ? 'photo' : 'place', id: id.value || null, name: name.value,
            file_path: photo?.file_path, location_name: photo?.location_name || '',
            catalog_latitude: photo?.catalog_latitude, catalog_longitude: photo?.catalog_longitude,
            latitude: Number(lat.value), longitude: Number(lon.value)});
    });
    const unplaced = photos.filter(p => !p.located);
    document.getElementById('unplaced-count').textContent = `${unplaced.length} photos need a location`;
    for (const photo of unplaced) {
        const li = document.createElement('li'); const button = document.createElement('button');
        button.type = 'button'; button.textContent = photo.title || 'Untitled photo';
        button.addEventListener('click', () => pickPhoto(photo.file_path)); li.append(button);
        document.getElementById('unplaced-photos').append(li);
    }
    const query = new URLSearchParams(location.search);
    if (query.get('edit') === 'photo' && photos.some(p => p.file_path === query.get('photo'))) pickPhoto(query.get('photo'));
    return editor;
}
