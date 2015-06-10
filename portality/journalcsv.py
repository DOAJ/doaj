CSV_HEADER = ["Title", "Title Alternative", "Identifier", "Publisher", "Language",
                    "ISSN", "EISSN", "Keyword", "Start Year", "End Year", "Added on date",
                    "Subjects", "Country", "Publication fee", "Further Information",
                    "CC License", "Content in DOAJ"]

def csv(self, multival_sep=','):
    """
    CSV_HEADER = ["Title", "Title Alternative", "Identifier", "Publisher", "Language",
                "ISSN", "EISSN", "Keyword", "Start Year", "End Year", "Added on date",
                "Subjects", "Country", "Publication fee", "Further Information",
                "CC License", "Content in DOAJ"]
    """
    YES_NO = {True: 'Yes', False: 'No', None: '', '': ''}
    row = []

    bibjson = self.bibjson()
    index = self.data.get('index', {})
    row.append(bibjson.title) # Title
    row.append(bibjson.alternative_title) # Title Alternative
    # Identifier
    homepage = bibjson.get_urls(urltype="homepage")
    if len(homepage) > 0:
        row.append(homepage[0])
    else:
        row.append("")
    row.append(bibjson.publisher)
    row.append( multival_sep.join(bibjson.language))

    # we're following the old CSV format strictly for now, so only 1
    # ISSN allowed - below is the code for handling multiple ones

    # ISSN taken from Print ISSN
    # row.append( multival_sep.join([id_['id'] for id_ in c['identifier'] if id_['type'] == 'pissn']) )
    pissns = bibjson.get_identifiers(bibjson.P_ISSN)
    row.append(pissns[0] if len(pissns) > 0 else '') # just the 1st one

    # EISSN - the same as ISSN applies
    # row.append( multival_sep.join([id_['id'] for id_ in c['identifier'] if id_['type'] == 'eissn']) )
    eissns = bibjson.get_identifiers(bibjson.E_ISSN)
    row.append(eissns[0] if len(eissns) > 0 else '') # just the 1st one

    row.append( multival_sep.join(bibjson.keywords) ) # Keywords
    row.append( bibjson.oa_start.get('year', '')) # Year OA began
    row.append( bibjson.oa_end.get('year', '')) # Year OA ended
    row.append( self.created_date ) # Date created
    row.append( multival_sep.join([subject['term'] for subject in bibjson.subjects()]) ) # Subject terms
    row.append( index.get('country', '') ) # Country
    row.append( "" ) # author pays - DEPRECATED
    row.append("") # author pays url - DEPRECATED

    # for now, follow the strange format of the CC License column
    # that the old CSV had. Also, only take the first CC license we see!
    lic = bibjson.get_license()
    if lic is not None:
        lt = lic.get("type", "")
        if lt.lower().startswith("cc"):
            row.append(lt[3:])
        else:
            row.append("")
    else:
        row.append("")
    #cc_licenses = [lic['type'][3:] for lic in c.get('license', []) if lic['type'].startswith('cc-')]
    #row.append(cc_licenses[0] if len(cc_licenses) > 0 else '')

    row.append(YES_NO.get(self.is_in_doaj(), ""))
    return row
