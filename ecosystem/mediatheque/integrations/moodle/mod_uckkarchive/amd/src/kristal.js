/**
 * Kristal interactions for mod_uckkarchive.
 *
 * This module is UI-only:
 * - filters Kristal cards;
 * - expands and collapses Kristal details;
 * - refreshes Kristal panels through declared Ajax services;
 * - refreshes linked media, content advisory, and external-work panels when a
 *   Kristal card exposes those regions;
 * - handles save/submit form calls when a page chooses to expose them;
 * - confirms server-side actions.
 *
 * It must not validate Kristals, revise archive records, decide provenance,
 * change visibility, export packages, delete evidence, resolve cultural
 * protocol access, or perform integrity workflow decisions locally.
 *
 * @module     mod_uckkarchive/kristal
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

import Ajax from 'core/ajax';
import Notification from 'core/notification';
import Templates from 'core/templates';
import {getString} from 'core/str';

const COMPONENT = 'uckkarchive';

const DEFAULT_METHODS = {
    // There is no declared list/card/draft/submit Kristal service in db/services.php.
    // The module therefore uses only declared services and preserves list/card UI
    // behaviour by refreshing existing cards individually when identifiers exist.
    getKristals: '',
    getKristal: 'mod_uckkarchive_get_kristal',
    createKristal: 'mod_uckkarchive_create_kristal',
    updateKristal: 'mod_uckkarchive_update_kristal',
    saveDraft: '',
    submitKristal: '',
    refreshCard: 'mod_uckkarchive_get_kristal',

    getMediaCard: 'mod_uckkarchive_get_media_card',
    getContentMarkers: 'mod_uckkarchive_get_content_markers',
    getExternalWorks: 'mod_uckkarchive_get_external_works',
};

const REGISTERED_METHODS = new Set([
    DEFAULT_METHODS.getKristal,
    DEFAULT_METHODS.createKristal,
    DEFAULT_METHODS.updateKristal,
    DEFAULT_METHODS.refreshCard,
    DEFAULT_METHODS.getMediaCard,
    DEFAULT_METHODS.getContentMarkers,
    DEFAULT_METHODS.getExternalWorks,
]);

const SELECTORS = {
    root: '[data-region="uckkarchive-kristals"]',
    panel: '[data-region="uckkarchive-kristal-panel"]',
    list: '[data-region="uckkarchive-kristal-list"]',
    status: '[data-region="uckkarchive-kristal-status"]',

    card: '[data-region="uckkarchive-kristal"]',
    details: '[data-region="uckkarchive-kristal-details"]',
    preview: '[data-region="uckkarchive-kristal-preview"]',

    linkedMediaPanel: '[data-region="uckkarchive-kristal-linked-media"]',
    contentAdvisoryPanel: '[data-region="uckkarchive-kristal-content-advisory"]',
    externalWorkPanel: '[data-region="uckkarchive-kristal-external-works"]',

    form: '[data-region="uckkarchive-kristal-form"]',
    titleInput: '[data-field="kristal-title"]',
    summaryInput: '[data-field="kristal-summary"]',
    contentInput: '[data-field="kristal-content"]',
    typeInput: '[data-field="kristal-type"]',
    statusInput: '[data-field="kristal-status"]',
    visibilityInput: '[data-field="kristal-visibility"]',
    validationInput: '[data-field="kristal-validation"]',
    provenanceInput: '[data-field="kristal-provenance"]',
    sourceComponentInput: '[data-field="kristal-source-component"]',
    sourceIdInput: '[data-field="kristal-source-id"]',
    mediaIdInput: '[data-field="kristal-media-id"]',
    externalWorkIdInput: '[data-field="kristal-external-work-id"]',

    search: '[data-action="uckkarchive-kristal-search"]',
    filter: '[data-action="uckkarchive-kristal-filter"]',
    filterButton: '[data-action="uckkarchive-kristal-filter-button"]',
    clearFilters: '[data-action="uckkarchive-kristal-clear-filters"]',

    toggle: '[data-action="uckkarchive-kristal-toggle"]',
    previewToggle: '[data-action="uckkarchive-kristal-toggle-preview"]',

    refresh: '[data-action="uckkarchive-kristal-refresh"]',
    refreshCard: '[data-action="uckkarchive-kristal-refresh-card"]',
    refreshLinkedMedia: '[data-action="uckkarchive-kristal-refresh-linked-media"]',
    refreshContentAdvisory: '[data-action="uckkarchive-kristal-refresh-content-advisory"]',
    refreshExternalWorks: '[data-action="uckkarchive-kristal-refresh-external-works"]',
    refreshRelatedPanels: '[data-action="uckkarchive-kristal-refresh-related-panels"]',

    saveDraft: '[data-action="uckkarchive-kristal-save-draft"]',
    submit: '[data-action="uckkarchive-kristal-submit"]',
    confirmAction: '[data-action="uckkarchive-kristal-confirm-action"]',

    countVisible: '[data-region="uckkarchive-kristal-count-visible"]',
    countTotal: '[data-region="uckkarchive-kristal-count-total"]',
    emptyFiltered: '[data-region="uckkarchive-kristal-empty-filtered"]',
};

const CLASSES = {
    loading: 'is-loading',
    dirty: 'is-dirty',
    saved: 'is-saved',
    error: 'has-error',
    hidden: 'd-none',
    expanded: 'is-expanded',
    filteredOut: 'is-filtered-out',
};

const ATTRIBUTES = {
    initialised: 'data-uckkarchive-kristal-initialised',
};

const DEFAULT_AUTOSAVE_DELAY = 2500;

let autosaveTimers = new WeakMap();

/**
 * Get a numeric dataset value.
 *
 * @param {HTMLElement|null} element Source element.
 * @param {String} key Dataset key.
 * @param {Number} fallback Fallback value.
 * @returns {Number}
 */
