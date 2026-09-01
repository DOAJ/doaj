def set_created_date(obj):
    """ Set the create_date to a fixed point in time, this time approximately the migration to current DOAJ era """

    obj['created_date'] = "2014-03-19T00:00:00Z"
    return obj