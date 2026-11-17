/**
 * Archive interactions for mod_uckkarchive.
 *
 * This module is intentionally UI-only:
 * - filters archive item lists;
 * - refreshes item cards and provenance panels;
 * - previews export packages;
 * - opens media library entry points;
 * - refreshes media/advisory/external-work panels when present;
 * - dispatches declared AJAX actions;
 * - displays accessible status messages.
 *
 * It must not validate archive records, revise archive history, expose
 * restricted items, export files authoritatively, open integrity cases, or
 * replace server-side capability checks.
 *
 * @module     mod_uckkarchive/archive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

import Ajax from 'core/ajax';
import Notification from 'core/notification';
import Templates from 'core/templates';
import {getString} from 'core/str';

const COMPONENT = 'uckkarchive';

const DEFAULT_METHODS = {
    getArchiveItems: 'mod_uckkarchive_get_archive_items',
    getArchiveItemCard: 'mod_uckkarchive_get_archive_item_card',
    getProvenancePanel: 'mod_uckkarchive_get_provenance_panel',
    getExportPreview: 'mod_uckkarchive_get_export_preview',
    exportItems: 'mod_uckkarchive_export_items',
    getExportStatus: 'mod_uckkarchive_get_export_status',

    searchMedia: 'mod_uckkarchive_search_media',
    getMediaCard: 'mod_uckkarchive_get_media_card',
    getMediaCollections: 'mod_uckkarchive_get_media_collections',
    getMediaCollection: 'mod_uckkarchive_get_media_collection',
    getMediaVersions: 'mod_uckkarchive_get_media_versions',

    getContentMarkers: 'mod_uckkarchive_get_content_markers',
    getContentTags: 'mod_uckkarchive_get_content_tags',
    getContentTagSets: 'mod_uckkarchive_get_content_tag_sets',

    getExternalWorks: 'mod_uckkarchive_get_external_works',
    getExternalWork: 'mod_uckkarchive_get_external_work',
};

const SELECTORS = {
    root: '[data-region="uckkarchive"]',
    status: '[data-region="uckkarchive-status"]',
    content: '[data-region="uckkarchive-content"]',

    itemList: '[data-region="uckkarchive-item-list"]',
    itemCard: '[data-region="uckkarchive-item-card"]',
    provenancePanel: '[data-region="uckkarchive-provenance-panel"]',
    exportPreview: '[data-region="uckkarchive-export-preview"]',

    mediaPanel: '[data-region="uckkarchive-media-panel"]',
    mediaList: '[data-region="uckkarchive-media-list"]',
    mediaCard: '[data-region="uckkarchive-media-card"]',
    mediaCollectionList: '[data-region="uckkarchive-media-collection-list"]',
    mediaCollection: '[data-region="uckkarchive-media-collection"]',
    mediaVersionList: '[data-region="uckkarchive-media-version-list"]',

    contentAdvisoryPanel: '[data-region="uckkarchive-content-advisory-panel"]',
    contentMarkerList: '[data-region="uckkarchive-content-marker-list"]',
    contentTagList: '[data-region="uckkarchive-content-tag-list"]',
    contentTagSetList: '[data-region="uckkarchive-content-tag-set-list"]',

    externalWorkPanel: '[data-region="uckkarchive-external-work-panel"]',
    externalWorkList: '[data-region="uckkarchive-external-work-list"]',
    externalWorkCard: '[data-region="uckkarchive-external-work-card"]',

    filterForm: '[data-region="uckkarchive-filter-form"]',
    search: '[data-field="archive-search"]',
    itemType: '[data-field="archive-itemtype"]',
    statusFilter: '[data-field="archive-status"]',
    validationState: '[data-field="archive-validationstate"]',
    visibility: '[data-field="archive-visibility"]',
    provenance: '[data-field="archive-provenance"]',
    sort: '[data-field="archive-sort"]',

    mediaSearch: '[data-field="media-search"]',
    mediaType: '[data-field="media-type"]',
    mediaStatus: '[data-field="media-status"]',
    mediaVisibility: '[data-field="media-visibility"]',
    mediaSort: '[data-field="media-sort"]',

    itemSelector: '[data-field="archive-item-select"]',
    mediaSelector: '[data-field="media-select"]',
    selectAll: '[data-action="uckkarchive-select-all"]',
    selectAllMedia: '[data-action="uckkarchive-select-all-media"]',

    refresh: '[data-action="uckkarchive-refresh"]',
    refreshMedia: '[data-action="uckkarchive-refresh-media"]',
    refreshAdvisories: '[data-action="uckkarchive-refresh-advisories"]',
    refreshExternalWorks: '[data-action="uckkarchive-refresh-external-works"]',

    applyFilters: '[data-action="uckkarchive-apply-filters"]',
    resetFilters: '[data-action="uckkarchive-reset-filters"]',

    loadItem: '[data-action="uckkarchive-load-item"]',
    loadMedia: '[data-action="uckkarchive-load-media"]',
    loadCollection: '[data-action="uckkarchive-load-collection"]',
    loadExternalWork: '[data-action="uckkarchive-load-external-work"]',
    loadContentAdvisory: '[data-action="uckkarchive-load-content-advisory"]',

    toggleProvenance: '[data-action="uckkarchive-toggle-provenance"]',
    toggleRegion: '[data-action="uckkarchive-toggle-region"]',

    previewExport: '[data-action="uckkarchive-preview-export"]',
    exportSelected: '[data-action="uckkarchive-export-selected"]',

    serviceAction: '[data-action="uckkarchive-service-action"]',
};

const CLASSES = {
    active: 'is-active',
    loading: 'is-loading',
    loaded: 'is-loaded',
    dirty: 'is-dirty',
    error: 'has-error',
    hidden: 'd-none',
    selected: 'is-selected',
    expanded: 'is-expanded',
};

const ATTRIBUTES = {
    initialised: 'data-uckkarchive-initialised',
};

let filterTimers = new WeakMap();

/**
 * Get a numeric dataset value.
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
 * Set accessible status text.
 *
 * @param {HTMLElement} root Archive root.
 * @param {String} message Message.
 */
