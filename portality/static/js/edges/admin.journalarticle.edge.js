$.extend(true, doaj, {

    adminJournalArticleBulkEdit: {

        active: false,

        newMultiFormBox: function (params) {
            params = params === undefined ? {} : params;
            return new doaj.adminJournalArticleBulkEdit.MultiFormBox(params);
        },
        MultiFormBox: function (params) {
            this.selector = params.selector;
            this.slideTime = params.slideTime !== undefined ? params.slideTime : 400;
            this.widths = params.widths !== undefined ? params.widths : {};
            this.bindings = params.bindings !== undefined ? params.bindings : {};
            this.validators = params.validators !== undefined ? params.validators : {};
            this.submitCfg = params.submit !== undefined ? params.submit : {};
            this.urls = params.urls !== undefined ? params.urls : {};

            this.context = false;
            this.initialContent = {};
            this.currentField = false;
            this.defaultWidth = false;
            this.currentWidth = false;
            this.currentError = false;

            this.init = function () {
                this.context = $(this.selector);
                this.defaultWidth = this.context.outerWidth() + "px";
                this.currentWidth = this.defaultWidth;
                this.context.css("width", this.defaultWidth);

                var that = this;
                var containers = this.context.find(".multiformbox-container");
                containers.each(function (i) {
                    var content = $(this).html();
                    var id = $(this).attr("id");
                    that.initialContent[id] = content;
                    $(this).html("");
                });

                var selectBox = this.context.find(".multiformbox-selector");
                var selectHandler = edges.eventClosure(this, "selectChanged");
                selectBox.unbind("change.multiformbox").bind("change.multiformbox", selectHandler);

                var submit = this.context.find(".multiformbox-submit");
                var submitHandler = edges.eventClosure(this, "submit");
                submit.unbind("click.multiformbox").bind("click.multiformbox", submitHandler);

                this.validate();
            };

            this.reset = function () {
                this.transitionPart1({
                    target: false
                });
                this._disableSubmit();
            };

            this.submit = function (element) {
                this._submitting();

                var cfg = this.submitCfg[this.currentField];
                if (!cfg) {
                    cfg = {}
                }

                var sure = false;
                if (cfg.sure) {
                    sure = confirm(cfg.sure);
                } else {
                    sure = true;
                }

                if (!sure) {
                    this._enableSubmit();
                    return;
                }

                var successHandler = edges.objClosure(this, "confirmSubmit");
                var errorHandler = edges.objClosure(this, "submitError");

                this._doSubmit({
                    cfg: cfg,
                    dryRun: true,
                    success: successHandler,
                    error: errorHandler
                });
            };

            this.confirmSubmit = function (data) {
                if (data.error) {
                    alert("There was a problem processing your request.  " + data.error);
                    this.validate();
                    return;
                }

                var sure = confirm('This operation will affect ' + this._affectedMessage(data) + '.');

                if (!sure) {
                    this._enableSubmit();
                    return;
                }

                var cfg = this.submitCfg[this.currentField];
                if (!cfg) {
                    cfg = {}
                }

                var successHandler = edges.objClosure(this, "submissionComplete");
                var errorHandler = edges.objClosure(this, "submitError");

                this._doSubmit({
                    cfg: cfg,
                    dryRun: false,
                    success: successHandler,
                    error: errorHandler
                });
            };

            this.submissionComplete = function (data) {
                var msg = "Your bulk edit request has been submitted and queued for execution.<br>";
                msg += this._affectedMessage(data) + " have been queued for edit.<br>";
                msg += 'You can see your request <a href="' + this._bulkJobUrl(data) + '" target="_blank">here</a> in the background jobs interface (opens new tab).<br>';
                msg += "You will get an email when your request has been processed; this could take anything from a few minutes to a few hours.<br>";
                msg += '<a href="#" id="bulk-action-feedback-dismiss">dismiss</a>';

                $(".bulk-action-feedback").html(msg).show();
                $("#bulk-action-feedback-dismiss").unbind("click").bind("click", function (event) {
                    event.preventDefault();
                    $(".bulk-action-feedback").html("").hide();
                });

                this.reset();
            };

            this._bulkJobUrl = function (data) {
                var url = "/admin/background_jobs?source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22" + data.job_id + "%22%2C%22default_operator%22%3A%22AND%22%7D%7D%2C%22sort%22%3A%5B%7B%22created_date%22%3A%7B%22order%22%3A%22desc%22%7D%7D%5D%2C%22from%22%3A0%2C%22size%22%3A25%7D";
                return url;
            };

            this._doSubmit = function (params) {
                var cfg = params.cfg;
                var dryRun = params.dryRun;
                var success = params.success;
                var error = params.error;

                var query = doaj.adminJournalArticleSearch.activeEdges["#admin_journals_and_articles"].currentQuery.objectify({
                    include_paging: false,
                    include_sort: false,
                    include_aggregations: false,
                    include_source_filters: false
                });

                /*
                var query = elasticSearchQuery({
                    options: doaj.currentFVOptions,
                    include_facets: false,
                    include_fields: false
                });*/

                var data = {};
                if (cfg.data) {
                    data = cfg.data(this.context);
                }
                data["selection_query"] = query;
                data["dry_run"] = dryRun;

                var url = this.urls[this.currentField];
                if (typeof(url) === "function") {
                    url = url();
                }


                $.ajax({
                    type: 'POST',
                    url: url,
                    data: JSON.stringify(data),
                    contentType: 'application/json',
                    success: success,
                    error: error
                });
            };

            this._affectedMessage = function (data) {
                var mfrg = "";
                if (data.affected) {
                    if ("journals" in data.affected && "articles" in data.affected) {
                        mfrg += data.affected.journals + " journals and " + data.affected.articles + " articles";
                    } else if ("journals" in data.affected) {
                        mfrg = data.affected.journals + " journals";
                    } else if ("articles" in data.affected) {
                        mfrg = data.affected.articles + " articles";
                    } else {
                        mfrg = "an unknown number of records";
                    }
                }
                return mfrg;
            };

            this.submitError = function (jqXHR, textStatus, errorThrown) {
                alert('There was an error with your request.');
                this._enableSubmit();
            };

            this.selectChanged = function (element) {
                var val = $(element).val();
                if (val === this.currentField) {
                    return;
                }

                this.transitionPart1({
                    target: val
                });
            };

            this.validate = function () {
                var valid = false;
                var error_id = false;
                if (this.currentField === false || this.currentField === "") {
                    valid = false;
                } else if (!(this.currentField in this.validators)) {
                    valid = true;
                } else {
                    var result = this.validators[this.currentField](this.context);
                    valid = result.valid;
                    if ("error_id" in result) {
                        error_id = result.error_id;
                    }
                }

                if (valid) {
                    this._enableSubmit();
                } else {
                    this._disableSubmit();
                }
                this._showError(error_id);
            };

            this._enableSubmit = function () {
                this.context.find(".multiformbox-submit").removeAttr('disabled').html("Submit");
            };

            this._disableSubmit = function () {
                this.context.find(".multiformbox-submit").attr('disabled', 'disabled').html("Submit");
            };

            this._submitting = function () {
                this.context.find(".multiformbox-submit").attr('disabled', 'disabled').html("<img src='/static/doaj/images/white-transparent-loader.gif'>&nbsp;Submitting...");
            };

            this._showError = function (error_id) {
                if (error_id === false && this.currentError !== false) {
                    this.context.find(".multiformbox-error").hide();
                } else if (error_id !== false && this.currentError !== error_id) {
                    this.context.find(".multiformbox-error").hide();
                    this.context.find("#" + error_id).show();
                }
                this.currentError = error_id;
            };

            this.transitionPart1 = function (params) {
                // first part of the transition is to slide the form up to cover whatever is there right now
                if (this.currentField === false) {
                    this.transitionPart2(params);
                    return;
                }
                var currentContainerId = this.currentField + "-container";
                var current = this.context.find("#" + currentContainerId);
                if (current.length > 0) {
                    params["current"] = current;
                    var clos = edges.objClosure(this, "transitionPart2", false, params);
                    current.slideUp(this.slideTime, clos);
                } else {
                    this.transitionPart2(params);
                    return;
                }
            };

            this.transitionPart2 = function (params) {
                // get rid of the old form, now it is hidden
                if (params.current) {
                    params.current.html("");
                }

                // second part is to adjust the width of the container
                var val = params.target;
                var width = this.defaultWidth;
                if (val in this.widths) {
                    width = this.widths[val];
                }
                if (width === this.currentWidth) {
                    this.transitionPart3(params);
                    return;
                }
                this.currentWidth = width;

                var clos = edges.objClosure(this, "transitionPart3", false, params);
                var that = this;
                this.context.animate({width: width},
                    {
                        duration: this.slideTime,
                        step: function () {
                            that.context.css("overflow", "");
                        },
                        complete: clos
                    }
                );
            };

            this.transitionPart3 = function (params) {
                this.currentField = params.target;
                if (this.currentField === "") {
                    this.currentField = false;
                }
                if (this.currentField === false) {
                    var selectBox = this.context.find(".multiformbox-selector");
                    selectBox.val("");
                    return;
                }

                // final part is to slide out the new form
                var containerId = params.target + "-container";
                var target = this.context.find("#" + containerId);
                if (target.length > 0) {
                    if (containerId in this.initialContent) {
                        target.html(this.initialContent[containerId]);
                    } else {
                        target.html("");
                    }
                }

                if (params.target in this.bindings) {
                    this.bindings[params.target](this.context);
                }

                var validateHandler = edges.eventClosure(this, "validate");
                var inputs = target.find(":input");
                inputs.unbind("keyup.multiformbox").bind("keyup.multiformbox", validateHandler);
                inputs.unbind("change.multiformbox").bind("change.multiformbox", validateHandler);

                target.slideDown(this.slideTime);
                this.validate();
            };

            this.init();
        }
    },

    adminJournalArticleSearch : {
        activeEdges : {},

        journalSelected : function(selector) {
            return function() {
                var type = doaj.adminJournalArticleSearch.activeEdges[selector].currentQuery.listMust(es.newTermFilter({field: "_type"}));
                // var type = doaj.currentFVOptions.active_filters._type;
                if (type && type.length > 0) {
                    type = type[0];
                }
                if (!type || type.value !== "journal") {
                    return {
                        valid: false,
                        error_id: "journal_type_error"
                    }
                }
                return {valid : true};
            }
        },

        anySelected : function(selector) {
            return function() {
                var type = doaj.adminJournalArticleSearch.activeEdges[selector].currentQuery.listMust(es.newTermFilter({field: "_type"}));
                if (!type || type.length === 0) {
                    return {
                        valid: false,
                        error_id: "any_type_error"
                    }
                }
                return {valid: true};
            }
        },

        typeSelected : function(selector) {
            return function() {
                var type = doaj.adminJournalArticleSearch.activeEdges[selector].currentQuery.listMust(es.newTermFilter({field: "_type"}));
                if (type && type.length > 0) {
                    return type[0].value;
                }
                return null;
            }
        },

        titleField : function (val, resultobj, renderer) {
            var field = '<span class="title">';
            var isjournal = false;
            if (resultobj.bibjson && resultobj.bibjson.journal) {
                // this is an article
                field += "<i class='far fa-file-alt'></i>";
            }
            else if (resultobj.suggestion) {
                // this is a suggestion
                field += "<i class='fa fa-sign-in' style=\"margin-right: 0.5em;\"></i>";
            } else {
                // this is a journal
                field += "<i class='fas fa-book-open'></i>";
                isjournal = true;
            }
            if (resultobj.bibjson.title) {
                if (isjournal) {
                    field += "&nbsp<a href='/toc/" + doaj.journal_toc_id(resultobj) + "'>" + edges.escapeHtml(resultobj.bibjson.title) + "</a>";
                } else {
                    field += "&nbsp" + edges.escapeHtml(resultobj.bibjson.title);
                }
                if (resultobj.admin && resultobj.admin.ticked) {
                    field += "&nbsp<img src='/static/doaj/images/tick_short.png' width='16px' height='16px' title='Accepted after March 2014' alt='Tick icon: journal was accepted after March 2014' style='padding-bottom: 3px'>​​";
                }
                if (resultobj.admin && resultobj.admin.seal) {
                    field += "&nbsp<img src='/static/doaj/images/seal_short.png' width='16px' height='16px' title='Awarded the DOAJ Seal' alt='Seal icon: awarded the DOAJ Seal' style='padding-bottom: 3px'>​​";
                }
                return field + "</span>"
            } else {
                return false;
            }
        },

        inDoaj : function(val, resultobj, renderer) {
            var mapping = {
                "false": {"text": "No", "class": "red"},
                "true": {"text": "Yes", "class": "green"}
            };
            var field = "";
            if (resultobj.admin && resultobj.admin.in_doaj !== undefined) {
                if(mapping[resultobj['admin']['in_doaj']]) {
                    var result = '<span class=' + mapping[resultobj['admin']['in_doaj']]['class'] + '>';
                    result += mapping[resultobj['admin']['in_doaj']]['text'];
                    result += '</span>';
                    field += result;
                } else {
                    field += resultobj['admin']['in_doaj'];
                }
                if (field === "") {
                    return false
                }
                return field
            }
            return false;
        },

        authorPays : function(val, resultobj, renderer) {
            var mapping = {
                "Y": {"text": "Has charges", "class": "red"},
                "N": {"text": "No charges", "class": "green"},
                "CON": {"text": "Conditional charges", "class": "blue"},
                "NY": {"text": "No info available", "class": ""}
            };
            var field = "";
            if (resultobj.bibjson && resultobj.bibjson.author_pays) {
                if(mapping[resultobj['bibjson']['author_pays']]) {
                    var result = '<span class=' + mapping[resultobj['bibjson']['author_pays']]['class'] + '>';
                    result += mapping[resultobj['bibjson']['author_pays']]['text'];
                    result += '</span>';
                    field += result;
                } else {
                    field += resultobj['bibjson']['author_pays'];
                }
                if (resultobj.bibjson && resultobj.bibjson.author_pays_url) {
                    var url = resultobj.bibjson.author_pays_url;
                    field += " (see <a href='" + url + "'>" + url + "</a>)"
                }
                if (field === "") {
                    return false
                }
                return field
            }
            return false;
        },

        createdDateWithTime : function (val, resultobj, renderer) {
            return doaj.iso_datetime2date_and_time(resultobj['created_date']);
        },

        lastUpdated : function (val, resultobj, renderer) {
            return doaj.iso_datetime2date_and_time(resultobj['last_updated']);
        },

        doiLink : function (val, resultobj, renderer) {
            if (resultobj.bibjson && resultobj.bibjson.identifier) {
                var ids = resultobj.bibjson.identifier;
                for (var i = 0; i < ids.length; i++) {
                    if (ids[i].type === "doi") {
                        var doi = ids[i].id;
                        var tendot = doi.indexOf("10.");
                        var url = "https://doi.org/" + doi.substring(tendot);
                        return "<a href='" + url + "'>" + edges.escapeHtml(doi.substring(tendot)) + "</a>"
                    }
                }
            }
            return false
        },

        links : function (val, resultobj, renderer) {
            if (resultobj.bibjson && resultobj.bibjson.link) {
                var ls = resultobj.bibjson.link;
                for (var i = 0; i < ls.length; i++) {
                    var t = ls[i].type;
                    var label = '';
                    if (t == 'fulltext') {
                        label = 'Full text'
                    } else if (t == 'homepage') {
                        label = 'Home page'
                    } else {
                        label = t.substring(0, 1).toUpperCase() + t.substring(1)
                    }
                    return "<strong>" + label + "</strong>: <a href='" + ls[i].url + "'>" + edges.escapeHtml(ls[i].url) + "</a>"
                }
            }
            return false;
        },

        journalLicense : function (val, resultobj, renderer) {
            var title = undefined;
            if (resultobj.bibjson && resultobj.bibjson.journal && resultobj.bibjson.journal.license) {
                var lics = resultobj["bibjson"]["journal"]["license"];
                if (lics.length > 0) {
                    title = lics[0].title
                }
            }
            else if (resultobj.bibjson && resultobj.bibjson.license) {
                var lics = resultobj["bibjson"]["license"];
                if (lics.length > 0) {
                    title = lics[0].title
                }
            }

            if (title) {
                if (doaj.licenceMap[title]) {
                    var urls = doaj.licenceMap[title];
                    // i know i know, i'm not using styles.  the attrs still work and are easier.
                    return "<a href='" + urls[1] + "' title='" + title + "' target='blank'><img src='" + urls[0] + "' width='80' height='15' valign='middle' alt='" + title + "'></a>"
                } else {
                    return title
                }
            }

            return false;
        },

        countryName : function (val, resultobj, renderer) {
            if (resultobj.index && resultobj.index.country) {
                return edges.escapeHtml(resultobj.index.country);
            }
            return false
        },

        abstract : function (val, resultobj, renderer) {
            if (resultobj['bibjson']['abstract']) {
                var result = '<a class="abstract_action" href="#" rel="';
                result += resultobj['id'];
                result += '">(show/hide)</a> <span class="abstract_text" style="display:none" rel="';
                result += resultobj['id'];
                result += '">' + '<br>';
                result += edges.escapeHtml(resultobj['bibjson']['abstract']);
                result += '</span>';
                return result;
            }
            return false;
        },

        issns : function (val, resultobj, renderer) {
            if (resultobj.bibjson && resultobj.bibjson.identifier) {
                var ids = resultobj.bibjson.identifier;
                var issns = [];
                for (var i = 0; i < ids.length; i++) {
                    if (ids[i].type === "pissn" || ids[i].type === "eissn") {
                        issns.push(edges.escapeHtml(ids[i].id))
                    }
                }
                return issns.join(", ")
            }
            return false
        },

        deleteArticle : function (val, resultobj, renderer) {
            if (!resultobj.suggestion && resultobj.bibjson.journal) {
                // if it's not a suggestion or a journal .. (it's an article!)
                // we really need to expose _type ...
                var result = '<a class="delete_article_link" href="';
                result += "/admin/article/";
                result += resultobj['id'];
                result += '" target="_blank"';
                result += '>Delete this article</a>';
                return result;
            }
            return false;
        },

        editJournal : function (val, resultobj, renderer) {
            if (!resultobj.suggestion && !resultobj.bibjson.journal) {
                // if it's not a suggestion or an article .. (it's a
                // journal!)
                // we really need to expose _type ...
                var result = '<a class="edit_journal_link" href="';
                result += doaj.adminJournalArticleSearchConfig.journalEditUrl;
                result += resultobj['id'];
                result += '" target="_blank"';
                result += '>Edit this journal</a>';
                return result;
            }
            return false;
        },

        init : function(params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#admin_journals_and_articles";
            var search_url = current_scheme + "//" + current_domain + doaj.adminJournalArticleSearchConfig.searchPath;

            var journalSelected = doaj.adminJournalArticleSearch.journalSelected(selector);
            var anySelected = doaj.adminJournalArticleSearch.anySelected(selector);
            var typeSelected = doaj.adminJournalArticleSearch.typeSelected(selector);

            var mfb = doaj.adminJournalArticleBulkEdit.newMultiFormBox({
                selector: "#admin-bulk-box",
                widths: {
                    edit_metadata: "600px"
                },
                bindings : {
                    editor_group : function(context) {
                        autocomplete($('#editor_group', context), 'name', 'editor_group', 1, false);
                    },
                    edit_metadata : function(context) {
                        autocomplete($('#publisher', context), 'bibjson.publisher');
                        autocomplete($('#platform', context), 'bibjson.provider');
                        $('#country', context).select2();
                        autocomplete($('#owner', context), 'id', 'account');
                    }
                },
                validators : {
                    withdraw : journalSelected,
                    reinstate: journalSelected,
                    delete: anySelected,
                    note : function(context) {
                        var valid = journalSelected();
                        if (!valid.valid) {
                            return valid;
                        }
                        var val = context.find("#note").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    },
                    editor_group : function(context) {
                        var valid = journalSelected();
                        if (!valid.valid) {
                            return valid;
                        }
                        var val = context.find("#editor_group").val();
                        if (val === "") {
                            return {valid: false};
                        }
                        return {valid: true};
                    },
                    edit_metadata : function(context) {
                        // first check that the journal has been selected
                        var valid = journalSelected();
                        if (!valid.valid) {
                            return valid;
                        }

                        // now check that at least one field has been completed
                        var found = false;
                        var fields = ["#publisher", "#platform", "#country", "#owner", "#contact_name", "#contact_email", "#doaj_seal"];
                        for (var i = 0; i < fields.length; i++) {
                            var val = context.find(fields[i]).val();
                            if (val !== "") {
                                found = true;
                            }
                        }
                        if (!found) {
                            return {valid: false};
                        }

                        // now check for valid field contents
                        // quick and dirty email check - this will be done properly server-side
                        var email = context.find("#contact_email").val();
                        if (email !== "") {
                            var match = email.match(/.+\@.+\..+/);
                            if (match === null) {
                                return {valid: false, error_id: "invalid_email"};
                            }
                        }

                        return {valid: true};
                    }
                },
                submit : {
                    delete : {
                        sure : 'Are you sure?  This operation cannot be undone!'
                    },
                    note : {
                        data: function(context) {
                            return {
                                note: $('#note', context).val()
                            };
                        }
                    },
                    editor_group : {
                        data : function(context) {
                            return {
                                editor_group: $('#editor_group', context).val()
                            };
                        }
                    },
                    edit_metadata : {
                        data : function(context) {
                            var seal = $('#doaj_seal', context).val();
                            if (seal === "True") {
                                seal = true;
                            } else if (seal === "False") {
                                seal = false;
                            }
                            var data = {
                                metadata : {
                                    publisher: $('#publisher', context).select2("val"),
                                    platform: $('#platform', context).select2("val"),
                                    country: $('#country', context).select2("val"),
                                    owner: $('#owner', context).select2("val"),
                                    contact_name: $('#contact_name', context).val(),
                                    contact_email: $('#contact_email', context).val(),
                                    doaj_seal: seal
                                }
                            };
                            return data;
                        }
                    }
                },
                urls : {
                    withdraw: "/admin/journals/bulk/withdraw",
                    reinstate: "/admin/journals/bulk/reinstate",
                    delete : function() {
                        var type = typeSelected();
                        if (type === "journal") {
                            return "/admin/journals/bulk/delete"
                        } else if (type === "article") {
                            return "/admin/articles/bulk/delete"
                        }
                        return null;
                    },
                    note : "/admin/journals/bulk/add_note",
                    editor_group : "/admin/journals/bulk/assign_editor_group",
                    edit_metadata : "/admin/journals/bulk/edit_metadata"
                }
            });
            doaj.adminJournalArticleBulkEdit.active = mfb;

            var countFormat = edges.numFormat({
                thousandsSeparator: ","
            });

            var components = [
                // facets
                edges.newRefiningANDTermSelector({
                    id: "journals_articles",
                    category: "facet",
                    field: "_type",
                    display: "Journals vs Articles",
                    valueMap : {
                        "journal" : "Journals",
                        "article" : "Articles"
                    },
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "in_doaj",
                    category: "facet",
                    field: "admin.in_doaj",
                    display: "In DOAJ?",
                    valueMap : {
                        "T" : "True",
                        "F" : "False"
                    },
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "journal_language",
                    category: "facet",
                    field: "index.language.exact",
                    display: "Journal Language",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "publisher",
                    category: "facet",
                    field: "index.publisher.exact",
                    display: "Publisher",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "platform_host_aggregator",
                    category: "facet",
                    field: "bibjson.provider.exact",
                    display: "Platform, Host, Aggregator",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "classification",
                    category: "facet",
                    field: "index.classification.exact",
                    display: "Classification",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "subject",
                    category: "facet",
                    field: "index.subject.exact",
                    display: "Subject",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "country_publisher",
                    category: "facet",
                    field: "index.country.exact",
                    display: "Country of publisher",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "author_pays",
                    category: "facet",
                    field: "bibjson.author_pays.exact",
                    display: "Publication charges?",
                    valueMap : {
                        "N" : "No",
                        "Y" : "Yes",
                        "NY" : "No Information",
                        "CON" : "Conditional"
                    },
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "journal_license",
                    category: "facet",
                    field: "index.license.exact",
                    display: "Journal License",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "publication_year",
                    category: "facet",
                    field: "bibjson.year.exact",
                    display: "Year of publication (Articles)",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),
                edges.newRefiningANDTermSelector({
                    id: "journal_title",
                    category: "facet",
                    field: "bibjson.journal.title.exact",
                    display: "Journal title (Articles)",
                    renderer: edges.bs3.newRefiningANDTermSelectorRenderer({
                        controls: true,
                        open: false,
                        togglable: true,
                        countFormat: countFormat
                    })
                }),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    sortOptions: [
                        {'display':'Date added to DOAJ','field':'created_date'},
                        {'display':'Last updated','field':'last_updated'},
                        {'display':'Title','field':'index.unpunctitle.exact'},
                        {'display':'Article: Publication date','field':['bibjson.year.exact', 'bibjson.month.exact']}
                    ],
                    fieldOptions: [
                        {'display':'Title','field':'index.title'},
                        {'display':'Keywords','field':'bibjson.keywords'},
                        {'display':'Subject','field':'index.classification'},
                        {'display':'Classification','field':'index.classification'},
                        {'display':'ISSN', 'field':'index.issn.exact'},
                        {'display':'DOI', 'field' : 'bibjson.identifier.id'},
                        {'display':'Country of publisher','field':'index.country'},
                        {'display':'Journal Language','field':'index.language'},
                        {'display':'Publisher','field':'index.publisher'},

                        {'display':'Article: Abstract','field':'bibjson.abstract'},
                        {'display':'Article: Author','field':'bibjson.author.name'},
                        {'display':'Article: Year','field':'bibjson.year'},
                        {'display':'Article: Journal Title','field':'bibjson.journal.title'},

                        {'display':'Journal: Alternative Title','field':'bibjson.alternative_title'},
                        {'display':'Journal: Platform, Host, Aggregator','field':'bibjson.provider'}
                    ],
                    defaultOperator: "AND",
                    renderer: edges.bs3.newFullSearchControllerRenderer({
                        freetextSubmitDelay: 1000,
                        searchButton: true,
                        searchPlaceholder: "Search All Journals and Articles"
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                edges.newPager({
                    id: "top-pager",
                    category: "top-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
                    })
                }),
                edges.newPager({
                    id: "bottom-pager",
                    category: "bottom-pager",
                    renderer: edges.bs3.newPagerRenderer({
                        sizeOptions: [10, 25, 50, 100],
                        numberFormat: countFormat,
                        scrollSelector: "html, body"
                    })
                }),

                // results display
                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: edges.bs3.newResultsFieldsByRowRenderer({
                        rowDisplay : [
                            [
                                {
                                    "pre" : "<strong>ID</strong>: <em>",
                                    "field" : "id",
                                    "post": "</em>"
                                }
                            ],
                            // Journals
                            [
                                {
                                    valueFunction: doaj.adminJournalArticleSearch.titleField
                                }
                            ],
                            [
                                {
                                    "pre": '<span class="alt_title">Alternative title: ',
                                    "field": "bibjson.alternative_title",
                                    "post": "</span>"
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>In DOAJ?</strong>: ",
                                    "valueFunction" : doaj.adminJournalArticleSearch.inDoaj
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Classification</strong>: ",
                                    "field": "index.classification"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Publisher</strong>: ",
                                    "field": "bibjson.publisher"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Platform, Host, Aggregator</strong>: ",
                                    "field": "bibjson.provider"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Publication charges?</strong>: ",
                                    "valueFunction": doaj.adminJournalArticleSearch.authorPays
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Started publishing Open Access content in</strong>: ",
                                    "field": "bibjson.oa_start.year"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Stopped publishing Open Access content in</strong>: ",
                                    "field": "bibjson.oa_end.year"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal Language</strong>: ",
                                    "field": "bibjson.language"
                                }
                            ],
                            // Articles
                            [
                                {
                                    "pre": "<strong>Authors</strong>: ",
                                    "field": "bibjson.author.name"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Publisher</strong>: ",
                                    "field": "bibjson.journal.publisher"
                                }
                            ],
                            [
                                {
                                    "pre":'<strong>Date of publication</strong>: ',
                                    "field": "bibjson.year"
                                },
                                {
                                    "pre":' <span class="date-month">',
                                    "field": "bibjson.month",
                                    "post": "</span>"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Published in</strong>: ",
                                    "field": "bibjson.journal.title",
                                    "notrailingspace": true
                                },
                                {
                                    "pre": ", Vol ",
                                    "field": "bibjson.journal.volume",
                                    "notrailingspace": true
                                },
                                {
                                    "pre": ", Iss ",
                                    "field": "bibjson.journal.number",
                                    "notrailingspace": true
                                },
                                {
                                    "pre": ", Pp ",
                                    "field": "bibjson.start_page",
                                    "notrailingspace": true
                                },
                                {
                                    "pre": "-",
                                    "field": "bibjson.end_page"
                                },
                                {
                                    "pre" : "(",
                                    "field": "bibjson.year",
                                    "post" : ")"
                                }
                            ],
                            [
                                {
                                    "pre" : "<strong>ISSN(s)</strong>: ",
                                    "valueFunction" : doaj.adminJournalArticleSearch.issns
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Keywords</strong>: ",
                                    "field": "bibjson.keywords"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Discontinued Date</strong>: ",
                                    "field": "bibjson.discontinued_date"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Date added to DOAJ</strong>: ",
                                    "valueFunction": doaj.adminJournalArticleSearch.createdDateWithTime
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Last updated</strong>: ",
                                    "valueFunction": doaj.adminJournalArticleSearch.lastUpdated
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>DOI</strong>: ",
                                    "valueFunction": doaj.adminJournalArticleSearch.doiLink
                                }
                            ],
                            [
                                {
                                    "valueFunction" : doaj.adminJournalArticleSearch.links
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal Language(s)</strong>: ",
                                    "field": "bibjson.journal.language"
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Journal License</strong>: ",
                                    "valueFunction": doaj.adminJournalArticleSearch.journalLicense
                                }
                            ],
                            [
                                {
                                    "pre": "<strong>Country of publisher</strong>: ",
                                    "valueFunction": doaj.adminJournalArticleSearch.countryName
                                }
                            ],
                            [
                                {
                                    "pre": '<strong>Abstract</strong>: ',
                                    "valueFunction": doaj.adminJournalArticleSearch.abstract
                                }
                            ],
                            [
                                {
                                    "valueFunction": doaj.adminJournalArticleSearch.editJournal
                                },
                                {
                                    "valueFunction": doaj.adminJournalArticleSearch.deleteArticle
                                }
                            ]
                        ]
                    })
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {
                        "_type": "Showing",
                        "admin.in_doaj" : "In DOAJ?",
                        "index.language.exact" : "Journal Language",
                        "index.publisher.exact" : "Publisher",
                        "bibjson.provider.exact" : "Platform, Host, Aggregator",
                        "index.classification.exact" : "Classification",
                        "index.subject.exact" : "Subject",
                        "index.country.exact" : "Country of publisher",
                        "bibjson.author_pays.exact" : "Publication charges?",
                        "index.license.exact" : "Journal License",
                        "bibjson.year.exact" : "Year of publication",
                        "bibjson.journal.title.exact" : "Journal title"
                    },
                    valueMaps : {
                        "_type" : {
                            "journal" : "Journals",
                            "article" : "Articles"
                        },
                        "admin.in_doaj" : {
                            "T" : "True",
                            "F" : "False"
                        },
                        "bibjson.author_pays.exact" : {
                            "N" : "No",
                            "Y" : "Yes",
                            "NY" : "No Information",
                            "CON" : "Conditional"
                        }
                    }
                }),

                // the standard searching notification
                edges.newSearchingNotification({
                    id: "searching-notification",
                    category: "searching-notification"
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                manageUrl: true,
                components: components
            });
            doaj.adminJournalArticleSearch.activeEdges[selector] = e;

            $(selector).on("edges:pre-render", function() {
                doaj.adminJournalArticleBulkEdit.active.validate();
            });

            // now bind the abstract expander
            $(selector).on("edges:post-render", function() {
                $(".abstract_action").off("click").on("click", function(event) {
                    event.preventDefault();
                    var el = $(this);
                    var at = $(".abstract_text").filter('[rel="' + el.attr("rel") + '"]');
                    at.slideToggle(300);
                });

                // now add the handlers for the article delete
                $(".delete_article_link").off("click").on("click", function(event) {
                    event.preventDefault();

                    function success_callback(data) {
                        alert("The article was successfully deleted");
                        doaj.adminJournalArticleSearch.activeEdges[selector].cycle();
                    }

                    function error_callback() {
                        alert("There was an error deleting the article")
                    }

                    var c = confirm("Are you really really sure?  You can't undo this operation!");
                    if (c) {
                        var href = $(this).attr("href");
                        var obj = {"delete" : "true"};
                        $.ajax({
                            type: "POST",
                            url: href,
                            data: obj,
                            success : success_callback,
                            error: error_callback
                        })
                    }
                });
            });
        }
    }
});


jQuery(document).ready(function($) {
    doaj.adminJournalArticleSearch.init();
});
