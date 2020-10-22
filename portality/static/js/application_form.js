"use strict";
doaj.af = {
    active: false
};


doaj.af.applicationFormFactory = (params) => {
    let form = $(".application_form");
    let context = form.attr("data-context");
    switch (context) {
        case "public":
            return doaj.af.newPublicApplicationForm(params);
        case "admin":
            return doaj.af.newManEdApplicationForm(params);
        case "update_request":
            return doaj.af.newUpdateRequestForm(params);
        case "application_read_only":
            return doaj.af.newReadOnlyApplicationForm(params);
        case "editor":
            return doaj.af.newEditorApplicationForm(params);
        case "associate_editor":
            return doaj.af.newAssociateApplicationForm(params);
        default:
            throw "Could not extract a context from the form";
    }
};

doaj.af.journalFormFactory = (params) => {
    let form = $(".application_form");
    let context = form.attr("data-context");
    switch (context) {
        case "admin":
            return doaj.af.newManEdJournalForm(params);
        case "editor":
            return doaj.af.newEditorJournalForm(params);
        case "associate_editor":
            return doaj.af.newAssociateJournalForm(params);
        case "readonly":
            return doaj.af.newReadOnlyJournalForm(params);
        default:
            throw "Could not extract a context from the form";
    }
};

doaj.af.newBaseApplicationForm = function(params) {
    return new doaj.af.BaseApplicationForm(params);
};
doaj.af.BaseApplicationForm = class {
    constructor(params) {
        this.form = $(".application_form");
        this.context = this.form.attr("data-context");
        this.sections = $(".form-section");

        this.editSectionsFromReview = true;

        this.jq("input, select").each((idx, inp) => {
            let name = $(inp).attr("name");
            if (name) {
                name = name.split("-");
                $(inp).attr("data-parsley-errors-container", "#" + name[0] + "_checkbox-errors");
            }
        });

        this.sections.each((idx, section) => {
            $(section).find("input, select").each((i, input) => {
                $(input).attr('data-parsley-group', 'block-' + idx);
            });
        });

        let submitSelector = this.jq("#submitBtn");
        edges.on(submitSelector, "click", this, "submitapplication");
    }

    jq(selector) {
        return $(selector, this.form);
    }

    prepareReview() {
        let review_table = this.jq("#review_table");
        review_table.html("");
        var that = this;
        this.TABS.forEach((tab, i) => {
            if (this.editSectionsFromReview) {
                review_table.append("<th>" + tab.title + "</th><th><a href='#' class='button edit_this_section' data-section=" + i + ">Edit this section</a></th>");
                let sectionSelector = $(".edit_this_section");
                edges.on(sectionSelector, "click", this, "editSectionClicked");
            } else {
                review_table.append("<th colspan='2'>" + tab.title + "</th>");
            }

            tab.fieldsets.forEach((fs) => {
                let fieldset = formulaic.active.fieldsets.find(elem => elem.name === fs);
                fieldset.fields.forEach((f) => {
                    if (f.label !== undefined && !f.hasOwnProperty("conditional") || (f.subfield === undefined && formulaic.active.isConditionSatisfied({field: f.name}))){
                        let value = this.determineFieldsValue(f.name);
                        let text = this.convertValueToText(value);

                        if (f.validate && $.inArray("is_url", f.validate) !== -1) {
                            text = '<a href="' + text + '" target="_blank">' + text + '</a>';
                        }

                        let html = `
                    <tr>
                        <td id="` + f.name + `__review_label">` + f.label + `</td>
                        <td id="` + f.name + `__review_value">` + text +`</td>
                    </tr>
                    `;
                        review_table.append(html);
                    }
                });
            });

        });
    };

    determineFieldsValue(name) {
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

    convertValueToText(value){
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

    submitapplication() {
        this.form.parsley();
        this.form.submit();
    };
};

doaj.af.newTabbedApplicationForm = function(params) {
    return new doaj.af.TabbedApplicationForm(params);
};

doaj.af.TabbedApplicationForm = class extends doaj.af.BaseApplicationForm {

    constructor(params) {
        super(params);

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

        this.tabs = $(".tab");

        this.tabValidationState = [];
        for (let i = 0; i < this.tabs.length; i++) {
            this.tabValidationState.push({"state" : "unvalidated"});
        }

        this.jq('[id^="page_link-"]').each((i, menu) =>  {
            $(menu).className = "page_link--disabled";
        });

        this.useStepIndicator();

        this.showTab(this.currentTab);

        let nextSelector = this.jq("#nextBtn");
        let prevSelector = this.jq("#prevBtn");

        edges.on(nextSelector, "click", this, "next");
        edges.on(prevSelector, "click", this, "prev");

        let reviewedSelector = this.jq("#reviewed");
        edges.on(reviewedSelector, "click", this, "manage_review_checkboxes", false, false, false);
    }

    useStepIndicator() {
        var that = this;
        $('[id^="page_link-"]').each((i, x) => {
            $(x).on("click", () => {
                that.navigate(i, true);
            });
        });
    };

    editSectionClicked(element) {
        let target = $(element).attr("data-section");
        this.showTab(target);
    };

    showTab(n) {
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
            submitButton.show().attr("disabled", "disabled");
            draftButton.show();

            this.form.parsley().whenValidate().done(() => {
                this.jq("#cannot-submit-invalid-fields").hide();
                this.manage_review_checkboxes();
            }).fail(() => {
                this.jq("#cannot-submit-invalid-fields").show();
            });

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

    prepNavigation(clearErrors = true) {
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
        if (clearErrors) {
            this.form.parsley().reset();
        }
    };

    checkBackendValidationFailures() {
        for (let i = 0; i < this.tabs.length - 1; i++) {
            var tab = $(this.tabs[i]);
            var errors = tab.find(".backend_validation_errors");
            if (errors.length > 0) {
                this.tabValidationState[i].state = "invalid";
            }
        }
    };

    validateTabs() {
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

    isTabEmpty(n) {
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

    next() {
        this.navigate(this.currentTab + 1);
    };

    prev() {
        this.navigate(this.currentTab - 1, true);
    };

    navigate(n, showEvenIfInvalid = false) {
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

    updateStepIndicator() {
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

    manage_review_checkboxes() {
        if (this.jq("#reviewed").is(":checked")) {
            this.jq("#submitBtn").show().removeAttr("disabled");
        }
    };
};

doaj.af.newEditorialApplicationForm = function(params) {
    return new doaj.af.EditorialApplicationForm(params);
};

doaj.af.EditorialApplicationForm = class extends doaj.af.BaseApplicationForm {
    constructor(params) {
        super(params);

        this.formDiff = edges.getParam(params.formDiff, false);

        this.sections.each((idx, sec) => {
            $(sec).show();
        });

        var that = this;
        $("#unlock").click(function(event) {
            event.preventDefault();
            let id = $(this).attr("data-id");
            let type = $(this).attr("data-type");
            that.unlock({type : type, id : id})
        });

        this._generate_values_preview();
    }

    displayableDiffValue(was) {
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

    unlock(params) {
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
    };

    _generate_values_preview() {
        $(".admin_value_preview").each((i,elem) => {
            let sourceId = $(elem).attr("data-source");
            let input = $(":input").filter(sourceId);
            let type = input.attr("type");
            let val = input.val();

            if (val && sourceId === "#subject") {
                val = this.lccCodeToText(val);
            }

            if (val) {
                $(elem).html(val);
            } else {
                $(elem).html("[no value]");
            }
        })
    };

    lccCodeToText(code) {
        function recurse(code, tree) {
            for (var i = 0; i < tree.length; i++) {
                var node = tree[i];
                if (node.id === code) {
                    return node.text;
                }

                if (node.children) {
                    let text = recurse(code, node.children);
                    if (text) {
                        return text;
                    }
                }
            }
            return false;
        }
        return recurse(code, doaj.af.lccTree)
    }
};

doaj.af.newPublicApplicationForm = function(params) {
    return new doaj.af.PublicApplicationForm(params);
};

doaj.af.PublicApplicationForm = class extends doaj.af.TabbedApplicationForm {
    constructor(params) {
        super(params);

        this.draft_id = false;

        let draftEl = $("input[name=id]", this.form);
        if (draftEl) {
            this.draft_id = draftEl.val();
        }

        if (this.draft_id) {
            this.prepNavigation();
        }

        let draftSelector = this.jq("#saveDraft");
        edges.on(draftSelector, "click", this, "savedraft");
    }

    savedraft() {
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
};

doaj.af.newUpdateRequestForm = function(params) {
    return new doaj.af.UpdateRequestForm(params);
};

doaj.af.UpdateRequestForm = class extends doaj.af.TabbedApplicationForm {
    constructor(params) {
        super(params);
        this.prepNavigation(false);
    };
};

doaj.af.newReadOnlyApplicationForm = function(params) {
    return new doaj.af.ReadOnlyApplicationForm(params);
};

doaj.af.ReadOnlyApplicationForm = class extends doaj.af.TabbedApplicationForm {
    constructor(params) {
        super(params);
        this.editSectionsFromReview = false;
        this.showTab(this.tabs.length - 1);
    }
};

doaj.af.newManEdApplicationForm = function(params) {
    return new doaj.af.ManEdApplicationForm(params)
};

doaj.af.ManEdApplicationForm = class extends doaj.af.EditorialApplicationForm {
    constructor(params) {
        super(params);

        $("#open_quick_reject").on("click", (e) => {
            e.preventDefault();
            $("#modal-quick_reject").show();
        });
    };
};

doaj.af.newEditorApplicationForm = function(params) {
    return new doaj.af.EditorApplicationForm(params);
};

doaj.af.EditorApplicationForm = class extends doaj.af.EditorialApplicationForm {
    constructor(params) {
        super(params);
    }
};

doaj.af.newAssociateApplicationForm = function(params) {
    return new doaj.af.AssociateApplicationForm(params);
};

doaj.af.AssociateApplicationForm = class extends doaj.af.EditorialApplicationForm {
    constructor(params) {
        super(params);
    }
};

doaj.af.newManEdJournalForm = function(params) {
    return new doaj.af.ManEdJournalForm(params)
};

doaj.af.ManEdJournalForm = class extends doaj.af.EditorialApplicationForm {
    constructor(params) {
        super(params);
    }

    submitapplication() {
        this.form.parsley();
        let optional = this.jq("#make_all_fields_optional").is(":checked");
        if (optional) {
            this.form.parsley().destroy();
        }
        this.form.submit();
    }
};

doaj.af.newEditorJournalForm = function(params) {
    return new doaj.af.EditorJournalForm(params);
};

doaj.af.EditorJournalForm = class extends doaj.af.EditorialApplicationForm {
    constructor(params) {
        super(params);
    }
};

doaj.af.newAssociateJournalForm = function(params) {
    return new doaj.af.AssociateJournalForm(params);
};

doaj.af.AssociateJournalForm = class extends doaj.af.EditorialApplicationForm {
    constructor(params) {
        super(params);
    }
};

doaj.af.newReadOnlyJournalForm = function(params) {
    return new doaj.af.ReadOnlyJournalForm(params);
};

doaj.af.ReadOnlyJournalForm = class extends doaj.af.TabbedApplicationForm {
    constructor(params) {
        super(params);
        this.editSectionsFromReview = false;
        this.showTab(this.tabs.length - 1);
    }
};

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

window.Parsley.addValidator("onlyIf", {
    validateString : function(value, requirement, parsleyInstance) {
        if (!!value){
            let fields = requirement.split(",");
            for (var i = 0; i < fields.length; i++) {
                let field = fields[i];
                let value = parsleyInstance.$element.attr("data-parsley-only-if-value_" + field);
                let not = parsleyInstance.$element.attr("data-parsley-only-if-not_" + field);
                if (value) {
                     if ($("[name=" + field + "]").val() !== value) {
                         return false;
                     }
                }
                if (not) {
                    if ($("[name=" + field + "]").val() === not) {
                         return false;
                     }
                }
            }
            return true;
        }
        else {
            return true;
        }
    },
    messages: {
        en: 'This only can be set when requirements are met'
    },
    priority: 1
});

window.Parsley.addValidator("notIf", {
    validateString : function(value, requirement, parsleyInstance) {
        if (!!value){
            let fields = requirement.split(",");
            for (var i = 0; i < fields.length; i++) {
                let field = fields[i];
                if (!!$("[name=" + field + "]").val()) {
                     return false;
                 }
            }
            return true;
        }
        else {
            return true;
        }
    },
    messages: {
        en: 'This only can be true when requirements are met'
    },
    priority: 1
});
