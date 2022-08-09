// ~~Notifications:Edge->Edges:Technology~~
// ~~-> Notifications:Model ~~
// ~~-> Elasticsearch:Technology ~~
// ~~-> Notifications:Feature ~~
$.extend(true, doaj, {

    notificationsSearch: {
        activeEdges: {},

        seen_url: "/dashboard/notifications/{notification_id}/seen",

        icons: {
            finished: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-box-arrow-in-right" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M6 3.5a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-2a.5.5 0 0 0-1 0v2A1.5 1.5 0 0 0 6.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-9A1.5 1.5 0 0 0 14.5 2h-8A1.5 1.5 0 0 0 5 3.5v2a.5.5 0 0 0 1 0v-2z"/>
                  <path fill-rule="evenodd" d="M11.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L10.293 7.5H1.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3z"/>
                </svg>`,
            status_change: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-menu-button-wide-fill" viewBox="0 0 16 16">
                  <path d="M1.5 0A1.5 1.5 0 0 0 0 1.5v2A1.5 1.5 0 0 0 1.5 5h13A1.5 1.5 0 0 0 16 3.5v-2A1.5 1.5 0 0 0 14.5 0h-13zm1 2h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1 0-1zm9.927.427A.25.25 0 0 1 12.604 2h.792a.25.25 0 0 1 .177.427l-.396.396a.25.25 0 0 1-.354 0l-.396-.396zM0 8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V8zm1 3v2a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2H1zm14-1V8a1 1 0 0 0-1-1H2a1 1 0 0 0-1 1v2h14zM2 8.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0 4a.5.5 0 0 1 .5-.5h6a.5.5 0 0 1 0 1h-6a.5.5 0 0 1-.5-.5z"/>
                </svg>`,
            assign: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-person-check-fill" viewBox="0 0 16 16">
                  <path fill-rule="evenodd" d="M15.854 5.146a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708 0l-1.5-1.5a.5.5 0 0 1 .708-.708L12.5 7.793l2.646-2.647a.5.5 0 0 1 .708 0z"/>
                  <path d="M1 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H1zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                </svg>`,
            unknown: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-alarm" viewBox="0 0 16 16">
                  <path d="M8.5 5.5a.5.5 0 0 0-1 0v3.362l-1.429 2.38a.5.5 0 1 0 .858.515l1.5-2.5A.5.5 0 0 0 8.5 9V5.5z"/>
                  <path d="M6.5 0a.5.5 0 0 0 0 1H7v1.07a7.001 7.001 0 0 0-3.273 12.474l-.602.602a.5.5 0 0 0 .707.708l.746-.746A6.97 6.97 0 0 0 8 16a6.97 6.97 0 0 0 3.422-.892l.746.746a.5.5 0 0 0 .707-.708l-.601-.602A7.001 7.001 0 0 0 9 2.07V1h.5a.5.5 0 0 0 0-1h-3zm1.038 3.018a6.093 6.093 0 0 1 .924 0 6 6 0 1 1-.924 0zM0 3.5c0 .753.333 1.429.86 1.887A8.035 8.035 0 0 1 4.387 1.86 2.5 2.5 0 0 0 0 3.5zM13.5 1c-.753 0-1.429.333-1.887.86a8.035 8.035 0 0 1 3.527 3.527A2.5 2.5 0 0 0 13.5 1z"/>
                </svg>`,
            seen: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-circle" viewBox="0 0 16 16">
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                </svg>`,
            unseen: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-circle-fill" viewBox="0 0 16 16">
                  <circle cx="8" cy="8" r="8"/>
                </svg>`
        },

        classifications: {
            finished: "Task has completed",
            status_change: "Application status change",
            assign: "Assigned to user"
        },

        init: function (params) {
            if (!params) { params = {} }

            var current_domain = document.location.host;
            var current_scheme = window.location.protocol;

            var selector = params.selector || "#notifications";
            var search_url = current_scheme + "//" + current_domain + doaj.notificationsSearchConfig.searchPath;

            var components = [
                doaj.components.searchingNotification(),

                // configure the search controller
                edges.newFullSearchController({
                    id: "search-controller",
                    category: "controller",
                    defaultOperator: "AND",
                    renderer: doaj.renderers.newFullSearchControllerRenderer({
                        freetextSubmitDelay: -1,
                        searchButton: true,
                        searchPlaceholder: "Search All Notifications",
                        clearButton: false
                    })
                }),

                // the pager, with the explicitly set page size options (see the openingQuery for the initial size)
                doaj.components.pager("top-pager", "top-pager"),
                doaj.components.pager("bottom-pager", "bottom-pager"),

                edges.newResultsDisplay({
                    id: "results",
                    category: "results",
                    renderer: doaj.notificationsSearch.newNotificationResultRenderer()
                }),

                // selected filters display, with all the fields given their display names
                edges.newSelectedFilters({
                    id: "selected-filters",
                    category: "selected-filters",
                    fieldDisplays: {}
                })
            ];

            var e = edges.newEdge({
                selector: selector,
                template: edges.bs3.newFacetview(),
                search_url: search_url,
                manageUrl: false,
                openingQuery : es.newQuery({
                    sort: {"field" : "created_date", "order" : "desc"},
                    size: 25
                }),
                components: components,
                callbacks : {
                    "edges:query-fail" : function() {
                        alert("There was an unexpected error.  Please reload the page and try again.  If the issue persists please contact an administrator.");
                    },
                    "edges:post-render": function() {
                        $(".notification_action_button").on("click", doaj.notifications.notificationClicked);
                    }
                }
            });
            doaj.notificationsSearch.activeEdges[selector] = e;
        },

        newNotificationResultRenderer : function(params) {
            return edges.instantiate(doaj.notificationsSearch.NotificationResultRenderer, params, edges.newRenderer);
        },
        NotificationResultRenderer : function(params) {
            this.namespace = "doaj-notifications-search";

            this.currentQueryString  = "";

            this.markdownConverter = new showdown.Converter({
                literalMidWordUnderscores: true
            });

            this.markAsSeenClass = false;
            this.seenStatusSpan = false;

            this.draw = function () {
                if (this.component.edge.currentQuery){
                    let qs = this.component.edge.currentQuery.getQueryString();
                    if (qs) {
                        this.currentQueryString = qs.queryString || "";
                    }
                }
                var frag = "<li class='alert'><p>You searched for ‘<i>";
                frag += edges.escapeHtml(this.currentQueryString);
                frag += "</i>’ and we found no results.</p>";
                frag += "<p>Please try the following:</p><ul>\
                    <li>Check the spelling and make sure that there are no missing characters.</li>\
                    <li>Use fewer words in your search to make the search less specific.</li>\
                    <li>Remove some of the filters you have set.</li>\
                    <li>Do your search again in English as much of the index uses English terms.</li>\
                    </ul></li>\
                ";

                if (this.component.results === false) {
                    frag = "";
                }

                this.markAsSeenClass = edges.css_classes(this.namespace, "seen", this);
                this.seenStatusSpan = edges.css_classes(this.namespace, "seen_status", this);

                var results = this.component.results;
                if (results && results.length > 0) {
                    // now call the result renderer on each result to build the records
                    frag = "";
                    for (var i = 0; i < results.length; i++) {
                        frag += this._renderResult(results[i]);
                    }
                }

                this.component.context.html(frag);
                feather.replace();

                let markAsSeenSelector = edges.css_class_selector(this.namespace, "seen", this);
                edges.on(markAsSeenSelector, "click", this, "markAsSeen")
            };

            this._renderResult = function(notification) {
                let seen_icon = this._seenIcon(notification.seen_date);

                let typeIcon = doaj.notificationsSearch.icons[notification.classification];
                if (!typeIcon) {
                    typeIcon = doaj.notificationsSearch.icons.unknown;
                }

                let typeTitle = doaj.notificationsSearch.classifications[notification.classification];
                if (!typeTitle) {
                    typeTitle = "Notification";
                }

                let actionFrag = `No action required`
                if (notification.action) {
                    actionFrag = `<a class="notification_action_button" href="${notification.action}">See action</a>`;
                } else {
                    if (!notification.seen_date) {
                        actionFrag += `<br><a href="#" class="${this.markAsSeenClass}" data-notification-id="${notification.id}">Mark as seen</a>`;
                    }
                }

                var body = this.markdownConverter.makeHtml(notification.long);

                var frag = `<div class="card search-results__record" data-notification-id="${notification.id}">
                    <article class="row">
                      <div class="col-sm-1">
                        <span class="${this.seenStatusSpan}">${seen_icon}</span>&nbsp;<span title="${typeTitle}">${typeIcon}</span>
                        </div>
                      <div class="col-sm-9 search-results__main">
                        <header>
                          <h3 class="search-results__heading">${notification.short}</h3>
                        </header>
                        <div class="search-results__body">
                          <ul class="inlined-list">
                            <li>${body}</li>
                          </ul>
                        </div>
                      </div>
                        <aside class="col-sm-2 search-results__aside">
                            <ul class="inlined-list">
                            <li>${doaj.humanDate(notification.created_date)}</li>
                          </ul>
                          <ul class="inlined-list">
                            <li>${actionFrag}</li>
                          </ul>
                        </div>
                    </article>
                </div>`;

                return frag;
            };

            this._seenIcon = function(seen_date) {
                let seenIcon = seen_date ? doaj.notificationsSearch.icons.seen : doaj.notificationsSearch.icons.unseen;
                let seenTitle = seen_date ? `Notification seen on ${doaj.humanDate(seen_date)}` : "New notification"
                let frag = `<span title="${seenTitle}">${seenIcon}</span>`;
                return frag;
            }

            this.markAsSeen = function(element) {
                let notificationId = $(element).attr("data-notification-id");
                $.ajax({
                    method: "post",
                    url: doaj.notificationsSearch.seen_url.replace("{notification_id}", notificationId),
                    contentType: "application/json",
                    dataType: "jsonp"
                });
                let frag = this._seenIcon((new Date()).toString())

                let row = $(`div[data-notification-id=${notificationId}]`);

                let seenSelector = edges.css_class_selector(this.namespace, "seen_status", this);
                let icon = row.find(seenSelector);
                icon.html(frag);

                let markSelector = edges.css_class_selector(this.namespace, "seen", this);
                row.find(markSelector).remove();
            };
        }
    }

});

jQuery(document).ready(function($) {
    doaj.notificationsSearch.init();
});
