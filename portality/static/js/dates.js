$.extend(true, doaj, {
    dates: {
        format: {
           FMT_DATETIME_STD: 'YYYY-MM-DDTH:mm:ssZ',
           FMT_DATETIME_NO_SECS: 'YYYY-MM-DD H:mm',
           FMT_DATE_STD: 'YYYY-MM-DD'
        },

        humanYearMonth : function(datestr) {
            var date = new Date(datestr);
            var monthnum = date.getUTCMonth();
            var year = date.getUTCFullYear();

            if (isNaN(monthnum) || isNaN(year)) {
                return "";
            }

            return doaj.monthmap[monthnum] + " " + String(year);
        },

        humanDate : function(datestr) {
            var date = new Date(datestr);
            var dom = date.getUTCDate();
            var monthnum = date.getUTCMonth();
            var year = date.getUTCFullYear();

            if (isNaN(monthnum) || isNaN(year) || isNaN(dom)) {
                return "";
            }

            return String(dom) + " " + doaj.monthmap[monthnum] + " " + String(year);
        },

        humanDateTime : function(datestr) {
            var date = new Date(datestr);
            var dom = date.getUTCDate();
            var monthnum = date.getUTCMonth();
            var year = date.getUTCFullYear();
            var hour = date.getUTCHours();
            var minute = date.getUTCMinutes();

            if (isNaN(monthnum) || isNaN(year) || isNaN(dom) || isNaN(hour) || isNaN(minute)) {
                return "";
            }

            if (String(hour).length === 1) {
                hour = "0" + String(hour);
            }

            if (String(minute).length === 1) {
                minute = "0" + String(minute);
            }

            return String(dom) + " " + doaj.monthmap[monthnum] + " " + String(year) + " at " + String(hour) + ":" + String(minute);
        },

        iso_datetime2date : function(isodate_str) {
            /* >>> '2003-04-03T00:00:00Z'.substring(0,10)
             * "2003-04-03"
             */
            return isodate_str.substring(0,10);
        },

        iso_datetime2date_and_time : function(isodate_str) {
            /* >>> "2013-12-13T22:35:42Z".replace('T',' ').replace('Z','')
             * "2013-12-13 22:35:42"
             */
            if (!isodate_str) { return "" }
            return isodate_str.replace('T',' ').replace('Z','')
        }

    }
});