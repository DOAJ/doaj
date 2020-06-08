from copy import deepcopy

from portality.formcontext.choices import Choices


def interpret_list(current_values, allowed_values, substitutions):
    current_values = deepcopy(current_values)
    interpreted_fields = {}

    foreign_values = {}
    for cv in current_values:
        if cv not in allowed_values:
            foreign_values[current_values.index(cv)] = cv
    ps = list(foreign_values.keys())
    ps.sort()

    # FIXME: if the data is broken, just return it as is
    if len(ps) > len(substitutions):
        return current_values

    i = 0
    for k in ps:
        interpreted_fields[substitutions[i].get("field")] = current_values[k]
        current_values[k] = substitutions[i].get("default")
        i += 1

    return current_values, interpreted_fields


def interpret_special(val):
    # if you modify this, make sure to modify reverse_interpret_special as well
    if isinstance(val, str):
        if val.lower() == Choices.TRUE.lower():
            return True
        elif val.lower() == Choices.FALSE.lower():
            return False
        elif val.lower() == Choices.NONE.lower():
            return None
        elif val == Choices.digital_archiving_policy_val("none"):
            return None

    if isinstance(val, list):
        if len(val) == 1:
            actual_val = interpret_special(val[0])
            if not actual_val:
                return []
            return val

        return val

    return val


def reverse_interpret_special(val, field=''):
    # if you modify this, make sure to modify interpret_special as well

    if val is None:
        return Choices.NONE
    elif val is True:
        return Choices.TRUE
    elif val is False:
        return Choices.FALSE
    # no need to handle digital archiving policy or other list
    # fields here - empty lists handled below

    if isinstance(val, list):
        if len(val) == 1:
            reverse_actual_val = reverse_interpret_special(val[0], field=field)
            return [reverse_actual_val]
        elif len(val) == 0:
            # mostly it'll just be a None val
            if field == 'digital_archiving_policy':
                return [Choices.digital_archiving_policy_val("none")]

            return [Choices.NONE]

        return val

    return val


def interpret_other(value, other_field_data, other_value=Choices.OTHER, store_other_label=False):
    '''
    Interpret a value list coming from (e.g.) checkboxes when one of
    them says "Other" and allows free-text input.

    The value can also be a string. In that case, if it matched other_value, other_field_data is returned
    instead of the original value. This is for radio buttons with an "Other" option - you only get 1 value
    from the form, but if it's "Other", you still need to replace it with the relevant free text field data.

    :param value: String or list of values from the form.
        checkboxes_field.data basically.
    :param other_field_data: data from the Other inline extra text input field.
        Usually checkboxes_field_other.data or similar.
    :param other_value: Which checkbox has an extra field? Put its value in here. It's "Other" by default.
        More technically: the value which triggers considering and adding the data in other_field to value.
    '''
    # if you modify this, make sure to modify reverse_interpret_other too
    if isinstance(value, str):
        if value == other_value:
            return other_field_data
    elif isinstance(value, list):
        value = value[:]
        # if "Other" (or some custom value) is in the there, remove it and take the data from the extra text field
        if other_value in value and other_field_data:
            # preserve the order, important for reversing this process when displaying the edit form
            where = value.index(other_value)
            if store_other_label:
                # Needed when multiple items in the list could be freely specified,
                # i.e. unrestricted by the choices for that field.
                # Digital archiving policies is such a field, with both an
                # "Other" choice requiring free text input and a "A national library"
                # choice requiring free text input, presumably with the name
                # of the library.
                value[where] = [other_value, other_field_data]
            else:
                value[where] = other_field_data
    # don't know what else to do, just return it as-is
    return value


def reverse_interpret_other(interpreted_value, possible_original_values, other_value=Choices.OTHER, replace_label=Choices.OTHER):
    '''
    Returns tuple: (main field value or list of values, other field value)
    '''
    # if you modify this, make sure to modify interpret_other too
    other_field_val = ''

    if isinstance(interpreted_value, str):
        # A special case first: where the value is the empty string.
        # In that case, the main field was never submitted (e.g. if it was
        # a choice of "Yes", "No" and "Other", none of those were submitted
        # as an answer - maybe it was an optional field).
        if not interpreted_value:
            return None, None

        # if the stored (a.k.a. interpreted) value is not one of the
        # possible values, then the "Other" option must have been
        # selected during initial submission
        # if so, all we've got to do is swap them
        # so the main field gets a value of "Other" or similar
        # and the secondary (a.k.a. other) field gets the currently
        # stored value - resulting in a form that looks exactly like the
        # one initially submitted
        if interpreted_value not in possible_original_values:
            return other_value, interpreted_value

    elif isinstance(interpreted_value, list):
        # 2 copies of the list needed
        interpreted_value = interpreted_value[:]  # don't modify the original list passed in
        for iv in interpreted_value[:]:  # don't modify the list while iterating over it

            # same deal here, if the original list was ['LOCKSS', 'Other']
            # and the secondary field was 'some other policy'
            # then it would have been interpreted by interpret_other
            # into ['LOCKSS', 'some other policy']
            # so now we need to turn that back into
            # (['LOCKSS', 'Other'], 'some other policy')
            if iv not in possible_original_values:
                where = interpreted_value.index(iv)

                if isinstance(iv, list):
                    # This is a field with two or more choices which require
                    # further specification via free text entry.
                    # If we only recorded the free text values, we wouldn't
                    # be able to tell which one relates to which choice.
                    # E.g. ["some other archiving policy", "Library of Chile"]
                    # does not tell us that "some other archiving policy"
                    # is related to the "Other" field, and "Library of Chile"
                    # is related to the "A national library field.
                    #
                    # [["Other", "some other archiving policy"], ["A national library", "Library of Chile"]]
                    # does tell us that, on the other hand.
                    # It is this case that we are dealing with here.
                    label = iv[0]
                    val = iv[1]
                    if label == replace_label:
                        other_field_val = val
                        interpreted_value[where] = label
                    else:
                        continue
                else:
                    other_field_val = iv
                    interpreted_value[where] = other_value
                    break

    return interpreted_value, other_field_val