const getNumberData = (element, key, fallback = 0) => {
    const value = Number(element?.dataset?.[key] ?? fallback);

    return Number.isFinite(value) ? value : fallback;
};

/**
 * Get a boolean dataset value.
 *
 * @param {HTMLElement|null} element Source element.
 * @param {String} key Dataset key.
 * @param {Boolean} fallback Fallback value.
 * @returns {Boolean}
 */
const getBooleanData = (element, key, fallback = false) => {
    const value = element?.dataset?.[key];

    if (value === undefined) {
        return fallback;
    }

    return value === '1' || value === 'true' || value === true;
};

/**
 * Resolve a Moodle Ajax method name against the declared service allow-list.
 *
 * @param {String|undefined|null} methodname Candidate method name.
 * @returns {String}
 */
const resolveMethod = methodname => {
    const resolved = String(methodname || '').trim();

    return REGISTERED_METHODS.has(resolved) ? resolved : '';
};

/**
 * Resolve an optional method override.
 *
 * @param {String|undefined|null} override Override method.
 * @param {String} fallback Fallback method.
 * @returns {String}
 */
const resolveOptionalMethod = (override, fallback = '') => {
    return resolveMethod(override) || resolveMethod(fallback);
};

/**
 * Resolve method names from data attributes or options.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Init options.
 * @returns {Object}
 */
const getMethods = (root, options = {}) => {
    return {
        getKristals: '',
        getKristal: resolveOptionalMethod(
            root.dataset.getKristalMethod || options.getKristalMethod,
            DEFAULT_METHODS.getKristal
        ),
        createKristal: resolveOptionalMethod(
            root.dataset.createKristalMethod || options.createKristalMethod,
            DEFAULT_METHODS.createKristal
        ),
        updateKristal: resolveOptionalMethod(
            root.dataset.updateKristalMethod || options.updateKristalMethod,
            DEFAULT_METHODS.updateKristal
        ),
        saveDraft: resolveOptionalMethod(
            root.dataset.saveDraftMethod || options.saveDraftMethod,
            DEFAULT_METHODS.saveDraft
        ),
        submitKristal: resolveOptionalMethod(
            root.dataset.submitMethod || options.submitMethod,
            DEFAULT_METHODS.submitKristal
        ),
        refreshCard: resolveOptionalMethod(
            root.dataset.refreshCardMethod || options.refreshCardMethod,
            DEFAULT_METHODS.refreshCard
        ),

        getMediaCard: resolveOptionalMethod(
            root.dataset.getMediaCardMethod || options.getMediaCardMethod,
            DEFAULT_METHODS.getMediaCard
        ),
        getContentMarkers: resolveOptionalMethod(
            root.dataset.getContentMarkersMethod || options.getContentMarkersMethod,
            DEFAULT_METHODS.getContentMarkers
        ),
        getExternalWorks: resolveOptionalMethod(
            root.dataset.getExternalWorksMethod || options.getExternalWorksMethod,
            DEFAULT_METHODS.getExternalWorks
        ),
    };
};

/**
 * Base Ajax args for this region.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Object}
 */
const getBaseArgs = root => {
    return {
        cmid: getNumberData(root, 'cmid'),
        archiveid: getNumberData(root, 'archiveid'),
        courseid: getNumberData(root, 'courseid'),
        contextid: getNumberData(root, 'contextid'),
    };
};

/**
 * Check required identifiers.
 *
 * @param {Object} args Ajax args.
 * @returns {Boolean}
 */
const hasRequiredIdentifiers = args => Boolean(args.cmid && args.archiveid);

/**
 * Set status text.
 *
 * @param {HTMLElement} root Root element.
 * @param {String} message Message.
 */
const setStatus = (root, message) => {
    const status = root.querySelector(SELECTORS.status);

    if (status) {
        status.textContent = message;
    }
};

/**
 * Dispatch a UI event from the root.
 *
 * @param {HTMLElement} root Root element.
 * @param {String} name Event name without the component prefix.
 * @param {Object} detail Event detail.
 */
const dispatchEvent = (root, name, detail = {}) => {
    root.dispatchEvent(new CustomEvent(`mod_uckkarchive:kristal:${name}`, {
        bubbles: true,
        detail,
    }));
};

/**
 * Call one Moodle Ajax service.
 *
 * @param {String} methodname Service name.
 * @param {Object} args Service args.
 * @returns {Promise<Object>}
 */
const callService = (methodname, args) => {
    const resolved = resolveMethod(methodname);

    if (!resolved) {
        return Promise.reject(new Error(`Undeclared UCKK Archive Ajax service: ${methodname || 'none'}`));
    }

    return Ajax.call([{
        methodname: resolved,
        args,
    }])[0];
};

/**
 * Return all visible/filterable Kristal cards.
 *
 * @param {HTMLElement} root Root element.
 * @returns {HTMLElement[]}
 */
const getCards = root => Array.from(root.querySelectorAll(SELECTORS.card));

/**
 * Get currently active filters.
 *
 * @param {HTMLElement} root Root element.
 * @returns {{search: String, filters: Object}}
 */
