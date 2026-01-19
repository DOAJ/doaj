jQuery(document).ready(function ($) {
    if (!("session" in doaj) || !("currentUserId" in doaj.session)) {
        $.extend(true, doaj, {
            session: {
                currentUserId: "{{ current_user.id }}"
            }
        });
    }
    if (!doaj.currentSessionId) {
        $("#ur_nudge--link").on("click", (event) => {
            event.preventDefault();
            $("#drawer-login").show()
            $("#user").focus()
        });
    }

    $(document).on('click', function (event) {
        const $drawer = $('#drawer-login');
        if ($drawer.css('display') !== 'block') return;

        if (
            !$(event.target).closest('#ur_nudge--link').length &&
            !$(event.target).closest('.drawer').length &&
            !$(event.target).closest('.drawer__content').length &&
            !$(event.target).closest('[data-toggle="drawer-login"]').length
        ) {
            $drawer.hide();
        }
    });

    $(document).on('keydown', function (event) {
        const $drawer = $('#drawer-login');
        if (event.key === 'Escape' && $drawer.css('display') === 'block') {
            $drawer.hide();
        }
    });
})