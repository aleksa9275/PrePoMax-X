"""Substantive C2 workflow through original form factories, rules and commands."""
import json
import traceback
from pathlib import Path
import clr
for assembly in ['PrePoMaxX.Workbench','PrePoMax','CaeModel','CaeGlobals','CaeMesh']:
    clr.AddReference(assembly)
from System import Array, Int32, Double, Func, String
from System.Windows.Forms import IWin32Window, MessageBoxButtons, MessageBoxIcon, DialogResult
from CaeGlobals import UnitSystemType, Selection, SelectionNodeMouse, vtkSelectItem, vtkSelectBy, vtkSelectOperation, MessageBoxes, MessageBoxModeEnum
from CaeModel import ModelSpaceEnum
from PrePoMax import ViewGeometryModelResults
from PrePoMax.Commands import RegenerateTypeEnum
from PrePoMaxX.UI import AuthoringSession, MaterialEditSession


def run(session, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    report={'success':False,'checks':[],'factories':{}}
    c=session.Controller
    a=AuthoringSession(c)
    def check(name, condition):
        if not condition:raise AssertionError(name)
        report['checks'].append(name)
    def field(rule,name):return next(f for f in rule.Properties.Fields if f.Name==name)
    def set_region(rule,kind,name,prefix=''):
        prop=prefix+'RegionType'
        text=next(v for v in field(rule,prop).Choices if kind.lower() in v.lower())
        rule.Properties.Set(prop,text)
        selectors=[f for f in rule.Properties.Fields if f.Name in [prefix+kind.title().replace(' ','')+'Name',kind.title().replace(' ','')+'Name']]
        selector=selectors[0]
        rule.Properties.Set(selector.Name,name)
    def create(family,name,step=None,kind=0):
        rule=a.Edit(family,step,None);rule.Select(kind);rule.Properties.Set('Name',name);return rule
    try:
        c.New();c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C)
        # Public fixture mesh is read by the original importer; authored definitions start empty.
        fixture=Path(__file__).resolve().parents[2]/'.project/reports/windows-reference/fixtures/definitions.inp'
        mesh=output/'cube.inp';mesh.write_text(fixture.read_text().split('*MATERIAL')[0])
        c.ImportFileCommand(str(mesh),False)
        c.CurrentView=ViewGeometryModelResults.Model;c.DrawModel(False)
        check('complete model tree families present',set(a.Families).issubset({e.Family for e in a.Tree}))
        parameters=a.Parameters();parameters.Table.Add()
        parameters.Table.Row(0).Set('Name','E0');parameters.Table.Row(0).Set('Equation','100000')
        parameters.Table.Add();parameters.Table.Row(1).Set('Name','E1');parameters.Table.Row(1).Set('Equation','=2*E0')
        parameters.Commit()
        check('original parameter table evaluates dependencies',c.Model.Parameters['E1'].Value==200000)
        bad=a.Parameters();bad.Table.Row(1).Set('Name','e0')
        try:bad.Commit();raise AssertionError('duplicate parameter accepted')
        except Exception as error:check('original parameter table rejects case-insensitive duplicate','already exists' in str(error) or 'cannot be used' in str(error))
        bad.Cancel()
        check('parameter rejection is isolated',c.Model.Parameters['E1'].Value==200000)
        material=a.Material();material.Name='Steel';material.AddProperty(2)
        material.Properties(0).Set('YoungsModulus','=E1');material.Properties(0).Set('PoissonsRatio','0.3')
        material.AddProperty(0);material.Properties(1).Set('Density','7.85e-9');material.Commit()
        check('new material uses original parameter equation',c.GetMaterial('Steel').Properties[0].YoungsPoissonsTemp[0][0].Value==200000)
        edit=a.Material('Steel');edit.TemperatureDependent=True;table=edit.Table(0);table.Add()
        table.Row(1).Set('YoungsModulusEq','180 GPa');table.Row(1).Set('PoissonsRatioEq','0.29');table.Row(1).Set('TemperatureEq','100')
        edit.Commit()
        check('material temperature toggle and row insertion',c.GetMaterial('Steel').TemperatureDependent and len(c.GetMaterial('Steel').Properties[0].YoungsPoissonsTemp)==2)
        edit=a.Material('Steel');edit.Table(0).Remove(1);edit.TemperatureDependent=False;edit.Commit()
        c.SaveToPmxCommand(str(output/'baseline.pmx'))
        part=next(iter(c.Model.Mesh.Parts.Values))
        def picked(kind,by):
            selection=Selection();selection.CurrentView=int(ViewGeometryModelResults.Model);selection.SelectItem=kind
            node=SelectionNodeMouse(Array[Double]([1,.5,.5]),Array[Double]([-1,0,0]),None,False,getattr(vtkSelectOperation,'None'),Array[Int32]([part.PartId]),None,by,0)
            node.Precision=.01;selection.Add(node)
            return selection,list(c.GetIdsFromSelection(selection))
        nodes,node_ids=picked(vtkSelectItem.Node,vtkSelectBy.Surface)
        check('original recorded face selection returns exact nodes',sorted(node_ids)==[2,3,6,7])
        rule=create('Node sets','PickedNodes');rule.SetSelection(Array[Int32](node_ids),nodes);rule.Commit()
        check('picked node set retains selection history',c.GetNodeSet('PickedNodes').CreationData.Nodes.Count==1)
        elements,element_ids=picked(vtkSelectItem.Element,vtkSelectBy.Element)
        rule=create('Element sets','AllElements');rule.SetSelection(Array[Int32](element_ids),elements);rule.Commit()
        faces,face_ids=picked(vtkSelectItem.Surface,vtkSelectBy.Surface)
        rule=create('Surfaces','LoadedFace');rule.SetSelection(Array[Int32](face_ids),faces);rule.Commit()
        check('original surface authoring computes area',abs(c.GetSurface('LoadedFace').Area-1)<1e-12)
        section=create('Sections','Solid');set_region(section,'Element set','AllElements');section.Commit()
        check('original section command stores assignment',c.GetSection('Solid').MaterialName=='Steel')
        incompatible=create('Sections','WrongShell',kind=1);set_region(incompatible,'Element set','AllElements')
        try:incompatible.Commit();raise AssertionError('incompatible section accepted')
        except Exception as error:check('original section type validation','not compatible' in str(error))
        reference=create('Reference points','RP');reference.Commit()
        coordinate=create('Coordinate systems','CS');coordinate.Commit()
        check('reference point and coordinate system commands',len(c.GetModelReferencePointNames())==1 and len(c.GetModelCoordinateSystemNames())==1)
        distribution=create('Distributions','Uniform');distribution.Commit()
        amplitude=create('Amplitudes','Ramp');amplitude.Commit()
        check('distribution and amplitude commands','Uniform' in list(c.GetDistributionNames()) and 'Ramp' in list(c.GetAmplitudeNames()))
        interaction=a.Interaction();interaction.Name='ContactLaw';interaction.AddProperty(0);interaction.AddProperty(1);interaction.Commit()
        check('surface interaction shared form construction','ContactLaw' in list(c.GetSurfaceInteractionNames()))
        contact=create('Contact pairs','Pair')
        try:contact.Commit();raise AssertionError('empty contact selection accepted')
        except Exception as error:check('original contact selection validation','at least one item' in str(error))
        # Preserve the original constructor's permitted self-contact definition.
        set_region(contact,'Surface','LoadedFace','Master');set_region(contact,'Surface','LoadedFace','Slave');contact.Commit()
        check('original contact pair authoring',c.GetContactPair('Pair').MasterRegionName=='LoadedFace')
        # A new static step comes from the original factory (including original default job).
        step=create('Steps','Static');step.Commit()
        check('original step authoring adds default job',c.GetStep('Static') is not None and c.Jobs.Count==1)
        bc=create('Boundary conditions','Fixed','Static',0);set_region(bc,'Node set','X0');bc.Commit()
        force=create('Loads','Force','Static',0);set_region(force,'Node set','PickedNodes');force.Properties.Set('F1','100');force.Commit()
        check('original BC and load authoring',c.GetBoundaryCondition('Static','Fixed') is not None and c.GetLoad('Static','Force').F1.Value==100)
        invalid=create('Loads','Zero','Static',0);set_region(invalid,'Node set','PickedNodes')
        try:invalid.Commit();raise AssertionError('zero force accepted')
        except Exception as error:check('original load validation rejects zero','must not be equal to 0' in str(error))
        a.Duplicate('Loads','Static',Array[String](['Force']))
        check('duplicate uses original command',len(c.GetLoadNamesForStep('Static'))==2)
        duplicate=next(n for n in c.GetLoadNamesForStep('Static') if n!='Force')
        a.Remove('Loads','Static',Array[String]([duplicate]))
        a.Activate('Loads','Static',Array[String](['Force']),False)
        check('activate/deactivate uses original command',not c.GetLoad('Static','Force').Active)
        c.UndoHistory(RegenerateTypeEnum.All)
        check('original history replays picked authoring',c.GetLoad('Static','Force').Active and sorted(c.GetNodeSet('PickedNodes').Labels)==[2,3,6,7])
        c.RedoHistory();a.Activate('Loads','Static',Array[String](['Force']),True)
        history=create('History outputs','Nodes','Static',0);set_region(history,'Node set','PickedNodes');history.Commit()
        fields=create('Field outputs','Nodal','Static',0);fields.Commit()
        check('original field/history output authoring',c.GetHistoryOutput('Static','Nodes') is not None and c.GetFieldOutput('Static','Nodal') is not None)
        spring=create('Constraints','Support',kind=0);set_region(spring,'Node set','X0','Master');spring.Properties.Set('K1','1000');spring.Commit()
        check('original constraint authoring',c.GetConstraint('Support').K1.Value==1000)
        initial=create('Initial conditions','InitialTemperature',kind=0);set_region(initial,'Node set','PickedNodes');initial.Properties.Set('Temperature','20');initial.Commit()
        check('original initial condition authoring',c.GetInitialCondition('InitialTemperature').Temperature.Value==20)
        model=a.Edit('Model properties',None,c.Model.Name);model.Properties.Set('Name','C2 authored model');model.Commit()
        check('original model properties apply',c.Model.Name=='C2 authored model')
        controls=a.Controls('Static');controls.AddProperty(0)
        previous_mode=MessageBoxes.Mode;previous_presenter=MessageBoxes.InteractivePresenter
        try:
            MessageBoxes.Mode=MessageBoxModeEnum.Interactive
            reject=Func[IWin32Window,String,String,MessageBoxButtons,MessageBoxIcon,DialogResult](lambda *args:DialogResult.Cancel)
            MessageBoxes.InteractivePresenter=reject
            check('original solution-control warning can cancel',not controls.Commit() and c.GetStep('Static').StepControls.Parameters.Count==0)
            accept=Func[IWin32Window,String,String,MessageBoxButtons,MessageBoxIcon,DialogResult](lambda *args:DialogResult.OK)
            MessageBoxes.InteractivePresenter=accept
            check('original solution-control warning accepts',controls.Commit() and c.GetStep('Static').StepControls.Parameters.Count==1)
        finally:
            MessageBoxes.Mode=previous_mode;MessageBoxes.InteractivePresenter=previous_presenter
        a.CreateFolder('Materials',None,'Structural',Array[String](['Steel']),None)
        folder=next(child for entry in a.Tree if entry.Family=='Materials' for child in entry.Children if child.FolderId)
        check('original tree folder layout',folder.Name=='Structural' and folder.Children[0].Name=='Steel')
        a.RenameFolder('Materials',None,folder.FolderId,'Solids')
        check('original folder rename',next(child for entry in a.Tree if entry.Family=='Materials' for child in entry.Children).Name=='Solids')
        # Exercise every available original prototype on every supported original step.
        c.SaveToPmxCommand(str(output/'matrix-base.pmx'))
        step_rule=a.Edit('Steps',None,None)
        prototype_count=len(step_rule.Choices)
        for index in range(prototype_count):
            c.New();session.Open(str(output/'matrix-base.pmx'))
            step_rule=a.Edit('Steps',None,None)
            choice=step_rule.Choices[index]
            if choice.Tag is None:continue
            step_rule.Select(index)
            item=step_rule.Item
            if item is None:continue
            name='Matrix'+str(index)
            step_rule.Properties.Set('Name',name)
            step_rule.Commit()
            entry={}
            for family in a.StepFamilies:
                draft=a.Edit(family,name,None)
                entry[family]=[]
                for i,prototype in enumerate(draft.Choices):
                    draft.Select(i)
                    entry[family].append({'name':prototype.Text,'properties':len(draft.Properties.Fields)})
            report['factories'][str(item.GetType().Name)]=entry
            step_rule=a.Edit('Steps',None,None)
        c.New();session.Open(str(output/'matrix-base.pmx'))
        wear=a.Edit('Steps',None,None)
        wear.Select(next(i for i,v in enumerate(wear.Choices) if 'Slip Wear' in v.Text))
        wear.Properties.Set('Name','Wear');wear.Commit()
        boundary=a.Edit('Steps',None,None)
        boundary.Select(next(i for i,v in enumerate(boundary.Choices) if 'Boundary Displacement' in v.Text))
        boundary.Properties.Set('Name','WearBoundary');boundary.Commit()
        report['factories']['BoundaryDisplacementStep']={}
        for family in a.StepFamilies:
            draft=a.Edit(family,'WearBoundary',None)
            report['factories']['BoundaryDisplacementStep'][family]=[]
            for i,prototype in enumerate(draft.Choices):
                draft.Select(i)
                report['factories']['BoundaryDisplacementStep'][family].append({'name':prototype.Text,'properties':len(draft.Properties.Fields)})
        check('original wear boundary-step sequencing',c.GetStep('WearBoundary').BoundaryConditions.Count==0)
        check('original step-family prototype matrix',len(report['factories'])==12)
        c.New();session.Open(str(output/'matrix-base.pmx'))
        c.ExportToCalculixCommand(str(output/'authored.inp'))
        c.SaveToPmxCommand(str(output/'authored.pmx'))
        c.New();session.Open(str(output/'authored.pmx'))
        check('authored project PMX preserves full definitions',c.GetLoad('Static','Force').F1.Value==100 and c.GetSection('Solid').MaterialName=='Steel' and sorted(c.GetNodeSet('PickedNodes').Labels)==[2,3,6,7])
        report['success']=True
    except Exception:
        report['error']=traceback.format_exc()
    finally:
        (output/'authoring.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['success']:raise RuntimeError(report['error'])
