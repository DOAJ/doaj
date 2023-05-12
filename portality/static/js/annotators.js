if (!window.hasOwnProperty("doaj")) { doaj = {}}
if (!doaj.hasOwnProperty("annotators")) { doaj.annotators = {}}

doaj.annotators.ISSNActive = class {

    MESSAGES = {
        "unable_to_access": "We were unable to access the ISSN.org service",
        "not_found": "The ISSN was <strong>NOT</strong> found at ISSN.org",
        "fully_validated": "The ISSN is fully registered at ISSN.org",
        "not_validated": "The ISSN has <strong>NOT</strong> been registered at ISSN.org"
    }

    ICONS = {
        "unable_to_access": "clock",
        "not_found": "x-circle",
        "fully_validated": "check-circle",
        "not_validated": "x-circle"
    }

    draw(annotation) {
        let icon = this.ICONS[annotation.advice];
        let message = this.MESSAGES[annotation.advice];

        let frag = `<span data-feather="${icon}" aria-hidden="true"></span><br> ${message} 
                    (<a href="${annotation.reference_url}">see record</a>).`;
        return frag;
    }
}

doaj.annotators.KeepersRegistry = class {
    MESSAGES = {
        "missing": "{service} is missing from the Keepers Registry record at ISSN.org",
        "present": "{service} is present and current in the Keepers Registry record at ISSN.org",
        "outdated": "{service} is not currently being used according to the Keepers Registry record as ISSN.org"
    }

    ICONS = {
        "missing": "x-circle",
        "present": "check-circle",
        "outdated": "x-circle"
    }

    draw(annotation) {
        let icon = this.ICONS[annotation.advice];
        let message = this.MESSAGES[annotation.advice];

        let context = JSON.parse(annotation.context);
        message = message.replace("{service}", context.service);

        let frag = `<span data-feather="${icon}" aria-hidden="true"></span> 
                    ${message} (see 
                    <a href="${annotation.reference_url}">${annotation.reference_url})</a>`;
        return frag;
    }
}

doaj.annotators.registry = {
    "issn_active": doaj.annotators.ISSNActive,
    "keepers_registry": doaj.annotators.KeepersRegistry
}

doaj.annotators.DismissedAnnotations = class {
    constructor(params) {
        this.selector = edges.getParam(params.selector, ".dismissed-annotations")

        this.namespace = "dismissed-annotations";

        this.draw();
    }

    draw() {
        if (!doaj.annotations || !doaj.annotations.annotations) {
            return
        }

        let frag = "<h2>Dismissed Annotations</h2><ul>";
        for (let anno of doaj.annotations.annotations) {
            if (!anno.dismissed) {
                continue
            }
            frag += this._renderDismissed(anno)
        }
        frag += "</ul>"

        $(this.selector).html(frag);

        let undismissSelector = edges.css_class_selector(this.namespace, "undismiss");
        edges.on(undismissSelector, "click", this, "undismiss");

        edges.on(window, "doaj:annotations-undismiss", this, "undismissHandler");
        edges.on(window, "doaj:annotations-dismiss", this, "dismissHandler");
    }

    _renderDismissed(annotation) {
        let frag = `<li class="alert">${annotation.field}: `;

        if (annotation.annotator && doaj.annotators &&
            doaj.annotators.registry.hasOwnProperty(annotation.annotator)) {
            frag += (new doaj.annotators.registry[annotation.annotator]()).draw(annotation);
        } else {
            frag += this._defaultRender(annotation);
        }
        let undismissClass = edges.css_classes(this.namespace, "undismiss");
        frag += ` (<a href="#" data-annotation-set="${doaj.annotations.id}" data-annotation="${annotation.id}" class="${undismissClass}">Undismiss</a>)`

        frag += `</li>`;
        return frag;
    }

    _defaultRender = function(annotation) {
        let frag = "";
        if (annotation.advice) {
            frag += `${annotation.advice}<br>`
        }
        if (annotation.reference_url) {
            frag += `<a href="${annotation.reference_url}" target="_blank">${annotation.reference_url}</a><br>`
        }
        if (annotation.suggested_value) {
            frag += `Suggested Value(s): ${annotation.suggested_value.join(", ")}<br>`
        }
        if (annotation.original_value) {
            frag += `(Original value when automated checks ran: ${annotation.original_value})`
        }
        return frag;
    }

    undismiss(element) {
        let el = $(element);
        let annotationSet = el.attr("data-annotation-set")
        let annotationId = el.attr("data-annotation");
        let url = "/service/annotation/undismiss/" + annotationSet + "/" + annotationId;
        let that = this;
        $.ajax({
            method: "post",
            url: url,
            error: function(data) {
                alert("There was an error undismissing the annotation, please try again");
            },
            success: function(data) {
                that.undismissSuccess(annotationId);
            }
        })
    }

    undismissSuccess(annotationId) {
        for (let anno of doaj.annotations.annotations) {
            if (anno.id === annotationId) {
                anno.dismissed = false;
            }
        }
        $(window).trigger("doaj:annotations-undismiss");
    }

    undismissHandler() {
        this.draw();
    }

    dismissHandler() {
        this.draw();
    }
}