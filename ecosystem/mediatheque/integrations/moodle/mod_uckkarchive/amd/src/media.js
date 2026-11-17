/**
 * Media library interactions for mod_uckkarchive.
 *
 * This module is intentionally UI-only:
 * - loads media lists from declared AJAX services;
 * - renders permission-filtered media cards returned by the server;
 * - submits create/update/delete/version/export actions to server services;
 * - refreshes visible panels, versions, selections, and status messages;
 * - improves accessibility and usability.
 *
 * It must not decide permissions, expose restricted media, authorize downloads,
 * validate content advisories, bypass Moodle capabilities, generate exports, or
 * replace server-side policy checks.
 *
 * @module     mod_uckkarchive/media
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

import Ajax from 'core/ajax';
import Notification from 'core/notification';
import Templates from 'core/templates';
import {getString} from 'core/str';

const COMPONENT = 'uckkarchive';

const DEFAULT_METHODS = {
    getMedia: 'mod_uckkarchive_get_media',
    searchMedia: 'mod_uckkarchive_search_media',
    getMediaItem: 'mod_uckkarchive_get_media_item',
    getMediaCard: 'mod_uckkarchive_get_media_card',
    addMedia: 'mod_uckkarchive_add_media',
    updateMedia: 'mod_uckkarchive_update_media',
    deleteMedia: 'mod_uckkarchive_delete_media',
    getMediaVersions: 'mod_uckkarchive_get_media_versions',
    addMediaVersion: 'mod_uckkarchive_add_media_version',
    exportMedia: 'mod_uckkarchive_export_media',
};

const DEFAULT_TEMPLATES = {
    mediaLibrary: 'mod_uckkarchive/media_library',
    mediaCard: 'mod_uckkarchive/media_card',
    mediaVersionList: 'mod_uckkarchive/media_version_list',
    mediaUpload: 'mod_uckkarchive/media_upload',
};

const SELECTORS = {
    root: '[data-region="uckkarchive-media"]',
    status: '[data-region="uckkarchive-media-status"]',
    warningRegion: '[data-region="uckkarchive-media-warnings"]',
    library: '[data-region="uckkarchive-media-library"]',
    list: '[data-region="uckkarchive-media-list"]',
    card: '[data-region="uckkarchive-media-card"]',
    details: '[data-region="uckkarchive-media-details"]',
    versions: '[data-region="uckkarchive-media-versions"]',
    filters: '[data-region="uckkarchive-media-filters"]',
    pagination: '[data-region="uckkarchive-media-pagination"]',
    selectionSummary: '[data-region="uckkarchive-media-selection-summary"]',

    searchInput: '[data-field="media-search"]',
    mediaTypeInput: '[data-field="media-type"]',
    statusInput: '[data-field="media-status"]',
    visibilityInput: '[data-field="media-visibility"]',
    sourceInput: '[data-field="media-source"]',
    tagInput: '[data-field="media-tag"]',
    contentTagInput: '[data-field="media-content-tag"]',
    collectionInput: '[data-field="media-collection"]',

    selectedMediaInput: '[data-field="selected-media"]',
    mediaCheckbox: '[data-field="media-select"]',

    form: '[data-region="uckkarchive-media-form"]',
    uploadForm: '[data-region="uckkarchive-media-upload-form"]',
    versionForm: '[data-region="uckkarchive-media-version-form"]',
    exportForm: '[data-region="uckkarchive-media-export-form"]',

    actionRefresh: '[data-action="uckkarchive-refresh-media"]',
    actionSearch: '[data-action="uckkarchive-search-media"]',
    actionResetFilters: '[data-action="uckkarchive-reset-media-filters"]',
    actionOpenMedia: '[data-action="uckkarchive-open-media"]',
    actionEditMedia: '[data-action="uckkarchive-edit-media"]',
    actionAddMedia: '[data-action="uckkarchive-add-media"]',
    actionSaveMedia: '[data-action="uckkarchive-save-media"]',
    actionDeleteMedia: '[data-action="uckkarchive-delete-media"]',
    actionSelectMedia: '[data-action="uckkarchive-select-media"]',
    actionSelectAll: '[data-action="uckkarchive-select-all-media"]',
    actionClearSelection: '[data-action="uckkarchive-clear-media-selection"]',
    actionLoadVersions: '[data-action="uckkarchive-load-media-versions"]',
    actionAddVersion: '[data-action="uckkarchive-add-media-version"]',
    actionExportMedia: '[data-action="uckkarchive-export-media"]',
    actionPage: '[data-action="uckkarchive-media-page"]',
};

const DEFAULT_STATE = {
    cmid: 0,
    page: 0,
    perpage: 20,
    sort: 'timemodified',
    direction: 'desc',
    media: [],
    selected: [],
    permissions: {},
    filters: {},
    loaded: false,
    loading: false,
};

const stateStore = new WeakMap();

/**
 * Merge configuration with defaults.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Options.
 * @returns {Object}
 */
