from portality import models, lcc
from portality.datasets import licenses

class JournalGenericXWalk(object):
    @classmethod
    def is_new_editor_group(cls, form, old):
        old_eg = old.editor_group
        new_eg = form.editor_group.data
        return old_eg != new_eg and new_eg is not None and new_eg != ""

    @classmethod
    def is_new_editor(cls, form, old):
        old_ed = old.editor
        new_ed = form.editor.data
        return old_ed != new_ed and new_ed is not None and new_ed != ""

    @classmethod
    def form2bibjson(cls, form, bibjson):
        if form.alternative_title.data:
            bibjson.alternative_title = form.alternative_title.data

        for apc_record in form.apc_charges.data:
            if not apc_record["apc_currency"] and not apc_record["apc_max"]:
                continue
            bibjson.add_apc(apc_record["apc_currency"], apc_record["apc_max"])

        if form.apc_url.data:
            bibjson.apc_url = form.apc_url.data

        if form.preservation_service.data:
            pres_services = [e for e in form.preservation_service.data if e not in ["national_library", "none", "other"]]
            if "other" in form.preservation_service.data and form.preservation_service_other.data:
                pres_services.append(form.preservation_service_other.data)
            bibjson.set_preservation(pres_services, None)
            if "national_library" in form.preservation_service.data and form.preservation_service_library.data:
                bibjson.add_preservation_library(form.preservation_service_library.data)
            if "none" in form.preservation_service.data:
                bibjson.has_preservation = False

        if form.preservation_service_url.data:
            bibjson.preservation_url = form.preservation_service_url.data

        if form.copyright_author_retains.data:
            bibjson.author_retains_copyright = form.copyright_author_retains.data

        if form.copyright_url.data:
            bibjson.copyright_url = form.copyright_url.data

        if "publisher_name" in form.publisher.data and form.publisher.data["publisher_name"]:
            bibjson.publisher_name = form.publisher.data["publisher_name"]
        if "publisher_country" in form.publisher.data and form.publisher.data["publisher_country"]:
            bibjson.publisher_country = form.publisher.data["publisher_country"]

        if form.deposit_policy.data:
            dep_services = [e for e in form.deposit_policy.data if e not in ["Unregistered", "none", "other"]]
            if "other" in form.deposit_policy.data and form.deposit_policy_other.data:
                dep_services.append(form.deposit_policy_other.data)
            if dep_services:
                bibjson.deposit_policy = dep_services
            if "Unregistered" in form.deposit_policy.data:
                bibjson.deposit_policy_registered = False
            elif len(dep_services) > 0:
                bibjson.deposit_policy_registered = True

        if form.review_process.data or form.review_url.data:
            processes = [e for e in form.review_process.data if e not in ["other"]]
            if "other" in form.review_process.data and form.review_process_other.data:
                processes.append(form.review_process_other.data)
            bibjson.set_editorial_review(processes, form.review_url.data, form.editorial_board_url.data)

        if form.pissn.data:
            bibjson.pissn = form.pissn.data

        if form.eissn.data:
            bibjson.eissn = form.eissn.data

        if "institution_name" in form.institution.data and form.institution.data["institution_name"]:
            bibjson.institution_name = form.institution.data["institution_name"]
        if "institution_country" in form.institution.data and form.institution.data["institution_country"]:
            bibjson.institution_country = form.institution.data["institution_country"]

        if form.keywords.data:
            bibjson.keywords = form.keywords.data

        if form.language.data:
            bibjson.language = form.language.data  # select multiple field - gives a list back

        lurl = form.license_terms_url.data
        if lurl:
            bibjson.license_terms_url = lurl
        if form.license.data:
            for ltype in form.license.data:
                by, nc, nd, sa = None, None, None, None
                if ltype in licenses:
                    by = licenses[ltype]['BY']
                    nc = licenses[ltype]['NC']
                    nd = licenses[ltype]['ND']
                    sa = licenses[ltype]['SA']
                    lurl = licenses[type]["url"]
                elif form.license_attributes.data:
                    by = True if 'BY' in form.license_attributes.data else False
                    nc = True if 'NC' in form.license_attributes.data else False
                    nd = True if 'ND' in form.license_attributes.data else False
                    sa = True if 'SA' in form.license_attributes.data else False
                bibjson.add_license(ltype, url=lurl, by=by, nc=nc, nd=nd, sa=sa)

        if form.license_display.data:
            bibjson.article_license_display = form.license_display.data

        if form.license_display_example_url.data:
            bibjson.article_license_display_example_url = form.license_display_example_url.data

        if form.boai.data:
            bibjson.boai = form.boai.data

        if form.oa_statement_url.data:
            bibjson.oa_statement_url = form.oa_statement_url.data

        if form.journal_url.data:
            bibjson.journal_url = form.journal_url.data

        if form.aims_scope_url.data:
            bibjson.aims_scope_url = form.aims_scope_url.data

        if form.author_instructions_url.data:
            bibjson.author_instructions_url = form.author_instructions_url.data

        if form.waiver_url.data:
            bibjson.waiver_url = form.waiver_url.data

        if form.persistent_identifiers.data:
            schemes = [e for e in form.persistent_identifiers.data if e not in ["none", "other"]]
            if "other" in form.persistent_identifiers.data and form.persistent_identifiers_other.data:
                schemes.append(form.persistent_identifiers_other.data)
            if len(schemes) > 0:
                bibjson.pid_scheme = schemes

        if form.plagiarism_detection.data:
            has_detection = form.plagiarism_detection.data == "y"
            bibjson.set_plagiarism_detection(form.plagiarism_url.data, has_detection)

        if form.publication_time_weeks.data:
            bibjson.publication_time_weeks = form.publication_time_weeks.data

        if form.other_charges_url.data:
            bibjson.other_charges_url = form.other_charges_url.data

        if form.title.data:
            bibjson.title = form.title.data

        if form.apc.data:
            has_apc = form.apc.data == "y"
            bibjson.has_apc = has_apc

        if form.has_other_charges.data:
            has_other = form.has_other_charges.data == "y"
            bibjson.has_other_charges = has_other

        if form.has_waiver.data:
            has_waiver = form.has_waiver.data == "y"
            bibjson.has_waiver = has_waiver

        if form.orcid_ids.data:
            orcids = form.orcid_ids.data == "y"
            bibjson.article_orcid = orcids

        if form.open_citations.data:
            oc = form.open_citations.data == "y"
            bibjson.article_i4oc_open_citations = oc

        if form.deposit_policy_url.data:
            bibjson.deposit_policy_url = form.deposit_policy_url.data

    @classmethod
    def bibjson2form(cls, bibjson, forminfo):
        from portality.models import JournalLikeBibJSON
        from portality.forms.application_forms import ApplicationFormFactory
        assert isinstance(bibjson, JournalLikeBibJSON)

        forminfo['alternative_title'] = bibjson.alternative_title

        forminfo["apc_charges"] = []
        for apc_record in bibjson.apc:
            forminfo["apc_charges"].append({
                "apc_currency" : apc_record.get("currency"),
                "apc_max" : apc_record.get("price")
            })

        forminfo["apc_url"] = bibjson.apc_url

        pres_choices = [x for x, y in ApplicationFormFactory.choices_for("preservation_service")]
        if bibjson.preservation_services is not None:
            forminfo["preservation_service"] = [x for x in bibjson.preservation_services if x in pres_choices]
            forminfo["preservation_service_other"] = " ".join([x for x in bibjson.preservation_services if x not in pres_choices])
            if len(forminfo["preservation_service_other"]) > 0:
                forminfo["preservation_service"].append("other")
        if "preservation_service" not in forminfo:
            forminfo["preservation_service"] = []
        if bibjson.preservation_library:
            forminfo["preservation_service_library"] = bibjson.preservation_library
            forminfo["preservation_service"].append("national_library")
        if bibjson.has_preservation is False and len(forminfo["preservation_service"]) == 0:
            forminfo["preservation_service"].append("none")

        forminfo["preservation_service_url"] = bibjson.preservation_url
        if bibjson.author_retains_copyright is not None:
            forminfo["copyright_author_retains"] = "y" if bibjson.author_retains_copyright else "n"
        forminfo["copyright_url"] = bibjson.copyright_url

        forminfo["publisher"] = {}
        forminfo["publisher"]["publisher_name"] = bibjson.publisher_name
        forminfo["publisher"]["publisher_country"] = bibjson.publisher_country

        dep_choices = [x for x, y in ApplicationFormFactory.choices_for("deposit_policy")]
        if bibjson.deposit_policy:
            forminfo["deposit_policy"] = [x for x in bibjson.deposit_policy if x in dep_choices]
            forminfo["deposit_policy_other"] = " ".join([x for x in bibjson.deposit_policy if x not in dep_choices])
            if len(forminfo["deposit_policy_other"]) > 0:
                forminfo["deposit_policy"].append("other")
        if "deposit_policy" not in forminfo:
            forminfo["deposit_policy"] = []
        if bibjson.deposit_policy_registered is False and len(forminfo["deposit_policy"]) == 0:
            forminfo["deposit_policy"].append("Unregistered")

        review_choices = [x for x, y in ApplicationFormFactory.choices_for("review_process")]
        if bibjson.editorial_review_process:
            forminfo["review_process"] = [x for x in bibjson.editorial_review_process if x in review_choices]
            forminfo["review_process_other"] = " ".join([x for x in bibjson.editorial_review_process if x not in review_choices])
            if len(forminfo["review_process_other"]) > 0:
                forminfo["review_process"].append("other")

        forminfo["review_url"] = bibjson.editorial_review_url
        forminfo["pissn"] = bibjson.pissn
        forminfo["eissn"] = bibjson.eissn

        forminfo["institution"] = {}
        forminfo["institution"]["institution_name"] = bibjson.institution_name
        forminfo["institution"]["institution_country"] = bibjson.institution_country

        forminfo['keywords'] = bibjson.keywords
        forminfo['language'] = bibjson.language

        license_attributes = []
        ltypes = []
        for l in bibjson.licenses:
            ltypes.append(l.get("type"))
            if l.get("type") == "Publisher's own license":
                if l.get("BY"): license_attributes.append("BY")
                if l.get("SA"): license_attributes.append("SA")
                if l.get("NC"): license_attributes.append("NC")
                if l.get("ND"): license_attributes.append("ND")
        forminfo["license_attributes"] = license_attributes
        forminfo["license"] = ltypes

        forminfo["license_display"] = bibjson.article_license_display
        forminfo["license_display_example_url"] = bibjson.article_license_display_example_url
        forminfo["boai"] = bibjson.boai
        forminfo["license_terms_url"] = bibjson.license_terms_url
        forminfo["oa_statement_url"] = bibjson.oa_statement_url
        forminfo["journal_url"] = bibjson.journal_url
        forminfo["aims_scope_url"] = bibjson.aims_scope_url
        forminfo["editorial_board_url"] = bibjson.editorial_board_url
        forminfo["author_instructions_url"] = bibjson.author_instructions_url
        forminfo["waiver_url"] = bibjson.waiver_url

        pid_choices = [x for x, y in ApplicationFormFactory.choices_for("persistent_identifiers")]
        if bibjson.pid_scheme:
            forminfo["persistent_identifiers"] = [x for x in bibjson.pid_scheme if x in pid_choices]
            forminfo["persistent_identifiers_other"] = " ".join([x for x in bibjson.pid_scheme if x not in pid_choices])
            if len(forminfo["persistent_identifiers_other"]) > 0:
                forminfo["persistent_identifiers"].append("other")

        if bibjson.plagiarism_detection is not None:
            forminfo["plagiarism_detection"] = "y" if bibjson.plagiarism_detection else "n"
        forminfo["plagiarism_url"] = bibjson.plagiarism_url
        forminfo["publication_time_weeks"] = bibjson.publication_time_weeks
        forminfo["other_charges_url"] = bibjson.other_charges_url
        forminfo['title'] = bibjson.title

        # FIXME: these translations don't handle partial records (i.e. drafts)
        # we may want to add some methods to allow the settedness of these fields to be checked
        if bibjson.has_apc is not None:
            forminfo["apc"] = "y" if bibjson.has_apc else "n"
        if bibjson.has_other_charges is not None:
            forminfo["has_other_charges"] = "y" if bibjson.has_other_charges else "n"
        if bibjson.has_waiver is not None:
            forminfo["has_waiver"] = "y" if bibjson.has_waiver else "n"
        if bibjson.article_orcid is not None:
            forminfo["orcid_ids"] = "y" if bibjson.article_orcid else "n"
        if bibjson.article_i4oc_open_citations is not None:
            forminfo["open_citations"] = "y" if bibjson.article_i4oc_open_citations else "n"

        forminfo["deposit_policy_url"] = bibjson.deposit_policy_url


