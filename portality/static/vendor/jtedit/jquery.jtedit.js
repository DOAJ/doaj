/*
 * jquery.jtedit.js
 *
 * a tool for prettily displaying JSON objects
 * and allowing edit of them
 * 
 * created by Mark MacGillivray - mark@cottagelabs.com
 *
 * copyheart 2012. http://copyheart.org
 * Copying is an act of love. Please copy and share.
 *
 * If you need more licensyness, the most you are going to get from me is
 * http://sam.zoy.org/wtfpl/COPYING
 *
 */


(function($){
    $.fn.jtedit = function(options) {

        // specify the defaults
        var defaults = {
            "makeform": true,               // whether or not to build the form first
            "actionbuttons": true,         // whether or not to show action buttons
            "jsonbutton": true,             // show json button or not (alt. for these is write the buttons yourself)
            "source":undefined,             // a source from which to GET the JSON data object
            "target":undefined,             // a target to which updated JSON should be POSTed
            "noedit":[],                    // a list of keys that should not be editable, when edit is enabled
            "data":undefined,               // a JSON object to render for editing
            "delete_redirect":"#",          // where to redirect to after deleting
            "addable":{},                   // things that should be provided as addables to the item
            "customadd": true,              // whether or not user can specify new item name
            "tags": []
        }

        // add in any overrides from the call
        var options = $.extend(defaults,options)

        // add in any options from the query URL
        var geturlparams = function() {
            var vars = [], hash
            var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&')
            for (var i = 0; i < hashes.length; i++) {
                    hash = hashes[i].split('=')
                    vars.push(hash[0])
                    if (!(hash[1] == undefined)) {
                        hash[1] = unescape(hash[1])
                        if (hash[0] == "source") {
                            hash[1] = hash[1].replace(/"/g,'')
                        } else if (hash[0] == "data") {
                            hash[1] = $.parseJSON(hash[1])
                        }
                    }
                    vars[hash[0]] = hash[1]
            }
            return vars
        }
        $.extend(options,geturlparams())


        // ===============================================        
                
        // visualise the data values onto the page form elements
        // and create the form elements in the process if necessary
        var dovisify = function() {
            var visify = function(data,route) {
                for (var key in data) {
                    route == undefined ? thisroute = key : thisroute = route + '_' + key
                    if ( typeof(data[key]) == 'object' ) {
                        visify(data[key],thisroute)
                    } else {
                        options.makeform != "done" ? $('#jtedit').append('<input type="text" class="jtedit_value jtedit_' + thisroute + '" />') : ""
                        $('.jtedit_' + thisroute).val( data[key] )
                    }
                }
            }
            visify( options.data )
            if ( options.makeform != "done" ) {
                $('.jtedit_value').autoResize({minHeight: 20, maxHeight:300, minWidth:50, maxWidth: 300, extraSpace: 5})
                $('.jtedit_value').bind('blur',updates)
                $('.jtedit_value').bind('mouseup',selectall)
                options.makeform = "done"
            }
            updates()
        }


        // parse visualised values from the page
        var parsevis = function() {
            function parser(scope, path, value) {
                var path = path.split('_'), i = 1, lim = path.length
                for (; i < lim; i += 1) {
                    if (typeof scope[path[i]] === 'undefined') {
                        parseInt(path[i+1]) == 0 ? scope[path[i]] = [] : scope[path[i]] = {}
                    }
                    i === lim - 1 ? scope[path[i]] = value : scope = scope[path[i]]
                }
            }
            var scope = {}
            $('.jtedit_value').each(function() {
                var classes = $(this).attr('class').split(/\s+/)
                for ( var cls in classes ) {
                    if ( classes[cls].indexOf('jtedit_') == 0 && classes[cls] != 'jtedit_value' ) {
                        var path = classes[cls]
                        break
                    }
                }                
                parser(scope, path, $(this).val())
            })
            return scope
        }
        
        // ===============================================
        
        // update JSON when changes occur on visual display
        var updates = function(event) {
            $('#jtedit_json').val(JSON.stringify(parsevis(),"","    "))
        }
        
        // update visual display when raw JSON updated
        var editjson = function(event) {
            options.data = $.parseJSON($(this).val())
            dovisify()
        }

        // select all in input / textarea
        var selectall = function(event) {
            event.preventDefault()
            $(this).select()
        }

        // save the record
        var jtedit_saveit = function(event,datain) {
            event.preventDefault()
            !datain ? datain = $.parseJSON(jQuery('#jtedit_json').val()) : false
            !options.target ? options.target = prompt('Please provide URL to save this record to:') : false
            if (options.target) {
                $.ajax({
                    url: options.target
                    , type: 'POST'
                    , data: JSON.stringify(datain)
                    , contentType: "application/json; charset=utf-8" 
                    , dataType: 'json'
                    , processData: false
                    , success: function(data, statusText, xhr) {
                        alert("Changes saved")
                        window.location = window.location
                    }
                    , error: function(xhr, message, error) {
                        alert("Error... " + error)
                    }
                })
            } else {
                alert('No suitable URL to save to was provided')
            }
        }

        // delete the record
        var jtedit_deleteit = function(event) {
            event.preventDefault()
            if (!options.target) {
                alert('There is no available source URL to delete from')
            } else {
                var confirmed = confirm("You are about to irrevocably delete this. Are you sure you want to do so?")
                if (confirmed) {
                    $.ajax({
                        url: options.target
                        , type: 'DELETE'
                        , success: function(data, statusText, xhr) {
                            alert("Deleted.")
                            window.location = options.delete_redirect
                        }
                        , error: function(xhr, message, error) {
                            alert("Error... " + error)
                        }
                    })
                }
            }
        }
        
        // show raw json on request
        var jtedit_json = function(event) {
            event.preventDefault()
            $('#jtedit_json').toggle()
        }
        
        // get data from a source URL
        var data_from_source = function(sourceurl) {
            $.ajax({
                url: sourceurl
                , type: 'GET'
                , success: function(data, statusText, xhr) {
                    options.data = data
                    dovisify()
                }
                , error: function(xhr, message, error) {
                    options.source = false
                    alert("Sorry. Your data could not be parsed from " + sourceurl + ". Please try again, or paste your data into the provided field.")
                    $('#jtedit_visual').hide()
                    $('#jtedit_json').show()
                }
            })
        }

        // ===============================================

        // create the plugin on the page
        return this.each(function() {

            obj = $(this)

            $('#jtedit',obj).remove()
            $(obj).append('<div id="jtedit" class="clearfix"></div>')
            var actions = ''
            if ( options.jsonbutton ) { actions += '<div class="jtedit_actions"><a class="btn jtedit_json" href="">show JSON</a>' }
            if ( options.actionbuttons ) {
                actions += ' <a class="jtedit_saveit btn btn-primary" href="save"><i class="icon-check icon-white"></i> save</a> ' + 
                '<a class="jtedit_deleteit btn btn-danger" href=""><i class="icon-remove icon-white"></i> delete</a>'
            }
            actions += '</div>'
            $('#jtedit').append( actions + '<div id="jtedit_visual"></div><textarea id="jtedit_json"></textarea>' )
                        
            $('#jtedit_json').hide()
            $('#jtedit_json').bind('blur',editjson)
            
            $('.jtedit_saveit').bind('click',jtedit_saveit)
            $('.jtedit_deleteit').bind('click',jtedit_deleteit)
            $('.jtedit_json').bind('click',jtedit_json)
            
            if (options.source) {
                data_from_source(options.source)
            } else if (options.data) {
                dovisify()
            } else {
                options.data = {"author": ["pretend",["list","inalist"],{"id": "PohlAdrian","name": "Pohl, Adrian"}], "journal":{"id":"somejournal","name":"somename"}, "biburl": "http://www.bibsonomy.org/bibtex/229ff5da471fd9d2706f2fd08c17b43dc/acka47", "cid": "Pohl_2010_LOD", "collection": "pohl", "copyright": "http://creativecommons.org/licenses/by/2.5/","id": "531e7aa806574787897314010f29d4cf", "keyword": ["ODOK hbz libraries linkeddata myown opendata presentation"], "link": [{"url": "http://www.slideshare.net/acka47/pohl-20100923-odoklod"}], "month": "September", "owner": "test", "title": "Freie Katalogdaten und Linked Data", "url": "http://localhost:5000/test/pohl/Pohl_2010_LOD", "year": "2010" }
                dovisify()
            }

        })

    }
})(jQuery)




