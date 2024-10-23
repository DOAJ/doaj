from portality import models


def create_editor_group_en():
    eg = models.EditorGroup()
    eg.set_name("English")
    eg.set_id('egid')
    return eg


def create_editor_group_cn():
    eg = models.EditorGroup()
    eg.set_name("Chinese")
    eg.set_id('egid2')
    return eg


def create_editor_group_jp():
    eg = models.EditorGroup()
    eg.set_name("Japanese")
    eg.set_id('egid3')
    return eg