const buildConfig = (root, options = {}) => {
    const dataset = root.dataset || {};

    return {
        cmid: Number(options.cmid || dataset.cmid || 0),
        page: Number(options.page || dataset.page || 0),
        perpage: Number(options.perpage || dataset.perpage || DEFAULT_STATE.perpage),
        sort: options.sort || dataset.sort || DEFAULT_STATE.sort,
        direction: options.direction || dataset.direction || DEFAULT_STATE.direction,
        methods: Object.assign({}, DEFAULT_METHODS, options.methods || {}),
        templates: Object.assign({}, DEFAULT_TEMPLATES, options.templates || {}),
        autoload: options.autoload !== undefined ? Boolean(options.autoload) : dataset.autoload !== 'false',
    };
};

/**
 * Get state for root.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Object}
 */
const getState = root => {
    if (!stateStore.has(root)) {
        const config = buildConfig(root);
        stateStore.set(root, Object.assign({}, DEFAULT_STATE, config, {
            filters: collectFilters(root),
            selected: readSelected(root),
        }));
    }

    return stateStore.get(root);
};

/**
 * Set partial state.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} patch State patch.
 * @returns {Object}
 */
const setState = (root, patch) => {
    const state = Object.assign({}, getState(root), patch);
    stateStore.set(root, state);
    return state;
};

/**
 * Return first element inside root.
 *
 * @param {HTMLElement} root Root element.
 * @param {String} selector Selector.
 * @returns {HTMLElement|null}
 */
const find = (root, selector) => root.querySelector(selector);

/**
 * Return all matching elements inside root.
 *
 * @param {HTMLElement} root Root element.
 * @param {String} selector Selector.
 * @returns {HTMLElement[]}
 */
const findAll = (root, selector) => Array.from(root.querySelectorAll(selector));

/**
 * Read value from input/select.
 *
 * @param {HTMLElement|null} element Element.
 * @returns {String}
 */
const valueOf = element => {
    if (!element) {
        return '';
    }

    if (element.type === 'checkbox') {
        return element.checked ? '1' : '';
    }

    return String(element.value || '').trim();
};

/**
 * Read integer data attribute.
 *
 * @param {HTMLElement|null} element Element.
 * @param {String} name Dataset name.
 * @param {Number} fallback Fallback.
 * @returns {Number}
 */
const dataInt = (element, name, fallback = 0) => {
    if (!element || !element.dataset || element.dataset[name] === undefined) {
        return fallback;
    }

    const value = Number(element.dataset[name]);
    return Number.isFinite(value) ? value : fallback;
};

/**
 * Collect filters from DOM.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Object}
 */
const collectFilters = root => ({
    query: valueOf(find(root, SELECTORS.searchInput)),
    mediatype: valueOf(find(root, SELECTORS.mediaTypeInput)),
    status: valueOf(find(root, SELECTORS.statusInput)),
    visibility: valueOf(find(root, SELECTORS.visibilityInput)),
    source: valueOf(find(root, SELECTORS.sourceInput)),
    tag: valueOf(find(root, SELECTORS.tagInput)),
    contenttag: valueOf(find(root, SELECTORS.contentTagInput)),
    collectionid: Number(valueOf(find(root, SELECTORS.collectionInput)) || 0),
});

/**
 * Clear filters in DOM.
 *
 * @param {HTMLElement} root Root element.
 */
const clearFilters = root => {
    [
        SELECTORS.searchInput,
        SELECTORS.mediaTypeInput,
        SELECTORS.statusInput,
        SELECTORS.visibilityInput,
        SELECTORS.sourceInput,
        SELECTORS.tagInput,
        SELECTORS.contentTagInput,
        SELECTORS.collectionInput,
    ].forEach(selector => {
        const element = find(root, selector);
        if (element) {
            element.value = '';
        }
    });
};

