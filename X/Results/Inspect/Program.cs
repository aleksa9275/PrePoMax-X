using System.Text.Json;
using CaeResults;
if(args.Length!=2||(args[0]!="inspect-frd"&&args[0]!="inspect-dat")){Console.Error.WriteLine("Usage: PrePoMaxX.InspectResults (inspect-frd <completed-static.frd> | inspect-dat <static.dat>)");return 2;}
try
{
 if(args[0]=="inspect-dat")
 {
  var dat=DatFileReader.ReadStaticSnapshot(args[1]);
  Console.WriteLine(JsonSerializer.Serialize(new{success=true,dat.SourceSha256,dat.DataSetCount,dat.ExcludedBasisTables,quantityUnits="as stored; no unit conversion or inference",completionEstablished=false,fullResultsPreprocessing=false,solverExecuted=false,
  histories=dat.Histories.Select(h=>new{h.SetName,h.BaseSetName,h.FieldName,h.ComponentName,h.StepId,h.Id,h.IntegrationPoint,h.IncrementIds,h.Entries.Local,h.Entries.Unit,time=h.Entries.Time,values=h.Entries.Values})}));return 0;
 }
 var snapshot=FrdFileReader.ReadStaticSnapshot(args[1]);
 var result=new{success=true,snapshot.SourceSha256,snapshot.UnitSystemHeader,snapshot.ModelSpace,snapshot.OriginalElementCount,snapshot.AxisymmetricScalingApplied,emptyResultMesh=snapshot.Nodes.Count==0,quantityUnits="stored units; original axisymmetric field scaling where indicated",fullResultsPreprocessing=false,solverExecuted=false,
 nodes=snapshot.NodeIdsInValueOrder.Select(id=>new{id,x=snapshot.Nodes[id].X,y=snapshot.Nodes[id].Y,z=snapshot.Nodes[id].Z}),
 elements=snapshot.Elements.Values.Select(e=>new{id=e.Id,type=e.GetType().Name,vtkCellType=e.GetVtkCellType(),nodeIds=e.NodeIds,vtkNodeIds=e.GetVtkNodeIds()}),nodeIdsInValueOrder=snapshot.NodeIdsInValueOrder,
 solverElements=snapshot.SolverElements.Values.Select(e=>new{id=e.Id,type=e.GetType().Name,nodeIds=e.NodeIds}),
 fields=snapshot.Fields.Select(f=>new{name=f.Data.Name,stepId=f.Data.StepId,incrementId=f.Data.StepIncrementId,time=f.Data.Time,stepType=f.Data.StepType.ToString(),mode=f.Data.ModeNumber,components=f.Field.GetComponentNames().ToDictionary(n=>n,n=>f.Field.GetComponentValues(n))})};
 Console.WriteLine(JsonSerializer.Serialize(result));return 0;
}
catch(Exception e)when(e is IOException or InvalidDataException or ArgumentException or NotSupportedException or FormatException or OverflowException or IndexOutOfRangeException or AggregateException or CaeGlobals.CaeException)
{Console.Error.WriteLine(JsonSerializer.Serialize(new{success=false,solverExecuted=false,error=e.GetBaseException().Message}));return 1;}
