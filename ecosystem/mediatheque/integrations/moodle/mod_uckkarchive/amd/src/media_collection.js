/**
 * Media collection interactions for mod_uckkarchive.
 *
 * This module is intentionally UI-only:
 * - loads media collection lists;
 * - loads a selected media collection;
 * - submits create/update collection forms;
 * - adds media to collections;
 * - removes media from collections;
 * - renders permission-filtered server responses.
 *
 * It must not authorize access, override media-level restrictions, duplicate
 * media files, expose restricted records, or replace server-side policy checks.
 *
 * @module     mod_uckkarchive/media_collection
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

import Ajax from 'core/ajax';
import Notification from 'core/notification';
import Templates from 'core/templates';
import {getString} from 'core/str';

const COMPONENT = 'uckkarchive';

const DEFAULT_METHODS = {
    getCollections: 'mod_uckkarchive_get_media_collections',
    getCollection: 'mod_uckkarchive_get_media_collection',
    addCollection: 'mod_uckkarchive_add_media_collection',
    updateCollection: 'mod_uckkarchive_update_media_collection',
    addMediaToCollection: 'mod_uckkarchive_add_media_to_collection',
    removeMediaFromCollection: 'mod_uckkarchive_remove_media_from_collection',
};

const DEFAULT_TEMPLATES = {
    collection: 'mod_uckkarchive/media_collection',
    collectionList: 'mod_uckkarchive/media_collection',
};

const SELECTORS = {
    root: '[data-region="uckkarchive-media-collection"]',
    status: '[data-region="media-collection-status"]',
    list: '[data-region="media-collection-list"]',
    collection: '[data-region="media-collection"]',
    collectionBody: '[data-region="media-collection-body"]',
    createForm: '[data-form="media-collection-create"]',
    updateForm: '[data-form="media-collection-update"]',
    filterForm: '[data-form="media-collection-filter"]',
    addMediaForm: '[data-form="media-collection-add-media"]',
    removeMediaButton: '[data-action="remove-media-from-collection"]',
    refreshButton: '[data-action="refresh-media-collections"]',
    loadButton: '[data-action="load-media-collection"]',
    createButton: '[data-action="create-media-collection"]',
    updateButton: '[data-action="update-media-collection"]',
    addMediaButton: '[data-action="add-media-to-collection"]',
    toggleButton: '[data-action="toggle-media-collection"]',
};

const EVENTS = {
    refreshed: 'mod_uckkarchive:media_collection_refreshed',
    loaded: 'mod_uckkarchive:media_collection_loaded',
    created: 'mod_uckkarchive:media_collection_created',
    updated: 'mod_uckkarchive:media_collection_updated',
    mediaAdded: 'mod_uckkarchive:media_collection_media_added',
    mediaRemoved: 'mod_uckkarchive:media_collection_media_removed',
};

const DEFAULT_FILTERS = {
    query: '',
    status: '',
    visibility: '',
    purpose: '',
    ownerid: 0,
    page: 0,
    perpage: 25,
};

const DEFAULT_METADATA = {
    summary: '',
    audience: '',
    teachingcontext: '',
    rightsnote: '',
    culturalprotocol: false,
    restrictednote: '',
    keywords: [],
};

/**
 * Normalize integer.
 *
 * @param {*} value Raw value.
 * @param {number} fallback Fallback.
 * @returns {number}
 */
const intValue = (value, fallback = 0) => {
    const parsed = parseInt(value, 10);
    return Number.isNaN(parsed) ? fallback : parsed;
};

/**
 * Normalize string.
 *
 * @param {*} value Raw value.
 * @returns {string}
 */
const stringValue = value => {
    if (value === null || value === undefined) {
        return '';
    }

    return String(value).trim();
};

/**
 * Normalize boolean.
 *
 * @param {*} value Raw value.
 * @returns {boolean}
 */
const boolValue = value => {
    if (typeof value === 'boolean') {
        return value;
    }

    if (typeof value === 'number') {
        return value === 1;
    }

    const normalized = stringValue(value).toLowerCase();
    return ['1', 'true', 'yes', 'on'].includes(normalized);
};

/**
 * Return a translated string with a fallback.
 *
 * @param {string} key String key.
 * @param {string} fallback Fallback text.
 * @returns {Promise<string>}
 */
