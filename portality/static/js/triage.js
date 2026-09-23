window.doaj = window.doaj || {};
window.doaj.triage = window.doaj.triage || {};

doaj.triage.initialRecommendation = null;

doaj.triage.recommendation = {};

doaj.triage.recommendation.render = function (recommendation) {
    if (!recommendation) {
        console.log("No recommendation");
        return;
    }

    console.log("Current Recommendation:", recommendation.code);

    if (recommendation.code !== "reject") {
        return;
    }

    console.log("Reasons:");

    (recommendation.reasons || []).forEach(function (reason) {
        var text = reason.question.text +
            " (" + reason.question.name + ")" +
            " [" + reason.question.field_id + "]: " +
            reason.answer;

        if (reason.sv) {
            text += " (SV: " + reason.sv + ")";
        }

        if (reason.exception) {
            text += " (Exception(s): " + reason.exception.join(", ") + ")";
        }

        console.log(text);
    });
};


// strings that are used consistently in the templates
doaj.triage.magicStrings = {
    reviewOutcomeFieldset: "-review_outcome",
    yourAnswer: "-your_answer"
}

doaj.triage.selectors = {
    form: "#triage",
    response: "#triage-async-response",
    saveableFields: 'input[type="text"], input[type="url"], input[type="number"], ' +
        'input[type="radio"], input[type="checkbox"], select, textarea',
    nextQuestionButton: ".js-triage-next-question",
    prevQuestionButton: ".js-triage-prev-question",
    questionWrapper: ".criterion-wrapper",
    summaryContainer: "#triage-error-summary",
    summaryLink: "[data-field-error-summary-for]",
    checkboxOther: "input[type='checkbox'][value='other']",
    checkboxNone: "input[type='checkbox'][value='none']",
    answers: "input[type='radio'][data-role='answer']",
    answersContainer: "fieldset.review_outcome-container",
    clearAnswersButton: "button[data-role='change_answers']",
    actionButton: "button[data-controls]",
    actionSection: "div[data-role='action']",
    recommendationHost: "#triage-recommendation"
};
doaj.triage.errorNodeClass = "triage-field-error";
doaj.triage.errorNodeDataAttr = "data-field-error-for";
doaj.triage.summaryHostClass = "triage-error-summary-host";
doaj.triage.summaryLinkDataAttr = "data-field-error-summary-for";

doaj.triage.init = function () {

    $(document).on("click", "#submitBtn", function (event) {
        event.preventDefault();
        doaj.triage.fullFormSubmit(this);
    });
}

doaj.triage._saving = false;
doaj.triage._queuedOptions = null;

doaj.triage._announce = function ($region, message) {
    $region.empty();

    window.requestAnimationFrame(function () {
        $region.text(message);
    });
};
doaj.triage.requestSave = function (options) {
    options = Object.assign({
        blocking: false,
        onSuccess: null,
        onFailure: null
    }, options || {});

    if (doaj.triage._saving) {
        doaj.triage._queuedOptions =
            doaj.triage._mergeQueuedOptions(
                doaj.triage._queuedOptions,
                options
            );
        return;
    }

    doaj.triage._runSave(options);
};

doaj.triage._showSaveSuccess = function () {
    const headersHeight = $("#ew_header").outerHeight() +
        $("#primary-nav").outerHeight();

    $(".save-notification").css("top", `${headersHeight}px`);

    $("#triage-save-notification-error")._hide();
    $("#triage-save-error-status").empty();

    $("#triage-save-notification-success")
        .stop(true, true)
        ._show()
        .show()
        .delay(3000)
        .fadeOut("slow");

    doaj.triage._announce(
        $("#triage-save-status"),
        "Triage saved"
    );
};

