/**
 * Content advisory interactions for mod_uckkarchive.
 *
 * This module is intentionally UI-only:
 * - loads permission-filtered content advisory markers;
 * - refreshes advisory panels;
 * - submits marker create/update/delete/review requests to Moodle services;
 * - updates advisory badges, locator previews, and reviewer UI;
 * - displays accessible status messages.
 *
 * It must not approve content advisories authoritatively, decide cultural
 * protocol access, expose restricted metadata, infer hidden permissions, or
 * replace server-side capability checks.
 *
 * @module     mod_uckkarchive/content_advisory
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

import Ajax from 'core/ajax';
import Notification from 'core/notification';
import Templates from 'core/templates';
import {getString} from 'core/str';

const COMPONENT = 'uckkarchive';

const DEFAULT_METHODS = {
    getContentMarkers: 'mod_uckkarchive_get_content_markers',
    getContentTags: 'mod_uckkarchive_get_content_tags',
    getContentTagSets: 'mod_uckkarchive_get_content_tag_sets',
    addContentMarker: 'mod_uckkarchive_add_content_marker',
    updateContentMarker: 'mod_uckkarchive_update_content_marker',
    deleteContentMarker: 'mod_uckkarchive_delete_content_marker',
    reviewContentMarker: 'mod_uckkarchive_review_content_marker',
};

const SELECTORS = {
    root: '[data-region="uckkarchive-content-advisory"]',
    status: '[data-region="uckkarchive-content-advisory-status"]',
    panel: '[data-region="uckkarchive-content-advisory-panel"]',
    list: '[data-region="uckkarchive-content-marker-list"]',
    marker: '[data-region="uckkarchive-content-marker"]',
    markerCount: '[data-region="uckkarchive-content-marker-count"]',

    createForm: '[data-region="uckkarchive-content-marker-create-form"]',
    updateForm: '[data-region="uckkarchive-content-marker-update-form"]',
    reviewForm: '[data-region="uckkarchive-content-review-form"]',
    filterForm: '[data-region="uckkarchive-content-marker-filter-form"]',

    refreshButton: '[data-action="refresh-content-markers"]',
    openCreateButton: '[data-action="open-content-marker-create"]',
    closeCreateButton: '[data-action="close-content-marker-create"]',
    editButton: '[data-action="edit-content-marker"]',
    cancelEditButton: '[data-action="cancel-content-marker-edit"]',
    deleteButton: '[data-action="delete-content-marker"]',
    reviewButton: '[data-action="review-content-marker"]',
    cancelReviewButton: '[data-action="cancel-content-marker-review"]',

    targetType: '[name="targettype"]',
    targetId: '[name="targetid"]',
    tagKey: '[name="tagkey"]',
    tagSetKey: '[name="tagsetkey"]',
    locatorType: '[name="locatortype"]',
    locatorStart: '[name="locatorstart"]',
    locatorEnd: '[name="locatorend"]',
    severity: '[name="severity"]',
    audienceSuitability: '[name="audiencesuitability"]',
    reviewState: '[name="reviewstate"]',
    culturalProtocol: '[name="culturalprotocol"]',
    restricted: '[name="restricted"]',
    rationale: '[name="rationale"]',
    note: '[name="note"]',

    locatorPreview: '[data-region="uckkarchive-locator-preview"]',
    advisoryBadgePreview: '[data-region="uckkarchive-advisory-badge-preview"]',

    filterTag: '[name="filtertag"]',
    filterTargetType: '[name="filtertargettype"]',
    filterReviewState: '[name="filterreviewstate"]',
    filterSeverity: '[name="filterseverity"]',
    filterAudienceSuitability: '[name="filteraudiencesuitability"]',
};

const TEMPLATES = {
    panel: 'mod_uckkarchive/content_advisory_panel',
};

const STATE = new WeakMap();

const DEFAULT_STATE = {
    cmid: 0,
    targettype: '',
    targetid: 0,
    markers: [],
    tags: [],
    tagsets: [],
    permissions: {},
    methods: DEFAULT_METHODS,
    template: TEMPLATES.panel,
    isLoading: false,
};

/**
 * Return root element.
 *
 * @param {string|HTMLElement|null} root Root selector or element.
 * @returns {HTMLElement|null}
 */
