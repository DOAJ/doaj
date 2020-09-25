'use strict';
$.extend(doaj, {
    af: {
        active: false,

        applicationFormFactory : (params) => {
            let form = $('.application_form');
            let context = form.attr('context');
            switch (context) {
                case 'public':
                    return new this.PublicApplicationForm(params);
                case 'admin':
                    return new this.ManEdApplicationForm(params);
                default:
                    throw 'Could not extract a context from the form';
            }
        },

        ApplicationForm: class {

            constructor(params) {
                this.currentTab = params.hasOwnProperty('currentTab') ? params.currentTab : 0;
                this.previousTab = params.hasOwnProperty('previousTab') ? params.previousTab : 0;
                this.form_diff = params.hasOwnProperty('form_diff') && params.form_diff !== '' ? params.form_diff : 0;

                this.form = $('.application_form');
                this.context = this.form.attr('context');
                this.tabs = $('.tab');
                this.sections = $('.form-section');
                this.draft_id = false;

                this.tabValidationState = [];


                this.jq('input, select').each((idx, inp) => {
                    let name = $(inp).attr('name');
                    // console.log(name);
                    if (name) {
                        name = name.split('-');
                        $(inp).attr('data-parsley-errors-container', '#' + name[0] + '_checkbox-errors');
                    }
                });

                for (let i = 0; i < this.tabs.length; i++) {
                    this.tabValidationState.push({'state' : 'unvalidated'});
                }

                this.prepareSections();
                this.useStepIndicator();

                this.showTab(this.currentTab);

                let nextSelector = this.jq('#nextBtn');
                let prevSelector = this.jq('#prevBtn');
                let sectionSelector = $('.edit_this_section');

                edges.on(nextSelector, 'click', this, 'next');
                edges.on(prevSelector, 'click', this, 'prev');
                edges.on(sectionSelector, 'click', this, 'editSectionClicked');
            }

            jq(selector) {
                return $(selector, this.form);
            }

            editSectionClicked (element) {
                let target = $(element).attr('data-section');
                this.showTab(target);
            }

            showTab(n) {
                this.tabs.each((idx, tab) => {
                    $(tab).hide();
                });

                let submitButton = this.jq('#submitBtn');
                let draftButton = this.jq('#draftBtn');
                $(this.tabs[n]).show();
                this.jq('#cannot_save_draft').hide();
                submitButton.hide();
                draftButton.show();
                // ... and fix the Previous/Next buttons:
                if (n === 0) {
                    this.jq('#prevBtn').hide();
                } else {
                    this.jq('#prevBtn').show();
                }

                if (n === (this.tabs.length - 1)) {
                    //show submit button only if all tabs are validated
                    this.jq('#nextBtn').hide();
                    submitButton.hide();
                    draftButton.show();
                    let validated = this.form_validated();
                    if (!validated) {
                        this.jq('#cannot-submit-invalid-fields').show();
                    } else {
                        this.jq('#cannot-submit-invalid-fields').hide();
                        submitButton.show();
                    }

                } else {
                    let nextBtn = this.jq('#nextBtn');
                    nextBtn.show();
                    nextBtn.html('Next');
                    submitButton.hide();
                    draftButton.show();
                }
                this.currentTab = n;
                this.previousTab = n-1;
                // ... and run a function that displays the correct step indicator:
                if(n === this.tabs.length - 1) {
                    // this.jq('#validated-' + n).val('True');
                    this.prepareReview();
                }
                if (this.context === 'admin') {
                    // this.modify_view();
                }
                else if (this.context === 'public') {
                    this.updateStepIndicator();
                }
                window.scrollTo(0,0);
            }

            prepDraftView() {
                this.validateTabs();
                for (let i = this.tabValidationState.length - 1; i >= 0; i--) {
                    if (this.tabValidationState[i].state === 'valid') {
                        break;
                    }
                    if (this.isTabEmpty(i)) {
                        this.tabValidationState[i].state = 'unvalidated';
                        this.jq('[data-parsley-group=block-' + i + ']').each((idx, inp) => {
                            $(inp).parsley().reset();
                        });
                    }
                }
                let tripwire = false;
                for (let i = 0; i < this.tabValidationState.length - 1; i++) {
                    let tvs = this.tabValidationState[i];
                    if (tvs.state === 'unvalidated') {
                        tripwire = true;
                        break;
                    }
                }
                if (!tripwire) {
                    this.tabValidationState[this.tabValidationState.length - 1].state = 'valid';
                }

                this.updateStepIndicator();
            }

            validateTabs() {
                for (let i = 0; i < this.tabs.length - 1; i++) {
                    this.form.parsley().whenValidate({
                        group: 'block-' + i
                    }).done(() => {
                        this.tabValidationState[i].state = 'valid';
                    }).fail(() => {
                        this.tabValidationState[i].state = 'invalid';
                    });
                }
                this.tabValidationState[this.tabs.length-1].state = 'unvalidated';
            }

            isTabEmpty (n) {
                let section = $(this.sections[n]);
                let inputs = section.find(':input');
                for (let i = 0; i < inputs.length; i++) {
                    let inp = $(inputs[i]);
                    let type = $(inp).attr('type');
                    if (type === 'radio' || type === 'checkbox') {
                        if (inp.is(':checked')) {
                            return false;
                        }
                    } else {
                        if (inp.val() !== '') {
                            return false;
                        }
                    }
                }
                return true;
            }

            prepareReview() {
                // for (let i = 0; i < formulaic.active.fieldsets.length; i++){
                //     this._generate_section_header();
                //     $(formulaic.active.fieldsets[i]).each(() => {
                //         if (1){     //field should be shown
                //         }
                //     })
                // }
            }

            prepareReview_old() {
                let review_values = $('td[id$="__review_value"]');
                review_values.each((idx, question) => {
                    let id = $(question).attr('id');
                    // TODO: think about how to generalise this.  If we add more fields like this or
                    // change the apc_charges bit then it will need updating
                    if (id === 'apc_charges__review_value') {
                        let currency = $('select[id$="apc_currency"]');
                        let max = $('input[id$="apc_max"]');
                        let result = '';
                        let isValid = true;
                        for (let i = 0; i < currency.length; i++){
                            let curr = $(currency[i]).find('option:selected').text();
                            let m = $(max[i]).val();
                            if (m !== '' || curr !== '') {
                                result += (m === '' ? '' : m) + ' ' + (curr === '' ? '' : curr) + ' ' + '<br>';
                            }
                        }
                        if ($(max[0]).parsley().validationResult !== true || ($(currency[0]).parsley().validationResult !== true)) {
                            isValid = false;
                        }
                        if (result === '' && isValid){
                            $(question).parent().hide();
                        }
                        else {
                            $(question).parent().show();
                            $(question).html(result);
                        }
                    }
                    else {
                        let name = id.substring(0, id.indexOf('__review_value'));
                        let input = $('input[name^="' + name + '"]');
                        if (input.length === 0) {  //it's not input but select
                            input = $('[name^="' + name + '"]');
                            let result = '';
                            input.each((idx, inp) => {
                                let val = $(inp).find('option:selected').text();
                                if (val !== '') {
                                    result += val + '<br>';
                                }

                            });
                            $(question).html(result);
                        } else {
                            if (id === 'keywords__review_value') {
                                let result = '';
                                let this_input = $('#keywords');
                                let keywords = this_input.val().split(',');
                                if (keywords.length !== 1) {
                                    $(keywords).each((idx, kw) => {
                                        result += kw + '<br>';
                                    });
                                }
                                else {
                                    result = keywords[0];
                                }
                                $(question).html(result);


                            } else {
                                if ($(input).attr('data-parsley-required-if') !== undefined) {
                                    if (input.val() === '' && $(input).parsley().validationResult === true){
                                        $(question).parent().hide();
                                        return;
                                    }
                                    else {
                                        $(question).parent().show();
                                    }
                                }
                                let type = input.attr('type');
                                if (type === 'text' || type === 'number') {
                                    $(question).html(input.val());
                                } else if (type === 'url') {
                                    $(question).html('<a href=' + input.val() + '>' + input.val() + '</a>');
                                } else if (type === 'radio') {
                                    if (input.is(':checked')) {
                                        let text = $('label[for=' + $(input.filter(':checked')).attr('id') + ']').text();
                                        $(question).html(text);
                                    }
                                } else if (type === 'checkbox') {
                                    let result = '';
                                    input.each((idx, i) => {
                                        if ($(i).is(':checked')) {
                                            let text = $('label[for=' + $(i).attr('id') + ']').text();
                                            result += text + '<br>';
                                        }
                                    });
                                    $(question).html(result);
                                }
                            }
                        }
                    }

                });
            }

            form_validated() {
                let result = true;
                let inputs = this.jq('[name^="validated"]');
                $(inputs).each((idx, input) => {
                    if (idx === inputs.length-1) {
                        return result;
                    }
                    if ($(input).val() !== 'True') {
                        result = false;
                        return;
                    }
                });
                return result;
            }

            next() {
                this.navigate(this.currentTab + 1);
            }

            prev() {
                this.navigate(this.currentTab - 1, true);
            }

            submitapplication() {
                this.form.submit();
            }

            savedraft() {
                this.form.attr('novalidate', 'novalidate');
                let draftEl = $('input[name=draft]');
                if (draftEl.length === 0) {
                    let input = $('<input>')
                        .attr('type', 'hidden')
                        .attr('name', 'draft').val(true);
                    this.form.append($(input));
                } else {
                    draftEl.val(true);
                }

                let parsleyForm = this.form.parsley();
                parsleyForm.destroy();
                this.form.submit();
            }

            navigate (n, showEvenIfInvalid = false) {

                // Hide the current tab:
                // let form = $('#' + '{{ form_id }}');

                this.form.parsley().whenValidate({
                    group: 'block-' + this.currentTab
                }).done(() => {
                    // $('#validated-' + this.currentTab).val('True');
                    this.tabValidationState[this.currentTab].state = 'valid';
                    this.previousTab = n-1;
                    this.currentTab = n;
                    // Otherwise, display the correct tab:
                    this.showTab(this.currentTab);
                }).fail(() => {
                    // $('#validated-' + this.currentTab).val('False');
                    this.tabValidationState[this.currentTab].state = 'invalid';
                    if (showEvenIfInvalid){
                        this.previousTab = n-1;
                        this.currentTab = n;
                        // Otherwise, display the correct tab:
                        this.showTab(this.currentTab);
                    }

                });
            }

            updateStepIndicator() {
                $('.application-nav__list-item').each((idx, x) => {
                    if (idx === this.currentTab) {
                        x.className = 'application-nav__list-item application-nav__list-item--active';
                    }
                    else {
                        if (this.tabValidationState[idx].state === 'valid') {
                            x.className = 'application-nav__list-item application-nav__list-item--done';
                        } else if (this.tabValidationState[idx].state === 'invalid') {
                            x.className = 'application-nav__list-item application-nav__list-item--invalid';
                        }
                        else {
                            x.className = 'application-nav__list-item';
                        }
                    }
                });
                //... and adds the 'active' class to the current step:

                $('#page_link-' + this.currentTab).className = 'page_link';
            }

            useStepIndicator() {
                $('[id^="page_link-"]').each((i, x) => {
                    $(x).on('click',() => {
                        if (this.context === 'public' && this.tabValidationState[i].state === 'unvalidated') {
                            //dev only!
                            //navigate(i);
                            return false;
                        } else {
                            this.navigate(i, true);
                        }
                    });
                });
            }

            prepareSections() {

                this.sections.each((idx, section) => {
                    $(section).find('input, select').each((i, input) => {
                        $(input).attr('data-parsley-group', 'block-' + idx);
                    });
                });

                this.jq('[id^="page_link-"]').each((i, menu) =>  {
                    $(menu).className = 'page_link--disabled';
                });
            }

            unlock (params) {
                let type = params.type;
                let id = params.id;

                let success_callback = () => {
                    window.open('', '_self', ''); //open the current window
                    window.close();
                };

                let error_callback = (jqXHR, textStatus, errorThrown) => {
                    window.alert('error releasing lock: ' + textStatus + ' ' + errorThrown);
                };

                $.ajax({
                    type: 'POST',
                    url: '/service/unlock/' + type + '/' + id,
                    contentType: 'application/json',
                    dataType: 'json',
                    success : success_callback,
                    error: error_callback
                });
            }
        },

        PublicApplicationForm: class extends this.ApplicationForm {
            constructor(params) {
                super(params);
                let draftEl = $('input[name=id]', this.form);
                if (draftEl) {
                    this.draft_id = draftEl.val();
                }

                let reviewedSelector = this.jq('#reviewed');
                edges.on(reviewedSelector, 'click', this, 'manage_review_checkboxes');

                if (this.draft_id) {
                    this.prepDraftView();
                }

                let submitSelector = this.jq('#submitBtn');
                let draftSelector = this.jq('#saveDraft');

                edges.on(submitSelector, 'click', this, 'submitapplication');
                edges.on(draftSelector, 'click', this, 'savedraft');

                edges.up(this, 'init');
            }

            manage_review_checkboxes() {
                let submitBtn = this.jq('#submitBtn');
                if (this.jq('#reviewed').checked) {
                    if(this.form_validated()){
                        submitBtn.show()
                    }
                    else {
                        submitBtn.hide();
                    }
                }
            }
        },

        ManEdApplicationForm: class extends this.ApplicationForm {
            constructor(params) {
                super(params);
                this.currentTab = 6;
                this.previousTab = 5;

                $('.application-nav__list-item').each((idx, x) => {
                    x.className = 'application-nav__list-item application-nav__list-item--active';
                });

                $('#open_quick_reject').on('click', (e) => {
                    e.preventDefault();
                    $('#modal-quick_reject').show();
                });

                $('#unlock').click(function(event) {
                    event.preventDefault();
                    let id = $(this).attr('data-id');
                    let type = $(this).attr('data-type');
                    unlock({type : type, id : id});
                });

                edges.up(this, 'init');
            }

            showTab (n) {
                edges.up(this, 'showTab', [n]);

                if (this.currentTab === 6) {
                    this._modifyReviewPage();
                } else {
                    this._defaultPageView();
                }
            }

            _modifyReviewPage() {
                let page = $('.page');
                page.removeClass('col-md-8');
                page.addClass('col-md-12');
                let buttons = $('.buttons');
                buttons.addClass('col-md-8 col-md-offset-4');
                $('.side-menus').hide();
                this._generate_values_preview();
            }

            _defaultPageView() {
                let page = $('.page');
                page.removeClass('col-md-12');
                page.addClass('col-md-8');
                let buttons = $('.buttons');
                buttons.removeClass('col-md-8 col-md-offset-4');
                $('.side-menus').show();
            }

            _generate_values_preview() {
                $('.admin_value_preview').each((i,elem) => {
                    let sourceId = $(elem).attr('data-source');
                    let input = $(sourceId);
                    if (input.val()) {
                        $(elem).html(input.val());
                    } else {
                        $(elem).html('[no value]');
                    }
                });
            }
        }
    }
});