doaj.triage._showSaveFailure = function () {
    const headersHeight =
        $("#ew_header").outerHeight() +
        $("#primary-nav").outerHeight();

    $(".save-notification").css("top", `${headersHeight}px`);

    $("#triage-save-notification-success")
        .stop(true, true)
        ._hide();

    $("#triage-save-status").empty();
    $("#triage-save-notification-error")._show();

    doaj.triage._announce(
        $("#triage-save-error-status"),
        "Triage could not be saved. Please try again."
    );
};


// Combine a newly-requested save with one already queued, so neither gets
// silently dropped: "blocking" wins if either call asked for it, and the
// most recent onSuccess callback is the one that will actually run.
doaj.triage._mergeQueuedOptions = function (existing, incoming) {
    existing = existing || {};
    return {
        blocking: !!(existing.blocking || incoming.blocking),
        onSuccess: incoming.onSuccess || existing.onSuccess,
        onFailure: incoming.onFailure || existing.onFailure
    };
};

doaj.triage._runSave = function (options) {
    var $form = $(doaj.triage.selectors.form);
    if ($form.length === 0) {
        return;
    }

    doaj.triage._saving = true;
    var formData = new FormData($form[0]);

    $.ajax({
        url: doaj.triage.asyncURL,
        method: "POST",
        data: formData,
        processData: false,
        contentType: false,
        dataType: "json"
    }).done(function (data) {
        doaj.triage._handleSaveResponse(data, options);
    }).fail(function (jqXHR, textStatus, errorThrown) {
        // A transport/server failure, distinct from a validation failure -
        // there's no field-level information to show, so just log it.
        console.error(
            "Triage async save failed:",
            textStatus,
            errorThrown,
            jqXHR.responseText
        );

        doaj.triage._showSaveFailure();

        if (typeof options.onFailure === "function") {
            options.onFailure({
                type: "request",
                jqXHR: jqXHR,
                textStatus: textStatus,
                errorThrown: errorThrown
            });
        }
    }).always(function () {
        doaj.triage._saving = false;
        doaj.triage._runQueuedSaveIfAny();
    });
};

doaj.triage._runQueuedSaveIfAny = function () {
    if (doaj.triage._queuedOptions === null) {
        return;
    }
    var next = doaj.triage._queuedOptions;
    doaj.triage._queuedOptions = null;
    doaj.triage._runSave(next);
};

doaj.triage._handleSaveResponse = function (data, options) {
    if (data.validation) {
        const severity = options.blocking
            ? doaj.triage.severity.BLOCKING
            : doaj.triage.severity.SOFT;

        doaj.triage.errors.render(
            data.validation.errors || [],
            severity
        );

        doaj.triage._showSaveFailure();

        if (typeof options.onFailure === "function") {
            options.onFailure({
                type: "validation",
                validation: data.validation
            });
        }

        return;
    }

    doaj.triage.errors.clearAll();
    doaj.triage.recommendation.render(data.recommendation);
    doaj.triage._showSaveSuccess();

    if (typeof options.onSuccess === "function") {
        options.onSuccess(data);
    }
};

/* ============================================================
 * Error rendering
 *
 * The backend reports errors as a list of {field_id, code: {msg}}, where
 * field_id is exactly the "name" attribute of the relevant control(s) - see
 * TriageFormProcessor.validation_report() and FormSerialiser.make_id() on
 * the backend. That means we can always find the field(s) an error belongs
 * to with a plain attribute selector, without knowing anything about the
 * form's structure up front.
 *
 * Errors are rendered in one of two severities, matching the save that
 * produced them (see triage.css / the admin_stylesheets block in
 * triage.html for the actual look, which is a placeholder pending a real
 * design pass):
 *  - "soft"        - a blur-triggered save came back with errors. These are
 *                    expected mid-answer (e.g. a note not filled in yet) and
 *                    are shown as a gentle "needs attention" hint.
 *  - "blocking"    - the "Next question" hard gate came back with errors.
 *                    These are shown as a firm "fix this before continuing"
 *                    message, since they're actively stopping the user.
 *
 * render() is a diff against what's currently displayed (doaj.triage.errors
 * ._current), not a blind clear-and-rebuild: a field whose error hasn't
 * actually changed keeps its existing DOM node untouched. This matters
 * because each node carries role="alert" - rebuilding every node on every
 * save (even ones triggered by a completely unrelated field) would make a
 * screen reader re-announce every outstanding error on every edit, not just
 * the ones that changed. Confirmed as a real (now fixed) issue during live
 * verification on 2026-07-14 - see TRIAGE_ASYNC_SAVE.md.
 * ============================================================ */

