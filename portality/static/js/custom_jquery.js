$.fn._show = function() {
    return this.each(function() {
        $(this).prop("hidden", false);
    });
};

$.fn._hide = function() {
    return this.each(function() {
        $(this).prop("hidden", true);
    });
};

$.fn._toggle = function() {
    return this.each(function() {
        $(this).prop("hidden", !$(this).prop("hidden"));
    });
};