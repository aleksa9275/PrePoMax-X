"""Representative C3 original-form → CAD/mesh → history/PMX workflow."""
import json
import traceback
from pathlib import Path
from System import Array, String, Int32
from CaeGlobals import UnitSystemType, Selection, SelectionNodeIds, vtkSelectItem, vtkSelectOperation
from CaeModel import ModelSpaceEnum
from PrePoMax import ViewGeometryModelResults
from PrePoMax.Commands import RegenerateTypeEnum
from PrePoMaxX.UI import GeometrySession


def run(session,output,fixture=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    report={'success':False,'checks':[],'factories':{}}
    c=session.Controller;g=GeometrySession(c)
    fixture=Path(fixture) if fixture else Path(__file__).parent/'fixtures/cube.brep'
    def check(name,value):
        if not value:raise AssertionError(name)
        report['checks'].append(name)
    def selection(kind,ids):
        s=Selection();s.CurrentView=int(c.CurrentView);s.SelectItem=kind
        s.Add(SelectionNodeIds(getattr(vtkSelectOperation,'None'),False,Array[Int32](ids)))
        return s
    def assign(rule,kind,ids,prefix=''):
        rule.SetSelection(Array[Int32](ids),selection(kind,ids),prefix)
    def names():return Array[String](list(c.Model.Geometry.Parts.Keys))
    def fields(rule):return {f.Name:f for f in rule.Properties.Fields}
    def set_choice(rule,field,match):
        text=next(v for v in fields(rule)[field].Choices if match.lower() in v.lower())
        rule.Properties.Set(field,text)
    try:
        c.New();c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C)
        # All ten original factories are exposed in 3D; original 2D filtering
        # excludes Sweep Mesh. No backend execution is inferred from this matrix.
        for space in [ModelSpaceEnum.ThreeD,ModelSpaceEnum.PlaneStress]:
            c.New();c.SetNewModelPropertiesCommand(space,UnitSystemType.MM_TON_S_C)
            rule=g.Edit('Mesh setup');entries=[]
            for i,choice in enumerate(rule.Choices):
                rule.Select(i);entries.append({'type':choice.Text,'properties':[f.Name for f in rule.Properties.Fields]})
            report['factories'][str(space)]=entries
        check('original 3D/2D mesh setup factories',len(report['factories']['ThreeD'])==10 and len(report['factories']['PlaneStress'])==9)
        c.New();c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C)
        c.ImportFileCommand(str(fixture.resolve()),False)
        c.CurrentView=ViewGeometryModelResults.Geometry;c.DrawGeometry(False)
        check('original CAD import and geometry scene',len(c.Model.Geometry.Parts)==1 and len(session.Presentation.SceneActors)>0)
        part=next(iter(c.Model.Geometry.Parts.Values));pid=part.PartId
        rule=g.Edit('Mesh setup');assign(rule,vtkSelectItem.Part,[pid])
        check('part-dependent original sizing defaults',rule.Item.MaxH==c.GetPartDefaultMeshingParameters(part.Name).MaxH)
        set_choice(rule,'AdvancedView','Advanced')
        set_choice(rule,'Relative','Absolute')
        rule.Properties.Set('MaxH','4');rule.Properties.Set('MinH','0')
        set_choice(rule,'SecondOrder','No')
        rule.Properties.Set('Name','Sizing');rule.Commit()
        check('mesh sizing commits original command',c.GetMeshSetupItem('Sizing').MaxH==4)
        invalid=g.Edit('Mesh setup')
        try:invalid.Commit();raise AssertionError('empty region accepted')
        except Exception as error:check('original empty setup rejection','at least one' in str(error))
        rule=g.Edit('Mesh setup');rule.Select(next(i for i,ch in enumerate(rule.Choices) if ch.Text=='Tetrahedral Gmsh'))
        rule.Properties.Set('Name','Tetrahedra');assign(rule,vtkSelectItem.Part,[pid]);rule.Commit()
        g.ExecuteNow('Duplicate mesh setup',Array[String](['Sizing']))
        check('duplicate mesh setup via original command',len(c.GetMeshSetupItemNames())==3)
        duplicate=next(n for n in c.GetMeshSetupItemNames() if n not in ['Sizing','Tetrahedra'])
        g.ExecuteNow('Remove mesh setup',Array[String]([duplicate]))
        g.SetActive(Array[String](['Sizing']),False);check('mesh setup activation command',not c.GetMeshSetupItem('Sizing').Active)
        g.SetActive(Array[String](['Sizing']),True)
        c.UndoHistory(RegenerateTypeEnum.All);check('mesh setup undo',not c.GetMeshSetupItem('Sizing').Active)
        c.RedoHistory();check('mesh setup redo',c.GetMeshSetupItem('Sizing').Active)
        # Build all geometry feature/property drafts without executing destructive
        # operations against arbitrary regions. Selected representative edits run below.
        for family in list(g.GeometryEditors):
            rule=g.Edit(family)
            choices=rule.Choices;rows=[]
            if len(choices):
                for i,choice in enumerate(choices):rule.Select(i);rows.append({'type':choice.Text,'properties':[f.Name for f in rule.Properties.Fields]})
            else:rows=[{'type':family,'properties':[f.Name for f in rule.Properties.Fields]}]
            report['factories'][family]=rows
        check('all CAD editing property factories',len(report['factories']['Split solid'])==4 and len(report['factories']['Split shell'])==5)
        c.CurrentView=ViewGeometryModelResults.Geometry
        part=next(iter(c.Model.Geometry.Parts.Values))
        props=g.Edit('Geometry parts',part.Name);props.Properties.Set('Name','Cube');props.Commit()
        check('original part properties rename','Cube' in list(c.GetGeometryPartNames()))
        c.SaveToPmxCommand(str(output/'cad-before-mesh.pmx'))
        g.ExecuteNow('Create mesh',names())
        c.CurrentView=ViewGeometryModelResults.Model;c.DrawModel(False)
        elements=len(c.Model.Mesh.Elements);nodes=len(c.Model.Mesh.Nodes)
        check('native original Gmsh creates solid mesh',elements>0 and nodes>0)
        for family in g.MeshEditors:
            rule=g.Edit(family,parts=Array[String](list(c.GetModelPartNames())))
            report['factories'][family]=[{'type':family,'properties':[f.Name for f in rule.Properties.Fields]}]
        check('all original mesh editing drafts',all(f in report['factories'] for f in g.MeshEditors))
        meshpart=next(iter(c.Model.Mesh.Parts.Values));before=meshpart.BoundingBox.MinX
        transform=g.Edit('Translate',parts=Array[String]([meshpart.Name]));transform.Properties.Set('X2','2');transform.Commit()
        check('model translation uses original command',c.Model.Mesh.Parts[meshpart.Name].BoundingBox.MinX==before+2)
        c.UndoHistory(RegenerateTypeEnum.All);check('mesh transform undo',c.Model.Mesh.Parts[meshpart.Name].BoundingBox.MinX==before)
        c.RedoHistory();check('mesh transform redo',c.Model.Mesh.Parts[meshpart.Name].BoundingBox.MinX==before+2)
        for family in ['Rotate','Mirror','Scale']:
            rule=g.Edit(family,parts=Array[String]([meshpart.Name]));report['factories'][family]=[{'properties':[f.Name for f in rule.Properties.Fields]}]
        c.RenumberNodesCommand(101);c.RenumberElementsCommand(201)
        check('original node/element renumber',min(c.Model.Mesh.Nodes)==101 and min(c.Model.Mesh.Elements)==201)
        quality=g.Edit('Element quality',parts=Array[String]([meshpart.Name]));quality.Preview()
        import math
        check('original native element quality statistics',math.isfinite(quality.Item.Min) and math.isfinite(quality.Item.Max) and quality.Item.Max>=quality.Item.Min)
        quality.Commit();check('original quality element-set command',len(c.GetUserElementSetNames())==1)
        c.SaveToPmxCommand(str(output/'meshed.pmx'));c.ExportMeshPartsCommand(Array[String]([meshpart.Name]),str(output/'mesh.inp'),__import__('FileInOut.Output',fromlist=['MeshExportFormatEnum']).MeshExportFormatEnum.Calculix)
        c.New();session.Open(str(output/'meshed.pmx'))
        check('CAD setup and generated mesh PMX round-trip',len(c.Model.Mesh.Elements)==elements and len(c.Model.Mesh.Nodes)==nodes and len(c.GetMeshSetupItemNames())==2 and len(c.Model.Geometry.Parts)==1)
        c.New();c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C);c.ImportFileCommand(str(fixture.resolve()),False)
        c.CurrentView=ViewGeometryModelResults.Geometry
        part=next(iter(c.Model.Geometry.Parts.Values))
        cad_min=part.BoundingBox.MinX
        transform=g.Edit('Translate',parts=Array[String]([part.Name]));transform.Properties.Set('X2','1');transform.Commit()
        report['cadBounds']={'beforeMinX':cad_min,'afterMinX':next(iter(c.Model.Geometry.Parts.Values)).BoundingBox.MinX}
        part=next(iter(c.Model.Geometry.Parts.Values))
        check('native CAD translation updates original geometry',part.BoundingBox.MinX==cad_min+1)
        split=g.Edit('Split solid');split.Select(1)
        for key,value in [('X','6'),('Nx','1'),('Ny','0'),('Nz','0')]:split.Properties.Set(key,value)
        assign(split,vtkSelectItem.Part,[part.PartId]);split.Commit()
        from CaeMesh import CompoundGeometryPart
        compounds=[p for p in c.Model.Geometry.Parts.Values if isinstance(p,CompoundGeometryPart)]
        check('native CAD split creates original compound cells',len(compounds)==1 and len(compounds[0].SubPartNames)==2)
        compound=compounds[0]
        before_commands=c.GetActiveCommandCount()
        try:c.GroupSplitCellsCommand(compound.Name,compound.SubPartNames,'Grouped');raise AssertionError('redundant grouping accepted')
        except Exception as error:check('original redundant grouping rejection','Rename the sub-part instead' in str(error) and c.GetActiveCommandCount()==before_commands)
        c.GroupSplitCellsCommand(compound.Name,Array[String]([compound.SubPartNames[0]]),'Grouped')
        c.RenameSplitSubPartCommand(compound.Name,'Grouped','Unified')
        check('original split cell grouping and subpart rename','Unified' in list(c.Model.Geometry.Parts[compound.Name].CellSubPartNames) and len(set(c.Model.Geometry.Parts[compound.Name].CellSubPartNames))==2)
        c.SaveToPmxCommand(str(output/'split.pmx'))
        c.New();session.Open(str(output/'split.pmx'))
        check('split CAD compound PMX round-trip',any(isinstance(p,CompoundGeometryPart) and len(p.SubPartNames)==2 for p in c.Model.Geometry.Parts.Values))
        report.update(success=True,nodes=nodes,elements=elements,project=str(output/'meshed.pmx'),splitProject=str(output/'split.pmx'))
    except Exception as error:
        report['error']=str(error);report['traceback']=traceback.format_exc();raise
    finally:(output/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
