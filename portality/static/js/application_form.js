"use strict";
$.extend(doaj, {
    af: {
        active: false,

        applicationFormFactory : (params) => {
            let form = $(".application_form");
            let context = form.attr("data-context");
            switch (context) {
                case "public":
                    return doaj.af.newPublicApplicationForm(params);
                case "admin":
                    return doaj.af.newManEdApplicationForm(params);
                case "update_request":
                    return doaj.af.newUpdateRequestForm(params);
                default:
                    throw "Could not extract a context from the form";
            }
        },

        journalFormFactory : (params) => {
            let form = $(".application_form");
            let context = form.attr("data-context");
            switch (context) {
                case "admin":
                    return doaj.af.newManEdJournalForm(params);
                default:
                    throw "Could not extract a context from the form";
            }
        },

        newApplicationForm: function(params) {
            return edges.instantiate(doaj.af.ApplicationForm, params);
        },
        ApplicationForm: function(params) {
            this.TABS = [
                {title: "Open access compliance", fieldsets: ["basic_compliance"]},
                {title: "About the Journal", fieldsets: ["about_the_journal", "publisher", "society_or_institution"]},
                {title: "Copyright & licensing", fieldsets: ["licensing", "embedded_licensing", "copyright"]},
                {title: "Editorial", fieldsets: ["peer_review", "plagiarism", "editorial"]},
                {title: "Business model", fieldsets: ["apc", "apc_waivers", "other_fees"]},
                {title: "Best practice", fieldsets: ["archiving_policy", "deposit_policy", "unique_identifiers"]},
            ];

            this.currentTab = params.hasOwnProperty("currentTab") ? params.currentTab : 0;
            this.previousTab = params.hasOwnProperty("previousTab") ? params.previousTab : 0;
            this.form_diff = params.hasOwnProperty("form_diff") && params.form_diff !== "" ? params.form_diff : 0;

            this.form = $(".application_form");
            this.context = this.form.attr("data-context");
            this.tabs = $(".tab");
            this.sections = $(".form-section");
            this.draft_id = false;

            this.tabValidationState = [];
            for (let i = 0; i < this.tabs.length; i++) {
                this.tabValidationState.push({"state" : "unvalidated"});
            }

            this.jq = (selector) => {
                return $(selector, this.form);
            };

            this.init = function() {
                this.jq("input, select").each((idx, inp) => {
                    let name = $(inp).attr("name");
                    if (name) {
                        name = name.split("-");
                        $(inp).attr("data-parsley-errors-container", "#" + name[0] + "_checkbox-errors");
                    }
                });
                this.prepareSections();
                this.useStepIndicator();

                this.showTab(this.currentTab);

                let nextSelector = this.jq("#nextBtn");
                let prevSelector = this.jq("#prevBtn");

                edges.on(nextSelector, "click", this, "next");
                edges.on(prevSelector, "click", this, "prev");
            };

            this.editSectionClicked = function(element) {
                let target = $(element).attr("data-section");
                this.showTab(target);
            };

            this.showTab = function(n) {
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
                    this.prepareReview();
                }
                //if (this.context === "public") {
                    this.updateStepIndicator();
                //}
                window.scrollTo(0,0);
            };

            this.prepNavigation = function() {
                this.validateTabs();
                this.checkBackendValidationFailures();
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
                let tripwire = false;
                for (let i = 0; i < this.tabValidationState.length - 1; i++) {
                    let tvs = this.tabValidationState[i];
                    if (tvs.state === "unvalidated") {
                        tripwire = true;
                        break;
                    }
                }
                if (!tripwire) {
                    this.tabValidationState[this.tabValidationState.length - 1].state = "valid";
                }

                this.updateStepIndicator();
            };

            this.checkBackendValidationFailures = function() {
                for (let i = 0; i < this.tabs.length - 1; i++) {
                    var tab = $(this.tabs[i]);
                    var errors = tab.find(".backend_validation_errors");
                    if (errors.length > 0) {
                        this.tabValidationState[i].state = "invalid";
                    }
                }
            };

            this.validateTabs = function() {
                var that = this;
                for (let i = 0; i < this.tabs.length - 1; i++) {
                    this.form.parsley().whenValidate({
                        group: 'block-' + i
                    }).done(() => {
                        that.tabValidationState[i].state = "valid";
                    }).fail(() => {
                        that.tabValidationState[i].state = "invalid";
                    });
                }
                this.tabValidationState[this.tabs.length-1].state = "unvalidated";
            };

            this.isTabEmpty = function(n) {
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

            this.prepareReview = function() {
                let review_table = this.jq("#review_table");
                review_table.html("");
                var that = this;
                this.TABS.forEach((tab, i) => {
                    review_table.append("<th>" + tab.title + "</th><th><a href='#' class='button edit_this_section' data-section=" + i + ">Edit this section</a></th>");
                    let sectionSelector = $(".edit_this_section");
                    edges.on(sectionSelector, "click", this, "editSectionClicked");
                    tab.fieldsets.forEach((fs) => {
                        let fieldset = formulaic.active.fieldsets.find(elem => elem.name === fs);
                        fieldset.fields.forEach((f) => {
                            if (that.formDiff && that.formDiff[f.name]) {
                                var was = that.formDiff[f.name].a;
                                was = that.displayableDiffValue(was);
                            }
                            if (f.label !== undefined && !f.hasOwnProperty("conditional") || (f.subfield === undefined && formulaic.active.isConditionSatisfied({field: f.name}))){
                                let value = this.determineFieldsValue(f.name);
                                let text = this.convertValueToText(value);

                                if (f.validate && $.inArray("is_url", f.validate) !== -1) {
                                    text = '<a href="' + text + '" target="_blank">' + text + '</a>';
                                }

                                let diff = "";
                                if (was) {
                                    diff = `<tr><td>&nbsp;<strong>WAS</strong></td><td><strong>` + was + `</strong></td></tr>`;
                                }

                                let html = `
                            <tr>
                                <td id="` + f.name + `__review_label">` + f.label + `</td>
                                <td id="` + f.name + `__review_value">` + text +`</td>
                            </tr>
                            ` + diff;
                                review_table.append(html);
                            }
                        });
                    });

                });
            };

            this.displayableDiffValue = function(was) {
                // FIXME: this is pretty unaware, it includes a bunch of assumptions which work for now but which
                // could be made more formal by knowing about the field it's formatting for
                if (!was || was.length === 0) {
                    return "-- no value --"
                }

                if (Array.isArray(was)) {
                    var displayable = [];
                    for (var i = 0; i < was.length; i++) {
                        displayable.push(this.displayableDiffValue(was[i]));
                    }
                    return displayable.join(", ");
                } else if (typeof was === "object") {
                    var keys = Object.keys(was);
                    var displayable = [];
                    for (var i = 0; i < keys.length; i++) {
                        var key = keys[i];
                        displayable.push(this.displayableDiffValue(was[key]));
                    }
                    return displayable.join(" ");
                } else {
                    if (was === "y") {
                        return "Yes";
                    }
                    if (was === "n") {
                        return "No";
                    }
                    return was;
                }
            };

            this.determineFieldsValue = function(name) {
                let inputs = this.jq(":input[id='" + name + "']");
                if (inputs.length === 0) {
                    inputs = this.jq(":input[id^='" + name + "-']");
                }
                let result = [];
                for (let i = 0; i < inputs.length; i++) {
                    let input = $(inputs[i]);
                    let type = input.attr("type");
                    if (type === "text" || type === "number" || type === "url") {
                        result.push(input.val());
                    }
                    else if (type === "radio") {
                        if (input.is(":checked")) {
                             result.push( $("label[for=" + $(input.filter(":checked")).attr("id") + "]").text());
                        }
                    }
                    else if (type === "checkbox") {
                        if (input.is(":checked")) {
                            result.push($("label[for='" + $(input.filter(":checked")).attr("id") + "']").text());
                        }
                    }
                    else if (type === undefined) {        //it means it is select, not input
                        result.push(input.find("option:selected").text());
                    }
                    else {

                        result.push("Something went wrong, question not found.");
                    }
                }
                return result;
            };

            this.convertValueToText = function(value){
                value = value.filter(v=>(v!=="" && v!==" "));
                let result = "";
                if (value.length > 0){
                   result = value[0];
                    for (let i = 1; i < value.length; i++){
                        result = result + ", " + value[i];
                    }
                }
                return result;
            };

            this.form_validated = function() {
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

            this.next = function() {
                this.navigate(this.currentTab + 1);
            };

            this.prev = function() {
                this.navigate(this.currentTab - 1, true);
            };

            this.submitapplication = function() {
                this.form.submit();
            };

            this.savedraft = function() {
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

            this.navigate = function(n, showEvenIfInvalid = false) {

                // Hide the current tab:
                // let form = $('#' + '{{ form_id }}');
                this.form.parsley().whenValidate({
                    group: "block-" + this.currentTab
                }).done(() => {
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

            this.updateStepIndicator = function() {
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

            this.useStepIndicator = function() {
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

            this.prepareSections = function() {

                this.sections.each((idx, section) => {
                    $(section).find("input, select").each((i, input) => {
                        $(input).attr('data-parsley-group', 'block-' + idx);
                    });
                });

                this.jq('[id^="page_link-"]').each((i, menu) =>  {
                    $(menu).className = "page_link--disabled";
                });
            };

            this.unlock = function(params) {
                let type = params.type;
                let id = params.id;

                let success_callback = (data) => {
                    window.open('', '_self', ''); //open the current window
                    window.close();
                };

                let error_callback = (jqXHR, textStatus, errorThrown) => {
                    alert("error releasing lock: " + textStatus + " " + errorThrown)
                };

                $.ajax({
                    type: "POST",
                    url: "/service/unlock/" + type + "/" + id,
                    contentType: "application/json",
                    dataType: "json",
                    success : success_callback,
                    error: error_callback
                })
            }
        },

        newPublicApplicationForm : function(params) {
            return edges.instantiate(doaj.af.PublicApplicationForm, params, doaj.af.newApplicationForm);
        },

        PublicApplicationForm : function(params) {
            this.init = function() {
                // edges.up(this, "init");
                let draftEl = $("input[name=id]", this.form);
                if (draftEl) {
                    this.draft_id = draftEl.val();
                }

                let reviewedSelector = this.jq("#reviewed");
                edges.on(reviewedSelector, "click", this, "manage_review_checkboxes", false, false, false);

                if (this.draft_id) {
                    this.prepNavigation();
                }

                let submitSelector = this.jq("#submitBtn");
                let draftSelector = this.jq("#saveDraft");

                edges.on(submitSelector, "click", this, "submitapplication");
                edges.on(draftSelector, "click", this, "savedraft");

                edges.up(this, "init");
            };

            this.manage_review_checkboxes = function() {
                if (this.jq("#reviewed").is(":checked")) {
                    this.form_validated() ? this.jq("#submitBtn").show() : this.jq("#submitBtn").hide()
                }
            };
        },

        newUpdateRequestForm : function(params) {
            return edges.instantiate(doaj.af.UpdateRequestForm, params, doaj.af.newApplicationForm);
        },

        UpdateRequestForm : function(params) {
            this.init = function() {
                let reviewedSelector = this.jq("#reviewed");
                edges.on(reviewedSelector, "click", this, "manage_review_checkboxes", false, false, false);

                this.prepNavigation();

                let submitSelector = this.jq("#submitBtn");
                edges.on(submitSelector, "click", this, "submitapplication");

                edges.up(this, "init");
            };

            this.manage_review_checkboxes = function() {
                if (this.jq("#reviewed").is(":checked")) {
                    this.form_validated() ? this.jq("#submitBtn").show() : this.jq("#submitBtn").hide()
                }
            };
        },

        newManEdApplicationForm : function(params) {
            return edges.instantiate(doaj.af.ManEdApplicationForm, params, doaj.af.newApplicationForm);
        },
        ManEdApplicationForm : function(params) {
            this.formDiff = edges.getParam(params.formDiff, false);

            this.init = function() {
                this.currentTab = 6;
                this.previousTab = 5;
                var that = this;

                $(".application-nav__list-item").each((idx, x) => {
                    x.className = "application-nav__list-item application-nav__list-item--active";
                });

                $("#open_quick_reject").on("click", (e) => {
                    e.preventDefault();
                    $("#modal-quick_reject").show();
                });

                $("#unlock").click(function(event) {
                    event.preventDefault();
                    let id = $(this).attr("data-id");
                    let type = $(this).attr("data-type");
                    that.unlock({type : type, id : id})
                });

                this.prepNavigation();

                edges.up(this, "init");
            };

            this.showTab = function(n) {
                edges.up(this, "showTab", [n]);

                if (this.currentTab === 6) {
                    this._modifyReviewPage();
                } else {
                    this._defaultPageView();
                }
            };

            this._modifyReviewPage = function() {
                let page = $(".page");
                page.removeClass("col-md-8");
                page.addClass("col-md-12");
                let buttons = $(".buttons");
                buttons.addClass("col-md-8 col-md-offset-4");
                $(".side-menus").hide();
                this._generate_values_preview();
            };

            this._defaultPageView = function() {
                let page = $(".page");
                page.removeClass("col-md-12");
                page.addClass("col-md-8");
                let buttons = $(".buttons");
                buttons.removeClass("col-md-8 col-md-offset-4");
                $(".side-menus").show();
            };

            this._generate_values_preview = function() {
                $(".admin_value_preview").each((i,elem) => {
                    let sourceId = $(elem).attr("data-source");
                    let input = $(":input").filter(sourceId);
                    let type = input.attr("type");
                    if (input.val()) {
                        $(elem).html(input.val());
                    } else {
                        $(elem).html("[no value]");
                    }
                })
            };
        },

        newManEdJournalForm : function(params) {
            return edges.instantiate(doaj.af.ManEdJournalForm, params, doaj.af.newApplicationForm);
        },
        ManEdJournalForm : function(params) {

            this.init = function() {
                this.currentTab = 6;
                this.previousTab = 5;
                var that = this;

                $(".application-nav__list-item").each((idx, x) => {
                    x.className = "application-nav__list-item application-nav__list-item--active";
                });

                $("#unlock").click(function(event) {
                    event.preventDefault();
                    let id = $(this).attr("data-id");
                    let type = $(this).attr("data-type");
                    that.unlock({type : type, id : id})
                });

                this.prepNavigation();

                edges.up(this, "init");
            };

            this.showTab = function(n) {
                edges.up(this, "showTab", [n]);

                if (this.currentTab === 6) {
                    this._modifyReviewPage();
                } else {
                    this._defaultPageView();
                }
            };

            this._modifyReviewPage = function() {
                let page = $(".page");
                page.removeClass("col-md-8");
                page.addClass("col-md-12");
                let buttons = $(".buttons");
                buttons.addClass("col-md-8 col-md-offset-4");
                $(".side-menus").hide();
                this._generate_values_preview();
            };

            this._defaultPageView = function() {
                let page = $(".page");
                page.removeClass("col-md-12");
                page.addClass("col-md-8");
                let buttons = $(".buttons");
                buttons.removeClass("col-md-8 col-md-offset-4");
                $(".side-menus").show();
            };

            this._generate_values_preview = function() {
                $(".admin_value_preview").each((i,elem) => {
                    let sourceId = $(elem).attr("data-source");
                    let input = $(":input").filter(sourceId);
                    let type = input.attr("type");
                    if (input.val()) {
                        $(elem).html(input.val());
                    } else {
                        $(elem).html("[no value]");
                    }
                })
            };
        }
    }
});

window.Parsley.addValidator("requiredIf", {
    validateString : function(value, requirement, parsleyInstance) {
        let field = parsleyInstance.$element.attr("data-parsley-required-if-field");
        if ($("[name='" + field + "']").filter(":checked").val() === requirement){
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
        let theOtherField = $("[name = " + requirement + "]");
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
      return (!value || ($("[name = " + requirement + "]")).val() !== value);
    },
    messages: {
        en: 'Value of this field and %s field must be different'
    },
    priority: 1
});

/*
window.Parsley.addValidator("onlyIf", {
    validateString : function(value, requirement, parsleyInstance) {
        if (!!value){
            let field = parsleyInstance.$element.attr("data-parsley-required-if-field");
            console.log(field);
            return true;
        }
        else {
            console.log("not checked");
            return true;
        }
    },
    messages: {
        en: 'This only can be true when requirements are met'
    },
    priority: 1
});

window.Parsley.addValidator("notIf", {
    validateString : function(value, requirement, parsleyInstance) {
        if (!!value){
            let field = parsleyInstance.$element.attr("data-parsley-required-if-field");
            console.log(field);
            return true;
        }
        else {
            console.log("not checked");
            return true;
        }
    },
    messages: {
        en: 'This only can be true when requirements are met'
    },
    priority: 1
});
 */