doaj.triage.severity = {
    SOFT: "soft",
    BLOCKING: "blocking"
};

doaj.triage.severityLabel = {
    soft: "Needs attention: ",
    blocking: "Fix this before continuing: "
};

doaj.triage.severity = {
    SOFT: "soft",
    BLOCKING: "blocking"
};

doaj.triage.severityLabel = {
    soft: "Needs attention: ",
    blocking: "Fix this before continuing: "
};


doaj.triage.Errors = class {
    constructor() {
        this.current = {};
    }

    render(errorList, severity) {
        var incoming = {};

        errorList.forEach(function (error) {
            var message = error.code && error.code.msg;

            if (error.field_id && message) {
                incoming[error.field_id] = {
                    message: message,
                    severity: severity
                };
                const $errorContainer = $(`#${error.field_id}-error-container`);
                $errorContainer
                    ._show()
                    .html(message);
                const $invalidField = $(`#${error.field_id}`);
                $invalidField
                    .attr("aria-invalid", "true")
                    .attr("aria-describedby", `${error.field_id}-error-container`)
                    .trigger("focus");
                const $answerInput = $invalidField.closest(".criterion-wrapper").find("input[data-role='answer']:checked");
                $answerInput.prop("checked", false);
            }
        });

        this.current = incoming;
        console.log("Validation errors:", incoming);
    }

    clearAll() {
        this.current = {};
        $('[aria-invalid="true"]').each(function () {
            const $field = $(this);
            const $errorContainer = $(`#${this.id}---error-container`);
            if ($errorContainer) {
                $errorContainer
                    .empty()
                    ._hide();
            }
            $field
                .removeAttr("aria-invalid")
                .removeAttr("aria-describedby");
        });
        console.log("Validation errors cleared");
    }
};

doaj.triage.errors = new doaj.triage.Errors();


doaj.triage.questions = {};
doaj.triage.questions._ids = function () {
    return $(doaj.triage.selectors.questionWrapper).map(function () {
        return this.id;
    }).get();
};

/* ============================================================
 * Existing manual submit paths (unchanged)
 * ============================================================ */

doaj.triage.fullFormSubmit = function (submitter) {
    let $form = $("#triage");
    let $response = $("#triage-async-response");

    if ($form.length === 0) {
        $response.html("<pre>Unable to find form with id 'triage'.</pre>");
        return;
    }

    // Submit the form directly (button is outside the form)
    $form[0].submit();
}