const getRoot = root => {
    if (root instanceof HTMLElement) {
        return root;
    }

    if (typeof root === 'string' && root.length > 0) {
        return document.querySelector(root);
    }

    return document.querySelector(SELECTORS.root);
};

/**
 * Merge root dataset into state.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Options.
 * @returns {Object}
 */
const buildState = (root, options = {}) => {
    const dataset = root.dataset || {};

    return {
        ...DEFAULT_STATE,
        ...options,
        cmid: intValue(options.cmid ?? dataset.cmid),
        targettype: textValue(options.targettype ?? dataset.targettype),
        targetid: intValue(options.targetid ?? dataset.targetid),
        methods: {
            ...DEFAULT_METHODS,
            ...(options.methods || {}),
        },
        template: options.template || dataset.template || TEMPLATES.panel,
    };
};

/**
 * Return component state for root.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Object}
 */
const getState = root => STATE.get(root) || buildState(root);

/**
 * Save state.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} state State.
 */
const setState = (root, state) => {
    STATE.set(root, state);
};

/**
 * Convert value to integer.
 *
 * @param {*} value Value.
 * @returns {Number}
 */
const intValue = value => {
    const parsed = parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : 0;
};

/**
 * Convert value to safe string.
 *
 * @param {*} value Value.
 * @returns {String}
 */
const textValue = value => {
    if (value === null || typeof value === 'undefined') {
        return '';
    }

    return String(value).trim();
};

/**
 * Convert form value to boolean.
 *
 * @param {*} value Value.
 * @returns {Boolean}
 */
const boolValue = value => {
    if (typeof value === 'boolean') {
        return value;
    }

    if (typeof value === 'number') {
        return value === 1;
    }

    const normalised = textValue(value).toLowerCase();

    return ['1', 'true', 'yes', 'on'].includes(normalised);
};

/**
 * Get a translatable string, with fallback.
 *
 * @param {String} key String key.
 * @param {String} fallback Fallback text.
 * @returns {Promise<String>}
 */
const stringOrFallback = async(key, fallback) => {
    try {
        return await getString(key, COMPONENT);
    } catch (error) {
        return fallback;
    }
};

/**
 * Display accessible status.
 *
 * @param {HTMLElement} root Root element.
 * @param {String} message Message.
 * @param {String} type Status type.
 */
const setStatus = (root, message, type = 'info') => {
    const status = root.querySelector(SELECTORS.status);
    if (!status) {
        return;
    }

    status.textContent = message;
    status.classList.remove('alert-info', 'alert-success', 'alert-warning', 'alert-danger');
    status.classList.add(`alert-${type}`);
    status.removeAttribute('hidden');
};

/**
 * Clear accessible status.
 *
 * @param {HTMLElement} root Root element.
 */
const clearStatus = root => {
    const status = root.querySelector(SELECTORS.status);
    if (!status) {
        return;
    }

    status.textContent = '';
    status.setAttribute('hidden', 'hidden');
};

/**
 * Call Moodle external service.
 *
 * @param {String} methodname Method name.
 * @param {Object} args Arguments.
 * @returns {Promise<Object>}
 */
const callService = async(methodname, args) => {
    const responses = await Ajax.call([{
        methodname,
        args,
    }]);

    return responses[0];
};

/**
 * Handle AJAX/service errors.
 *
 * @param {HTMLElement} root Root element.
 * @param {Error|Object} error Error.
 */
const handleError = async(root, error) => {
    const message = await stringOrFallback('contentadvisoryerror', 'Content advisory action failed.');

    setStatus(root, message, 'danger');
    Notification.exception(error);
};

