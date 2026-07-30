if (!window.doaj) { doaj = {} }

doaj.triage = {};

/* ============================================================
 * Configuration
 *
 * asyncURL is injected from the page template (triage.html) after this
 * script loads - nothing in here should ever hardcode a URL or field name.
 * ============================================================ */

doaj.triage.asyncURL = null;

// strings that are used consistently in the templates
doaj.triage.magicStrings = {
    reviewOutcomeFieldset: "-review_outcome",
    yourAnswer: "-your_answer"
}

doaj.triage.selectors = {
    form: "#triage",
    response: "#triage-async-response",

    // Any control whose value contributes to a triage answer. Deliberately
    // selector-based (not a list of field names) so this keeps working as
    // fields are added/removed from the form.
    saveableFields: 'input[type="text"], input[type="url"], input[type="number"], ' +
                     'input[type="radio"], input[type="checkbox"], select, textarea',

    // Every question carries its own Prev/Next (see
    // _triage_compound_base.html) - only the currently-expanded one is ever
    // visible/interactive, but the selector matches all of them.
    nextQuestionButton: ".js-triage-next-question",
    prevQuestionButton: ".js-triage-prev-question",

    // One <section> per question - see doaj.triage.questions below.
    questionWrapper: ".criterion-wrapper",

    // _triage_form.html already renders an (otherwise unused) error
    // container as the first child of the form - the ">" combinator picks
    // that one out specifically, since the same "error-container" class
    // also appears deeper in the DOM (one per fieldset/note field) and
    // those are not ours to touch.
    summaryContainer: "#triage > .error-container",
    summaryLink: "[data-field-error-summary-for]",
    checkboxOther: "input[type='checkbox'][value='other']",
    checkboxNone: "input[type='checkbox'][value='none']",
    answers: "input[type='radio'][data-role='answer']",
    answersContainer: "fieldset.review_outcome-container",
    clearAnswersButton: "button[data-role='change_answers']",
    actionButton: "button[data-controls]",
    actionSection: "div[data-role='action']",

    // Host for the "reject" recommendation panel - see triage.html. Rebuilt
    // in full on every save response, same approach as errors.summary.
    recommendationHost: "#triage-recommendation"
};

// Class + data attribute used to tag error messages we inject next to a
// field, so a later render pass can find, update or remove them again.
doaj.triage.errorNodeClass = "triage-field-error";
doaj.triage.errorNodeDataAttr = "data-field-error-for";
doaj.triage.summaryHostClass = "triage-error-summary-host";
doaj.triage.summaryLinkDataAttr = "data-field-error-summary-for";

/* ============================================================
 * init
 *
 * Wires up:
 *  - the existing manual "Check" / "Save" buttons
 *  - a soft, per-field async save triggered on genuine value changes
 *  - a hard validation gate on the "Next question" placeholder button
 * ============================================================ */

