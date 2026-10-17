import {createEditor} from './travel-editor.js';
const reference = window.TRAVEL_REFERENCE;
const history = window.TRAVEL_HISTORY;
const status = document.getElementById('map-status');
const list = document.getElementById('place-list');
const detail = document.getElementById('place-detail');
const search = document.getElementById('place-search');
let states = reference.states.filter(f => !history.overnightStateExceptions.includes(f.properties.code));
let countries = reference.countries.filter(f => history.countries.includes(f.properties.code));
let provinces = [];
const places = [...reference.places, ...history.additionalPlaces];
let view;
let editor;
let photoRows = [];
let placeState;
let selectedPhoto = new URLSearchParams(location.search).get('photo');
const graphics = new Map();
const layers = {};
const worldBounds = {xmin: -180, ymin: -58, xmax: 180, ymax: 80, spatialReference: {wkid: 4326}};

function counts() {
    const container = document.getElementById('travel-counts');
    container.replaceChildren();
    for (const text of [`${states.length} overnight states`, `${provinces.length} Canadian provinces / territories`, `${countries.length} countries visited`, `${reference.places.length} national parks`, `${places.filter(p => p.kind === 'city').length} reviewed cities`]) {
        const span = document.createElement('span'); span.textContent = text; container.append(span);
    }
}

function showDetail(place) {
    detail.replaceChildren(); detail.hidden = false;
    const heading = document.createElement('h2'); heading.textContent = place.name; detail.append(heading);
    if (place.kind === 'park') {
        const note = document.createElement('p'); note.textContent = 'Visited · General park location'; detail.append(note);
        const link = document.createElement('a'); link.href = place.url; link.textContent = 'Explore this park at NPS.gov'; detail.append(link);
    }
    if (place.kind === 'photo') {
        const note = document.createElement('p'); note.textContent = [...new Set(place.photos.map(p => p.coordinate_source))].join(' · ');
        detail.append(note);
    }
    if (editor && place.kind === 'place') {
        for (const [label, action] of [['Edit this place', () => editor.edit(place)], ['Remove this place', () => editor.remove(place)]]) {
            const button = document.createElement('button'); button.type = 'button'; button.className = 'editor-action';
            button.textContent = label; button.addEventListener('click', action); detail.append(button);
        }
    }
    for (const photo of place.photos || []) {
        const link = document.createElement('a'); link.className = 'place-photo';
        link.href = `../photography/index.html?photo=${encodeURIComponent(photo.file_path)}`;
        const img = document.createElement('img'); img.src = `../${photo.file_path}`; img.alt = photo.title || place.name; img.loading = 'lazy';
        const title = document.createElement('span'); title.textContent = photo.title || 'View photograph';
        link.append(img, title); detail.append(link);
    }
}

async function selectPlace(place) {
    showDetail(place);
    if (!view) return;
    const kind = place.kind === 'photo' ? 'photos' : place.kind === 'park' ? 'parks' : 'cities';
    const layer = layers[kind];
    if (layer) layer.visible = true;
    document.getElementById(`show-${kind}`).checked = true;
    try { await view.goTo({center: [place.longitude, place.latitude], zoom: 9}); }
    catch (error) { if (error.name !== 'AbortError') status.textContent = 'Could not move the map to this location.'; }
}

function renderList() {
    const term = search.value.trim().toLocaleLowerCase();
    const results = places.filter(p => p.name.toLocaleLowerCase().includes(term));
    list.replaceChildren();
    for (const place of results) {
        const li = document.createElement('li'); const button = document.createElement('button');
        button.type = 'button'; button.textContent = place.name;
        button.addEventListener('click', () => selectPlace(place)); li.append(button); list.append(li);
    }
    document.getElementById('place-count').textContent = `${results.length} places`;
}

async function json(url) {
    const response = await fetch(url, {signal: AbortSignal.timeout(20000)});
    if (!response.ok) throw new Error('Unavailable');
    return response.json();
}