const lang = async(key, fallback) => {
    try {
        return await getString(key, COMPONENT);
    } catch (error) {
        return fallback;
    }
};

/**
 * Dispatch a DOM event.
 *
 * @param {HTMLElement} root Root node.
 * @param {string} name Event name.
 * @param {Object} detail Event detail.
 */
const dispatch = (root, name, detail = {}) => {
    root.dispatchEvent(new CustomEvent(name, {
        bubbles: true,
        detail,
    }));
};

/**
 * Execute one AJAX call.
 *
 * @param {string} methodname External function name.
 * @param {Object} args Arguments.
 * @returns {Promise<Object>}
 */
const call = (methodname, args = {}) => {
    return Ajax.call([{
        methodname,
        args,
    }])[0];
};

/**
 * Find element inside root.
 *
 * @param {HTMLElement} root Root node.
 * @param {string} selector Selector.
 * @returns {HTMLElement|null}
 */
const find = (root, selector) => root.querySelector(selector);

/**
 * Set a status message.
 *
 * @param {HTMLElement} root Root node.
 * @param {string} message Message.
 * @param {string} state State class.
 */
const setStatus = (root, message = '', state = '') => {
    const node = find(root, SELECTORS.status);
    if (!node) {
        return;
    }

    node.textContent = message;
    node.dataset.state = state;
};

/**
 * Disable or enable a form/button during an async operation.
 *
 * @param {HTMLElement|null} node Node.
 * @param {boolean} disabled Disabled state.
 */
const setBusy = (node, disabled) => {
    if (!node) {
        return;
    }

    node.classList.toggle('is-busy', disabled);
    node.setAttribute('aria-busy', disabled ? 'true' : 'false');

    if ('disabled' in node) {
        node.disabled = disabled;
    }

    node.querySelectorAll('button, input, select, textarea').forEach(child => {
        child.disabled = disabled;
    });
};

/**
 * Get cmid from root or Moodle page.
 *
 * @param {HTMLElement} root Root node.
 * @returns {number}
 */
const getCmid = root => {
    const fromRoot = intValue(root.dataset.cmid, 0);
    if (fromRoot > 0) {
        return fromRoot;
    }

    if (typeof M !== 'undefined' && M.cfg && M.cfg.cmid) {
        return intValue(M.cfg.cmid, 0);
    }

    return 0;
};

/**
 * Get configured methods.
 *
 * @param {HTMLElement} root Root node.
 * @returns {Object}
 */
const getMethods = root => {
    let configured = {};

    if (root.dataset.methods) {
        try {
            configured = JSON.parse(root.dataset.methods);
        } catch (error) {
            configured = {};
        }
    }

    return Object.assign({}, DEFAULT_METHODS, configured);
};

/**
 * Get configured templates.
 *
 * @param {HTMLElement} root Root node.
 * @returns {Object}
 */
const getTemplates = root => {
    let configured = {};

    if (root.dataset.templates) {
        try {
            configured = JSON.parse(root.dataset.templates);
        } catch (error) {
            configured = {};
        }
    }

    return Object.assign({}, DEFAULT_TEMPLATES, configured);
};

/**
 * Serialize form to plain object.
 *
 * @param {HTMLFormElement|null} form Form.
 * @returns {Object}
 */
const serializeForm = form => {
    if (!form) {
        return {};
    }

    const data = {};
    const formData = new FormData(form);

    formData.forEach((value, key) => {
        if (key.endsWith('[]')) {
            const cleanKey = key.slice(0, -2);
            if (!Array.isArray(data[cleanKey])) {
                data[cleanKey] = [];
            }
            data[cleanKey].push(value);
            return;
        }

        if (Object.prototype.hasOwnProperty.call(data, key)) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }
            data[key].push(value);
            return;
        }

        data[key] = value;
    });

    return data;
};

/**
 * Normalize metadata payload.
 *
 * @param {Object} raw Raw metadata.
 * @returns {Object}
 */