/**
 * Read selected media ids from hidden field and checkboxes.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Number[]}
 */
const readSelected = root => {
    const selected = new Set();
    const input = find(root, SELECTORS.selectedMediaInput);

    if (input && input.value) {
        input.value.split(',').forEach(value => {
            const id = Number(value);
            if (id > 0) {
                selected.add(id);
            }
        });
    }

    findAll(root, SELECTORS.mediaCheckbox).forEach(checkbox => {
        if (checkbox.checked) {
            const id = Number(checkbox.value || checkbox.dataset.mediaid || 0);
            if (id > 0) {
                selected.add(id);
            }
        }
    });

    return Array.from(selected);
};

/**
 * Write selected media ids to hidden field and checkboxes.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number[]} selected Selected ids.
 */
const writeSelected = (root, selected) => {
    const unique = Array.from(new Set(selected.map(Number).filter(id => id > 0)));
    const input = find(root, SELECTORS.selectedMediaInput);

    if (input) {
        input.value = unique.join(',');
    }

    findAll(root, SELECTORS.mediaCheckbox).forEach(checkbox => {
        const id = Number(checkbox.value || checkbox.dataset.mediaid || 0);
        checkbox.checked = unique.includes(id);
    });

    setState(root, {selected: unique});
    updateSelectionSummary(root);
};

/**
 * Update selection summary.
 *
 * @param {HTMLElement} root Root element.
 */
const updateSelectionSummary = root => {
    const summary = find(root, SELECTORS.selectionSummary);
    if (!summary) {
        return;
    }

    const selected = getState(root).selected || [];
    summary.textContent = String(selected.length);
    summary.dataset.count = String(selected.length);
};

/**
 * Display status message.
 *
 * @param {HTMLElement} root Root element.
 * @param {String} message Message.
 * @param {String} type Status type.
 */
const showStatus = (root, message, type = 'info') => {
    const status = find(root, SELECTORS.status);
    if (!status) {
        return;
    }

    status.textContent = message;
    status.dataset.status = type;
    status.classList.remove('is-info', 'is-success', 'is-warning', 'is-error');
    status.classList.add(`is-${type}`);
};

/**
 * Display localized status message.
 *
 * @param {HTMLElement} root Root element.
 * @param {String} key String key.
 * @param {String} type Status type.
 * @returns {Promise<void>}
 */
const showStringStatus = (root, key, type = 'info') => {
    return getString(key, COMPONENT)
        .then(message => showStatus(root, message, type))
        .catch(() => showStatus(root, key, type));
};

/**
 * Render a template into a region.
 *
 * @param {String} template Template name.
 * @param {Object} context Template context.
 * @param {HTMLElement} target Target element.
 * @returns {Promise<void>}
 */
const renderInto = (template, context, target) => {
    if (!target) {
        return Promise.resolve();
    }

    return Templates.render(template, context)
        .then(html => Templates.replaceNodeContents(target, html, ''));
};

/**
 * Call one Moodle AJAX method.
 *
 * @param {String} methodname Method name.
 * @param {Object} args Arguments.
 * @returns {Promise<Object>}
 */
const callService = (methodname, args = {}) => {
    return Ajax.call([{
        methodname,
        args,
    }])[0];
};

/**
 * Normalize warnings.
 *
 * @param {Object} response Service response.
 * @returns {Array}
 */
const warningsOf = response => Array.isArray(response.warnings) ? response.warnings : [];

/**
 * Render warnings.
 *
 * @param {HTMLElement} root Root element.
 * @param {Array} warnings Warnings.
 */
const renderWarnings = (root, warnings = []) => {
    const region = find(root, SELECTORS.warningRegion);

    if (!region) {
        return;
    }

    if (!warnings.length) {
        region.innerHTML = '';
        region.hidden = true;
        return;
    }

    const items = warnings.map(warning => {
        const message = String(warning.message || warning.warningcode || '');
        return `<li>${escapeHtml(message)}</li>`;
    }).join('');

    region.innerHTML = `<ul>${items}</ul>`;
    region.hidden = false;
};

/**
 * Escape unsafe text for simple warning rendering.
 *
 * @param {String} value Raw value.
 * @returns {String}
 */
