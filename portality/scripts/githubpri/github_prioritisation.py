import csv

from portality.scripts.githubpri import pri_data_serv


def priorities(priorities_file, outfile, username=None, password=None, ):
    table = pri_data_serv.create_priorities_excel_data(priorities_file, username, password)
    # with open(outfile, "w") as f:
    #     writer = csv.writer(f)
    #     writer.writerows(table)
    #
    print(table)
    table.to_csv('/tmp/pri.csv', index=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username")
    parser.add_argument("-p", "--password")
    parser.add_argument("-r", "--rules")
    parser.add_argument("-o", "--out")
    args = parser.parse_args()

    priorities(args.rules, args.out,
               username=args.username, password=args.password, )