const setStatus = (root, message) => {
    const status = root.querySelector(SELECTORS.status);

    if (status) {
        status.textContent = message;
    }
};

/**
 * Return external method names for this root.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 * @returns {Object}
 */
const getMethods = (root, options = {}) => {
    return {
        getArchiveItems: root.dataset.getItemsMethod || options.getItemsMethod || DEFAULT_METHODS.getArchiveItems,
        getArchiveItemCard: root.dataset.getCardMethod || options.getCardMethod || DEFAULT_METHODS.getArchiveItemCard,
        getProvenancePanel: root.dataset.getProvenanceMethod || options.getProvenanceMethod ||
            DEFAULT_METHODS.getProvenancePanel,
        getExportPreview: root.dataset.getExportPreviewMethod || options.getExportPreviewMethod ||
            DEFAULT_METHODS.getExportPreview,
        exportItems: root.dataset.exportItemsMethod || options.exportItemsMethod || DEFAULT_METHODS.exportItems,
        getExportStatus: root.dataset.getExportStatusMethod || options.getExportStatusMethod ||
            DEFAULT_METHODS.getExportStatus,

        searchMedia: root.dataset.searchMediaMethod || options.searchMediaMethod || DEFAULT_METHODS.searchMedia,
        getMediaCard: root.dataset.getMediaCardMethod || options.getMediaCardMethod || DEFAULT_METHODS.getMediaCard,
        getMediaCollections: root.dataset.getMediaCollectionsMethod || options.getMediaCollectionsMethod ||
            DEFAULT_METHODS.getMediaCollections,
        getMediaCollection: root.dataset.getMediaCollectionMethod || options.getMediaCollectionMethod ||
            DEFAULT_METHODS.getMediaCollection,
        getMediaVersions: root.dataset.getMediaVersionsMethod || options.getMediaVersionsMethod ||
            DEFAULT_METHODS.getMediaVersions,

        getContentMarkers: root.dataset.getContentMarkersMethod || options.getContentMarkersMethod ||
            DEFAULT_METHODS.getContentMarkers,
        getContentTags: root.dataset.getContentTagsMethod || options.getContentTagsMethod ||
            DEFAULT_METHODS.getContentTags,
        getContentTagSets: root.dataset.getContentTagSetsMethod || options.getContentTagSetsMethod ||
            DEFAULT_METHODS.getContentTagSets,

        getExternalWorks: root.dataset.getExternalWorksMethod || options.getExternalWorksMethod ||
            DEFAULT_METHODS.getExternalWorks,
        getExternalWork: root.dataset.getExternalWorkMethod || options.getExternalWorkMethod ||
            DEFAULT_METHODS.getExternalWork,
    };
};

/**
 * Build base service arguments.
 *
 * @param {HTMLElement} root Archive root.
 * @returns {Object}
 */
const getBaseArgs = root => {
    return {
        cmid: getNumberData(root, 'cmid'),
        archiveid: getNumberData(root, 'archiveid'),
        contextid: getNumberData(root, 'contextid'),
        sesskey: M.cfg.sesskey,
    };
};

/**
 * Check whether base identifiers are usable.
 *
 * @param {Object} args Ajax args.
 * @returns {Boolean}
 */
const hasRequiredIdentifiers = args => {
    return Boolean(args.cmid || args.archiveid);
};

/**
 * Collect current archive filter values.
 *
 * @param {HTMLElement} root Archive root.
 * @returns {Object}
 */
const collectFilters = root => {
    return {
        search: getFieldValue(root, SELECTORS.search),
        itemtype: getFieldValue(root, SELECTORS.itemType),
        status: getFieldValue(root, SELECTORS.statusFilter),
        validationstate: getFieldValue(root, SELECTORS.validationState),
        visibility: getFieldValue(root, SELECTORS.visibility),
        provenance: getFieldValue(root, SELECTORS.provenance),
        sort: getFieldValue(root, SELECTORS.sort),
    };
};

/**
 * Collect current media filter values.
 *
 * @param {HTMLElement} root Archive root.
 * @returns {Object}
 */