const normalizeMetadata = raw => {
    const metadata = Object.assign({}, DEFAULT_METADATA, raw || {});

    if (typeof metadata.keywords === 'string') {
        metadata.keywords = metadata.keywords
            .split(',')
            .map(keyword => keyword.trim())
            .filter(keyword => keyword !== '');
    }

    if (!Array.isArray(metadata.keywords)) {
        metadata.keywords = [];
    }

    metadata.summary = stringValue(metadata.summary);
    metadata.audience = stringValue(metadata.audience);
    metadata.teachingcontext = stringValue(metadata.teachingcontext);
    metadata.rightsnote = stringValue(metadata.rightsnote);
    metadata.restrictednote = stringValue(metadata.restrictednote);
    metadata.culturalprotocol = boolValue(metadata.culturalprotocol);

    return metadata;
};

/**
 * Build collection create payload from a form or object.
 *
 * @param {HTMLElement} root Root node.
 * @param {Object} raw Raw values.
 * @returns {Object}
 */
const buildCreatePayload = (root, raw) => {
    const cmid = intValue(raw.cmid, getCmid(root));

    return {
        cmid,
        title: stringValue(raw.title),
        description: stringValue(raw.description),
        purpose: stringValue(raw.purpose),
        visibility: stringValue(raw.visibility || 'course'),
        status: stringValue(raw.status || 'draft'),
        metadata: normalizeMetadata({
            summary: raw.summary,
            audience: raw.audience,
            teachingcontext: raw.teachingcontext,
            rightsnote: raw.rightsnote,
            culturalprotocol: raw.culturalprotocol,
            restrictednote: raw.restrictednote,
            keywords: raw.keywords,
        }),
    };
};

/**
 * Build collection update payload from a form or object.
 *
 * @param {HTMLElement} root Root node.
 * @param {Object} raw Raw values.
 * @returns {Object}
 */
const buildUpdatePayload = (root, raw) => {
    const data = {
        title: stringValue(raw.title),
        description: stringValue(raw.description),
        visibility: stringValue(raw.visibility),
        purpose: stringValue(raw.purpose),
        status: stringValue(raw.status),
        sortorder: intValue(raw.sortorder, 0),
    };

    const metadata = normalizeMetadata({
        summary: raw.summary,
        audience: raw.audience,
        teachingcontext: raw.teachingcontext,
        rightsnote: raw.rightsnote,
        culturalprotocol: raw.culturalprotocol,
        restrictednote: raw.restrictednote,
        keywords: raw.keywords,
    });

    return {
        cmid: intValue(raw.cmid, getCmid(root)),
        collectionid: intValue(raw.collectionid, intValue(raw.id, 0)),
        collectionuuid: stringValue(raw.collectionuuid || raw.uuid),
        data: Object.assign(data, {
            metadatajson: JSON.stringify(metadata),
        }),
    };
};

/**
 * Build collection list filters.
 *
 * @param {HTMLElement} root Root node.
 * @returns {Object}
 */
const buildFilters = root => {
    const form = find(root, SELECTORS.filterForm);
    const raw = serializeForm(form);

    return Object.assign({}, DEFAULT_FILTERS, {
        query: stringValue(raw.query),
        status: stringValue(raw.status),
        visibility: stringValue(raw.visibility),
        purpose: stringValue(raw.purpose),
        ownerid: intValue(raw.ownerid, 0),
        page: intValue(raw.page, 0),
        perpage: intValue(raw.perpage, intValue(root.dataset.perpage, DEFAULT_FILTERS.perpage)),
    });
};

/**
 * Render a template into a container.
 *
 * @param {string} template Template name.
 * @param {Object} context Template context.
 * @param {HTMLElement|null} container Target container.
 * @returns {Promise<string>}
 */
const renderInto = async(template, context, container) => {
    const html = await Templates.render(template, context);

    if (container) {
        Templates.replaceNodeContents(container, html, '');
    }

    return html;
};

/**
 * Refresh collection list.
 *
 * @param {HTMLElement} root Root node.
 * @param {Object} overrides Filter overrides.
 * @returns {Promise<Object>}
 */
const refreshCollections = async(root, overrides = {}) => {
    const methods = getMethods(root);
    const templates = getTemplates(root);
    const cmid = getCmid(root);
    const filters = Object.assign({}, buildFilters(root), overrides);

    setStatus(root, await lang('mediacollection:refreshing', 'Refreshing media collections...'), 'loading');

    try {
        const response = await call(methods.getCollections, {
            cmid,
            filters,
            page: intValue(filters.page, 0),
            perpage: intValue(filters.perpage, DEFAULT_FILTERS.perpage),
        });

        const container = find(root, SELECTORS.list);
        if (container) {
            await renderInto(templates.collectionList, response, container);
        }

        setStatus(root, await lang('mediacollection:refreshed', 'Media collections refreshed.'), 'success');
        dispatch(root, EVENTS.refreshed, {response});

        return response;
    } catch (error) {
        setStatus(root, await lang('mediacollection:refreshfailed', 'Could not refresh media collections.'), 'error');
        Notification.exception(error);
        throw error;
    }
};

