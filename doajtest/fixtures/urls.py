VALID_URL_LISTS = [
    "https://www.sunshine.com",
    "http://www.moonlight.com",
    "https://www.cosmos.com#galaxy",
    "https://www.cosmos.com/galaxy",
    "https://www.cosmos.com/galaxy#peanut",
    "http://ftp.example.com/file%20name.txt",
    "https://revistalogos.policia.edu.co:8443/index.php/rlct/about",
    "https://revistalogos.policia.edu.co:65535/index.php/rlct/about",
    "https://revistalogos.policia.edu.co:0/index.php/rlct/about",
    'http://example-xxxx.xx:999/a/b/c?d=1&f=2#qq',
]

INVALID_URL_LISTS = [
    "ht:www",
    "nonexistent.com",
    "https://www.doaj.org and https://www.reddit.com",
    "http://www.doaj.org and www.doaj.org",
    "http://www.doaj.org, www.doaj.org",
    "http://www.doaj.org, https://www.doaj.org",
    "http://ftp.example.com/file name.txt",
    "https://revistalogos.policia.edu.co:65536/index.php/rlct/about",
    "https://revistalogos.policia.edu.co:655350/index.php/rlct/about"
]
