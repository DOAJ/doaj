from wtforms.fields.core import UnboundField

class FormHelper(object):

    def render_field(self, field, **kwargs):
        # begin the frag
        frag = ""

        # deal with the first error if it is relevant
        first_error = kwargs.pop("first_error", False)
        if first_error:
            frag += '<a name="first_problem"></a>'

        # call the correct render function on the field type
        if field.type == "FormField":
            frag += self._form_field(field, **kwargs)
        elif field.type == "FieldList":
            frag += self._field_list(field, **kwargs)
        else:
            frag += self._wrap_control_group(field, self._render_field(field, **kwargs), **kwargs)

        return frag

    def _wrap_control_group(self, field, contents, **kwargs):
        hidden = kwargs.pop("hidden", False)
        container_class = kwargs.pop("container_class", None)
        disabled = kwargs.pop("disabled", False)
        render_subfields_horizontal = kwargs.pop("render_subfields_horizontal", False)
        complete_me = kwargs.get("complete_me", False)

        frag = '<div class="control-group'
        if field.errors:
            frag += " error"
        if render_subfields_horizontal:
            frag += " row"
        if container_class is not None:
            frag += " " + container_class
        #if complete_me and (field.flags.required or field.flags.display_required_star) and (field.data is None or field.data == "" or field.data == "None") and not disabled:
        if complete_me:
            #if not field.validate():
            frag += " complete-me"
        frag += '" id="'
        frag += field.short_name + '-container"'
        if hidden:
            frag += ' style="display:none;"'
        frag += ">"
        if contents is not None:
            frag += contents
        frag += "</div>"

        return frag

    def _form_field(self, field, **kwargs):
        # get the useful kwargs
        render_subfields_horizontal = kwargs.pop("render_subfields_horizontal", False)

        frag = ""
        # for each subfield, do the render
        for subfield in field:
            if render_subfields_horizontal and not (subfield.type == 'CSRFTokenField' and not subfield.value):
                subfield_width = "3"
                remove = []
                for kwarg, val in kwargs.iteritems():
                    if kwarg == 'subfield_display-' + subfield.short_name:
                        subfield_width = val
                        remove.append(kwarg)
                for rm in remove:
                    del kwargs[rm]
                frag += '<div class="span' + subfield_width + ' nested-field-container">'
                frag += self._render_field(subfield, maximise_width=True, **kwargs)
                frag += "</div>"
            else:
                frag += self._render_field(subfield, **kwargs)

        return self._wrap_control_group(field, frag, **kwargs)

    def _field_list(self, field, **kwargs):
        # for each subfield, do the render
        frag = ""
        for subfield in field:
            if subfield.type == "FormField":
                frag += self.render_field(subfield, **kwargs)
            else:
                frag = self._wrap_control_group(field, self._render_field(field, **kwargs), **kwargs)
        return frag

    def _render_field(self, field, **kwargs):
        # interesting arguments from keywords
        extra_input_fields = kwargs.get("extra_input_fields")
        q_num = kwargs.pop("q_num", None)
        maximise_width = kwargs.pop("maximise_width", False)
        clazz = kwargs.get("class", "")

        if field.type == 'CSRFTokenField' and not field.value:
            return ""

        frag = ""

        # If this is the kind of field that requires a label, give it one
        if field.type not in ['SubmitField', 'HiddenField', 'CSRFTokenField']:
            if q_num is not None:
                frag += '<a class="animated" name="' + q_num + '"></a>'
            frag += '<label class="control-label" for="' + field.short_name + '">'
            if q_num is not None:
                frag += '<a class="animated orange" href="#' + field.short_name + '-container" title="Link to this question" tabindex="-1">' + q_num + ')</a>&nbsp;'
            frag += field.label.text
            if field.flags.required or field.flags.display_required_star:
                frag += '&nbsp;<span class="red">*</span>'
            frag += "</label>"

        # determine if this is a checkbox
        is_checkbox = False
        if (field.type == "SelectMultipleField"
                and field.option_widget.__class__.__name__ == 'CheckboxInput'
                and field.widget.__class__.__name__ == 'ListWidget'):
            is_checkbox = True

        extra_class = ""
        if is_checkbox:
            extra_class += " checkboxes"

        frag += '<div class="controls' + extra_class + '">'
        if field.type == "RadioField":
            for subfield in field:
                frag += self._render_radio(subfield, **kwargs)
        elif is_checkbox:
            frag += '<ul id="' + field.short_name + '">'
            for subfield in field:
                frag += self._render_checkbox(subfield, **kwargs)
            frag += "</ul>"
        else:
            if maximise_width:
                clazz += " span11"
                kwargs["class"] = clazz
            frag += field(**kwargs) # FIXME: this is probably going to do some weird stuff

            # FIXME: field.value isn't always set
            #if field.value in extra_input_fields.keys():
            #    extra_input_fields[field.value](**{"class" : "extra_input_field"})

        if field.errors:
            frag += '<ul class="errors">'
            for error in field.errors:
                frag += '<li>' + error + '</li>'
            frag += "</ul>"

        if field.description:
            frag += '<p class="help-block">' + field.description + '</p>'

        frag += "</div>"
        return frag

    def _render_radio(self, field, **kwargs):
        extra_input_fields = kwargs.pop("extra_input_fields", {})

        frag = '<label class="radio" for="' + field.short_name + '">'
        frag += field(**kwargs)
        frag += '<span class="label-text">' + field.label.text + '</span>'

        if field.label.text in extra_input_fields.keys():
            frag += "&nbsp;" + extra_input_fields[field.label.text](**{"class" : "extra_input_field"})

        frag += "</label>"
        return frag


    def _render_checkbox(self, field, **kwargs):
        extra_input_fields = kwargs.pop("extra_input_fields", {})

        frag = "<li>"
        frag += field(**kwargs)
        frag += '<label for="' + field.short_name + '">' + field.label.text + '</label>'

        if field.label.text in extra_input_fields.keys():
            eif = extra_input_fields[field.label.text]
            if not isinstance(eif, UnboundField):
                frag += "&nbsp;" + extra_input_fields[field.label.text](**{"class" : "extra_input_field"})

        frag += "</li>"
        return frag