const escapeHtml = value => String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

/**
 * Load media list from server.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} overrides Overrides.
 * @returns {Promise<Object>}
 */
const loadMedia = (root, overrides = {}) => {
    const state = getState(root);

    if (state.loading) {
        return Promise.resolve(state);
    }

    const nextState = setState(root, Object.assign({}, overrides, {
        filters: overrides.filters || collectFilters(root),
        loading: true,
    }));

    showStringStatus(root, 'loading', 'info');

    const args = {
        cmid: nextState.cmid,
        filters: Object.assign({}, nextState.filters),
        page: nextState.page,
        perpage: nextState.perpage,
        sort: nextState.sort,
        direction: nextState.direction,
        include: ['permissions', 'counts'],
    };

    if (args.filters.query) {
        return callService(nextState.methods.searchMedia, args)
            .then(response => handleMediaResponse(root, response))
            .catch(error => handleError(root, error));
    }

    delete args.filters.query;

    return callService(nextState.methods.getMedia, args)
        .then(response => handleMediaResponse(root, response))
        .catch(error => handleError(root, error));
};

/**
 * Handle media list response.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} response Service response.
 * @returns {Object}
 */
const handleMediaResponse = (root, response) => {
    const state = setState(root, {
        media: response.media || response.items || [],
        permissions: response.permissions || {},
        pagination: response.pagination || {},
        loaded: true,
        loading: false,
    });

    renderWarnings(root, warningsOf(response));
    renderMediaList(root, response);
    updateSelectionSummary(root);

    showStringStatus(root, 'mediaupdated', 'success');

    return state;
};

/**
 * Render media list.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} response Service response.
 * @returns {Promise<void>}
 */
const renderMediaList = (root, response) => {
    const state = getState(root);
    const target = find(root, SELECTORS.list) || find(root, SELECTORS.library);

    if (!target) {
        return Promise.resolve();
    }

    const context = {
        media: response.media || response.items || [],
        pagination: response.pagination || {},
        permissions: response.permissions || {},
        hasmedia: Boolean((response.media || response.items || []).length),
        selected: state.selected || [],
    };

    return renderInto(state.templates.mediaLibrary, context, target)
        .then(() => {
            writeSelected(root, state.selected || []);
        });
};

/**
 * Open one media item.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} mediaid Media id.
 * @returns {Promise<Object>}
 */
const openMedia = (root, mediaid) => {
    const state = getState(root);

    if (!mediaid) {
        return Promise.resolve({});
    }

    showStringStatus(root, 'loading', 'info');

    return callService(state.methods.getMediaItem, {
        cmid: state.cmid,
        mediaid,
        include: {
            files: true,
            versions: false,
            relations: false,
            advisories: true,
        },
    })
        .then(response => {
            renderMediaDetails(root, response);
            showStringStatus(root, 'medialoaded', 'success');
            return response;
        })
        .catch(error => handleError(root, error));
};

/**
 * Render media details/card.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} response Response.
 * @returns {Promise<void>}
 */
const renderMediaDetails = (root, response) => {
    const state = getState(root);
    const target = find(root, SELECTORS.details) || find(root, SELECTORS.card);

    if (!target) {
        return Promise.resolve();
    }

    const context = response.record ? response : {
        record: response.media || response.item || response,
        permissions: response.permissions || state.permissions || {},
        warnings: warningsOf(response),
    };

    return renderInto(state.templates.mediaCard, context, target);
};

/**
 * Load media card only.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} mediaid Media id.
 * @returns {Promise<Object>}
 */
const loadMediaCard = (root, mediaid) => {
    const state = getState(root);

    return callService(state.methods.getMediaCard, {
        cmid: state.cmid,
        mediaid,
    })
        .then(response => {
            renderMediaDetails(root, response);
            return response;
        })
        .catch(error => handleError(root, error));
};

/**
 * Save media form through add/update service.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLFormElement} form Form.
 * @returns {Promise<Object>}
 */
const saveMedia = (root, form) => {
    const state = getState(root);
    const data = formToObject(form);
    const mediaid = Number(data.mediaid || data.id || 0);
    const method = mediaid > 0 ? state.methods.updateMedia : state.methods.addMedia;

    data.cmid = Number(data.cmid || state.cmid || 0);

    showStringStatus(root, 'saving', 'info');

    return callService(method, data)
        .then(response => {
            showStringStatus(root, 'saved', 'success');
            renderWarnings(root, warningsOf(response));
            return loadMedia(root).then(() => response);
        })
        .catch(error => handleError(root, error));
};

