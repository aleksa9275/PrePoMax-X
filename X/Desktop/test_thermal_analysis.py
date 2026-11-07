"""Thermal model admission and real editor-to-original service regressions."""
import copy
from pathlib import Path
import unittest
from PyQt6 import QtWidgets
from analysis_editor import AnalysisDialog,validate_definition
from thermal_workflow_fixtures import CASES,definition,mesh
from viewport import decode

class ThermalAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def reject(self,spec,data=None):
        with self.assertRaises(ValueError):validate_definition(data or mesh('steady-conduction'),spec)

    def test_examples_roundtrip_editor_and_original_validation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                with self.subTest(case=case):
                    p=Path(directory)/(case+'.inp');p.write_bytes(mesh(case));spec=definition(case)
                    dialog=AnalysisDialog(None,decode(p),p.read_bytes(),spec,10)
                    self.assertTrue(dialog.validate_current(),dialog.message.text())
                    self.assertEqual(dialog.definition['materials'],spec['materials'])
                    self.assertEqual(dialog.definition['step']['heatLoads'],spec['step']['heatLoads'])
                    self.assertEqual(dialog.definition['step']['temperatures'],spec['step']['temperatures'])
                    self.assertFalse(dialog.validation['solverExecuted'])
                    dialog.close()

    def test_transient_capacity_and_initial_temperature_required(self):
        for key in ('density','specificHeat'):
            s=definition('transient-heating');s['materials'][0].pop(key);self.reject(s)
        s=definition('transient-heating');s['step']['thermal'].pop('initialTemperature');self.reject(s)

    def test_steady_heat_sink_and_thermal_material_required(self):
        s=definition('steady-conduction');s['step']['temperatures']=[];self.reject(s)
        s=definition('steady-conduction');s['materials'][0]['conductivity']='0';self.reject(s)
        s=definition('steady-conduction');s['materials'][0]['youngsModulus']='1000';self.reject(s)
        s=definition('steady-conduction');s['step']['loads']=[{'name':'Force','nodeSet':'TOP','forcePerNode':['1','0','0']}];self.reject(s)

    def test_temperature_overlap_and_incomplete_heat_face_refused(self):
        s=definition('steady-conduction');s['step']['temperatures'].append(copy.deepcopy(s['step']['temperatures'][0]));s['step']['temperatures'][-1]['name']='Duplicate';self.reject(s)
        s=definition('surface-heating');s['step']['heatLoads'][0]['region']='MISSING';self.reject(s)
        s=definition('surface-heating');data=mesh('surface-heating')+b'*Nset,Nset=POINT\n143\n';s['step']['heatLoads'][0]['region']='POINT';self.reject(s,data)
        s=definition('surface-heating');s['step']['heatLoads'].append({**s['step']['heatLoads'][0],'name':'Duplicate'});self.reject(s)

    def test_invalid_convection_and_deltmx_refused(self):
        for value in ('0','-2'):
            s=definition('film-cooling');s['step']['heatLoads'][0]['magnitude']=value;self.reject(s)
        s=definition('transient-heating');s['step']['thermal']['maximumTemperatureChange']=-1;self.reject(s)

    def test_original_units_convert_identical_material_and_load_decks(self):
        for case,quantity,bare in [('steady-conduction','conductivity','1'),('surface-heating','magnitude','10'),('film-cooling','magnitude','2')]:
            s=definition(case);first=validate_definition(mesh(case),s)['deckSha256']
            if quantity=='conductivity':s['materials'][0][quantity]=bare
            else:s['step']['heatLoads'][0][quantity]=bare
            self.assertEqual(first,validate_definition(mesh(case),s)['deckSha256'])
        s=definition('transient-heating');first=validate_definition(mesh('transient-heating'),s)['deckSha256']
        # 1 J/(kg K) = 10^6 mJ/(t K).
        s['materials'][0]['specificHeat']='0.001 J/(kg·°C)'
        self.assertEqual(first,validate_definition(mesh('transient-heating'),s)['deckSha256'])

if __name__=='__main__':unittest.main()
