from copy import deepcopy

from formulaic.core import Field, FieldCapability, Structure, OPTIONAL, SINGLE, REQUIRED, REPEATABLE, ErrorCode
from formulaic.serialise.form.controls import Hidden, Textarea, TextInput
from formulaic.serialise.form.core import CompoundFieldCapability, FormCapability, FormObject, FormFieldCapability, \
    FormSerialiser, FormDataParser, GenericFormStructureCapability
from portality.forms.workflow.core import GenericField, GenericControl, GenericROFieldRenderer, \
    GenericROControlRenderer, GenericCompound
from portality.models import Application


########################################
## stand alone notes

##############
## Component fields

class NoteID(Field):
    class C(FormFieldCapability):
        label = "Note ID"
        control_class = Hidden
        render_class = GenericField
        control_render_class = GenericControl

    name = "note_id"
    capabilities = (C(),)

class NoteText(Field):
    class C(FormFieldCapability):
        label = None    # No need to label the control
        control_class = Textarea
        render_class = GenericField
        control_render_class = GenericControl

    name = "note_text"
    capabilities = (C(),)

class NoteCreated(Field):
    class C(FormFieldCapability):
        label = "Created"
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "note_created"
    capabilities = (C(),)

class NoteLastUpdated(Field):
    class C(FormFieldCapability):
        label = "Last Updated"
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "note_last_updated"
    capabilities = (C(),)

class NoteAuthor(Field):
    class C(FormFieldCapability):
        label = "Author"
        control_class = TextInput
        render_class = GenericROFieldRenderer
        control_render_class = GenericROControlRenderer

    name = "note_author"
    capabilities = (C(),)

#################
## Compound note

class Note(Structure):
    class C(CompoundFieldCapability):
        label = "Note"
        repeatable_label = "Notes"
        order = [
            "note_id",
            "note_text",
            "note_created",
            "note_last_updated",
            "note_author"
        ]
        render_class = GenericCompound
        list_render_class = None # will use the default

    name_ = "note"
    capabilities_ = (C(),)

    note_id = NoteID(OPTIONAL, SINGLE)
    note_text = NoteText(REQUIRED, SINGLE)
    note_created = NoteCreated(OPTIONAL, SINGLE)
    note_last_updated = NoteLastUpdated(OPTIONAL, SINGLE)
    note_author = NoteAuthor(OPTIONAL, SINGLE)

###################
## Form

class NotesForm(Structure):
    class C(FormCapability):
        label = "Notes"
        order = [
            "notes"
        ]
        render_class = None # will use the default

    name_ = "notes"
    capabilities_ = (C(),)

    notes = Note(OPTIONAL, REPEATABLE)

class StandAloneNotes(FormObject):
    struct = NotesForm()

class StandAloneNotesProcessor:
    def __init__(self, source_application: Application, raw_formdata: dict = None):
        self._source_application = source_application
        self._raw_formdata = raw_formdata

        from portality.forms.workflow.crosswalk import Application2Notes
        self.form2obj_xwalk = None # TODO
        self.obj2form_xwalk = Application2Notes()
        self.serialiser = FormSerialiser()
        self.parser = FormDataParser()

        self._form_inst: StandAloneNotes = None
        self._target_application: Application = None

        if self._raw_formdata is not None:
            self.rawform2forminstance()

        elif self._source_application:
            self.source2forminstance()

        else:
            self.blank_form()

    ################################
    ## accessors

    @property
    def source_application(self):
        return self._source_application

    @property
    def target_application(self):
        return self._target_application

    @property
    def form_instance(self):
        return self._form_inst

    @form_instance.setter
    def form_instance(self, inst):
        self._form_inst = inst

    ################################
    ## Data transformations

    def rawform2forminstance(self):
        if self._raw_formdata is None:
            raise ValueError("No raw form data to process")

        data = self.parser.representation_to_data(self._raw_formdata, StandAloneNotes.struct)
        self.form_instance = StandAloneNotes(data)

    def source2forminstance(self):
        if not self._source_application:
            raise ValueError("Must provide both source application and workflow control")

        self.form_instance = self.obj2form_xwalk.transform(self._source_application)

    def forminstance2target(self, account):
        partial_application = self.form2obj_xwalk.transform(self._form_inst, account)
        self._target_application = self._patch_application(partial_application)

    def blank_form(self):
        self.form_instance = StandAloneNotes()

    ################################
    ## Form submission methods

    def pre_validate(self):
        pass

    def validate(self):
        if self.form_instance is None:
            raise ValueError("No form instance to validate")

        self.pre_validate()
        return self.form_instance.validate()

    def finalise(self, account):
        self.forminstance2target(account)
        self._target_application.save()

    ################################
    ## Internal processing methods

    def _patch_application(self, partial_application: Application) -> Application:
        target = Application(**deepcopy(self._source_application.data))
        tbj = target.bibjson()
        sbj = partial_application.bibjson()

        # this patcher assumes all the metadata have been provided by the partial.
        # If it's possible a partial won't have that info, then we need to update this to
        # accommodate

        # EISSN/PISSN
        tbj.eissn = sbj.eissn
        tbj.pissn = sbj.pissn

        # Title
        tbj.title = sbj.title

        # Continuation
        tbj.replaces = sbj.replaces

        # License information
        tbj.remove_licenses()
        for lic in sbj.licenses:
            tbj.add_license_obj(lic)
        tbj.license_terms_url = sbj.license_terms_url

        # Copyright
        tbj.author_retains_copyright = sbj.author_retains_copyright
        tbj.copyright_url = sbj.copyright_url

        return target

    ##########################
    ## Form serialisation

    def render_form(self):
        form_html = self.serialiser.data_to_string(
            self.form_instance.data,
            self.form_instance.struct,
            application=self._source_application,
            errors=self.form_instance.validation_result
        )
        return form_html

    def validation_report(self):
        def code2msg(error_code: ErrorCode, field):
            # field = error_code.error.field
            if isinstance(field, Structure):
                field = field.ref_

            cap = None
            if field.has_capability(GenericFormStructureCapability):
                cap = field.get_capability(GenericFormStructureCapability)
            elif field.has_capability(FormFieldCapability):
                cap = field.get_capability(FormFieldCapability)

            msg = cap.error_message(error_code)
            return msg

        # get the raw validation dict
        d = self.form_instance.validation_result.as_dict(code2msg)

        # enhance it for form usage
        if "errors" not in d:
            return d

        for e in d["errors"]:
            e["field_id"] = self.serialiser.make_id(self.form_instance.struct, e["path"], e["data_context"])
            if "relevant_to" in e:
                for r in e["relevant_to"]:
                    r["field_id"] = self.serialiser.make_id(self.form_instance.struct, r["path"])

        # now let's flatten it to make it simpler for the front end
        f = []
        for e in d["errors"]:
            if "msg" in e["code"] and e["code"]["msg"] != "":
                f.append({
                    "field_id": e["field_id"],
                    "code": e["code"]
                })

            for rt in e.get("relevant_to", []):
                if "msg" in rt["code"] and rt["code"]["msg"] != "":
                    f.append({
                        "field_id": rt["field_id"],
                        "code": rt["code"]
                    })

        m = {
            "valid": d["valid"],
            "errors": f,
            "full_error_trace": d["errors"]
        }

        return m