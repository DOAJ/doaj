from portality.core import app

class TourService(object):
    def activeTours(self, path, user):
        tours = app.config.get("TOURS", {})
        active_tours = []
        for k, v in tours.items():
            if self._is_active_path(path, k):
                for tour in v:
                    if "roles" in tour:
                        if user is None:
                            continue
                        for r in tour.get("roles"):
                            if user.has_role(r):
                                active_tours.append(tour)
                                break
                    else:
                        active_tours.append(tour)
        return active_tours

    def _is_active_path(self, given, candidate):
        sw = False
        if candidate.endswith("*"):
            candidate = candidate[:-1]
            sw = True

        if not sw and given == candidate:
            return True

        if sw and given.startswith(candidate):
            return True

        return False

    def validateContentId(self, content_id):
        tours = app.config.get("TOURS", {})
        for k, v in tours.items():
            for tour in v:
                if tour.get("content_id") == content_id:
                    return True
        return False