from portality.models import JournalLikeBibJSON

class JCTInProgressXWalk(object):

    @classmethod
    def application2jct(cls, application):
        bj = application.bibjson()
        assert isinstance(bj, JournalLikeBibJSON)

        record = {}
        record["doaj_id"] = application.id
        record["pissn"] = bj.pissn
        record["eissn"] = bj.eissn
        record["author_retains_copyright"] = bj.author_retains_copyright
        record["publishing_license"] = [x.get("type") for x in bj.licenses]
        record["pids"] = bj.pid_scheme
        record["preservation"] = bj.flattened_archiving_policies
        record["license_embedded"] = "Embed" in bj.article_license_display
        record["pricing_info"] = bj.has_apc or bj.has_other_charges
        record["waiver"] = bj.has_waiver

        return record