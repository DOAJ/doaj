#### ```remove_duplicate_subjects.py```
*S.E. Feb 2016*

Fix for issue 982, where append in ```GenericBibJSON.add_subject()``` was
creating duplicate subjects each time ```models.Article.add_journal_metadata()```
was run.
