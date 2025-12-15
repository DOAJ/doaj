from portality import models


class State:

    def __init__(self, application):
        self._application = application

    @classmethod
    def query(cls):
        return StateQuery("Draft")

    @property
    def application(self):
        return self._application

    def enter(self):
        pass

    def exit(self, event, *args, **kwargs):
        pass


class StateQuery:
    def __init__(self, domain:str, subdomain:str=None, badge:list=None, editor_group:bool=False, editor:bool=False, revisions:bool=False):
        self.domain = domain
        self.subdomain = subdomain
        self.badge = badge or []
        self.editor_group = editor_group
        self.editor = editor
        self.revisions = revisions

    def query(self):
        q = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"workflow.domain.exact": self.domain}}
                    ]
                }
            }
        }
        if self.subdomain:
            q["query"]["bool"]["must"].append({"term": {"admin.workflow.subdomain.exact": self.subdomain}})
        if self.badge:
            q["query"]["bool"]["must"].append({"terms": {"admin.workflow.badges.exact": self.badge}})
        if self.editor_group:
            q["query"]["bool"]["must"].append({"exists": {"field": "admin.editor_group"}})
        if self.editor:
            q["query"]["bool"]["must"].append({"exists": {"field": "admin.editor"}})
        if self.revisions:
            q["query"]["bool"]["must"].append({"exists": {"field": "admin.workflow.revisions"}})


class Draft(State):
    SUBMIT = "submit"

    def exit(self, event, *args, **kwargs):
        if event == self.SUBMIT:
            self._submit_handler()
        else:
            raise ValueError(f"Invalid event '{event}' for Draft state")

    def _submit_handler(self):
        pass

class Submitted(State):
    AUTOCHECKS_COMPLETE = "autochecks_complete"

    def exit(self, event, *args, **kwargs):
        if event == self.AUTOCHECKS_COMPLETE:
            self._autochecks_complete_handler()
        else:
            raise ValueError(f"Invalid event '{event}' for Submitted state")

    def _autochecks_complete_handler(self):
        pass

class QualityTestNoEditor(State):
    CLAIM = "claim"

    def exit(self, event, account=None, *args, **kwargs):
        if event == self.CLAIM:
            self._claim_handler(account)
        else:
            raise ValueError(f"Invalid event '{event}' for QualityTestNoEditor state")

    def _claim_handler(self, account):
        self.application.set_editor(account.id)

class QualityTestWithEditor(State):
    UNCLAIM = "unclaim",
    PASS = "quality_test_pass"
    FAIL = "quality_test_fail"

    def exit(self, event, *args, **kwargs):
        if event == self.UNCLAIM:
            self._unclaim()
        elif event == self.PASS:
            self._quality_test_pass()
        elif event == self.FAIL:
            self._quality_test_fail()
        else:
            raise ValueError(f"Invalid event '{event}' for QualityTestWithEditor state")

    def _remove_badge(self):
        pass

    def _unclaim(self):
        self.application.remove_editor()
        self._remove_badge()

    def _quality_test_pass(self):
        pass

    def _quality_test_fail(self):
        pass


class WorkflowService:
    TRANSITIONS = [
        (Draft, Draft.SUBMIT, Submitted),
        (Submitted, Submitted.AUTOCHECKS_COMPLETE, QualityTestNoEditor),
        (QualityTestNoEditor, QualityTestNoEditor.CLAIM, QualityTestWithEditor),
    ]

    @classmethod
    def list_for_state(cls, state:State.__class__):
        query = state.query()
        for app in models.Application.iterate_unstable(q=query):
            yield state(app)

    @classmethod
    def event(cls, state_instance:State, event:str):
        for (source, evt, target) in cls.TRANSITIONS:
            if isinstance(state_instance, source) and evt == event:
                return cls.transition(state_instance, event, target, validate=False)
        raise ValueError(f"No transition for event '{event}' from state '{type(state_instance).__name__}'")

    @classmethod
    def transition(cls, state_instance:State, event, target_state:State.__class__, validate=True):
        if validate:
            found = False
            for (source, evt, target) in cls.TRANSITIONS:
                if isinstance(state_instance, source) and evt == event and target == target_state:
                    found = True
                    break
            if not found:
                raise ValueError(f"Invalid transition for event '{event}' from state '{type(state_instance).__name__}' to state '{target_state.__name__}'")

        state_instance.exit(event)
        new_state = target_state(state_instance.application)
        new_state.enter()
        return new_state


if __name__ == "__main__":
    drafts = WorkflowService.list_for_state(Draft)
    draft = drafts.__next__()
    new_state = WorkflowService.event(draft, draft.SUBMIT)
