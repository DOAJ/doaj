DOI_LIST = [
    "https://doi.org/10.3403/bseniso9233",
    "https://doi.org/10.1016/s1874-558x(04)80052-6",
    "https://doi.org/10.1002/9781444341850.ch3",
    "https://doi.org/10.1016/b978-0-12-417012-4.00029-6",
    "https://doi.org/10.3403/01095063",
    "https://doi.org/10.1016/b978-0-12-374407-4.00076-5",
    "https://doi.org/10.1016/j.foodhyd.2008.08.016",
    "http://dx.doi.org/10.20914/2310-1202-2016-4-135-140",
    "http://dx.doi.org/10.1590/S0104-66322008000200008",
    "http://dx.doi.org/10.1371/journal.pone.0057696",
    "http://dx.doi.org/10.14295/2238-6416.v71i4.511",
    "http://dx.doi.org/10.4081/ijas.2009.s2.450",
    "https://doi.org/10.3403string/bseniso9233",
    "https://doi.org/10.3403.999/bseniso9233",
    "HTTPS://DOI.ORG/10.3403/BSENISO9233",                                         # TODO: do we normalise case on save?
]

HANDLE_LIST = [
    "http://hdl.handle.net/10.1000/182",
    #"http://hdl.handle.net/10568/89928",       # FIXME: open question whether we should support prefixes other than 10.
    #"http://hdl.handle.net/1893/23601",
    #"http://hdl.handle.net/2134/6997"
]

INVALID_DOI_LIST = [
    "This is not a DOI or handle",
    "https://doaj.org",
    "http://dx.doi.org",
    "https://doi.org",
    "https://dx.doi.org/invalid",
    "http://hd&.handle.net/10.1234/567",
    "httpx://doi.org/10.3403/bseniso9233",
    "https:/doi.org/10.3403/bseniso9233",
    "https://doi.org/10.3403",
    "https://doi.org.uk/10.3403/bseniso9233",
    "https://doi.org/10.3403/   556",
    "   https://doi.org/10.3403/01095063",
    "https://doi.org/10.3403/01095063       ",
    "\thttps://doi.org/\t10.3403/01095063\t",
    "https://doi.org/10.3403/01095063\thttps://doi.org/\t10.3403/01095063\t"
]
