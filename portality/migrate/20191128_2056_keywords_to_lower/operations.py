from portality import models
from portality.core import app
import esprit
import re

def rewrite_keywords(journal):
    bib = journal.bibjson()
    kwords = [k.lower() for k in bib.keywords]
    bib.set_keywords(kwords)
