doaj.dashboard = {};

doaj.dashboard.init = function() {
    $(".js-group-tab").on("click", doaj.dashboard.groupTabClick)
}

doaj.dashboard.groupTabClick = function(event) {
    let groupId = $(event.target).attr("data-group-id");
    doaj.dashboard.loadGroupTab(groupId);
}

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

    let allEditors = [data.editor_group.editor].concat(data.editor_group.associates);

    let editorListFrag = "";
    for (let i = 0; i < allEditors.length; i++) {
        let ed = allEditors[i];
        editorListFrag += `<li>
            <a href="#" class="label tag">${ed}</a>
            <a href="#" class="tag tag--secondary">${data.by_editor[ed]} <span class="sr-only">applications</span></a>
        </li>`;
    }

    editorListFrag += `<li>
        <a href="#" class="label tag tag--featured">unassigned</a>
        <a href="#" class="tag tag--secondary">${data.unassigned} <span class="sr-only">applications</span></a>
    </li>`;

    let statusFrag = "";
    let statuses = Object.keys(data.by_status);
    for (let i = 0; i < statuses.length; i++) {
        let status = statuses[i];
        statusFrag += `<li>
            <a href="#">
                <span>${status} <span>${data.by_status[status]}</span></span>
                <span></span>
            </a>
        </li>`
    }

    let frag = `<h3>
        ${data.editor_group.name}’s ongoing applications
        <a href="#" class="tag tag--secondary">${data.total} <span class="sr-only">applications</span></a>
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