var doaj = {
    currentFVOptions: false,
    active : false,

    newMultiFormBox : function(params) {
        params = params === undefined ? {} : params;
        return new doaj.MultiFormBox(params);
    },
    MultiFormBox : function(params) {
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

        this.init = function() {
            this.context = $(this.selector);
            this.defaultWidth = this.context.outerWidth() + "px";
            this.currentWidth = this.defaultWidth;
            this.context.css("width", this.defaultWidth);

            var that = this;
            var containers = this.context.find(".multiformbox-container");
            containers.each(function(i) {
                var content = $(this).html();
                var id = $(this).attr("id");
                that.initialContent[id] = content;
                $(this).html("");
            });

            var selectBox = this.context.find(".multiformbox-selector");
            var selectHandler = doaj.eventClosure(this, "selectChanged");
            selectBox.unbind("change.multiformbox").bind("change.multiformbox", selectHandler);

            var submit = this.context.find(".multiformbox-submit");
            var submitHandler = doaj.eventClosure(this, "submit");
            submit.unbind("click.multiformbox").bind("click.multiformbox", submitHandler);

            this.validate();
        };

        this.reset = function() {
            this.transitionPart1({
                target: false
            });
            this._disableSubmit();
        };

        this.submit = function(element) {
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

            var successHandler = doaj.objClosure(this, "confirmSubmit");
            var errorHandler = doaj.objClosure(this, "submitError");

            this._doSubmit({
                cfg: cfg,
                dryRun: true,
                success: successHandler,
                error: errorHandler
            });
        };

        this.confirmSubmit = function(data) {
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

            var successHandler = doaj.objClosure(this, "submissionComplete");
            var errorHandler = doaj.objClosure(this, "submitError");

            this._doSubmit({
                cfg: cfg,
                dryRun: false,
                success: successHandler,
                error: errorHandler
            });
        };

        this.submissionComplete = function(data) {
            var msg = "Your bulk edit request has been submitted and queued for execution.<br>";
            msg += this._affectedMessage(data) + " have been queued for edit.<br>";
            msg += 'You can see your request <a href="' + this._bulkJobUrl(data) + '" target="_blank">here</a> in the background jobs interface (opens new tab).<br>';
            msg += "You will get an email when your request has been processed; this could take anything from a few minutes to a few hours.<br>";
            msg += '<a href="#" id="bulk-action-feedback-dismiss">dismiss</a>';

            $(".bulk-action-feedback").html(msg).show();
            $("#bulk-action-feedback-dismiss").unbind("click").bind("click", function(event) {
                event.preventDefault();
                $(".bulk-action-feedback").html("").hide();
            });

            this.reset();
        };

        this._bulkJobUrl = function(data) {
            var url = "/admin/background_jobs?source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22" + data.job_id + "%22%2C%22default_operator%22%3A%22AND%22%7D%7D%2C%22sort%22%3A%5B%7B%22created_date%22%3A%7B%22order%22%3A%22desc%22%7D%7D%5D%2C%22from%22%3A0%2C%22size%22%3A25%7D";
            return url;
        };

        this._doSubmit = function(params) {
            var cfg = params.cfg;
            var dryRun = params.dryRun;
            var success = params.success;
            var error = params.error;

            var query = elasticSearchQuery({
                options: doaj.currentFVOptions,
                include_facets: false,
                include_fields: false
            });

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
                data: serialiseQueryObject(data),
                contentType : 'application/json',
                success : success,
                error: error
            });
        };

        this._affectedMessage = function(data) {
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

        this.submitError = function(jqXHR, textStatus, errorThrown) {
            alert('There was an error with your request.');
            this._enableSubmit();
        };

        this.selectChanged = function(element) {
            var val = $(element).val();
            if (val === this.currentField) {
                return;
            }

            this.transitionPart1({
                target: val
            });
        };

        this.validate = function() {
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

        this._enableSubmit = function() {
            this.context.find(".multiformbox-submit").removeAttr('disabled').html("Submit");
        };

        this._disableSubmit = function() {
            this.context.find(".multiformbox-submit").attr('disabled', 'disabled').html("Submit");
        };

        this._submitting = function() {
            this.context.find(".multiformbox-submit").attr('disabled', 'disabled').html("<img src='/static/doaj/images/white-transparent-loader.gif'>&nbsp;Submitting...");
        };

        this._showError = function(error_id) {
            if (error_id === false && this.currentError !== false) {
                this.context.find(".multiformbox-error").hide();
            } else if (error_id !== false && this.currentError !== error_id) {
                this.context.find(".multiformbox-error").hide();
                this.context.find("#" + error_id).show();
            }
            this.currentError = error_id;
        };

        this.transitionPart1 = function(params) {
            // first part of the transition is to slide the form up to cover whatever is there right now
            if (this.currentField === false) {
                this.transitionPart2(params);
                return;
            }
            var currentContainerId = this.currentField + "-container";
            var current = this.context.find("#" + currentContainerId);
            if (current.length > 0) {
                params["current"] = current;
                var clos = doaj.objClosure(this, "transitionPart2", false, params);
                current.slideUp(this.slideTime, clos);
            } else {
                this.transitionPart2(params);
                return;
            }
        };

        this.transitionPart2 = function(params) {
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

            var clos = doaj.objClosure(this, "transitionPart3", false, params);
            var that = this;
            this.context.animate({width: width},
                {
                    duration: this.slideTime,
                    step: function() {
                        that.context.css("overflow", "");
                    },
                    complete: clos
                }
            );
        };

        this.transitionPart3 = function(params) {
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

            var validateHandler = doaj.eventClosure(this, "validate");
            var inputs = target.find(":input");
            inputs.unbind("keyup.multiformbox").bind("keyup.multiformbox", validateHandler);
            inputs.unbind("change.multiformbox").bind("change.multiformbox", validateHandler);

            target.slideDown(this.slideTime);
            this.validate();
        };

        this.init();
    },

    objClosure : function(obj, fn, args, context_params) {
        return function() {
            if (args) {
                var params = {};
                for (var i = 0; i < args.length; i++) {
                    if (arguments.length > i) {
                        params[args[i]] = arguments[i];
                    }
                }
                if (context_params) {
                    params = $.extend(params, context_params);
                }
                obj[fn](params);
            } else {
                var slice = Array.prototype.slice;
                var theArgs = slice.apply(arguments);
                if (context_params) {
                    theArgs.push(context_params);
                }
                obj[fn].apply(obj, theArgs);
            }
        }
    },

    eventClosure : function(obj, fn) {
        return function(event) {
            event.preventDefault();
            obj[fn](this);
        }
    }
};