const collectMediaFilters = root => {
    return {
        search: getFieldValue(root, SELECTORS.mediaSearch),
        mediatype: getFieldValue(root, SELECTORS.mediaType),
        status: getFieldValue(root, SELECTORS.mediaStatus),
        visibility: getFieldValue(root, SELECTORS.mediaVisibility),
        sort: getFieldValue(root, SELECTORS.mediaSort),
    };
};

/**
 * Get a single field value.
 *
 * @param {HTMLElement} root Archive root.
 * @param {String} selector Field selector.
 * @returns {String}
 */
const getFieldValue = (root, selector) => {
    const field = root.querySelector(selector);

    if (!field) {
        return '';
    }

    return String(field.value ?? '').trim();
};

/**
 * Collect selected archive item IDs.
 *
 * @param {HTMLElement} root Archive root.
 * @returns {Array<Number>}
 */
const getSelectedItemIds = root => {
    return Array.from(root.querySelectorAll(SELECTORS.itemSelector))
        .filter(field => field.checked)
        .map(field => Number(field.value || field.dataset.itemid || 0))
        .filter(value => Number.isFinite(value) && value > 0);
};

/**
 * Collect selected media IDs.
 *
 * @param {HTMLElement} root Archive root.
 * @returns {Array<Number>}
 */
const getSelectedMediaIds = root => {
    return Array.from(root.querySelectorAll(SELECTORS.mediaSelector))
        .filter(field => field.checked)
        .map(field => Number(field.value || field.dataset.mediaid || 0))
        .filter(value => Number.isFinite(value) && value > 0);
};

/**
 * Call a Moodle Ajax service.
 *
 * @param {String} methodname Method name.
 * @param {Object} args Method args.
 * @returns {Promise<Object>}
 */
const callService = (methodname, args) => {
    return Ajax.call([{
        methodname,
        args,
    }])[0];
};

/**
 * Replace region HTML.
 *
 * @param {HTMLElement|null} region Target region.
 * @param {String} html Markup.
 * @param {String} js Template JS.
 */
const replaceRegion = (region, html, js = '') => {
    if (!region) {
        return;
    }

    Templates.replaceNodeContents(region, html, js);

    if (js) {
        Templates.runTemplateJS(js);
    }
};

/**
 * Render a service response into a region.
 *
 * @param {HTMLElement|null} region Target region.
 * @param {Object} response Service response.
 * @param {String} fallbackTemplate Template name if response has context only.
 * @returns {Promise<void>}
 */
const renderResponse = async(region, response, fallbackTemplate = '') => {
    if (!region || !response) {
        return;
    }

    if (response.html) {
        replaceRegion(region, response.html, response.js || '');
        return;
    }

    if (response.template && response.context) {
        const html = await Templates.render(response.template, response.context);
        replaceRegion(region, html, '');
        return;
    }

    if (fallbackTemplate && response.context) {
        const html = await Templates.render(fallbackTemplate, response.context);
        replaceRegion(region, html, '');
    }
};

/**
 * Show a hidden region.
 *
 * @param {HTMLElement|null} region Region.
 */
const showRegion = region => {
    if (!region) {
        return;
    }

    region.classList.remove(CLASSES.hidden);
    region.hidden = false;
};

/**
 * Toggle a region identified by a selector/id from the trigger.
 *
 * @param {HTMLElement} trigger Trigger.
 */
const toggleDeclaredRegion = trigger => {
    const selector = trigger.dataset.target || trigger.getAttribute('aria-controls');

    if (!selector) {
        return;
    }

    const target = selector.startsWith('#') ? document.querySelector(selector) : document.getElementById(selector);

    if (!target) {
        return;
    }

    const expanded = target.hidden || target.classList.contains(CLASSES.hidden);

    target.hidden = !expanded;
    target.classList.toggle(CLASSES.hidden, !expanded);
    target.classList.toggle(CLASSES.expanded, expanded);

    trigger.setAttribute('aria-expanded', expanded ? 'true' : 'false');
};

