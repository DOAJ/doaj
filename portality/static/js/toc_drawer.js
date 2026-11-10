doaj.toc_drawer = {};

doaj.toc_drawer.init = function () {
    if (doaj.current_user) {
        return
    }

    // the open link
    $("#ur_nudge--link").on("click", doaj.toc_drawer.onOpen);

    // the explicit close link
    $('[data-dismiss="drawer-login"]').on('click', doaj.toc_drawer.onClose);

    // click anywhere else on the page
    $(document).on('click', doaj.toc_drawer.onClickAway);

    // hit the escape key
    $(document).on('keydown', doaj.toc_drawer.onEscape);
}

doaj.toc_drawer.open = function () {
    $("#drawer-login").addClass('is-open')
    $("#user").focus()
}

doaj.toc_drawer.close = function() {
    const $drawer = $('#drawer-login');
    if ($drawer.css('display') !== 'block') {
        return;
    }
    $drawer.removeClass('is-open');
}

// event handlers

doaj.toc_drawer.onEscape = function (event) {
    if (event.key === 'Escape') {
        doaj.toc_drawer.close();
    }
}

doaj.toc_drawer.onOpen = function (event) {
    event.preventDefault();
    doaj.toc_drawer.open();
}

doaj.toc_drawer.onClose = function (event) {
    event.preventDefault();
    doaj.toc_drawer.close();
}

doaj.toc_drawer.onClickAway = function (event) {
    if (
        !$(event.target).closest('#ur_nudge--link').length &&
        !$(event.target).closest('.drawer').length &&
        !$(event.target).closest('.drawer__content').length &&
        !$(event.target).closest('[data-toggle="drawer-login"]').length
    ) {
        doaj.toc_drawer.close();
    }
}