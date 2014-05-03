from portality import models, article
import json, codecs

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--source", help="source file of articles to load")

    args = parser.parse_args()

    if not args.source:
        print "Please specify a source file with the -s option"
        exit()

    f = codecs.open(args.source)
    j = json.loads(f.read())

    for data in j:
        a = models.Article(**data)
        a.bibjson().remove_subjects()
        article.XWalk().add_journal_info(a)
        a.save()




