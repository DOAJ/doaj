from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.testdrive.factory import TestDrive
from portality import models, constants
from portality.bll import DOAJ
from portality.lib import dates


class Workflow(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "Admin " + un,[constants.ROLE_ADMIN])
        acc.set_password(pw)
        acc.generate_api_key()
        acc.save()

        svc = DOAJ.workflowService()
        states = []
        for i in range(5):
            source = ApplicationFixtureFactory.make_application_source()
            app = models.Application(**source)
            app.set_id(app.makeid())
            app.bibjson().title = "Workflow Test " + str(i)
            app.set_created(dates.before_now(86400*i))
            state = svc.initialise_workflow(acc, app)
            state.workflow_control.set_created(app.created_date)
            state.workflow_control.triage.ethics_not_excluded.compliant = True
            state.saveall()
            states.append(state)

        report = {

        }
        for state in states:
            t = str(type(state))
            if t not in report:
                report[t] = []
            report[t].append({
                "application" : state.application.id,
                "workflow_control": state.workflow_control.id
            })

        return {
            "account": {
                "username": acc.id,
                "password": pw,
                "api_key": acc.api_key
            },
            "states": report
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for state, components in params["states"].items():
            for component in components:
                models.Application.remove_by_id(component["application"])
                models.WorkflowControl.remove_by_id(component["workflow_control"])

        return {"status": "success"}