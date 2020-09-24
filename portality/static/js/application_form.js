$.extend(doaj, {
    af: {
        active: false,

        newApplicationForm: (params) => {
            return edges.instantiate(doaj.af.ApplicationForm, params);
        },
        ApplicationForm: function(params) {
            this.currentTab = params.hasOwnProperty("currentTab") ? params.currentTab : 0;
            this.previousTab = params.hasOwnProperty("previousTab") ? params.previousTab : 0;
            this.draft_id = params.hasOwnProperty("draft_id") && params.draft_id !== undefined ? params.draft_id : 0;
            this.form_diff = params.hasOwnProperty("form_diff") && params.form_diff !== "" ? params.form_diff : 0;

            this.form = $(".application_form");
            this.context = this.form.attr("context");
            this.tabs = $(".tab");
            this.sections = $(".form-section");

            this.tabValidationState = [];

            this.jq = (selector) => {
                return $(selector, this.form);
            };

            this.init = () => {
                this.jq("input, select").each((idx, inp) => {
                    let name = $(inp).attr("name");
                    // console.log(name);
                    if (name) {
                        name = name.split("-");
                        $(inp).attr("data-parsley-errors-container", "#" + name[0] + "_checkbox-errors");
                    }
                });

                let reviewedSelector = this.jq("#reviewed");
                edges.on(reviewedSelector, "click", this, "manage_review_checkboxes");
                // $("#reviewed").on("click", doaj.af.manage_review_checkboxes);

                for (let i = 0; i < this.tabs.length; i++) {
                    this.tabValidationState.push({"state" : "unvalidated"});
                }

                this.prepareSections();
                this.useStepIndicator();

                // Display the current tab
                if (this.context === "admin") {
                    //this.setup_maned();
                }
                // $(".application_form").parsley().validate();
                //this.currentTab = -1;
                //for (let i = 0; i < this.tabs.length; i++) {
                //    this.next();
                    // showTab(i);
                //}
                // this.currentTab = 0;

                if (this.draft_id !== 0) {
                    // this.validateTabs();
                    this.prepDraftView();
                }

                this.showTab(this.currentTab);

                let nextSelector = this.jq("#nextBtn");
                let prevSelector = this.jq("#prevBtn");
                let submitSelector = this.jq("#submitBtn");
                let draftSelector = this.jq("#saveDraft");

                edges.on(nextSelector, "click", this, "next");
                edges.on(prevSelector, "click", this, "prev");
                edges.on(submitSelector, "click", this, "submitapplication");
                edges.on(draftSelector, "click", this, "savedraft");
            };

            this.destroyParsley = function() {
                if (this.activeParsley) {
                    this.activeParsley.destroy();
                    this.activeParsley = false;
                    this.context.off("submit.Parsley");
                }
                // $(".has-error").removeClass("has-error");
            };

            this.bounceParsley = function() {
                if (!this.doValidation) { return; }
                this.destroyParsley();
                this.activeParsley = this.context.parsley();
            };

            this.showTab = (n) => {
                // This function will display the specified tab of the form ...
                //hide all other tabs
                // if (n < this.sections.length-1){
                //     let hiddenField = this.jq("#validated-" + n);
                //     if (hiddenField.val() === "") {
                //         hiddenField.val("False");
                //     }
                // }

                this.tabs.each((idx, tab) => {
                    $(tab).hide();
                });

                let submitButton = this.jq("#submitBtn");
                let draftButton = this.jq("#draftBtn");
                $(this.tabs[n]).show();
                this.jq("#cannot_save_draft").hide();
                submitButton.hide();
                draftButton.show();
                // ... and fix the Previous/Next buttons:
                if (n === 0) {
                    this.jq("#prevBtn").hide();
                } else {
                    this.jq("#prevBtn").show();
                }

                if (n === (this.tabs.length - 1)) {
                    //show submit button only if all tabs are validated
                    this.jq("#nextBtn").hide();
                    submitButton.hide();
                    draftButton.show();
                    let validated = this.form_validated();
                    if (!validated) {
                        this.jq("#cannot-submit-invalid-fields").show();
                    } else {
                        this.jq("#cannot-submit-invalid-fields").hide();
                        submitButton.show();
                    }

                } else {
                    let nextBtn = this.jq("#nextBtn");
                    nextBtn.show();
                    nextBtn.html("Next");
                    submitButton.hide();
                    draftButton.show();
                }
                this.currentTab = n;
                this.previousTab = n-1;
                // ... and run a function that displays the correct step indicator:
                if(n === this.tabs.length - 1) {
                    // this.jq("#validated-" + n).val("True");
                    this.prepareReview();
                }
                if (this.context === "admin") {
                    // this.modify_view();
                }
                else if (this.context === "public") {
                    this.updateStepIndicator();
                }
                window.scrollTo(0,0);
            };

            this.prepDraftView = () => {
                this.validateTabs();
                for (let i = this.tabValidationState.length - 1; i >= 0; i--) {
                    if (this.tabValidationState[i].state === "valid") {
                        break;
                    }
                    if (this.isTabEmpty(i)) {
                        this.tabValidationState[i].state = "unvalidated";
                        this.jq("[data-parsley-group=block-" + i + "]").each((idx, inp) => {
                            $(inp).parsley().reset();
                        });
                    }
                }
                this.updateStepIndicator();
            };

            this.validateTabs = () => {
                for (let i = 0; i < this.tabs.length - 1; i++) {
                    this.form.parsley().whenValidate({
                        group: 'block-' + i
                    }).done(() => {
                        this.tabValidationState[i].state = "valid";
                    }).fail(() => {
                        this.tabValidationState[i].state = "invalid";
                    });
                }
                this.tabValidationState[this.tabs.length-1].state = "unvalidated";
            };

            this.isTabEmpty = (n) => {
                let section = $(this.sections[n]);
                let inputs = section.find(":input");
                for (let i = 0; i < inputs.length; i++) {
                    let inp = $(inputs[i]);
                    let type = $(inp).attr("type");
                    if (type === "radio" || type === "checkbox") {
                        if (inp.is(":checked")) {
                            return false;
                        }
                    } else {
                        if (inp.val() !== "") {
                            return false;
                        }
                    }
                }
                return true;
            };

            this.prepareReview = () => {
                for (let i = 0; i < formulaic.active.fieldsets.length; i++){
                    this._generate_section_header();
                    $(formulaic.active.fieldsets[i]).each(() => {
                        if (1){     //field should be shown
                        }
                    })
                }
            }

            this.prepareReview_old = () => {
                let review_values = $("td[id$='__review_value']");
                review_values.each((idx, question) => {
                    let id = $(question).attr('id');
                    // TODO: think about how to generalise this.  If we add more fields like this or
                    // change the apc_charges bit then it will need updating
                    if (id === "apc_charges__review_value") {
                        let currency = $("select[id$='apc_currency']");
                        let max = $("input[id$='apc_max']");
                        let result = "";
                        let isValid = true;
                        for (let i = 0; i < currency.length; i++){
                            let curr = $(currency[i]).find('option:selected').text();
                            let m = $(max[i]).val();
                            if (m !== "" || curr !== "") {
                                result += (m === "" ? "" : m) + " " + (curr === "" ? "" : curr) + " " + "<br>";
                            }
                        }
                        if ($(max[0]).parsley().validationResult !== true || ($(currency[0]).parsley().validationResult !== true)) {
                            isValid = false;
                        }
                        if (result === "" && isValid){
                            $(question).parent().hide();
                        }
                        else {
                            $(question).parent().show();
                            $(question).html(result);
                        }
                    }
                    else {
                        let name = id.substring(0, id.indexOf("__review_value"));
                        let input = $("input[name^='" + name + "']");
                        if (input.length === 0) {  //it's not input but select
                            input = $("[name^='" + name + "']");
                            let result = "";
                            input.each((idx, inp) => {
                                let val = $(inp).find('option:selected').text();
                                if (val !== "") {
                                    result += val + "<br>";
                                }

                            });
                            $(question).html(result);
                        } else {
                            if (id === "keywords__review_value") {
                                let result = "";
                                let this_input = $('#keywords');
                                let keywords = this_input.val().split(",");
                                if (keywords.length !== 1) {
                                    $(keywords).each((idx, kw) => {
                                        result += kw + "<br>";
                                    });
                                }
                                else {
                                    result = keywords[0];
                                }
                                $(question).html(result);


                            } else {
                                if ($(input).attr("data-parsley-required-if") !== undefined) {
                                    if (input.val() === "" && $(input).parsley().validationResult === true){
                                        $(question).parent().hide();
                                        return;
                                    }
                                    else {
                                        $(question).parent().show();
                                    }
                                }
                                let type = input.attr("type");
                                if (type === "text" || type === "number") {
                                    $(question).html(input.val())
                                } else if (type === "url") {
                                    $(question).html('<a href=' + input.val() + '>' + input.val() + '</a>')
                                } else if (type === "radio") {
                                    if (input.is(":checked")) {
                                        let text = $('label[for=' + $(input.filter(':checked')).attr('id') + ']').text();
                                        $(question).html(text);
                                    }
                                } else if (type === "checkbox") {
                                    let result = '';
                                    input.each((idx, i) => {
                                        if ($(i).is(":checked")) {
                                            let text = $('label[for=' + $(i).attr('id') + ']').text();
                                            result += text + "<br>";
                                        }
                                    });
                                    $(question).html(result)
                                }
                            }
                        }
                    }

                })
            };

            this.form_validated = () => {
                let result = true;
                let inputs = this.jq("[name^='validated']");
                $(inputs).each((idx, input) => {
                    if (idx === inputs.length-1) {
                        return result;
                    }
                    if ($(input).val() !== "True") {
                        result = false;
                        return;
                    }
                });
                return result;
            };

            this.next = () => {
                this.navigate(this.currentTab + 1);
            };

            this.prev = () => {
                this.navigate(this.currentTab - 1, true);
            };

            this.submitaplication = () => {
                let parsleyForm = this.form.parsley();
                this.form.submit();
            };

            this.savedraft = () => {
                this.form.attr('novalidate', 'novalidate');
                var draftEl = $("input[name=draft]");
                if (draftEl.length === 0) {
                    let input = $("<input>")
                       .attr("type", "hidden")
                       .attr("name", "draft").val(true);
                    this.form.append($(input));
                } else {
                    draftEl.val(true);
                }

                let parsleyForm = this.form.parsley();
                parsleyForm.destroy();
                this.form.submit();
            };

            this.navigate = (n, showEvenIfInvalid = false) => {

                // Hide the current tab:
                // let form = $('#' + '{{ form_id }}');

                this.form.parsley().whenValidate({
                    group: 'block-' + this.currentTab
                }).done(() => {
                    // $("#validated-" + this.currentTab).val("True");
                    this.tabValidationState[this.currentTab].state = "valid";
                    this.previousTab = n-1;
                    this.currentTab = n;
                    // Otherwise, display the correct tab:
                    this.showTab(this.currentTab);
                }).fail(() => {
                    // $("#validated-" + this.currentTab).val("False");
                    this.tabValidationState[this.currentTab].state = "invalid";
                    if (showEvenIfInvalid){
                        this.previousTab = n-1;
                        this.currentTab = n;
                        // Otherwise, display the correct tab:
                        this.showTab(this.currentTab);
                    }

                });
            };

            this.updateStepIndicator = () => {
                $(".application-nav__list-item").each((idx, x) => {
                    if (idx === this.currentTab) {
                        x.className = "application-nav__list-item application-nav__list-item--active";
                    }
                    else {
                        if (this.tabValidationState[idx].state === "valid") {
                            x.className = "application-nav__list-item application-nav__list-item--done";
                        } else if (this.tabValidationState[idx].state === "invalid") {
                            x.className = "application-nav__list-item application-nav__list-item--invalid";
                        }
                        else {
                            x.className = "application-nav__list-item";
                        }
                    }
                });
                //... and adds the "active" class to the current step:

                $("#page_link-" + this.currentTab).className = "page_link";
            };

            this.useStepIndicator = () => {
                $('[id^="page_link-"]').each((i, x) => {
                    $(x).on("click", () => {
                        if (this.context === "public" && this.tabValidationState[i].state === 'unvalidated') {
                            //dev only!
                            //navigate(i);
                            return false;
                        } else {
                            this.navigate(i, true);
                        }
                    });
                });
            };

            this.prepareSections = () => {

                this.sections.each((idx, section) => {
                    $(section).find("input, select").each((i, input) => {
                        $(input).attr('data-parsley-group', 'block-' + idx);
                    });
                });

                this.jq('[id^="page_link-"]').each((i, menu) =>  {
                    $(menu).className = "page_link--disabled";
                });
            };

            this.manage_review_checkboxes = () => {
                if (this.jq("#reviewed").checked) {
                    this.form_validated() ? this.jq("#submitBtn").show() : this.jq("#submitBtn").hide()
                }
            };

            // construct
            this.init();
        }
    }
});

window.Parsley.addValidator("requiredIf", {
    validateString : function(value, requirement, parsleyInstance) {
        let field = parsleyInstance.$element.attr("data-parsley-required-if-field");
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

window.Parsley.addValidator("requiredvalue", {
    validateString : function(value, requirement) {
        return (value === requirement);
    },
    messages: {
        en: 'DOAJ only indexed open access journals which comply with the statement above. Please check and update the open access statement of your journal. You may return to this application at any time.'
    },
    priority: 32
});

window.Parsley.addValidator("optionalIf", {
    validateString : function(value, requirement) {
        theOtherField = $("[name = " + requirement + "]");
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

window.Parsley.addValidator("differentTo", {
    validateString : function(value, requirement) {
      return (!value || ($("[name = " + requirement + "]")).val() !== value)
    },
    messages: {
        en: 'Value of this field and %s field must be different'
    },
    priority: 1
});