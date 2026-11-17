/**
 * Export interactions for mod_uckkarchive.
 *
 * This module is intentionally UI-only:
 * - collects export scope/options from the DOM;
 * - requests export preparation through declared Ajax services;
 * - refreshes export status/panel markup;
 * - exposes download links returned by the server;
 * - optionally polls pending export jobs.
 *
 * It must not decide permissions, bypass visibility, include restricted data
 * locally, validate archive records, create provenance, or generate packages
 * client-side.
 *
 * Supported scopes:
 * - archive: selected archive item export through the registered item export service;
 * - items: selected archive item export service;
 * - media: selected media export service;
 * - collection: media collection export service.
 *
 * @module     mod_uckkarchive/export
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

import Ajax from 'core/ajax';
import Notification from 'core/notification';
import Templates from 'core/templates';
import {getString} from 'core/str';

const COMPONENT = 'uckkarchive';

const SCOPES = {
    archive: 'archive',
    items: 'items',
    media: 'media',
    collection: 'collection',
};

const STATES = {
    pending: 'pending',
    queued: 'queued',
    processing: 'processing',
    complete: 'complete',
    completed: 'completed',
    ready: 'ready',
    failed: 'failed',
    blocked: 'blocked',
    cancelled: 'cancelled',
};

const DEFAULT_METHODS = {
    preview: 'mod_uckkarchive_get_export_preview',
    status: 'mod_uckkarchive_get_export_status',
    items: 'mod_uckkarchive_export_items',
    media: 'mod_uckkarchive_export_media',
    collection: 'mod_uckkarchive_export_collection',
};

const SELECTORS = {
    root: '[data-region="uckkarchive-export"]',
    form: '[data-region="uckkarchive-export-form"]',
    panel: '[data-region="uckkarchive-export-panel"]',
    status: '[data-region="uckkarchive-export-status"]',
    progress: '[data-region="uckkarchive-export-progress"]',
    progressBar: '[data-region="uckkarchive-export-progressbar"]',
    downloadRegion: '[data-region="uckkarchive-export-download"]',
    downloadLink: '[data-region="uckkarchive-export-download-link"]',
    manifestRegion: '[data-region="uckkarchive-export-manifest"]',
    manifestLink: '[data-region="uckkarchive-export-manifest-link"]',
    warningRegion: '[data-region="uckkarchive-export-warnings"]',

    scopeInput: '[data-field="export-scope"]',
    formatInput: '[data-field="export-format"]',
    visibilityInput: '[data-field="export-visibility"]',
    redactionLevelInput: '[data-field="redaction-level"]',
    descriptionInput: '[data-field="export-description"]',
    reasonInput: '[data-field="export-reason"]',

    itemIdsInput: '[data-field="itemids"]',
    mediaIdsInput: '[data-field="mediaids"]',
    collectionIdInput: '[data-field="collectionid"]',
    collectionUuidInput: '[data-field="collectionuuid"]',

    includeProofsInput: '[data-field="include-proofs"]',
    includeProvenanceInput: '[data-field="include-provenance"]',
    includeRevisionsInput: '[data-field="include-revisions"]',
    includeKristalsInput: '[data-field="include-kristals"]',
    includeRestrictedInput: '[data-field="include-restricted"]',
    includeIntegrityInput: '[data-field="include-integrity"]',
    anonymiseInput: '[data-field="anonymise-users"]',

    includeFilesInput: '[data-field="include-files"]',
    includeOriginalsInput: '[data-field="include-originals"]',
    includeDerivativesInput: '[data-field="include-derivatives"]',
    includeThumbnailsInput: '[data-field="include-thumbnails"]',
    includePreviewsInput: '[data-field="include-previews"]',
    includeCaptionsInput: '[data-field="include-captions"]',
    includeTranscriptsInput: '[data-field="include-transcripts"]',
    includeAttachmentsInput: '[data-field="include-attachments"]',
    includeVersionsInput: '[data-field="include-versions"]',
    includeRelationsInput: '[data-field="include-relations"]',
    includeTagsInput: '[data-field="include-tags"]',
    includeAdvisoriesInput: '[data-field="include-advisories"]',
    includeExternalRefsInput: '[data-field="include-external-refs"]',
    includeExternalWorksInput: '[data-field="include-external-works"]',
    includeRedactedManifestInput: '[data-field="include-redacted-manifest"]',

    actionPrepare: '[data-action="uckkarchive-prepare-export"]',
    actionRefresh: '[data-action="uckkarchive-refresh-export"]',
    actionCancel: '[data-action="uckkarchive-cancel-export"]',
    actionDownload: '[data-action="uckkarchive-download-export"]',
    actionToggleAdvanced: '[data-action="uckkarchive-toggle-export-advanced"]',
    advancedRegion: '[data-region="uckkarchive-export-advanced"]',
};

const CLASSES = {
    loading: 'is-loading',
    pending: 'is-pending',
    complete: 'is-complete',
    error: 'has-error',
    hidden: 'd-none',
};

const ATTRIBUTES = {
    initialised: 'data-uckkarchive-export-initialised',
};

const POLL_LIMIT = 60;
const POLL_INTERVAL = 3000;

let pollTimers = new WeakMap();
let pollCounts = new WeakMap();

/**
 * Get integer dataset value.
 *
 * @param {HTMLElement} element Source element.
 * @param {String} key Dataset key.
 * @param {Number} fallback Fallback value.
 * @returns {Number}
 */