/**
 * Delete one media record.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} mediaid Media id.
 * @returns {Promise<Object>}
 */
const deleteMedia = (root, mediaid) => {
    const state = getState(root);

    if (!mediaid) {
        return Promise.resolve({});
    }

    return Notification.confirm(
        getString('deletemedia', COMPONENT),
        getString('deletemediaconfirm', COMPONENT),
        getString('delete', 'core'),
        getString('cancel', 'core'),
        () => {
            showStringStatus(root, 'deleting', 'info');

            return callService(state.methods.deleteMedia, {
                cmid: state.cmid,
                mediaid,
            })
                .then(response => {
                    const selected = (getState(root).selected || []).filter(id => id !== mediaid);
                    writeSelected(root, selected);
                    showStringStatus(root, 'deleted', 'success');
                    return loadMedia(root).then(() => response);
                })
                .catch(error => handleError(root, error));
        }
    );
};

/**
 * Load media versions.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} mediaid Media id.
 * @returns {Promise<Object>}
 */
const loadVersions = (root, mediaid) => {
    const state = getState(root);
    const target = find(root, SELECTORS.versions);

    if (!mediaid) {
        return Promise.resolve({});
    }

    return callService(state.methods.getMediaVersions, {
        cmid: state.cmid,
        mediaid,
        include: {
            deleted: false,
            files: true,
            metadata: true,
            hashes: true,
        },
    })
        .then(response => {
            if (target) {
                return renderInto(state.templates.mediaVersionList, response, target)
                    .then(() => response);
            }

            return response;
        })
        .catch(error => handleError(root, error));
};

/**
 * Add media version from form.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLFormElement} form Form.
 * @returns {Promise<Object>}
 */
const addVersion = (root, form) => {
    const state = getState(root);
    const data = formToObject(form);
    data.cmid = Number(data.cmid || state.cmid || 0);

    showStringStatus(root, 'saving', 'info');

    return callService(state.methods.addMediaVersion, data)
        .then(response => {
            showStringStatus(root, 'saved', 'success');

            const mediaid = Number(data.mediaid || response.mediaid || 0);
            if (mediaid > 0) {
                return loadVersions(root, mediaid).then(() => response);
            }

            return response;
        })
        .catch(error => handleError(root, error));
};

/**
 * Export selected media.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLFormElement|null} form Optional export form.
 * @returns {Promise<Object>}
 */
const exportSelected = (root, form = null) => {
    const state = getState(root);
    const selected = readSelected(root);

    if (!selected.length) {
        return showStringStatus(root, 'selectmediafirst', 'warning').then(() => ({}));
    }

    const formData = form ? formToObject(form) : {};
    const options = {
        includeoriginals: truthy(formData.includeoriginals, true),
        includederivatives: truthy(formData.includederivatives, true),
        includethumbnails: truthy(formData.includethumbnails, true),
        includepreviews: truthy(formData.includepreviews, true),
        includecaptions: truthy(formData.includecaptions, true),
        includetranscripts: truthy(formData.includetranscripts, true),
        includeattachments: truthy(formData.includeattachments, true),
        includeversions: truthy(formData.includeversions, true),
        includerelations: truthy(formData.includerelations, true),
        includetags: truthy(formData.includetags, true),
        includeadvisories: truthy(formData.includeadvisories, true),
        includeexternalrefs: truthy(formData.includeexternalrefs, true),
        redactionlevel: formData.redactionlevel || 'standard',
        visibility: formData.visibility || 'private',
    };

    showStringStatus(root, 'exporting', 'info');

    return callService(state.methods.exportMedia, {
        cmid: state.cmid,
        mediaids: selected,
        format: formData.format || 'zip',
        options,
        reason: formData.reason || '',
    })
        .then(response => {
            renderWarnings(root, warningsOf(response));
            showStringStatus(root, 'exportcreated', 'success');
            return response;
        })
        .catch(error => handleError(root, error));
};

/**
 * Convert form values to object.
 *
 * @param {HTMLFormElement} form Form.
 * @returns {Object}
 */
