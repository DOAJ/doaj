from copy import deepcopy

DEFAULT_EDITOR_GROUP_NAME = 'editorgroup'

class EditorGroupFixtureFactory(object):

    @classmethod
    def make_editor_group_source(cls, group_name=DEFAULT_EDITOR_GROUP_NAME, editor="eddie"):
        r = deepcopy(EDITOR_GROUP_SOURCE)
        r['name'] = group_name
        r['editor'] = editor
        return r

    @classmethod
    def setup_editor_group_with_editors(cls, group_name=DEFAULT_EDITOR_GROUP_NAME):
        from portality import models
        from doajtest.fixtures import AccountFixtureFactory

        models.Account(**AccountFixtureFactory.make_editor_source()).save()
        models.Account(**AccountFixtureFactory.make_assed1_source()).save()
        models.Account(**AccountFixtureFactory.make_assed2_source()).save()
        models.Account(**AccountFixtureFactory.make_assed3_source()).save()
        eg = models.EditorGroup(**cls.make_editor_group_source(group_name=group_name, editor="eddie"))
        eg.save(blocking=True)
        return eg

EDITOR_GROUP_SOURCE = {
    "name" : "",
    "associates" : ["associate", "associate_2", "associate_3"],
    "editor" : "eddie"
}