/**
 * Refresh archive item list.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const refreshArchiveItems = async(root, options = {}) => {
    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        filters: collectFilters(root),
    };

    if (!hasRequiredIdentifiers(args)) {
        return;
    }

    const list = root.querySelector(SELECTORS.itemList) || root.querySelector(SELECTORS.content);

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('archive:refreshing', COMPONENT));

        const response = await callService(methods.getArchiveItems, args);

        await renderResponse(list, response, 'mod_uckkarchive/archive_view');

        root.classList.add(CLASSES.loaded);
        setStatus(root, await getString('archive:refreshed', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('archive:refreshfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Refresh media list when a media region exists inside the archive page.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const refreshMediaList = async(root, options = {}) => {
    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        filters: collectMediaFilters(root),
    };

    if (!hasRequiredIdentifiers(args)) {
        return;
    }

    const list = root.querySelector(SELECTORS.mediaList) || root.querySelector(SELECTORS.mediaPanel);

    if (!list) {
        return;
    }

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('media:refreshing', COMPONENT));

        const response = await callService(methods.searchMedia, args);

        await renderResponse(list, response, 'mod_uckkarchive/media_library');

        root.classList.add(CLASSES.loaded);
        setStatus(root, await getString('media:refreshed', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('media:refreshfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Refresh media collections when a collection region exists.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const refreshMediaCollections = async(root, options = {}) => {
    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
    };

    const region = root.querySelector(SELECTORS.mediaCollectionList);

    if (!region || !hasRequiredIdentifiers(args)) {
        return;
    }

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('mediacollections:refreshing', COMPONENT));

        const response = await callService(methods.getMediaCollections, args);

        await renderResponse(region, response, 'mod_uckkarchive/media_collection');

        setStatus(root, await getString('mediacollections:refreshed', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('mediacollections:refreshfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Refresh external works when a region exists.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const refreshExternalWorks = async(root, options = {}) => {
    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        filters: {
            search: getFieldValue(root, '[data-field="external-work-search"]'),
            worktype: getFieldValue(root, '[data-field="external-work-type"]'),
            status: getFieldValue(root, '[data-field="external-work-status"]'),
            visibility: getFieldValue(root, '[data-field="external-work-visibility"]'),
        },
    };

    const region = root.querySelector(SELECTORS.externalWorkList) || root.querySelector(SELECTORS.externalWorkPanel);

    if (!region || !hasRequiredIdentifiers(args)) {
        return;
    }

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('externalworks:refreshing', COMPONENT));

        const response = await callService(methods.getExternalWorks, args);

        await renderResponse(region, response, 'mod_uckkarchive/external_work_card');

        setStatus(root, await getString('externalworks:refreshed', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('externalworks:refreshfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Load one archive item card.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Number} itemid Archive item id.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const loadArchiveItemCard = async(root, itemid, options = {}) => {
    if (!itemid) {
        return;
    }

    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        itemid,
    };

    const cardRegion = root.querySelector(SELECTORS.itemCard);

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('archiveitem:loading', COMPONENT));

        const response = await callService(methods.getArchiveItemCard, args);

        await renderResponse(cardRegion, response, 'mod_uckkarchive/archive_item_card');

        markActiveArchiveItem(root, itemid);
        setStatus(root, await getString('archiveitem:loaded', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('archiveitem:loadfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Load one media card.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Number} mediaid Media id.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const loadMediaCard = async(root, mediaid, options = {}) => {
    if (!mediaid) {
        return;
    }

    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        mediaid,
    };

    const cardRegion = root.querySelector(SELECTORS.mediaCard) || root.querySelector(SELECTORS.mediaPanel);

    if (!cardRegion) {
        return;
    }

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('media:loading', COMPONENT));

        const response = await callService(methods.getMediaCard, args);

        await renderResponse(cardRegion, response, 'mod_uckkarchive/media_card');

        markActiveMedia(root, mediaid);
        showRegion(cardRegion);
        setStatus(root, await getString('media:loaded', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('media:loadfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Load one media collection.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Number} collectionid Collection id.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const loadMediaCollection = async(root, collectionid, options = {}) => {
    if (!collectionid) {
        return;
    }

    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        collectionid,
    };

    const region = root.querySelector(SELECTORS.mediaCollection) || root.querySelector(SELECTORS.mediaCollectionList);

    if (!region) {
        return;
    }

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('mediacollection:loading', COMPONENT));

        const response = await callService(methods.getMediaCollection, args);

        await renderResponse(region, response, 'mod_uckkarchive/media_collection');

        showRegion(region);
        setStatus(root, await getString('mediacollection:loaded', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('mediacollection:loadfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Load media versions for one media record.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Number} mediaid Media id.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const loadMediaVersions = async(root, mediaid, options = {}) => {
    if (!mediaid) {
        return;
    }

    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        mediaid,
    };

    const region = root.querySelector(SELECTORS.mediaVersionList);

    if (!region) {
        return;
    }

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('mediaversions:loading', COMPONENT));

        const response = await callService(methods.getMediaVersions, args);

        await renderResponse(region, response, 'mod_uckkarchive/media_version_list');

        showRegion(region);
        setStatus(root, await getString('mediaversions:loaded', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('mediaversions:loadfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Load provenance panel for one archive item.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Number} itemid Archive item id.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const loadProvenancePanel = async(root, itemid, options = {}) => {
    if (!itemid) {
        return;
    }

    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        itemid,
    };

    const panel = root.querySelector(SELECTORS.provenancePanel);

    if (!panel) {
        return;
    }

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('provenance:loading', COMPONENT));

        const response = await callService(methods.getProvenancePanel, args);

        await renderResponse(panel, response, 'mod_uckkarchive/provenance_panel');

        showRegion(panel);
        setStatus(root, await getString('provenance:loaded', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('provenance:loadfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Load content advisory markers for a target.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} target Target descriptor.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const loadContentAdvisoryPanel = async(root, target = {}, options = {}) => {
    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        targettype: target.targettype || root.dataset.targetType || '',
        targetid: Number(target.targetid || root.dataset.targetId || 0),
        mediaid: Number(target.mediaid || 0),
        externalworkid: Number(target.externalworkid || 0),
    };

    const panel = root.querySelector(SELECTORS.contentAdvisoryPanel) ||
        root.querySelector(SELECTORS.contentMarkerList);

    if (!panel || !hasRequiredIdentifiers(args)) {
        return;
    }

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('contentadvisory:loading', COMPONENT));

        const response = await callService(methods.getContentMarkers, args);

        await renderResponse(panel, response, 'mod_uckkarchive/content_advisory_panel');

        showRegion(panel);
        setStatus(root, await getString('contentadvisory:loaded', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('contentadvisory:loadfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Load one external work card.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Number} externalworkid External work id.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const loadExternalWorkCard = async(root, externalworkid, options = {}) => {
    if (!externalworkid) {
        return;
    }

    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        externalworkid,
    };

    const region = root.querySelector(SELECTORS.externalWorkCard) ||
        root.querySelector(SELECTORS.externalWorkPanel);

    if (!region) {
        return;
    }

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('externalwork:loading', COMPONENT));

        const response = await callService(methods.getExternalWork, args);

        await renderResponse(region, response, 'mod_uckkarchive/external_work_card');

        showRegion(region);
        setStatus(root, await getString('externalwork:loaded', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('externalwork:loadfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Preview selected archive export.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const previewExport = async(root, options = {}) => {
    const itemids = getSelectedItemIds(root);
    const mediaids = getSelectedMediaIds(root);

    if (!itemids.length && !mediaids.length) {
        await Notification.alert(
            await getString('export:noitems:title', COMPONENT),
            await getString('export:noitems:body', COMPONENT)
        );
        return;
    }

    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        itemids,
        mediaids,
        format: root.dataset.exportFormat || 'json',
        scope: mediaids.length && !itemids.length ? 'media' : 'mixed',
    };

    const region = root.querySelector(SELECTORS.exportPreview);

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('export:previewloading', COMPONENT));

        const response = await callService(methods.getExportPreview, args);

        await renderResponse(region, response, '');

        showRegion(region);
        setStatus(root, await getString('export:previewloaded', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('export:previewfailed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Request export for selected items/media.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const exportSelected = async(root, options = {}) => {
    const itemids = getSelectedItemIds(root);
    const mediaids = getSelectedMediaIds(root);

    if (!itemids.length && !mediaids.length) {
        await Notification.alert(
            await getString('export:noitems:title', COMPONENT),
            await getString('export:noitems:body', COMPONENT)
        );
        return;
    }

    const confirmed = await confirmAction(
        'export:confirm:title',
        'export:confirm:body',
        'export:confirm:button'
    );

    if (!confirmed) {
        return;
    }

    const methods = getMethods(root, options);
    const args = {
        ...getBaseArgs(root),
        itemids,
        mediaids,
        format: root.dataset.exportFormat || 'json',
        scope: mediaids.length && !itemids.length ? 'media' : 'mixed',
    };

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('export:starting', COMPONENT));

        const response = await callService(methods.exportItems, args);

        if (response?.redirecturl) {
            window.location.assign(response.redirecturl);
            return;
        }

        if (response?.downloadurl) {
            window.location.assign(response.downloadurl);
            return;
        }

        await renderResponse(root.querySelector(SELECTORS.exportPreview), response, '');

        setStatus(root, await getString('export:started', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('export:failed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Dispatch a generic declared service action.
 *
 * The trigger may provide:
 * - data-method
 * - optional data-item-id
 * - optional data-media-id
 * - optional data-collection-id
 * - optional data-external-work-id
 * - optional data-content-marker-id
 * - optional data-confirm="true"
 *
 * @param {HTMLElement} root Archive root.
 * @param {HTMLElement} trigger Action trigger.
 * @returns {Promise<void>}
 */
