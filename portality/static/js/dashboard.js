// ~~Dashboard:Feature~~
doaj.dashboard = {};

doaj.dashboard.init = function() {
    $(".js-group-tab").on("click", doaj.dashboard.groupTabClick)
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
    let allEditors = [data.editor_group.editor].concat(data.editor_group.associates);

    let editorListFrag = "";
    for (let i = 0; i < allEditors.length; i++) {
        let ed = allEditors[i];
        // ~~-> ApplicationSearch:Page~~
        let appQuerySource = doaj.searchQuerySource({"term" : [
            {"admin.editor.exact" : ed},
            {"admin.editor_group.exact" : data.editor_group.name},
            {"index.application_type.exact" : "new application"}    // this is required so we only see open applications, not finished ones
        ]})
        let urQuerySource = doaj.searchQuerySource({"term" : [
            {"admin.editor.exact" : ed},
            {"admin.editor_group.exact" : data.editor_group.name},
            {"index.application_type.exact" : "update request"}    // this is required so we only see open update requests, not finished ones
        ]})
        let appCount = 0;
        let urCount = 0;
        if (data.by_editor[ed]) {
            appCount = data.by_editor[ed].applications || 0;
            urCount = data.by_editor[ed].update_requests || 0;
        }
        editorListFrag += `<li>
            <a href="mailto:${data.editors[ed].email}" class="label tag">${ed}</a>
            <span class="tag tag--secondary">
                <a href="/admin/applications?source=${appQuerySource}">${appCount} <span class="sr-only">applications</span> APP</a> | 
                <a href="/admin/update_requests?source=${urQuerySource}">${urCount} <span class="sr-only">update requests</span> UR</a>
            </span>
        </li>`;
    }

    // ~~-> ApplicationSearch:Page~~
    let appUnassignedSource = doaj.searchQuerySource({"term" : [
            {"admin.editor_group.exact" : data.editor_group.name},
            {"index.has_editor.exact": "No"},
            {"index.application_type.exact" : "new application"}    // this is required so we only see open applications, not finished ones
    ]})
    let urUnassignedSource = doaj.searchQuerySource({"term" : [
            {"admin.editor_group.exact" : data.editor_group.name},
            {"index.has_editor.exact": "No"},
            {"index.application_type.exact" : "update request"}    // this is required so we only see open update requests, not finished ones
    ]})
    editorListFrag += `<li>
        <span class="label tag tag--featured">unassigned</span>
        <span class="tag tag--secondary">
            <a href="/admin/applications?source=${appUnassignedSource}">${data.unassigned.applications} <span class="sr-only">applications</span> APP</a> | 
            <a href="/admin/update_requests?source=${urUnassignedSource}">${data.unassigned.update_requests} <span class="sr-only">update requests</span> UR</a>
        </span>
    </li>`;

    let appStatusFrag = "";
    let urStatusFrag = "";
    let statuses = Object.keys(data.by_status);
    for (let i = 0; i < statuses.length; i++) {
        let status = statuses[i];
        // ~~-> ApplicationSearch:Page~~
        if (data.by_status[status].applications > 0) {
            let appStatusSource = doaj.searchQuerySource({
                "term": [
                    {"admin.editor_group.exact": data.editor_group.name},
                    {"admin.application_status.exact": status},
                    {"index.application_type.exact": "new application"}    // this is required so we only see open applications, not finished ones
                ]
            })
            appStatusFrag += `<li>
                <a href="/admin/applications?source=${appStatusSource}">
                    <span>${status} <span>${data.by_status[status].applications}</span></span>
                    <span></span>
                </a>
            </li>`;
        }

        // ~~-> UpdateRequestsSearch:Page~~
        if (data.by_status[status].update_requests > 0) {
            let urStatusSource = doaj.searchQuerySource({
                "term": [
                    {"admin.editor_group.exact": data.editor_group.name},
                    {"admin.application_status.exact": status},
                    {"index.application_type.exact": "update request"}    // this is required so we only see open update requests, not finished ones
                ]
            })
            urStatusFrag += `<li>
                <a href="/admin/update_requests?source=${urStatusSource}">
                    <span>${status} <span>${data.by_status[status].update_requests}</span></span>
                    <span></span>
                </a>
            </li>`;
        }
    }

    // ~~-> ApplicationSearch:Page~~
    let appGroupSource = doaj.searchQuerySource({ "term" : [
        {"admin.editor_group.exact" : data.editor_group.name},
        {"index.application_type.exact" : "new application"}    // this is required so we only see open applications, not finished ones
    ]})
    let urGroupSource = doaj.searchQuerySource({ "term" : [
        {"admin.editor_group.exact" : data.editor_group.name},
        {"index.application_type.exact" : "update request"}    // this is required so we only see open applications, not finished ones
    ]})
    let frag = `<h3>
        ${data.editor_group.name}’s ongoing applications
        <span class="tag tag--secondary">
            <a href="/admin/applications?source=${appGroupSource}">${data.total.applications} <span class="sr-only">applications</span> APP</a> | 
            <a href="/admin/update_requests?source=${urGroupSource}">${data.total.update_requests} <span class="sr-only">update requests</span> UR</a>
        </span>
    </h3>

    <h4 class="label label--tertiary">By editor</h4>
    <ul class="inlined-list type-06">
        ${editorListFrag}
    </ul>

    <hr/>

    <h4 class="label label--tertiary">By status</h4>
    <h5>New Applications</h5>
    <ul class="inlined-list progress-bar">
        ${appStatusFrag}
    </ul>
    <h5>Update Requests</h5>
    <ul class="inlined-list progress-bar">
        ${urStatusFrag}
    </ul>`;
    return frag;
}