const formToObject = form => {
    const data = {};
    const formData = new FormData(form);

    formData.forEach((value, key) => {
        if (data[key] !== undefined) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }
            data[key].push(value);
            return;
        }

        data[key] = value;
    });

    form.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        if (!checkbox.name) {
            return;
        }

        data[checkbox.name] = checkbox.checked ? 1 : 0;
    });

    return data;
};

/**
 * Convert mixed value to boolean with default.
 *
 * @param {*} value Value.
 * @param {Boolean} fallback Fallback.
 * @returns {Boolean}
 */
const truthy = (value, fallback = false) => {
    if (value === undefined || value === null || value === '') {
        return fallback;
    }

    return value === true || value === 1 || value === '1' || value === 'true' || value === 'on';
};

/**
 * Handle action clicks.
 *
 * @param {HTMLElement} root Root element.
 * @param {MouseEvent} event Click event.
 */
const handleClick = (root, event) => {
    const target = event.target.closest('[data-action]');

    if (!target || !root.contains(target)) {
        return;
    }

    const action = target.dataset.action;
    const mediaid = dataInt(target, 'mediaid', Number(target.value || 0));

    switch (action) {
        case 'uckkarchive-refresh-media':
            event.preventDefault();
            loadMedia(root);
            break;

        case 'uckkarchive-search-media':
            event.preventDefault();
            setState(root, {page: 0, filters: collectFilters(root)});
            loadMedia(root);
            break;

        case 'uckkarchive-reset-media-filters':
            event.preventDefault();
            clearFilters(root);
            setState(root, {page: 0, filters: collectFilters(root)});
            loadMedia(root);
            break;

        case 'uckkarchive-open-media':
            event.preventDefault();
            openMedia(root, mediaid);
            break;

        case 'uckkarchive-edit-media':
            event.preventDefault();
            loadMediaCard(root, mediaid);
            break;

        case 'uckkarchive-delete-media':
            event.preventDefault();
            deleteMedia(root, mediaid);
            break;

        case 'uckkarchive-load-media-versions':
            event.preventDefault();
            loadVersions(root, mediaid);
            break;

        case 'uckkarchive-select-all-media':
            event.preventDefault();
            selectAllVisible(root);
            break;

        case 'uckkarchive-clear-media-selection':
            event.preventDefault();
            writeSelected(root, []);
            break;

        case 'uckkarchive-export-media':
            event.preventDefault();
            exportSelected(root, find(root, SELECTORS.exportForm));
            break;

        case 'uckkarchive-media-page':
            event.preventDefault();
            setState(root, {page: dataInt(target, 'page', 0)});
            loadMedia(root);
            break;

        default:
            break;
    }
};

/**
 * Handle change events.
 *
 * @param {HTMLElement} root Root element.
 * @param {Event} event Change event.
 */
const handleChange = (root, event) => {
    const target = event.target;

    if (target.matches(SELECTORS.mediaCheckbox)) {
        writeSelected(root, readSelected(root));
        return;
    }

    if (target.closest(SELECTORS.filters)) {
        setState(root, {page: 0, filters: collectFilters(root)});
        loadMedia(root);
    }
};

/**
 * Handle submit events.
 *
 * @param {HTMLElement} root Root element.
 * @param {SubmitEvent} event Submit event.
 */
const handleSubmit = (root, event) => {
    const form = event.target;

    if (!(form instanceof HTMLFormElement)) {
        return;
    }

    if (form.matches(SELECTORS.form) || form.matches(SELECTORS.uploadForm)) {
        event.preventDefault();
        saveMedia(root, form);
        return;
    }

    if (form.matches(SELECTORS.versionForm)) {
        event.preventDefault();
        addVersion(root, form);
        return;
    }

    if (form.matches(SELECTORS.exportForm)) {
        event.preventDefault();
        exportSelected(root, form);
    }
};

/**
 * Handle keydown events.
 *
 * @param {HTMLElement} root Root element.
 * @param {KeyboardEvent} event Key event.
 */
const handleKeydown = (root, event) => {
    if (!event.target.matches(SELECTORS.searchInput)) {
        return;
    }

    if (event.key !== 'Enter') {
        return;
    }

    event.preventDefault();
    setState(root, {page: 0, filters: collectFilters(root)});
    loadMedia(root);
};

/**
 * Select all visible media checkboxes.
 *
 * @param {HTMLElement} root Root element.
 */
