"""C5 application services against original Controller and strict file formats."""
import json,traceback
from pathlib import Path
from System import Array,String,Double
from CaeGlobals import UnitSystemType
from CaeModel import ModelSpaceEnum
from PrePoMaxX.UI import ApplicationSession,KeywordEditSession
from PrePoMax.Commands import RegenerateTypeEnum
from PrePoMax.Rpc import RpcSessionInfoWriter

def run(session,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);checks=[];report={'success':False,'checks':checks}
    def check(name,condition):
        checks.append({'name':name,'passed':bool(condition)})
        if not condition:raise AssertionError(name)
    c=session.Controller;application=ApplicationSession(session)
    try:
        c.New();c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C)
        root=Path(__file__).resolve().parents[2];c.ImportFileCommand(str(root/'.project/reports/windows-reference/fixtures/definitions.inp'),False)
        settings=application.Settings();check('all thirteen original settings pages',len(settings.Pages)==13)
        page=next(n for n in settings.Pages if n=='Graphics');fields=list(settings.Page(page).Fields);check('original graphics descriptors',any(f.Name=='AmbientComponent' for f in fields))
        settings.Page(page).Set('AmbientComponent','0.45');settings.Apply();check('settings apply through original container',abs(c.Settings.Graphics.AmbientComponent-.45)<1e-6)
        preferences=output/'settings.bin';application.SavePreferences(str(preferences));settings.Reset(page);settings.Apply();application.LoadPreferences(str(preferences));check('strict settings save/load',abs(c.Settings.Graphics.AmbientComponent-.45)<1e-6)
        lib=application.Library();lib.New(str(output/'materials.lib'));category=lib.Category(lib.Root,'Metals');lib.ToLibrary(category,'XSTEEL');lib.Save()
        loaded=application.Library();loaded.Open(str(output/'materials.lib'));check('original .lib category and material graph',loaded.Root.Items[0].Items[0].Tag.Name=='XSTEEL')
        loaded.ToModel(loaded.Root.Items[0].Items[0]);check('library import isolated before apply',not c.Model.Materials.ContainsKey('XSTEEL_Library-1'));loaded.Apply();check('library copies use original naming and commands',c.Model.Materials.ContainsKey('XSTEEL_Library-1'))
        loaded.Rename(loaded.Root,loaded.Root.Items[0],'Alloys');loaded.Save();check('library category rename persisted',loaded.Root.Items[0].Name=='Alloys')
        history=application.History();check('original history rows exposed',len(history.Rows)==c.GetCommands().Count)
        check('original command property inspector',any(f.Name=='Name' for f in history.Properties(0).Fields))
        history.Save(str(output/'history.pmh'));saved=len(history.Rows);history.Clear();history.Open(str(output/'history.pmh'));check('strict PMH round-trip',len(history.Rows)==saved)
        journal=output/'History.py';history.ExportPython(str(journal));check('original Python journal exporter',journal.is_file() and 'pmx' in journal.read_text())
        c.DuplicateMaterialsCommand(Array[String](['XSTEEL']))
        try:history.Apply();raise AssertionError('stale history accepted')
        except Exception as error:check('stale history draft refused','history was changed' in str(error))
        history.Reset();before=[r.Name for r in history.Rows];history.Move(len(before)-1,-1);check('history reorder uses original commands',history.Rows[-2].Name==before[-1]);history.Reset()
        keywords=KeywordEditSession(c)
        def walk(node):
            yield node
            for child in node.Nodes:yield from walk(child)
        node=keywords.Add(keywords.Root);keywords.Set(node,'*USER MATERIAL\n1, 2, 3',True);keywords.Apply();check('original user keyword added by command',c.GetCalculixUserKeywords().Count==1)
        editor=KeywordEditSession(c);node=next(n for n in walk(editor.Root) if n.User);editor.Move(node,True);editor.Set(node,'*USER MATERIAL\n4, 5, 6',True);editor.Apply();check('original user keyword tree movement and update','4, 5, 6' in str(next(iter(c.GetCalculixUserKeywords().Values)).Data))
        editor=KeywordEditSession(c);node=next(n for n in walk(editor.Root) if n.Parent is not None and not n.User and not n.Title and n.Data and '*ELASTIC' in n.Data.upper());original=node.Data;editor.Set(node,original+'\n** C5 override',True);editor.Apply();check('generated keyword signature override recorded',any(o.Data is not None and 'C5 override' in o.Data for o in c.GetCalculixKeywordOverrides()))
        editor=KeywordEditSession(c);node=next(n for n in walk(editor.Root) if n.Modified);editor.Reset(node);editor.Apply();check('generated override reset retains user keywords',len(c.GetCalculixKeywordOverrides())==0 and c.GetCalculixUserKeywords().Count==1)
        application.Export(str(output/'model.inp'),False);application.Export(str(output/'abaqus.inp'),True);check('original CalculiX and Abaqus deck exporters',all((output/n).is_file() for n in ['model.inp','abaqus.inp']))
        application.Parameters(str(output/'parameters.csv'),False);check('original parameter exporter',(output/'parameters.csv').is_file())
        application.Rename('Materials',None,'XSTEEL_Library-1','LibrarySteel');check('original rename command',c.Model.Materials.ContainsKey('LibrarySteel'))
        from PrePoMaxX.UI import PlotSession
        from UserControls import SidePanelsState,XYPlotPanelState,XYPlotState,XYPlotCurveState
        plots=PlotSession(c);plots.AddPlot();curve=XYPlotCurveState();curve.XValues=Array[Double]([0,1,2]);curve.YValues=Array[Double]([2,4,6]);curve.Settings.Name='OriginalState';plots.State.Plots[0].Curves.Add(curve)
        state=SidePanelsState();state.XYPlotPanelState=plots.State;session.Presentation.SetPendingSidePanelsState(state)
        c.SaveToPmxCommand(str(output/'application.pmx'));session.Open(str(output/'application.pmx'));restored=session.Presentation.GetSidePanelsState().XYPlotPanelState;check('original plot state survives strict PMX',restored.Plots[0].Curves[0].YValues[2]==6)
        check('keyword/library state survives strict PMX',c.GetCalculixUserKeywords().Count==1 and c.Model.Materials.ContainsKey('LibrarySteel'))
        # Existing engine API drives a private script scope and records one original command.
        result=application.Execute('print(6 * 7)',True,None,Array[String]([]));result.Wait();check('original Python execution output',not result.Result.Error and '42' in result.Result.Output)
        check('script recorded as original command',c.GetActiveCommands()[c.GetActiveCommandCount()-1].GetType().Name=='CRunPythonScript')
        check('automation starts disabled',not application.Automation.IsRunning and not c.AutomationSettings.AccessToken)
        from PrePoMaxX.UI import QuerySession,AdvisorPages,ContactSearchSession
        from System import Int32,Action
        query=QuerySession(c);check('original node and assembly query calculations','Node' in query.Run('Node',Array[Int32]([1])) and 'Assembly' in query.Run('Assembly',Array[Int32]([])))
        check('original distance and angle query outputs','Distance' in query.Run('Distance',Array[Int32]([1,2])) and 'Angle' in query.Run('Angle',Array[Int32]([1,2,3])))
        actions=[];callback=Action[String,Int32](lambda name,index:actions.append((str(name),int(index))));pages=AdvisorPages.Create(callback);pages[0].Items[1].Activate();check('original advisor pages and action arguments',len(pages)==9 and actions==[('tsmiNew_Click',-1)])
        from CaeMesh.ContactSearchNamespace import GeometryFilterEnum
        search=ContactSearchSession(c);task=search.Search(.01,10,'ByParts','Tie','','Surface to surface',False,GeometryFilterEnum.Solid);task.Wait();check('original contact search runs on live model',not task.IsFaulted)
        RpcSessionInfoWriter.NativeSessionsDirectory=str(output/'sessions')
        report['success']=True
    except Exception as error:report['error']=str(error);report['traceback']=traceback.format_exc()
    finally:application.Dispose();(output/'application.json').write_text(json.dumps(report,indent=2)+'\n')
    if not report['success']:raise RuntimeError(report['error'])
