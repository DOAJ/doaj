// ~~Dashboard:Feature~~
doaj.dashboard = {
    statusOrder: [
        "pending",
        "in progress",
        "completed",
        "update_request",
        "revisions_required",
        "on hold",
        "ready",
        "rejected",
        "accepted"
    ],
    visibleStatusFilters: [
        "pending",
        "in progress",
        "completed",
        "on hold",
        "ready",
    ]
};

doaj.dashboard.init = function (context) {
    doaj.dashboard.context = context;
    doaj.dashboard.motivationalBanners = motivational_banners;
    doaj.dashboard.context.historical_count = historical_count;
    $(".js-group-tab").on("click", doaj.dashboard.groupTabClick);

    // trigger a click on the first one, so there is something for the user to look at
    let first = $(".js-managed-groups-tabs").find("li:first-child a");
    if (first) {
        first.trigger("click");
    }
    this.generateMotivationalBanner();

}

doaj.dashboard.generateMotivationalBanner = function () {

    _addNumberToBanner = function (text) {
        var number = `<span class="tag tag--confirmation">` + doaj.dashboard.context.historical_count + `</span>`;
        var bannerTextWithNumber = text.replace(/{{ COUNT }}/g, number);
        return bannerTextWithNumber;
    }
    _addTextToBanner = function (text) {
        $("#banner_text_placeholder").html(text);
    }

    if (doaj.dashboard.context.historical_count == 0) {
        bannerText = doaj.dashboard.motivationalBanners["banners"]["zero_count"][0];
    } else {
        var available_texts = doaj.dashboard.motivationalBanners["banners"]["positive_count"]
        var randomIndex = Math.floor(Math.random() * available_texts.length);
        var randomBannerText = available_texts[randomIndex];
        bannerText = _addNumberToBanner(randomBannerText);
    }
    _addTextToBanner(bannerText);
}

doaj.dashboard.groupTabClick = function (event) {
    let groupId = $(event.target).attr("data-group-id");
    doaj.dashboard.loadGroupTab(groupId);
}

// ~~->GroupStats:Endpoint~~
doaj.dashboard.loadGroupTab = function (groupId) {
    $.ajax({
        type: "GET",
        contentType: "application/json",
        dataType: "jsonp",
        url: "/service/groupstatus/" + groupId,
        success: doaj.dashboard.groupLoaded,
        error: doaj.dashboard.groupLoadError
    });
}

doaj.dashboard.groupLoaded = function (data) {
    let container = $("#group-tab");
    container.html(doaj.dashboard.renderGroupInfo(data));
}

doaj.dashboard.groupLoadError = function (data) {
    alert("Unable to determine group status at this time");
}

