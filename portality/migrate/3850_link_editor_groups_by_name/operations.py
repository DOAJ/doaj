import warnings
from typing import Union

from portality import constants, models
from portality.models import Application, Journal


def make_update_request(application):
    if application.related_journal and not application.application_type == constants.APPLICATION_TYPE_UPDATE_REQUEST:
        application.application_type = constants.APPLICATION_TYPE_UPDATE_REQUEST
    return application


def name_to_id(model: Union[Application, Journal]):
    eg_id = model.editor_group
    if eg_id is None:
        return model
    new_val = models.EditorGroup.group_exists_by_name(eg_id)
    if not new_val:
        # print(f'editor group not found by name [{eg_id}]')
        return model


    # print(f'editor group [{eg_id}] -> [{new_val}]')
    model.set_editor_group(new_val)
    return model


def id_to_name(model: Union[Application, Journal]):
    warnings.warn("TOBEREMOVE: rollback for debug only")
    eg_id = model.editor_group
    if eg_id is None:
        return model
    eg = models.EditorGroup.pull(eg_id)
    if not eg:
        # print(f'editor group not found by id [{eg_id}]')
        return model

    # print(f'editor group [{eg_id}] -> [{eg.name}]')
    model.set_editor_group(eg.name)
    return model
