from portality import constants
from portality import models


class StatisticsGroupsStructure():
    """
    Creates a group structure for statistics testdrive:
    3 groups, each with the same Man Ed, 2 groups with the same editor, each with different number of AssEds
    """

    NUMBER_OF_GROUPS = 3;
    NUMBER_OF_EDITORS = 2
    NUMBER_OF_ASSEDITORS = 8

    def setup(self):
        self.createAccounts()
        self.createGroups()
        self.createProvenanceData()

    def createAccounts(self):
        un = self.create_random_str()
        pw1 = self.create_random_str()
        self.admin = models.Account.make_account(un + "@example.com", un, "Editor " + un, [constants.ROLE_ADMIN])
        admin.set_password(pw1)
        admin.save()

        self.editors = [];
        for i in range(NUMBER_OF_EDITORS+1):
            us = self.create_random_str()
            pw = self.create_random_str()
            editors[i] = models.Account.make_account(un + "@example.com", un, "Editor" + str(i) + " " + un, [constants.ROLE_EDITOR])
            editors[i].set_password(pw)
            editors[i].save()

        self.asseds = []
        for i in range(NUMBER_OF_ASSEDITORS+1):
            us = self.create_random_str()
            pw = self.create_random_str()
            asseds[i] = models.Account.make_account(un + "@example.com", un, "AssEd" + str(i) + " " + un, [constants.ROLE_ASSOCIATE_EDITOR])
            asseds[i].set_password(pw)
            asseds[i].save()

    def createGroups(self):
        eg_source = EditorGroupFixtureFactory.make_editor_group_source(maned=self.admin.id);
        eg1 = models.EditorGroup(**eg_source)
        eg1.editor = self.editors[0];
        for i in range(2):
            eg.add_associate(self.asseds[i]);
        eg1.save(blocking=True)

        eg_source = EditorGroupFixtureFactory.make_editor_group_source(maned=self.admin.id);
        eg2 = models.EditorGroup(**eg_source)
        eg2.editor = self.editors[0];
        for i in range(2,5):
            eg.add_associate(self.asseds[i]);
        eg2.save(blocking=True)

        eg_source = EditorGroupFixtureFactory.make_editor_group_source(maned=self.admin.id);
        eg3 = models.EditorGroup(**eg_source)
        eg3.editor = self.editors[0];
        for i in range(5,9):
            eg.add_associate(self.asseds[i]);
        eg3.save(blocking=True)

    def createProvenanceData(self):

        self.add_provenance_record("status:" + constants.APPLICATION_STATUS_READY, "editor", editors[0], eg1)
        self.add_provenance_record("status:" + constants.APPLICATION_STATUS_READY, "editor", editors[0], eg1)
        self.add_provenance_record("status:" + constants.APPLICATION_STATUS_COMPLETED, "associate_editor", assed1.id,
                                   eg)
        self.add_provenance_record("status:" + constants.APPLICATION_STATUS_COMPLETED, "associate_editor", assed2.id,
                                   eg)
        self.add_provenance_record("status:" + constants.APPLICATION_STATUS_COMPLETED, "associate_editor", assed3.id,
                                   eg)



