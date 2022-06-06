doaj.notifications = {};
doaj.notifications.top_url = "/dashboard/top_notifications";
doaj.notifications.seen_url = "/dashboard/notifications/{notification_id}/seen"
doaj.notifications.page_url = "/dashboard/notifications"

doaj.notifications.init = function() {
    $.ajax({
        method: "get",
        url: doaj.notifications.top_url,
        contentType: "application/json",
        dataType: "jsonp",
        success: doaj.notifications.notificationsReceived
    })
}

doaj.notifications.notificationsReceived = function(data) {
    let frag = "";
    for (let i = 0; i < data.length; i++) {
        let notification = data[i];
        let seenClass = notification.seen_date ? "notification_seen" : "notification_unseen";
        frag += `<li>
            <a href="${notification.action}" class="dropdown__link notification_action_link ${seenClass}" data-notification-id="${notification.id}">
                <span>${notification.message}</span>
                <time datetime="${notification.created_date}">${notification.created_date}</time>
            </a>
        </li>`;
    }
    frag += `<li>
      <a href="${doaj.notifications.page_url}" class="dropdown__link">
          See all notifications
      </a>
    </li>`;

    $("#top_notifications").html(frag);

    $(".notification_action_link").on("click", doaj.notifications.notificationClicked);
}

doaj.notifications.notificationClicked = function(event) {
    let el = $(this);
    let notificationId = el.attr("data-notification-id");
    doaj.notifications.setAsSeen(notificationId, el);
}

doaj.notifications.setAsSeen = function(notificationId, element) {
    $.ajax({
        method: "post",
        url: doaj.notifications.seen_url.replace("{notification_id}", notificationId),
        contentType: "application/json",
        dataType: "jsonp"
    });
    element.removeClass("notification_unseen").addClass("notification_seen");
}

jQuery(document).ready(function($) {
    doaj.notifications.init();
});