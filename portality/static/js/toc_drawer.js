jQuery(document).ready(function ($) {
    if (!doaj.session.currentUserId) {
        $("#ur_nudge--link").on("click", (event) => {
            event.preventDefault();
            $("#drawer-login").addClass('is-open')
            $("#user").focus()
        });
    }

    $('[data-dismiss="drawer-login"]').on('click', function () {
        $("#drawer-login").removeClass('is-open');
    });

    $(document).on('click', function (event) {
        const $drawer = $('#drawer-login');
        if ($drawer.css('display') !== 'block') return;

        if (
            !$(event.target).closest('#ur_nudge--link').length &&
            !$(event.target).closest('.drawer').length &&
            !$(event.target).closest('.drawer__content').length &&
            !$(event.target).closest('[data-toggle="drawer-login"]').length
        ) {
            $drawer.removeClass('is-open');
        }
    });

    $(document).on('keydown', function (event) {
        const $drawer = $('#drawer-login');
        if (event.key === 'Escape' && $drawer.css('display') === 'block') {
            $drawer.hide();
        }
    });
})