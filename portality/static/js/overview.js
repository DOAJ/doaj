window.doaj = window.doaj || {};
doaj.workflow = doaj.workflow || {};

doaj.workflow.Overview = class {
    constructor(wfc) {
        this.stage = {
            NEW: "submission",
            TRIAGE: "triage"
        }
        this.triage_answers = wfc.modules.triage.questions;
        this.$tabs = $('button[role="tab"][aria-controls]');

        this.sections = {
            submission: $(".submission").first(),
            triage: $(".triage").first()
        };

        this.$showRejectionSection = $("#show-rejection-section");
        this.$rejectionSection = $("#rejection_section");
    }

    init() {

        this.$tabs.on("click", (event) => {
            event.preventDefault();
            this.activateTab(event.currentTarget.id);
        });

        this.activateTab(this.isTriageStarted() ? `${this.stage.TRIAGE}-tab` : `${this.stage.NEW}-tab`);

        if (this.$rejectionSection.length) {
            this.$showRejectionSection
                .attr({
                    "aria-controls": "rejection_section",
                    "aria-expanded": String(
                        !this.$rejectionSection.prop("hidden")
                    )
                })
                .on("click", (event) => {
                    event.preventDefault();
                    this.showRejectionSection();
                });
        }
    }

    isTriageStarted() {
        return Object.values(this.triage_answers).some(
            value => Object.hasOwn(value, "answer")
        )
    }

    activateTab(tabId) {
        const activeTab = document.getElementById(tabId);

        if (!activeTab) return;

        const $tabs = $(activeTab)
            .closest('[role="tablist"]')
            .find('[role="tab"]');

        $tabs.each((index, tab) => {
            const $tab = $(tab);
            const isActive = tab === activeTab;

            $tab
                .attr({
                    "aria-selected": String(isActive),
                    "tabindex": isActive ? "0" : "-1"
                })
                .toggleClass("button--cta", isActive);

            const panel = document.getElementById(
                $tab.attr("aria-controls")
            );

            $(panel).prop("hidden", !isActive);
        });

        $(activeTab).trigger("focus");
    }

    showRejectionSection() {
        this.$rejectionSection.prop("hidden", false);
        this.$showRejectionSection.attr("aria-expanded", "true");

        // Move focus into the revealed section before hiding the trigger.
        this.$rejectionSection
            .attr("tabindex", "-1")
            .trigger("focus");

        this.$showRejectionSection.prop("hidden", true);
    }
}