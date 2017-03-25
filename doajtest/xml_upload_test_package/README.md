This directory contains some files you can use for manually testing the 
upload interface.

not_xml.xml - a file which claims to be XML but isn't.

schema_invalid.xml - an XML file which does not conform to the DOAJ schema

successful.xml - a DOAJ schema valid file which can be successfully imported.  Ensure the issn and eissn fields match the issns of a single journal owned by the test user

unmatched_issn.xml - a DOAJ schema valid file which cannot be imported because an ISSN is unmatched.  Ensure the issn field matches the issn of a journal owned by the test user, and the eissn is an unknown issn in DOAJ.

unowned_issn.xml - a DOAJ schema valid file which cannot be imported because an ISSN is owned by another user.  Ensure the issn field matches the issn of a journal owned by the test user, and the eissn is an issn owned by another user.

shared_issn.xml - a DOAJ schema valid file which cannot be imported because an ISSN is erronsouly owned by two users.  To use this file you'll need to modify your DOAJ data to allocate the issn and/or eissn to multiple users.