const getActiveFilters = root => {
    const search = root.querySelector(SELECTORS.search);
    const filters = {};

    root.querySelectorAll(SELECTORS.filter).forEach(field => {
        const key = field.dataset.filterKey || field.name || '';

        if (!key) {
            return;
        }

        if (field.type === 'checkbox') {
            if (field.checked) {
                filters[key] = field.value || '1';
            }
            return;
        }

        if (field.type === 'radio') {
            if (field.checked && field.value !== '') {
                filters[key] = field.value;
            }
            return;
        }

        if (field.value !== '') {
            filters[key] = field.value;
        }
    });

    root.querySelectorAll(SELECTORS.filterButton).forEach(button => {
        if (button.getAttribute('aria-pressed') !== 'true') {
            return;
        }

        const key = button.dataset.filterKey || '';
        const value = button.dataset.filterValue || '';

        if (key && value) {
            filters[key] = value;
        }
    });

    return {
        search: search ? search.value.trim().toLowerCase() : '',
        filters,
    };
};

/**
 * Convert filter key to dataset key.
 *
 * @param {String} key Filter key.
 * @returns {String}
 */
const filterKeyToDatasetKey = key => {
    return key.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
};

/**
 * Whether a card matches active filters.
 *
 * @param {HTMLElement} card Kristal card.
 * @param {String} search Search query.
 * @param {Object} filters Filters.
 * @returns {Boolean}
 */
const matchesFilters = (card, search, filters) => {
    if (search) {
        const haystack = [
            card.textContent || '',
            card.dataset.title || '',
            card.dataset.summary || '',
            card.dataset.kristalType || '',
            card.dataset.status || '',
            card.dataset.visibility || '',
            card.dataset.validation || '',
            card.dataset.provenance || '',
            card.dataset.sourceComponent || '',
            card.dataset.mediaTitle || '',
            card.dataset.mediaType || '',
            card.dataset.contentTags || '',
            card.dataset.contentSeverity || '',
            card.dataset.externalWorkTitle || '',
            card.dataset.externalWorkType || '',
        ].join(' ').toLowerCase();

        if (!haystack.includes(search)) {
            return false;
        }
    }

    return Object.entries(filters).every(([key, value]) => {
        if (value === '*' || value === 'all') {
            return true;
        }

        const datasetKey = filterKeyToDatasetKey(key);
        const datasetValue = card.dataset[datasetKey] || '';

        if (datasetValue.includes('|')) {
            return datasetValue.split('|').includes(value);
        }

        return datasetValue === value;
    });
};

/**
 * Apply current filters to Kristal cards.
 *
 * @param {HTMLElement} root Root element.
 */
const applyFilters = root => {
    const {search, filters} = getActiveFilters(root);
    const cards = getCards(root);
    let visible = 0;

    cards.forEach(card => {
        const match = matchesFilters(card, search, filters);

        card.hidden = !match;
        card.classList.toggle(CLASSES.hidden, !match);
        card.classList.toggle(CLASSES.filteredOut, !match);

        if (match) {
            visible++;
        }
    });

    updateCounts(root, visible, cards.length);
    dispatchEvent(root, 'filtered', {
        visible,
        total: cards.length,
        filters,
        search,
    });
};

/**
 * Update visible and total counts.
 *
 * @param {HTMLElement} root Root element.
 * @param {Number} visible Visible count.
 * @param {Number} total Total count.
 */
const updateCounts = (root, visible, total) => {
    const visibleNode = root.querySelector(SELECTORS.countVisible);
    const totalNode = root.querySelector(SELECTORS.countTotal);
    const emptyNode = root.querySelector(SELECTORS.emptyFiltered);

    if (visibleNode) {
        visibleNode.textContent = String(visible);
    }

    if (totalNode) {
        totalNode.textContent = String(total);
    }

    if (emptyNode) {
        const showEmpty = total > 0 && visible === 0;
        emptyNode.hidden = !showEmpty;
        emptyNode.classList.toggle(CLASSES.hidden, !showEmpty);
    }
};

/**
 * Clear filters.
 *
 * @param {HTMLElement} root Root element.
 */
const clearFilters = root => {
    const search = root.querySelector(SELECTORS.search);

    if (search) {
        search.value = '';
    }

    root.querySelectorAll(SELECTORS.filter).forEach(field => {
        if (field.type === 'checkbox' || field.type === 'radio') {
            field.checked = false;
        } else {
            field.value = '';
        }
    });

    root.querySelectorAll(SELECTORS.filterButton).forEach(button => {
        button.setAttribute('aria-pressed', 'false');
        button.classList.remove('active');
    });

    applyFilters(root);
};

/**
 * Toggle a filter button group.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement} button Button.
 */
const toggleFilterButton = (root, button) => {
    const key = button.dataset.filterKey || '';

    if (!key) {
        return;
    }

    const pressed = button.getAttribute('aria-pressed') === 'true';
    const allowMultiple = getBooleanData(button, 'allowMultiple', false);

    if (!allowMultiple) {
        root.querySelectorAll(`${SELECTORS.filterButton}[data-filter-key="${key}"]`).forEach(peer => {
            peer.setAttribute('aria-pressed', 'false');
            peer.classList.remove('active');
        });
    }

    button.setAttribute('aria-pressed', pressed ? 'false' : 'true');
    button.classList.toggle('active', !pressed);

    applyFilters(root);
};

/**
 * Toggle a collapsible region.
 *
 * @param {HTMLElement} trigger Trigger.
 * @param {String} regionSelector Region selector.
 * @param {String} parentSelector Parent selector.
 */
const toggleRegion = (trigger, regionSelector, parentSelector = SELECTORS.card) => {
    const parent = trigger.closest(parentSelector);

    if (!parent) {
        return;
    }

    const region = parent.querySelector(regionSelector);

    if (!region) {
        return;
    }

    const expanded = trigger.getAttribute('aria-expanded') === 'true';
    const nextExpanded = !expanded;

    trigger.setAttribute('aria-expanded', nextExpanded ? 'true' : 'false');
    region.hidden = !nextExpanded;
    region.classList.toggle(CLASSES.hidden, !nextExpanded);
    parent.classList.toggle(CLASSES.expanded, nextExpanded);
};

