import re
from portality.models import JournalLikeObject


def rename_policy(journal_like: JournalLikeObject):
    """ Update the name of Sherpa/Romeo to Open Policy Finder in metadata """
    jbib = journal_like.bibjson()
    if "Sherpa/Romeo" in jbib.deposit_policy:
        jbib.remove_deposit_policy("Sherpa/Romeo")
        jbib.add_deposit_policy("Open Policy Finder")
    return journal_like


def rewrite_sherpa_url(journal_like: JournalLikeObject):
    """ Substitute the updated URL for Open Policy Finder  """
    jbib = journal_like.bibjson()
    policy_url = jbib.deposit_policy_url
    if policy_url is not None:
        jbib.deposit_policy_url = re.sub(r'\s?https?://(v2|www)\.sherpa\.ac\.uk/',
                                         "https://openpolicyfinder.jisc.ac.uk/",
                                         policy_url)
    return journal_like

