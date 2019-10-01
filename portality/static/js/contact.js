jQuery(document).ready(function($) {

    function calculateRemaining() {
        var len = $("#message").val().length;
        var remaining = 1000 - len;
        if (remaining >= 0) {
            $("#wordcount").html(remaining + " remaining")
        } else {
            $("#wordcount").html((remaining * -1) + " over")
        }
    }

    $("#message").bind("keyup", function(event) {
        calculateRemaining()
    });

    calculateRemaining();
});