# Continuations

This migrate script removes the existing "history" portion of a record in the index, and turns each record in
that list into a first-class journal object

    python portality/upgrade.py -u portality/migrate/continuations/continuations.json -v