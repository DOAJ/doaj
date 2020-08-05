from copy import deepcopy


class AccountFixtureFactory(object):
    @staticmethod
    def make_publisher_source():
        return deepcopy(PUBLISHER_SOURCE)

    @staticmethod
    def make_managing_editor_source():
        return deepcopy(MANED_SOURCE)

    @staticmethod
    def make_editor_source():
        return deepcopy(EDITOR_SOURCE)

    @staticmethod
    def make_assed1_source():
        return deepcopy(ASSED_SOURCE1)

    @staticmethod
    def make_assed2_source():
        return deepcopy(ASSED_SOURCE2)

    @staticmethod
    def make_assed3_source():
        return deepcopy(ASSED_SOURCE3)

PUBLISHER_SOURCE = {
    "email": "pub@example.com",
    "name": "Joe Publisher",
    "role": ['publisher', 'api'],
    "id": "publisher"
}

MANED_SOURCE = {
    "email": "maned@example.com",
    "name": "Managing Editor / Administrator",
    "role": ['admin', 'api'],
    "id": "maned"
}

EDITOR_SOURCE = {
    "email": "eddie@example.com",
    "name": "Eddie",
    "role": ["editor"],
    "id": "eddie"
}

ASSED_SOURCE1 = {
    "email": "associate@example.com",
    "name": "Associate One",
    "role": ["associate_editor"],
    "id": "associate"
}

ASSED_SOURCE2 = {
    "email": "associate_2@example.com",
    "name": "Associate Two",
    "role": ["associate_editor"],
    "id": "associate_2"
}

ASSED_SOURCE3 = {
    "email": "associate_3@example.com",
    "name": "Associate Three",
    "role": ["associate_editor"],
    "id": "associate_3"
}