const getNumberData = (element, key, fallback = 0) => {
    const value = Number(element?.dataset?.[key] ?? fallback);

    return Number.isFinite(value) ? value : fallback;
};

/**
 * Return configured Ajax method names.
 *
 * @param {HTMLElement} root Export root.
 * @param {Object} options Initialisation options.
 * @returns {Object}
 */
const getMethods = (root, options = {}) => ({
    preview: root.dataset.previewMethod || options.previewMethod || DEFAULT_METHODS.preview,
    status: root.dataset.statusMethod || options.statusMethod || DEFAULT_METHODS.status,
    items: root.dataset.itemsMethod || options.itemsMethod || DEFAULT_METHODS.items,
    media: root.dataset.mediaMethod || options.mediaMethod || DEFAULT_METHODS.media,
    collection: root.dataset.collectionMethod || options.collectionMethod || DEFAULT_METHODS.collection,
});

/**
 * Build base request arguments.
 *
 * @param {HTMLElement} root Export root.
 * @returns {Object}
 */
const getBaseArgs = root => ({
    cmid: getNumberData(root, 'cmid'),
    archiveid: getNumberData(root, 'archiveid'),
    exportid: getNumberData(root, 'exportid'),
});

/**
 * Normalise export scope.
 *
 * @param {String} scope Raw scope.
 * @returns {String}
 */
const normaliseScope = scope => {
    const value = String(scope || '').trim().toLowerCase();

    return Object.values(SCOPES).includes(value) ? value : SCOPES.archive;
};

/**
 * Normalise service state to the UI state vocabulary.
 *
 * @param {Object} response Service response.
 * @returns {String}
 */
const normaliseState = (response = {}) => {
    const value = String(response.status || response.state || '').trim().toLowerCase();

    if ([STATES.complete, STATES.completed, STATES.ready].includes(value)) {
        return STATES.complete;
    }

    if ([STATES.failed, STATES.blocked].includes(value)) {
        return STATES.failed;
    }

    if (value === STATES.cancelled) {
        return STATES.cancelled;
    }

    if ([STATES.pending, STATES.queued, STATES.processing].includes(value)) {
        return value;
    }

    return response.downloadurl ? STATES.complete : '';
};

/**
 * Validate required identifiers.
 *
 * @param {Object} args Request arguments.
 * @param {String} scope Export scope.
 * @returns {Boolean}
 */
const hasRequiredIdentifiers = (args, scope = SCOPES.archive) => {
    if (!args.cmid) {
        return false;
    }

    if ([SCOPES.media, SCOPES.items, SCOPES.collection].includes(scope)) {
        return true;
    }

    return Boolean(args.archiveid);
};

/**
 * Set local status text.
 *
 * @param {HTMLElement} root Export root.
 * @param {String} message Message.
 */
const setStatus = (root, message) => {
    const status = root.querySelector(SELECTORS.status);

    if (status) {
        status.textContent = message;
    }
};

/**
 * Show or hide loading state.
 *
 * @param {HTMLElement} root Export root.
 * @param {Boolean} loading Loading state.
 */
const setLoading = (root, loading) => {
    root.classList.toggle(CLASSES.loading, loading);

    root.querySelectorAll('button, input, select, textarea').forEach(control => {
        if (control.matches(SELECTORS.actionDownload)) {
            return;
        }

        control.disabled = loading;
    });
};

/**
 * Get value for one field.
 *
 * @param {HTMLElement|null} field Field.
 * @returns {String|Boolean}
 */