/**
 * Serialize a form into a plain object.
 *
 * @param {HTMLFormElement} form Form.
 * @returns {Object}
 */
const serializeForm = form => {
    const data = {};
    const formData = new FormData(form);

    for (const [key, value] of formData.entries()) {
        if (Object.prototype.hasOwnProperty.call(data, key)) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }

            data[key].push(value);
            continue;
        }

        data[key] = value;
    }

    form.querySelectorAll('input[type="checkbox"]').forEach(input => {
        data[input.name] = input.checked;
    });

    return data;
};

/**
 * Build marker payload from form data and root defaults.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} raw Raw data.
 * @returns {Object}
 */
const buildMarkerPayload = (root, raw) => {
    const state = getState(root);

    return {
        cmid: intValue(raw.cmid || state.cmid),
        markerid: intValue(raw.markerid || raw.id),
        targettype: textValue(raw.targettype || state.targettype),
        targetid: intValue(raw.targetid || state.targetid),
        tagkey: textValue(raw.tagkey),
        tagsetkey: textValue(raw.tagsetkey),
        locatortype: textValue(raw.locatortype),
        locatorstart: textValue(raw.locatorstart),
        locatorend: textValue(raw.locatorend),
        severity: textValue(raw.severity),
        audiencesuitability: textValue(raw.audiencesuitability),
        reviewstate: textValue(raw.reviewstate),
        culturalprotocol: boolValue(raw.culturalprotocol),
        restricted: boolValue(raw.restricted),
        rationale: textValue(raw.rationale),
        note: textValue(raw.note),
        metadata: textValue(raw.metadata || '{}'),
    };
};

/**
 * Build marker filter payload.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Object}
 */
const buildFilters = root => {
    const state = getState(root);
    const filterForm = root.querySelector(SELECTORS.filterForm);
    const raw = filterForm ? serializeForm(filterForm) : {};

    return {
        targettype: textValue(raw.filtertargettype || state.targettype),
        targetid: intValue(raw.targetid || state.targetid),
        tagkey: textValue(raw.filtertag),
        reviewstate: textValue(raw.filterreviewstate),
        severity: textValue(raw.filterseverity),
        audiencesuitability: textValue(raw.filteraudiencesuitability),
    };
};

/**
 * Load advisory markers from the server.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Promise<Object>}
 */
const loadMarkers = async root => {
    const state = getState(root);
    const response = await callService(state.methods.getContentMarkers, {
        cmid: state.cmid,
        filters: buildFilters(root),
    });

    state.markers = response.markers || response.contentmarkers || [];
    state.permissions = response.permissions || {};
    setState(root, state);

    return response;
};

/**
 * Load available advisory tags.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Promise<Object>}
 */
const loadTags = async root => {
    const state = getState(root);

    try {
        const response = await callService(state.methods.getContentTags, {
            cmid: state.cmid,
        });

        state.tags = response.tags || [];
        setState(root, state);

        return response;
    } catch (error) {
        return {tags: [], warnings: []};
    }
};

/**
 * Load available advisory tag sets.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Promise<Object>}
 */
const loadTagSets = async root => {
    const state = getState(root);

    try {
        const response = await callService(state.methods.getContentTagSets, {
            cmid: state.cmid,
        });

        state.tagsets = response.tagsets || response.contenttagsets || [];
        setState(root, state);

        return response;
    } catch (error) {
        return {tagsets: [], warnings: []};
    }
};

/**
 * Render the advisory panel.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} response Service response.
 * @returns {Promise<void>}
 */
