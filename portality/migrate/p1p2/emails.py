from portality.models import Account, Journal, Suggestion
import csv

ALL = "all_emails.csv"
MULTI = "multi_emails.csv"
APP = "application_emails.csv"

def get_publisher(acc):
    q = {
        "query" : {
            "bool" : {
                "must" : [
                    {"term" : {"admin.owner.exact" : acc.id}},
                    {"term" : {"admin.in_doaj" : True}}
                ]
            }

        },
        "size" : 0,
        "facets" : {
            "publishers" : {
                "terms" : {
                    "field" : "bibjson.publisher.exact",
                    "size" : 1000
                }
            }
        }
    }
    es = Journal.query(q=q)
    pubs = [term.get("term") for term in es.get("facets", {}).get("publishers", {}).get("terms", [])]
    if len(pubs) == 0:
        return None
    return ", ".join(pubs)

fall = open(ALL, "wb")
all_writer = csv.writer(fall)
all_writer.writerow(["Account ID", "Email", "Name", "Publisher"])

fmulti = open(MULTI, "wb")
multi_writer = csv.writer(fmulti)
multi_writer.writerow(["Account ID", "Email", "Name", "Publisher"])

print ("processing accounts")
for a in Account.iterall():
    id = a.id
    name = a.name
    count = len(a.journal) if a.journal is not None else 0
    email = a.email
    if email is None:
        continue
    
    publisher = None
    if count > 0:
        publisher = get_publisher(a)

    # if they don't publish any journals in the doaj, ignore their account
    if publisher is None:
        continue

    if name is not None:
        name = str(name).encode("utf8", "replace")
    if name is None or name == "":
        name = "no name available"
    publisher = str(publisher).encode("utf8", "replace")
    if email is not None and email != "":
        try:
            email = str(email, "utf8")
        except: pass
        emails = [e.strip() for e in email.encode("utf8", "replace").split(",") if e is not None and e != ""]
        for e in emails:
            row = [id, e, name, publisher]
            all_writer.writerow(row)
            if count > 1:
                multi_writer.writerow(row)

fall.close()
fmulti.close()


def get_suggesters():
    q = {
        "query" : {
            "filtered" : {
                "filter" : {
                    "bool": {
                        "should" : [
                            {"terms" : {"admin.application_status.exact" : ["pending", "answer received"]}},
                            {"missing" : {"field" : "admin.application_status"}}
                        ]
                    }
                }
            }

        },
        "size" : 0,
        "facets" : {
            "suggester" : {
                "terms" : {
                    "field" : "suggestion.suggester.email.exact",
                    "size" : 20000
                }
            }
        }
    }
    es = Suggestion.query(q=q)
    emails = [(term.get("term"), term.get("count")) for term in es.get("facets", {}).get("suggester", {}).get("terms", [])]
    return emails

def get_suggestions(email):
    q = {
        "query" : {
            "filtered" : {
                "filter" : {
                    "bool" : {
                        "must" : [{"term" : {"suggestion.suggester.email.exact" : email}}],
                        "should" : [
                            {"terms" : {"admin.application_status.exact" : ["pending", "answer received"]}},
                            {"missing" : {"field" : "admin.application_status"}}
                        ]
                    }
                }
            }
        }
    }
    return Suggestion.iterate(q)

fapp = open(APP, "wb")
app_writer = csv.writer(fapp)
app_writer.writerow(["Email", "Name", "Publisher", "Number of Applications"])

print ("processing suggestions")
for email, count in get_suggesters():
    suggs = get_suggestions(email)
    
    names = set()
    publishers = set()
    for sugg in suggs:
        name = sugg.suggester.get("name")
        publisher = sugg.bibjson().publisher
        if name is not None and name != "":
            names.add(name)
        if publisher is not None and publisher != "":
            publishers.add(publisher)
    
    if len(names) == 0:
        names.add("no name available")
    
    name = ", ".join(names)
    publisher = ", ".join(publishers)
    
    if name is not None:s
        name = str(name).encode("utf8", "replace")
    if name is None or name == "":
        name = "no name available"
    
    publisher = str(publisher).encode("utf8", "replace")
    
    try:
        email = str(email, "utf8")
    except: pass
    emails = [e.strip() for e in email.encode("utf8", "replace").split(",") if e is not None and e != ""]
    for e in emails:
        row = [e, name, publisher, count]
        app_writer.writerow(row)

fapp.close()































