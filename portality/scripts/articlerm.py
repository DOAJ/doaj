from portality import models

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username", help="username of user whose articles to remove.")
    parser.add_argument("-g", "--ghost", help="specify if you want the articles being deleted not to be snapshot", action="store_true")

    args = parser.parse_args()

    if not args.username:
        print "Please specify a username with the -u option"
        exit()

    snapshot = not args.ghost

    models.Article.delete_selected(owner=args.username, snapshot=snapshot)