const renderPanel = async(root, response) => {
    const state = getState(root);
    const panel = root.querySelector(SELECTORS.panel) || root.querySelector(SELECTORS.list);

    if (!panel) {
        updateMarkerCount(root, state.markers.length);
        return;
    }

    const context = {
        ...(response || {}),
        markers: state.markers,
        contentmarkers: state.markers,
        tags: state.tags,
        tagsets: state.tagsets,
        permissions: state.permissions,
        hasmarkers: state.markers.length > 0,
        markercount: state.markers.length,
        cmid: state.cmid,
        targettype: state.targettype,
        targetid: state.targetid,
    };

    try {
        const html = await Templates.render(state.template, context);
        Templates.replaceNodeContents(panel, html, '');
    } catch (error) {
        renderFallbackList(panel, state.markers);
    }

    updateMarkerCount(root, state.markers.length);
};

/**
 * Render simple fallback marker list.
 *
 * @param {HTMLElement} target Target element.
 * @param {Array} markers Marker records.
 */
const renderFallbackList = (target, markers) => {
    if (!target) {
        return;
    }

    target.innerHTML = '';

    if (!markers.length) {
        const empty = document.createElement('div');
        empty.className = 'alert alert-info';
        empty.setAttribute('role', 'status');
        empty.textContent = 'No content advisories.';
        target.appendChild(empty);
        return;
    }

    const list = document.createElement('ul');
    list.className = 'uckkarchive-content-marker-list';

    markers.forEach(marker => {
        const item = document.createElement('li');
        item.className = 'uckkarchive-content-marker-list__item';
        item.dataset.markerid = marker.id || marker.markerid || '';

        const label = document.createElement('span');
        label.className = 'badge badge-info uckkarchive-content-marker-list__badge';
        label.textContent = marker.taglabel || marker.tagkey || marker.tag || 'advisory';

        const details = document.createElement('span');
        details.className = 'uckkarchive-content-marker-list__details';
        details.textContent = [
            marker.severity || '',
            marker.audiencesuitability || marker.audience_suitability || '',
            marker.reviewstate || '',
        ].filter(Boolean).join(' · ');

        item.appendChild(label);
        item.appendChild(document.createTextNode(' '));
        item.appendChild(details);
        list.appendChild(item);
    });

    target.appendChild(list);
};

/**
 * Update marker count.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} count Count.
 */
const updateMarkerCount = (root, count) => {
    const markerCount = root.querySelector(SELECTORS.markerCount);
    if (markerCount) {
        markerCount.textContent = String(count);
    }
};

/**
 * Refresh marker panel.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Promise<void>}
 */
const refresh = async root => {
    const state = getState(root);

    if (state.isLoading) {
        return;
    }

    state.isLoading = true;
    setState(root, state);

    const loading = await stringOrFallback('loading', 'Loading…');
    setStatus(root, loading, 'info');

    try {
        await Promise.all([
            loadTags(root),
            loadTagSets(root),
        ]);

        const response = await loadMarkers(root);
        await renderPanel(root, response);

        clearStatus(root);
    } catch (error) {
        await handleError(root, error);
    } finally {
        const updated = getState(root);
        updated.isLoading = false;
        setState(root, updated);
    }
};

/**
 * Submit marker creation.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLFormElement} form Form.
 * @returns {Promise<void>}
 */
const submitCreate = async(root, form) => {
    const state = getState(root);
    const payload = buildMarkerPayload(root, serializeForm(form));

    try {
        await callService(state.methods.addContentMarker, payload);

        const message = await stringOrFallback('contentmarkercreated', 'Content marker created.');
        setStatus(root, message, 'success');

        form.reset();
        closeCreateForm(root);
        await refresh(root);
    } catch (error) {
        await handleError(root, error);
    }
};

/**
 * Submit marker update.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLFormElement} form Form.
 * @returns {Promise<void>}
 */
const submitUpdate = async(root, form) => {
    const state = getState(root);
    const payload = buildMarkerPayload(root, serializeForm(form));

    if (!payload.markerid) {
        return;
    }

    try {
        await callService(state.methods.updateContentMarker, payload);

        const message = await stringOrFallback('contentmarkerupdated', 'Content marker updated.');
        setStatus(root, message, 'success');

        closeEditForm(root, payload.markerid);
        await refresh(root);
    } catch (error) {
        await handleError(root, error);
    }
};