//------------------------- my code  -------------------------
doaj.triage.questions.showOverview = function () {
    console.log("TODO: show overview");
};
doaj.triage.questions.answerIcons = {
    compliant: `<svg xmlns="http://www.w3.org/2000/svg" 
                    width="24" 
                    height="24" 
                    viewBox="0 0 24 24" 
                    fill="none"
                    aria-hidden="true"
                    class="answer-icon"
                >
                    <path d="M12 0.375C5.57967 0.375 0.375 5.57967 0.375 12C0.375 18.4203 5.57967 23.625 12 23.625C18.4203 23.625 23.625 18.4203 23.625 12C23.625 5.57967 18.4203 0.375 12 0.375ZM12 2.625C17.1812 2.625 21.375 6.81802 21.375 12C21.375 17.1812 17.182 21.375 12 21.375C6.81881 21.375 2.625 17.182 2.625 12C2.625 6.81881 6.81802 2.625 12 2.625ZM18.5721 8.73127L17.5157 7.66636C17.2969 7.44581 16.9408 7.44436 16.7202 7.66317L10.0943 14.2358L7.29159 11.4103C7.07283 11.1898 6.71667 11.1883 6.49613 11.4071L5.43117 12.4635C5.21062 12.6822 5.20917 13.0384 5.42798 13.259L9.68334 17.5488C9.90211 17.7693 10.2583 17.7708 10.4788 17.552L18.5689 9.52678C18.7894 9.30797 18.7908 8.95181 18.5721 8.73127Z" fill="#3A5959"/>
                </svg>`,
    non_compliant: `<svg xmlns="http://www.w3.org/2000/svg" 
                    width="24" 
                    height="24" 
                    viewBox="0 0 24 24" 
                    fill="none"
                    aria-hidden="true"
                    class="answer-icon"
                >
                        <path d="M12 0.375C5.57812 0.375 0.375 5.57812 0.375 12C0.375 18.4219 5.57812 23.625 12 23.625C18.4219 23.625 23.625 18.4219 23.625 12C23.625 5.57812 18.4219 0.375 12 0.375ZM12 21.375C6.82031 21.375 2.625 17.1797 2.625 12C2.625 6.82031 6.82031 2.625 12 2.625C17.1797 2.625 21.375 6.82031 21.375 12C21.375 17.1797 17.1797 21.375 12 21.375Z" fill="#982E0A"/>
                        <path d="M12.1562 14.3438C10.9654 14.3438 10 15.3091 10 16.5C10 17.6909 10.9654 18.6562 12.1562 18.6562C13.3471 18.6562 14.3125 17.6909 14.3125 16.5C14.3125 15.3091 13.3471 14.3438 12.1562 14.3438Z" fill="#982E0A"/>
                        <path d="M10.1091 6.59316L10.4568 12.9682C10.4731 13.2665 10.7197 13.5 11.0185 13.5H13.294C13.5928 13.5 13.8394 13.2665 13.8557 12.9682L14.2034 6.59316C14.221 6.27094 13.9645 6 13.6418 6H10.6707C10.348 6 10.0915 6.27094 10.1091 6.59316Z" fill="#982E0A"/>
                    </svg>`,
    later: `<svg xmlns="http://www.w3.org/2000/svg" 
                    width="24" 
                    height="24" 
                    viewBox="0 0 24 24" 
                    fill="none"
                    aria-hidden="true"
                    class="answer-icon"
            >
                <path d="M12 0.375C5.58014 0.375 0.375 5.58202 0.375 12C0.375 18.4217 5.58014 23.625 12 23.625C18.4199 23.625 23.625 18.4217 23.625 12C23.625 5.58202 18.4199 0.375 12 0.375ZM12 21.375C6.81881 21.375 2.625 17.1829 2.625 12C2.625 6.82055 6.819 2.625 12 2.625C17.1793 2.625 21.375 6.81895 21.375 12C21.375 17.1811 17.1829 21.375 12 21.375ZM17.0271 9.4125C17.0271 12.5556 13.6323 12.6039 13.6323 13.7655V14.0625C13.6323 14.3731 13.3805 14.625 13.0698 14.625H10.9301C10.6195 14.625 10.3676 14.3731 10.3676 14.0625V13.6566C10.3676 11.9811 11.6379 11.3113 12.5979 10.773C13.4211 10.3116 13.9256 9.99769 13.9256 9.38653C13.9256 8.57812 12.8944 8.04155 12.0607 8.04155C10.9737 8.04155 10.4719 8.55609 9.76655 9.44634C9.57638 9.68634 9.22936 9.73092 8.98533 9.54591L7.68108 8.55694C7.44169 8.37544 7.38806 8.03822 7.55714 7.78992C8.66466 6.16364 10.0753 5.25 12.2716 5.25C14.5718 5.25 17.0271 7.0455 17.0271 9.4125ZM13.9688 17.25C13.9688 18.3356 13.0856 19.2188 12 19.2188C10.9144 19.2188 10.0312 18.3356 10.0312 17.25C10.0312 16.1644 10.9144 15.2812 12 15.2812C13.0856 15.2812 13.9688 16.1644 13.9688 17.25Z" fill="#F9D950"/>
            </svg>`,
    action: `<svg xmlns="http://www.w3.org/2000/svg" 
                width="24" 
                height="24" 
                viewBox="0 0 24 24" 
                fill="none"
                aria-hidden="true"
                class="answer-icon"
            >
                <path d="M12 0.375C5.57967 0.375 0.375 5.57967 0.375 12C0.375 18.4203 5.57967 23.625 12 23.625C18.4203 23.625 23.625 18.4203 23.625 12C23.625 5.57967 18.4203 0.375 12 0.375ZM12 2.625C17.1812 2.625 21.375 6.81802 21.375 12C21.375 17.1812 17.182 21.375 12 21.375C6.81881 21.375 2.625 17.182 2.625 12C2.625 6.81881 6.81802 2.625 12 2.625Z" fill="#FD5A3B"/>
                <path d="M16.9668 10.3366L10.1283 16.9309L7.77411 17.182C7.09182 17.2548 6.51109 16.6998 6.58661 16.0369L6.84703 13.7668L13.6856 7.1725C14.2819 6.59745 15.2455 6.59745 15.8392 7.1725L16.9642 8.25732C17.5606 8.83238 17.5606 9.76402 16.9668 10.3366ZM14.3939 11.1125L12.8809 9.65353L8.04234 14.3218L7.85224 15.9616L9.55276 15.7783L14.3939 11.1125ZM16.0814 9.11112L14.9564 8.0263C14.8496 7.92334 14.6752 7.92334 14.571 8.0263L13.7663 8.80225L15.2793 10.2612L16.084 9.48528C16.1882 9.37981 16.1882 9.21408 16.0814 9.11112Z" fill="#FD5A3B"/>
            </svg>`
};

