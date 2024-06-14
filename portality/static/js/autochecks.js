if (!window.hasOwnProperty("doaj")) { doaj = {}}
if (!doaj.hasOwnProperty("autocheckers")) { doaj.autocheckers = {}}

doaj.autocheckers.ISSNActive = class {

    MESSAGES = {
        "unable_to_access": "We were unable to access the ISSN.org service",
        "not_found": "The ISSN ({{ISSN}}) was <strong>not found</strong> at ISSN.org",
        "fully_validated": "The ISSN ({{ISSN}}) is fully registered at ISSN.org",
        "not_validated": "The ISSN ({{ISSN}}) has <strong>not been registered</strong> at ISSN.org"
    }

    ICONS = {
        "unable_to_access": "clock",
        "not_found": "x-circle",
        "fully_validated": "check-circle",
        "not_validated": "x-circle"
    }

    STYLE = {
        "unable_to_access": "error",
        "not_found": "error",
        "fully_validated": "success",
        "not_validated": "warn"
    }

    draw(autocheck) {
        let icon = this.ICONS[autocheck.advice];
        let message = this.MESSAGES[autocheck.advice];
        message = message.replace("{{ISSN}}", autocheck.original_value);

        let style = this.STYLE[autocheck.advice];

        let frag = `<div><span class="icon-container icon-container--${autocheck.advice} icon-container--${style}"><span data-feather="${icon}" aria-hidden="true"></span></span>
                    ${message} (<a href="${autocheck.reference_url}" target="_blank">see record</a>)</div>`;
        return frag;
    }
}

doaj.autocheckers.PublicationTime = class {
     MESSAGES = {
        "below_2_weeks": "Average time between article submission & publication is 2 weeks or shorter",
        "over_2_weeks": "Average time between article submission & publication is more than 2 weeks",
    }

    ICONS = {
        "below_2_weeks": "x-circle",
        "over_2_weeks": "check-circle",
    }

    STYLE = {
        "below_2_weeks": "warn",
        "over_2_weeks": "success",
    }

    draw(autocheck) {
        let icon = this.ICONS[autocheck.advice];
        let message = this.MESSAGES[autocheck.advice];
        let style = this.STYLE[autocheck.advice];

        let frag = `<div><span class="icon-container icon-container--${autocheck.advice} icon-container--${style}"><span data-feather="${icon}" aria-hidden="true"></span></span>
                    ${message} </div>`;
        console.log(frag);
        return frag;
    }
}

doaj.autocheckers.KeepersRegistry = class {
    MESSAGES = {
        "missing": "Keepers does not show any content archived in {service}.",
        "present": "The journal content is actively archived in {service}.",
        "outdated": "The journal has content archived in {service} but it's not current.",
        "not_recorded": "Keepers Registry does not currently record information about {service}."
    }

    ICONS = {
        "missing": "x-circle",
        "present": "check-circle",
        "outdated": "x-circle",
        "not_recorded": "info"
    }

    STYLE = {
        "missing": "error",
        "present": "success",
        "outdated": "error",
        "not_recorded": "info"
    }

    draw(autocheck) {
        let icon = this.ICONS[autocheck.advice];
        let message = this.MESSAGES[autocheck.advice];

        let context = JSON.parse(autocheck.context);
        message = message.replace("{service}", context.service);

        let style = this.STYLE[autocheck.advice];

        let frag = `<div><span class="icon-container icon-container--${autocheck.advice} icon-container--${style}""><span data-feather="${icon}" aria-hidden="true"></span></span>
                    ${message} (<a href="${autocheck.reference_url}" target="_blank">see record</a>)</div>`;
        return frag;
    }
}

doaj.autocheckers.registry = {
    "issn_active": doaj.autocheckers.ISSNActive,
    "keepers_registry": doaj.autocheckers.KeepersRegistry,
    "publication_time": doaj.autocheckers.PublicationTime
}

doaj.autocheckers.AutochecksManager = class {
    constructor(params) {
        this.selector = edges.getParam(params.selector, ".autochecks-manager")

        this.namespace = "autochecks-manager";

        this.draw();
    }

    draw() {
        if (!doaj.autochecks || !doaj.autochecks.checks) {
            return;
        }

        let d = new Date(doaj.autochecks.created_date);
        let date = d.toLocaleDateString("en-GB", {year: "numeric", month: "long", day: "numeric"});

        let toggleClass = edges.css_classes(this.namespace, "toggle");
        let frag = `Autochecks were made on ${date} <span class="tags"><span class="tag"><a href="#" class="${toggleClass}" data-state="hidden">Show All Autochecks</a></span></span>`;

        $(this.selector).html(frag);

        let toggleSelector = edges.css_class_selector(this.namespace, "toggle");
        edges.on(toggleSelector, "click", this, "toggle");
    }

    toggle(element) {
        let el = $(element);
        let state = el.attr("data-state");
        let autocheckSelector = ".formulaic-autocheck-container";
        if (state === "shown") {
            $(autocheckSelector).hide();
            el.attr("data-state", "hidden");
            el.html("Show All Autochecks")
        } else {
            $(autocheckSelector).show();
            el.attr("data-state", "shown");
            el.html("Hide All Autochecks");
        }
    }
}