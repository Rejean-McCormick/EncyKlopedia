/**
 * Unified media-library editor interactions for mod_uckkarchive.
 *
 * This module is UI-only. It improves navigation through the editor workflow,
 * surfaces accessible status changes, and mirrors simple form state in the
 * editor shell. It must not decide access, validate cultural restrictions,
 * approve content markers, publish media, export files, or bypass server-side
 * capability checks.
 *
 * @module     mod_uckkarchive/media_library_editor
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

const ROOT_SELECTOR = '[data-region="uckkarchive-media-library-editor"]';

const SELECTORS = {
    jump: '[data-action="uckkarchive-media-editor-jump"]',
    panel: '[data-region="media-editor-panel"]',
    notification: '[data-region="media-editor-notification"]',
    form: 'form',
    title: '[name="title"]',
    status: '[name="status"]',
    visibility: '[name="visibility"]',
    audience: '[name="audiencesuitability"]',
};

/**
 * Find the editor root.
 *
 * @param {Object} config AMD config.
 * @returns {HTMLElement|null}
 */
const getRoot = config => {
    const rootName = config && config.root ? String(config.root) : '';

    if (rootName !== '') {
        const byRegion = document.querySelector(`[data-region="${CSS.escape(rootName)}"]`);
        if (byRegion) {
            return byRegion;
        }

        const byId = document.getElementById(rootName);
        if (byId) {
            return byId;
        }
    }

    return document.querySelector(ROOT_SELECTOR);
};

/**
 * Scroll to one editor panel.
 *
 * @param {HTMLElement} root Editor root.
 * @param {string} targetId Panel id.
 */
const jumpToPanel = (root, targetId) => {
    const panel = root.querySelector(`#${CSS.escape(targetId)}`);
    if (!panel) {
        return;
    }

    panel.scrollIntoView({behavior: 'smooth', block: 'start'});
    panel.setAttribute('tabindex', '-1');
    panel.focus({preventScroll: true});
};

/**
 * Activate one workflow button.
 *
 * @param {HTMLElement} root Editor root.
 * @param {HTMLElement} button Clicked workflow button.
 */
const activateWorkflowStep = (root, button) => {
    root.querySelectorAll(SELECTORS.jump).forEach(item => {
        item.classList.remove('is-active');
        item.removeAttribute('aria-current');
    });

    button.classList.add('is-active');
    button.setAttribute('aria-current', 'step');
};

/**
 * Bind workflow navigation.
 *
 * @param {HTMLElement} root Editor root.
 */
const bindWorkflowNavigation = root => {
    root.addEventListener('click', event => {
        const button = event.target.closest(SELECTORS.jump);
        if (!button || !root.contains(button) || button.disabled) {
            return;
        }

        event.preventDefault();

        activateWorkflowStep(root, button);
        jumpToPanel(root, button.dataset.target || '');
    });
};

/**
 * Mark the editor as dirty after form changes.
 *
 * @param {HTMLElement} root Editor root.
 */
const bindDirtyState = root => {
    const form = root.querySelector(SELECTORS.form);
    if (!form) {
        return;
    }

    const watchedFields = [
        SELECTORS.title,
        SELECTORS.status,
        SELECTORS.visibility,
        SELECTORS.audience,
    ].join(', ');

    form.addEventListener('change', () => {
        root.classList.add('is-dirty');
    });

    form.addEventListener('input', event => {
        if (event.target && event.target.matches(watchedFields)) {
            root.classList.add('is-dirty');
        }
    });
};

/**
 * Initialise the editor.
 *
 * @param {Object} config AMD config.
 */
export const init = config => {
    const root = getRoot(config);
    if (!root) {
        return;
    }

    bindWorkflowNavigation(root);
    bindDirtyState(root);
};

export default {
    init,
};