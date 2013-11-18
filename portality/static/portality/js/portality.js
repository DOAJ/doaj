
jQuery(document).ready(function() {    
    
    // a default addition to ajax call to show a loading element, if configured
    $.ajaxSetup({
        beforeSend:function(){
            $("#loadcover").show();
            $("#loading").show();
        },
        complete:function(){
            $("#loadcover").hide();
            $("#loading").hide();
        }
    });


});