window.Parsley.addValidator('requiredIf', {
    validateString : function(value, requirement, parsleyInstance) {
        let field = parsleyInstance.$element.attr('data-parsley-required-if-field');
        if ($('[name="' + field + '"]').filter(':checked').val() === requirement){
            return !!value;
        }
        return true;
    },
    messages: {
        en: 'This field is required, because you answered "%s" to the previous question.'
    },
    priority: 33
});

window.Parsley.addValidator('requiredvalue', {
    validateString : function(value, requirement) {
        return (value === requirement);
    },
    messages: {
        en: 'DOAJ only indexed open access journals which comply with the statement above. Please check and update the open access statement of your journal. You may return to this application at any time.'
    },
    priority: 32
});

window.Parsley.addValidator('optionalIf', {
    validateString : function(value) {
        let theOtherField = $('[name = " + requirement + "]');
        if (!!value || !!($(theOtherField)).val()) {
            $(theOtherField).parsley().reset();
            return true;
        }
        return false;
    },
    messages: {
        en: 'You need to provide the answer to either this field or %s field (or both)'
    },
    priority: 300
});

window.Parsley.addValidator('differentTo', {
    validateString : function(value) {
      return (!value || ($('[name = " + requirement + "]')).val() !== value);
    },
    messages: {
        en: 'Value of this field and %s field must be different'
    },
    priority: 1
});