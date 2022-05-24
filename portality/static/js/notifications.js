doaj.notifications = {};
doaj.notifications.url = "/dashboard/top_notifications";

doaj.notifications.init = function() {
    $.ajax({
        method: "get",
        url: doaj.notifications.url,
        contentType: "application/json",
        dataType: "jsonp",
        success: doaj.notifications.notificationsReceived
    })
}

doaj.notifications.notificationsReceived = function(data) {
    let frag = "";
    for (let i = 0; i < data.length; i++) {
        let notification = data[i];
        frag += `<li>
            <a href="${notification.action}" class="dropdown__link notification_action_link">
                <span>${notification.message}</span>
                <time datetime="${notification.created_date}">${notification.created_date}</time>
            </a>
        </li>`;
    }
    frag += `<li>
      <a href="/dashboard/notifications" class="dropdown__link">
          See all notifications
      </a>
    </li>`;

    $("#top_notifications").html(frag);
}

jQuery(document).ready(function($) {
    doaj.notifications.init();
});