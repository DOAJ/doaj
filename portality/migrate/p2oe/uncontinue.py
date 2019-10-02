from portality import models

# these are the ids of the journal and the issn of the erroneous continuation
id = "d241030fda0b419f9aaaf542d57a61af"
issn = "0049-3449"

# details to create the new journal record
name = "Maluch Vergara"
email = "malucha.vergara@uc.cl"
owner = "00493449"

# get the journal and the other journal's bibjson from the history
para = models.Journal.pull(id)
vida = para.get_history_for(issn)

# create a new journal record from the bibjson, and set some default values
new = models.Journal()
new.set_bibjson(vida)
new.set_in_doaj(True)
new.set_application_status("accepted")
new.add_note("Journal separated from erroneous continuation by CL")
new.add_contact(name, email)
new.set_owner(owner)
new.save()
print ("Created new record with id", new.id)

# remove the erroneous journal from the history, add a note, and re-save the original journal
para.remove_history(issn)
para.add_note("CL removed journal " + issn + " from continuations history; was there erroneously")
para.save()
print ("Removed erroneous record from", id)