counts(); renderList(); search.addEventListener('input', renderList);
let photoWarning = '';
try {
    placeState = await json(`${window.PORTFOLIO_API_BASE}/travel/places`);
    states = reference.states.filter(f => placeState.regions.US.includes(f.properties.code));
    provinces = reference.provinces.filter(f => placeState.regions.CA.includes(f.properties.code));
    countries = window.TRAVEL_COUNTRIES.filter(f => placeState.regions.countries.includes(f.properties.code));
    places.push(...placeState.data.places);
    places.push(...placeState.cities.filter(c => placeState.data.cityVisits[c.id] === 'visited').map(c => ({...c, kind: 'city', name: `${c.name}, ${c.state}`})));
    counts(); renderList();
} catch (_) { photoWarning = 'Saved places could not be loaded. '; }
try {
    const data = await json(`${window.PORTFOLIO_API_BASE}/travel/photos`);
    photoRows = data.photos;
    const groups = new Map();
    for (const photo of data.photos.filter(p => p.located)) {
        const id = `photo-${photo.latitude.toFixed(5)}-${photo.longitude.toFixed(5)}`;
        if (!groups.has(id)) groups.set(id, {id, kind: 'photo', name: photo.map_location_name || (photo.location_name && photo.location_name !== 'Unknown Location' ? photo.location_name : (photo.title || 'Photo location')), latitude: photo.latitude, longitude: photo.longitude, photos: []});
        groups.get(id).photos.push(photo);
    }
    places.push(...groups.values()); renderList();
    if (selectedPhoto && !places.some(p => p.photos?.some(photo => photo.file_path === selectedPhoto))) {
        photoWarning = 'This photograph does not yet have a confirmed map location. ';
    }
} catch (_) { photoWarning = 'Photo locations could not be loaded. '; }
editor = createEditor(placeState, photoRows);