/**
 * Submit content marker review.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLFormElement} form Form.
 * @returns {Promise<void>}
 */
const submitReview = async(root, form) => {
    const state = getState(root);
    const raw = serializeForm(form);
    const markerid = intValue(raw.markerid || raw.id);

    if (!markerid) {
        return;
    }

    const payload = {
        cmid: intValue(raw.cmid || state.cmid),
        markerid,
        reviewstate: textValue(raw.reviewstate),
        severity: textValue(raw.severity),
        audiencesuitability: textValue(raw.audiencesuitability),
        rationale: textValue(raw.rationale),
        reviewnote: textValue(raw.reviewnote || raw.note),
        culturalprotocol: boolValue(raw.culturalprotocol),
        restricted: boolValue(raw.restricted),
        metadata: textValue(raw.metadata || '{}'),
    };

    try {
        await callService(state.methods.reviewContentMarker, payload);

        const message = await stringOrFallback('contentmarkerreviewed', 'Content marker reviewed.');
        setStatus(root, message, 'success');

        closeReviewForm(root, markerid);
        await refresh(root);
    } catch (error) {
        await handleError(root, error);
    }
};

/**
 * Delete marker after user confirmation.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} markerid Marker id.
 * @returns {Promise<void>}
 */
const deleteMarker = async(root, markerid) => {
    if (!markerid) {
        return;
    }

    const confirmation = await stringOrFallback(
        'confirmdeletecontentmarker',
        'Delete this content marker?'
    );

    let confirmed = false;

    try {
        confirmed = await Notification.confirm(
            confirmation,
            '',
            await stringOrFallback('delete', 'Delete'),
            await stringOrFallback('cancel', 'Cancel')
        );
    } catch (error) {
        confirmed = window.confirm(confirmation);
    }

    if (!confirmed) {
        return;
    }

    const state = getState(root);

    try {
        await callService(state.methods.deleteContentMarker, {
            cmid: state.cmid,
            markerid,
        });

        const message = await stringOrFallback('contentmarkerdeleted', 'Content marker deleted.');
        setStatus(root, message, 'success');

        await refresh(root);
    } catch (error) {
        await handleError(root, error);
    }
};

/**
 * Open create form.
 *
 * @param {HTMLElement} root Root element.
 */
const openCreateForm = root => {
    const form = root.querySelector(SELECTORS.createForm);
    if (!form) {
        return;
    }

    form.removeAttribute('hidden');

    const first = form.querySelector('input, select, textarea, button');
    if (first) {
        first.focus();
    }
};

/**
 * Close create form.
 *
 * @param {HTMLElement} root Root element.
 */
const closeCreateForm = root => {
    const form = root.querySelector(SELECTORS.createForm);
    if (form) {
        form.setAttribute('hidden', 'hidden');
    }
};

/**
 * Open edit form for marker.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} markerid Marker id.
 */
const openEditForm = (root, markerid) => {
    const marker = findMarkerElement(root, markerid);
    if (!marker) {
        return;
    }

    const form = marker.querySelector(SELECTORS.updateForm);
    if (!form) {
        return;
    }

    form.removeAttribute('hidden');

    const first = form.querySelector('input, select, textarea, button');
    if (first) {
        first.focus();
    }
};

/**
 * Close edit form.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} markerid Marker id.
 */
const closeEditForm = (root, markerid) => {
    const marker = findMarkerElement(root, markerid);
    if (!marker) {
        return;
    }

    const form = marker.querySelector(SELECTORS.updateForm);
    if (form) {
        form.setAttribute('hidden', 'hidden');
    }
};

/**
 * Open review form.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} markerid Marker id.
 */
const openReviewForm = (root, markerid) => {
    const marker = findMarkerElement(root, markerid);
    if (!marker) {
        return;
    }

    const form = marker.querySelector(SELECTORS.reviewForm);
    if (!form) {
        return;
    }

    form.removeAttribute('hidden');

    const first = form.querySelector('input, select, textarea, button');
    if (first) {
        first.focus();
    }
};