/**
 * Load a single collection.
 *
 * @param {HTMLElement} root Root node.
 * @param {number} collectionid Collection id.
 * @param {string} collectionuuid Collection UUID.
 * @returns {Promise<Object>}
 */
const loadCollection = async(root, collectionid = 0, collectionuuid = '') => {
    const methods = getMethods(root);
    const templates = getTemplates(root);
    const cmid = getCmid(root);

    setStatus(root, await lang('mediacollection:loading', 'Loading media collection...'), 'loading');

    try {
        const response = await call(methods.getCollection, {
            cmid,
            collectionid: intValue(collectionid, 0),
            collectionuuid: stringValue(collectionuuid),
            includeitems: true,
            includemedia: true,
            includepermissions: true,
        });

        const container = find(root, SELECTORS.collection) || find(root, SELECTORS.collectionBody);
        if (container) {
            await renderInto(templates.collection, response, container);
        }

        root.dataset.collectionid = String(response.collectionid || collectionid || '');
        root.dataset.collectionuuid = String(response.collectionuuid || collectionuuid || '');

        setStatus(root, await lang('mediacollection:loaded', 'Media collection loaded.'), 'success');
        dispatch(root, EVENTS.loaded, {response});

        return response;
    } catch (error) {
        setStatus(root, await lang('mediacollection:loadfailed', 'Could not load media collection.'), 'error');
        Notification.exception(error);
        throw error;
    }
};

/**
 * Create a media collection.
 *
 * @param {HTMLElement} root Root node.
 * @param {HTMLFormElement|null} form Form.
 * @returns {Promise<Object>}
 */
const createCollection = async(root, form = null) => {
    const methods = getMethods(root);
    const raw = serializeForm(form || find(root, SELECTORS.createForm));
    const payload = buildCreatePayload(root, raw);

    if (!payload.title) {
        Notification.alert(
            await lang('error', 'Error'),
            await lang('mediacollection:titlerequired', 'A collection title is required.'),
            await lang('ok', 'OK')
        );
        return {};
    }

    setBusy(form, true);
    setStatus(root, await lang('mediacollection:creating', 'Creating media collection...'), 'loading');

    try {
        const response = await call(methods.addCollection, payload);

        setStatus(root, await lang('mediacollection:created', 'Media collection created.'), 'success');
        dispatch(root, EVENTS.created, {response});

        if (form) {
            form.reset();
        }

        await refreshCollections(root);

        if (response.collectionid) {
            await loadCollection(root, response.collectionid, response.collectionuuid || '');
        }

        return response;
    } catch (error) {
        setStatus(root, await lang('mediacollection:createfailed', 'Could not create media collection.'), 'error');
        Notification.exception(error);
        throw error;
    } finally {
        setBusy(form, false);
    }
};

/**
 * Update a media collection.
 *
 * @param {HTMLElement} root Root node.
 * @param {HTMLFormElement|null} form Form.
 * @returns {Promise<Object>}
 */
const updateCollection = async(root, form = null) => {
    const methods = getMethods(root);
    const raw = serializeForm(form || find(root, SELECTORS.updateForm));
    const payload = buildUpdatePayload(root, raw);

    if (!payload.collectionid && !payload.collectionuuid) {
        payload.collectionid = intValue(root.dataset.collectionid, 0);
        payload.collectionuuid = stringValue(root.dataset.collectionuuid);
    }

    if (!payload.collectionid && !payload.collectionuuid) {
        Notification.alert(
            await lang('error', 'Error'),
            await lang('mediacollection:missingcollection', 'A collection id or UUID is required.'),
            await lang('ok', 'OK')
        );
        return {};
    }

    setBusy(form, true);
    setStatus(root, await lang('mediacollection:updating', 'Updating media collection...'), 'loading');

    try {
        const response = await call(methods.updateCollection, payload);

        setStatus(root, await lang('mediacollection:updated', 'Media collection updated.'), 'success');
        dispatch(root, EVENTS.updated, {response});

        await refreshCollections(root);
        await loadCollection(root, payload.collectionid, payload.collectionuuid);

        return response;
    } catch (error) {
        setStatus(root, await lang('mediacollection:updatefailed', 'Could not update media collection.'), 'error');
        Notification.exception(error);
        throw error;
    } finally {
        setBusy(form, false);
    }
};