const runServiceAction = async(root, trigger) => {
    const method = trigger.dataset.method || '';
    const itemid = getNumberData(trigger, 'itemId');
    const mediaid = getNumberData(trigger, 'mediaId');
    const collectionid = getNumberData(trigger, 'collectionId');
    const externalworkid = getNumberData(trigger, 'externalWorkId');
    const contentmarkerid = getNumberData(trigger, 'contentMarkerId');

    if (!method) {
        return;
    }

    if (trigger.dataset.confirm === 'true') {
        const confirmed = await confirmAction(
            trigger.dataset.confirmTitleKey || 'action:confirm:title',
            trigger.dataset.confirmBodyKey || 'action:confirm:body',
            trigger.dataset.confirmButtonKey || 'action:confirm:button'
        );

        if (!confirmed) {
            return;
        }
    }

    const args = {
        ...getBaseArgs(root),
        itemid,
        mediaid,
        collectionid,
        externalworkid,
        contentmarkerid,
        action: trigger.dataset.serviceAction || trigger.dataset.actionKey || '',
    };

    root.classList.add(CLASSES.loading);
    root.classList.remove(CLASSES.error);

    try {
        setStatus(root, await getString('action:running', COMPONENT));

        const response = await callService(method, args);

        if (response?.redirecturl) {
            window.location.assign(response.redirecturl);
            return;
        }

        if (response?.mediaid || mediaid) {
            await loadMediaCard(root, Number(response?.mediaid || mediaid));
        } else if (response?.externalworkid || externalworkid) {
            await loadExternalWorkCard(root, Number(response?.externalworkid || externalworkid));
        } else if (response?.collectionid || collectionid) {
            await loadMediaCollection(root, Number(response?.collectionid || collectionid));
        } else if (response?.contentmarkerid || contentmarkerid) {
            await loadContentAdvisoryPanel(root, {
                targettype: trigger.dataset.targetType || '',
                targetid: getNumberData(trigger, 'targetId'),
                mediaid,
                externalworkid,
            });
        } else if (response?.itemid || itemid) {
            await loadArchiveItemCard(root, Number(response?.itemid || itemid));
        } else {
            await refreshArchiveItems(root);
        }

        setStatus(root, await getString('action:done', COMPONENT));
    } catch (error) {
        root.classList.add(CLASSES.error);
        setStatus(root, await getString('action:failed', COMPONENT));
        Notification.exception(error);
    } finally {
        root.classList.remove(CLASSES.loading);
    }
};

