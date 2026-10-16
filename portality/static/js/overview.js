window.doaj = window.doaj || {};
doaj.workflow = doaj.workflow || {};

doaj.workflow.Overview = class {
    constructor(wfc) {
        this.answers = wfc.modules.triage.questions;
        this.$toggleLinks = $(
            'a[data-toggle="submission"], a[data-toggle="triage"]'
        );

        this.sections = {
            submission: $(".submission").first(),
            triage: $(".triage").first()
        };

        if (this.hasAnswer()) {
            this.sections.triage._show();
            this.sections.submission._hide();
        }
        else {
            this.sections.triage._hide();
            this.sections.submission._show();
        }

        this.$showRejectionSection = $("#show-rejection-section");
        this.$rejectionSection = $("#rejection_section");
    }

    init() {
        this.$toggleLinks.on("click", (event) => {
            const sectionName = $(event.currentTarget).attr("data-toggle");
            const $section = this.sections[sectionName];

            if (!$section || !$section.length) {
                return;
            }

            event.preventDefault();
            this.showSection(sectionName);
        });

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

    hasAnswer() {
        return Object.values(this.answers).some(
            value => Object.hasOwn(value, "answer")
        )
    }

    showSection(sectionName) {
        Object.entries(this.sections).forEach(([name, $section]) => {
            $section.toggle(name === sectionName);
        });

        this.$toggleLinks.each((index, link) => {
            const $link = $(link);

            $link.toggleClass(
                "button--cta",
                $link.attr("data-toggle") === sectionName
            );
        });
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