/**
 * Add a media object to a collection.
 *
 * @param {HTMLElement} root Root node.
 * @param {HTMLFormElement|null} form Form.
 * @param {Object} overrides Overrides.
 * @returns {Promise<Object>}
 */
const addMediaToCollection = async(root, form = null, overrides = {}) => {
    const methods = getMethods(root);
    const raw = Object.assign({}, serializeForm(form || find(root, SELECTORS.addMediaForm)), overrides);

    const collectionid = intValue(raw.collectionid, intValue(root.dataset.collectionid, 0));
    const mediaid = intValue(raw.mediaid, 0);

    if (!collectionid || !mediaid) {
        Notification.alert(
            await lang('error', 'Error'),
            await lang('mediacollection:missingmediaorcollection', 'A collection and media item are required.'),
            await lang('ok', 'OK')
        );
        return {};
    }

    const payload = {
        cmid: intValue(raw.cmid, getCmid(root)),
        collectionid,
        mediaid,
        sortorder: intValue(raw.sortorder, -1),
        metadata: {
            role: stringValue(raw.role),
            note: stringValue(raw.note),
            purpose: stringValue(raw.purpose),
        },
    };

    setBusy(form, true);
    setStatus(root, await lang('mediacollection:addingmedia', 'Adding media to collection...'), 'loading');

    try {
        const response = await call(methods.addMediaToCollection, payload);

        setStatus(root, await lang('mediacollection:mediaadded', 'Media added to collection.'), 'success');
        dispatch(root, EVENTS.mediaAdded, {response});

        await loadCollection(root, collectionid, root.dataset.collectionuuid || '');

        if (form) {
            form.reset();
        }

        return response;
    } catch (error) {
        setStatus(root, await lang('mediacollection:addmediafailed', 'Could not add media to collection.'), 'error');
        Notification.exception(error);
        throw error;
    } finally {
        setBusy(form, false);
    }
};

/**
 * Remove a media object from a collection.
 *
 * @param {HTMLElement} root Root node.
 * @param {number} collectionid Collection id.
 * @param {number} mediaid Media id.
 * @param {boolean} strict Strict mode.
 * @returns {Promise<Object>}
 */
const removeMediaFromCollection = async(root, collectionid = 0, mediaid = 0, strict = false) => {
    const methods = getMethods(root);

    collectionid = intValue(collectionid, intValue(root.dataset.collectionid, 0));
    mediaid = intValue(mediaid, 0);

    if (!collectionid || !mediaid) {
        Notification.alert(
            await lang('error', 'Error'),
            await lang('mediacollection:missingmediaorcollection', 'A collection and media item are required.'),
            await lang('ok', 'OK')
        );
        return {};
    }

    setStatus(root, await lang('mediacollection:removingmedia', 'Removing media from collection...'), 'loading');

    try {
        const response = await call(methods.removeMediaFromCollection, {
            cmid: getCmid(root),
            collectionid,
            collectionuuid: stringValue(root.dataset.collectionuuid),
            mediaid,
            mediauuid: '',
            strict: boolValue(strict),
        });

        setStatus(root, await lang('mediacollection:mediaremoved', 'Media removed from collection.'), 'success');
        dispatch(root, EVENTS.mediaRemoved, {response});

        await loadCollection(root, collectionid, root.dataset.collectionuuid || '');

        return response;
    } catch (error) {
        setStatus(root, await lang('mediacollection:removemediafailed', 'Could not remove media from collection.'), 'error');
        Notification.exception(error);
        throw error;
    }
};

/**
 * Toggle a collection panel.
 *
 * @param {HTMLElement} root Root node.
 * @param {HTMLElement} button Toggle button.
 */
