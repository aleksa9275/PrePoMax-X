"""Focused original-property/Controller workflow, also runnable without a display."""
import json
from pathlib import Path
from System import Array, Double
from CaeGlobals import UnitSystemType
from CaeModel import ModelSpaceEnum, Material, Elastic, Density, ThermalExpansion
from PrePoMax import ViewThermalExpansion
from PrePoMax.Commands import RegenerateTypeEnum
from PrePoMaxX.UI import MaterialEditSession, PropertySheet


def run(session, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    checks = []
    c = session.Controller
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)
    def matrix(rows):
        return Array[Array[Double]]([Array[Double](row) for row in rows])
    def modulus():
        return c.GetMaterial('XSTEEL').Properties[0].YoungsPoissonsTemp[0][0].Value
    c.New()
    c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD, UnitSystemType.MM_TON_S_C)
    root = Path(__file__).resolve().parents[2]
    c.ImportFileCommand(str(root / '.project/reports/windows-reference/fixtures/definitions.inp'), False)
    c.SaveToPmxCommand(str(output / 'baseline.pmx'))
    untouched = MaterialEditSession(c, 'XSTEEL')
    before = c.GetActiveCommands().Count
    check('unchanged accept does not record a command', not untouched.Commit() and c.GetActiveCommands().Count == before)
    draft = MaterialEditSession(c, 'XSTEEL')
    fields = draft.Properties(0).Fields
    check('original descriptor names', [f.Name for f in fields] == ['YoungsModulus', 'PoissonsRatio'])
    check('original descriptor description', 'Young' in fields[0].Description)
    draft.Properties(0).Set('YoungsModulus', '100 GPa')
    check('draft is isolated before accept/cancel', modulus() == 210000)
    draft = MaterialEditSession(c, 'XSTEEL')
    check('cancel discards converted value', '210000' in draft.Properties(0).Fields[0].Text)
    try:
        draft.Properties(0).Set('YoungsModulus', '-1')
        draft.Commit()
        raise AssertionError('negative modulus accepted')
    except Exception as error:
        check('original validation rejects negative modulus', 'larger than 0' in str(error))
    check('invalid accept leaves model unchanged', modulus() == 210000)
    draft.Properties(0).Set('YoungsModulus', '=100000*2')
    draft.Commit()
    check('original equation converter and setter', modulus() == 200000)
    c.UndoHistory(RegenerateTypeEnum.All)
    check('original undo restores material', modulus() == 210000)
    c.RedoHistory()
    check('original redo restores edit', modulus() == 200000)
    draft = MaterialEditSession(c, 'XSTEEL')
    draft.Properties(0).Set('YoungsModulus', '100 GPa')
    draft.Commit()
    check('original unit conversion', modulus() == 100000)
    c.SaveToPmxCommand(str(output / 'edited.pmx'))
    c.ExportToCalculixCommand(str(output / 'edited.inp'))
    c.New()
    session.Open(str(output / 'edited.pmx'))
    check('original PMX reopen retains edit', modulus() == 100000)
    check('Controller retained render geometry', len(session.Presentation.SceneActors) > 0)
    m = Material('TemperatureTable')
    m.TemperatureDependent = True
    m.AddProperty(Elastic(matrix([[150000,.29,20],[140000,.28,100]])))
    m.AddProperty(Density(matrix([[7.85e-9,20],[7.7e-9,100]])))
    m.AddProperty(ThermalExpansion(matrix([[1e-5,20],[1.2e-5,100]])))
    c.AddMaterialCommand(m)
    draft = MaterialEditSession(c, m.Name)
    check('temperature table selected', draft.ShowTable(0) and not draft.ShowProperties(0) and draft.RowCount(0)==2)
    check('temperature column visible', 'TemperatureEq' in [f.Name for f in draft.Row(0,0).Fields])
    draft.Row(0,1).Set('YoungsModulusEq', '130 GPa')
    draft.Commit()
    check('table changes original data', c.GetMaterial(m.Name).Properties[0].YoungsPoissonsTemp[1][0].Value == 130000)
    view = ViewThermalExpansion(ThermalExpansion(matrix([[1e-5,20]])), False)
    check('dynamic property initially visible', 'ThermalExpansion' in [f.Name for f in PropertySheet(view).Fields])
    view.SetTemperatureDependence(True)
    check('original dynamic visibility updates', 'ThermalExpansion' not in [f.Name for f in PropertySheet(view).Fields])
    draft = MaterialEditSession(c, 'XSTEEL')
    check('non-temperature table column hidden', 'TemperatureEq' not in [f.Name for f in draft.Row(0,0).Fields])
    draft.Name = 'temperaturetable'
    try:
        draft.Commit()
        raise AssertionError('duplicate name accepted')
    except Exception as error:
        check('original name collision validation', 'already exists' in str(error))
    (output / 'service.json').write_text(json.dumps({'success':True,'checks':checks}, indent=2)+'\n')
