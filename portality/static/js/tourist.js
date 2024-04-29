if (!doaj.hasOwnProperty("tourist")) { doaj.tourist = {}}

doaj.tourist.cookiePrefix = "";
doaj.tourist.allTours = [];
doaj.tourist.currentTour = null;
doaj.tourist.contentId = null;

doaj.tourist.init = function(params) {
    doaj.tourist.allTours = params.tours || [];
    doaj.tourist.cookiePrefix = params.cookie_prefix;

    let available = doaj.tourist.listAvailableTours();
    let availableIds = available.map((x) => { return x.content_id });

    let navContainer = $("#dropdown--tour_nav")

    if (availableIds.length === 0) {
        navContainer.hide();
    } else {
        let tourNav = $("#feature_tours li");
        for (let navEntry of tourNav) {
            let ne = $(navEntry);
            let trigger = ne.find("a.trigger_tour");
            let tourId = trigger.attr("data-tour-id");
            if (!availableIds.includes(tourId)) {
                ne.hide();
            }
        }

        $(".trigger_tour").on("click", doaj.tourist.triggerTour);
        navContainer.show();
        navContainer.hoverIntent(doaj.tourist.showDropdown, doaj.tourist.hideDropdown);

        let first = doaj.tourist.findNextTour();
        if (first) {
            doaj.tourist.start(first);
        }
    }
}

doaj.tourist.showDropdown = function(e) {
    $("#feature_tours").show();
}
doaj.tourist.hideDropdown = function() {
    $("#feature_tours").hide();
}

doaj.tourist.findNextTour = function() {
    let cookies = document.cookie.split("; ");

    let first = false;
    for (let tour of doaj.tourist.allTours) {
        // check to see if required selectors are present on the page
        if (tour.selectors) {
            let selectorsPresent = 0;
            for (let selector of tour.selectors) {
                let el = $(selector);
                if (el.length > 0) {
                    selectorsPresent++;
                }
            }
            if (tour.selectors.length !== selectorsPresent) {
                continue;
            }
        }

        // if we are good to go ahead, then check the cookies to see if the tour needs to be shown
        let cookieName = doaj.tourist.cookiePrefix + tour.content_id + "=" + tour.content_id;
        let cookie = cookies.find(c => c === cookieName);

        // if it has not previously been shown, then show it
        if (!cookie) {
            first = tour;
            break;
        }
    }
    return first;
}

doaj.tourist.listAvailableTours = function() {
    let available = [];
    for (let tour of doaj.tourist.allTours) {
        // check to see if required selectors are present on the page
        if (tour.selectors) {
            let selectorsPresent = 0;
            for (let selector of tour.selectors) {
                let el = $(selector);
                if (el.length > 0) {
                    selectorsPresent++;
                }
            }
            if (tour.selectors.length !== selectorsPresent) {
                continue;
            }
        }
        available.push(tour);
    }
    return available;
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