"""Dynamics controls and stored-basis integration rejection boundaries."""
import json
from pathlib import Path
import tempfile
import unittest
from PyQt6 import QtWidgets
from analysis_editor import AnalysisDialog,validate_definition
from dynamics_workflow_fixtures import CASES,fixture
from viewport import decode

class DynamicsAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    def reject(self,case,change):
        data,spec=fixture(case);change(spec)
        with self.assertRaises(ValueError):validate_definition(data,spec)
    def test_all_examples_editor_and_original_validation(self):
        with tempfile.TemporaryDirectory() as name:
            for case in CASES:
                with self.subTest(case=case):
                    data,spec=fixture(case);path=Path(name)/(case+'.inp');path.write_bytes(data);d=AnalysisDialog(None,decode(path),data,spec)
                    self.assertTrue(d.validate_current(),d.message.text());self.assertFalse(d.validation['solverExecuted'])
                    for k,v in spec['step']['dynamics'].items():self.assertEqual(d.definition['step']['dynamics'][k],v)
                    d.close()
    def test_density_required_for_every_dynamic_section(self):
        for case in ('implicit-ramp','modal-ramp'):self.reject(case,lambda s:s['materials'][0].pop('density'))
    def test_alpha_checked_before_original_clamping(self):
        for alpha in (-.334,.01):self.reject('implicit-ramp',lambda s:s['step']['dynamics'].update(alpha=alpha))
    def test_damping_type_and_coefficients_refused(self):
        self.reject('implicit-ramp',lambda s:s['step']['dynamics'].update(damping='Constant'))
        self.reject('implicit-ramp',lambda s:s['step']['dynamics'].update(massDamping=-1))
        self.reject('modal-ramp',lambda s:s['step']['dynamics'].update(modalDampingRatio=1))
    def test_basis_mode_limits_and_distinct_name(self):
        for modes in (0,1001):self.reject('modal-ramp',lambda s:s['step']['dynamics'].update(basisModes=modes))
        self.reject('modal-ramp',lambda s:s['step']['dynamics'].update(basisName=s['step']['name']))
    def test_nonhomogeneous_or_time_variable_basis_supports_refused(self):
        self.reject('modal-ramp',lambda s:s['step']['constraints'][0].update(displacements=[None,'1','0']))
        self.reject('modal-ramp',lambda s:s['step']['constraints'][0].update(amplitude='Ramp'))
    def test_nonlinear_and_temperature_dynamics_are_explicitly_pending(self):
        self.reject('implicit-ramp',lambda s:s['step'].update(nonlinearGeometry=True))
        self.reject('modal-ramp',lambda s:s['step'].update(initialTemperature='20'))

if __name__=='__main__':unittest.main()
