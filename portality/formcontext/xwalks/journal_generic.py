class JournalGenericXWalk(object):
    @classmethod
    def is_new_editor_group(cls, form, old):
        old_eg = old.editor_group
        new_eg = form.editor_group.data
        return old_eg != new_eg and new_eg is not None and new_eg != ""

    @classmethod
    def is_new_editor(cls, form, old):
        old_ed = old.editor
        new_ed = form.editor.data
        return old_ed != new_ed and new_ed is not None and new_ed != ""