$.extend(true, doaj, {

    multiFormBox: {

        active: false,

        newMultiFormBox: function (params) {
            params = params === undefined ? {} : params;
            return new doaj.multiFormBox.MultiFormBox(params);
        },
        MultiFormBox: function (params) {
            this.selector = params.selector;
            this.slideTime = params.slideTime !== undefined ? params.slideTime : 400;
            this.widths = params.widths !== undefined ? params.widths : {};
            this.bindings = params.bindings !== undefined ? params.bindings : {};
            this.validators = params.validators !== undefined ? params.validators : {};
            this.submitCfg = params.submit !== undefined ? params.submit : {};
            this.urls = params.urls !== undefined ? params.urls : {};
            this.edgeSelector = params.edgeSelector;

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

                var query = doaj.adminJournalArticleSearch.activeEdges[this.edgeSelector].currentQuery.objectify({
                    include_paging: false,
                    include_sort: false,
                    include_aggregations: false,
                    include_source_filters: false
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
    }
});