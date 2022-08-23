// ~~Dashboard:Feature~~
doaj.dashboard = {
    statusOrder : [
        "pending",
        "in progress",
        "completed",
        "update_request",
        "revisions_required",
        "on hold",
        "ready",
        "rejected",
        "accepted"
    ]
};

doaj.dashboard.init = function() {
    $(".js-group-tab").on("click", doaj.dashboard.groupTabClick);

    // trigger a click on the first one, so there is something for the user to look at
    let first = $(".js-managed-groups-tabs").find("li:first-child a");
    first.trigger("click");
}

doaj.dashboard.groupTabClick = function(event) {
    let groupId = $(event.target).attr("data-group-id");
    doaj.dashboard.loadGroupTab(groupId);
}

// ~~->GroupStats:Endpoint~~
doaj.dashboard.loadGroupTab = function(groupId) {
    $.ajax({
        type: "GET",
        contentType: "application/json",
        dataType: "jsonp",
        url: "/service/groupstatus/" + groupId,
        success: doaj.dashboard.groupLoaded,
        error: doaj.dashboard.groupLoadError
    });
}

doaj.dashboard.groupLoaded = function(data) {
    let container = $("#group-tab");
    container.html(doaj.dashboard.renderGroupInfo(data));
}

doaj.dashboard.groupLoadError = function(data) {
    alert("Unable to determine group status at this time");
}

doaj.dashboard.renderGroupInfo = function(data) {
    // ~~-> EditorGroup:Model~~

    // first remove the editor from the associates list if they are there
    let edInAssEd = data.editor_group.associates.indexOf(data.editor_group.editor)
    if (edInAssEd > -1) {
        data.editor_group.associates.splice(edInAssEd, 1);
    }

    let allEditors = [data.editor_group.editor].concat(data.editor_group.associates);

    let editorListFrag = "";
    for (let i = 0; i < allEditors.length; i++) {
        let ed = allEditors[i];
        // ~~-> ApplicationSearch:Page~~
        let appQuerySource = doaj.searchQuerySource({
            "term" : [
                {"admin.editor.exact" : ed},
                {"admin.editor_group.exact" : data.editor_group.name},
                {"index.application_type.exact" : "new application"}    // this is required so we only see open applications, not finished ones
            ],
            "sort": [{"admin.date_applied": {"order": "asc"}}]
        })
        // // ~~-> UpdateRequestsSearch:Page ~~
        // let urQuerySource = doaj.searchQuerySource({"term" : [
        //     {"admin.editor.exact" : ed},
        //     {"admin.editor_group.exact" : data.editor_group.name},
        //     {"index.application_type.exact" : "update request"}    // this is required so we only see open update requests, not finished ones
        // ]})
        let appCount = 0;
        let urCount = 0;
        if (data.by_editor[ed]) {
            appCount = data.by_editor[ed].applications || 0;
            urCount = data.by_editor[ed].update_requests || 0;
        }

        let isEd = "";
        if (i === 0) {  // first one in the list is always the editor
            isEd = " (Ed.)"
        }
        editorListFrag += `<li>
            <a href="mailto:${data.editors[ed].email}" target="_blank" class="label tag">${ed}${isEd}</a>
            <a href="/admin/applications?source=${appQuerySource}" class="tag tag--tertiary" style="margin-right: 1.5rem;">${appCount} <span class="sr-only">applications</span></a>
        </li>`;
    }

    // ~~-> ApplicationSearch:Page~~
    let appUnassignedSource = doaj.searchQuerySource({
        "term" : [
            {"admin.editor_group.exact" : data.editor_group.name},
            {"index.has_editor.exact": "No"},
            {"index.application_type.exact" : "new application"}    // this is required so we only see open applications, not finished ones
        ],
        "sort": [{"admin.date_applied": {"order": "asc"}}]
    });
    // ~~-> UpdateRequestsSearch:Page ~~
    // let urUnassignedSource = doaj.searchQuerySource({"term" : [
    //         {"admin.editor_group.exact" : data.editor_group.name},
    //         {"index.has_editor.exact": "No"},
    //         {"index.application_type.exact" : "update request"}    // this is required so we only see open update requests, not finished ones
    // ]})
    editorListFrag += `<li>
        <span class="label tag tag--featured">Unassigned</span>
        <a href="/admin/applications?source=${appUnassignedSource}" class="tag tag--tertiary">${data.unassigned.applications} <span class="sr-only">applications</span></a>
    </li>`;

    let appStatusProgressBar = "";

    for (let j = 0; j < doaj.dashboard.statusOrder.length; j++) {
        let status = doaj.dashboard.statusOrder[j];
        if (data.by_status.hasOwnProperty(status)) {
            if (data.by_status[status].applications > 0) {
                // ~~-> ApplicationSearch:Page~~
                let appStatusSource = doaj.searchQuerySource({
                    "term": [
                        {"admin.editor_group.exact": data.editor_group.name},
                        {"admin.application_status.exact": status},
                        {"index.application_type.exact": "new application"}    // this is required so we only see open applications, not finished ones
                    ],
                    "sort": [{"admin.date_applied": {"order": "asc"}}]
                })
                appStatusProgressBar += `<li class="progress-bar__bar progress-bar__bar--${status.replace(' ', '-')}" style="width: ${(data.by_status[status].applications/data.total.applications)*100}%;">
                    <a href="/admin/applications?source=${appStatusSource}" class="progress-bar__link" title="See ${data.by_status[status].applications} applications that’re ${status}.">
                        ${status} (${data.by_status[status].applications})
                    </a></li>`;
            }
        }
    }

    // ~~-> ApplicationSearch:Page~~
    let appGroupSource = doaj.searchQuerySource({
        "term" : [
            {"admin.editor_group.exact" : data.editor_group.name},
            {"index.application_type.exact" : "new application"}    // this is required so we only see open applications, not finished ones
        ],
        "sort": [{"admin.date_applied": {"order": "asc"}}]
    });
    // ~~-> UpdateRequestsSearch:Page ~~
    // let urGroupSource = doaj.searchQuerySource({ "term" : [
    //     {"admin.editor_group.exact" : data.editor_group.name},
    //     {"index.application_type.exact" : "update request"}    // this is required so we only see open applications, not finished ones
    // ]})
    let frag = `<div class="tabs__content card">
        <h3>
          ${data.editor_group.name}’s ongoing applications
          <a href="/admin/applications?source=${appGroupSource}" class="tag tag--secondary">${data.total.applications}<span class="sr-only"> applications</span></a>
        </h3>

        <section>
          <h4 class="label label--secondary">By editor</h4>
          <ul class="inlined-list type-06">
              ${editorListFrag}
          </ul>
        </section>

        <section>
          <h4 class="label label--secondary">Applications by status</h4>
          <h3 class="sr-only">Status progress bar colour legend</h3>
          <ul class="inlined-list">
            <li><span class="progress-bar__bar--pending label label--secondary" style="padding: .5em;">Pending</span></li>
            <li><span class="progress-bar__bar--in-progress label label--secondary" style="padding: .5em;">In progress</span></li>
            <li><span class="progress-bar__bar--completed label label--secondary" style="padding: .5em;">Completed</span></li>
            <li><span class="progress-bar__bar--on-hold label label--secondary" style="padding: .5em;">On hold</span></li>
            <li><span class="progress-bar__bar--ready label" style="padding: .5em; color: #FFF;">Ready</span></li>
          </ul>
          <ul class="inlined-list progress-bar">
            ${appStatusProgressBar}
          </ul>
        </section>
      </div>`;
    return frag;
}