/**
 * Toggle a Kristal detail panel.
 *
 * @param {HTMLElement} trigger Trigger.
 */
const toggleDetails = trigger => {
    toggleRegion(trigger, SELECTORS.details);
};

/**
 * Toggle a Kristal preview panel.
 *
 * @param {HTMLElement} trigger Trigger.
 */
const togglePreview = trigger => {
    toggleRegion(trigger, SELECTORS.preview);
};

/**
 * Collect form field value.
 *
 * @param {HTMLElement|null} field Field.
 * @returns {String|Number|Boolean}
 */
const getFieldValue = field => {
    if (!field) {
        return '';
    }

    if (field.type === 'checkbox') {
        return field.checked;
    }

    if (field.type === 'number' || field.dataset.valueType === 'number') {
        const value = Number(field.value);
        return Number.isFinite(value) ? value : 0;
    }

    return field.value;
};

/**
 * Collect one Kristal form payload.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Object}
 */
const collectKristalData = root => {
    const form = root.querySelector(SELECTORS.form);

    return {
        ...getBaseArgs(root),
        kristalid: getNumberData(root, 'kristalid') || getNumberData(form, 'kristalid'),
        itemid: getNumberData(root, 'itemid') || getNumberData(form, 'itemid'),
        proofid: getNumberData(root, 'proofid') || getNumberData(form, 'proofid'),
        mediaid: getNumberData(root, 'mediaid') || getNumberData(form, 'mediaid')
            || Number(getFieldValue(root.querySelector(SELECTORS.mediaIdInput)) || 0),
        externalworkid: getNumberData(root, 'externalworkid') || getNumberData(form, 'externalworkid')
            || Number(getFieldValue(root.querySelector(SELECTORS.externalWorkIdInput)) || 0),
        title: getFieldValue(root.querySelector(SELECTORS.titleInput)),
        summary: getFieldValue(root.querySelector(SELECTORS.summaryInput)),
        content: getFieldValue(root.querySelector(SELECTORS.contentInput)),
        kristaltype: getFieldValue(root.querySelector(SELECTORS.typeInput)),
        status: getFieldValue(root.querySelector(SELECTORS.statusInput)),
        visibility: getFieldValue(root.querySelector(SELECTORS.visibilityInput)),
        validationstate: getFieldValue(root.querySelector(SELECTORS.validationInput)),
        provenance: getFieldValue(root.querySelector(SELECTORS.provenanceInput)),
        sourcecomponent: getFieldValue(root.querySelector(SELECTORS.sourceComponentInput)),
        sourceid: getFieldValue(root.querySelector(SELECTORS.sourceIdInput)),
        sesskey: form?.dataset?.sesskey || M.cfg.sesskey,
    };
};

/**
 * Convert collected form data to the canonical external service payload.
 *
 * create_kristal accepts: cmid, itemid, title, claim, body, evidence,
 * confidence, visibility, provenance, metadatajson.
 *
 * update_kristal accepts: cmid, kristalid, title, claim, body, evidence,
 * confidence, status, visibility, validationstate.
 *
 * @param {Object} data Collected Kristal data.
 * @param {Object} overrides Payload overrides.
 * @returns {Object}
 */
const buildKristalServicePayload = (data, overrides = {}) => {
    const metadata = {
        kristaltype: data.kristaltype || '',
        sourcecomponent: data.sourcecomponent || '',
        sourceid: data.sourceid || 0,
        mediaid: data.mediaid || 0,
        externalworkid: data.externalworkid || 0,
        proofid: data.proofid || 0,
    };

    const claim = String(data.summary || data.content || data.title || '').trim();
    const body = String(data.content || '').trim();
    const evidence = String(data.summary || '').trim();
    const payload = {
        cmid: data.cmid,
        title: data.title || '',
        claim,
        body,
        evidence,
        confidence: Number.isFinite(Number(data.confidence)) ? Number(data.confidence) : 0,
        visibility: data.visibility || '',
        provenance: data.provenance || 'human',
        status: data.status || '',
        validationstate: data.validationstate || '',
        ...overrides,
    };

    if (data.kristalid) {
        payload.kristalid = data.kristalid;
    } else {
        payload.itemid = data.itemid;
        payload.metadatajson = JSON.stringify(metadata);
    }

    return payload;
};

/**
 * Resolve the correct declared write method for the current payload.
 *
 * @param {Object} methods Resolved method map.
 * @param {Object} data Collected Kristal data.
 * @param {String} preferred Optional preferred method.
 * @returns {String}
 */
const getWriteMethod = (methods, data, preferred = '') => {
    return resolveMethod(preferred)
        || (data.kristalid ? methods.updateKristal : methods.createKristal);
};

/**
 * Update an existing card from a get_kristal response when no rendered HTML
 * is returned by the external service.
 *
 * @param {HTMLElement|null} card Card element.
 * @param {Object|null} kristal Kristal export object.
 */
