if (!window.hasOwnProperty("doaj")) { doaj = {}}
if (!doaj.hasOwnProperty("autocheckers")) { doaj.autocheckers = {}}

doaj.autocheckers.ISSNActive = class {

    MESSAGES = {
        "unable_to_access": "We were unable to access the ISSN.org service",
        "not_found": "The ISSN was <strong>not found</strong> at ISSN.org",
        "fully_validated": "The ISSN is fully registered at ISSN.org",
        "not_validated": "The ISSN has <strong>not been registered</strong> at ISSN.org"
    }

    ICONS = {
        "unable_to_access": "clock",
        "not_found": "x-circle",
        "fully_validated": "check-circle",
        "not_validated": "x-circle"
    }

    draw(autocheck) {
        let icon = this.ICONS[autocheck.advice];
        let message = this.MESSAGES[autocheck.advice];

        let frag = `<div><span class="icon-container icon-container--${autocheck.advice}"><span data-feather="${icon}" aria-hidden="true"></span></span>
                    ${message} (<a href="${autocheck.reference_url}">see record</a>).</div>`;
        return frag;
    }
}

doaj.autocheckers.KeepersRegistry = class {
    MESSAGES = {
        "missing": "{service} is <strong>missing</strong> from the Keepers Registry record at ISSN.org",
        "present": "{service} is present and current in the Keepers Registry record at ISSN.org",
        "outdated": "{service} is <strong>not currently being used</strong> according to the Keepers Registry record as ISSN.org"
    }

    ICONS = {
        "missing": "x-circle",
        "present": "check-circle",
        "outdated": "x-circle"
    }

    draw(autocheck) {
        let icon = this.ICONS[autocheck.advice];
        let message = this.MESSAGES[autocheck.advice];

        let context = JSON.parse(autocheck.context);
        message = message.replace("{service}", context.service);

        let frag = `<div><span class="icon-container icon-container--${autocheck.advice}"><span data-feather="${icon}" aria-hidden="true"></span></span>
                    ${message} (<a href="${autocheck.reference_url}">see record</a>).</div>`;
        return frag;
    }
}

doaj.autocheckers.registry = {
    "issn_active": doaj.autocheckers.ISSNActive,
    "keepers_registry": doaj.autocheckers.KeepersRegistry
}

doaj.autocheckers.DismissedAutochecks = class {
    constructor(params) {
        this.selector = edges.getParam(params.selector, ".dismissed-autochecks")

        this.namespace = "dismissed-autochecks";

        this.draw();
    }

    draw() {
        if (!doaj.autochecks || !doaj.autochecks.autochecks) {
            return
        }

        let frag = "<h2>Dismissed Autochecks</h2><ul class='unstyled-list'>";
        for (let anno of doaj.autochecks.autochecks) {
            if (!anno.dismissed) {
                continue
            }
            frag += this._renderDismissed(anno)
        }
        frag += "</ul>"

        $(this.selector).html(frag);

        let undismissSelector = edges.css_class_selector(this.namespace, "undismiss");
        edges.on(undismissSelector, "click", this, "undismiss");

        edges.on(window, "doaj:autochecks-undismiss", this, "undismissHandler");
        edges.on(window, "doaj:autochecks-dismiss", this, "dismissHandler");
    }

    _renderDismissed(autocheck) {
        let frag = `<li class="alert"><h3 class='label label--large'>“${autocheck.field}”</h3> `;

        if (autocheck.checked_by && doaj.autocheckers &&
            doaj.autocheckers.registry.hasOwnProperty(autocheck.checked_by)) {
            frag += (new doaj.autocheckers.registry[autocheck.checked_by]()).draw(autocheck);
        } else {
            frag += this._defaultRender(autocheck);
        }
        let undismissClass = edges.css_classes(this.namespace, "undismiss");
        frag += `<button href="#" data-autocheck-set="${doaj.autochecks.id}" data-autocheck="${autocheck.id}" class="${undismissClass}">Undismiss</button>`

        frag += `</li>`;
        return frag;
    }

    _defaultRender = function(autocheck) {
        let frag = "";
        if (autocheck.advice) {
            frag += `${autocheck.advice}<br>`
        }
        if (autocheck.reference_url) {
            frag += `<a href="${autocheck.reference_url}" target="_blank">${autocheck.reference_url}</a><br>`
        }
        if (autocheck.suggested_value) {
            frag += `Suggested Value(s): ${autocheck.suggested_value.join(", ")}<br>`
        }
        if (autocheck.original_value) {
            frag += `(Original value when automated checks ran: ${autocheck.original_value})`
        }
        return frag;
    }

    undismiss(element) {
        let el = $(element);
        let autocheckSet = el.attr("data-autocheck-set")
        let autocheckId = el.attr("data-autocheck");
        let url = "/service/autocheck/undismiss/" + autocheckSet + "/" + autocheckId;
        let that = this;
        $.ajax({
            method: "post",
            url: url,
            error: function(data) {
                alert("There was an error undismissing the autocheck, please try again");
            },
            success: function(data) {
                that.undismissSuccess(autocheckId);
            }
        })
    }

    undismissSuccess(autocheckId) {
        for (let anno of doaj.autochecks.autochecks) {
            if (anno.id === autocheckId) {
                anno.dismissed = false;
            }
        }
        $(window).trigger("doaj:autochecks-undismiss");
    }

    undismissHandler() {
        this.draw();
    }

    dismissHandler() {
        this.draw();
    }
}