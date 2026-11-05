
from doajtest.helpers import DoajTestCase
from doajtest.unit.bll_workflow.helper_triage_workflow import run_test 

class TestTriageWorkflow(DoajTestCase):
    
    def test_001(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "1"
})
        
    def test_002(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "2"
})
        
    def test_003(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "3"
})
        
    def test_004(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "4"
})
        
    def test_005(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "5"
})
        
    def test_006(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "6"
})
        
    def test_007(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "7"
})
        
    def test_008(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "8"
})
        
    def test_009(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "9"
})
        
    def test_010(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "10"
})
        
    def test_011(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "11"
})
        
    def test_012(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "12"
})
        
    def test_013(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "13"
})
        
    def test_014(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "14"
})
        
    def test_015(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "15"
})
        
    def test_016(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "16"
})
        
    def test_017(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "17"
})
        
    def test_018(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "18"
})
        
    def test_019(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "19"
})
        
    def test_020(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "20"
})
        
    def test_021(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "21"
})
        
    def test_022(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "22"
})
        
    def test_023(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "23"
})
        
    def test_024(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "24"
})
        
    def test_025(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "25"
})
        
    def test_026(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "26"
})
        
    def test_027(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "27"
})
        
    def test_028(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "28"
})
        
    def test_029(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "29"
})
        
    def test_030(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "30"
})
        
    def test_031(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "31"
})
        
    def test_032(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "32"
})
        
    def test_033(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "33"
})
        
    def test_034(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "34"
})
        
    def test_035(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "35"
})
        
    def test_036(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "36"
})
        
    def test_037(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "37"
})
        
    def test_038(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "38"
})
        
    def test_039(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "39"
})
        
    def test_040(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "40"
})
        
    def test_041(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "41"
})
        
    def test_042(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "42"
})
        
    def test_043(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "43"
})
        
    def test_044(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "44"
})
        
    def test_045(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "45"
})
        
    def test_046(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "46"
})
        
    def test_047(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "47"
})
        
    def test_048(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "48"
})
        
    def test_049(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "49"
})
        
    def test_050(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "50"
})
        
    def test_051(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "51"
})
        
    def test_052(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "52"
})
        
    def test_053(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "53"
})
        
    def test_054(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "54"
})
        
    def test_055(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "55"
})
        
    def test_056(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "56"
})
        
    def test_057(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "57"
})
        
    def test_058(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "58"
})
        
    def test_059(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_minimal_review",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "59"
})
        
    def test_060(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_minimal_review",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "60"
})
        
    def test_061(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_minimal_review",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "61"
})
        
    def test_062(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_minimal_review",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "62"
})
        
    def test_063(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_minimal_review",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "63"
})
        
    def test_064(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_minimal_review",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "64"
})
        
    def test_065(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_minimal_review",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "65"
})
        
    def test_066(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_minimal_review",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "66"
})
        
    def test_067(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "rejected",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "no",
  "test_id": "67"
})
        
    def test_068(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "rejected",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "no",
  "test_id": "68"
})
        
    def test_069(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "69"
})
        
    def test_070(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "70"
})
        
    def test_071(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "71"
})
        
    def test_072(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "72"
})
        
    def test_073(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "73"
})
        
    def test_074(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "74"
})
        
    def test_075(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "75"
})
        
    def test_076(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "76"
})
        
    def test_077(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "77"
})
        
    def test_078(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "78"
})
        
    def test_079(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "79"
})
        
    def test_080(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "80"
})
        
    def test_081(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "81"
})
        
    def test_082(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "82"
})
        
    def test_083(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "83"
})
        
    def test_084(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "84"
})
        
    def test_085(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "85"
})
        
    def test_086(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "86"
})
        
    def test_087(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "87"
})
        
    def test_088(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "88"
})
        
    def test_089(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "89"
})
        
    def test_090(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "90"
})
        
    def test_091(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "91"
})
        
    def test_092(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "92"
})
        
    def test_093(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "93"
})
        
    def test_094(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "94"
})
        
    def test_095(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "95"
})
        
    def test_096(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "96"
})
        
    def test_097(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "97"
})
        
    def test_098(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "98"
})
        
    def test_099(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "99"
})
        
    def test_100(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "100"
})
        
    def test_101(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "101"
})
        
    def test_102(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "102"
})
        
    def test_103(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "103"
})
        
    def test_104(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "104"
})
        
    def test_105(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "105"
})
        
    def test_106(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "106"
})
        
    def test_107(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "107"
})
        
    def test_108(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "108"
})
        
    def test_109(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "109"
})
        
    def test_110(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "110"
})
        
    def test_111(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "111"
})
        
    def test_112(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "112"
})
        
    def test_113(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "113"
})
        
    def test_114(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "114"
})
        
    def test_115(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_minimal_review",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "115"
})
        
    def test_116(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_minimal_review",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "116"
})
        
    def test_117(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_minimal_review",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "117"
})
        
    def test_118(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_minimal_review",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "118"
})
        
    def test_119(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_minimal_review",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "119"
})
        
    def test_120(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_minimal_review",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "120"
})
        
    def test_121(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_minimal_review",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "121"
})
        
    def test_122(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_minimal_review",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "122"
})
        
    def test_123(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "123"
})
        
    def test_124(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "124"
})
        
    def test_125(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "125"
})
        
    def test_126(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "126"
})
        
    def test_127(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "127"
})
        
    def test_128(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "128"
})
        
    def test_129(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "129"
})
        
    def test_130(self):
        run_test({
  "module": "triage",
  "stage": "in_progress",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.2",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "130"
})
        
    def test_131(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "131"
})
        
    def test_132(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "132"
})
        
    def test_133(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "133"
})
        
    def test_134(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "134"
})
        
    def test_135(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "135"
})
        
    def test_136(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_claim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "136"
})
        
    def test_137(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "137"
})
        
    def test_138(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "138"
})
        
    def test_139(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "139"
})
        
    def test_140(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "140"
})
        
    def test_141(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "141"
})
        
    def test_142(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "pending",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "142"
})
        
    def test_143(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "143"
})
        
    def test_144(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "144"
})
        
    def test_145(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "145"
})
        
    def test_146(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "146"
})
        
    def test_147(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "147"
})
        
    def test_148(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "none",
  "action": "event_assign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.1",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "pending",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "148"
})
        
    def test_149(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "149"
})
        
    def test_150(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "150"
})
        
    def test_151(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "151"
})
        
    def test_152(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "152"
})
        
    def test_153(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "153"
})
        
    def test_154(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "154"
})
        
    def test_155(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "155"
})
        
    def test_156(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "action_edit",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "156"
})
        
    def test_157(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "157"
})
        
    def test_158(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "158"
})
        
    def test_159(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "159"
})
        
    def test_160(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "160"
})
        
    def test_161(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "161"
})
        
    def test_162(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "162"
})
        
    def test_163(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "163"
})
        
    def test_164(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unclaim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "164"
})
        
    def test_165(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "165"
})
        
    def test_166(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "166"
})
        
    def test_167(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "167"
})
        
    def test_168(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "168"
})
        
    def test_169(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "169"
})
        
    def test_170(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "170"
})
        
    def test_171(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "171"
})
        
    def test_172(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_unassign",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "172"
})
        
    def test_173(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "173"
})
        
    def test_174(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "174"
})
        
    def test_175(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "175"
})
        
    def test_176(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "176"
})
        
    def test_177(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "177"
})
        
    def test_178(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "178"
})
        
    def test_179(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "179"
})
        
    def test_180(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "180"
})
        
    def test_181(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "181"
})
        
    def test_182(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "182"
})
        
    def test_183(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "183"
})
        
    def test_184(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "184"
})
        
    def test_185(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "185"
})
        
    def test_186(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "186"
})
        
    def test_187(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "187"
})
        
    def test_188(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "188"
})
        
    def test_189(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "rejected",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "no",
  "test_id": "189"
})
        
    def test_190(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "rejected",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "no",
  "test_id": "190"
})
        
    def test_191(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "191"
})
        
    def test_192(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "192"
})
        
    def test_193(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "193"
})
        
    def test_194(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "194"
})
        
    def test_195(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "195"
})
        
    def test_196(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_fail",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "196"
})
        
    def test_197(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_rescind_minimal_review",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "197"
})
        
    def test_198(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_rescind_minimal_review",
  "actor": "assigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "198"
})
        
    def test_199(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_rescind_minimal_review",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "199"
})
        
    def test_200(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_rescind_minimal_review",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "200"
})
        
    def test_201(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_rescind_minimal_review",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "201"
})
        
    def test_202(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_rescind_minimal_review",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "202"
})
        
    def test_203(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_rescind_minimal_review",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "203"
})
        
    def test_204(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_rescind_minimal_review",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "204"
})
        
    def test_205(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_triaged",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "quick_fail",
  "state_id": "1.3",
  "result_module": "quick_fail",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "no",
  "test_id": "205"
})
        
    def test_206(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_triaged",
  "actor": "assigned_triage",
  "has_minimal_review": "yes",
  "label": "quality_review",
  "state_id": "1.3",
  "result_module": "quality_review",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "no",
  "test_id": "206"
})
        
    def test_207(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_triaged",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "quick_fail",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "207"
})
        
    def test_208(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_triaged",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "quality_review",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "208"
})
        
    def test_209(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_triaged",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "quick_fail",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "209"
})
        
    def test_210(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_triaged",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "quality_review",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "210"
})
        
    def test_211(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_triaged",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "quick_fail",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "211"
})
        
    def test_212(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "triage",
  "action": "event_triaged",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "quality_review",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "212"
})
        
    def test_213(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "213"
})
        
    def test_214(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "214"
})
        
    def test_215(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "215"
})
        
    def test_216(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "216"
})
        
    def test_217(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "217"
})
        
    def test_218(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "218"
})
        
    def test_219(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "219"
})
        
    def test_220(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "action_edit",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "220"
})
        
    def test_221(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "221"
})
        
    def test_222(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "222"
})
        
    def test_223(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "223"
})
        
    def test_224(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "224"
})
        
    def test_225(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "225"
})
        
    def test_226(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "226"
})
        
    def test_227(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "227"
})
        
    def test_228(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unclaim",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "228"
})
        
    def test_229(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "229"
})
        
    def test_230(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "230"
})
        
    def test_231(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "231"
})
        
    def test_232(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "232"
})
        
    def test_233(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "233"
})
        
    def test_234(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "234"
})
        
    def test_235(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "235"
})
        
    def test_236(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_unassign",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "pending",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "236"
})
        
    def test_237(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "237"
})
        
    def test_238(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "238"
})
        
    def test_239(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "minimal_review",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "239"
})
        
    def test_240(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "240"
})
        
    def test_241(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "241"
})
        
    def test_242(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "242"
})
        
    def test_243(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "243"
})
        
    def test_244(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "assigned",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "244"
})
        
    def test_245(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "245"
})
        
    def test_246(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "246"
})
        
    def test_247(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "247"
})
        
    def test_248(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "248"
})
        
    def test_249(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "249"
})
        
    def test_250(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "250"
})
        
    def test_251(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "251"
})
        
    def test_252(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_reassign_non_triage",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "252"
})
        
    def test_253(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "253"
})
        
    def test_254(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "254"
})
        
    def test_255(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "255"
})
        
    def test_256(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "256"
})
        
    def test_257(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "257"
})
        
    def test_258(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "258"
})
        
    def test_259(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "259"
})
        
    def test_260(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_fail",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "rejected",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "260"
})
        
    def test_261(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_rescind_minimal_review",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "261"
})
        
    def test_262(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_rescind_minimal_review",
  "actor": "assigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "262"
})
        
    def test_263(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_rescind_minimal_review",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "263"
})
        
    def test_264(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_rescind_minimal_review",
  "actor": "admin",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "in_progress",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "no",
  "test_id": "264"
})
        
    def test_265(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_rescind_minimal_review",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "265"
})
        
    def test_266(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_rescind_minimal_review",
  "actor": "unassigned_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "266"
})
        
    def test_267(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_rescind_minimal_review",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "267"
})
        
    def test_268(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_rescind_minimal_review",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "no",
  "label": "none",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "Triage",
  "error": "AuthoriseException",
  "test_id": "268"
})
        
    def test_269(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_triaged",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "quick_fail",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "269"
})
        
    def test_270(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_triaged",
  "actor": "assigned_non_triage",
  "has_minimal_review": "yes",
  "label": "quality_review",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "270"
})
        
    def test_271(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_triaged",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "quick_fail",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "271"
})
        
    def test_272(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_triaged",
  "actor": "admin",
  "has_minimal_review": "yes",
  "label": "quality_review",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "272"
})
        
    def test_273(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_triaged",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "quick_fail",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "273"
})
        
    def test_274(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_triaged",
  "actor": "unassigned_triage",
  "has_minimal_review": "yes",
  "label": "quality_review",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "274"
})
        
    def test_275(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_triaged",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "quick_fail",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "275"
})
        
    def test_276(self):
        run_test({
  "module": "triage",
  "stage": "minimal_review",
  "reviewer": "non_triage",
  "action": "event_triaged",
  "actor": "unassigned_non_triage",
  "has_minimal_review": "yes",
  "label": "quality_review",
  "state_id": "1.3",
  "result_module": "triage",
  "result_stage": "",
  "result_reviewer": "none",
  "initial_legacy_status": "in progress",
  "result_legacy_status": "in progress",
  "initial_legacy_eg": "Triage",
  "result_legacy_eg": "none",
  "error": "AuthoriseException",
  "test_id": "276"
})
        