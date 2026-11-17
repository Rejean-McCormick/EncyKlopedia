/**
 * External work interactions for mod_uckkarchive.
 *
 * This module is intentionally UI-only:
 * - searches external work references;
 * - refreshes external work cards;
 * - submits create/update requests to server-side services;
 * - helps fill locator/reference fields in advisory/media forms;
 * - displays accessible status messages.
 *
 * It must not authorize access, expose restricted data, decide cultural
 * protocol access, decide export permission, copy protected external works, or
 * replace server-side capability checks.
 *
 * @module     mod_uckkarchive/external_work
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

import Ajax from 'core/ajax';
import Notification from 'core/notification';
import Templates from 'core/templates';
import {getString} from 'core/str';

const COMPONENT = 'uckkarchive';

const DEFAULT_METHODS = {
    getExternalWorks: 'mod_uckkarchive_get_external_works',
    getExternalWork: 'mod_uckkarchive_get_external_work',
    addExternalWork: 'mod_uckkarchive_add_external_work',
    updateExternalWork: 'mod_uckkarchive_update_external_work',
};

const SELECTORS = {
    root: '[data-region="uckkarchive-external-work"]',
    status: '[data-region="uckkarchive-external-work-status"]',
    searchForm: '[data-region="uckkarchive-external-work-search"]',
    createForm: '[data-region="uckkarchive-external-work-create"]',
    updateForm: '[data-region="uckkarchive-external-work-update"]',
    list: '[data-region="uckkarchive-external-work-list"]',
    card: '[data-region="uckkarchive-external-work-card"]',
    cardContainer: '[data-region="uckkarchive-external-work-card-container"]',
    empty: '[data-region="uckkarchive-external-work-empty"]',
    warnings: '[data-region="uckkarchive-external-work-warnings"]',

    cmid: '[data-field="cmid"]',
    externalWorkId: '[data-field="externalworkid"]',
    externalWorkUuid: '[data-field="externalworkuuid"]',
    query: '[data-field="external-work-query"]',
    workType: '[data-field="worktype"]',
    statusField: '[data-field="status"]',
    visibility: '[data-field="visibility"]',
    audienceSuitability: '[data-field="audiencesuitability"]',
    rightsStatus: '[data-field="rightsstatus"]',
    title: '[data-field="title"]',
    creator: '[data-field="creator"]',
    sourceUrl: '[data-field="sourceurl"]',
    identifier: '[data-field="identifier"]',
    locatorType: '[data-field="locatortype"]',
    locatorValue: '[data-field="locator"]',
    targetExternalWorkId: '[data-field="target-externalworkid"]',
    targetExternalWorkTitle: '[data-field="target-externalwork-title"]',

    actionSearch: '[data-action="uckkarchive-search-external-works"]',
    actionRefreshList: '[data-action="uckkarchive-refresh-external-works"]',
    actionResetSearch: '[data-action="uckkarchive-reset-external-work-search"]',
    actionOpenCard: '[data-action="uckkarchive-open-external-work"]',
    actionRefreshCard: '[data-action="uckkarchive-refresh-external-work"]',
    actionSelect: '[data-action="uckkarchive-select-external-work"]',
    actionCreate: '[data-action="uckkarchive-create-external-work"]',
    actionUpdate: '[data-action="uckkarchive-update-external-work"]',
    actionApplyLocator: '[data-action="uckkarchive-apply-external-work-locator"]',
    actionDismissWarning: '[data-action="uckkarchive-dismiss-external-work-warning"]',
};

const TEMPLATES = {
    card: 'mod_uckkarchive/external_work_card',
};

const DEFAULT_STATE = {
    page: 0,
    perpage: 20,
    sort: 'timemodified',
    direction: 'desc',
};

/**
 * Return merged options.
 *
 * @param {Object} options Options.
 * @returns {Object}
 */
