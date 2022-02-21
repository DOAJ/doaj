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
        let querySource = doaj.searchQuerySource({"term" : [
            {"admin.editor.exact" : ed},
            {"admin.editor_group.exact" : data.editor_group.name}
        ]})
        let editorCount = data.by_editor[ed] || 0;
        editorListFrag += `<li>
            <a href="mailto:${data.editors[ed].email}" class="label tag">${ed}</a>
            <a href="/admin/applications?source=${querySource}" class="tag tag--secondary">${editorCount} <span class="sr-only">applications</span></a>
        </li>`;
    }

    // ~~-> ApplicationSearch:Page~~
    let unassignedSource = doaj.searchQuerySource({"term" : [
            {"admin.editor_group.exact" : data.editor_group.name},
            {"index.has_editor.exact": "No"}
    ]})
    editorListFrag += `<li>
        <span class="label tag tag--featured">unassigned</span>
        <a href="/admin/applications?source=${unassignedSource}" class="tag tag--secondary">${data.unassigned} <span class="sr-only">applications</span></a>
    </li>`;

    let statusFrag = "";
    let statuses = Object.keys(data.by_status);
    for (let i = 0; i < statuses.length; i++) {
        let status = statuses[i];
        // ~~-> ApplicationSearch:Page~~
        let statusSource = doaj.searchQuerySource({ "term" : [
            {"admin.editor_group.exact" : data.editor_group.name},
            {"admin.application_status.exact": status}
        ]})
        statusFrag += `<li>
            <a href="/admin/applications?source=${statusSource}">
                <span>${status} <span>${data.by_status[status]}</span></span>
                <span></span>
            </a>
        </li>`;
    }

    // ~~-> ApplicationSearch:Page~~
    let groupSource = doaj.searchQuerySource({ "term" : [
        {"admin.editor_group.exact" : data.editor_group.name}
    ]})
    let frag = `<h3>
        ${data.editor_group.name}’s ongoing applications
        <a href="/admin/applications?source=${groupSource}" class="tag tag--secondary">${data.total} <span class="sr-only">applications</span></a>
    </h3>

    <h4 class="label label--tertiary">By editor</h4>
    <ul class="inlined-list type-06">
        ${editorListFrag}
    </ul>

    <hr/>

    <h4 class="label label--tertiary">By status</h4>
    <ul class="inlined-list progress-bar">
        ${statusFrag}
    </ul>`;
    return frag;
}