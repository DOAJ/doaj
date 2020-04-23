/*jshint esversion: 6 */

$(document).ready(function() {

    function prepAuthorContainer(params) {
        var ne = params.element;
        var reset = params.reset_value;
        var number = params.number;

        ne.id = 'authors-' + number + '-container';

        ne = $(ne);
        ne.find('[id^=authors-]').each( function () {
            var ce = $(this);

            // reset the value
            if (reset) {
                ce.val('')
            }

            // set the id as requestsed
            items = ce.attr('id').split('-');
            var id = 'authors-' + number + '-' + items[2];

            // set both the id and the name to the new id, as per wtforms requirements
            ce.attr('id', id);
            ce.attr('name', id);
        });

        // we also need to update the remove button
        ne.find("[id^=remove_authors-]").each(function() {
            var ce = $(this);

            // update the id as above - saving us a closure again
            items = ce.attr('id').split('-');
            var id = 'remove_authors-' + number;

            // set both the id and the name to the new id
            ce.attr('id', id);
            ce.attr('name', id);
        })
    }

    function showHideFirstRemoveButton() {
        // Hide delete button when there's just one author
        if ($('[id^=authors-][id$="container"]').length === 1) {
            $('#remove_authors-0').css('display', 'none')
        } else {
            $('#remove_authors-0').css('display', 'inherit')
        }
    }

    function removeAuthor() {
        event.preventDefault();

        var id = $(this).attr("id");
        var short_name = id.split("_")[1];
        var container = short_name + "-container";

        $("#" + container).remove();

        var count = 0;
        $('[id^=authors-][id$="container"]').each(function() {
            prepAuthorContainer({
                element : this,
                number: count,
                reset_value: false
            });
            count++;
        });

        showHideFirstRemoveButton()
    }

    $('input[name=more_authors]').click( function(event) {
        event.preventDefault();

        // get the last author div in the list
        var all_e = $('[id^=authors-][id$="container"]');
        var e = all_e.last();

        // make a clone of the last author div
        var ne = e.clone()[0];

        // extract the last author's number from the div id and increment it
        var items = ne.id.split('-');
        var number = parseInt(items[1]);
        number = number + 1;

        // increment all the numbers
        prepAuthorContainer({
            element : ne,
            number : number,
            reset_value : true
        });

        e.after(ne);

        var rem_b = $(".remove_button");
        rem_b.unbind("click");
        rem_b.click(removeAuthor);
        if (all_e.length === 1){
            $('#remove_authors-1').css('display', 'inherit')
        }

        showHideFirstRemoveButton()
	});

    $(".remove_button").click(removeAuthor);

    $("#keywords").select2({
        minimumInputLength: 1,
        tags: [],
        tokenSeparators: [","]
    });

    $("#pissn").select2();
    $("#eissn").select2();
    showHideFirstRemoveButton();

})