const getFieldValue = field => {
    if (!field) {
        return '';
    }

    if (field.type === 'checkbox') {
        return field.checked;
    }

    if (field.type === 'radio') {
        return field.checked ? field.value : '';
    }

    return field.value;
};

/**
 * Collect radio/select/text value from a selector.
 *
 * @param {HTMLElement} root Export root.
 * @param {String} selector Field selector.
 * @returns {String|Boolean}
 */
const collectSingleValue = (root, selector) => {
    const fields = Array.from(root.querySelectorAll(selector));

    if (!fields.length) {
        return '';
    }

    if (fields[0].type === 'radio') {
        const checked = fields.find(field => field.checked);
        return checked ? checked.value : '';
    }

    return getFieldValue(fields[0]);
};

/**
 * Collect boolean field value with a default.
 *
 * @param {HTMLElement} root Export root.
 * @param {String} selector Field selector.
 * @param {Boolean} fallback Fallback.
 * @returns {Boolean}
 */
const collectBoolean = (root, selector, fallback = false) => {
    const fields = Array.from(root.querySelectorAll(selector));

    if (!fields.length) {
        return fallback;
    }

    return Boolean(collectSingleValue(root, selector));
};

/**
 * Collect a positive integer from one selector.
 *
 * @param {HTMLElement} root Export root.
 * @param {String} selector Field selector.
 * @param {Number} fallback Fallback.
 * @returns {Number}
 */
const collectInteger = (root, selector, fallback = 0) => {
    const value = Number(collectSingleValue(root, selector) || fallback);

    return Number.isFinite(value) && value > 0 ? Math.trunc(value) : fallback;
};

/**
 * Split a comma/space separated id list.
 *
 * @param {String} value Raw value.
 * @returns {Number[]}
 */
const splitIdList = value => String(value || '')
    .split(/[,\s]+/)
    .map(id => Number(id))
    .filter(id => Number.isInteger(id) && id > 0);

/**
 * Collect ids from checkboxes, multiselects, text fields or data attributes.
 *
 * @param {HTMLElement} root Export root.
 * @param {String} selector Field selector.
 * @param {String} datasetKey Root dataset key.
 * @returns {Number[]}
 */
const collectIds = (root, selector, datasetKey) => {
    const fields = Array.from(root.querySelectorAll(selector));
    const ids = [];

    fields.forEach(field => {
        if (field.type === 'checkbox') {
            if (field.checked) {
                ids.push(...splitIdList(field.value || field.dataset.id));
            }
            return;
        }

        if (field.tagName === 'SELECT' && field.multiple) {
            Array.from(field.selectedOptions).forEach(option => {
                ids.push(...splitIdList(option.value));
            });
            return;
        }

        ids.push(...splitIdList(field.value || field.dataset.id));
    });

    ids.push(...splitIdList(root.dataset?.[datasetKey]));

    return Array.from(new Set(ids));
};

/**
 * Collect export options from the form.
 *
 * @param {HTMLElement} root Export root.
 * @returns {Object}
 */
const collectExportData = root => {
    const base = getBaseArgs(root);
    const scope = normaliseScope(collectSingleValue(root, SELECTORS.scopeInput) || root.dataset.scope);

    return {
        ...base,
        scope,
        format: String(collectSingleValue(root, SELECTORS.formatInput) || root.dataset.format || 'json'),
        visibility: String(collectSingleValue(root, SELECTORS.visibilityInput) || root.dataset.visibility || 'course'),
        redactionlevel: String(
            collectSingleValue(root, SELECTORS.redactionLevelInput) ||
            root.dataset.redactionLevel ||
            'standard'
        ),
        description: String(collectSingleValue(root, SELECTORS.descriptionInput) || ''),
        reason: String(collectSingleValue(root, SELECTORS.reasonInput) || ''),

        itemids: collectIds(root, SELECTORS.itemIdsInput, 'itemids'),
        mediaids: collectIds(root, SELECTORS.mediaIdsInput, 'mediaids'),
        collectionid: collectInteger(root, SELECTORS.collectionIdInput, getNumberData(root, 'collectionid')),
        collectionuuid: String(collectSingleValue(root, SELECTORS.collectionUuidInput) || root.dataset.collectionuuid || ''),

        includeproofs: collectBoolean(root, SELECTORS.includeProofsInput, true),
        includeprovenance: collectBoolean(root, SELECTORS.includeProvenanceInput, true),
        includerevisions: collectBoolean(root, SELECTORS.includeRevisionsInput, true),
        includekristals: collectBoolean(root, SELECTORS.includeKristalsInput, true),
        includerestricted: collectBoolean(root, SELECTORS.includeRestrictedInput, false),
        includeintegrity: collectBoolean(root, SELECTORS.includeIntegrityInput, false),
        anonymiseusers: collectBoolean(root, SELECTORS.anonymiseInput, false),

        includefiles: collectBoolean(root, SELECTORS.includeFilesInput, true),
        includeoriginals: collectBoolean(root, SELECTORS.includeOriginalsInput, true),
        includederivatives: collectBoolean(root, SELECTORS.includeDerivativesInput, true),
        includethumbnails: collectBoolean(root, SELECTORS.includeThumbnailsInput, true),
        includepreviews: collectBoolean(root, SELECTORS.includePreviewsInput, true),
        includecaptions: collectBoolean(root, SELECTORS.includeCaptionsInput, true),
        includetranscripts: collectBoolean(root, SELECTORS.includeTranscriptsInput, true),
        includeattachments: collectBoolean(root, SELECTORS.includeAttachmentsInput, true),
        includeversions: collectBoolean(root, SELECTORS.includeVersionsInput, true),
        includerelations: collectBoolean(root, SELECTORS.includeRelationsInput, true),
        includetags: collectBoolean(root, SELECTORS.includeTagsInput, true),
        includeadvisories: collectBoolean(root, SELECTORS.includeAdvisoriesInput, true),
        includeexternalrefs: collectBoolean(root, SELECTORS.includeExternalRefsInput, true),
        includeexternalworks: collectBoolean(root, SELECTORS.includeExternalWorksInput, true),
        includeredactedmanifest: collectBoolean(root, SELECTORS.includeRedactedManifestInput, true),
    };
};

