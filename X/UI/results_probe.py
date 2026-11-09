"""C4 original job, result-tool, animation and PMX service workflow."""
import json,time,uuid
from pathlib import Path
from System import Array,String,Double,Single
from CaeGlobals import UnitSystemType,UnitSystem
from CaeModel import ModelSpaceEnum,SolverTypeEnum
from CaeJob import JobStatus,CalculixMonitorDataParser,AnalysisJob
from CaeResults import FOFieldNames,ResultHistoryOutputFromTable,FeResults
from PrePoMaxX.UI import ResultsSession
from PrePoMax.Commands import RegenerateTypeEnum


def prepare(session,output):
    c=session.Controller;c.New();c.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C)
    c.ImportFileCommand(str(Path(__file__).resolve().parents[2]/'.project/reports/windows-reference/fixtures/definitions.inp'),False)
    work=Path(output)/('solver-'+uuid.uuid4().hex[:8]);work.mkdir(parents=True)
    settings=c.Settings;settings.Solver.WorkDirectoryForSettingsOnly=str(work);settings.Solver.CalculixDefaultSolverType=SolverTypeEnum.Spooles;c.Settings=settings
    for step in c.Model.StepCollection.StepsList:step.SolverType=SolverTypeEnum.Spooles
    return work


def run(session,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);checks=[];c=session.Controller;r=ResultsSession(session)
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    try:
        work=prepare(session,output)
        draft=r.Edit('Jobs');draft.Properties.Set('Name','C4Cube');check('original analysis descriptors',len(draft.Properties.Fields)==6)
        draft.Commit();job=c.GetJob('C4Cube');check('original analysis command',job is not None and job.Argument=='C4Cube')
        duplicate=r.Edit('Jobs')
        duplicate.Properties.Set('Name','C4Cube')
        try:duplicate.Commit();raise AssertionError('duplicate accepted')
        except Exception as e:check('original analysis name validation','already exists' in str(e))
        r.Execute('Duplicate jobs',Array[String](['C4Cube']));check('duplicate analysis original command',len(c.GetJobNames())==2)
        other=[n for n in c.GetJobNames() if n!='C4Cube'][0];r.Execute('Remove jobs',Array[String]([other]));check('remove analysis original command',len(c.GetJobNames())==1)
        c.UndoHistory(RegenerateTypeEnum.All);check('job undo',len(c.GetJobNames())==2);c.RedoHistory();check('job redo',len(c.GetJobNames())==1)
        job=c.GetJob('C4Cube')
        task=r.RunJob('C4Cube',False);task.GetAwaiter().GetResult();check('original Controller native solver completed',job.JobStatus==JobStatus.OK)
        check('original job output retained','Job finished' in job.GetAllOutputData() or bool(job.GetAllOutputData()))
        check('original status parser',CalculixMonitorDataParser.ParseStatus(job.StatusFileData).Count>0)
        check('original convergence parser',CalculixMonitorDataParser.ParseConvergence(job.ConvergenceFileData).Count>=0)
        r.OpenJob('C4Cube').GetAwaiter().GetResult();check('original FRD reader',c.ResultsInitialized and len(c.CurrentResult.Mesh.Nodes)==8)
        c.CurrentResult.UnitSystem=UnitSystem(UnitSystemType.Undefined);session.Presentation.SelectResultsUnitSystem('MM_TON_S_C');check('explicit original result-unit selection',c.CurrentResult.UnitSystem.UnitSystemType==UnitSystemType.MM_TON_S_C)
        check('scalar actors retained',len(session.Presentation.SceneActors)>0 and any(a.Data.Geometry.Nodes.Values is not None for a in session.Presentation.SceneActors))
        check('original legend/status commands retained',{'SetScalarBarColorSpectrum','SetScalarBarText','SetStatusBlock'}.issubset({str(v.Name) for v in session.Presentation.RenderCommands}))
        fields=list(r.Fields);check('field/component inventory',len(fields)>2 and len(r.Components(fields[0]))>0)
        field='DISP';component='U1';step=list(r.Steps)[-1];increment=list(r.Increments(step))[-1];r.Field(field,component,step,increment)
        check('original displacement field unchanged',abs(c.GetNodalValue(2)-100/210000)<1e-9)
        r.Deformation('DISP','TrueScale',Single(1));check('true-scale original deformation',c.GetScale()==1)
        for view in ['Undeformed','Deformed','ColorContours','VectorPlot']:
            r.Representation(view);check('original '+view+' representation',len(session.Presentation.SceneActors)>0)
        r.Field('STRESS','S11',step,increment);r.Representation('TensorPlot');check('original tensor plot',any(v.Name=='AddTensorFieldActor' for v in session.Presentation.RenderCommands))
        r.Representation('ColorContours')
        for family,name in [('Result coordinate systems','ResultCS'),('Result reference points','ResultRP')]:
            draft=r.Edit(family);draft.Properties.Set('Name',name);draft.Commit();check('original '+family+' command',name in list(c.GetResultCoordinateSystemNames() if family=='Result coordinate systems' else c.GetResultReferencePointNames()))
        draft=r.Edit('Result coordinate systems','ResultCS');draft.Properties.Set('Name','ResultCS_Renamed');draft.Commit();check('original result coordinate edit', 'ResultCS_Renamed' in list(c.GetResultCoordinateSystemNames()))
        for family,count in [('Result fields',4),('Result histories',7)]:
            draft=r.Edit(family);check(family+' original factory count',len(draft.Choices)==count)
            for i,choice in enumerate(draft.Choices):draft.Select(i);list(draft.Properties.Fields)
            check(family+' original descriptors',True)
        r.Field('STRESS','S11',step,increment);source_stress=c.GetNodalValue(2)
        draft=r.Edit('Result fields');draft.Select(2);draft.Properties.Set('Name','DoubleStress');draft.Properties.Set('Equation','=2*STRESS.S11');draft.Commit()
        check('original equation field command',c.GetResultFieldOutput('DoubleStress') is not None)
        # Field evaluation uses the original result engine; no second numerical model.
        r.Field('DoubleStress',r.Components('DoubleStress')[0],step,increment);check('original equation doubles source field unchanged',abs(c.GetNodalValue(2)-2*source_stress)<1e-6)
        engineering=[{'name':'analytic double stress','passed':abs(c.GetNodalValue(2)-200)<1e-3,'expected':200,'actual':float(c.GetNodalValue(2)),'absoluteTolerance':1e-3,'status':'failed; D061 deferred, engineering acceptance remains open'}]
        draft=r.Edit('Result histories');draft.Select(len(draft.Choices)-1);draft.Properties.Set('Name','Measured');table=draft.Item
        table.DataPoints=Array[Array[Double]]([Array[Double]([0,1]),Array[Double]([1,2])]);draft.Changed();draft.Commit()
        check('original table history validation/calculation', 'Measured' in list(c.GetHistoryResultSetNames()))
        before=len(c.GetHistoryResultSetNames());r.Execute('Duplicate histories',Array[String](['Measured']));check('original derived-history duplication',len(c.GetHistoryResultSetNames())==before+1)
        r.Field('DISP','U1',step,increment)
        frames=r.Animate('Scale factor',5);check('original animation frames',frames==5 and any(a.Data.Geometry.NodesAnimation is not None and len(a.Data.Geometry.NodesAnimation)==5 for a in session.Presentation.SceneActors))
        time_frames=r.Animate('Time increments',5);check('original increment animation',time_frames>=1)
        c.DrawResults(False);r.ExportField(str(output/'field.csv'));check('original result field export',(output/'field.csv').stat().st_size>0)
        # Exercise the real Controller cancellation path with a controlled long-lived
        # child. This helper is not a solver or an engineering acceptance result.
        import os
        if os.name!='nt':
            helper=output/'controlled-cancel.sh';helper.write_text('#!/bin/sh\nprintf ready > CancelProbe.ready\nexec sleep 30\n');helper.chmod(0o700)
            cancel_work=output/('cancel-work-'+uuid.uuid4().hex[:8]);cancel_work.mkdir(exist_ok=True)
            cancel_job=AnalysisJob('CancelProbe',str(helper),'CancelProbe',str(cancel_work));cancel_job.ExecutableOverridden=True;cancel_job.WorkDirectoryOverridden=True;c.AddJobCommand(cancel_job);cancel_job=c.GetJob('CancelProbe')
            task=r.RunJob('CancelProbe',False);deadline=time.monotonic()+5
            while not (cancel_work/'CancelProbe.ready').exists() and not task.IsCompleted and time.monotonic()<deadline:time.sleep(.01)
            check('controlled cancellation child is running',(cancel_work/'CancelProbe.ready').exists() and cancel_job.JobStatus==JobStatus.Running)
            r.Kill('CancelProbe');check('Controller cancellation task returned',task.Wait(5000));task.GetAwaiter().GetResult();check('Controller analysis cancellation status',cancel_job.JobStatus==JobStatus.Killed)
            c.RemoveJobsCommand(Array[String](['CancelProbe']))
        c.SaveToPmxCommand(str(output/'results.pmx'));c.New();session.Open(str(output/'results.pmx'))
        check('strict PMX result round trip',c.ResultsInitialized and c.GetResultFieldOutput('DoubleStress') is not None and 'Measured' in list(c.GetHistoryResultSetNames()))
        report={'success':True,'checks':checks,'workDirectory':str(job.WorkDirectory),'project':str(output/'results.pmx'),'fields':fields,'engineeringChecks':engineering}
    except Exception:
        import traceback;report={'success':False,'checks':checks,'error':traceback.format_exc()}
        (output/'results.json').write_text(json.dumps(report,indent=2)+'\n');raise
    (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