const updateKristalCardFromRecord = (card, kristal) => {
    if (!card || !kristal) {
        return;
    }

    card.dataset.kristalid = String(kristal.id || card.dataset.kristalid || '');
    card.dataset.itemid = String(kristal.itemid || card.dataset.itemid || '');
    card.dataset.title = kristal.title || card.dataset.title || '';
    card.dataset.summary = kristal.claim || card.dataset.summary || '';
    card.dataset.status = kristal.status || card.dataset.status || '';
    card.dataset.visibility = kristal.visibility || card.dataset.visibility || '';
    card.dataset.validation = kristal.validationstate || card.dataset.validation || '';
    card.dataset.provenance = kristal.provenance || card.dataset.provenance || '';

    const titleNode = card.querySelector('[data-region="kristal-title"], [data-field="kristal-title-output"]');
    if (titleNode && kristal.title) {
        titleNode.textContent = kristal.title;
    }

    const claimNode = card.querySelector('[data-region="kristal-claim"], [data-field="kristal-claim-output"]');
    if (claimNode && kristal.claim) {
        claimNode.innerHTML = kristal.claim;
    }

    const bodyNode = card.querySelector('[data-region="kristal-body"], [data-field="kristal-body-output"]');
    if (bodyNode && kristal.body) {
        bodyNode.innerHTML = kristal.body;
    }

    const evidenceNode = card.querySelector('[data-region="kristal-evidence"], [data-field="kristal-evidence-output"]');
    if (evidenceNode && kristal.evidence) {
        evidenceNode.innerHTML = kristal.evidence;
    }

    const statusNode = card.querySelector('[data-region="kristal-status-label"], [data-field="kristal-status-output"]');
    if (statusNode && kristal.status) {
        statusNode.textContent = kristal.status;
    }

    const validationNode = card.querySelector('[data-region="kristal-validation-label"], [data-field="kristal-validation-output"]');
    if (validationNode && kristal.validationstate) {
        validationNode.textContent = kristal.validationstate;
    }
};

/**
 * Validate minimum client-side requirements before submit.
 *
 * Server-side validation remains authoritative.
 *
 * @param {HTMLElement} root Root element.
 * @returns {Promise<Boolean>}
 */
const validateBeforeSubmit = async(root) => {
    const data = collectKristalData(root);

    if (!hasRequiredIdentifiers(data)) {
        await Notification.alert(
            await getString('kristalerror', COMPONENT),
            await getString('archivemissingidentifiers', COMPONENT)
        );
        return false;
    }

    if (!String(data.title || '').trim()) {
        await Notification.alert(
            await getString('kristalerror', COMPONENT),
            await getString('kristalmissingtitle', COMPONENT)
        );
        return false;
    }

    if (!String(data.content || '').trim()) {
        await Notification.alert(
            await getString('kristalerror', COMPONENT),
            await getString('kristalmissingcontent', COMPONENT)
        );
        return false;
    }

    return true;
};

/**
 * Mark form region dirty.
 *
 * @param {HTMLElement} root Root element.
 */
const markDirty = root => {
    root.classList.add(CLASSES.dirty);
    root.classList.remove(CLASSES.saved);
};

/**
 * Mark form region saved.
 *
 * @param {HTMLElement} root Root element.
 */
const markSaved = root => {
    root.classList.remove(CLASSES.dirty);
    root.classList.add(CLASSES.saved);
};

/**
 * Build target args for linked panels.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement|null} source Source trigger/card.
 * @returns {Object}
 */
const getTargetArgs = (root, source = null) => {
    const card = source?.closest?.(SELECTORS.card) || source || root;
    const base = getBaseArgs(root);
    const kristalid = getNumberData(source, 'kristalid') || getNumberData(card, 'kristalid') || getNumberData(root, 'kristalid');
    const mediaid = getNumberData(source, 'mediaid') || getNumberData(card, 'mediaid') || getNumberData(root, 'mediaid');
    const externalworkid = getNumberData(source, 'externalworkid')
        || getNumberData(card, 'externalworkid')
        || getNumberData(root, 'externalworkid');
    const itemid = getNumberData(source, 'itemid') || getNumberData(card, 'itemid') || getNumberData(root, 'itemid');

    return {
        ...base,
        kristalid,
        mediaid,
        externalworkid,
        itemid,
    };
};

/**
 * Render an Ajax response into a target region.
 *
 * @param {HTMLElement} region Target region.
 * @param {Object} response Ajax response.
 * @returns {Promise<Boolean>}
 */
const renderResponseToRegion = async(region, response) => {
    if (!region || !response) {
        return false;
    }

    if (response.template && response.context) {
        const html = await Templates.render(response.template, response.context);
        Templates.replaceNodeContents(region, html, response.js || '');
    } else if (response.html) {
        Templates.replaceNodeContents(region, response.html, response.js || '');
    } else {
        return false;
    }

    if (response.js) {
        Templates.runTemplateJS(response.js);
    }

    return true;
};

/**
 * Save a Kristal draft.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Init options.
 * @returns {Promise<void>}
 */