/**
 * Build service arguments for the selected scope.
 *
 * Only registered Moodle external services are used:
 * - mod_uckkarchive_export_items
 * - mod_uckkarchive_export_media
 * - mod_uckkarchive_export_collection
 *
 * The legacy `archive` scope is treated as an item export and therefore
 * requires selected item ids. A full-archive prepare service must be added
 * server-side before the UI can call one.
 *
 * @param {Object} data Collected export data.
 * @returns {Object}
 */
const buildServiceArgs = data => {
    if (data.scope === SCOPES.media) {
        return {
            cmid: data.cmid,
            mediaids: data.mediaids,
            format: data.format || 'zip',
            options: {
                includeoriginals: data.includeoriginals,
                includederivatives: data.includederivatives,
                includethumbnails: data.includethumbnails,
                includepreviews: data.includepreviews,
                includecaptions: data.includecaptions,
                includetranscripts: data.includetranscripts,
                includeattachments: data.includeattachments,
                includeversions: data.includeversions,
                includerelations: data.includerelations,
                includetags: data.includetags,
                includeadvisories: data.includeadvisories,
                includeexternalrefs: data.includeexternalrefs,
                redactionlevel: data.redactionlevel,
                visibility: data.visibility,
            },
            reason: data.reason,
        };
    }

    if (data.scope === SCOPES.collection) {
        return {
            cmid: data.cmid,
            collectionid: data.collectionid,
            collectionuuid: data.collectionuuid,
            format: data.format || 'zip',
            options: {
                includefiles: data.includefiles,
                includethumbnails: data.includethumbnails,
                includepreviews: data.includepreviews,
                includederivatives: data.includederivatives,
                includeversions: data.includeversions,
                includeadvisories: data.includeadvisories,
                includeexternalworks: data.includeexternalworks,
                redactionlevel: data.redactionlevel,
                visibility: data.visibility,
            },
            reason: data.reason,
        };
    }

    return {
        cmid: data.cmid,
        itemids: data.itemids,
        exportformat: data.format || 'json',
        description: data.description,
        reason: data.reason,
        redactionlevel: data.redactionlevel,
        includeproofs: data.includeproofs,
        includeprovenance: data.includeprovenance,
        includeversions: data.includeversions,
    };
};

/**
 * Return method name for the selected scope.
 *
 * @param {Object} methods Configured method names.
 * @param {String} scope Export scope.
 * @returns {String}
 */
const methodForScope = (methods, scope) => {
    if (scope === SCOPES.media) {
        return methods.media;
    }

    if (scope === SCOPES.collection) {
        return methods.collection;
    }

    return methods.items;
};

/**
 * Call a Moodle Ajax service.
 *
 * @param {String} methodname External function name.
 * @param {Object} args External function args.
 * @returns {Promise<Object>}
 */
const callService = (methodname, args) => Ajax.call([{
    methodname,
    args,
}])[0];

