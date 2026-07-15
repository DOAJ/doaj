/*jshint esversion: 6 */

$(document).ready(function() {

    function initRepeatableFieldList(options) {
        var prefix = options.prefix;
        var removeButtonSelector = options.removeButtonSelector;
        var addButtonSelector = options.addButtonSelector;
        var onAdd = options.onAdd;

        function prepContainer(params) {
            var ne = params.element;
            var reset = params.reset_value;
            var number = params.number;

            ne.id = prefix + '-' + number + '-container';

            ne = $(ne);
            ne.find('[id^=' + prefix + '-]').each(function () {
                var ce = $(this);

                // reset the value
                if (reset) {
                    if (ce.is('select')) {
                        // selects may have no blank option, so val('') can leave nothing selected;
                        // default to the first option instead
                        ce.prop('selectedIndex', 0);
                    } else {
                        ce.val('');
                    }
                }

                // set the id as requested
                var items = ce.attr('id').split('-');
                var id = prefix + '-' + number + '-' + items[2];

                // set both the id and the name to the new id, as per wtforms requirements
                ce.attr('id', id);
                ce.attr('name', id);
            });

            // we also need to update the remove button
            ne.find(removeButtonSelector).each(function () {
                var ce = $(this);
                var id = 'remove_' + prefix + '-' + number;

                // set both the id and the name to the new id
                ce.attr('id', id);
                ce.attr('name', id);
            });
        }

        function showHideFirstRemoveButton() {
            // Hide delete button when there's just one entry
            if ($('[id^=' + prefix + '-][id$="container"]').length === 1) {
                $('#remove_' + prefix + '-0').css('display', 'none');
            } else {
                $('#remove_' + prefix + '-0').css('display', 'inherit');
            }
        }

        function removeItem(event) {
            event.preventDefault();

            var id = $(this).attr("id");
            // strip the leading "remove_" to get the container's short_name (e.g. other_identifiers-0)
            var short_name = id.replace(/^remove_/, '');
            var container = short_name + "-container";

            $("#" + container).remove();

            var count = 0;
            $('[id^=' + prefix + '-][id$="container"]').each(function () {
                prepContainer({
                    element: this,
                    number: count,
                    reset_value: false
                });
                count++;
            });

            showHideFirstRemoveButton();
        }

        $(addButtonSelector).click(function (event) {
            event.preventDefault();

            // get the last entry in the list
            var all_e = $('[id^=' + prefix + '-][id$="container"]');
            var e = all_e.last();

            // make a clone of the last entry
            var ne = e.clone()[0];

            // extract the last entry's number from the container id and increment it
            var items = ne.id.split('-');
            var number = parseInt(items[1]);
            number = number + 1;

            // increment all the numbers
            prepContainer({
                element: ne,
                number: number,
                reset_value: true
            });

            e.after(ne);

            var rem_b = $(removeButtonSelector);
            rem_b.unbind("click");
            rem_b.click(removeItem);
            if (all_e.length === 1) {
                $('#remove_' + prefix + '-1').css('display', 'inherit');
            }

            showHideFirstRemoveButton();

            if (onAdd) {
                onAdd(ne);
            }
        });

        showHideFirstRemoveButton();
        $(removeButtonSelector).click(removeItem);
    }

    initRepeatableFieldList({
        prefix: 'authors',
        removeButtonSelector: '.remove_author__button',
        addButtonSelector: 'button[name=more_authors]'
    });

    initRepeatableFieldList({
        prefix: 'other_identifiers',
        removeButtonSelector: '.remove_identifier__button',
        addButtonSelector: 'button[name=more_other_identifiers]',
        onAdd: function (container) {
            syncIdentifierTypeVisibility($(container).find('.identifier-type-select'));
        }
    });

    // The "Type of identifier" dropdown offers the known identifier types plus an
    // "other" option. The free-text type field is only needed (and shown) when
    // "other" is selected - the rest of the time the dropdown value *is* the type.
    function syncIdentifierTypeVisibility(select) {
        var typeInput = select.closest('.identifier-item').find('.identifier-type-other');
        if (select.val() === 'other') {
            typeInput.show();
        } else {
            typeInput.hide();
        }
    }

    $('#identifier-list').on('change', '.identifier-type-select', function () {
        syncIdentifierTypeVisibility($(this));
    });

    $('.identifier-type-select').each(function () {
        var select = $(this);
        var typeInput = select.closest('.identifier-item').find('.identifier-type-other');
        var existingType = typeInput.val();

        // an existing type that isn't one of the dropdown's known options must have
        // been freely typed in previously, so select "other" and reveal the field
        if (existingType && select.find('option[value="' + existingType + '"]').length === 0) {
            select.val('other');
        }

        syncIdentifierTypeVisibility(select);
    });

    $("#article_metadata_form").on("submit", function () {
        // whenever a known type is selected, that dropdown value is the type -
        // copy it into the (possibly hidden) type field so it gets submitted.
        // Rows the user hasn't engaged with (no identifier value entered) are left
        // alone so they don't get flagged as incomplete.
        $('#identifier-list .identifier-item').each(function () {
            var item = $(this);
            var select = item.find('.identifier-type-select');
            var idInput = item.find('input[id$="-id"]');
            var typeInput = item.find('.identifier-type-other');

            if (select.val() !== 'other' && idInput.val() !== '') {
                typeInput.val(select.val());
            }
        });
    });

    $("#pissn").select2({
        allowClear: false,
        width: 'resolve',
        newOption: 'false'
    });
    $("#eissn").select2({
        allowClear: false,
        width: 'resolve',
        newOption: 'false'
    });

    $("#keywords").select2({
        multiple: true,
        minimumInputLength: 1,
        allowClear: false,
        tags: [],
        tokenSeparators: [','],
        width: 'resolve'
    })

    $("#article_metadata_form").on("submit", function(event) {
        $("button[type=submit]").prop("disabled", true);
    })
 })