const normaliseOptions = (options = {}) => {
    return Object.assign({}, DEFAULT_STATE, {
        methods: Object.assign({}, DEFAULT_METHODS, options.methods || {}),
        templates: Object.assign({}, TEMPLATES, options.templates || {}),
    }, options);
};

/**
 * Return root node.
 *
 * @param {String|Element} root Root id or element.
 * @returns {Element|null}
 */
const getRoot = root => {
    if (root instanceof Element) {
        return root;
    }

    if (typeof root === 'string' && root !== '') {
        return document.getElementById(root) || document.querySelector(root);
    }

    return document.querySelector(SELECTORS.root);
};

/**
 * Return first matching node.
 *
 * @param {Element} root Root element.
 * @param {String} selector Selector.
 * @returns {Element|null}
 */
const find = (root, selector) => root ? root.querySelector(selector) : null;

/**
 * Return all matching nodes.
 *
 * @param {Element} root Root element.
 * @param {String} selector Selector.
 * @returns {Element[]}
 */
const findAll = (root, selector) => root ? Array.from(root.querySelectorAll(selector)) : [];

/**
 * Return element value.
 *
 * @param {Element|null} node Node.
 * @param {String} fallback Fallback.
 * @returns {String}
 */
const valueOf = (node, fallback = '') => {
    if (!node) {
        return fallback;
    }

    if (node.type === 'checkbox') {
        return node.checked ? '1' : '0';
    }

    return typeof node.value === 'string' ? node.value.trim() : fallback;
};

/**
 * Return integer element value.
 *
 * @param {Element|null} node Node.
 * @param {Number} fallback Fallback.
 * @returns {Number}
 */
const intValueOf = (node, fallback = 0) => {
    const value = parseInt(valueOf(node, ''), 10);
    return Number.isFinite(value) ? value : fallback;
};

/**
 * Get cmid from root/form.
 *
 * @param {Element} root Root.
 * @returns {Number}
 */
const getCmid = root => {
    const explicit = root.dataset.cmid ? parseInt(root.dataset.cmid, 10) : 0;
    if (explicit > 0) {
        return explicit;
    }

    return intValueOf(find(root, SELECTORS.cmid), 0);
};

/**
 * Set status message.
 *
 * @param {Element} root Root.
 * @param {String} message Message.
 * @param {String} type Type.
 */
const setStatus = (root, message, type = 'info') => {
    const status = find(root, SELECTORS.status);
    if (!status) {
        return;
    }

    status.textContent = message;
    status.classList.remove('alert-info', 'alert-success', 'alert-warning', 'alert-danger', 'hidden');
    status.classList.add(`alert-${type}`);
    status.setAttribute('role', type === 'danger' ? 'alert' : 'status');
};

/**
 * Clear status message.
 *
 * @param {Element} root Root.
 */
const clearStatus = root => {
    const status = find(root, SELECTORS.status);
    if (!status) {
        return;
    }

    status.textContent = '';
    status.classList.add('hidden');
};

/**
 * Set loading state.
 *
 * @param {Element} root Root.
 * @param {Boolean} loading Loading.
 */
const setLoading = (root, loading) => {
    root.classList.toggle('is-loading', loading);
    root.setAttribute('aria-busy', loading ? 'true' : 'false');

    findAll(root, 'button, input, select, textarea').forEach(node => {
        if (node.dataset.disableDuringExternalWorkLoad === 'false') {
            return;
        }
        node.disabled = loading;
    });
};

/**
 * Get localized string with fallback.
 *
 * @param {String} key String key.
 * @param {String} fallback Fallback.
 * @returns {Promise<String>}
 */
const safeString = (key, fallback) => {
    return getString(key, COMPONENT).catch(() => fallback);
};

/**
 * Display exception.
 *
 * @param {Element} root Root.
 * @param {Error|Object} exception Exception.
 * @returns {Promise<void>}
 */
const displayException = (root, exception) => {
    setLoading(root, false);

    return safeString('error', 'Error')
        .then(label => {
            setStatus(root, label, 'danger');
            return Notification.exception(exception);
        });
};

