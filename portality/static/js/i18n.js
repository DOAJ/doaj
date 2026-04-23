// i18n.js - Internationalization for JavaScript
"use strict";

doaj.i18n = {
    active: false,
    translations: {}
};

// Initialize the translation system
doaj.i18n.init = function(translations) {
    doaj.i18n.translations = translations || {};
    doaj.i18n.active = true;
};

// Get a translated string
doaj.i18n.get = function(key) {
    if (doaj.i18n.active && doaj.i18n.translations.hasOwnProperty(key)) {
        return doaj.i18n.translations[key];
    }
    return key;  // Return the key itself if no translation found
};