doaj.triage.init = function () {

    $(document).on("click", "#checkBtn", function (event) {
        event.preventDefault();
        doaj.triage.asyncFormSubmit();
    });

    $(document).on("click", "#submitBtn", function (event) {
        event.preventDefault();
        doaj.triage.fullFormSubmit(this);
    });

    // Soft save: fires on "change", not "blur"/"focusout". A single event
    // type covers every control type correctly here, with no per-type
    // branching needed:
    //   - text / textarea / number / url: the browser only fires "change"
    //     on blur if the value actually differs from what it was on focus.
    //   - select / radio / checkbox: fires immediately on selection/toggle.
    // That means someone tabbing through the form with a screen reader (or
    // just reviewing answers without editing them) never triggers a save -
    // there's a genuine value to persist, or there's no request at all.
    $(document).on("change", doaj.triage.selectors.saveableFields, function () {
        doaj.triage.requestSave();
    });

    // Hard gate: "Next question" always forces a save first. If that save
    // comes back with errors, we block and leave the (now more visible)
    // errors in place rather than letting the user move on.
    $(document).on("click", doaj.triage.selectors.nextQuestionButton, function (event) {
        event.preventDefault();
        var questionId = $(event.currentTarget).closest(doaj.triage.selectors.questionWrapper).attr("id");

        doaj.triage.requestSave({
            blocking: true,
            onSuccess: function () {
                doaj.triage.advanceQuestion(questionId);
            }
        });
    });

    // "Previous question" never gates on validation - soft save already
    // persists edits made so far, so this just navigates back.
    $(document).on("click", doaj.triage.selectors.prevQuestionButton, function (event) {
        event.preventDefault();
        var questionId = $(event.currentTarget).closest(doaj.triage.selectors.questionWrapper).attr("id");
        doaj.triage.questions.goPrev(questionId);
    });

    $(document).on("change", doaj.triage.selectors.checkboxOther, function (event) {
        doaj.triage.setupOther($(event.target))
    })
    $(document).on("change", doaj.triage.selectors.checkboxNone, function (event) {
        doaj.triage.setupNone($(event.target))
    })
    $(document).on("change", doaj.triage.selectors.answers, function (event) {
        doaj.triage.setupAnswers($(event.target))
    })
    $(document).on("click", doaj.triage.selectors.clearAnswersButton, function (event) {
        doaj.triage.clearAnswers($(event.target))
    })
    // Findability: clicking an entry in the error summary (see
    // doaj.triage.summary) jumps straight to the field it's about, instead
    // of making the user hunt for it down a very long form.
    $(document).on("click", doaj.triage.selectors.summaryLink, function (event) {
        event.preventDefault();
        var fieldId = $(event.currentTarget).attr(doaj.triage.summaryLinkDataAttr);
        doaj.triage.scrollToField(fieldId);
    });

    // "Question X of N" (in the fixed top banner) doubles as a "jump back
    // to the question you're actually on" button.
    $(document).on("click", "#triage-progress-label", function (event) {
        event.preventDefault();
        doaj.triage.questions.scrollToActive();
    });

    doaj.triage.setupUI();

    // quick implementation of a dependent question within an action group
    $("[data-dependency-trigger]").on("change", function(event) {
        const $trigger = $(event.currentTarget);
        doaj.triage.setupDependents($trigger);
    });
    $("[data-dependency-trigger]").each(function() {
        doaj.triage.setupDependents($(this));
    })
};

doaj.triage.setupDependents = function($trigger) {
    const key = $trigger.attr("data-dependency-trigger");
    const target = $(`[data-dependency-key="${key}"]`)
    const hidden = target.attr("hidden")
    if (hidden) {
        target.removeAttr("hidden");
    } else {
        target.attr("hidden", "true");
    }
}

doaj.triage.setupUI = function () {
    $(doaj.triage.selectors.checkboxOther).each(function () {
        doaj.triage.setupOther($(this));
    })
    $(doaj.triage.selectors.checkboxNone).each(function () {
        doaj.triage.setupNone($(this));
    })
    $(doaj.triage.selectors.answersContainer).each(function () {
        if ($(this).find("input[type='radio']:checked").length > 0) {
            const $checkedAnswer = $(this).find("input[type=radio]:checked");
            // const $changeButtonContainer = $(this).find(doaj.triage.selectors.clearAnswersButton).parent()
            // $(this).find("input[type='radio']").not($checkedAnswer).parent()._hide();
            // $changeButtonContainer._show();
            doaj.triage.setupAnswers($checkedAnswer);
        }
    });
    doaj.triage.questions.setupInit();
}

/* ============================================================
 * scrollToField
 *
 * Shared by the error summary (click a listed issue) - scrolls the field's
 * control(s) into view and focuses it, the way jumping to a real anchor
 * would, but working for radio/checkbox groups too (which have no single
 * element whose id equals field_id).
 * ============================================================ */

