from portality.bll.services.notifications import NotificationsService


class InterceptNotifications(NotificationsService):
    def __init__(self, intercept_to):
        super(InterceptNotifications, self).__init__()
        self.intercept_to = intercept_to

    def notify(self, notification):
        notification = super().notify(notification)
        self.intercept_to.append(notification)
        return notification