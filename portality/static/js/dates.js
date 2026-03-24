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
        },

        is_in_the_past: function(date, format=doaj.dates.format.FMT_DATE_STD) {
            const input = new Date(date);
            const today = new Date();

            // Force both to local date only
            input.setHours(0, 0, 0, 0);
            today.setHours(0, 0, 0, 0);

            return input < today;
        },

        parseDate: function(dateStr, format) {
            const formatMap = {
                'YYYY': '(\\d{4})',
                'YY': '(\\d{2})',
                'MM': '(\\d{2})',
                'M': '(\\d{1,2})',
                'DD': '(\\d{2})',
                'D': '(\\d{1,2})',
                'HH': '(\\d{2})',
                'H': '(\\d{1,2})',
                'mm': '(\\d{2})',
                'm': '(\\d{1,2})',
                'ss': '(\\d{2})',
                's': '(\\d{1,2})',
                'SSS': '(\\d{3})',
                'MMM': '([A-Za-z]{3})',
                'MMMM': '([A-Za-z]+)',
                'Z': 'Z'
            };

            const monthMap = {
                'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
                'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
            };

            // Create a regular expression to match the dateStr based on the format
            let regexPattern = format.replace(/YYYY|YY|MM|M|DD|D|HH|H|mm|m|ss|s|SSS|MMMM|MMM|Z/g, (match) => {
                return formatMap[match] || match;
            });

            const regex = new RegExp(`^${regexPattern}$`);
            const matches = dateStr.match(regex);

            if (!matches) {
                throw new Error("Date string does not match format");
            }

            // Extract components based on the format
            let year = 1970, month = 0, day = 1, hours = 0, minutes = 0, seconds = 0, milliseconds = 0;

            const formatTokens = format.match(/YYYY|YY|MM|M|DD|D|HH|H|mm|m|ss|s|SSS|MMMM|MMM|Z/g) || [];
            let matchIndex = 1;

            for (const token of formatTokens) {
                const value = matches[matchIndex++];
                switch (token) {
                    case 'YYYY':
                        year = parseInt(value, 10);
                        break;
                    case 'YY':
                        year = 2000 + parseInt(value, 10);
                        break;
                    case 'MM':
                    case 'M':
                        month = parseInt(value, 10) - 1;
                        break;
                    case 'MMM':
                        month = monthMap[value];
                        break;
                    case 'DD':
                    case 'D':
                        day = parseInt(value, 10);
                        break;
                    case 'HH':
                    case 'H':
                        hours = parseInt(value, 10);
                        break;
                    case 'mm':
                    case 'm':
                        minutes = parseInt(value, 10);
                        break;
                    case 'ss':
                    case 's':
                        seconds = parseInt(value, 10);
                        break;
                    case 'SSS':
                        milliseconds = parseInt(value, 10);
                        break;
                }
            }

            return new Date(year, month, day, hours, minutes, seconds, milliseconds);
        },

        formatDate: function (date, format) {
            const monthNamesShort = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const monthNamesFull = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

            const padZero = (num, length = 2) => String(num).padStart(length, '0');

            const replacements = {
                'YYYY': date.getFullYear(),
                'YY': String(date.getFullYear()).slice(-2),
                'MMMM': monthNamesFull[date.getMonth()],
                'MMM': monthNamesShort[date.getMonth()],
                'MM': padZero(date.getMonth() + 1),
                'M': date.getMonth() + 1,
                'DD': padZero(date.getDate()),
                'D': date.getDate(),
                'HH': padZero(date.getHours()),
                'H': date.getHours(),
                'mm': padZero(date.getMinutes()),
                'm': date.getMinutes(),
                'ss': padZero(date.getSeconds()),
                's': date.getSeconds(),
                'SSS': padZero(date.getMilliseconds(), 3)
            };

            // Replace format tokens in the string
            return format.replace(/YYYY|YY|MMMM|MMM|MM|M|DD|D|HH|H|mm|m|ss|s|SSS/g, (match) => replacements[match]);
        },

        reformat: function(s, inFormat, outFormat) {
            const parsedDate = doaj.dates.parseDate(s, inFormat);
            return doaj.dates.formatDate(parsedDate, outFormat);
        }

    }
});