class JournalFormXWalk(JournalGenericXWalk):

    @classmethod
    def form2obj(cls, form):
        journal = models.Journal()
        bibjson = journal.bibjson()

        # first do the generic crosswalk to bibjson
        cls.form2bibjson(form, bibjson)

        ################################################

        # admin fields we haven't thought about yet

        """
        for formnote in form.notes.data:
            if formnote["note"]:
                journal.add_note(formnote["note"])

        new_subjects = []
        for code in form.subject.data:
            sobj = {"scheme": 'LCC', "term": lcc.lookup_code(code), "code": code}
            new_subjects.append(sobj)
        bibjson.set_subjects(new_subjects)

        if getattr(form, 'owner', None):
            owner = form.owner.data
            if owner:
                owner = owner.strip()
                journal.set_owner(owner)

        if getattr(form, 'editor_group', None):
            editor_group = form.editor_group.data
            if editor_group:
                editor_group = editor_group.strip()
                journal.set_editor_group(editor_group)

        if getattr(form, "editor", None):
            editor = form.editor.data
            if editor:
                editor = editor.strip()
                journal.set_editor(editor)

        if getattr(form, "doaj_seal", None):
            journal.set_seal(form.doaj_seal.data)

        # continuations information
        if getattr(form, "replaces", None):
            bibjson.replaces = form.replaces.data
        if getattr(form, "is_replaced_by", None):
            bibjson.is_replaced_by = form.is_replaced_by.data
        if getattr(form, "discontinued_date", None):
            bibjson.discontinued_date = form.discontinued_date.data
        """

        return journal


    @classmethod
    def obj2form(cls, obj):
        forminfo = {}
        bibjson = obj.bibjson()

        cls.bibjson2form(bibjson, forminfo)

        """
        forminfo['contact_name'] = listpop(obj.contacts(), {}).get('name')
        forminfo['contact_email'] = listpop(obj.contacts(), {}).get('email')
        forminfo['confirm_contact_email'] = forminfo['contact_email']
        forminfo["replaces"] = bibjson.replaces
        forminfo["is_replaced_by"] = bibjson.is_replaced_by
        forminfo["discontinued_date"] = bibjson.discontinued_date

        forminfo['notes'] = obj.ordered_notes

        forminfo['subject'] = []
        for s in bibjson.subjects():
            if "code" in s:
                forminfo['subject'].append(s['code'])

        forminfo['owner'] = obj.owner
        if obj.editor_group is not None:
            forminfo['editor_group'] = obj.editor_group
        if obj.editor is not None:
            forminfo['editor'] = obj.editor

        forminfo['doaj_seal'] = obj.has_seal()
        """

        return forminfo