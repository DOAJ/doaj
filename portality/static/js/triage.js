if (!window.doaj) { doaj = {}}

doaj.triage = {}
doaj.triage.asyncURL = null;

doaj.triage.init = function() {
    $(document).on("click", "#checkBtn", function (event) {
        event.preventDefault();
        doaj.triage.asyncFormSubmit();
    });

    $(document).on("click", "#submitBtn", function (event) {
        event.preventDefault();
        doaj.triage.fullFormSubmit(this);
    });
}

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

doaj.triage.progress = function() {

}
