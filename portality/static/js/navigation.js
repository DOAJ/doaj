doaj.primaryNav = {};

doaj.primaryNav.init = function() {
    doaj.primaryNav.toggle = $("#primary-nav-toggle");
    doaj.primaryNav.close = $("#primary-nav-close");
    doaj.primaryNav.panel = $("#primary-nav-menu");
    doaj.primaryNav.backdrop = $("#primary-nav-backdrop");

    doaj.primaryNav.toggle.on("click", doaj.primaryNav.toggleMenu);
    doaj.primaryNav.close.on("click", function() {
        doaj.primaryNav.closeMenu(true);
    });
    doaj.primaryNav.backdrop.on("click", function() {
        doaj.primaryNav.closeMenu(true);
    });

    $(document).on("keydown", doaj.primaryNav.keydown);
    $(window).on("resize", doaj.primaryNav.resize);
}

doaj.primaryNav.openMenu = function() {
    doaj.primaryNav.panel.addClass("is-open");
    doaj.primaryNav.backdrop.prop("hidden", false);
    doaj.primaryNav.toggle.attr("aria-expanded", "true");
    $("body").addClass("primary-nav-open");
    doaj.primaryNav.close.trigger("focus");
}

doaj.primaryNav.closeMenu = function(restoreFocus) {
    doaj.primaryNav.panel.removeClass("is-open");
    doaj.primaryNav.backdrop.prop("hidden", true);
    doaj.primaryNav.toggle.attr("aria-expanded", "false");
    $("body").removeClass("primary-nav-open");

    if (restoreFocus) {
        doaj.primaryNav.toggle.trigger("focus");
    }
}

doaj.primaryNav.toggleMenu = function() {
    if (doaj.primaryNav.panel.hasClass("is-open")) {
        doaj.primaryNav.closeMenu(false);
    } else {
        doaj.primaryNav.openMenu();
    }
}

doaj.primaryNav.keydown = function(event) {
    if (
        event.key === "Escape" &&
        doaj.primaryNav.panel.hasClass("is-open")
    ) {
        doaj.primaryNav.closeMenu(true);
    }
}

doaj.primaryNav.resize = function() {
    if (
        window.innerWidth >= 1024 &&
        doaj.primaryNav.panel.hasClass("is-open")
    ) {
        doaj.primaryNav.closeMenu(false);
    }
}

jQuery(document).ready(function($) {
    doaj.primaryNav.init();
});