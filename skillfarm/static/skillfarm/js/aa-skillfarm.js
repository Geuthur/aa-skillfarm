/* global aaSkillfarmDeafaultSettings, aaSkillfarmSettingsOverride, objectDeepMerge, bootstrap */

/**
 * Default settings for aaSkillfarm
 * Settings can be overridden by defining aaSkillfarmSettingsOverride before this script is loaded.
 */
const aaSkillfarmSettings = (typeof aaSkillfarmSettingsOverride !== 'undefined')
    ? objectDeepMerge(aaSkillfarmDeafaultSettings, aaSkillfarmSettingsOverride) // jshint ignore:line
    : aaSkillfarmDeafaultSettings;

/**
 * Bootstrap tooltip by (@ppfeufer)
 *
 * @param {string} [selector=body] Selector for the tooltip elements, defaults to 'body'
 *                                 to apply to all elements with the data-bs-tooltip attribute.
 *                                 Example: 'body', '.my-tooltip-class', '#my-tooltip-id'
 *                                 If you want to apply it to a specific element, use that element's selector.
 *                                 If you want to apply it to all elements with the data-bs-tooltip attribute,
 *                                 use 'body' or leave it empty.
 * @param {string} [namespace=aa-skillfarm] Namespace for the tooltip
 * @param {string} [trigger=hover] Trigger for the tooltip ('hover', 'click', etc.)
 * @returns {void}
 */
const _bootstrapTooltip = ({selector = 'body', namespace = 'aa-skillfarm', trigger = 'hover'} = {}) => {
    document.querySelectorAll(`${selector} [data-bs-tooltip="${namespace}"]`)
        .forEach((tooltipTriggerEl) => {
            // Dispose existing tooltip instance if it exists
            const existing = bootstrap.Tooltip.getInstance(tooltipTriggerEl);
            if (existing) {
                existing.dispose();
            }

            // Remove any leftover tooltip elements
            $('.bs-tooltip-auto').remove();

            // Create new tooltip instance
            return new bootstrap.Tooltip(tooltipTriggerEl, { trigger });
        });
};