/**
 * Confirm export request.
 *
 * @param {Object} data Export data.
 * @returns {Promise<Boolean>}
 */
const confirmExport = async(data) => {
    const title = await getString('confirmexport', COMPONENT);
    const restricted = data.includerestricted ||
        data.includeintegrity ||
        data.redactionlevel !== 'none' ||
        data.scope === SCOPES.media ||
        data.scope === SCOPES.collection;

    const message = restricted
        ? await getString('confirmrestrictedexportbody', COMPONENT)
        : await getString('confirmexportbody', COMPONENT);
    const confirm = await getString('exportarchive', COMPONENT);
    const cancel = await getString('cancel', 'moodle');

    return new Promise(resolve => {
        Notification.confirm(
            title,
            message,
            confirm,
            cancel,
            () => resolve(true),
            () => resolve(false)
        );
    });
};

/**
 * Validate export request client-side.
 *
 * Server-side validation remains authoritative.
 *
 * @param {HTMLElement} root Export root.
 * @param {Object} data Export data.
 * @returns {Promise<Boolean>}
 */
const validateBeforePrepare = async(root, data) => {
    if (!hasRequiredIdentifiers(data, data.scope)) {
        await Notification.alert(
            await getString('exporterror', COMPONENT),
            await getString('exportmissingidentifiers', COMPONENT)
        );
        return false;
    }

    if (data.scope === SCOPES.media && !data.mediaids.length) {
        await Notification.alert(
            await getString('exporterror', COMPONENT),
            await getString('medianotfound', COMPONENT)
        );
        return false;
    }

    if ((data.scope === SCOPES.items || data.scope === SCOPES.archive) && !data.itemids.length) {
        await Notification.alert(
            await getString('exporterror', COMPONENT),
            await getString('noitemsselected', COMPONENT)
        );
        return false;
    }

    if (data.scope === SCOPES.collection && !data.collectionid && !data.collectionuuid.trim()) {
        await Notification.alert(
            await getString('exporterror', COMPONENT),
            await getString('nomediacollections', COMPONENT)
        );
        return false;
    }

    if (!data.reason.trim() && (data.includerestricted || data.includeintegrity || data.redactionlevel === 'restricted')) {
        await Notification.alert(
            await getString('exporterror', COMPONENT),
            await getString('exportreasonrequired', COMPONENT)
        );

        const reason = root.querySelector(SELECTORS.reasonInput);
        if (reason) {
            reason.focus();
        }

        return false;
    }

    return true;
};

/**
 * Prepare export package.
 *
 * @param {HTMLElement} root Export root.
 * @param {Object} options Initialisation options.
 * @returns {Promise<void>}
 */
