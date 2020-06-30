from portality.models.journal import JournalBibJSON

class JCTInProgressXWalk(object):

    @classmethod
    def application2jct(cls, application):
        bj = application.bibjson()
        assert isinstance(bj, JournalBibJSON)

        record = {}
        record["doaj_id"] = application.id
        record["pissn"] = bj.get_one_identifier(bj.P_ISSN)
        record["eissn"] = bj.get_one_identifier(bj.E_ISSN)

        record["author_retains_copyright"] = bj.author_copyright.get("copyright") == "True"

        lic = bj.get_license()
        if lic is not None:
            record["publishing_license"] = [lic.get("type")]
            record["license_embedded"] = lic.get("embedded", False)

        record["pids"] = bj.persistent_identifier_scheme

        record["preservation"] = bj.flattened_archiving_policies

        if bj.apc_url is not None or bj.submission_charges_url is not None:
            record["pricing_info"] = True
        else:
            record["pricing_info"] = False

        wiaver_url = bj.get_single_url("waiver_policy")
        record["waiver"] = wiaver_url is not None

        return record