try {
    const configData = await json(`${window.PORTFOLIO_API_BASE}/travel/config`);
    const [esriConfig, EsriMap, MapView, Graphic, GraphicsLayer, GeoJSONLayer, reactiveUtils, FeatureLayer, Extent] = await $arcgis.import([
        '@arcgis/core/config.js', '@arcgis/core/Map.js', '@arcgis/core/views/MapView.js',
        '@arcgis/core/Graphic.js', '@arcgis/core/layers/GraphicsLayer.js', '@arcgis/core/layers/GeoJSONLayer.js', '@arcgis/core/core/reactiveUtils.js', '@arcgis/core/layers/FeatureLayer.js', '@arcgis/core/geometry/Extent.js'
    ]);
    const worldView = new Extent(worldBounds);
    esriConfig.apiKeys.basemapStyles = configData.apiKey;
    function boundaryLayer(features, name, color, outline) {
        if (!features.length) return new GraphicsLayer({title: name});
        const url = URL.createObjectURL(new Blob([JSON.stringify({type: 'FeatureCollection', features})], {type: 'application/geo+json'}));
        const layer = new GeoJSONLayer({url, title: name, copyright: 'Natural Earth',
            renderer: {type: 'simple', symbol: {type: 'simple-fill', color, outline}},
            popupTemplate: {title: '{name}', content: name}});
        layer.load().finally(() => URL.revokeObjectURL(url)).catch(() => {
            status.textContent = `${name} could not be loaded. Reload to retry.`;
        });
        return layer;
    }
    layers.states = boundaryLayer([...states, ...provinces], 'Stayed at least one night', [75, 151, 114, 0.35], {color: '#387d61', width: 0.7});
    layers.countries = boundaryLayer(countries, 'Country visited', [0, 0, 0, 0], {color: '#ba6c23', width: 1});
    layers.parks = new GraphicsLayer({title: 'National parks and places'});
    layers.photos = new GraphicsLayer({title: 'Photo locations'});
    for (const place of places.filter(p => p.kind === 'park' || p.kind === 'photo')) {
        const graphic = new Graphic({geometry: {type: 'point', longitude: place.longitude, latitude: place.latitude},
            attributes: {placeId: place.id}, symbol: {type: 'simple-marker', size: place.kind === 'photo' ? 12 : 8,
                color: place.kind === 'photo' ? '#865ab1' : '#24745e', outline: {color: '#fff', width: 1.2}}});
        graphics.set(place.id, graphic); (place.kind === 'photo' ? layers.photos : layers.parks).add(graphic);
    }
    layers.cities = new FeatureLayer({title: 'Reviewed cities and other places', objectIdField: 'ObjectID', geometryType: 'point', spatialReference: {wkid: 4326},
        fields: [{name: 'ObjectID', type: 'oid'}, {name: 'placeId', type: 'string'}, {name: 'name', type: 'string'}],
        source: places.filter(p => ['city', 'place'].includes(p.kind)).map((p, i) => new Graphic({
            geometry: {type: 'point', longitude: p.longitude, latitude: p.latitude}, attributes: {ObjectID: i + 1, placeId: p.id, name: p.name}})),
        renderer: {type: 'simple', symbol: {type: 'simple-marker', color: '#2d6ca2', size: 9, outline: {color: 'white', width: 1}}},
        featureReduction: {type: 'cluster', clusterRadius: '55px', clusterMinSize: '22px', clusterMaxSize: '38px', maxScale: 500000,
            labelingInfo: [{labelExpressionInfo: {expression: "Text($feature.cluster_count, '#,###')"}, labelPlacement: 'center-center',
                symbol: {type: 'text', color: 'white', font: {size: 10, weight: 'bold'}}}]}});
    const map = new EsriMap({basemap: {style: {id: 'arcgis/light-gray'}}, layers: Object.values(layers)});
    const draftLayer = new GraphicsLayer({title: 'Point being placed', listMode: 'hide'});
    map.add(draftLayer);
    view = new MapView({container: 'travel-map', map, center: [0, 25], zoom: 1, constraints: {snapToZoom: false}});
    await view.when();
    await Promise.all([map.basemap.loadAll(), layers.states.load(), layers.countries.load()]);
    await view.goTo(worldView, {animate: false});
    await reactiveUtils.whenOnce(() => !view.updating);
    status.textContent = photoWarning + 'Select a marker or choose a place from the list.';
    document.addEventListener('travel-preview-point', event => {
        const point = event.detail;
        draftLayer.removeAll();
        draftLayer.add(new Graphic({geometry: {type: 'point', latitude: point.latitude, longitude: point.longitude},
            symbol: {type: 'simple-marker', style: 'diamond', size: 18, color: '#d87518', outline: {color: 'white', width: 2}}}));
        view.goTo({center: [point.longitude, point.latitude], zoom: 11}).catch(() => {});
    });
    view.on('click', async event => {
        if (editor?.picking && event.mapPoint) {
            draftLayer.removeAll();
            draftLayer.add(new Graphic({geometry: event.mapPoint, symbol: {type: 'simple-marker', style: 'diamond', size: 18, color: '#d87518', outline: {color: 'white', width: 2}}}));
            editor.choose(event.mapPoint); return;
        }
        const result = await view.hitTest(event, {include: [layers.parks, layers.photos, layers.cities]});
        const cluster = result.results.find(r => r.graphic?.isAggregate)?.graphic;
        if (cluster) { await view.goTo({target: cluster.geometry, zoom: view.zoom + 2}); return; }
        const id = result.results.find(r => r.graphic?.attributes?.placeId)?.graphic.attributes.placeId;
        const place = places.find(p => p.id === id); if (place) showDetail(place);
    });
    for (const name of ['states', 'countries', 'parks', 'photos', 'cities']) {
        document.getElementById(`show-${name}`).addEventListener('change', event => { layers[name].visible = event.target.checked; });
    }
    const views = {world: worldView, canada: {center: [-100, 58], zoom: 3}, usa: {center: [-98, 38], zoom: 4}, hawaii: {center: [-157, 20.7], zoom: 6}};
    document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
        view.goTo(views[button.dataset.view]).catch(error => {
            if (error.name !== 'AbortError') status.textContent = 'Could not change the map view. Please try again.';
        });
    }));
    const selected = places.find(p => p.photos?.some(photo => photo.file_path === selectedPhoto));
    if (selected) await selectPlace(selected);
} catch (_) {
    // Do not log Esri request errors: request URLs can contain the browser key.
    status.textContent = photoWarning + 'The map could not load. Check your connection and basemap key configuration, then reload. You can still browse the places list.';
}