/**
 * Call Moodle Ajax service.
 *
 * @param {String} methodname Method name.
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
 * Serialize a form into a plain object.
 *
 * Uses `data-field` as the preferred field name.
 *
 * @param {HTMLFormElement|Element|null} form Form.
 * @returns {Object}
 */
const serializeForm = form => {
    const data = {};

    if (!form) {
        return data;
    }

    Array.from(form.querySelectorAll('input, select, textarea')).forEach(field => {
        if (!field.name && !field.dataset.field) {
            return;
        }

        const name = field.dataset.field || field.name;

        if (field.type === 'checkbox') {
            data[name] = field.checked;
            return;
        }

        if (field.type === 'radio') {
            if (field.checked) {
                data[name] = field.value;
            }
            return;
        }

        if (field.multiple) {
            data[name] = Array.from(field.selectedOptions).map(option => option.value);
            return;
        }

        data[name] = typeof field.value === 'string' ? field.value.trim() : field.value;
    });

    return data;
};

/**
 * Remove empty values from object.
 *
 * @param {Object} data Data.
 * @returns {Object}
 */
const compact = data => {
    const result = {};

    Object.keys(data || {}).forEach(key => {
        const value = data[key];

        if (value === null || typeof value === 'undefined') {
            return;
        }

        if (typeof value === 'string' && value.trim() === '') {
            return;
        }

        result[key] = value;
    });

    return result;
};

/**
 * Collect search filters.
 *
 * @param {Element} root Root.
 * @returns {Object}
 */
const collectSearch = root => {
    const form = find(root, SELECTORS.searchForm);
    const data = serializeForm(form);

    return {
        cmid: getCmid(root),
        query: data['external-work-query'] || data.query || valueOf(find(root, SELECTORS.query)),
        filters: compact({
            worktype: data.worktype || valueOf(find(root, SELECTORS.workType)),
            status: data.status || valueOf(find(root, SELECTORS.statusField)),
            visibility: data.visibility || valueOf(find(root, SELECTORS.visibility)),
            audiencesuitability: data.audiencesuitability || valueOf(find(root, SELECTORS.audienceSuitability)),
            rightsstatus: data.rightsstatus || valueOf(find(root, SELECTORS.rightsStatus)),
            creator: data.creator || valueOf(find(root, SELECTORS.creator)),
            identifier: data.identifier || valueOf(find(root, SELECTORS.identifier)),
            sourceurl: data.sourceurl || valueOf(find(root, SELECTORS.sourceUrl)),
        }),
    };
};

/**
 * Collect external work update/create payload.
 *
 * @param {Element} root Root.
 * @param {HTMLFormElement|Element|null} form Form.
 * @returns {Object}
 */
const collectWorkPayload = (root, form) => {
    const data = serializeForm(form);

    return {
        cmid: getCmid(root),
        externalworkid: parseInt(data.externalworkid || data['externalworkid'] || 0, 10) || 0,
        externalworkuuid: data.externalworkuuid || '',
        updates: compact({
            worktype: data.worktype,
            status: data.status,
            visibility: data.visibility,
            audiencesuitability: data.audiencesuitability,
            rightsstatus: data.rightsstatus,
            title: data.title,
            subtitle: data.subtitle,
            creator: data.creator,
            publisher: data.publisher,
            publicationyear: data.publicationyear,
            language: data.language,
            sourceurl: data.sourceurl,
            identifier: data.identifier,
            identifiertype: data.identifiertype,
            citation: data.citation,
            rightsstatement: data.rightsstatement,
            licensekey: data.licensekey,
            sourcenote: data.sourcenote,
            teachingnote: data.teachingnote,
            culturalprotocolnote: data.culturalprotocolnote,
            description: data.description,
            provenanceid: data.provenanceid,
            metadata: data.metadata,
        }),
        record: compact({
            worktype: data.worktype,
            status: data.status,
            visibility: data.visibility,
            audiencesuitability: data.audiencesuitability,
            rightsstatus: data.rightsstatus,
            title: data.title,
            subtitle: data.subtitle,
            creator: data.creator,
            publisher: data.publisher,
            publicationyear: data.publicationyear,
            language: data.language,
            sourceurl: data.sourceurl,
            identifier: data.identifier,
            identifiertype: data.identifiertype,
            citation: data.citation,
            rightsstatement: data.rightsstatement,
            licensekey: data.licensekey,
            sourcenote: data.sourcenote,
            teachingnote: data.teachingnote,
            culturalprotocolnote: data.culturalprotocolnote,
            description: data.description,
            provenanceid: data.provenanceid,
            metadata: data.metadata,
        }),
        reason: data.reason || '',
    };
};