/**
 * Confirm a user action.
 *
 * @param {String} titleKey Title string key.
 * @param {String} bodyKey Body string key.
 * @param {String} buttonKey Confirm button string key.
 * @returns {Promise<Boolean>}
 */
const confirmAction = async(titleKey, bodyKey, buttonKey) => {
    const [title, body, button, cancel] = await Promise.all([
        getString(titleKey, COMPONENT),
        getString(bodyKey, COMPONENT),
        getString(buttonKey, COMPONENT),
        getString('cancel', 'moodle'),
    ]);

    return new Promise(resolve => {
        Notification.confirm(
            title,
            body,
            button,
            cancel,
            () => resolve(true),
            () => resolve(false)
        );
    });
};

/**
 * Mark one archive item as active in the list.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Number} itemid Archive item id.
 */
const markActiveArchiveItem = (root, itemid) => {
    root.querySelectorAll(SELECTORS.loadItem).forEach(trigger => {
        const current = getNumberData(trigger, 'itemId');
        const active = current === itemid;

        trigger.classList.toggle(CLASSES.active, active);
        trigger.setAttribute('aria-current', active ? 'true' : 'false');
    });
};

/**
 * Mark one media item as active in the list.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Number} mediaid Media id.
 */
const markActiveMedia = (root, mediaid) => {
    root.querySelectorAll(SELECTORS.loadMedia).forEach(trigger => {
        const current = getNumberData(trigger, 'mediaId');
        const active = current === mediaid;

        trigger.classList.toggle(CLASSES.active, active);
        trigger.setAttribute('aria-current', active ? 'true' : 'false');
    });
};

/**
 * Set all visible item checkboxes.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Boolean} checked Checked state.
 */
const setAllSelections = (root, checked) => {
    root.querySelectorAll(SELECTORS.itemSelector).forEach(field => {
        if (!field.disabled) {
            field.checked = checked;
            field.closest(SELECTORS.itemCard)?.classList.toggle(CLASSES.selected, checked);
        }
    });
};

/**
 * Set all visible media checkboxes.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Boolean} checked Checked state.
 */
const setAllMediaSelections = (root, checked) => {
    root.querySelectorAll(SELECTORS.mediaSelector).forEach(field => {
        if (!field.disabled) {
            field.checked = checked;
            field.closest('[data-region="media-card"]')?.classList.toggle(CLASSES.selected, checked);
            field.closest(SELECTORS.mediaCard)?.classList.toggle(CLASSES.selected, checked);
        }
    });
};

/**
 * Schedule debounced filter refresh.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 * @param {Function} callback Refresh callback.
 */
const scheduleRefresh = (root, options = {}, callback = refreshArchiveItems) => {
    const delay = Number(options.filterDelay || root.dataset.filterDelay || 350);
    const previous = filterTimers.get(root);

    if (previous) {
        window.clearTimeout(previous);
    }

    const timer = window.setTimeout(() => {
        callback(root, options);
    }, Number.isFinite(delay) ? delay : 350);

    filterTimers.set(root, timer);
};

/**
 * Schedule debounced archive filter refresh.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 */
const scheduleFilterRefresh = (root, options = {}) => {
    scheduleRefresh(root, options, refreshArchiveItems);
};

/**
 * Schedule debounced media filter refresh.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 */
const scheduleMediaFilterRefresh = (root, options = {}) => {
    scheduleRefresh(root, options, refreshMediaList);
};

/**
 * Reset filter form.
 *
 * @param {HTMLElement} root Archive root.
 */
const resetFilters = root => {
    const form = root.querySelector(SELECTORS.filterForm);

    if (form) {
        form.reset();
    }
};

