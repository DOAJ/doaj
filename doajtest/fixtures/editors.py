from copy import deepcopy


class EditorGroupFixtureFactory(object):
    @staticmethod
    def make_editor_group_source():
        return deepcopy(EDITOR_GROUP_SOURCE)

EDITOR_GROUP_SOURCE = {
    "name" : "Test Editor Group",
    "associates" : ["associate", "associate_2", "associate_3"],
    "editor" : "eddie"
}