doaj.triage.setupNone = function ($that) {
    const $fieldset = $that.closest("fieldset");
    if ($that.is(":checked")) {
        $fieldset.find("input").not($that)
            .prop("checked", false)
            .trigger("change")
            .prop("disabled", true);
    }
    else {
        $fieldset.find("input").not($that)
            .prop("disabled", false);
    }
}
doaj.triage.setupAnswers = function($that) {
    const $fieldset = $that.closest("fieldset");
    let $that_label = $(`label[for="${$that.attr("id")}"]`);
    const $changeButtonContainer = $fieldset.find(doaj.triage.selectors.clearAnswersButton).parent()
    if ($that.is("[data-controls]")){
        $fieldset.find("label").parent()._hide();
        doaj.triage.setupAction($that);
    }
    else {
         if ($that.is(":checked")) {
            $fieldset.find("label").not($that_label).parent()._hide();
            $changeButtonContainer._show();
        }
        else {
            $fieldset.find("label").not($that_label).parent()._show();
            $changeButtonContainer._hide();
        }
    }
    doaj.triage.requestSave();
}

doaj.triage.setupAction = function ($that) {
    const $action_section = $(`#${$that.data("controls")}-container`);
    const $answer_paragraph = $action_section.find("span.answer");
    let $that_label = $(`label[for="${$that.attr("id")}"]`).find(".label-text");
    $action_section._show();
    $answer_paragraph.text($that_label.text());
    $action_section.find("input").each(function () {
        if ($(`label[for="${$(this).attr("id")}"]`).length === 0) {
            $(this).attr("aria-describedby", $answer_paragraph.attr("id"));
        }
    })
    let $action_inputs = $action_section.find("input")
    if ($action_inputs.length > 0) {
        $action_inputs[0].focus()
    }

}

doaj.triage.clearAnswers = function($clearBtn) {
    const compound_name = $clearBtn.data("controls");
    const answers = $clearBtn.data("controls")+doaj.triage.magicStrings.reviewOutcomeFieldset;
    const $answers = $(`#${answers}`).find("input");
    $answers.parent()._show();
    $answers.prop("checked", false);
    if ($clearBtn.hasClass("review-outcome-answer")) {
        $clearBtn.parent()._hide();
    }
    const $action_section = $(`[data-group="${compound_name}"][data-role="additional_info"]`);
    $action_section._hide();
    doaj.triage.requestSave();
}

doaj.triage.setupOther = function ($that) {
    let $input = $that.is("label")
            ? $($that[0].control)
            : $that;
        const controls_id = $input.data("controls");
        if (controls_id.length > 0) {
            let $details = $(`#${controls_id}`)
            let $details_label = $(`label[for="${$details.attr("id")}"]`);
            if ($input.is(":checked")) {
                $details._show();
                $details_label._show();
            }
            else {
                $details._hide();
                $details_label._hide();
            }
        }
}

doaj.triage.scrollToField = function (fieldId) {
    var $fields = $('[name="' + fieldId + '"]');
    if ($fields.length === 0) {
        return;
    }

    // For a radio/checkbox group, focus whichever option is actually
    // selected (most relevant to the user) rather than always the first.
    var $target = $fields.filter(":checked").first();
    if ($target.length === 0) {
        $target = $fields.first();
    }

    // Only the active question's body is ever visible - if this field's
    // question isn't the active one (e.g. the user has since opened a
    // different question), it's sitting inside a hidden accordion body,
    // and scrollIntoView()/focus() on a display:none element are silent
    // no-ops. Expand the right question first so there's actually
    // something visible to scroll to.
    var $question = $target.closest(doaj.triage.selectors.questionWrapper);
    var questionId = $question.attr("id");
    if (questionId && questionId !== doaj.triage.questions.activeQuestionId) {
        doaj.triage.questions.activate(questionId, { scroll: false });
    }

    doaj.triage.questions._scrollWithHeaderOffset($target, "center");
    $target.trigger("focus");
};

/* ============================================================
 * Save orchestration
 *
 * requestSave() is the single entry point both the soft (blur) and hard
 * (next question) triggers go through. Saves are coalesced: if one is
 * already in flight, we don't fire a second request immediately - we just
 * remember that another save is needed and run it once, with whatever the
 * form contains by then, as soon as the current one finishes. This keeps
 * things simple when a user tabs quickly through several fields (no request
 * pile-up, no risk of an earlier response arriving after a later one and
 * clobbering fresher error state).
 * ============================================================ */

