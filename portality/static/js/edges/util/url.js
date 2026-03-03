// ~~ Edge URL Utilities ~~
doaj.edgeUtil = doaj.edgeUtil || {};

doaj.edgeUtil.url = {

    /**
     * Returns base URL including scheme + host
     * Example: https://doaj.org
     */
    getBaseURL: function() {
        return window.location.protocol + "//" + document.location.host;
    },

    /**
     * Builds full URL from provided path
     * @param {string} path
     */
    build: function(path) {
        return this.getBaseURL() + path;
    }
};