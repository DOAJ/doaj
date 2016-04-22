from portality import models
from portality.core import app
from portality.clcsv import UnicodeWriter
import esprit
import codecs


PENDING = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"admin.application_status.exact" : "reapplication"}}
            ]
        }
    }
}

if __name__ == "__main__":

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print "Please specify an output file path with the -o option"
        parser.print_help()
        exit()

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    with codecs.open(args.out, "wb", "utf-8") as f:
        writer = UnicodeWriter(f)
        writer.writerow(["ID", "Journal Name", "E-ISSN", "P-ISSN", "Owner"])

        for s in esprit.tasks.scroll(conn, models.Suggestion.__type__, q=PENDING, page_size=100, keepalive='10m'):
            sugg = models.Suggestion(_source=s)
            journal_id = sugg.current_journal
            journal = models.Journal.pull(journal_id)

            if journal is not None:
                if journal.is_in_doaj():
                    journal.set_in_doaj(False)
                    journal.remove_current_application()
                    journal.add_note("Journal automatically withdrawn from DOAJ due to unreturned reapplication")
                    journal.save()
                    journal.propagate_in_doaj_status_to_articles()  # will save each article, could take a while

                    bibjson = journal.bibjson()
                    writer.writerow([journal.id, bibjson.title, bibjson.get_one_identifier(bibjson.E_ISSN), bibjson.get_one_identifier(bibjson.P_ISSN), journal.owner])

            sugg.delete()