const prepareExport = async(root, options = {}) => {
    const methods = getMethods(root, options);
    const data = collectExportData(root);

    if (!await validateBeforePrepare(root, data)) {
        return;
    }

    if (!await confirmExport(data)) {
        return;
    }

    setLoading(root, true);
    root.classList.remove(CLASSES.error, CLASSES.complete);
    root.classList.add(CLASSES.pending);

    try {
        setStatus(root, await getString('exportpreparing', COMPONENT));

        const response = await callService(methodForScope(methods, data.scope), buildServiceArgs(data));

        applyExportResponse(root, response);

        const state = normaliseState(response);

        if (state === STATES.complete || response?.downloadurl) {
            root.classList.remove(CLASSES.pending);
            root.classList.add(CLASSES.complete);
            setStatus(root, await getString('exportready', COMPONENT));
            stopPolling(root);
            return;
        }

        if (state === STATES.failed) {
            root.classList.add(CLASSES.error);
            root.classList.remove(CLASSES.pending);
            setStatus(root, await getString('exportfailed', COMPONENT));
            stopPolling(root);
            return;
        }

        setStatus(root, await getString('exportqueued', COMPONENT));
        startPolling(root, options);
    } catch (error) {
        root.classList.add(CLASSES.error);
        root.classList.remove(CLASSES.pending);
        setStatus(root, await getString('exportfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        setLoading(root, false);
    }
};

/**
 * Refresh export status.
 *
 * @param {HTMLElement} root Export root.
 * @param {Object} options Initialisation options.
 * @returns {Promise<Object|null>}
 */
const refreshStatus = async(root, options = {}) => {
    const methods = getMethods(root, options);
    const args = getBaseArgs(root);

    if (!hasRequiredIdentifiers(args, SCOPES.archive) || !args.exportid) {
        return null;
    }

    try {
        const response = await callService(methods.status, args);
        applyExportResponse(root, response);

        const state = normaliseState(response);

        if (state === STATES.complete || response?.downloadurl) {
            root.classList.remove(CLASSES.pending);
            root.classList.add(CLASSES.complete);
            setStatus(root, await getString('exportready', COMPONENT));
            stopPolling(root);
        } else if (state === STATES.failed) {
            root.classList.add(CLASSES.error);
            root.classList.remove(CLASSES.pending);
            setStatus(root, await getString('exportfailed', COMPONENT));
            stopPolling(root);
        } else if (state === STATES.cancelled) {
            root.classList.remove(CLASSES.pending, CLASSES.complete);
            setStatus(root, await getString('exportcancelled', COMPONENT));
            stopPolling(root);
        }

        return response;
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('exportrefreshfailed', COMPONENT));
        Notification.exception(error);
        return null;
    }
};

/**
 * Refresh export panel/status using registered services only.
 *
 * If an export id is present, refresh status through
 * mod_uckkarchive_get_export_status. Otherwise, preview item/archive export
 * data through mod_uckkarchive_get_export_preview when item ids are available.
 *
 * @param {HTMLElement} root Export root.
 * @param {Object} options Initialisation options.
 * @returns {Promise<void>}
 */
const refreshPanel = async(root, options = {}) => {
    const methods = getMethods(root, options);
    const args = getBaseArgs(root);

    setLoading(root, true);

    try {
        setStatus(root, await getString('exportrefreshing', COMPONENT));

        if (args.exportid) {
            await refreshStatus(root, options);
            return;
        }

        const data = collectExportData(root);

        if ((data.scope === SCOPES.archive || data.scope === SCOPES.items) && data.itemids.length) {
            const preview = await callService(methods.preview, {
                cmid: data.cmid,
                itemids: data.itemids,
                exportformat: data.format || 'json',
                includeproofs: data.includeproofs,
                includeprovenance: data.includeprovenance,
                includeversions: data.includeversions,
            });

            applyExportResponse(root, preview);
            renderPreview(root, preview);
        }

        setStatus(root, await getString('exportrefreshed', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('exportrefreshfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        setLoading(root, false);
    }
};

/**
 * Stop local export polling.
 *
 * No cancel-export external function is registered for this component. This
 * action therefore only stops the local polling loop. Server-side cancellation
 * must be implemented and registered before this module can cancel jobs.
 *
 * @param {HTMLElement} root Export root.
 * @returns {Promise<void>}
 */
const cancelExport = async(root) => {
    stopPolling(root);
    root.classList.remove(CLASSES.pending);
    setStatus(root, await getString('exportpollingstopped', COMPONENT));
};

/**
 * Render a lightweight export preview when the registered preview service is used.
 *
 * @param {HTMLElement} root Export root.
 * @param {Object} preview Preview response.
 */
const renderPreview = (root, preview = {}) => {
    const panel = root.querySelector(SELECTORS.panel);

    if (!panel || !preview || typeof preview !== 'object') {
        return;
    }

    const list = document.createElement('dl');
    list.className = 'row uckkarchive-export__preview';

    const rows = [
        ['format', preview.format],
        ['itemcount', preview.itemcount],
        ['proofcount', preview.proofcount],
        ['provenancecount', preview.provenancecount],
        ['revisioncount', preview.revisioncount],
    ];

    rows.forEach(([key, value]) => {
        if (value === undefined || value === null || value === '') {
            return;
        }

        const term = document.createElement('dt');
        term.className = 'col-sm-4';
        term.textContent = key;

        const description = document.createElement('dd');
        description.className = 'col-sm-8';
        description.textContent = String(value);

        list.appendChild(term);
        list.appendChild(description);
    });

    panel.replaceChildren(list);
};

/**
 * Apply export response to UI.
 *
 * @param {HTMLElement} root Export root.
 * @param {Object} response Service response.
 */
const applyExportResponse = (root, response = {}) => {
    if (!response || typeof response !== 'object') {
        return;
    }

    if (response.exportid) {
        root.dataset.exportid = String(response.exportid);
    }

    if (response.exportuuid) {
        root.dataset.exportuuid = String(response.exportuuid);
    }

    const state = normaliseState(response);
    if (state) {
        root.dataset.exportStatus = state;
    }

    updateProgress(root, Number(response.progress ?? (state === STATES.complete ? 100 : 0)));

    if (response.message) {
        setStatus(root, response.message);
    }

    if (response.downloadurl) {
        showDownload(root, response.downloadurl, response.filename || '');
    }

    if (response.manifesturl) {
        showManifest(root, response.manifesturl);
    }

    if (response.manifest) {
        root.dataset.manifest = typeof response.manifest === 'string' ? response.manifest : JSON.stringify(response.manifest);
    }

    if (response.warnings) {
        showWarnings(root, response.warnings);
    }

    if (response.html) {
        replacePanel(root, response.html, response.js || '');
    }
};

/**
 * Update visual progress state.
 *
 * @param {HTMLElement} root Export root.
 * @param {Number} progress Progress percent.
 */
const updateProgress = (root, progress) => {
    if (!Number.isFinite(progress)) {
        return;
    }

    const safeProgress = Math.max(0, Math.min(100, Math.round(progress)));
    const progressRegion = root.querySelector(SELECTORS.progress);
    const progressBar = root.querySelector(SELECTORS.progressBar);

    if (progressRegion) {
        progressRegion.hidden = false;
        progressRegion.setAttribute('aria-valuenow', String(safeProgress));
    }

    if (progressBar) {
        progressBar.style.width = `${safeProgress}%`;
        progressBar.textContent = `${safeProgress}%`;
    }
};

/**
 * Display download link.
 *
 * @param {HTMLElement} root Export root.
 * @param {String} url Download URL.
 * @param {String} filename Optional filename.
 */
const showDownload = (root, url, filename = '') => {
    const region = root.querySelector(SELECTORS.downloadRegion);
    const link = root.querySelector(SELECTORS.downloadLink);

    if (region) {
        region.hidden = false;
        region.classList.remove(CLASSES.hidden);
    }

    if (link) {
        link.href = url;

        if (filename) {
            link.textContent = filename;
            link.setAttribute('download', filename);
        }
    }
};

/**
 * Display manifest link.
 *
 * @param {HTMLElement} root Export root.
 * @param {String} url Manifest URL.
 */
const showManifest = (root, url) => {
    const region = root.querySelector(SELECTORS.manifestRegion);
    const link = root.querySelector(SELECTORS.manifestLink);

    if (region) {
        region.hidden = false;
        region.classList.remove(CLASSES.hidden);
    }

    if (link) {
        link.href = url;
    }
};

/**
 * Display warning messages.
 *
 * @param {HTMLElement} root Export root.
 * @param {Array} warnings Warning rows or strings.
 */
const showWarnings = (root, warnings = []) => {
    const region = root.querySelector(SELECTORS.warningRegion);

    if (!region || !Array.isArray(warnings)) {
        return;
    }

    region.innerHTML = '';

    warnings.forEach(warning => {
        const message = typeof warning === 'string' ? warning : warning.message;

        if (!message) {
            return;
        }

        const node = document.createElement('div');
        node.className = 'alert alert-warning uckkarchive-export__warning';
        node.textContent = message;
        region.appendChild(node);
    });

    region.hidden = !region.children.length;
};

/**
 * Replace export panel contents.
 *
 * @param {HTMLElement} root Export root.
 * @param {String} html HTML.
 * @param {String} js Template JS.
 */
const replacePanel = (root, html, js = '') => {
    const panel = root.querySelector(SELECTORS.panel);

    if (!panel) {
        return;
    }

    Templates.replaceNodeContents(panel, html, js);

    if (js) {
        Templates.runTemplateJS(js);
    }

    initialiseRoot(root, {
        ...root.dataset,
        preserveInitialised: true,
    });
};

/**
 * Start polling export status.
 *
 * @param {HTMLElement} root Export root.
 * @param {Object} options Initialisation options.
 */
const startPolling = (root, options = {}) => {
    stopPolling(root);

    if (!getNumberData(root, 'exportid')) {
        return;
    }

    pollCounts.set(root, 0);

    const interval = Number(options.pollInterval || root.dataset.pollInterval || POLL_INTERVAL);

    const timer = window.setInterval(async() => {
        const count = (pollCounts.get(root) || 0) + 1;
        pollCounts.set(root, count);

        if (count > POLL_LIMIT) {
            stopPolling(root);
            setStatus(root, await getString('exportpollingstopped', COMPONENT));
            return;
        }

        await refreshStatus(root, options);
    }, Number.isFinite(interval) ? interval : POLL_INTERVAL);

    pollTimers.set(root, timer);
};

/**
 * Stop polling export status.
 *
 * @param {HTMLElement} root Export root.
 */
const stopPolling = root => {
    const timer = pollTimers.get(root);

    if (timer) {
        window.clearInterval(timer);
    }

    pollTimers.delete(root);
    pollCounts.delete(root);
};

/**
 * Toggle advanced export options.
 *
 * @param {HTMLElement} root Export root.
 * @param {HTMLElement} trigger Toggle control.
 */
const toggleAdvanced = (root, trigger) => {
    const region = root.querySelector(SELECTORS.advancedRegion);

    if (!region) {
        return;
    }

    const expanded = trigger.getAttribute('aria-expanded') === 'true';

    trigger.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    region.hidden = expanded;
    region.classList.toggle(CLASSES.hidden, expanded);
};

/**
 * Handle click events.
 *
 * @param {MouseEvent} event Click event.
 * @param {HTMLElement} root Export root.
 * @param {Object} options Initialisation options.
 */
const handleClick = (event, root, options = {}) => {
    const prepare = event.target.closest(SELECTORS.actionPrepare);

    if (prepare) {
        event.preventDefault();
        prepareExport(root, options);
        return;
    }

    const refresh = event.target.closest(SELECTORS.actionRefresh);

    if (refresh) {
        event.preventDefault();
        refreshPanel(root, options);
        return;
    }

    const cancel = event.target.closest(SELECTORS.actionCancel);

    if (cancel) {
        event.preventDefault();
        cancelExport(root, options);
        return;
    }

    const toggle = event.target.closest(SELECTORS.actionToggleAdvanced);

    if (toggle) {
        event.preventDefault();
        toggleAdvanced(root, toggle);
    }
};

/**
 * Handle form submit events.
 *
 * @param {SubmitEvent} event Submit event.
 * @param {HTMLElement} root Export root.
 * @param {Object} options Initialisation options.
 */
const handleSubmit = (event, root, options = {}) => {
    if (!event.target.matches(SELECTORS.form)) {
        return;
    }

    event.preventDefault();
    prepareExport(root, options);
};

/**
 * Initialise one root.
 *
 * @param {HTMLElement} root Export root.
 * @param {Object} options Initialisation options.
 */
const initialiseRoot = (root, options = {}) => {
    if (!root) {
        return;
    }

    if (root.getAttribute(ATTRIBUTES.initialised) === 'true' && !options.preserveInitialised) {
        return;
    }

    if (root.getAttribute(ATTRIBUTES.initialised) !== 'true') {
        root.addEventListener('click', event => handleClick(event, root, options));
        root.addEventListener('submit', event => handleSubmit(event, root, options));
        root.setAttribute(ATTRIBUTES.initialised, 'true');
    }

    if (root.dataset.autopoll === 'true') {
        startPolling(root, options);
    }
};

/**
 * Initialise archive export UI.
 *
 * Recommended PHP:
 * $PAGE->requires->js_call_amd('mod_uckkarchive/export', 'init', [$uniqid]);
 *
 * Recommended Mustache:
 * {{#js}}
 * require(['mod_uckkarchive/export'], function(Export) {
 *     Export.init('{{uniqid}}');
 * });
 * {{/js}}
 *
 * @param {String|null} rootId Optional root id.
 * @param {Object} options Optional configuration.
 */
export const init = (rootId = null, options = {}) => {
    const roots = rootId
        ? [document.getElementById(rootId)].filter(Boolean)
        : Array.from(document.querySelectorAll(SELECTORS.root));

    roots.forEach(root => initialiseRoot(root, options));
};

/**
 * Public helper to prepare an archive export.
 *
 * @param {String} rootId Root id.
 * @param {Object} options Optional configuration.
 * @returns {Promise<void>}
 */
export const prepare = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return prepareExport(root, options);
};

/**
 * Public helper to refresh archive export status.
 *
 * @param {String} rootId Root id.
 * @param {Object} options Optional configuration.
 * @returns {Promise<Object|null>}
 */
export const refreshStatusFor = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve(null);
    }

    return refreshStatus(root, options);
};

/**
 * Public helper to refresh archive export panel.
 *
 * @param {String} rootId Root id.
 * @param {Object} options Optional configuration.
 * @returns {Promise<void>}
 */
export const refresh = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return refreshPanel(root, options);
};

/**
 * Public helper to stop status polling.
 *
 * @param {String} rootId Root id.
 */
export const stop = rootId => {
    const root = document.getElementById(rootId);

    if (root) {
        stopPolling(root);
    }
};

/**
 * Public helper to collect export data for tests.
 *
 * @param {String} rootId Root id.
 * @returns {Object|null}
 */
export const collect = rootId => {
    const root = document.getElementById(rootId);

    if (!root) {
        return null;
    }

    return collectExportData(root);
};