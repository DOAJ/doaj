class FormHelper(object):

    def render_field(self, form_context, field_name, **kwargs):
        # pull useful data out of the kwargs and form_context
        first_error = kwargs.get("field_with_first_error")
        disabled = form_context.is_disabled(field_name)
        hidden = kwargs.get("hidden", False)
        render_subfields_horizontal = kwargs.get("render_subfields_horizontal", False)
        container_class = kwargs.get("container_class")

        # get the field itself
        field = form_context.form[field_name]

        # begin the frag
        frag = ""
        if first_error == field.short_name:
            frag += '<a name="first_problem"></a>'

        # call the correct render function on the field type
        if field.type == "FormField":
            frag += self._form_field(field, **kwargs)
        elif field.type == "FieldList":
            frag += self._field_list(field, **kwargs)
        else:
            frag = '<div class="control-group'
            if field.errors:
                frag += " error"
            if container_class is not None:
                frag += container_class
            frag += '" id="'
            frag += field.short_name + '-container"'
            if hidden:
                frag += ' style="display:none;"'
            frag += ">"
            frag += self._render_field(field, **kwargs)
            frag += "</div>"

        return frag

    def _form_field(self, field, **kwargs):
        # get the useful kwargs
        hidden = kwargs.get("hidden", False)
        render_subfields_horizontal = kwargs.get("render_subfields_horizontal", False)
        container_class = kwargs.get("container_class")

        # start the div for this group of fields
        frag = '<div class="control-group'
        if field.errors:
            frag += " error"
        if render_subfields_horizontal:
            frag += " row-fluid"
        if container_class is not None:
            frag += container_class
        frag += '" id="'
        frag += field.short_name + '-container"'
        if hidden:
            frag += ' style="display:none;"'
        frag += ">"

        # for each subfield, do the render
        for subfield in field:
            if render_subfields_horizontal and not (subfield.type == 'CSRFTokenField' and not subfield.value):
                subfield_width = "3"
                for kwarg, val in kwargs.iteritems():
                    if kwarg == 'subfield_display-' + subfield.short_name:
                        subfield_width = val
                frag += '<div class="span' + subfield_width + ' nested-field-container">'
                frag += self._render_field(subfield, maximise_width=True, **kwargs)
                frag += "</div>"
            else:
                frag += self._render_field(subfield, **kwargs)


        # close off the div and return
        frag += "</div>"
        return frag

    def _field_list(self, field, **kwargs):
        # get the useful kwargs
        hidden = kwargs.get("hidden", False)

        # for each subfield, do the render
        for subfield in field:
            if subfield.type == "FormField":
                return self.render_field(subfield, **kwargs)
            else:
                frag = '<div class="control-group'
                if field.errors:
                    frag += " error"
                frag += '" id="'
                frag += field.short_name + '-container"'
                if hidden:
                    frag += ' style="display:none;"'
                frag += ">"

                frag += self._render_field(subfield, **kwargs)

                frag += "</div>"
                return frag

    def _render_field(self, field, **kwargs):
        # interesting arguments from keywords
        extra_input_field = kwargs.get("extra_input_field")
        display_extra_when_label_is = kwargs.get("display_extra_when_label_is", "other")
        extra_input_field2 = kwargs.get("extra_input_field2")
        display_extra2_when_label_is = kwargs.get("display_extra2_when_label_is", "other")
        q_num = kwargs.get("q_num", "")
        maximise_width = kwargs.get("maximise_width", False)
        clazz = kwargs.get("class", "")

        if field.type == 'CSRFTokenField' and not field.value:
            return ""

        frag = ""

        # If this is the kind of field that requires a label, give it one
        if field.type not in ['SubmitField', 'HiddenField', 'CSRFTokenField']:
            if q_num:
                frag += '<a class="animated" name="' + q_num + '"></a>'
            frag += '<label class="control-label" for="' + field.short_name + '">'
            if q_num:
                frag += '<a class="animated orange" href="#' + field.short_name + '-container" title="Link to this question" tabindex="-1">' + q_num + ')</a>'
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

        frag += '<div class="controls ' + extra_class + '">'
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

            # FIXME: exactly 2 allowed?  Plus, how to actually pass in the form elements from the parent render object?
            if extra_input_field and display_extra_when_label_is.lower() == field.value.lower():
                frag += extra_input_field(**{"class" : "extra_input_field"})
            if extra_input_field2  and display_extra2_when_label_is.lower() == field.value.lower():
                frag += extra_input_field2(**{"class" : "extra_input_field"})

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
        """
        {% macro __render_radio(field,
                      extra_input_field='', display_extra_when_label_is='',
                      extra_input_field2='', display_extra2_when_label_is=''
                 )
        %}
        <label class="radio" for="{{field.short_name}}">
            {{ field(**kwargs) }}
            <span class="label-text">{{field.label.text}}</span>

            {% if extra_input_field and display_extra_when_label_is.lower() == field.label.text.lower() %}
              {{ extra_input_field(class="extra_input_field") }}
            {% endif %}

            {% if extra_input_field2 and display_extra2_when_label_is.lower() == field.label.text.lower() %}
              {{ extra_input_field2(class="extra_input_field") }}
            {% endif %}
        </label>
        {% endmacro %}
        """
        frag = '<label class="radio" for="' + field.short_name + '">'
        frag += field(**kwargs)

        # FIXME: deal with extra input fields....

        frag += "</label>"
        return frag


    def _render_checkbox(self, field, **kwargs):
        """
        {% macro __render_checkbox(field,
                      extra_input_field='', display_extra_when_label_is='',
                      extra_input_field2='', display_extra2_when_label_is=''
                 )
        %}
        <li>
            {{ field(**kwargs) }}
            <label for="{{field.short_name}}">{{field.label.text}}</label>

            {% if extra_input_field and display_extra_when_label_is.lower() == field.label.text.lower() %}
              {{ extra_input_field(class="extra_input_field") }}
            {% endif %}

            {% if extra_input_field2 and display_extra2_when_label_is.lower() == field.label.text.lower() %}
              {{ extra_input_field2(class="extra_input_field") }}
            {% endif %}
        </li>
        {% endmacro %}
        """
        frag = "<li>"
        frag += field(**kwargs)
        frag += '<label for="' + field.short_name + '">' + field.label.text + '</label>'

        # FIXME: deal with extra input fields ...

        frag += "</li>"
        return frag