const selectAllVisible = root => {
    const selected = new Set(getState(root).selected || []);

    findAll(root, SELECTORS.mediaCheckbox).forEach(checkbox => {
        const id = Number(checkbox.value || checkbox.dataset.mediaid || 0);
        if (id > 0) {
            checkbox.checked = true;
            selected.add(id);
        }
    });

    writeSelected(root, Array.from(selected));
};

/**
 * Handle AJAX/service errors.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} error Error.
 * @returns {Object}
 */
const handleError = (root, error) => {
    setState(root, {loading: false});
    showStringStatus(root, 'error', 'error');
    Notification.exception(error);
    return {};
};

/**
 * Bind event listeners once.
 *
 * @param {HTMLElement} root Root element.
 */
const bind = root => {
    if (root.dataset.mediaAmdBound === '1') {
        return;
    }

    root.dataset.mediaAmdBound = '1';

    root.addEventListener('click', event => handleClick(root, event));
    root.addEventListener('change', event => handleChange(root, event));
    root.addEventListener('submit', event => handleSubmit(root, event));
    root.addEventListener('keydown', event => handleKeydown(root, event));
};

/**
 * Initialise one media library root.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Options.
 * @returns {Promise<Object>}
 */
const initRoot = (root, options = {}) => {
    const config = buildConfig(root, options);
    stateStore.set(root, Object.assign({}, DEFAULT_STATE, config, {
        filters: collectFilters(root),
        selected: readSelected(root),
    }));

    bind(root);
    updateSelectionSummary(root);

    if (config.autoload) {
        return loadMedia(root);
    }

    return Promise.resolve(getState(root));
};

/**
 * Initialise media library UI.
 *
 * @param {String|HTMLElement|null} rootOrId Root id, root element, or null for all roots.
 * @param {Object} options Options.
 * @returns {Promise<Array|Object>}
 */
export const init = (rootOrId = null, options = {}) => {
    if (rootOrId instanceof HTMLElement) {
        return initRoot(rootOrId, options);
    }

    if (typeof rootOrId === 'string' && rootOrId !== '') {
        const root = document.getElementById(rootOrId) || document.querySelector(rootOrId);
        return root ? initRoot(root, options) : Promise.resolve({});
    }

    const roots = Array.from(document.querySelectorAll(SELECTORS.root));
    return Promise.all(roots.map(root => initRoot(root, options)));
};

/**
 * Refresh media list for a root.
 *
 * @param {String|HTMLElement} rootOrId Root id or element.
 * @param {Object} overrides State overrides.
 * @returns {Promise<Object>}
 */
export const refresh = (rootOrId, overrides = {}) => {
    const root = rootOrId instanceof HTMLElement ? rootOrId : document.getElementById(rootOrId);

    if (!root) {
        return Promise.resolve({});
    }

    return loadMedia(root, overrides);
};

/**
 * Open one media item by id.
 *
 * @param {String|HTMLElement} rootOrId Root id or element.
 * @param {Number} mediaid Media id.
 * @returns {Promise<Object>}
 */
export const open = (rootOrId, mediaid) => {
    const root = rootOrId instanceof HTMLElement ? rootOrId : document.getElementById(rootOrId);

    if (!root) {
        return Promise.resolve({});
    }

    return openMedia(root, Number(mediaid));
};

/**
 * Load versions for one media item.
 *
 * @param {String|HTMLElement} rootOrId Root id or element.
 * @param {Number} mediaid Media id.
 * @returns {Promise<Object>}
 */
export const versions = (rootOrId, mediaid) => {
    const root = rootOrId instanceof HTMLElement ? rootOrId : document.getElementById(rootOrId);

    if (!root) {
        return Promise.resolve({});
    }

    return loadVersions(root, Number(mediaid));
};

/**
 * Export selected media for one root.
 *
 * @param {String|HTMLElement} rootOrId Root id or element.
 * @returns {Promise<Object>}
 */
export const exportSelectedMedia = rootOrId => {
    const root = rootOrId instanceof HTMLElement ? rootOrId : document.getElementById(rootOrId);

    if (!root) {
        return Promise.resolve({});
    }

    return exportSelected(root, find(root, SELECTORS.exportForm));
};

export default {
    init,
    refresh,
    open,
    versions,
    exportSelectedMedia,
};