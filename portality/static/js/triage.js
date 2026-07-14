if (!window.doaj) { doaj = {} }

doaj.triage = {};

/* ============================================================
 * Configuration
 *
 * asyncURL is injected from the page template (triage.html) after this
 * script loads - nothing in here should ever hardcode a URL or field name.
 * ============================================================ */

doaj.triage.asyncURL = null;

doaj.triage.selectors = {
    form: "#triage",
    response: "#triage-async-response",

    // Any control whose value contributes to a triage answer. Deliberately
    // selector-based (not a list of field names) so this keeps working as
    // fields are added/removed from the form.
    saveableFields: 'input[type="text"], input[type="url"], input[type="number"], ' +
                     'input[type="radio"], input[type="checkbox"], select, textarea',

    // The placeholder "Next question" button lives in _triage_compound.html.
    // Only the class/data-attribute contract below is relied on here.
    nextQuestionButton: ".js-triage-next-question"
};

// Class + data attribute used to tag error messages we inject next to a
// field, so a later render pass can find and remove them again.
doaj.triage.errorNodeClass = "triage-field-error";
doaj.triage.errorNodeDataAttr = "data-field-error-for";

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
        var $button = $(event.currentTarget);

        doaj.triage.requestSave({
            blocking: true,
            onSuccess: function () {
                doaj.triage.advanceQuestion($button);
            }
        });
    });
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
    options = options || {};

    if (doaj.triage._saving) {
        doaj.triage._queuedOptions = doaj.triage._mergeQueuedOptions(doaj.triage._queuedOptions, options);
        return;
    }

    doaj.triage._runSave(options);
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

doaj.triage.errors.render = function (errorList, severity) {
    doaj.triage.errors.clearAll();

    errorList.forEach(function (error) {
        var message = error.code && error.code.msg;
        if (error.field_id && message) {
            doaj.triage.errors._renderOne(error.field_id, message, severity);
        }
    });
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

doaj.triage.errors.clearAll = function () {
    $("[" + doaj.triage.errorNodeDataAttr + "]").remove();
};

/* ============================================================
 * Question navigation
 *
 * There is no wizard/pagination UI yet - "Next question" is currently just
 * a placeholder button (see _triage_compound.html). Once the save behind it
 * succeeds, there's nothing further for us to do here, so we notify the DOM
 * in case a future navigation implementation wants to react to it.
 * ============================================================ */

doaj.triage.advanceQuestion = function ($button) {
    var questionId = $button.data("question-id");
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