class FormHelperBS3(object):

    def render_field(self, field, **kwargs):
        # begin the frag
        frag = ""

        # deal with the first error if it is relevant
        first_error = kwargs.pop("first_error", False)
        if first_error:
            frag += '<a name="first_problem"></a>'

        # call the correct render function on the field type
        if field.type == "FormField":
            frag += self._form_field(field, **kwargs)
        elif field.type == "FieldList":
            frag += self._field_list(field, **kwargs)
        else:
            frag += self._wrap_control_group(field, self._render_field(field, **kwargs), **kwargs)

        return frag

    def _wrap_control_group(self, field, contents, **kwargs):
        hidden = kwargs.pop("hidden", False)
        container_class = kwargs.pop("container_class", None)
        disabled = kwargs.pop("disabled", False)
        render_subfields_horizontal = kwargs.pop("render_subfields_horizontal", False)
        complete_me = kwargs.get("complete_me", False)

        frag = '<div class="from-group'
        if field.errors:
            frag += " error"
        if render_subfields_horizontal:
            frag += " row"
        if container_class is not None:
            frag += " " + container_class
        #if complete_me and (field.flags.required or field.flags.display_required_star) and (field.data is None or field.data == "" or field.data == "None") and not disabled:
        if complete_me:
            #if not field.validate():
            frag += " complete-me"
        frag += '" id="'
        frag += field.short_name + '-container"'
        if hidden:
            frag += ' style="display:none;"'
        frag += ">"
        if contents is not None:
            frag += contents
        frag += "</div>"

        return frag

    def _form_field(self, field, **kwargs):
        # get the useful kwargs
        render_subfields_horizontal = kwargs.pop("render_subfields_horizontal", False)

        frag = ""
        # for each subfield, do the render
        for subfield in field:
            if render_subfields_horizontal and not (subfield.type == 'CSRFTokenField' and not subfield.value):
                subfield_width = "3"
                remove = []
                for kwarg, val in kwargs.iteritems():
                    if kwarg == 'subfield_display-' + subfield.short_name:
                        subfield_width = val
                        remove.append(kwarg)
                for rm in remove:
                    del kwargs[rm]
                frag += '<div class="col-xs-' + subfield_width + ' nested-field-container">'
                frag += self._render_field(subfield, maximise_width=True, **kwargs)
                frag += "</div>"
            else:
                frag += self._render_field(subfield, **kwargs)

        return self._wrap_control_group(field, frag, **kwargs)

    def _field_list(self, field, **kwargs):
        # for each subfield, do the render
        frag = ""
        for subfield in field:
            if subfield.type == "FormField":
                frag += self.render_field(subfield, **kwargs)
            else:
                frag = self._wrap_control_group(field, self._render_field(field, **kwargs), **kwargs)
        return frag

    def _render_field(self, field, **kwargs):
        # interesting arguments from keywords
        extra_input_fields = kwargs.get("extra_input_fields")
        q_num = kwargs.pop("q_num", None)
        maximise_width = kwargs.pop("maximise_width", False)
        clazz = kwargs.get("class", "")

        if field.type == 'CSRFTokenField' and not field.value:
            return ""

        frag = ""

        # If this is the kind of field that requires a label, give it one
        if field.type not in ['SubmitField', 'HiddenField', 'CSRFTokenField']:
            if q_num is not None:
                frag += '<a class="animated" name="' + q_num + '"></a>'
            frag += '<label for="' + field.short_name + '">'
            if q_num is not None:
                frag += '<a class="animated orange" href="#' + field.short_name + '-container" title="Link to this question" tabindex="-1">' + q_num + ')</a>&nbsp;'
            frag += field.label.text
            if field.flags.required or field.flags.display_required_star:
                frag += '&nbsp;<span class="red">*</span>'
            frag += "</label>"

        # determine if this is a checkbox
        is_checkbox = False
        if (field.type == "SelectMultipleField"
                and field.option_widget.__class__.__name__ == 'CheckboxInput'
                and field.widget.__class__.__name__ == 'ListWidget'):
            is_checkbox = True

        extra_class = ""
        if is_checkbox:
            extra_class += " checkboxes"

        frag += '<div class="controls' + extra_class + '">'
        if field.type == "RadioField":
            for subfield in field:
                frag += self._render_radio(subfield, **kwargs)
        elif is_checkbox:
            frag += '<ul id="' + field.short_name + '">'
            for subfield in field:
                frag += self._render_checkbox(subfield, **kwargs)
            frag += "</ul>"
        else:
            if maximise_width:
                clazz += " col-xs-11"
                kwargs["class"] = clazz
            frag += field(**kwargs) # FIXME: this is probably going to do some weird stuff

            # FIXME: field.value isn't always set
            #if field.value in extra_input_fields.keys():
            #    extra_input_fields[field.value](**{"class" : "extra_input_field"})

        if field.errors:
            frag += '<ul class="errors">'
            for error in field.errors:
                frag += '<li>' + error + '</li>'
            frag += "</ul>"

        if field.description:
            frag += '<p class="help-block">' + field.description + '</p>'

        frag += "</div>"
        return frag

    def _render_radio(self, field, **kwargs):
        extra_input_fields = kwargs.pop("extra_input_fields", {})

        frag = '<label class="radio" for="' + field.short_name + '">'
        frag += field(**kwargs)
        frag += '<span class="label-text">' + field.label.text + '</span>'

        if field.label.text in extra_input_fields.keys():
            frag += "&nbsp;" + extra_input_fields[field.label.text](**{"class" : "extra_input_field"})

        frag += "</label>"
        return frag


    def _render_checkbox(self, field, **kwargs):
        extra_input_fields = kwargs.pop("extra_input_fields", {})

        frag = "<li>"
        frag += field(**kwargs)
        frag += '<label for="' + field.short_name + '">' + field.label.text + '</label>'

        if field.label.text in extra_input_fields.keys():
            eif = extra_input_fields[field.label.text]
            if not isinstance(eif, UnboundField):
                frag += "&nbsp;" + extra_input_fields[field.label.text](**{"class" : "extra_input_field"})

        frag += "</li>"
        return frag