/**
 * Close review form.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} markerid Marker id.
 */
const closeReviewForm = (root, markerid) => {
    const marker = findMarkerElement(root, markerid);
    if (!marker) {
        return;
    }

    const form = marker.querySelector(SELECTORS.reviewForm);
    if (form) {
        form.setAttribute('hidden', 'hidden');
    }
};

/**
 * Find marker element.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} markerid Marker id.
 * @returns {HTMLElement|null}
 */
const findMarkerElement = (root, markerid) => {
    return root.querySelector(`${SELECTORS.marker}[data-markerid="${markerid}"]`);
};

/**
 * Resolve marker id from target.
 *
 * @param {HTMLElement} target Event target.
 * @returns {Number}
 */
const markerIdFromTarget = target => {
    const button = target.closest('[data-markerid], [data-content-marker-id]');
    if (!button) {
        return 0;
    }

    return intValue(button.dataset.markerid || button.dataset.contentMarkerId);
};

/**
 * Update locator preview.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement} source Source element.
 */
const updateLocatorPreview = (root, source) => {
    const form = source.closest('form');
    if (!form) {
        return;
    }

    const preview = form.querySelector(SELECTORS.locatorPreview) || root.querySelector(SELECTORS.locatorPreview);
    if (!preview) {
        return;
    }

    const raw = serializeForm(form);
    const locatortype = textValue(raw.locatortype);
    const start = textValue(raw.locatorstart);
    const end = textValue(raw.locatorend);

    preview.textContent = formatLocator(locatortype, start, end);
};

/**
 * Format locator preview text.
 *
 * @param {String} type Locator type.
 * @param {String} start Start.
 * @param {String} end End.
 * @returns {String}
 */
const formatLocator = (type, start, end) => {
    if (!type && !start && !end) {
        return '';
    }

    if (start && end) {
        return `${type}: ${start} – ${end}`;
    }

    if (start) {
        return `${type}: ${start}`;
    }

    return type;
};

/**
 * Update badge preview.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement} source Source element.
 */
const updateBadgePreview = (root, source) => {
    const form = source.closest('form');
    if (!form) {
        return;
    }

    const preview = form.querySelector(SELECTORS.advisoryBadgePreview) ||
        root.querySelector(SELECTORS.advisoryBadgePreview);

    if (!preview) {
        return;
    }

    const raw = serializeForm(form);
    const tagkey = textValue(raw.tagkey);
    const severity = textValue(raw.severity);
    const suitability = textValue(raw.audiencesuitability);
    const restricted = boolValue(raw.restricted);
    const cultural = boolValue(raw.culturalprotocol);

    preview.textContent = [tagkey, severity, suitability].filter(Boolean).join(' · ');
    preview.classList.toggle('uckkarchive-content-advisory-badge--restricted', restricted);
    preview.classList.toggle('uckkarchive-content-advisory-badge--cultural', cultural);
};

/**
 * Update previews from form event.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement} source Source element.
 */
const updatePreviews = (root, source) => {
    if (
        source.matches(SELECTORS.locatorType) ||
        source.matches(SELECTORS.locatorStart) ||
        source.matches(SELECTORS.locatorEnd)
    ) {
        updateLocatorPreview(root, source);
    }

    if (
        source.matches(SELECTORS.tagKey) ||
        source.matches(SELECTORS.severity) ||
        source.matches(SELECTORS.audienceSuitability) ||
        source.matches(SELECTORS.restricted) ||
        source.matches(SELECTORS.culturalProtocol)
    ) {
        updateBadgePreview(root, source);
    }
};

/**
 * Bind events.
 *
 * @param {HTMLElement} root Root element.
 */
