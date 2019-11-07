/*jshint esversion: 6 */
//import * as config from '/dev.cfg';

jQuery(document).ready(function($) {

    function calculateRemaining() {
        var len = $("#message").val().length;
        var remaining = 1000 - len;
        if (remaining >= 0) {
            $("#wordcount").html(remaining + " remaining");
        } else {
            $("#wordcount").html((remaining * -1) + " over");
        }
    }

    $("#message").bind("keyup", function(event) {
        calculateRemaining();
    });

    calculateRemaining();


});

var onloadCallback = function() {

    $("#submitBtn").prop("disabled", true);

    var captchaCallback = function(param) {
        $.get( "gettoken/" + param, function( data ) {
          if (!data.success) {
              window.alert("something went wrong" + data.error);
          }
          else {
              $("#submitBtn").prop("disabled", false);
          }
        });
  };

    function ajax1() {
         return $.get("get_site_key");
    }

    $.when(ajax1()).done(function(key) {
        window.console.log("now");
        grecaptcha.render('html_element', {
                'sitekey' : key,
                'callback' : captchaCallback,
            });
        }
    );


};