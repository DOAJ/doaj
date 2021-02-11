var onloadCallback = function() {

    $("#submitBtn").prop("disabled", true);

    var captchaCallback = function(param) {
      $('#recaptcha_value').val(param);
      $("#submitBtn").prop("disabled", false);
  };

    function ajax1() {
         return $.get("/get_recaptcha_site_key");
    }

    $.when(ajax1()).done(function(key) {
        grecaptcha.render('recaptcha_div', {
                'sitekey' : key,
                'callback' : captchaCallback,
            });
        }
    );
};