/**
 * Handle root input/change events.
 *
 * @param {Event} event Input/change event.
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 */
const handleChange = (event, root, options = {}) => {
    const target = event.target;

    if (target.closest(SELECTORS.filterForm)) {
        root.classList.add(CLASSES.dirty);

        if (target.matches(SELECTORS.mediaSearch) ||
                target.matches(SELECTORS.mediaType) ||
                target.matches(SELECTORS.mediaStatus) ||
                target.matches(SELECTORS.mediaVisibility) ||
                target.matches(SELECTORS.mediaSort)) {
            scheduleMediaFilterRefresh(root, options);
            return;
        }

        scheduleFilterRefresh(root, options);
        return;
    }

    if (target.matches(SELECTORS.itemSelector)) {
        target.closest(SELECTORS.itemCard)?.classList.toggle(CLASSES.selected, target.checked);
        return;
    }

    if (target.matches(SELECTORS.mediaSelector)) {
        target.closest('[data-region="media-card"]')?.classList.toggle(CLASSES.selected, target.checked);
        target.closest(SELECTORS.mediaCard)?.classList.toggle(CLASSES.selected, target.checked);
    }
};

/**
 * Handle click events.
 *
 * @param {MouseEvent} event Click event.
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 */
const handleClick = (event, root, options = {}) => {
    const refresh = event.target.closest(SELECTORS.refresh);

    if (refresh) {
        event.preventDefault();
        refreshArchiveItems(root, options);
        return;
    }

    const refreshMedia = event.target.closest(SELECTORS.refreshMedia);

    if (refreshMedia) {
        event.preventDefault();
        refreshMediaList(root, options);
        refreshMediaCollections(root, options);
        return;
    }

    const refreshAdvisories = event.target.closest(SELECTORS.refreshAdvisories);

    if (refreshAdvisories) {
        event.preventDefault();
        loadContentAdvisoryPanel(root, {
            targettype: refreshAdvisories.dataset.targetType || '',
            targetid: getNumberData(refreshAdvisories, 'targetId'),
            mediaid: getNumberData(refreshAdvisories, 'mediaId'),
            externalworkid: getNumberData(refreshAdvisories, 'externalWorkId'),
        }, options);
        return;
    }

    const refreshExternalWorks = event.target.closest(SELECTORS.refreshExternalWorks);

    if (refreshExternalWorks) {
        event.preventDefault();
        refreshExternalWorksList(root, options);
        return;
    }

    const applyFilters = event.target.closest(SELECTORS.applyFilters);

    if (applyFilters) {
        event.preventDefault();

        if (applyFilters.dataset.target === 'media') {
            refreshMediaList(root, options);
        } else {
            refreshArchiveItems(root, options);
        }

        return;
    }

    const reset = event.target.closest(SELECTORS.resetFilters);

    if (reset) {
        event.preventDefault();
        resetFilters(root);

        if (reset.dataset.target === 'media') {
            refreshMediaList(root, options);
        } else {
            refreshArchiveItems(root, options);
        }

        return;
    }

    const loadItem = event.target.closest(SELECTORS.loadItem);

    if (loadItem) {
        event.preventDefault();
        loadArchiveItemCard(root, getNumberData(loadItem, 'itemId'), options);
        return;
    }

    const loadMedia = event.target.closest(SELECTORS.loadMedia);

    if (loadMedia) {
        event.preventDefault();
        const mediaid = getNumberData(loadMedia, 'mediaId');
        loadMediaCard(root, mediaid, options);

        if (loadMedia.dataset.loadVersions === 'true') {
            loadMediaVersions(root, mediaid, options);
        }

        return;
    }

    const loadCollection = event.target.closest(SELECTORS.loadCollection);

    if (loadCollection) {
        event.preventDefault();
        loadMediaCollection(root, getNumberData(loadCollection, 'collectionId'), options);
        return;
    }

    const loadExternalWork = event.target.closest(SELECTORS.loadExternalWork);

    if (loadExternalWork) {
        event.preventDefault();
        loadExternalWorkCard(root, getNumberData(loadExternalWork, 'externalWorkId'), options);
        return;
    }

    const loadAdvisory = event.target.closest(SELECTORS.loadContentAdvisory);

    if (loadAdvisory) {
        event.preventDefault();
        loadContentAdvisoryPanel(root, {
            targettype: loadAdvisory.dataset.targetType || '',
            targetid: getNumberData(loadAdvisory, 'targetId'),
            mediaid: getNumberData(loadAdvisory, 'mediaId'),
            externalworkid: getNumberData(loadAdvisory, 'externalWorkId'),
        }, options);
        return;
    }

    const provenance = event.target.closest(SELECTORS.toggleProvenance);

    if (provenance) {
        event.preventDefault();
        loadProvenancePanel(root, getNumberData(provenance, 'itemId'), options);
        return;
    }

    const toggleRegion = event.target.closest(SELECTORS.toggleRegion);

    if (toggleRegion) {
        event.preventDefault();
        toggleDeclaredRegion(toggleRegion);
        return;
    }

    const selectAll = event.target.closest(SELECTORS.selectAll);

    if (selectAll) {
        event.preventDefault();
        setAllSelections(root, selectAll.dataset.checked !== 'true');
        selectAll.dataset.checked = selectAll.dataset.checked === 'true' ? 'false' : 'true';
        return;
    }

    const selectAllMedia = event.target.closest(SELECTORS.selectAllMedia);

    if (selectAllMedia) {
        event.preventDefault();
        setAllMediaSelections(root, selectAllMedia.dataset.checked !== 'true');
        selectAllMedia.dataset.checked = selectAllMedia.dataset.checked === 'true' ? 'false' : 'true';
        return;
    }

    const preview = event.target.closest(SELECTORS.previewExport);

    if (preview) {
        event.preventDefault();
        previewExport(root, options);
        return;
    }

    const exportButton = event.target.closest(SELECTORS.exportSelected);

    if (exportButton) {
        event.preventDefault();
        exportSelected(root, options);
        return;
    }

    const serviceAction = event.target.closest(SELECTORS.serviceAction);

    if (serviceAction) {
        event.preventDefault();
        runServiceAction(root, serviceAction);
    }
};

