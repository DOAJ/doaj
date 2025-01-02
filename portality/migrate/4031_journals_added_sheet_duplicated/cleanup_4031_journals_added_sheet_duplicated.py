from portality.models.datalog_journal_added import DatalogJournalAdded


def main():
    # remove all records
    query = {
        "query": {
            "match_all": {}
        },
    }
    DatalogJournalAdded.delete_by_query(query)


if __name__ == '__main__':
    main()
