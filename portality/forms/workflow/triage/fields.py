from formulaic.coerce.coerce import Boolean
from formulaic.core import Field
from formulaic.serialise.form.controls import Radio
from portality.forms.workflow.core import WorkflowFormFieldCapability


class EthicsNotExcluded(Field):
    class EthicsNotExcludedCapability(WorkflowFormFieldCapability):
        label = "Current exclusions"

        options = [
            {"value": "y",
             "label": "Compliant, this application is from a journal or publisher that is not currently excluded."},
            {"value": "n",
             "label": "Non-compliant, this application is from a journal or publisher that is currently excluded."}
        ]

        control_class = Radio

        check = """
            This application is from a journal or publisher that is not 
            currently excluded. (Note:  if an exclusion does not relate 
            to all journals from a publisher, an application for another 
            journal from that publisher should not be rejected at this 
            stage.)
        """

        instructions = """
            If the exclusion does not relate to all journals from a publisher, an application for another journal from that publisher should not be rejected at this stage. Specifically:
            - If there is a current publisher exclusion, the answer is ""No""
            - if there is a current journal exclusion for the journal we triage, the answer is ""No""
            - if there is a current journal exclusion for a different journal than the one we triage from the same publisher, the answer is ""Yes""
        """

    name = "ethics_not_excluded",
    coerce = [Boolean()]
    capabilities = (EthicsNotExcludedCapability,)