doaj.triage.questions.Question = class {
    static $all = [];
    static save_reminder_text = `You’ve changed one or more values. Click <span class="answer compliant">Continue triage</span> to save your changes and move to the next question.`

    static getByIdx(idx) {
        return this.$all.find(q => q.idx === idx);
    }

    static getByName(name) {
        return this.$all.find(q => q.name === name);
    }


    static init() {
        this.$all = doaj.triage.questions._ids().map(
            (name, index) => new this(name, index)
        );
    }


    constructor(name, idx) {
        this.name = name;
        this.idx = idx;

        this.$wrapper = $(`#${name}`);
        this.instructions = new doaj.triage.instructions.Drawer(this);
        this.$headerBtn = this.$wrapper.find(
            ".criterion-wrapper--header > button"
        );
        this.$body = $(`#${this.$headerBtn.attr("aria-controls")}`);
        this.group = QuestionGroup.getByElement(
            this.$wrapper.closest(".question-group")
        );

        this.pendingAction = false;

        this.$reviewOutcomeContainer = this.$wrapper.find(
            ".review_outcome-container"
        )

        this.$reminder = this.$wrapper.find(".save-reminder");
        this.$reminderText = this.$reminder.find(".save-reminder-text");

        this.$answerInput = this.$wrapper.find(
            "input[data-role='answer']"
        );
        this.$changeAnswerBtn = this.$wrapper.find(
            "button[data-role='change_answers']"
        );
        this.$actionInput = this.$wrapper.find(
            "input[type='radio'][value='action']"
        )
        this.$actionSection = this.$wrapper.find(
            "div.action-container"
        );
        this.$continueBtn = this.$wrapper.find(
            "button[data-role='continue-triage']"
        );

        this.$editBtn = this.$wrapper.find(".button-edit");
        this.$confirmCheckboxes = this.$wrapper.find(".confirmation-checkbox");
        if (this.$confirmCheckboxes.length > 0) {
            this.$changeAnswerBtn.remove();
            this.$answerInput.prop("disabled", this.$confirmCheckboxes.filter(":not(:checked)").length !== 0);
        }

        this.$checkboxOther = this.$wrapper.find(
            "input[type='checkbox'][data-role='other_option']"
        )
        if (this.$checkboxOther.length) {
            const controlledId = this.$checkboxOther.attr("data-controls");

            const $otherValue = this.$wrapper
                .find("#" + controlledId)
                .closest("[data-role='other_value']");

            if (this.$checkboxOther.is(":checked")) {
                $otherValue._show();
            } else {
                $otherValue._hide();
            }
        }

        this.$checkboxNone = this.$wrapper.find(
            "input[type='checkbox'][value='none']"
        )
        const noneIsChecked = this.$checkboxNone.is(":checked");
        const $otherCheckboxes = this.$checkboxNone
            .closest("fieldset")
            .find("input[type='checkbox']")
            .not(this.$checkboxNone);

        if (noneIsChecked) {
            $otherCheckboxes.prop("checked", false);
        }

        $otherCheckboxes.prop("disabled", noneIsChecked);

        this.$srAnswer = this.$wrapper.find(".sr-answer");

        this.answer = this.checkAnswered();

        if (this.answer) {
            this.$continueBtn.addClass("checked");
        }
        this._setupEvents();
    }

    _setupEvents() {
        this.$answerInput.on("click", (event) => {
            this.setAnswer($(event.currentTarget));
        });

        this.$changeAnswerBtn.on("click", () => {
            this.changeAnswer();
        });

        this.$continueBtn.on("click", () => {
            this.continueTriage();
        });

        const $show_by_default_checkbox = $("#ew_header--show_instructions_by_default");
        $show_by_default_checkbox.on("click", () => {
            doaj.triage.instructions.Drawer.show_by_default = $show_by_default_checkbox.is(":checked");
            if (this.expanded) {
                if ($show_by_default_checkbox.is(":checked")) {
                    this.instructions.open();
                } else {
                    this.instructions.close();
                }
            }
        })

        if (this.$checkboxNone) {
            this.$checkboxNone.on("change", () => {
                const noneIsChecked = this.$checkboxNone.is(":checked");

                const $otherCheckboxes = this.$checkboxNone
                    .closest("fieldset")
                    .find("input[type='checkbox']")
                    .not(this.$checkboxNone);

                if (noneIsChecked) {
                    $otherCheckboxes.prop("checked", false);
                }

                $otherCheckboxes.prop("disabled", noneIsChecked);
            });
        }

        if (this.$checkboxOther) {
            this.$checkboxOther.on("change", () => {
                const controlledId = this.$checkboxOther.attr("data-controls");

                const $otherValue = this.$wrapper
                    .find("#" + controlledId)
                    .closest("[data-role='other_value']");

                if (this.$checkboxOther.is(":checked")) {
                    $otherValue._show();
                    $otherValue.trigger("focus");
                } else {
                    $otherValue.find("input").val("");
                    $otherValue._hide();
                }
            })
            this.$wrapper.find("input").not(".review-outcome-answer").on("change", () => {
                if (this.answer) {
                    if (this.answer.val() !== "action") {
                        this.changeAnswer()
                    } else {
                        this.$answerInput.prop("checked", false);
                        this.$headerBtn.find(".answer-icon").remove();
                        this.answer = null;
                        this.pendingAction = true;
                        this.$continueBtn.removeClass("checked");
                    }
                }
            });
            this.$editBtn.on("click", function() {
                const controlledId = $(this).attr("aria-controls");
                const question = doaj.triage.questions.Question.getByName(controlledId);
                if (question) {
                    question.activate();
                }
            })
        }

        this.$confirmCheckboxes.on("click", () => {
            this.$answerInput.prop("checked", false);
            this.$answerInput.prop("disabled", this.$confirmCheckboxes.filter(":not(:checked)").length !== 0);
        });
    }

    _show_save_reminder() {
        this.$reminder._show();
        setTimeout(() => {
            this.$reminderText.html(Question.save_reminder_text);
        }, 0);
    }

    _hide_save_reminder() {
        this.$reminder._hide();
        this.$reminderText.empty();
    }
    continueTriage() {
        const wasPending = this.pendingAction;

        if (wasPending) {
            this.$actionInput.prop("checked", true);
        }

        doaj.triage.requestSave({
            blocking: true,

            onSuccess: () => {
                if (wasPending) {
                    this.pendingAction = false;
                    this.answer = this.$actionInput;
                    this._setupAnswered(this.answer);
                }

                this.activateNext();
            },

            onFailure: () => {
                if (wasPending) {
                    // Prevent another whole-form save from accidentally
                    // persisting this unconfirmed action answer.
                    this.$actionInput.prop("checked", false);
                }
            }
        });
    }

    changeAnswer() {
        this.$answerInput.prop("checked", false);
        this.$actionSection._hide();
        this.$reviewOutcomeContainer._show();
        this.$answerInput.parent()._show();
        this.$headerBtn.find(".answer-icon").remove();
        this.answer = null;
        this.pendingAction = false;
        this.$continueBtn.removeClass("checked");

        doaj.triage.requestSave();
    }

    checkAnswered() {
        const $answer = this.$wrapper
            .find('[data-role="answer"]:checked')
            .first();
        if ($answer.length) {
            this._setupAnswered($answer);
            return $answer;
        }
        return null;
    }

    setAnswer($answer) {
        if ($answer.val() === "action") {
            this.pendingAction = true;
            this.$actionInput.prop("checked", false);
            this._setupAnswered($answer);
        } else {
            this.answer = $answer;
            doaj.triage.requestSave({
                blocking: true,

                onSuccess: () => {
                    this.answer = $answer;
                    this._setupAnswered($answer);
                    this.activateNext();
                }
            });
        }
    }

    _setupAnswered($answer) {
        if ($answer.val() === "action") {
            this.$reviewOutcomeContainer._hide();
            this.$actionSection._show();
            const answerLabel = $('label[for="' + $answer.attr("id") + '"]').text().trim();
            this.$actionSection.find("span.your-answer").html(answerLabel);
            if (this.pendingAction) {
                this.$actionSection.find("input").first().trigger("focus");
            } else {
                this._hide_save_reminder();
                this.$headerBtn.find(".answer-icon").remove();
                const answerVal = $answer.val();
                this.$headerBtn.prepend(
                    doaj.triage.questions.answerIcons[answerVal]
                );
                this.$continueBtn.addClass("checked");
                this.$srAnswer.text(`Answered: ${answerVal}`);
            }
        } else {
            this.$answerInput.not($answer).parent()._hide();
            this.$changeAnswerBtn.parent()._show();
            this.$headerBtn.find(".answer-icon").remove();
            const answerVal = $answer.val();
            this.$headerBtn.prepend(
                doaj.triage.questions.answerIcons[answerVal]
            );
            this.$continueBtn.addClass("checked");
            this.$srAnswer.text(`Answered: ${answerVal}`);
        }
    }

    expand() {
        this.$headerBtn.attr("aria-expanded", "true");
        this.$headerBtn.trigger("focus");
        this.$body._show();
    }

    collapse() {
        this.$headerBtn.attr("aria-expanded", "false");
        this.$body._hide();
    }

    activate() {
        const questions = doaj.triage.questions;
        const previous = questions.currentQuestion;

        if (previous) {
            previous.deactivate();
            this.instructions.close({restoreFocus: false});
        }

        questions.currentQuestion = this;
        QuestionGroup.collapseOtherNonCurrent(this.group);

        this.group.expand();

        this.$headerBtn
            .attr("aria-current", "true")
            .trigger("focus");
        this.expand();
        this.scrollTo();

        if (this.instructions.show_by_default) {
            this.instructions.open();
        }
    }

    activateNext() {
        const next = Question.getNextUnanswered(this);

        if (next) {
            next.activate();
        } else {
            doaj.triage.questions.showOverview();
        }
    }

    static getFirstUnanswered() {
        return this.$all.find(question => !question.answer);
    }

    static getNextUnanswered(current) {
        const afterCurrent = this.$all
            .slice(current.idx + 1)
            .find(question => !question.answer);

        if (afterCurrent) {
            return afterCurrent;
        }

        return this.$all
            .slice(0, current.idx)
            .find(question => !question.answer);
    }

    deactivate() {
        this.$headerBtn.removeAttr("aria-current");
        this.collapse();
    }

    scrollTo() {
        const headersHeight = $("#ew_header").outerHeight() + $("#primary-nav").outerHeight();
        $(".criterion-wrapper").css("scroll-margin-top", `${headersHeight}px`);
        this.$wrapper[0].scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }

    get expanded() {
        return this.$headerBtn.attr("aria-expanded") === "true";
    }
};

