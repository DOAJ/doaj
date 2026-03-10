doaj.publisher_csvs = {};

doaj.publisher_csvs.init = function() {
    $("#validate").on("click", function(event) {
        event.preventDefault();

        let fd = new FormData();
        let file = $('#upload-csv-file')[0].files[0];
        if (!file) {
            alert("You must select a file to validate");
            return;
        }
        if (!file.name.endsWith(".csv")) {
            alert("You must provide a CSV file");
            return;
        }

        fd.append("journal_csv", file);

        $("#validation-results").html("Validating your file, please wait ...");

        $.ajax({
           url: "/publisher/journal-csv/validate",
           type: "POST",
           data: fd,
           processData: false,
           contentType: false,
           success: function(response) {
              doaj.publisher_csvs.render_validation_results(response);
           },
           error: function(jqXHR, textStatus, errorMessage) {
               let msg = "There was an unexpected problem validating your file, please try again, and contact us if the problem persists.";
               $("#validation-results").html(msg);
           }
        });
    })
}

doaj.publisher_csvs.render_validation_results = function(response) {

    let generalFrag = "";
    if (response.general && response.general.length > 0) {
        generalFrag += `<h3>General errors</h3><ul>`;
        for (let g of response.general) {
            generalFrag += `<li>[${g[0]}] ${g[1]}</li>`;
        }
        generalFrag += `</ul>`;
    }

    let headerFrag = "";
    if (response.headers && Object.keys(response.headers).length > 0) {
        headerFrag = `<h3>Issues with column titles</h3><ul>`;
        for (let pos in response.headers) {
            let column_name = doaj.publisher_csvs.column_to_sheet_reference(pos);
            headerFrag += `<li>Column ${column_name} [${response.headers[pos][0]}]: ${response.headers[pos][1]}</li>`
        }
        headerFrag += `</ul>`;
    }

    let rowsFrag = "";
    if (response.rows && Object.keys(response.rows).length > 0) {
        rowsFrag = `<h3>Issues with journal records</h3><ul>`;
        for (let pos in response.rows) {
            rowsFrag += `<li>Row ${pos} [${response.rows[pos][0]}]: ${response.rows[pos][1]}</li>`
        }
        rowsFrag += `</ul>`;
    }

    let valuesFrag = "";
    if (response.values && Object.keys(response.values).length > 0) {
        valuesFrag = `<h3>Issues with individual cells</h3><ul>`;
        for (let row in response.values) {
            for (let pos in response.values[row]) {
                let column_name = doaj.publisher_csvs.column_to_sheet_reference(pos);
                valuesFrag += `<li>
                    Row ${row}, Column ${column_name} [${response.values[row][pos][0]}]: ${response.values[row][pos][1]}
                    (was: '${response.values[row][pos][2]}', now: '${response.values[row][pos][3]}')
                    </li>`
            }
        }
        valuesFrag += `</ul>`;
    }

    let successFrag = "";
    if (!response.has_errors) {
        if (response.has_warnings) {
            successFrag = "<h3>File validated successfully but with warnings.</h3> Please check the warnings below and contact us with queries. If all looks good, please send us the file.";
        } else {
            successFrag = "<h3>File validated successfully.</h3>You can now send us the file.";
        }
    }

    let frag = successFrag + generalFrag + headerFrag + rowsFrag + valuesFrag;
    $("#validation-results").html(frag);
}

doaj.publisher_csvs.column_to_sheet_reference = function(n) {
    let r = "";
    while (n >= 0) {
        let charRef = (n%26) + 65;
        r = String.fromCharCode(charRef) + r;
        n = Math.floor(n/26) - 1;
    }
    return r;
}