doaj.triage._saving = false;
doaj.triage._queuedOptions = null;

doaj.triage.requestSave = function (options) {
    console.log("requestSave");
    const defaultOptions = {
        onSuccess: function () {
            console.log("success");
            $('#triage-save-notification-error')._hide();
            $('#triage-save-notification-success')
                .stop(true, true)
                ._show()
                .delay(3000)
                .fadeOut('slow');
        },
        onFailure: function () {
            console.log("failure");
            $('#triage-save-notification-error')._show();
        }
    }
    options = options || defaultOptions;

    if (doaj.triage._saving) {
        doaj.triage._queuedOptions = doaj.triage._mergeQueuedOptions(doaj.triage._queuedOptions, options);
        return;
    }

    doaj.triage._runSave(options);
    console.log("runSave finished")
};

// Combine a newly-requested save with one already queued, so neither gets
// silently dropped: "blocking" wins if either call asked for it, and the
// most recent onSuccess callback is the one that will actually run.
doaj.triage._mergeQueuedOptions = function (existing, incoming) {
    existing = existing || {};
    return {
        blocking: !!(existing.blocking || incoming.blocking),
        onSuccess: incoming.onSuccess || existing.onSuccess
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
        console.error("Triage async save failed:", textStatus, errorThrown, jqXHR.responseText);
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
        // Invalid: nothing was persisted. Always (re)render the errors so
        // they stay in sync with the latest answers, whether this was a
        // soft (blur) or blocking (next question) save - the severity
        // reflects which kind of save actually produced this response.
        var severity = options.blocking ? doaj.triage.severity.BLOCKING : doaj.triage.severity.SOFT;
        doaj.triage.errors.render(data.validation.errors || [], severity);
        return;
    }

    // No "validation" key means the form validated and has been saved.
    doaj.triage.errors.clearAll();
    doaj.triage.recommendation.render(data.recommendation);

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

doaj.triage.errors = {};

doaj.triage.severity = {
    SOFT: "soft",
    BLOCKING: "blocking"
};

doaj.triage.severityLabel = {
    soft: "Needs attention: ",
    blocking: "Fix this before continuing: "
};

// field_id -> {message, severity} for whatever is currently displayed.
doaj.triage.errors._current = {};

doaj.triage.errors.render = function (errorList, severity) {
    var incoming = {};
    errorList.forEach(function (error) {
        var message = error.code && error.code.msg;
        if (error.field_id && message) {
            incoming[error.field_id] = { message: message, severity: severity };
        }
    });

    // Drop anything that no longer has an error.
    Object.keys(doaj.triage.errors._current).forEach(function (fieldId) {
        if (!incoming[fieldId]) {
            doaj.triage.errors._removeOne(fieldId);
        }
    });

    // Create or update only entries that are new or genuinely changed.
    Object.keys(incoming).forEach(function (fieldId) {
        var next = incoming[fieldId];
        var current = doaj.triage.errors._current[fieldId];
        if (!current || current.message !== next.message || current.severity !== next.severity) {
            doaj.triage.errors._renderOne(fieldId, next.message, next.severity);
        }
    });

    doaj.triage.errors._current = incoming;
    doaj.triage.summary.render(incoming);
};

doaj.triage.errors._renderOne = function (fieldId, message, severity) {
    // Radio/checkbox groups render one control per option, all sharing the
    // same "name" - selecting by name (rather than id) works for both that
    // case and the single-control case (text/select/textarea/number).
    var $fields = $('[name="' + fieldId + '"]');
    if ($fields.length === 0) {
        return;
    }

    var label = doaj.triage.severityLabel[severity] || "";
    var $existing = $("[" + doaj.triage.errorNodeDataAttr + "=\"" + fieldId + "\"]");

    if ($existing.length > 0) {
        // Update the existing node in place rather than replace it, so an
        // unrelated screen-reader announcement isn't triggered for a field
        // whose error text/severity is unchanged (that check already
        // happened in render() - by the time we get here, something about
        // this field's error really did change).
        $existing
            .removeClass(doaj.triage.errorNodeClass + "--" + doaj.triage.severity.SOFT)
            .removeClass(doaj.triage.errorNodeClass + "--" + doaj.triage.severity.BLOCKING)
            .addClass(doaj.triage.errorNodeClass + "--" + severity)
            .text(label + message);
        return;
    }

    var $error = $("<p></p>")
        .addClass(doaj.triage.errorNodeClass)
        .addClass(doaj.triage.errorNodeClass + "--" + severity)
        .attr(doaj.triage.errorNodeDataAttr, fieldId)
        .attr("role", "alert")
        .text(label + message);

    // Anchor the message after the group as a whole: a wrapping <fieldset>
    // if there is one (e.g. the radio group's review-outcome fieldset),
    // otherwise directly after the last matching control.
    var $last = $fields.last();
    var $anchor = $last.closest("fieldset");
    if ($anchor.length === 0) {
        $anchor = $last;
    }

    $anchor.after($error);
};

doaj.triage.errors._removeOne = function (fieldId) {
    $("[" + doaj.triage.errorNodeDataAttr + "=\"" + fieldId + "\"]").remove();
};

doaj.triage.errors.clearAll = function () {
    $("[" + doaj.triage.errorNodeDataAttr + "]").remove();
    doaj.triage.errors._current = {};
    doaj.triage.summary.render({});
};

/* ============================================================
 * Error summary ("a way to find the invalid fields to review")
 *
 * Renders a list of every currently outstanding error into the (otherwise
 * unused) error container _triage_form.html already places at the top of
 * the form, each entry linking to its field via scrollToField(). Unlike the
 * inline per-field errors, this is rebuilt in full on every render() call:
 * it's a single aria-live="polite" region rather than one role="alert" per
 * field, so a full rebuild here doesn't cause the same re-announcement
 * problem - "polite" is coalesced/queued by assistive tech rather than
 * interrupting, and it's the one place a changed *count* genuinely is the
 * thing worth announcing.
 * ============================================================ */

doaj.triage.summary = {};

doaj.triage.summary.render = function (errorsByFieldId) {
    var $container = $(doaj.triage.selectors.summaryContainer).first();
    if ($container.length === 0) {
        return;
    }

    $container.addClass(doaj.triage.summaryHostClass).attr("aria-live", "polite");

    var fieldIds = Object.keys(errorsByFieldId);
    if (fieldIds.length === 0) {
        $container.empty();
        return;
    }

    var heading = fieldIds.length === 1
        ? "1 question still needs attention:"
        : fieldIds.length + " questions still need attention:";

    var $list = $("<ul></ul>").addClass("triage-error-summary__list");
    fieldIds.forEach(function (fieldId) {
        var entry = errorsByFieldId[fieldId];
        var $link = $("<a></a>")
            .attr("href", "#")
            .addClass("triage-error-summary__link")
            .addClass("triage-error-summary__link--" + entry.severity)
            .attr(doaj.triage.summaryLinkDataAttr, fieldId)
            .text(entry.message);
        $list.append($("<li></li>").append($link));
    });

    $container
        .empty()
        .append($("<p></p>").addClass("triage-error-summary__heading").text(heading))
        .append($list);
};

/* ============================================================
 * Recommendation panel
 *
 * Kept in sync with every save response - only ever shown for a "reject"
 * recommendation (confirmed with user: nothing else is worth surfacing at
 * the top of the form while triage is still in progress). Rebuilt in full
 * each time, same approach as errors.summary above.
 * ============================================================ */

doaj.triage.recommendation = {};

doaj.triage.recommendation.render = function (recommendation) {
    var $host = $(doaj.triage.selectors.recommendationHost);
    if ($host.length === 0) {
        return;
    }

    if (!recommendation || recommendation.code !== "reject") {
        $host.empty();
        return;
    }

    var $reasons = $("<ul></ul>");
    (recommendation.reasons || []).forEach(function (reason) {
        var text = reason.question.text + " (" + reason.question.name + ") [" + reason.question.field_id + "]: " + reason.answer;
        if (reason.sv) {
            text += " (SV:" + reason.sv + ")";
        }
        if (reason.exception) {
            text += " (Exception(s): " + reason.exception.join(", ") + ")";
        }
        $reasons.append($("<li></li>").text(text));
    });

    $host
        .empty()
        .append($("<p></p>").text("Current Recommendation: " + recommendation.code))
        .append($("<p></p>").text("Reasons:").append($reasons));
};

/* ============================================================
 * Question navigation
 *
 * Exactly one .criterion-wrapper (question) is ever expanded - "active" -
 * at a time; everything else stays collapsed. A question only ever changes
 * on an explicit click - either its own accordion header, or its own
 * Prev/Next buttons (each question carries its own, see
 * _triage_compound_base.html - only the active one's are ever visible).
 * There is deliberately no scroll-driven auto-expand: the question list
 * scrolls like any normal list, and only clicking changes what's open.
 * ============================================================ */

doaj.triage.questions = {};
doaj.triage.questions.activeQuestionId = null;

// Flattened, DOM-order list of every question id on the page - Prev/Next
// navigate purely by position in this list, so fieldset grouping/nesting
// above the question level is irrelevant to them.
doaj.triage.questions._ids = function () {
    return $(doaj.triage.selectors.questionWrapper).map(function () {
        return this.id;
    }).get();
};

doaj.triage.questions._isAnswered = function ($wrapper) {
    var answered = false;
    $wrapper.find(doaj.triage.selectors.saveableFields).each(function () {
        var $field = $(this);
        if ($field.is(":checkbox, :radio")) {
            if ($field.is(":checked")) {
                answered = true;
            }
        } else if ($.trim($field.val() || "") !== "") {
            answered = true;
        }
    });
    return answered;
};

// Each question carries its own Prev/Next (see _triage_compound_base.html)
// - only the currently-active one is ever visible, but keep its buttons'
// disabled state correct regardless (first question: no Prev, last: no Next).
doaj.triage.questions._updateOwnButtons = function (questionId) {
    var ids = doaj.triage.questions._ids();
    var index = ids.indexOf(questionId);
    $(`#${questionId}-prev`).prop("disabled", index <= 0);
    $(`#${questionId}-next`).prop("disabled", index === -1 || index >= ids.length - 1);
};

// The progress bar/label is the one thing still shared (lives in the fixed
// banner at the top - see triage.html), so it's kept in sync separately.
doaj.triage.questions._updateProgress = function (questionId) {
    var ids = doaj.triage.questions._ids();
    var index = ids.indexOf(questionId);
    if (index !== -1) {
        $("#triage-progress").attr({ value: index + 1, max: ids.length });
        $("#triage-progress-label").text("Question " + (index + 1) + " of " + ids.length);
    }
};

// The progress label (#triage-progress-label) is a button, not just text -
// clicking it scrolls the question list to bring the currently active
// question back into view. Needed because each question's Prev/Next now
// scrolls away with its own content (previewing a distant question via its
// header, without using Prev/Next, leaves no other way back to "the one
// I'm actually on").
doaj.triage.questions.scrollToActive = function () {
    var questionId = doaj.triage.questions.activeQuestionId;
    if (!questionId) {
        return;
    }
    var $target = $(`#${questionId}`);
    if ($target.length > 0) {
        doaj.triage.questions._scrollWithHeaderOffset($target, "start");
    }
};

// How long the collapse/expand slide takes - meant to read as a smooth
// transition rather than a showpiece animation, but slow enough to actually
// be felt (200ms read as barely different from instant).
doaj.triage.questions.ANIMATION_MS = 350;

// Both the site nav and .ew_header (the workflow item's title/status
// banner) are position:sticky and sit above the question content at a
// higher z-index, so a plain scrollIntoView({block:"start"}) can leave the
// top chunk of the target tucked underneath them - the browser only
// guarantees the element's edge reaches the *viewport* edge, it has no
// idea a sticky element is floating on top of that same edge. This
// measures where .ew_header actually currently sits on screen (it moves
// as you scroll, and its height itself isn't fixed) and scrolls just far
// enough to clear it, rather than assuming a fixed pixel offset.
doaj.triage.questions._scrollWithHeaderOffset = function ($target, block) {
    var el = $target && $target.get(0);
    if (!el) {
        return;
    }
    var clearance = 16;
    var $stickyHeader = $(".ew_header");
    var safeTop = clearance;
    if ($stickyHeader.length > 0) {
        safeTop = $stickyHeader.get(0).getBoundingClientRect().bottom + clearance;
    }

    var targetRect = el.getBoundingClientRect();
    var delta;
    if (block === "center") {
        var safeHeight = window.innerHeight - safeTop;
        delta = targetRect.top - safeTop - Math.max(0, (safeHeight - targetRect.height) / 2);
    } else {
        delta = targetRect.top - safeTop;
    }
    window.scrollBy({ top: delta, behavior: "smooth" });
};

// Collapses whichever question was previously active, expands questionId,
// and keeps its own Prev/Next plus the shared progress bar in sync.
// Scrolling is opt-in via options.scroll: Prev/Next and the initial
// auto-opened question scroll their target into view within the scrollable
// question list; a manual header click doesn't need to (the user already
// clicked something visible).
//
// The collapse/expand itself is animated (slideUp/slideDown) rather than
// the instant hidden-attribute toggle _hide()/_show() do elsewhere - with
// an instant toggle, the whole page layout jumps in one frame *before* the
// smooth scroll even starts, so the scroll ends up animating across an
// already-changed layout, which is what read as a jarring "blur" rather
// than a smooth transition. Sliding the height open/closed over the same
// short window the scroll animates in makes the two feel like one movement
// instead of a snap followed by a scroll.
//
// The global `[hidden] { display: none !important }` rule (see
// _workflow.scss) would otherwise fight jQuery's own inline height/display
// styles for the whole animation, so the `hidden` attribute is only ever
// applied once a collapse has *finished* (not before), and removed before
// an expand *starts* (not after) - it's never present while an animation
// is actually running.
//
// IMPORTANT: scrollIntoView() only runs in the slideDown *callback*, once
// the expand has fully finished - not synchronously alongside it. Calling
// it immediately (tried first) computes the scroll target against a layout
// that's still actively changing: the question above is still shrinking
// out from under it for the next ~200ms, so the browser's smooth-scroll
// commits to a fixed pixel offset that's correct for the *starting* layout
// but not the *final* one - once the collapse finishes and the page is
// genuinely shorter, that same offset lands much further down the (now
// shorter) document than intended. Live-confirmed as a real bug this way:
// clicking Next from question 6 landed on question 27. Waiting for the
// slide to finish before measuring where to scroll fixes it at the root,
// rather than trying to compensate for a moving target.
doaj.triage.questions.activate = function (questionId, options) {
    options = options || {};
    var $target = $(`#${questionId}`);
    if ($target.length === 0 || questionId === doaj.triage.questions.activeQuestionId) {
        return;
    }

    var previousId = doaj.triage.questions.activeQuestionId;
    if (previousId) {
        var $prevBody = $(`#${previousId}-body`);
        $(`#${previousId}-header`).attr("aria-expanded", "false");
        $(`#${previousId}`).removeClass("is-active");
        $prevBody.stop(true, true).slideUp(doaj.triage.questions.ANIMATION_MS, function () {
            $prevBody.prop("hidden", true).css({ display: "", height: "" });
        });
    }

    var $newBody = $(`#${questionId}-body`);
    $newBody.prop("hidden", false).hide().stop(true, true).slideDown(doaj.triage.questions.ANIMATION_MS, function () {
        if (options.scroll) {
            doaj.triage.questions._scrollWithHeaderOffset($target, "start");
        }
    });
    $(`#${questionId}-header`).attr("aria-expanded", "true");
    $target.addClass("is-active");

    doaj.triage.questions.activeQuestionId = questionId;
    doaj.triage.questions._updateOwnButtons(questionId);
    doaj.triage.questions._updateProgress(questionId);
};

doaj.triage.questions.goNext = function (questionId) {
    var ids = doaj.triage.questions._ids();
    var index = ids.indexOf(questionId);
    if (index === -1 || index >= ids.length - 1) {
        return;
    }
    doaj.triage.questions.activate(ids[index + 1], { scroll: true });
};

doaj.triage.questions.goPrev = function (questionId) {
    var ids = doaj.triage.questions._ids();
    var index = ids.indexOf(questionId);
    if (index <= 0) {
        return;
    }
    doaj.triage.questions.activate(ids[index - 1], { scroll: true });
};

// Runs once on page load: opens the first not-yet-answered question so a
// reviewer resumes where they left off (falls back to the last question if
// everything is already answered).
doaj.triage.questions.setupInit = function () {
    var ids = doaj.triage.questions._ids();
    if (ids.length === 0) {
        return;
    }

    var targetId = ids[ids.length - 1];
    for (var i = 0; i < ids.length; i++) {
        if (!doaj.triage.questions._isAnswered($(`#${ids[i]}`))) {
            targetId = ids[i];
            break;
        }
    }

    doaj.triage.questions.activate(targetId, { scroll: true });
};

// There is no wizard/pagination UI beyond the accordion above, so "advance"
// here just means "go to the next question" plus notifying the DOM in case
// a future implementation wants to react to it too.
doaj.triage.advanceQuestion = function (questionId) {
    doaj.triage.questions.goNext(questionId);
    $(document).trigger("doaj:triage:question-advanced", { questionId: questionId });
};

/* ============================================================
 * Existing manual submit paths (unchanged)
 * ============================================================ */

doaj.triage.asyncFormSubmit = function() {
    let $form = $("#triage");
    let $response = $("#triage-async-response");

    if ($form.length === 0) {
        $response.html("<pre>Unable to find form with id 'triage'.</pre>");
        return;
    }

    let formData = new FormData($form[0]);

    $.ajax({
        url: doaj.triage.asyncURL,
        method: "POST",
        data: formData,
        processData: false,
        contentType: false,
        dataType: "json"
    }).done(function (data) {
        $response.html("<pre>" + JSON.stringify(data, null, 2) + "</pre>");
    }).fail(function (jqXHR, textStatus, errorThrown) {
        var errorPayload = {
            status: jqXHR.status,
            textStatus: textStatus,
            error: errorThrown,
            responseText: jqXHR.responseText
        };
        $response.html("<pre>" + JSON.stringify(errorPayload, null, 2) + "</pre>");
    });
}

doaj.triage.fullFormSubmit = function(submitter) {
    let $form = $("#triage");
    let $response = $("#triage-async-response");

    if ($form.length === 0) {
        $response.html("<pre>Unable to find form with id 'triage'.</pre>");
        return;
    }

    // Submit the form directly (button is outside the form)
    $form[0].submit();
}

doaj.triage.show = function(elements) {
    $(elements)._show();
}

doaj.triage.hide = function(elements) {
    $(elements)._hide();
}

doaj.triage.toggle = function(elements) {
    $(elements)._toggle();
}

doaj.triage.toggleSection = function(section, btn) {
    const $section = $(`#${section}`);
    const $btn = $(btn);
    const expanded = $btn.attr("aria-expanded") === "true";
    $section._toggle();
    $btn.attr("aria-expanded", !expanded.toString());
}

doaj.triage.toggleInput = function(input_id, trigger) {
    console.log("toggle")
    const $input = $(`#${input_id}`);
    const $trigger = $(trigger);
    $input._toggle();
    $input.attr("hidden") === "true" ? $input.focus() : $trigger.focus();
}

doaj.triage.continue = function() {
    console.log("continue clicked")
    doaj.triage.requestSave();
}

doaj.triage.reject = function() {
    console.log("reject")
}
