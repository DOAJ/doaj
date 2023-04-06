if (!window.hasOwnProperty("doaj")) { doaj = {}}
if (!doaj.hasOwnProperty("annotators")) { doaj.annotators = {}}

doaj.annotators.ISSNActive = class {

    MESSAGES = {
        "unable_to_access": "We were unable to access the ISSN.org service",
        "not_found": "The ISSN was not found at ISSN.org",
        "fully_validated": "The ISSN is fully registered at ISSN.org",
        "not_validated": "The ISSN has not been registered at ISSN.org"
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

        let frag = `<span data-feather="${icon}" aria-hidden="true"></span> 
                    Checked ${annotation.original_value}: ${message} (see 
                    <a href="${annotation.reference_url}">${annotation.reference_url})</a>`;
        return frag;
    }
}

doaj.annotators.registry = {
    "issn_active": doaj.annotators.ISSNActive
}