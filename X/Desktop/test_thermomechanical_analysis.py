"""Original radiation/amplitude/thermal-stress admission and editor integration."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from PyQt6 import QtWidgets
from analysis_editor import AnalysisDialog,validate_definition
from thermomechanical_workflow_fixtures import CASES,fixture
from viewport import decode

class ThermomechanicalAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    def reject(self,case,change):
        data,spec=fixture(case);change(spec)
        with self.assertRaises(ValueError):validate_definition(data,spec)
    def test_all_examples_through_editor_and_original_validation(self):
        with tempfile.TemporaryDirectory() as name:
            for case in CASES:
                with self.subTest(case=case):
                    data,spec=fixture(case);path=Path(name)/(case+'.inp');path.write_bytes(data)
                    d=AnalysisDialog(None,decode(path),data,spec);self.assertTrue(d.validate_current(),d.message.text());self.assertFalse(d.validation['solverExecuted'])
                    for before,after in zip(spec['materials'],d.definition['materials']):self.assertEqual(before,after)
                    if 'amplitudes' in spec:self.assertEqual(d.definition['amplitudes'][0]['points'],spec['amplitudes'][0]['points'])
                    d.close()
    def test_radiation_constants_and_unclamped_emissivity_required(self):
        self.reject('radiation-cooling',lambda s:s['step']['thermal'].pop('stefanBoltzmann'))
        for value in ('-0.1','1.1'):
            self.reject('radiation-cooling',lambda s:s['step']['heatLoads'][0].update(magnitude=value))
        self.reject('radiation-cooling',lambda s:s['step']['heatLoads'][0].update(sinkTemperature='-300'))
    def test_temperature_tables_positive_ordered_and_unambiguous(self):
        self.reject('temperature-conductivity',lambda s:s['materials'][0].update(conductivity='1'))
        self.reject('temperature-conductivity',lambda s:s['materials'][0].update(conductivityTable=[['1','100'],['2','0']]))
        self.reject('temperature-conductivity',lambda s:s['materials'][0].update(conductivityTable=[['0','0'],['2','100']]))
    def test_missing_duplicate_and_unordered_amplitudes_refused(self):
        self.reject('amplitude-force',lambda s:s.update(amplitudes=[]))
        self.reject('amplitude-force',lambda s:s['amplitudes'].append(copy.deepcopy(s['amplitudes'][0])))
        self.reject('amplitude-force',lambda s:s['amplitudes'][0].update(points=[[0,0],[0,1]]))
    def test_temperature_fields_require_explicit_initial_and_full_coverage(self):
        self.reject('free-expansion',lambda s:s['step'].pop('initialTemperature'))
        self.reject('free-expansion',lambda s:s['step']['temperatureFields'][0].update(nodeSet='X0'))
        self.reject('free-expansion',lambda s:s['materials'][0].pop('expansionZeroTemperature'))
    def test_bindings_cannot_disappear_in_editor(self):
        data,spec=fixture('amplitude-force')
        with tempfile.TemporaryDirectory() as name:
            p=Path(name)/'mesh.inp';p.write_bytes(data);d=AnalysisDialog(None,decode(p),data,spec)
            self.assertEqual(d.collect()['step']['loads'][0]['amplitude'],'Pulse')
            d.amplitude_bindings.table.item(0,1).setText('Missing')
            self.assertFalse(d.validate_current());self.assertIn('existing definition',d.message.text());d.close()
    def test_temperature_amplitude_and_time_shifts_reach_original_validation(self):
        data,s=fixture('free-expansion');s['amplitudes']=[{'name':'Temperature-profile','points':[[0,1],[1,1]],'shiftX':.1,'shiftY':.2,'timeSpan':'TotalTime'}]
        s['step']['temperatureFields'][0]['amplitude']='Temperature-profile';self.assertTrue(validate_definition(data,s)['success'])

if __name__=='__main__':unittest.main()
