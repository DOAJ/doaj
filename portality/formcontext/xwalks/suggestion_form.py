class SuggestionFormXWalk(object):

    _formFields2objectFields = {
        "instructions_authors_url" : "bibjson.link.url where bibjson.link.type=author_instructions",
        "oa_statement_url" : "bibjson.link.url where bibjson.link.type=oa_statement",
        "aims_scope_url" : "bibjson.link.url where bibjson.link.type=aims_scope",
        "submission_charges_url" : "bibjson.submission_charges_url",
        "editorial_board_url" : "bibjson.link.url where bibjson.link.type=editorial_board",
    }

    @classmethod
    def formField2objectField(cls, field):
        return cls._formFields2objectFields.get(field, field)

    @classmethod
    def form2obj(cls, form):
        raise NotImplementedError("This method is deprecated, use the newer version in portality.crosswalks.application_form")


    @classmethod
    def obj2form(cls, obj):
        raise NotImplementedError(
            "This method is deprecated, use the newer version in portality.crosswalks.application_form")

