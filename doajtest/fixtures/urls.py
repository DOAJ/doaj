VALID_URL_LISTS = [
    "https://www.sunshine.com",
    "http://www.moonlight.com",
    "https://www.cosmos.com#galaxy",
    "https://www.cosmos.com/galaxy",
    "https://www.cosmos.com/galaxy#peanut",
    "http://ftp.example.com/file%20name.txt"
]

INVALID_URL_LISTS = [
    "ht:www",
    "nonexistent.com",
    "https://www.doaj.org and https://www.reddit.com",
    "http://www.doaj.org and www.doaj.org",
"http://www.doaj.org, www.doaj.org",
"http://www.doaj.org, https://www.doaj.org",
"http://ftp.example.com/file name.txt"
]