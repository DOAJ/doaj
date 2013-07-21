/*
 * jquery.jsite.js
 *
 * a tool for controlling edit functionality on the CL website
 * almost abstracted enough to be used as a lib on other sites
 *
 * DOES NOT WORK WITHOUT jquery.jtedit.js and jquery.facetview.js
 * 
 * created by Mark MacGillivray - mark@cottagelabs.com
 *
 * copyheart 2012. http://copyheart.org
 *
 */

(function($){
    $.fn.jsite = function(options) {


//------------------------------------------------------------------------------
        // READY THE DEFAULTS

        // specify the defaults - currently pushed from Flask settings
        var defaults = {
            "post_pagebuild_callback": false
        };

        // and add in any overrides from the call
        $.fn.jsite.options = $.extend(defaults,options);
        var options = $.fn.jsite.options;
        
        
//------------------------------------------------------------------------------
        // BUILD THE PAGE DEPENDING ON SETTINGS AND PERMISSIONS
        var makepage = function() {
            var singleedit = function(event) {
                event.preventDefault();
                editpage();
            };
            
            if ( !options.newrecord && !options.data['editable'] ) {
                viewpage();
            } else if ( options.editable ) {
                if ( options.data['editable'] && options.loggedin ) {
                    editpage();
                }
            } else {
                $('.edit_page').hide();
                $('.edit_page').parent().next().hide();
            }
        }
        

        // do the nested embed of dynamic divs
        var embed = function(data) {
            var content = data['content'];
            this.into.html('');
            this.into.append(content);
            this.into.attr('id',data['id']);
            this.into.addClass('expanded');
            var children = [];
            this.into.find('.dynamic').each(function() {
                children.push($(this).attr('data-source').replace('.json',''));
                var src = $(this).attr('data-source').replace('.json','') + '.json';
                $.ajax({"url": src, "success": embed, "into": $(this)});
            });
            if ( $('.dynamic').not('.expanded').length == 0 && typeof options.post_pagebuild_callback == 'function') {
                // add any action events to all the things in the page now
                // - the facetview builder should probably happen now for example
                // put in an option to edit the embedded page directly, if logged in?
                options.post_pagebuild_callback.call(this);
            };
        };        
        // VIEW A PAGE AS NORMAL
        var viewpage = function(event) {
            // replace any dynamic content divs with the actual content
            $('.dynamic').each(function() {
                var src = $(this).attr('data-source').replace('.json','') + '.json';
                $.ajax({"url": src, "success": embed, "into": $(this)});
            });
        
            // put any facetviews into any facetview divs
            $('.facetview').each(function() {
                var opts = jQuery.extend(true, {}, options.facetview); // clone the options
                for ( var style in options.facetview_displays ) {
                    $(this).hasClass('facetview-' + style) ? opts = $.extend(opts, options.facetview_displays[style] ) : "";
                };
                $(this).hasClass('facetview-slider') ? opts.pager_slider = true : "";
                $(this).hasClass('facetview-descending') ? opts['sort'] = [{"created_date.exact":{"order":"desc"}}] : "";
                $(this).hasClass('facetview-ascending') ? opts['sort'] = [{"created_date.exact":{"order":"asc"}}] : "";
                if ( $(this).hasClass('facetview-searchable') ) {
                    opts.embedded_search = true;
                } else {
                    opts.embedded_search = false;
                };
                $(this).attr('data-search') ? opts.q = $(this).attr('data-search') : "";
                $(this).attr('data-size') ? opts.paging.size = $(this).attr('data-size') : "";
                $(this).attr('data-from') ? opts.paging.from = $(this).attr('data-from') : "";
                $(this).facetview(opts);
            });

            // enable commenting if necessary
            if ( options.data["comments"] && options.comments ) {
                var disqus = '<div id="comments" class="container"><div class="comments"><div class="row-fluid" id="disqus_thread"></div></div></div> \
                    <script type="text/javascript"> \
                    var disqus_shortname = "' + options.comments + '"; \
                    (function() { \
                        var dsq = document.createElement("script"); dsq.type = "text/javascript"; dsq.async = true; \
                        dsq.src = "http://" + disqus_shortname + ".disqus.com/embed.js"; \
                        (document.getElementsByTagName("head")[0] || document.getElementsByTagName("body")[0]).appendChild(dsq); \
                    })(); \
                </script>';
                $('#main').after(disqus);
            };
        };
        
        // SHOW EDITABLE VERSION OF PAGE
        var editpage = function(event) {
            event ? event.preventDefault() : ""
            var record = options.data
        
            $('.edit_page').parent().remove();
            $('#facetview').hide()
            $('#topstrap').hide()
            $('#bottom').hide()
            $('#article').html("")
                                    
            // if collaborative edit is on, get the content from etherpad
            if ( options.collaborative ) {
                $('#article').hide()
                $('hr').hide()
                $('#main').css({
                    'position':'absolute',
                    'z-index':1000,
                    'width':'100%'
                })
                $('body > .container > .content').css({
                    'padding-top':0,
                    'padding-bottom':0,
                })
                var collab_edit = '<div id="collab_edit"></div>'
                $('body').append(collab_edit)
                $('#collab_edit').css({
                    'padding':0,
                    'margin':'40px 0 0 0',
                    'position':'absolute',
                    'top':0,
                    'left':0,
                    'width':'100%',
                    'z-index':2
                })
                $('#collab_edit').pad({
                  'padId'             : record.id,
                  'host'              : 'http://pads.cottagelabs.com',
                  'baseUrl'           : '/p/',
                  'showControls'      : true,
                  'showChat'          : true,
                  'showLineNumbers'   : true,
                  'userName'          : 'unnamed',
                  'useMonospaceFont'  : false,
                  'noColors'          : false,
                  'hideQRCode'        : false,
                  'height'            : '100%',
                  'border'            : 0,
                  'borderStyle'       : 'solid'
                })
                $('#collab_edit').height( $(window).height() - 44 )
            } else {
                var editor = '<div class="row-fluid" style="margin-bottom:20px;"><div class="span12"> \
                    <textarea class="tinymce jtedit_value data-path="content" id="form_content" name="content" \
                    style="width:99%;min-height:300px;" placeholder="content. text, markdown or html will work."> \
                    </textarea></div></div>'
                $('#article').append(editor)
                if ( options.richtextedit ) {
	                $('textarea.tinymce').tinymce({
		                script_url : '/static/vendor/tinymce/jscripts/tiny_mce/tiny_mce.js',
		                theme : "advanced",
		                plugins : "autolink,lists,style,layer,table,advimage,advlink,inlinepopups,media,searchreplace,contextmenu,paste,fullscreen,noneditable,nonbreaking,xhtmlxtras,advlist",
		                theme_advanced_buttons1 : "bold,italic,underline,|,justifyleft,justifycenter,justifyright,justifyfull,formatselect,fontselect,fontsizeselect,|,forecolor,backcolor,|,bullist,numlist,|,outdent,indent,blockquote,|,sub,sup,|,styleprops",
		                theme_advanced_buttons2 : "undo,redo,|,cut,copy,paste,|,search,replace,|,hr,link,unlink,anchor,image,charmap,media,table,|,insertlayer,moveforward,movebackward,absolute,|,cleanup,code,help,visualaid,fullscreen",
		                theme_advanced_toolbar_location : "top",
		                theme_advanced_toolbar_align : "left",
		                theme_advanced_statusbar_location : "bottom",
		                theme_advanced_resizing : true,

	                })
	            }
                $('#form_content').val(record['content'])
            }

        }

        

//------------------------------------------------------------------------------
        // TWEETS
        var tweets = function() {
            $(".tweet").tweet({
                username: options.twitter,
                avatar_size: 48,
                count: 5,
                join_text: "auto",
                auto_join_text_default: "",
                auto_join_text_ed: "",
                auto_join_text_ing: "",
                auto_join_text_reply: "",
                auto_join_text_url: "",
                loading_text: "loading tweets..."
            })
        }

        // scroll to anchors with offset
        var scroller = function(event) {
            if ( $(this).attr('href').length > 1 && $(this).attr('href').substring(0,1) == '#' ) {
                event.preventDefault()
                $('html,body').animate({scrollTop: $('a[name=' + $(this).attr('href').replace('#','') +  ']').offset().top - 70}, 10)
            }
        }

        var contactus = function(event) {
            event.preventDefault()
            
            var try_again = function(event) {
                event.preventDefault()
                
                var form = $(this).parent().siblings("form")
                $(this).parent().detach()
                form.show()
            }
            
            var form = $(this).parent()
            var message = form.children('[name="message"]').val()
            var email = form.children('[name="email"]').val()
            var action = form.attr("action")
            $.post(action, {"message" : message, "email" : email})
                .success(function() {
                    form.hide()
                    form.parent().prepend('<div class="alert alert-success" style="text-align:left;">thanks for your message! we\'ll get back to you as soon as we can</div>')
                })
                .error(function() {
                    form.hide()
                    form.parent().prepend('<div class="alert alert-error" style="text-align:left;">oops! something went wrong sending your message; please <a href="/contact" id="contact_try_again">try again</a></div>') 
                    $('#contact_try_again').bind('click', try_again)
                })
        }

        return this.each(function() {
                        
            // make the topnav sticky on scroll if on big screen
            if ( $(window).width() > 797 ) {
                var fromtop = '';
                $(window).scroll(function() {
		            if ( $(window).scrollTop() > $('#topnav').offset().top && $('#topnav').hasClass('navbar-in-page') ) {
		                fromtop = $('#topnav').offset().top;
                        $('#topnav').removeClass('navbar-in-page');
                        $('#topnav').addClass('navbar-fixed-top');
                        $('body').css({'padding-top':'40px'});
                        if ( $('#subnav').length ) {
                            $('#subnav').addClass('subnav-fixed-top');
                            $('body').css({'padding-top':'80px'});
                        };
                    };
                    if ( $(window).scrollTop() < fromtop && $('#topnav').hasClass('navbar-fixed-top') ) {
                        if ( $('#subnav').length ) {
                            $('#subnav').removeClass('subnav-fixed-top');
                        };
                        $('#topnav').removeClass('navbar-fixed-top');
                        $('#topnav').addClass('navbar-in-page');
                        $('body').css({'padding-top':'0px'});
                    };
                });
            };

            // bind new page creation to new page button
            var newpage = function(event) {
                event.preventDefault();
                var subaddr = window.location.pathname;
                subaddr.charAt(subaddr.length-1) != '/' ? subaddr += '/' : "";
                var newaddr = prompt('what / where ?',subaddr);
                newaddr.indexOf('/null') == -1 ? window.location = newaddr : "";
            };
            $('#new_page').bind('click',newpage);

            // bind anchor scroller offset fix
            $('a').bind('click',scroller);

            // bind the twitter display if twitter account provided
            options.twitter ? tweets() : false;
            
            // add the contact us form handler
            $('#submit_contact').bind('click', contactus);
            
            makepage();

        });

    };

    // options are declared as a function so that they can be retrieved
    // externally (which allows for saving them remotely etc)
    $.fn.jsite.options = {};

})(jQuery)

