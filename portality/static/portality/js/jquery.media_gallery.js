/*
 * jquery.media_gallery.js
 *
 * runs the gallery plugin for cl site (which relies on bootstrap-image-gallery)
 *
 * created by Mark MacGillivray - mark@cottagelabs.com
 *
 * copyheart 2012. http://copyheart.org
 *
 */

(function($){
    $.fn.media_gallery = function(options) {


//------------------------------------------------------------------------------
        // READY THE DEFAULTS

        // specify the defaults - currently pushed from Flask settings
        var defaults = {}

        // and add in any overrides from the call
        $.fn.media_gallery.options = $.extend(defaults,options)
        var options = $.fn.media_gallery.options
        
        var gallery = '<div id="absolute_media_gallery"> \
    <div id="uploadsection" class="hero-unit well" style="height:100px;"> \
    <p style="color:#aaa;">Drag and drop here to upload new files</p> \
    </div> \
    <p><button id="start-slideshow" class="btn" data-slideshow="5000" data-target="#modal-gallery" data-selector="#gallery a[rel=gallery]">slideshow</button> \
        <button id="toggle-fullscreen" class="btn" data-toggle="button">fullscreen</button> \
        <button id="close-gallery" class="btn" data-slideshow="5000" data-target="#modal-gallery" data-selector="#gallery a[rel=gallery]">close gallery</button>'
        //<button id="manual-upload" class="btn" data-slideshow="5000" data-target="#modal-gallery" data-selector="#gallery a[rel=gallery]">manual upload</button></p>
    //<p style="color:#ccc;">Drag and drop choices onto page text area or media display</p> 
    gallery += '</p> \
    <div id="gallery" data-toggle="modal-gallery" data-target="#modal-gallery"></div> \
    <div id="modal-gallery" class="modal modal-gallery hide fade"> \
        <div class="modal-header"> \
            <a class="close" data-dismiss="modal">&times;</a> \
            <h3 class="modal-title"></h3> \
        </div> \
        <div class="modal-body"><div class="modal-image"></div></div> \
        <div class="modal-footer"> \
            <a class="btn modal-download" target="_blank"> \
                <i class="icon-download"></i> \
                <span>Download</span> \
            </a> \
            <a class="btn modal-play modal-slideshow" data-slideshow="5000"> \
                <i class="icon-play"></i> \
                <span>Slideshow</span> \
            </a> \
            <a class="btn modal-next"> \
                <span>Next</span> \
                <i class="icon-arrow-right"></i> \
            </a> \
            <a class="btn modal-prev"> \
                <i class="icon-arrow-left"></i> \
                <span>Previous</span> \
            </a> \
        </div> \
    </div> \
</div>'

        var savethis = function(event) {
            event = event.originalEvent
            event.preventDefault()
            var upfile = event.dataTransfer.files[0]
            $.ajax({
                type: 'POST', 
                url: '/media/' + upfile.name, 
                data: upfile,
                processData: false,
                contentType: false,
                success: function() {window.location = window.location}
            })
        }

        var close = function(event) {
            event.preventDefault()
            $('#absolute_media_gallery').remove()
        }

        var manual = function(event) {
            event.preventDefault()
            alert('trigger manual file upload choice for failing drag and drop')
        }

        return this.each(function() {
        
            $.ajax({
                url: '/media',
                method: 'GET',
                headers: {
                    Accept: 'application/json'
                },
                success: function(data) {
                    var g = ''
                    for (var f in data) {
                        var p = data[f].split('.')
                        var pp = p[p.length - 1]
                        if ( pp =='png' || pp == 'jpg' || pp == 'jpeg' || pp == 'gif' ) {
                            g += '<a rel="gallery" _target="blank" class="span2 thumbnail" href="/media/'
                            g += data[f] + '"><img src="/media/' + data[f] + '" /></a>'
                        } else {
                            g += '<div class="span2 thumbnail"><h3><a _target="blank" href="/media/'
                            g += data[f] + '">' + data[f] + '</a></h3></div>'
                        }
                    }
                    $('#gallery').append(g)
                }
            })
        
            
            $(this).append(gallery)
            $('#uploadsection').on('dragover', function (e) {
                e = e.originalEvent
                e.preventDefault()
                e.dataTransfer.dropEffect = 'copy'
            })
            .on('drop', savethis)
            //$('#file-input').on('change', load);

            // Start slideshow button:
            $('#start-slideshow').button().click(function () {
                var options = $(this).data(),
                    modal = $(options.target),
                    data = modal.data('modal')
                if (data) {
                    $.extend(data.options, options)
                } else {
                    options = $.extend(modal.data(), options)
                }
                modal.find('.modal-slideshow').find('i')
                    .removeClass('icon-play')
                    .addClass('icon-pause')
                modal.modal(options);
            });
            // Toggle fullscreen button:
            $('#toggle-fullscreen').button().click(function () {
                var button = $(this),
                    root = document.documentElement
                if (!button.hasClass('active')) {
                    $('#modal-gallery').addClass('modal-fullscreen');
                    if (root.webkitRequestFullScreen) {
                        root.webkitRequestFullScreen(
                            window.Element.ALLOW_KEYBOARD_INPUT
                        );
                    } else if (root.mozRequestFullScreen) {
                        root.mozRequestFullScreen()
                    }
                } else {
                    $('#modal-gallery').removeClass('modal-fullscreen');
                    (document.webkitCancelFullScreen ||
                        document.mozCancelFullScreen ||
                        $.noop).apply(document)
                }
            })
            
            $('#close-gallery').bind('click',close)
            $('#manual-upload').bind('click',manual)
            
        })

    }

    // options are declared as a function so that they can be retrieved
    // externally (which allows for saving them remotely etc)
    $.fn.media_gallery.options = {}

})(jQuery)