doaj.dashboard.renderGroupInfo = function (data) {
    // Remove the editor from the associates list if they are there
    _removeEditorFromAssociates = function (data) {
        if (data.editor_group.associates && data.editor_group.associates.length > 0) {
            let edInAssEd = data.editor_group.associates.indexOf(data.editor_group.editor);
            if (edInAssEd > -1) {
                data.editor_group.associates.splice(edInAssEd, 1);
            }
        } else {
            data.editor_group.associates = [];  // to avoid having to keep checking it below
        }
    }

    // Generate the search query source
    _generateSearchQuerySource = function (term, sort) {
        return doaj.searchQuerySource({
            "term": term,
            "sort": sort
        });
    }

    _generateStatusLinks = function (data) {
        const statusLinks = {};

        // Generate URL for each status
        doaj.dashboard.statusOrder.forEach(status => {
            const queryParams = [
                {"admin.editor_group.exact": data.editor_group.name},
                {"admin.application_status.exact": status},
                {"index.application_type.exact": "new application"}    // only see open applications, not finished ones
            ];
            const sortOptions = [{"admin.date_applied": {"order": "asc"}}];
            const querySource = _generateSearchQuerySource(queryParams, sortOptions);
            const url = `${doaj.dashboard.context.applicationsSearchBase}?source=${querySource}`;

            statusLinks[status] = url;
        });

        return statusLinks;
    }

    const statusLinks = _generateStatusLinks(data)

    _generateColorLegend = function(data) {
        return `<div id="color-legend" class="color-legend">
        <ul class="inlined-list">
            ${doaj.dashboard.visibleStatusFilters.map(status => {
            // Use the statusLink for each status
            const link = statusLinks[status] || '#'; // Fallback to # if no link is found

            return `<li><a href="${link}" class="label status status--link status--${status.replace(' ', '-')}" title="See ${data.by_status[status]?.applications || 0} ${status} application(s)">
${status}</a></li>`;
        }).join('')}
        </ul>
    </div>`;
    }


    // Generate the editor list fragment
    _generateEditorListFragment = function (data, allEditors) {
        let editorListFrag = "";
        let unassignedFragment = _generateUnassignedApplicationsFragment(data);
        for (let i = 0; i < allEditors.length; i++) {
            let ed = allEditors[i];
            let appQuerySource = _generateSearchQuerySource([
                {"admin.editor.exact": ed},
                {"admin.editor_group.exact": data.editor_group.name},
                {"index.application_type.exact": "new application"}    // only see open applications, not finished ones
            ], [{"admin.date_applied": {"order": "asc"}}]);

            let appCount = data.by_editor[ed]?.applications || 0;
            let urCount = data.by_editor[ed]?.update_requests || 0;

            if (data.editors[ed]) {
                let isEd = i === 0 ? " (Editor)" : "";
                editorListFrag += `<li>`;
                if (data.editors[ed].email) {
                    editorListFrag += `<a href="mailto:${data.editors[ed].email}" target="_blank" class="label tag" title="Send an email to ${ed}">${ed}${isEd}</a>`;
                } else {
                    editorListFrag += `<span class="label tag">${ed}${isEd} (no email)</span>`;
                }
                editorListFrag += `<a href="${doaj.dashboard.context.applicationsSearchBase}?source=${appQuerySource}" class="tag tag--tertiary" title="See ${ed}’s applications" style="margin-right: 1.5rem;"><strong>${appCount}</strong> <span class="sr-only">applications</span></a></li>`;
            }
        }
        editorListFrag += `${unassignedFragment}`
        return editorListFrag;
    }

    // Generate the unassigned applications fragment
    _generateUnassignedApplicationsFragment = function (data) {
        let appUnassignedSource = _generateSearchQuerySource([
            {"admin.editor_group.exact": data.editor_group.name},
            {"index.has_editor.exact": "No"},
            {"index.application_type.exact": "new application"}    // only see open applications, not finished ones
        ], [{"admin.date_applied": {"order": "asc"}}]);

        return `<li>
            <span class="label tag tag--featured">Unassigned</span>
            <a href="${doaj.dashboard.context.applicationsSearchBase}?source=${appUnassignedSource}" class="tag tag--tertiary" title="See unassigned applications">${data.unassigned.applications} <span class="sr-only">applications</span></a>
        </li>`;
    }

    // Generate the status progress bar
    _generateStatusProgressBar = function (data) {


        let appStatusProgressBar = "";

        for (let status of doaj.dashboard.statusOrder) {
            if (data.by_status[status]?.applications > 0) {
                let url = statusLinks[status]; // Get the URL from the precomputed status links

                appStatusProgressBar += `<li class="status status--link status--${status.replace(' ', '-')} progress-bar__bar" style="width: ${(data.by_status[status].applications / data.total.applications) * 100}%;">
                <a href="${url}" class="progress-bar__link" title="See ${data.by_status[status].applications} ${status} application(s)">
                    <strong>${data.by_status[status].applications}</strong>
                </a></li>`;
            }
        }

        return appStatusProgressBar;
    }


    _generateStatisticsFragment = function (data) {
        let statisticsFrag = "";
        let historicalNumbers = data.historical_numbers;

        if (historicalNumbers) {
            statisticsFrag += `<section>
                <h3>Statistics for the current year (${historicalNumbers.year})</h3>`;

            if (current_user.role.includes("admin")) {
                // Ready applications by editor
                statisticsFrag += `<h4 class="label label--secondary">Editor's <span class="label status status--ready" style="padding: .5em; display: unset;">Ready</span> Applications: `;
                statisticsFrag += `<span class="label tag" style="margin-left: .5em;">${historicalNumbers.editor.id}</span> <span class="tag tag--tertiary">${historicalNumbers.editor.count}</span></h4>`;
            }

            // Completed applications by associated editor
            if (historicalNumbers.associate_editors.length) {
                statisticsFrag += `<h4 class="label label--secondary">Applications <span class="progress-bar__bar--completed label label--secondary" style="padding: .5em; display: unset;">Completed</span> by associated editors</h4>`;
                statisticsFrag += `<ul class="inlined-list">`;
                for (let associateEditor of historicalNumbers.associate_editors) {
                    statisticsFrag += `<li><span class="label tag">${associateEditor.name}</span> <span class="tag tag--tertiary">${associateEditor.count}</span></span>`;
                }

                statisticsFrag += `</ul>`
            }
            statisticsFrag += `</section>`;
        }

        return statisticsFrag;
    };


    // Generate the main fragment
    _renderMainFragment = function (data) {
        _removeEditorFromAssociates(data);

        let colorLegend = _generateColorLegend(data);
        let allEditors = [data.editor_group.editor].concat(data.editor_group.associates);
        let editorListFrag = _generateEditorListFragment(data, allEditors);
        let appStatusProgressBar = _generateStatusProgressBar(data);
        let statisticsFragment = _generateStatisticsFragment(data);

        let appGroupSource = _generateSearchQuerySource([
            {"admin.editor_group.exact": data.editor_group.name},
            {"index.application_type.exact": "new application"}    // only see open applications, not finished ones
        ], [{"admin.date_applied": {"order": "asc"}}]);


        // Combine all fragments
        let frag = `<div class="tabs__content card activity-section">
        <h3>
            ${data.editor_group.name}’s open applications
            <a href="${doaj.dashboard.context.applicationsSearchBase}?source=${appGroupSource}" 
            class="tag tag--secondary" 
            title="See all ${data.editor_group.name}’s open applications ">
                ${data.total.applications}
                <span class="sr-only"> applications</span>
            </a>
        </h3>
        
        <section>
            <h3 class="sr-only">Status progress bar colour legend</h3>
            ${colorLegend}
        </section>
        
        <section>
          <h4 class="label label--secondary">By editor</h4>
          <ul class="inlined-list">
              ${editorListFrag}
          </ul>
        </section>`
        if (data["total"]["applications"]) {
            frag += `<section>
                <h4 class="label label--secondary">Applications by status</h4>
                <ul class="inlined-list progress-bar">
                    ${appStatusProgressBar}
                </ul>
            </section>`
        }
        frag += `${statisticsFragment}</div>`;

        return frag;
    }

    return _renderMainFragment(data);
}

