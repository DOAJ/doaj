import datetime
import json
import time
from copy import deepcopy
from typing import List, Union

import jsonpatch

from portality import models
from portality.core import app
from portality.dao import DomainObject


def create_what_by_obj(action: List[str],
                       old_obj: Union[DomainObject, dict],
                       new_obj: DomainObject) -> dict:
    if not isinstance(old_obj, dict) and not isinstance(old_obj, new_obj.__class__):
        app.logger.warngin(f'create_what_by_obj but type mismatch [{type(old_obj)}][{type(new_obj)}]')
        return {}

    old_obj_dict = old_obj if isinstance(old_obj, dict) else old_obj.data
    old_id = old_obj_dict.get('id')

    if old_id != new_obj.id:
        app.logger.warning(f'create_what_by_obj but id mismatch [{old_id}][{new_obj.id}]')

    diff_list = jsonpatch.make_patch(old_obj_dict, new_obj.data).patch
    for _diff in diff_list:
        if 'value' in _diff and isinstance(_diff['value'], dict):
            # avoid type problem of elasticsearch
            try:
                _diff['value'] = json.dumps(_diff['value'])
            except Exception:
                _diff['value'] = str(_diff['value'])

    what_dict = {
        'action': action,
        'id': old_id,
        'es_type': old_obj_dict.get('es_type'),
        'object_type': new_obj.__class__.__name__,
        'diff': diff_list,
    }
    return what_dict


def create_who_obj_by_account(account: dict):
    if account is None or not isinstance(account,  dict):
        who_dict = dict(
            user='unknown',
            roles=['unknown'],
            editor_groups=[],
        )
        return who_dict

    editor_groups = [g.name for g in models.EditorGroup.groups_by_editor(account.get('id'))]
    who_dict = {
        'user': account.get('id', 'unknown'),
        'roles': account.get('role', ['unknown']),
        'editor_groups': editor_groups,
    }
    return who_dict


class AuditBuilder:
    """ Tool for create and save audit record
    """

    def __init__(self, action: Union[List[str], str],
                 target_obj: DomainObject = None,
                 who: dict = None):

        self.target_obj = target_obj
        self.target_obj_data = target_obj and deepcopy(target_obj.data)
        self.action = action if isinstance(action, str) else action
        self.who = who

    def fill_who_by_raw(self,
                        user: str = None,
                        roles: List[str] = None,
                        editor_groups: List[str] = None,
                        ):
        self.who = dict(user=user,
                        roles=roles,
                        editor_groups=editor_groups, )
        return self

    def fill_who_by_account(self, account: "models.Account" = None):
        if account is None:
            try:
                from flask_login import current_user
                account = current_user.data
            except Exception as e:
                print(f'for debug -- get current_user fail in fill_who_by_account  {str(e)}')
                account = None

        self.who = create_who_obj_by_account(account)
        return self

    def save(self, target_obj: DomainObject = None, created_at=None):

        t = time.time()
        if target_obj is None and self.target_obj is None:
            raise ValueError('new_obj and target_obj have not provided')

        if target_obj is None:
            target_obj = self.target_obj

        if self.who is None:
            self.fill_who_by_account()

        # pull old_obj_data if not provided
        if self.target_obj_data is None:
            self.target_obj_data = {}
            if target_obj.id:
                org_obj = target_obj.pull(target_obj.id)
                if org_obj:
                    self.target_obj_data = deepcopy(org_obj.data)

        what = create_what_by_obj(self.action, self.target_obj_data, target_obj)
        created_at = created_at or datetime.datetime.now()

        print(what)

        (models.Audit
         .create(self.who, what, created_at=created_at)
         .save(blocking=False))

        print(f'************ audit save time  --- [{self.action}][{time.time() - t}]')

# TOBEREMOVE
#
# def main():
#     print('aaaaaaa')
#     a = models.Audit(a=11, b=22)
#     a.save(blocking=True)
#     # a = Notification()
#     # a.save(blocking=True)
#     print('bbbbbbbbbbbbb')
#
#     for o in models.Audit.object_query():
#         print(o)
#
#
# def main2():
#     j_list = Journal.object_query()
#     j_list = list(j_list)
#
#     old_obj_dict = deepcopy(j_list[0].data)
#     j_list[0].data['bibjson']['title'] = 'akkakak'
#     j_list[0].data['bibjson']['eissn'] = 'xxxx'
#
#     # print(j_list[0])
#     js = json.dumps(j_list[0].data, indent=4)
#     print(js)
#
#     what = create_what_by_obj(['ccc'],
#                               Journal(**old_obj_dict),
#                               j_list[0])
#     print(what)
#
#
# if __name__ == '__main__':
#     main2()
