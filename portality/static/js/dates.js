$.extend(true, doaj, {
    dates: {
        format: {
           FMT_DATETIME_STD: 'YYYY-MM-DDTH:mm:ssZ',
           FMT_DATETIME_NO_SECS: 'YYYY-MM-DD H:mm',
           FMT_DATE_STD: 'YYYY-MM-DD'
        },
        reformat: function(s, inFormat, outFormat) {
            return moment(s, inFormat).format(outFormat);
        }

    }
});