from doajtest.helpers import DoajTestCase
from portality.models import Journal, Note


class TestModels(DoajTestCase):
    def test_01_add_notes_and_save(self):
        j = Journal()
        j.add_note("Note 1")
        j.add_note("Note 2", date="2001-01-01T00:00:00Z")
        j.add_note("Note 3", date="2002-01-01T00:00:00Z", id="1234567890")
        j.add_note("Note 4", date="2003-01-01T00:00:00Z", id="2345678901", author_id="test")
        j.add_note_by_dict({
            "note": "Note 5",
            "date": "2004-01-01T00:00:00Z",
            "id": "3456789012",
            "author_id": "test"
        })

        notes = j.notes
        note_asserts = [False, False, False, False, False]
        for note in notes:
            if note.get("note") == "Note 1":
                note_asserts[0] = True
            elif note.get("note") == "Note 2":
                assert note.get("date") == "2001-01-01T00:00:00Z"
                note_asserts[1] = True
            elif note.get("note") == "Note 3":
                assert note.get("date") == "2002-01-01T00:00:00Z"
                assert note.get("id") == "1234567890"
                note_asserts[2] = True
            elif note.get("note") == "Note 4":
                assert note.get("date") == "2003-01-01T00:00:00Z"
                assert note.get("id") == "2345678901"
                assert note.get("author_id") == "test"
                note_asserts[3] = True
            elif note.get("note") == "Note 5":
                assert note.get("date") == "2004-01-01T00:00:00Z"
                assert note.get("id") == "3456789012"
                assert note.get("author_id") == "test"
                note_asserts[4] = True

        assert all(note_asserts)

        # no blocking on save, we want to see this all work synchronously
        j.save()

        j2 = Journal.pull(j.id)
        notes = j2.notes

        note_asserts = [False, False, False, False, False]
        for note in notes:
            if note.get("note") == "Note 1":
                note_asserts[0] = True
            elif note.get("note") == "Note 2":
                assert note.get("date") == "2001-01-01T00:00:00Z"
                note_asserts[1] = True
            elif note.get("note") == "Note 3":
                assert note.get("date") == "2002-01-01T00:00:00Z"
                assert note.get("id") == "1234567890"
                note_asserts[2] = True
            elif note.get("note") == "Note 4":
                assert note.get("date") == "2003-01-01T00:00:00Z"
                assert note.get("id") == "2345678901"
                assert note.get("author_id") == "test"
                note_asserts[3] = True
            elif note.get("note") == "Note 5":
                assert note.get("date") == "2004-01-01T00:00:00Z"
                assert note.get("id") == "3456789012"
                assert note.get("author_id") == "test"
                note_asserts[4] = True

        assert all(note_asserts)

    def test_02_add_and_remove(self):
        j = Journal()
        n1 = j.add_note("Note 1")
        n2 = j.add_note("Note 2", date="2001-01-01T00:00:00Z")
        n3 = j.add_note("Note 3", date="2002-01-01T00:00:00Z", id="1234567890")
        n4 = j.add_note("Note 4", date="2003-01-01T00:00:00Z", id="2345678901", author_id="test")

        j.save()

        j.remove_note(n2)
        j.remove_note_by_id("2345678901")   # Note 4

        note_asserts = [False, False]
        notes = j.notes
        assert len(notes) == 2
        for note in notes:
            if note.get("note") == "Note 1":
                note_asserts[0] = True
            elif note.get("note") == "Note 3":
                note_asserts[1] = True

        assert all(note_asserts)

        j.save()

        j2 = Journal.pull(j.id)
        notes = j2.notes
        note_asserts = [False, False]

        assert len(notes) == 2
        for note in notes:
            if note.get("note") == "Note 1":
                note_asserts[0] = True
            elif note.get("note") == "Note 3":
                note_asserts[1] = True

        assert all(note_asserts)


    def test_03_setting_retrieving(self):
        j = Journal()
        n1 = j.add_note("Note 1")
        n2 = j.add_note("Note 2", date="2001-01-01T00:00:00Z")
        n3 = j.add_note("Note 3", date="2002-01-01T00:00:00Z", id="1234567890")
        n4 = j.add_note("Note 4", date="2003-01-01T00:00:00Z", id="2345678901", author_id="test")

        n2_2 = j.get_note_by_id(n2.id)
        assert n2_2.get("date") == "2001-01-01T00:00:00Z"
        assert n2_2.get("note") == "Note 2"

        j.remove_notes()
        assert len(j.notes) == 0

        j.set_notes([n1, n3])
        assert len(j.notes) == 2

        note_asserts = [False, False]
        for note in j.notes:
            if note.get("note") == "Note 1":
                note_asserts[0] = True
            elif note.get("note") == "Note 3":
                note_asserts[1] = True
        assert all(note_asserts)

        for n in j.note_objects:
            assert isinstance(n, Note)

        n4 = j.add_note("Note 4", date="2003-01-01T00:00:00Z")

        nids = j.note_ids
        assert len(nids) == 3
        for nid in nids:
            assert j.get_note_by_id(nid) is not None

        ordered = j.ordered_notes
        assert ordered[0].get("id") == n1.id
        assert ordered[1].get("id") == n4.id
        assert ordered[2].get("id") == n3.id

    def test_04_flags_individual(self):
        j = Journal()
        assert not j.is_flagged
        n1 = j.add_note("Note 1")
        f1 = j.add_note("Flag", author_id="test", assigned_to="test2", deadline="2027-01-01T00:00:00Z")

        assert j.is_flagged
        assert j.flag_note_id == f1.id
        assert j.flag_assignee == "test2"
        assert len(j.flags) == 1
        assert len(j.notes_except_flags) == 1
        assert len(j.notes) == 2

        j.remove_note(f1)

        assert not j.is_flagged
        assert len(j.flags) == 0
        assert len(j.notes_except_flags) == 1
        assert len(j.notes) == 1

        f2 = j.add_note("Flag 2", author_id="test", assigned_to="test3", deadline="2027-01-01T00:00:00Z")
        j.remove_note(n1)

        assert j.is_flagged
        assert len(j.flags) == 1
        assert len(j.notes_except_flags) == 0
        assert len(j.notes) == 1

        f2_2 = j.flags[0]
        assert f2_2.get("flag", {}).get("assigned_to") == "test3"
        assert f2_2.get("flag", {}).get("deadline") == "2027-01-01"

        f2_3 = j.get_note_by_id(f2.id)
        assert f2_3.get("flag", {}).get("assigned_to") == "test3"
        assert f2_3.get("flag", {}).get("deadline") == "2027-01-01"

    def test_05_flags_grouped(self):
        j = Journal()
        j.set_notes([
            {"note": "Note 1"},
            {"note": "Flag 1", "flag": {"assigned_to": "test"}},
        ])

        assert j.is_flagged
        assert j.flag_assignee == "test"
        assert len(j.flags) == 1
        assert len(j.notes_except_flags) == 1
        assert len(j.notes) == 2

        note_asserts = [False, False]
        for note in j.notes:
            if note.get("note") == "Note 1":
                assert note.get("flag") is None
                note_asserts[0] = True
            elif note.get("note") == "Flag 1":
                assert note.get("flag") is not None
                assert note["flag"]["assigned_to"] == "test"
                note_asserts[1] = True
        assert all(note_asserts)

        assert len(j.note_objects) == 2
        assert len(j.note_ids) == 2

        for note in j.notes_except_flags:
            assert note.get("note") == "Note 1"
            assert note.get("flag") is None

        for flag in j.flags:
            assert flag.get("note") == "Flag 1"
            assert flag["flag"].get("assigned_to") == "test"

        j.remove_notes()
        assert not j.is_flagged
        assert j.flag_assignee is None
        assert len(j.flags) == 0
        assert len(j.notes_except_flags) == 0
        assert len(j.notes) == 0
        assert len(j.note_objects) == 0

    def test_06_flags_notes_manipulation(self):
        j = Journal()
        n1 = j.add_note("Note 1")
        assert len(j.notes_except_flags) == 1

        j.set_flag(n1.id, "test", "2027-01-01T00:00:00Z")

        assert j.is_flagged
        assert j.flag_assignee == "test"
        assert j.flag_note_id == n1.id
        assert j.flag_deadline == "2027-01-01"
        assert len(j.flags) == 1
        assert len(j.notes_except_flags) == 0

        j.delete_flag()

        assert not j.is_flagged
        assert len(j.flags) == 0
        assert len(j.notes_except_flags) == 1

        j.set_flag(n1.id, "test", "2027-01-01T00:00:00Z")
        n2 = j.resolve_flag(n1.id, "Resolved")

        assert not j.is_flagged
        assert len(j.flags) == 0
        assert len(j.notes_except_flags) == 1
        assert j.notes_except_flags[0].get("note") == "Resolved"

        j.set_flag(n2.id, "test2", "2027-01-01T00:00:00Z")
        assert j.is_flagged

        j.delete_flag_and_note()
        assert not j.is_flagged
        assert len(j.flags) == 0
        assert len(j.notes_except_flags) == 0

    def test_07_detach_notes(self):
        j = Journal()
        n1 = j.add_note("Note 1")
        n2 = j.add_note("Flag 1", assigned_to="test", deadline="2027-01-01T00:00:00Z")

        detached = j.get_detached_notes()
        assert len(detached) == 2

        note_asserts = [False, False]
        for d in detached:
            assert "id" not in d
            if d.get("note") == "Note 1":
                assert d.get("flag") is None
                note_asserts[0] = True
            elif d.get("note") == "Flag 1":
                assert d.get("flag") is None
                note_asserts[1] = True
        assert all(note_asserts)