/**
 * Render warnings.
 *
 * @param {Element} root Root.
 * @param {Array} warnings Warnings.
 */
const renderWarnings = (root, warnings = []) => {
    const region = find(root, SELECTORS.warnings);
    if (!region) {
        return;
    }

    region.innerHTML = '';

    if (!warnings.length) {
        region.classList.add('hidden');
        return;
    }

    region.classList.remove('hidden');

    warnings.forEach(warning => {
        const item = document.createElement('div');
        item.className = 'alert alert-warning';
        item.setAttribute('role', 'alert');
        item.dataset.warningCode = warning.warningcode || '';
        item.textContent = warning.message || warning.warningcode || '';
        region.appendChild(item);
    });
};

/**
 * Render an external work card.
 *
 * @param {Element} root Root.
 * @param {Object} record Record.
 * @param {Object} options Options.
 * @returns {Promise<void>}
 */
const renderCard = (root, record, options) => {
    const container = find(root, SELECTORS.cardContainer) || find(root, SELECTORS.card);
    if (!container) {
        return Promise.resolve();
    }

    return Templates.render(options.templates.card, record)
        .then(html => Templates.replaceNodeContents(container, html, ''))
        .catch(() => {
            container.innerHTML = fallbackCard(record);
        });
};

/**
 * Basic fallback card when template is unavailable.
 *
 * @param {Object} record Record.
 * @returns {String}
 */
const fallbackCard = record => {
    const title = escapeHtml(record.title || '');
    const creator = escapeHtml(record.creator || '');
    const citation = escapeHtml(record.citation || '');
    const type = escapeHtml(record.worktype || '');

    return [
        '<article class="uckkarchive-external-work-card" data-region="uckkarchive-external-work-card"',
        ` data-externalworkid="${Number(record.id || 0)}">`,
        `<h4>${title}</h4>`,
        creator ? `<p>${creator}</p>` : '',
        type ? `<span class="badge badge-secondary">${type}</span>` : '',
        citation ? `<p>${citation}</p>` : '',
        '</article>',
    ].join('');
};

/**
 * Escape HTML.
 *
 * @param {String} value Value.
 * @returns {String}
 */
const escapeHtml = value => {
    const div = document.createElement('div');
    div.textContent = value;
    return div.innerHTML;
};

/**
 * Refresh external work list.
 *
 * @param {Element} root Root.
 * @param {Object} options Options.
 * @returns {Promise<Object>}
 */
const refreshList = (root, options = {}) => {
    options = normaliseOptions(options);
    const search = collectSearch(root);

    setLoading(root, true);

    return safeString('loading', 'Loading')
        .then(message => setStatus(root, message, 'info'))
        .then(() => call(options.methods.getExternalWorks, {
            cmid: search.cmid,
            query: search.query || '',
            filters: search.filters || {},
            page: options.page,
            perpage: options.perpage,
            sort: options.sort,
            direction: options.direction,
        }))
        .then(response => {
            setLoading(root, false);
            clearStatus(root);
            renderWarnings(root, response.warnings || []);
            renderList(root, response.records || response.externalworks || response.works || [], options);
            return response;
        })
        .catch(exception => displayException(root, exception));
};

