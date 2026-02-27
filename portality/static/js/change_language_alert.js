// ~~DontLeave:Feature~~
doaj.lang_change = {
    active: false
}

doaj.lang_change.Monitor = class {
    constructor(params) {
        this.containerSelector = params.containerSelector;
        this.elementSelectorEvents = params.elementSelectorEvents || [{"input, select" : "change"}];
        this.submitSelector = params.submitSelector || this.containerSelector;
        this.langSelector = $("select", this.submitSelector);
        this.warningModal = params.warningModal || $("#warningModal")
        this.stayButton = params.stayButton ? $(params.stayButton, this.warningModal) : $("#stayBtn", this.warningModal)
        this.leaveButton = params.leaveButton ? $(params.leaveButton, this.warningModal) : $("#leaveBtn", this.warningModal)
        this.changed = false;
        this.pendingSubmitEvent = null;
        this.currentLang = $(this.langSelector).val();

        // Update only if the value really changed -> ignore status changes when hidden/shown
        for (let i = 0; i < this.elementSelectorEvents.length; i++) {
            let selectorEvent = this.elementSelectorEvents[i];
            let selector = Object.keys(selectorEvent)[0];
            let event = selectorEvent[selector];
            $(selector, this.containerSelector).bind(event, (event) => {
                const $el = $(event.target);
                let newVal;
                // handle only "true" changes, ignore those triggered by a field being hidden
                if ($el.is(':checkbox') || $el.is(':radio')) {
                    newVal = $el.prop('checked');   // boolean true/false
                } else {
                    newVal = $el.val()?.trim() || "";  // normalize to "" if empty
                }
                const oldVal = $el.data("oldVal") ?? "";
                if (oldVal !== newVal) {
                    this.changed = true;
                }
            });
        }

        $(this.submitSelector).bind("submit", (e) => {
            console.log("submit!")
            e.preventDefault();
            this.pendingSubmitEvent = e;
            if(this.changed) {
                $(this.warningModal).css('display','flex'); // show modal
            }
            else {
                e.target.submit();
            }
        })

        $(this.stayButton).bind('click', () => {
            $(this.warningModal).hide();
            // set select back to the previous value
            $(this.langSelector).val(this.currentLang);
            this.pendingSubmitEvent = null; // cancel pending submit
        });

        $(this.leaveButton).bind('click', () => {
            $(this.warningModal).hide();
            if (this.pendingSubmitEvent) {
                // use the native DOM method to not trigger jquery submit handler
                const form = document.querySelector(this.submitSelector);
                form.submit();
                this.pendingSubmitEvent = null;
            }
        });
    }
}

doaj.lang_change.init = function(params) {
    doaj.lang_change.active = new doaj.lang_change.Monitor(params);
}