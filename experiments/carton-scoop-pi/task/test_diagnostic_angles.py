import json,unittest
from pathlib import Path
from diagnostic_angles import DiagnosticBottomAngles
from angle_tracking import BODIES,evidence_error,PHYSICS_DT

class DiagnosticAngleTests(unittest.TestCase):
    def make(self):return DiagnosticBottomAngles({n:5729.58 for n in BODIES})
    def state(self):
        s=json.loads((Path(__file__).parents[1]/'start/snapshot.json').read_text())
        return {n:s['poses'][n] for n in BODIES},{n:[0.]*6 for n in BODIES}
    def test_restored_fixture_tracks_but_cannot_furnish_task_evidence(self):
        t=self.make();p,v=self.state();self.assertTrue(t.initialize(0,0.,p,v),t.failure)
        for k in range(1,13):self.assertTrue(t.advance(k,k*PHYSICS_DT,p,v))
        self.assertIsNotNone(evidence_error(t.evidence(1,12),t.angles,.05,1))
        self.assertFalse(t.evidence(1,12)['initialized_from_authored_zero'])
    def test_unknown_initial_branch_and_nonzero_velocity_rejected(self):
        t=self.make();p,v=self.state();v['north'][3]=.01
        self.assertFalse(t.initialize(0,0.,p,v))
        t=self.make();p,v=self.state();p['north_bottom'][3:]=[1.,0.,0.,0.]
        self.assertFalse(t.initialize(0,0.,p,v))
    def test_reseeding_after_restored_start_is_sticky_failure(self):
        t=self.make();p,v=self.state();self.assertTrue(t.initialize(0,0.,p,v))
        self.assertFalse(t.initialize(0,0.,p,v))
