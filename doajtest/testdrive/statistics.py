from doajtest.testdrive.factory import TestDrive
from portality import constants
from portality import models
from doajtest.fixtures import EditorGroupFixtureFactory
import string
import random

class Statistics(TestDrive):
    """
    Creates a group structure for statistics testdrive:
    3 groups, each with the same Man Ed, 2 groups with the same editor, each with different number of AssEds
    """

    NUMBER_OF_GROUPS = 3
    NUMBER_OF_EDITORS = 2
    NUMBER_OF_ASSEDITORS = 8

    FINISHED_APPLICATIONS = [
        {'role': 'editor', 'group': 0, 'index': 0, 'count': 2},
        {'role': 'editor', 'group': 1, 'index': 0, 'count': 3},
        {'role': 'editor', 'group': 2, 'index': 1, 'count': 3},
        {'role': 'assed', 'group': 0, 'index': 0, 'count': 0},
        {'role': 'assed', 'group': 0, 'index': 1, 'count': 4},
        {'role': 'assed', 'group': 1,  'index': 2, 'count': 0},
        {'role': 'assed', 'group': 1, 'index': 3, 'count': 5},
        {'role': 'assed', 'group': 1, 'index': 4, 'count': 3},
        {'role': 'assed', 'group': 2, 'index': 5, 'count': 7},
        {'role': 'assed', 'group': 2, 'index': 6, 'count': 4},
        {'role': 'assed', 'group': 2, 'index': 7, 'count': 2},
    ]

    # Define editor groups and associate editors' associations
    EDITOR_GROUPS = {
        'eg0': {'editor_index': 0, 'start_assed_index': 0, 'end_assed_index': 2},
        'eg1': {'editor_index': 0, 'start_assed_index': 2, 'end_assed_index': 5},
        'eg2': {'editor_index': 1, 'start_assed_index': 5, 'end_assed_index': 8},
    }

    def setup(self) -> dict:
        self.createAccounts()
        self.createGroups()
        self.createProvenanceData()
        return {
            "admin": {
                "username": self.admin,
                "password": self.admin_pass
            },
            "editor_1": {
                "username": self.editors[0]["id"],
                "password": self.editors[0]["pass"]
            },
            "editor_2": {
                "username": self.editors[1]["id"],
                "password": self.editors[1]["pass"]
            },
            "associate_editor_1": {
                "username": self.asseds[0]["id"],
                "password": self.asseds[0]["pass"]
            },
            "associate_editor_2": {
                "username": self.asseds[1]["id"],
                "password": self.asseds[1]["pass"]
            },
            "finished_applications": self.finished_by_user,
            "non_renderable": {
                "asseds": [assed['id'] for assed in
                           self.asseds[2:]],
                "groups": self.groups,
                "provenance": self.provenance_data
            }
        }

    def create_random_str(self, n_char=10):
        s = string.ascii_letters + string.digits
        return ''.join(random.choices(s, k=n_char))

    def createAccounts(self):
        un = self.create_random_str()
        pw1 = self.create_random_str()
        admin = models.Account.make_account(un + "@example.com", un, "Admin " + un, [constants.ROLE_ADMIN])
        admin.set_password(pw1)
        admin.save()
        self.admin = admin.id
        self.admin_pass = pw1

        # Create editors accounts
        self.editors = []
        for i in range(self.NUMBER_OF_EDITORS):
            us = self.create_random_str()
            pw = self.create_random_str()
            editor = models.Account.make_account(us + "@example.com", us, "Editor" + str(i+1) + " " + us,
                                                 [constants.ROLE_EDITOR])
            editor.set_password(pw)
            editor.save()
            self.editors.append({"id": editor.id, "pass": pw})

        # Create associate editors accounts
        self.asseds = []
        for i in range(self.NUMBER_OF_ASSEDITORS):
            us = self.create_random_str()
            pw = self.create_random_str()
            assed = models.Account.make_account(us + "@example.com", us, "AssEd" + str(i+1) + " " + us,
                                                [constants.ROLE_ASSOCIATE_EDITOR])
            assed.set_password(pw)
            assed.save()
            self.asseds.append({"id": assed.id, "pass": pw})

    def createGroups(self):

        self.groups = []
        for group_key, group_info in self.EDITOR_GROUPS.items():
            eg_source = EditorGroupFixtureFactory.make_editor_group_source(group_name=group_key, maned=self.admin,
                                                                           editor=
                                                                           self.editors[group_info['editor_index']][
                                                                               "id"])
            del eg_source["associates"]  # these will be added in a moment
            editor_group = models.EditorGroup(**eg_source)
            editor_group.set_id(group_key)
            ids_to_set = [assed['id'] for assed in
                          self.asseds[group_info['start_assed_index']:group_info['end_assed_index']]]
            editor_group.set_associates(ids_to_set)
            editor_group.save()
            self.groups.append(editor_group.id)

    def createProvenanceData(self):

        self.finished_by_user = {}
        self.provenance_data = []
        role_mapping = {
            "editor": {
                "array": self.editors,
                "status": constants.APPLICATION_STATUS_READY
            },
            "assed": {
                "array": self.asseds,
                "status": constants.APPLICATION_STATUS_COMPLETED
            }
        }

        for entry in self.FINISHED_APPLICATIONS:
            role = entry["role"]
            idx = entry['index']
            count = entry['count']
            group_key = "eg" + str(entry['group'])

            users = role_mapping[role]["array"]
            app_status = role_mapping[role]["status"]

            status = "status:" + app_status
            user_id = users[idx]["id"]
            user_name_with_eg = user_id + " (" + role + " in " + group_key + ")"

            self.finished_by_user[user_name_with_eg] = str(count)

            for i in range(count):
                p = self.add_provenance_record(status, role, user_id, group_key)
                self.provenance_data.append(p.id)

    def add_provenance_record(self, status, role, user, editor_group):
        data = {
            "user": user,
            "roles": [role],
            "type": "suggestion",
            "action": status,
            "editor_group": [editor_group]
        }
        p = models.Provenance(**data)
        p.save()
        print(p.id)
        return p

    def teardown(self, params):
        for key, obj in params.items():
            print(key)
            if key != "non_renderable" and key != "finished_applications":
                models.Account.remove_by_id(obj["username"])

        non_renderable = params.get("non_renderable", {})

        for assed in non_renderable.get("asseds", []):
            models.Account.remove_by_id(assed)

        for provenance_id in non_renderable.get("provenance", []):
            models.Provenance.remove_by_id(provenance_id)

        for group in non_renderable.get("groups", []):
            models.Provenance.remove_by_id(group)

        return {"success": True}


if __name__ == "__main__":
    structure = Statistics()
    params = structure.setup()
    print(structure.admin)
    print(structure.editors)
    print(structure.asseds)
    print(structure.groups)
    print(structure.provenance_data)
    structure.teardown(params)