const bindEvents = root => {
    root.addEventListener('click', event => {
        const target = event.target;

        if (!(target instanceof HTMLElement)) {
            return;
        }

        if (target.closest(SELECTORS.refreshButton)) {
            event.preventDefault();
            refresh(root);
            return;
        }

        if (target.closest(SELECTORS.openCreateButton)) {
            event.preventDefault();
            openCreateForm(root);
            return;
        }

        if (target.closest(SELECTORS.closeCreateButton)) {
            event.preventDefault();
            closeCreateForm(root);
            return;
        }

        if (target.closest(SELECTORS.editButton)) {
            event.preventDefault();
            openEditForm(root, markerIdFromTarget(target));
            return;
        }

        if (target.closest(SELECTORS.cancelEditButton)) {
            event.preventDefault();
            closeEditForm(root, markerIdFromTarget(target));
            return;
        }

        if (target.closest(SELECTORS.reviewButton)) {
            event.preventDefault();
            openReviewForm(root, markerIdFromTarget(target));
            return;
        }

        if (target.closest(SELECTORS.cancelReviewButton)) {
            event.preventDefault();
            closeReviewForm(root, markerIdFromTarget(target));
            return;
        }

        if (target.closest(SELECTORS.deleteButton)) {
            event.preventDefault();
            deleteMarker(root, markerIdFromTarget(target));
        }
    });

    root.addEventListener('submit', event => {
        const form = event.target;

        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        if (form.matches(SELECTORS.createForm)) {
            event.preventDefault();
            submitCreate(root, form);
            return;
        }

        if (form.matches(SELECTORS.updateForm)) {
            event.preventDefault();
            submitUpdate(root, form);
            return;
        }

        if (form.matches(SELECTORS.reviewForm)) {
            event.preventDefault();
            submitReview(root, form);
            return;
        }

        if (form.matches(SELECTORS.filterForm)) {
            event.preventDefault();
            refresh(root);
        }
    });

    root.addEventListener('change', event => {
        const target = event.target;

        if (!(target instanceof HTMLElement)) {
            return;
        }

        updatePreviews(root, target);

        if (
            target.matches(SELECTORS.filterTag) ||
            target.matches(SELECTORS.filterTargetType) ||
            target.matches(SELECTORS.filterReviewState) ||
            target.matches(SELECTORS.filterSeverity) ||
            target.matches(SELECTORS.filterAudienceSuitability)
        ) {
            refresh(root);
        }
    });

    root.addEventListener('input', event => {
        const target = event.target;

        if (!(target instanceof HTMLElement)) {
            return;
        }

        updatePreviews(root, target);
    });
};

/**
 * Initialise one content advisory root.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Options.
 */
const initRoot = (root, options = {}) => {
    if (!root || root.dataset.contentAdvisoryInitialised === '1') {
        return;
    }

    root.dataset.contentAdvisoryInitialised = '1';

    const state = buildState(root, options);
    setState(root, state);

    bindEvents(root);

    if (root.dataset.autoload !== '0') {
        refresh(root);
    }
};

/**
 * Initialise module.
 *
 * @param {String|HTMLElement|null} root Root selector or element.
 * @param {Object} options Options.
 */
export const init = (root = null, options = {}) => {
    if (root === null) {
        document.querySelectorAll(SELECTORS.root).forEach(element => initRoot(element, options));
        return;
    }

    const element = getRoot(root);
    if (element) {
        initRoot(element, options);
    }
};

/**
 * Public refresh helper.
 *
 * @param {String|HTMLElement|null} root Root selector or element.
 * @returns {Promise<void>}
 */
export const refreshPanel = async(root = null) => {
    const element = getRoot(root);
    if (element) {
        await refresh(element);
    }
};

/**
 * Public marker reload helper.
 *
 * @param {String|HTMLElement|null} root Root selector or element.
 * @returns {Promise<Array>}
 */
export const getMarkers = async(root = null) => {
    const element = getRoot(root);
    if (!element) {
        return [];
    }

    await loadMarkers(element);
    return getState(element).markers;
};

export default {
    init,
    refreshPanel,
    getMarkers,
};