const saveDraft = async(root, options = {}) => {
    const methods = getMethods(root, options);
    const data = collectKristalData(root);

    if (!hasRequiredIdentifiers(data) || (!data.kristalid && !data.itemid)) {
        return;
    }

    const methodname = getWriteMethod(methods, data, methods.saveDraft);
    const args = buildKristalServicePayload(data, {
        status: data.status || 'draft',
    });

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('kristalsaving', COMPONENT));

        const response = await callService(methodname, args);

        if (response?.kristalid) {
            root.dataset.kristalid = String(response.kristalid);
        }

        if (response?.html) {
            replacePanel(root, response.html, response.js || '');
        }

        markSaved(root);
        setStatus(root, await getString('kristalsaved', COMPONENT));
        dispatchEvent(root, 'saved', {
            response,
            args,
            methodname,
        });

        if (options.refreshRelatedAfterSave !== false && root.dataset.refreshRelatedAfterSave !== 'false') {
            await refreshRelatedPanels(root, root, options, {silent: true});
        }
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('kristalsavefailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Submit a Kristal to server-side workflow.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Init options.
 * @returns {Promise<void>}
 */
const submitKristal = async(root, options = {}) => {
    const valid = await validateBeforeSubmit(root);

    if (!valid) {
        return;
    }

    const confirmed = await confirmAction({
        dataset: {
            confirmTitle: await getString('confirmkristalsubmit', COMPONENT),
            confirmBody: await getString('confirmkristalsubmitbody', COMPONENT),
        },
    });

    if (!confirmed) {
        return;
    }

    const methods = getMethods(root, options);
    const data = collectKristalData(root);

    if (!data.kristalid && !data.itemid) {
        return;
    }

    const methodname = getWriteMethod(methods, data, methods.submitKristal);
    const args = buildKristalServicePayload(data, {
        status: 'submitted',
        validationstate: data.validationstate || '',
    });

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('kristalsubmitting', COMPONENT));

        const response = await callService(methodname, args);

        if (response?.redirecturl) {
            window.location.assign(response.redirecturl);
            return;
        }

        if (response?.kristalid) {
            root.dataset.kristalid = String(response.kristalid);
        }

        if (response?.html) {
            replacePanel(root, response.html, response.js || '');
        }

        markSaved(root);
        setStatus(root, await getString('kristalsubmitted', COMPONENT));
        dispatchEvent(root, 'submitted', {
            response,
            args,
            methodname,
        });

        if (options.refreshRelatedAfterSubmit !== false && root.dataset.refreshRelatedAfterSubmit !== 'false') {
            await refreshRelatedPanels(root, root, options, {silent: true});
        }
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('kristalsubmitfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Refresh all Kristals for a region.
 *
 * There is no declared list-level Kristal Ajax service in db/services.php.
 * This method therefore refreshes existing cards individually through
 * mod_uckkarchive_get_kristal when card identifiers are available, then
 * reapplies local filters. This preserves UI behaviour without calling an
 * undeclared service.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Init options.
 * @returns {Promise<void>}
 */
const refreshKristals = async(root, options = {}) => {
    const args = getBaseArgs(root);

    if (!hasRequiredIdentifiers(args)) {
        await Notification.alert(
            await getString('kristalerror', COMPONENT),
            await getString('archivemissingidentifiers', COMPONENT)
        );
        return;
    }

    const cards = getCards(root);

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('kristalrefreshing', COMPONENT));

        if (cards.length > 0) {
            await Promise.all(cards.map(card => refreshKristalCard(root, card, options, {silent: true})));
        } else {
            applyFilters(root);
        }

        setStatus(root, await getString('kristalrefreshed', COMPONENT));
        dispatchEvent(root, 'refreshed', {
            response: null,
            args,
            refreshedcards: cards.length,
        });
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('kristalrefreshfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Refresh a single Kristal card.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement} trigger Trigger.
 * @param {Object} options Init options.
 * @param {Object} behavior Behaviour options.
 * @returns {Promise<void>}
 */
const refreshKristalCard = async(root, trigger, options = {}, behavior = {}) => {
    const card = trigger.closest?.(SELECTORS.card) || trigger;
    const kristalid = getNumberData(trigger, 'kristalid') || getNumberData(card, 'kristalid');
    const itemid = getNumberData(trigger, 'itemid') || getNumberData(card, 'itemid');

    if (!kristalid && !itemid) {
        return;
    }

    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        kristalid,
        itemid,
    };

    card?.classList.add(CLASSES.loading);

    try {
        const response = await callService(methods.refreshCard, args);

        if (card && response?.template && response?.context) {
            const html = await Templates.render(response.template, response.context);
            Templates.replaceNode(card, html, response.js || '');
        } else if (card && response?.html) {
            Templates.replaceNode(card, response.html, response.js || '');
        } else if (card && response?.kristal) {
            updateKristalCardFromRecord(card, response.kristal);
        }

        if (response?.js) {
            Templates.runTemplateJS(response.js);
        }

        applyFilters(root);
        dispatchEvent(root, 'cardRefreshed', {
            response,
            args,
        });
    } catch (error) {
        if (!behavior.silent) {
            Notification.exception(error);
        }
    } finally {
        card?.classList.remove(CLASSES.loading);
    }
};

/**
 * Refresh linked media card panel for a Kristal.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement|null} source Trigger/card.
 * @param {Object} options Init options.
 * @param {Object} behavior Behavior options.
 * @returns {Promise<void>}
 */
const refreshLinkedMedia = async(root, source = null, options = {}, behavior = {}) => {
    const panel = (source?.closest?.(SELECTORS.card) || root).querySelector(SELECTORS.linkedMediaPanel)
        || root.querySelector(SELECTORS.linkedMediaPanel);
    const args = getTargetArgs(root, source);
    const methods = getMethods(root, options);

    if (!panel || !args.mediaid) {
        return;
    }

    panel.classList.add(CLASSES.loading);

    try {
        const response = await callService(methods.getMediaCard, {
            cmid: args.cmid,
            mediaid: args.mediaid,
            include: {
                tags: true,
                files: true,
                versions: true,
                advisories: true,
            },
        });

        await renderResponseToRegion(panel, response);
        dispatchEvent(root, 'linkedMediaRefreshed', {
            response,
            args,
        });
    } catch (error) {
        if (!behavior.silent) {
            Notification.exception(error);
        }
    } finally {
        panel.classList.remove(CLASSES.loading);
    }
};

/**
 * Refresh content advisory panel for a Kristal target.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement|null} source Trigger/card.
 * @param {Object} options Init options.
 * @param {Object} behavior Behavior options.
 * @returns {Promise<void>}
 */
const refreshContentAdvisory = async(root, source = null, options = {}, behavior = {}) => {
    const panel = (source?.closest?.(SELECTORS.card) || root).querySelector(SELECTORS.contentAdvisoryPanel)
        || root.querySelector(SELECTORS.contentAdvisoryPanel);
    const args = getTargetArgs(root, source);
    const methods = getMethods(root, options);

    if (!panel || !args.cmid) {
        return;
    }

    const targettype = panel.dataset.targetType
        || source?.dataset?.targetType
        || (args.mediaid ? 'media' : 'archive_item');
    const targetid = getNumberData(panel, 'targetid')
        || getNumberData(source, 'targetid')
        || args.mediaid
        || args.itemid
        || args.kristalid;

    if (!targetid) {
        return;
    }

    panel.classList.add(CLASSES.loading);

    try {
        const response = await callService(methods.getContentMarkers, {
            cmid: args.cmid,
            targettype,
            targetid,
            include: {
                tags: true,
                reviews: true,
                externalworks: true,
            },
        });

        await renderResponseToRegion(panel, response);
        dispatchEvent(root, 'contentAdvisoryRefreshed', {
            response,
            args: {
                ...args,
                targettype,
                targetid,
            },
        });
    } catch (error) {
        if (!behavior.silent) {
            Notification.exception(error);
        }
    } finally {
        panel.classList.remove(CLASSES.loading);
    }
};

/**
 * Refresh external works panel for a Kristal.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement|null} source Trigger/card.
 * @param {Object} options Init options.
 * @param {Object} behavior Behavior options.
 * @returns {Promise<void>}
 */
const refreshExternalWorks = async(root, source = null, options = {}, behavior = {}) => {
    const panel = (source?.closest?.(SELECTORS.card) || root).querySelector(SELECTORS.externalWorkPanel)
        || root.querySelector(SELECTORS.externalWorkPanel);
    const args = getTargetArgs(root, source);
    const methods = getMethods(root, options);

    if (!panel || !args.cmid) {
        return;
    }

    panel.classList.add(CLASSES.loading);

    try {
        const response = await callService(methods.getExternalWorks, {
            cmid: args.cmid,
            mediaid: args.mediaid || 0,
            kristalid: args.kristalid || 0,
            itemid: args.itemid || 0,
            include: {
                markers: true,
                rights: true,
            },
        });

        await renderResponseToRegion(panel, response);
        dispatchEvent(root, 'externalWorksRefreshed', {
            response,
            args,
        });
    } catch (error) {
        if (!behavior.silent) {
            Notification.exception(error);
        }
    } finally {
        panel.classList.remove(CLASSES.loading);
    }
};

/**
 * Refresh all related Kristal side panels exposed by the current page.
 *
 * @param {HTMLElement} root Root element.
 * @param {HTMLElement|null} source Trigger/card.
 * @param {Object} options Init options.
 * @param {Object} behavior Behavior options.
 * @returns {Promise<void>}
 */
const refreshRelatedPanels = async(root, source = null, options = {}, behavior = {}) => {
    await Promise.all([
        refreshLinkedMedia(root, source, options, behavior),
        refreshContentAdvisory(root, source, options, behavior),
        refreshExternalWorks(root, source, options, behavior),
    ]);

    applyFilters(root);
};

/**
 * Replace panel contents.
 *
 * @param {HTMLElement} root Root element.
 * @param {String} html HTML.
 * @param {String} js Template JS.
 */
const replacePanel = (root, html, js = '') => {
    const panel = root.querySelector(SELECTORS.panel) || root.querySelector(SELECTORS.list);

    if (!panel) {
        return;
    }

    Templates.replaceNodeContents(panel, html, js);

    if (js) {
        Templates.runTemplateJS(js);
    }
};

/**
 * Confirm a server-side action.
 *
 * @param {HTMLElement|Object} trigger Trigger or trigger-like object.
 * @returns {Promise<Boolean>}
 */
const confirmAction = async(trigger) => {
    const title = trigger.dataset.confirmTitle || await getString('confirmarchiveaction', COMPONENT);
    const body = trigger.dataset.confirmBody || await getString('confirmarchiveactionbody', COMPONENT);
    const confirmLabel = trigger.dataset.confirmButton || await getString('confirm', 'moodle');
    const cancelLabel = trigger.dataset.cancelButton || await getString('cancel', 'moodle');

    return new Promise(resolve => {
        Notification.confirm(
            title,
            body,
            confirmLabel,
            cancelLabel,
            () => resolve(true),
            () => resolve(false)
        );
    });
};

/**
 * Schedule draft autosave.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Init options.
 */
const scheduleAutosave = (root, options = {}) => {
    if (options.autosave === false || root.dataset.autosave === 'false') {
        return;
    }

    const form = root.querySelector(SELECTORS.form);

    if (!form) {
        return;
    }

    const delay = Number(options.autosaveDelay || root.dataset.autosaveDelay || DEFAULT_AUTOSAVE_DELAY);
    const previous = autosaveTimers.get(root);

    if (previous) {
        window.clearTimeout(previous);
    }

    const timer = window.setTimeout(() => {
        saveDraft(root, options);
    }, Number.isFinite(delay) ? delay : DEFAULT_AUTOSAVE_DELAY);

    autosaveTimers.set(root, timer);
};

/**
 * Handle form/filter changes.
 *
 * @param {Event} event Event.
 * @param {HTMLElement} root Root element.
 * @param {Object} options Init options.
 */
const handleChange = (event, root, options = {}) => {
    if (
        event.target.closest(SELECTORS.search)
        || event.target.closest(SELECTORS.filter)
    ) {
        applyFilters(root);
        return;
    }

    if (event.target.closest(SELECTORS.form)) {
        markDirty(root);
        scheduleAutosave(root, options);
    }
};

/**
 * Handle click actions.
 *
 * @param {MouseEvent} event Click event.
 * @param {HTMLElement} root Root element.
 * @param {Object} options Init options.
 */
const handleClick = async(event, root, options = {}) => {
    const clearButton = event.target.closest(SELECTORS.clearFilters);
    if (clearButton) {
        event.preventDefault();
        clearFilters(root);
        return;
    }

    const filterButton = event.target.closest(SELECTORS.filterButton);
    if (filterButton) {
        event.preventDefault();
        toggleFilterButton(root, filterButton);
        return;
    }

    const toggleButton = event.target.closest(SELECTORS.toggle);
    if (toggleButton) {
        event.preventDefault();
        toggleDetails(toggleButton);
        return;
    }

    const previewButton = event.target.closest(SELECTORS.previewToggle);
    if (previewButton) {
        event.preventDefault();
        togglePreview(previewButton);
        return;
    }

    const refreshButton = event.target.closest(SELECTORS.refresh);
    if (refreshButton) {
        event.preventDefault();
        await refreshKristals(root, options);
        return;
    }

    const refreshCardButton = event.target.closest(SELECTORS.refreshCard);
    if (refreshCardButton) {
        event.preventDefault();
        await refreshKristalCard(root, refreshCardButton, options);
        return;
    }

    const refreshMediaButton = event.target.closest(SELECTORS.refreshLinkedMedia);
    if (refreshMediaButton) {
        event.preventDefault();
        await refreshLinkedMedia(root, refreshMediaButton, options);
        return;
    }

    const refreshAdvisoryButton = event.target.closest(SELECTORS.refreshContentAdvisory);
    if (refreshAdvisoryButton) {
        event.preventDefault();
        await refreshContentAdvisory(root, refreshAdvisoryButton, options);
        return;
    }

    const refreshExternalWorksButton = event.target.closest(SELECTORS.refreshExternalWorks);
    if (refreshExternalWorksButton) {
        event.preventDefault();
        await refreshExternalWorks(root, refreshExternalWorksButton, options);
        return;
    }

    const refreshRelatedButton = event.target.closest(SELECTORS.refreshRelatedPanels);
    if (refreshRelatedButton) {
        event.preventDefault();
        await refreshRelatedPanels(root, refreshRelatedButton, options);
        return;
    }

    const saveButton = event.target.closest(SELECTORS.saveDraft);
    if (saveButton) {
        event.preventDefault();
        await saveDraft(root, options);
        return;
    }

    const submitButton = event.target.closest(SELECTORS.submit);
    if (submitButton) {
        event.preventDefault();
        await submitKristal(root, options);
        return;
    }

    const confirmTrigger = event.target.closest(SELECTORS.confirmAction);
    if (confirmTrigger) {
        const confirmed = await confirmAction(confirmTrigger);

        if (!confirmed) {
            event.preventDefault();
            event.stopPropagation();
        }
    }
};

/**
 * Initialise one Kristal root.
 *
 * @param {HTMLElement} root Root element.
 * @param {Object} options Init options.
 */
const initialiseRoot = (root, options = {}) => {
    if (!root || root.getAttribute(ATTRIBUTES.initialised) === 'true') {
        return;
    }

    root.setAttribute(ATTRIBUTES.initialised, 'true');

    root.addEventListener('input', event => handleChange(event, root, options));
    root.addEventListener('change', event => handleChange(event, root, options));
    root.addEventListener('click', event => {
        handleClick(event, root, options);
    });

    applyFilters(root);

    if (options.refreshRelatedOnInit === true || root.dataset.refreshRelatedOnInit === 'true') {
        refreshRelatedPanels(root, root, options, {silent: true});
    }

    dispatchEvent(root, 'initialised', {
        options,
    });
};

/**
 * Initialise UCKK archive Kristal UI.
 *
 * Recommended PHP:
 * $PAGE->requires->js_call_amd('mod_uckkarchive/kristal', 'init', [$uniqid]);
 *
 * Recommended Mustache:
 * {{#js}}
 * require(['mod_uckkarchive/kristal'], function(Kristal) {
 *     Kristal.init('{{uniqid}}');
 * });
 * {{/js}}
 *
 * @param {String|null} rootId Optional root element id.
 * @param {Object} options Runtime options.
 */
export const init = (rootId = null, options = {}) => {
    const roots = rootId
        ? [document.getElementById(rootId)].filter(Boolean)
        : Array.from(document.querySelectorAll(SELECTORS.root));

    roots.forEach(root => initialiseRoot(root, options));
};

/**
 * Public helper to refresh Kristals.
 *
 * @param {String} rootId Root element id.
 * @param {Object} options Runtime options.
 * @returns {Promise<void>}
 */
export const refresh = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return refreshKristals(root, options);
};

/**
 * Public helper to save the current Kristal draft.
 *
 * @param {String} rootId Root element id.
 * @param {Object} options Runtime options.
 * @returns {Promise<void>}
 */
export const save = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return saveDraft(root, options);
};

/**
 * Public helper to reapply filters.
 *
 * @param {String} rootId Root element id.
 */
export const filter = rootId => {
    const root = document.getElementById(rootId);

    if (root) {
        applyFilters(root);
    }
};

/**
 * Public helper to refresh related Kristal media/advisory/external-work panels.
 *
 * @param {String} rootId Root element id.
 * @param {Object} options Runtime options.
 * @returns {Promise<void>}
 */
export const refreshRelated = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return refreshRelatedPanels(root, root, options);
};