doaj.triage.questions.QuestionGroup = class {
    static $all = [];

    static getByElement(element) {
        const name = $(element).attr("id");
        return this.$all.find(group => group.name === name);
    }

    static getByName(name) {
        return this.$all.find(group => group.name === name);
    }

    static init() {
        this.$all = $(".question-group").map(function () {
            return new doaj.triage.questions.QuestionGroup(this.id);
        }).get();
    }

    constructor(name) {
        this.name = name;
        this.$wrapper = $(`#${name}`);
        this.$headerBtn = this.$wrapper.find(
            "> .question-group--header > button"
        );
        this.$body = this.$wrapper.find(
            "> .question-group--body"
        );
    }

    get expanded() {
        return this.$headerBtn.attr("aria-expanded") === "true";
    }

    get containsCurrentQuestion() {
        return this === doaj.triage.questions.currentQuestion?.group;
    }

    expand() {
        /**
         * Makes this group visible
         */
        this.$headerBtn.attr("aria-expanded", "true");
        this.$body._show();
    }

    collapse() {
        this.$headerBtn.attr("aria-expanded", "false");
        this.$body._hide();
    }

    toggle() {
        if (this.expanded) {
            this.collapse();
        } else {
            this.open();
        }
    }

    open() {
        /**
         * the user has requested to open this group; enforce the group-state rules
         */
        if (!this.containsCurrentQuestion) {
            QuestionGroup.collapseOtherNonCurrent(this);
        }

        this.expand();
    }

    static collapseOtherNonCurrent(groupToOpen) {
        this.$all
            .filter(group =>
                group !== groupToOpen &&
                !group.containsCurrentQuestion
            )
            .forEach(group => group.collapse());
    }
};

//----------------- do now ------------------
doaj.triage.instructions.init();
doaj.triage.instructions.Drawer.init();
const QuestionGroup = doaj.triage.questions.QuestionGroup;
const Question = doaj.triage.questions.Question;
QuestionGroup.init();
Question.init();
const $firstUnanswered = Question.getFirstUnanswered();
if ($firstUnanswered) {
    $firstUnanswered.activate();
} else {
    Question.$all[0].activate();
}

doaj.triage.questions.handleQuestionHeaderClick = function (btn) {
    const $btn = $(btn);
    const questionId = $btn.data("question-id");
    const question = Question.getByName(questionId);

    if ($btn.attr("aria-expanded") === "true") {
        question.collapse();
    } else {
        question.activate();
    }
};
doaj.triage.questions.handleQuestionGroupHeaderClick = function (btn) {
    const $btn = $(btn);
    const groupId = $btn.data("group-id");
    const group = QuestionGroup.getByName(groupId);

    if ($btn.attr("aria-expanded") === "true") {
        group.collapse();
    } else {
        group.open();
    }
}