/**
 * Render list of external works.
 *
 * @param {Element} root Root.
 * @param {Array} records Records.
 * @param {Object} options Options.
 */
const renderList = (root, records = [], options = {}) => {
    const list = find(root, SELECTORS.list);
    const empty = find(root, SELECTORS.empty);

    if (!list) {
        return;
    }

    list.innerHTML = '';

    if (!records.length) {
        if (empty) {
            empty.classList.remove('hidden');
        }
        return;
    }

    if (empty) {
        empty.classList.add('hidden');
    }

    records.forEach(record => {
        const item = document.createElement('li');
        item.className = 'uckkarchive-external-work-list__item';
        item.dataset.externalworkid = record.id || record.externalworkid || '';

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-link uckkarchive-external-work-list__button';
        button.dataset.action = 'uckkarchive-open-external-work';
        button.dataset.externalworkid = record.id || record.externalworkid || '';
        button.textContent = record.title || record.citation || record.identifier || '';

        item.appendChild(button);

        if (record.creator) {
            const creator = document.createElement('span');
            creator.className = 'uckkarchive-external-work-list__creator';
            creator.textContent = ` ${record.creator}`;
            item.appendChild(creator);
        }

        list.appendChild(item);
    });

    root.dispatchEvent(new CustomEvent('uckkarchive:externalworklistupdated', {
        bubbles: true,
        detail: {
            records,
            options,
        },
    }));
};

/**
 * Refresh one external work card.
 *
 * @param {Element} root Root.
 * @param {Number} externalWorkId External work id.
 * @param {Object} options Options.
 * @returns {Promise<Object>}
 */
const refreshCard = (root, externalWorkId, options = {}) => {
    options = normaliseOptions(options);
    externalWorkId = parseInt(externalWorkId, 10) || 0;

    if (externalWorkId <= 0) {
        return Promise.resolve({});
    }

    setLoading(root, true);

    return call(options.methods.getExternalWork, {
        cmid: getCmid(root),
        externalworkid: externalWorkId,
    })
        .then(response => {
            setLoading(root, false);
            renderWarnings(root, response.warnings || []);

            const record = response.record || response.externalwork || response;
            return renderCard(root, record, options).then(() => {
                root.dispatchEvent(new CustomEvent('uckkarchive:externalworkloaded', {
                    bubbles: true,
                    detail: {
                        externalwork: record,
                    },
                }));

                return response;
            });
        })
        .catch(exception => displayException(root, exception));
};

/**
 * Create external work.
 *
 * @param {Element} root Root.
 * @param {Object} options Options.
 * @returns {Promise<Object>}
 */
const createWork = (root, options = {}) => {
    options = normaliseOptions(options);
    const form = find(root, SELECTORS.createForm);
    const payload = collectWorkPayload(root, form);

    setLoading(root, true);

    return call(options.methods.addExternalWork, {
        cmid: payload.cmid,
        record: payload.record,
        reason: payload.reason,
    })
        .then(response => {
            setLoading(root, false);
            renderWarnings(root, response.warnings || []);

            return safeString('externalworkcreated', 'External work created')
                .then(message => setStatus(root, message, 'success'))
                .then(() => {
                    const record = response.record || response.externalwork || {};
                    if (record.id) {
                        return renderCard(root, record, options);
                    }
                    return refreshList(root, options);
                })
                .then(() => response);
        })
        .catch(exception => displayException(root, exception));
};

/**
 * Update external work.
 *
 * @param {Element} root Root.
 * @param {Object} options Options.
 * @returns {Promise<Object>}
 */
