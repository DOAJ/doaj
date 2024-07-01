from portality import constants
from portality import models
from doajtest.fixtures import EditorGroupFixtureFactory
import string
import random


class StatisticsGroupsStructure():
    """
    Creates a group structure for statistics testdrive:
    3 groups, each with the same Man Ed, 2 groups with the same editor, each with different number of AssEds
    """

    NUMBER_OF_GROUPS = 3
    NUMBER_OF_EDITORS = 2
    NUMBER_OF_ASSEDITORS = 8

    FINISHED_APPLICATIONS = {
        'ed0': 2,
        'ed1': 3,
        'assed1': 4,
        'assed2': 1,
        'assed3': 0,
        'assed4': 5,
        'assed5': 3,
        'assed6': 7,
        'assed7': 4,
        'assed8': 2,
    }

    # Define editor groups and associate editors' associations
    EDITOR_GROUPS = {
        'eg0': {'editor_index': 0, 'start_assed_index': 0, 'end_assed_index': 2},
        'eg1': {'editor_index': 0, 'start_assed_index': 2, 'end_assed_index': 5},
        'eg2': {'editor_index': 1, 'start_assed_index': 5, 'end_assed_index': 8},
    }

    def create_random_str(self, n_char=10):
        s = string.ascii_letters + string.digits
        return ''.join(random.choices(s, k=n_char))

    def setup(self):
        self.createAccounts()
        self.createGroups()
        self.createProvenanceData()

    def createAccounts(self):
        un = self.create_random_str()
        pw1 = self.create_random_str()
        admin = models.Account.make_account(un + "@example.com", un, "Editor " + un, [constants.ROLE_ADMIN])
        admin.set_password(pw1)
        admin.save()
        self.admin = admin.id

        # Create editors accounts
        self.editors = []
        for i in range(self.NUMBER_OF_EDITORS):
            us = self.create_random_str()
            pw = self.create_random_str()
            editor = models.Account.make_account(us + "@example.com", us, "Editor" + str(i) + " " + us,
                                                 [constants.ROLE_EDITOR])
            editor.set_password(pw)
            editor.save()
            self.editors.append(editor.id)

        # Create associate editors accounts
        self.asseds = []
        for i in range(1, self.NUMBER_OF_ASSEDITORS + 1):
            us = self.create_random_str()
            pw = self.create_random_str()
            assed = models.Account.make_account(us + "@example.com", us, "AssEd" + str(i) + " " + us,
                                                [constants.ROLE_ASSOCIATE_EDITOR])
            assed.set_password(pw)
            assed.save()
            self.asseds.append(assed.id)

    def createGroups(self):

        self.groups = [];
        for group_key, group_info in self.EDITOR_GROUPS.items():
            eg_source = EditorGroupFixtureFactory.make_editor_group_source(group_name=group_key, maned=self.admin, editor=self.editors[group_info['editor_index']])
            del eg_source["associates"] # these will be added in a moment
            editor_group = models.EditorGroup(**eg_source)
            editor_group.set_associates(self.asseds[group_info['start_assed_index']:group_info['end_assed_index']])
            editor_group.save(blocking=True)
            self.groups.append(editor_group.id)

    def createProvenanceData(self):

        self.provenance_data = [];
        for key, count in self.FINISHED_APPLICATIONS.items():
            if key.startswith('ed'):
                for _ in range(count):
                    for group_key in self.EDITOR_GROUPS:
                        if group_key in key:
                            p = self.add_provenance_record("status:" + constants.APPLICATION_STATUS_READY, "editor",
                                                       self.editors[int(key[-1])], group_key)
                            self.provenance_data.append(p.id)
            elif key.startswith('assed'):
                for _ in range(count):
                    group_key = key.replace('assed', 'eg')
                    user_id = self.asseds[int(key[-1]) - 1]
                    p = self.add_provenance_record("status:" + constants.APPLICATION_STATUS_COMPLETED,
                                               "associate_editor", user_id, group_key)
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
        p.save(blocking=True)
        return p;

    def teardown(self):
        for editor in self.editors:
            models.Account.remove_by_id(editor)
        for assed in self.asseds:
            models.Account.remove_by_id(assed)
        for group in self.groups:
            models.EditorGroup.remove_by_id(group)
        for p in self.provenance_data:
            models.Provenance.remove_by_id(p)

if __name__ == "__main__":
    structure = StatisticsGroupsStructure()
    structure.setup()
    print(structure.admin)
    print(structure.editors)
    print(structure.asseds)
    print(structure.groups)
    print(structure.provenance_data)
    structure.teardown()