const toggleCollection = (root, button) => {
    const targetId = button.getAttribute('aria-controls') || button.dataset.target;
    if (!targetId) {
        return;
    }

    const target = root.querySelector(`#${CSS.escape(targetId)}`);
    if (!target) {
        return;
    }

    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    target.hidden = expanded;
};

/**
 * Bind root events.
 *
 * @param {HTMLElement} root Root node.
 */
const bindEvents = root => {
    root.addEventListener('submit', event => {
        const form = event.target;

        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        if (form.matches(SELECTORS.createForm)) {
            event.preventDefault();
            createCollection(root, form);
            return;
        }

        if (form.matches(SELECTORS.updateForm)) {
            event.preventDefault();
            updateCollection(root, form);
            return;
        }

        if (form.matches(SELECTORS.filterForm)) {
            event.preventDefault();
            refreshCollections(root);
            return;
        }

        if (form.matches(SELECTORS.addMediaForm)) {
            event.preventDefault();
            addMediaToCollection(root, form);
        }
    });

    root.addEventListener('click', event => {
        const target = event.target;
        const action = target.closest('[data-action]');

        if (!action || !root.contains(action)) {
            return;
        }

        if (action.matches(SELECTORS.refreshButton)) {
            event.preventDefault();
            refreshCollections(root);
            return;
        }

        if (action.matches(SELECTORS.loadButton)) {
            event.preventDefault();
            loadCollection(
                root,
                intValue(action.dataset.collectionid, 0),
                stringValue(action.dataset.collectionuuid)
            );
            return;
        }

        if (action.matches(SELECTORS.createButton)) {
            event.preventDefault();
            createCollection(root, find(root, SELECTORS.createForm));
            return;
        }

        if (action.matches(SELECTORS.updateButton)) {
            event.preventDefault();
            updateCollection(root, find(root, SELECTORS.updateForm));
            return;
        }

        if (action.matches(SELECTORS.addMediaButton)) {
            event.preventDefault();
            addMediaToCollection(root, find(root, SELECTORS.addMediaForm), {
                collectionid: action.dataset.collectionid,
                mediaid: action.dataset.mediaid,
                sortorder: action.dataset.sortorder,
                role: action.dataset.role,
                note: action.dataset.note,
                purpose: action.dataset.purpose,
            });
            return;
        }

        if (action.matches(SELECTORS.removeMediaButton)) {
            event.preventDefault();
            removeMediaFromCollection(
                root,
                intValue(action.dataset.collectionid, 0),
                intValue(action.dataset.mediaid, 0),
                boolValue(action.dataset.strict)
            );
            return;
        }

        if (action.matches(SELECTORS.toggleButton)) {
            event.preventDefault();
            toggleCollection(root, action);
        }
    });
};

/**
 * Initialize one root.
 *
 * @param {HTMLElement} root Root node.
 * @param {Object} options Options.
 */
const initRoot = (root, options = {}) => {
    if (!root || root.dataset.mediaCollectionInit === '1') {
        return;
    }

    root.dataset.mediaCollectionInit = '1';

    if (options.cmid) {
        root.dataset.cmid = String(options.cmid);
    }

    if (options.methods) {
        root.dataset.methods = JSON.stringify(Object.assign({}, getMethods(root), options.methods));
    }

    if (options.templates) {
        root.dataset.templates = JSON.stringify(Object.assign({}, getTemplates(root), options.templates));
    }

    bindEvents(root);

    if (boolValue(root.dataset.autoload)) {
        refreshCollections(root);
    }

    const initialCollectionId = intValue(root.dataset.collectionid, 0);
    const initialCollectionUuid = stringValue(root.dataset.collectionuuid);

    if (initialCollectionId > 0 || initialCollectionUuid !== '') {
        loadCollection(root, initialCollectionId, initialCollectionUuid);
    }
};

/**
 * Initialize media collection UI.
 *
 * @param {string|HTMLElement} rootSelector Root selector or element.
 * @param {Object} options Init options.
 */
export const init = (rootSelector = SELECTORS.root, options = {}) => {
    if (typeof rootSelector === 'string') {
        document.querySelectorAll(rootSelector).forEach(root => initRoot(root, options));
        return;
    }

    initRoot(rootSelector, options);
};

/**
 * Public API.
 */
export default {
    init,
    refreshCollections,
    loadCollection,
    createCollection,
    updateCollection,
    addMediaToCollection,
    removeMediaFromCollection,
};