const updateWork = (root, options = {}) => {
    options = normaliseOptions(options);
    const form = find(root, SELECTORS.updateForm);
    const payload = collectWorkPayload(root, form);

    setLoading(root, true);

    return call(options.methods.updateExternalWork, {
        cmid: payload.cmid,
        externalworkid: payload.externalworkid,
        externalworkuuid: payload.externalworkuuid,
        updates: payload.updates,
        reason: payload.reason,
    })
        .then(response => {
            setLoading(root, false);
            renderWarnings(root, response.warnings || []);

            return safeString('externalworkupdated', 'External work updated')
                .then(message => setStatus(root, message, 'success'))
                .then(() => {
                    const record = response.record || response.externalwork || {};
                    if (record.id) {
                        return renderCard(root, record, options);
                    }
                    return response;
                })
                .then(() => response);
        })
        .catch(exception => displayException(root, exception));
};

/**
 * Apply selected external work to target locator/reference fields.
 *
 * @param {Element} root Root.
 * @param {Element} source Source button/element.
 */
const applyExternalWorkLocator = (root, source) => {
    const externalWorkId = source.dataset.externalworkid || '';
    const title = source.dataset.externalworktitle || source.dataset.title || '';
    const locatorType = source.dataset.locatortype || '';
    const locator = source.dataset.locator || '';

    const targetExternalWorkId = find(root, SELECTORS.targetExternalWorkId) || find(root, SELECTORS.externalWorkId);
    const targetExternalWorkTitle = find(root, SELECTORS.targetExternalWorkTitle);
    const targetLocatorType = find(root, SELECTORS.locatorType);
    const targetLocatorValue = find(root, SELECTORS.locatorValue);

    if (targetExternalWorkId) {
        targetExternalWorkId.value = externalWorkId;
        targetExternalWorkId.dispatchEvent(new Event('change', {bubbles: true}));
    }

    if (targetExternalWorkTitle) {
        targetExternalWorkTitle.value = title;
        targetExternalWorkTitle.dispatchEvent(new Event('change', {bubbles: true}));
    }

    if (targetLocatorType && locatorType) {
        targetLocatorType.value = locatorType;
        targetLocatorType.dispatchEvent(new Event('change', {bubbles: true}));
    }

    if (targetLocatorValue && locator) {
        targetLocatorValue.value = locator;
        targetLocatorValue.dispatchEvent(new Event('change', {bubbles: true}));
    }

    root.dispatchEvent(new CustomEvent('uckkarchive:externalworkselected', {
        bubbles: true,
        detail: {
            externalworkid: externalWorkId,
            title,
            locatortype: locatorType,
            locator,
        },
    }));
};

/**
 * Reset search form.
 *
 * @param {Element} root Root.
 */
const resetSearch = root => {
    const form = find(root, SELECTORS.searchForm);
    if (form && typeof form.reset === 'function') {
        form.reset();
    }

    clearStatus(root);
    renderWarnings(root, []);
};

/**
 * Handle click event.
 *
 * @param {Element} root Root.
 * @param {MouseEvent} event Event.
 * @param {Object} options Options.
 */
const handleClick = (root, event, options) => {
    const action = event.target.closest('[data-action]');
    if (!action || !root.contains(action)) {
        return;
    }

    const actionName = action.dataset.action;

    if (actionName === 'uckkarchive-search-external-works' ||
            actionName === 'uckkarchive-refresh-external-works') {
        event.preventDefault();
        refreshList(root, options);
        return;
    }

    if (actionName === 'uckkarchive-reset-external-work-search') {
        event.preventDefault();
        resetSearch(root);
        refreshList(root, options);
        return;
    }

    if (actionName === 'uckkarchive-open-external-work' ||
            actionName === 'uckkarchive-refresh-external-work') {
        event.preventDefault();
        refreshCard(root, action.dataset.externalworkid || action.value || 0, options);
        return;
    }

    if (actionName === 'uckkarchive-select-external-work' ||
            actionName === 'uckkarchive-apply-external-work-locator') {
        event.preventDefault();
        applyExternalWorkLocator(root, action);
        return;
    }

    if (actionName === 'uckkarchive-create-external-work') {
        event.preventDefault();
        createWork(root, options);
        return;
    }

    if (actionName === 'uckkarchive-update-external-work') {
        event.preventDefault();
        updateWork(root, options);
        return;
    }

    if (actionName === 'uckkarchive-dismiss-external-work-warning') {
        event.preventDefault();
        const warning = action.closest('.alert');
        if (warning) {
            warning.remove();
        }
    }
};

