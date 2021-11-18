// ~~DontLeave:Feature~~
doaj.dontleave = {
    active: false
}

doaj.dontleave.Monitor = class {
    constructor(params) {
        this.containerSelector = params.containerSelector;
        this.elementSelectorEvents = params.elementSelectorEvents || [{"input, select" : "change"}, {"button": "click"}];

        this.changed = false;
        this.submitting = false;

        for (let i = 0; i < this.elementSelectorEvents.length; i++) {
            let selectorEvent = this.elementSelectorEvents[i];
            let selector = Object.keys(selectorEvent)[0];
            let event = selectorEvent[selector];
            $(selector, this.containerSelector).bind(event, () => this.changed = true);
        }

        $(this.containerSelector).on("submit", () => {
            this.submitting = true;
        })

        $(window).bind("beforeunload", (event) => this.beforeUnload(event));
    }

    beforeUnload(event) {
        if (!this.changed || this.submitting) {
            event.cancel();
        }
        return "Any unsaved changes may be lost"
    }

    submissionFailed() {
        this.submitting = false;
    }
}

doaj.dontleave.init = function(params) {
    doaj.dontleave.active = new doaj.dontleave.Monitor(params);
}