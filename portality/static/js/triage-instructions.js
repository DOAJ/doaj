window.doaj = window.doaj || {};
window.doaj.triage = window.doaj.triage || {};

doaj.triage.instructions = {
    current: null
};
doaj.triage.instructions.init = function () {
    $(document)
        .off("keydown.triageInstructions")
        .on("keydown.triageInstructions", function (event) {
            if (
                event.key === "Escape" &&
                doaj.triage.instructions.current
            ) {
                doaj.triage.instructions.current.close();
            }
        });
};
doaj.triage.instructions.Drawer = class {
    static show_by_default = false;

    static init() {
        const $show_by_default_checkbox = $("#ew_header--show_instructions_by_default");
        this.show_by_default = $show_by_default_checkbox.is(":checked");
    }

    constructor($question) {
        this.$question = $question;
        this.$triggerBtn = this.$question.$wrapper
            .find("[data-role='open-instructions']")
            .first();
        this.$layout = this.$triggerBtn.closest(".criterion-layout");
        this.available = false;
        if (!this.$triggerBtn.length) {
            return;
        }
        const drawerId = this.$triggerBtn.attr("aria-controls");
        const $drawer = drawerId
            ? $(`#${drawerId}`)
            : null;

        if (!$drawer) {
            console.warn(
                `Instructions drawer not found for ${question.name}`
            );
            return;
        }

        this.$drawer = $drawer;
        this.$closeButton = this.$drawer
            .find("[data-role='close-instructions']")
            .first();

        this.available = true;
        this._setupEvents();
    }

    _setupEvents() {
        this.$triggerBtn.on(
            "click.triageInstructions",
            () => { this.isOpen ? this.close() : this.open(); },
        );

        this.$closeButton.on(
            "click.triageInstructions",
            () => this.close()
        );
    }

    get show_by_default() {
        return doaj.triage.instructions.Drawer.show_by_default;
    }
    get isOpen() {
        return this.$layout.hasClass(
            "criterion-layout--instructions-open"
        );
    }

    open() {
        if (!this.available) {
            return;
        }

        const current = doaj.triage.instructions.current;

        if (current && current !== this) {
            current.close({restoreFocus: false});
        }

        doaj.triage.instructions.current = this;

        this.$layout.addClass(
            "criterion-layout--instructions-open"
        );

        $("body").addClass("criterion-instructions-open");

        this.$drawer.attr("aria-hidden", "false");
        this.$triggerBtn.attr("aria-expanded", "true");
        this.$closeButton.trigger("focus");
    }

    close({restoreFocus = true} = {}) {
        if (!this.available || !this.isOpen) {
            return;
        }

        this.$layout.removeClass(
            "criterion-layout--instructions-open"
        );

        $("body").removeClass("criterion-instructions-open");
        this.$triggerBtn.attr("aria-expanded", "false");

        if (restoreFocus) {
            this.$triggerBtn.trigger("focus");
        }

        this.$drawer.attr("aria-hidden", "true");

        if (doaj.triage.instructions.current === this) {
            doaj.triage.instructions.current = null;
        }
    }
};