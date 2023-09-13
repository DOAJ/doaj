if (!doaj.hasOwnProperty("tourist")) { doaj.tourist = {}}

doaj.tourist.cookiePrefix = "";
doaj.tourist.allTours = [];
doaj.tourist.currentTour = null;
doaj.tourist.contentId = null;

doaj.tourist.init = function(params) {
    doaj.tourist.allTours = params.tours || [];
    doaj.tourist.cookiePrefix = params.cookie_prefix;

    $(".trigger_tour").on("click", doaj.tourist.triggerTour);

    let first = doaj.tourist.findNextTour();
    if (first) {
        doaj.tourist.start(first);
    }
}

doaj.tourist.findNextTour = function() {
    let cookies = document.cookie.split("; ");

    let first = false;
    for (let tour of doaj.tourist.allTours) {
        let cookieName = doaj.tourist.cookiePrefix + tour.content_id + "=" + tour.content_id;
        let cookie = cookies.find(c => c === cookieName);
        if (!cookie) {
            first = tour;
            break;
        }
    }
    return first;
}

doaj.tourist.start = function (tour) {
    doaj.tourist.contentId = tour.content_id;
    doaj.tourist.currentTour = new Tourguide({
        src: `/tours/${tour.content_id}`,
        onStart: doaj.tourist.startCallback,
        onComplete: doaj.tourist.completeCallback
    });
    doaj.tourist.currentTour.start()
}

doaj.tourist.startCallback = function(options) {
    doaj.tourist.seen({tour: doaj.tourist.contentId});
}

doaj.tourist.completeCallback = function(options) {
    doaj.tourist.currentTour = null;
    doaj.tourist.contentId = null;

    let next = doaj.tourist.findNextTour();
    if (next) {
        doaj.tourist.start(next);
    } else {
        $([document.documentElement, document.body]).animate({
            scrollTop: 0
        }, 500);
    }
}

doaj.tourist.seen = function(params) {
    $.ajax({
        type: "GET",
        url: `/tours/${doaj.tourist.contentId}/seen`,
        success: function() {}
    })
}

doaj.tourist.triggerTour = function(event) {
    event.preventDefault();
    let tour_id = $(event.currentTarget).attr("data-tour-id");
    doaj.tourist.start({content_id: tour_id});
}