jQuery(document).ready(function($) {

    function journalSelected() {
        var type = doaj.currentFVOptions.active_filters._type;
        if (type && type.length > 0) {
            type = type[0];
        }
        if (!type || type !== "journal") {
            return {
                valid: false,
                error_id: "journal_type_error"
            }
        }
        return {valid : true};
    }

    function anySelected() {
        var type = doaj.currentFVOptions.active_filters._type;
        if (!type || type.length === 0) {
            return {
                valid: false,
                error_id: "any_type_error"
            }
        }
        return {valid: true};
    }

    function typeSelected() {
        var type = doaj.currentFVOptions.active_filters._type;
        if (type && type.length > 0) {
            return type[0];
        }
        return null;
    }

    var mfb = doaj.newMultiFormBox({
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
    doaj.active = mfb;


    function adminJAPostSearch(options, context) {
        doaj.currentFVOptions = options;
        doaj.active.validate();
    }

    /////////////////////////////////////////////////////////////////

    $('.facetview.admin_journals_and_articles').facetview({
        search_url: es_scheme + '//' + es_domain + '/admin_query/journal,article/_search?',

        render_results_metadata: doajPager,
        render_active_terms_filter: doajRenderActiveTermsFilter,
        post_render_callback: doajJAPostRender,
        post_search_callback: adminJAPostSearch,

        sharesave_link: false,
        freetext_submit_delay: 1000,
        default_facet_hide_inactive: true,
        default_facet_operator: "AND",
        default_operator : "AND",

        facets: [
            {'field': '_type', 'display': 'Journals vs. Articles'},
            {'field': 'admin.in_doaj', 'display': 'In DOAJ?'},
            {'field': 'index.classification.exact', 'display': 'Subject'},
            {'field': 'index.language.exact', 'display': 'Journal Language'},
            {'field': 'index.publisher.exact', 'display': 'Publisher'},
            {'field': 'bibjson.provider.exact', 'display': 'Platform, Host, Aggregator'},
            {'field': 'index.classification.exact', 'display': 'Classification'},
            {'field': 'index.subject.exact', 'display': 'Subject'},
            {'field': 'index.language.exact', 'display': 'Journal Language'},
            {'field': 'index.country.exact', 'display': 'Country of publisher'},
            {'field': 'bibjson.author_pays.exact', 'display': 'Publication charges?'},
            {'field': 'index.license.exact', 'display': 'Journal License'},
            // Articles
            {'field': 'bibjson.author.exact', 'display': 'Author (Articles)'},
            {'field': 'bibjson.year.exact', 'display': 'Year of publication (Articles)'},
            {'field': 'bibjson.journal.title.exact', 'display': 'Journal title (Articles)'}
        ],

        search_sortby: [
            {'display':'Date added to DOAJ','field':'created_date'},
            {'display':'Last updated','field':'last_updated'},
            {'display':'Title','field':'index.unpunctitle.exact'},
            {'display':'Article: Publication date','field':['bibjson.year.exact', 'bibjson.month.exact']}
        ],

        searchbox_fieldselect: [
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

        page_size : 10,
        from : 0,

        results_render_callbacks: {
            'bibjson.author_pays': fv_author_pays,
            'created_date': fv_created_date_with_time,
            'last_updated': fv_last_updated,
            'bibjson.abstract': fv_abstract,
            'journal_license' : fv_journal_license,
            "title_field" : fv_title_field,
            "doi_link" : fv_doi_link,
            "links" : fv_links,
            "issns" : fv_issns,
            "edit_journal": fv_edit_journal,
            "delete_article" : fv_delete_article,
            "in_doaj": fv_in_doaj,
            "country_name": fv_country_name
        },
        result_display: [
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
                    "field" : "title_field"
                }
                /*
                 {
                 "pre": '<span class="title">',
                 "field": "bibjson.title",
                 "post": "</span>"
                 }
                 */
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
                    "field" : "in_doaj"
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
                    "field": "bibjson.author_pays"
                }
            ],
            /*
             [
             {
             "pre": "<strong>More information on publishing charges</strong>: ",
             "field": "bibjson.author_pays_url",
             }
             ],
             */
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
                    "field" : "issns"
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
                    "field": "created_date"
                }
            ],
            [
                {
                    "pre": "<strong>Last updated</strong>: ",
                    "field": "last_updated"
                }
            ],
            [
                {
                    "pre": "<strong>DOI</strong>: ",
                    "field": "doi_link"
                }
            ],
            [
                {
                    "field" : "links"
                }
                /*
                 {
                 "pre": "<strong>More information - ",
                 "field": "bibjson.link.type",
                 "post": "</strong>: ",
                 },
                 {
                 "field": "bibjson.link.url",
                 },
                 */
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
                    "field": "journal_license"
                }
            ],
            [
                {
                    "pre": "<strong>Country of publisher</strong>: ",
                    "field": "country_name"
                }
            ],
            [
                {
                    "pre": '<strong>Abstract</strong>: ',
                    "field": "bibjson.abstract"
                }
            ],
            [
                {
                    "field": "edit_journal"
                },
                {
                    "field" : "delete_article"
                }
            ]
        ]
    });
});