/**
 * Bind events.
 *
 * @param {Element} root Root.
 * @param {Object} options Options.
 */
const bindEvents = (root, options) => {
    root.addEventListener('click', event => handleClick(root, event, options));

    const searchForm = find(root, SELECTORS.searchForm);
    if (searchForm) {
        searchForm.addEventListener('submit', event => {
            event.preventDefault();
            refreshList(root, options);
        });
    }

    const createForm = find(root, SELECTORS.createForm);
    if (createForm) {
        createForm.addEventListener('submit', event => {
            event.preventDefault();
            createWork(root, options);
        });
    }

    const updateForm = find(root, SELECTORS.updateForm);
    if (updateForm) {
        updateForm.addEventListener('submit', event => {
            event.preventDefault();
            updateWork(root, options);
        });
    }
};

/**
 * Initialise one external work root.
 *
 * @param {Element} root Root.
 * @param {Object} options Options.
 */
const initialiseRoot = (root, options) => {
    if (!root || root.dataset.externalWorkInitialised === '1') {
        return;
    }

    root.dataset.externalWorkInitialised = '1';
    bindEvents(root, options);

    if (root.dataset.autoload === '1') {
        refreshList(root, options);
    }

    const initialExternalWorkId = parseInt(root.dataset.externalworkid || '0', 10);
    if (initialExternalWorkId > 0) {
        refreshCard(root, initialExternalWorkId, options);
    }
};

/**
 * Initialise module.
 *
 * @param {String|Element|null} rootId Root id, selector, element, or null.
 * @param {Object} options Options.
 */
export const init = (rootId = null, options = {}) => {
    options = normaliseOptions(options);

    if (rootId) {
        const root = getRoot(rootId);
        if (root) {
            initialiseRoot(root, options);
        }
        return;
    }

    findAll(document, SELECTORS.root).forEach(root => initialiseRoot(root, options));
};

/**
 * Public helper: refresh external work list.
 *
 * @param {String|Element} rootId Root id or element.
 * @param {Object} options Options.
 * @returns {Promise<Object>}
 */
export const refreshExternalWorks = (rootId, options = {}) => {
    const root = getRoot(rootId);
    if (!root) {
        return Promise.resolve({});
    }

    return refreshList(root, options);
};

/**
 * Public helper: refresh one external work card.
 *
 * @param {String|Element} rootId Root id or element.
 * @param {Number} externalWorkId External work id.
 * @param {Object} options Options.
 * @returns {Promise<Object>}
 */
export const refreshExternalWorkCard = (rootId, externalWorkId, options = {}) => {
    const root = getRoot(rootId);
    if (!root) {
        return Promise.resolve({});
    }

    return refreshCard(root, externalWorkId, options);
};

/**
 * Public helper: create an external work from the configured form.
 *
 * @param {String|Element} rootId Root id or element.
 * @param {Object} options Options.
 * @returns {Promise<Object>}
 */
export const createExternalWork = (rootId, options = {}) => {
    const root = getRoot(rootId);
    if (!root) {
        return Promise.resolve({});
    }

    return createWork(root, options);
};

/**
 * Public helper: update an external work from the configured form.
 *
 * @param {String|Element} rootId Root id or element.
 * @param {Object} options Options.
 * @returns {Promise<Object>}
 */
export const updateExternalWork = (rootId, options = {}) => {
    const root = getRoot(rootId);
    if (!root) {
        return Promise.resolve({});
    }

    return updateWork(root, options);
};