/**
 * Wrapper used by event handlers to avoid shadowing the refreshExternalWorks selector variable.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 * @returns {Promise<void>}
 */
const refreshExternalWorksList = (root, options = {}) => refreshExternalWorks(root, options);

/**
 * Initialise one archive root.
 *
 * @param {HTMLElement} root Archive root.
 * @param {Object} options Optional init options.
 */
const initialiseRoot = (root, options = {}) => {
    if (!root || root.getAttribute(ATTRIBUTES.initialised) === 'true') {
        return;
    }

    root.setAttribute(ATTRIBUTES.initialised, 'true');

    root.addEventListener('input', event => handleChange(event, root, options));
    root.addEventListener('change', event => handleChange(event, root, options));
    root.addEventListener('click', event => handleClick(event, root, options));

    if (options.refreshOnInit || root.dataset.refreshOnInit === 'true') {
        refreshArchiveItems(root, options);
    }

    if (options.refreshMediaOnInit || root.dataset.refreshMediaOnInit === 'true') {
        refreshMediaList(root, options);
    }

    if (options.refreshCollectionsOnInit || root.dataset.refreshCollectionsOnInit === 'true') {
        refreshMediaCollections(root, options);
    }

    if (options.refreshExternalWorksOnInit || root.dataset.refreshExternalWorksOnInit === 'true') {
        refreshExternalWorks(root, options);
    }
};

/**
 * Initialise archive UI.
 *
 * Recommended PHP:
 * $PAGE->requires->js_call_amd('mod_uckkarchive/archive', 'init', [$uniqid]);
 *
 * Recommended Mustache:
 * {{#js}}
 * require(['mod_uckkarchive/archive'], function(Archive) {
 *     Archive.init('{{uniqid}}');
 * });
 * {{/js}}
 *
 * @param {String|null} rootId Optional root element id.
 * @param {Object} options Optional configuration.
 */
export const init = (rootId = null, options = {}) => {
    const roots = rootId
        ? [document.getElementById(rootId)].filter(Boolean)
        : Array.from(document.querySelectorAll(SELECTORS.root));

    roots.forEach(root => initialiseRoot(root, options));
};

/**
 * Public helper to refresh archive items.
 *
 * @param {String} rootId Root element id.
 * @param {Object} options Optional configuration.
 * @returns {Promise<void>}
 */
export const refresh = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return refreshArchiveItems(root, options);
};

/**
 * Public helper to refresh media.
 *
 * @param {String} rootId Root element id.
 * @param {Object} options Optional configuration.
 * @returns {Promise<void>}
 */
export const refreshMedia = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return refreshMediaList(root, options);
};

/**
 * Public helper to refresh external works.
 *
 * @param {String} rootId Root element id.
 * @param {Object} options Optional configuration.
 * @returns {Promise<void>}
 */
export const refreshExternalWorkList = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return refreshExternalWorks(root, options);
};

/**
 * Public helper to load one archive item card.
 *
 * @param {String} rootId Root element id.
 * @param {Number} itemid Archive item id.
 * @param {Object} options Optional configuration.
 * @returns {Promise<void>}
 */
export const loadItem = (rootId, itemid, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return loadArchiveItemCard(root, Number(itemid), options);
};

/**
 * Public helper to load one media card.
 *
 * @param {String} rootId Root element id.
 * @param {Number} mediaid Media id.
 * @param {Object} options Optional configuration.
 * @returns {Promise<void>}
 */
export const loadMedia = (rootId, mediaid, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return loadMediaCard(root, Number(mediaid), options);
};

/**
 * Public helper to load content advisories.
 *
 * @param {String} rootId Root element id.
 * @param {Object} target Target descriptor.
 * @param {Object} options Optional configuration.
 * @returns {Promise<void>}
 */
export const loadContentAdvisory = (rootId, target = {}, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return loadContentAdvisoryPanel(root, target, options);
};

/**
 * Public helper to preview export for selected items/media.
 *
 * @param {String} rootId Root element id.
 * @param {Object} options Optional configuration.
 * @returns {Promise<void>}
 */
export const previewSelectedExport = (rootId, options = {}) => {
    const root = document.getElementById(rootId);

    if (!root) {
        return Promise.resolve();
    }

    return previewExport(root, options);
};