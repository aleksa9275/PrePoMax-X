using System.Reflection;
using CaeGlobals;
using CaeModel;
using PrePoMax;
using PrePoMaxX.Persistence;

RuntimeInitialization.SetCultureAndLanguage();
string testRoot=Environment.GetEnvironmentVariable("PREPOMAXX_PHASE_B_OUTPUT")??Path.Combine(Path.GetTempPath(),"prepomaxx-phase-b");
Directory.CreateDirectory(testRoot);
Assembly[] assemblies={typeof(Controller).Assembly,typeof(FeModel).Assembly,typeof(CaeMesh.FeMesh).Assembly,typeof(CaeResults.FeResults).Assembly,typeof(CaeJob.AnalysisJob).Assembly,typeof(NamedClass).Assembly,typeof(vtkControl.vtkMaxActorData).Assembly,typeof(UserControls.SidePanelsState).Assembly,typeof(System.Windows.Forms.DialogResult).Assembly};
if(args.Length>0 && args[0]=="--catalog")
{
 foreach(var a in assemblies)
  foreach(var t in a.GetTypes().Where(t=>t.IsSerializable && !t.IsDefined(typeof(System.Runtime.CompilerServices.CompilerGeneratedAttribute),false) && !typeof(Delegate).IsAssignableFrom(t)).OrderBy(t=>t.FullName,StringComparer.Ordinal))Console.WriteLine(a.GetName().Name+"|"+t.FullName);
 foreach(var a in assemblies)foreach(var t in a.GetTypes().Where(t=>t.IsInterface).OrderBy(t=>t.FullName,StringComparer.Ordinal))Console.WriteLine("@"+a.GetName().Name+"|"+t.FullName);
 foreach(var t in typeof(NamedClass).Assembly.GetTypes().Where(t=>typeof(System.ComponentModel.TypeConverter).IsAssignableFrom(t)).OrderBy(t=>t.FullName,StringComparer.Ordinal))Console.WriteLine("@"+t.Assembly.GetName().Name+"|"+t.FullName);
 return;
}
var names=File.ReadAllLines(Path.Combine(Directory.GetCurrentDirectory(),"X/Persistence/allowed-types.txt"));
var policy=new NrbfTypePolicy(assemblies,names);
BinarySerialization.Factory=()=>new RestrictedNrbfSerializer(policy);
try
{
 if(args.Length>0 && args[0]=="--persistence")Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new {success=true,checks=PersistenceChecks.Run(policy)}));
 var material=new Material("Steel");
 var clone=material.DeepClone();
 if(ReferenceEquals(material,clone)||clone.Name!="Steel")throw new Exception("Clone failed");
 Console.WriteLine("Material clone passed");
 var form=new FrmMain();
 form.ScreenUpdating=true;form.RenderingOn=true;
 form.Query=(name,values)=> name switch {
  "SetStateWorking"=>true,
  "GetTreeExpandCollapseState"=>new bool[][] {Array.Empty<bool>(),Array.Empty<bool>(),Array.Empty<bool>()},
  "GetStableTreeExpandCollapseState"=>new Dictionary<string,bool>[] {new(),new(),new()},
  "GetSidePanelsState"=>new UserControls.SidePanelsState(),
  "Add3DCells" or "Add3DNodes"=>new vtkControl.vtkMaxActor((vtkControl.vtkMaxActorData)values[0]),
  "ContainsActor"=>false,
  _=>throw new NotSupportedException("Query: "+name)
 };
 form.Presentation=(name,values)=> {if(name is "WriteErrorToOutput")Console.Error.WriteLine(values[0]);};
 var controller=new Controller(form);
 Console.WriteLine("Controller initialized");
 SettingsContainer.IsSaveDisabled=true;
 controller.New();
 controller.AddMaterialCommand(new Material("Steel"));
 if(!controller.Model.Materials.ContainsKey("Steel"))throw new Exception("Material command failed");
 controller.UndoHistory(PrePoMax.Commands.RegenerateTypeEnum.All);
 if(controller.Model.Materials.ContainsKey("Steel"))throw new Exception("Undo failed");
 controller.RedoHistory();
 if(!controller.Model.Materials.ContainsKey("Steel"))throw new Exception("Redo failed");
 Directory.CreateDirectory(testRoot);
 controller.SaveToPmxCommand(Path.Combine(testRoot,"material.pmx"));
 controller.New();
 controller.Open(Path.Combine(testRoot,"material.pmx"));
 if(!controller.Model.Materials.ContainsKey("Steel"))throw new Exception("PMX roundtrip failed");
 Console.WriteLine("Material command, undo/redo, PMX roundtrip passed");
 if(args.Length>0 && args[0]=="--workflow")
 {
  string input=Path.GetFullPath(args[1]);string output=Path.GetFullPath(args[2]);Directory.CreateDirectory(output);
  controller.New();controller.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C);controller.ImportFileCommand(input,false);
  if(controller.Model.Mesh==null || controller.Model.Mesh.Elements.Count==0)throw new Exception("INP import failed");
  int elements=controller.Model.Mesh.Elements.Count;
  controller.ExportToCalculixCommand(Path.Combine(output,"before.inp"));
  controller.SaveToPmxCommand(Path.Combine(output,"project.pmx"));
  controller.New();controller.Open(Path.Combine(output,"project.pmx"));
  if(controller.Model.Mesh.Elements.Count!=elements)throw new Exception("PMX mesh roundtrip failed");
  controller.ExportToCalculixCommand(Path.Combine(output,"after.inp"));
  Console.WriteLine("Original Controller import/export/PMX: "+elements+" elements, "+controller.GetActiveCommands().Count+" commands");
 }
 if(args.Length>0 && args[0]=="--mesh")
 {
  NativeTools.Configure(Path.GetFullPath(args[1]));
  string work=Path.GetFullPath(args[2]);Directory.CreateDirectory(work);controller.RegenerationWorkDirectory=work;
  controller.New();controller.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C);
  controller.ImportFileCommand(Path.GetFullPath(args[3]),false);
  var part=controller.Model.Geometry.Parts.Values.First();int[] ids={part.PartId};
  var selection=new Selection {CurrentView=(int)ViewGeometryModelResults.Geometry,SelectItem=vtkSelectItem.Part};
  selection.Add(new SelectionNodeIds(vtkSelectOperation.None,false,ids));
  var sizing=new CaeMesh.MeshingParameters("Linear") {RelativeSize=false,MaxH=5,MinH=0,SecondOrder=false,CreationIds=ids,CreationData=selection};
  controller.AddMeshSetupItemCommand(sizing);
  var tetrahedra=new CaeMesh.TetrahedralGmsh("Tetrahedra") {CreationIds=ids,CreationData=selection};
  controller.AddMeshSetupItemCommand(tetrahedra);
  if(!controller.CreateMeshesCommand(new[]{part.Name}))throw new Exception("Controller meshing failed");
  if(controller.Model.Mesh.Elements.Count==0)throw new Exception("Mesher returned no elements");
  controller.SaveToPmxCommand(Path.Combine(work,"cad.pmx"));
  int elements=controller.Model.Mesh.Elements.Count;
  controller.New();controller.Open(Path.Combine(work,"cad.pmx"));
  if(controller.Model.Mesh.Elements.Count!=elements)throw new Exception("CAD/mesh roundtrip failed");
  Console.WriteLine("Original Controller native CAD/Gmsh/PMX passed: "+elements+" elements");
 }
 if(args.Length>0 && args[0]=="--exports")
 {
  NativeTools.Configure(Path.GetFullPath(args[1]));
  PrePoMax.Python.PythonEngineManager.NativeRuntimeProfile=Path.GetFullPath(args[2]);
  controller.New();controller.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C);
  controller.ImportFileCommand(Path.GetFullPath(".project/reports/windows-reference/fixtures/definitions.inp"),false);
  controller.CurrentView=ViewGeometryModelResults.Model;controller.DrawModel(false);
  form.SetCurrentEdgesVisibilities(vtkControl.vtkEdgesVisibility.NoEdges);
  string file=Path.Combine(testRoot,"cube.3mf");
  controller.ExportTo3mfCommand(new Export3mfFileProperties {FileName=file});
  using(var archive=System.IO.Compression.ZipFile.OpenRead(file))
  {
   var entry=archive.GetEntry("3D/3dmodel.model")??throw new Exception("3MF model is missing");
   using var stream=entry.Open();var xml=System.Xml.Linq.XDocument.Load(stream);
   if(xml.Descendants().Count(e=>e.Name.LocalName=="triangle")!=12)throw new Exception("3MF triangle count differs");
  }
  var texture=new vtkControl.vtkMaxLookupTable {Colors=new[]{System.Drawing.Color.Red,System.Drawing.Color.Blue}};
  texture.WriteAsTexture(2,4,Path.Combine(testRoot,"texture.png"));
  using var spatial=form.EnableNativeSpatialQueries();string part=controller.Model.Mesh.Parts.Keys.First();
  form.SmoothPart(part,0,Path.Combine(testRoot,"smooth.stl"));
  form.CropPartWithCube(part,0.5,0.5,0.5,4,Path.Combine(testRoot,"crop-cube.stl"));
  form.CropPartWithCylinder(part,100,Path.Combine(testRoot,"crop-cylinder.stl"));
  foreach(string name in new[]{"smooth.stl","crop-cube.stl","crop-cylinder.stl"})
   if(new FileInfo(Path.Combine(testRoot,name)).Length<84)throw new Exception("Native geometry output is empty: "+name);
  Console.WriteLine("Original 3MF command, portable texture and native surface tools passed");
 }
 if(args.Length>0 && args[0]=="--spatial")
 {
  PrePoMax.Python.PythonEngineManager.NativeRuntimeProfile=Path.GetFullPath(args[1]);
  controller.New();controller.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C);
  controller.ImportFileCommand(Path.GetFullPath(".project/reports/windows-reference/fixtures/definitions.inp"),false);
  controller.CurrentView=ViewGeometryModelResults.Model;controller.DrawModel(false);
  using var spatial=form.EnableNativeSpatialQueries();spatial.SelectionPrecision=0.01;
  string part=controller.Model.Mesh.Parts.Keys.First();
  form.GetGeometryPickProperties(new double[]{1,0.5,0.5},out int element,out int[] edge,out int[] face,new[]{part});
  if(element!=1 || face.Length!=3 || !face.All(n=>new[]{2,3,6,7}.Contains(n)))throw new Exception("Native face pick failed");
  form.GetClosestCellsOnParts(new double[]{2,0.5,0.5},new[]{part},out double[] distances,out double[][] normals);
  if(Math.Abs(distances[0]-1)>1e-12 || normals[0]==null)throw new Exception("Native closest-cell query failed");
  double[][] planes={new double[]{-0.1,0,0,-1,0,0},new double[]{1.1,0,0,1,0,0},new double[]{0,-0.1,0,0,-1,0},new double[]{0,1.1,0,0,1,0},new double[]{0,0,-0.1,0,0,-1},new double[]{0,0,1.1,0,0,1}};
  form.GetPointAndCellIdsInsideFrustum(planes,new[]{part},out int[] nodes,out int[] cells);
  if(nodes.Length!=8 || cells.Length!=1)throw new Exception("Native volume-frustum query failed");
  controller.SaveToPmxCommand(Path.Combine(testRoot,"spatial-baseline.pmx"));
  int partId=controller.Model.Mesh.Parts[part].PartId;
  var picked=new SelectionNodeMouse(new double[]{1,0.5,0.5},new double[]{-1,0,0},null,false,vtkSelectOperation.None,new[]{partId},new[]{new double[]{0,0,0}},vtkSelectBy.Surface,0) {Precision=0.01};
  var selection=new Selection {CurrentView=(int)ViewGeometryModelResults.Model,SelectItem=vtkSelectItem.Node};selection.Add(picked);
  int[] labels=controller.GetIdsFromSelection(selection);
  if(!labels.Order().SequenceEqual(new[]{2,3,6,7}))throw new Exception("Original mouse selection did not resolve the complete face");
  var nodeSet=new CaeMesh.FeNodeSet("PickedFace",labels) {CreationData=selection,CreationIds=labels};
  controller.AddNodeSetCommand(nodeSet);
  controller.AddMaterialCommand(new Material("Extra"));
  controller.UndoHistory(PrePoMax.Commands.RegenerateTypeEnum.All);
  if(controller.Model.Materials.ContainsKey("Extra") || !controller.Model.Mesh.NodeSets["PickedFace"].Labels.Order().SequenceEqual(new[]{2,3,6,7}))throw new Exception("Replay from saved state did not preserve the picked node set");
  controller.RedoHistory();
  if(!controller.Model.Materials.ContainsKey("Extra"))throw new Exception("Redo after saved-state replay failed");
  controller.ExportToStl(new[]{part},Path.Combine(testRoot,"cube.stl"));
  Console.WriteLine("Native spatial queries, original mouse selection, saved-state replay and STL passed");
 }
 if(args.Length>0 && args[0]=="--solve")
 {
  NativeTools.EnablePlatformExecutables();
  string solver=SolverRuntime.Validate(Path.GetFullPath(args[1]),args[2],Path.GetFullPath(args[3]));
  string work=Path.GetFullPath(args[4]);Directory.CreateDirectory(work);
  controller.New();controller.SetNewModelPropertiesCommand(ModelSpaceEnum.ThreeD,UnitSystemType.MM_TON_S_C);
  controller.ImportFileCommand(Path.GetFullPath(".project/reports/windows-reference/fixtures/definitions.inp"),false);
  var settings=controller.Settings;settings.Solver.CalculixExe=solver;settings.Solver.WorkDirectoryForSettingsOnly=work;
  settings.Solver.CalculixDefaultSolverType=SolverTypeEnum.Spooles;controller.Settings=settings;
  foreach(var step in controller.Model.StepCollection.StepsList)step.SolverType=SolverTypeEnum.Spooles;
  var job=new CaeJob.AnalysisJob("cube",solver,"cube",work);
  controller.AddJobCommand(job);
  if(!controller.PrepareAndRunJobCommand(job.Name,false,true,30000))throw new Exception("Controller refused job execution");
  if(controller.GetJob(job.Name).JobStatus!=CaeJob.JobStatus.OK)throw new Exception("Job did not finish: "+controller.GetJob(job.Name).JobStatus);
  controller.Open(Path.Combine(work,"cube.frd"));
  if(!controller.ResultsInitialized)throw new Exception("Controller did not initialize results");
  controller.SaveToPmxCommand(Path.Combine(work,"results.pmx"));
  controller.New();controller.Open(Path.Combine(work,"results.pmx"));
  if(!controller.ResultsInitialized)throw new Exception("Saved results did not reopen");
  Console.WriteLine("Original Controller solve/results/PMX passed");
 }
 if(args.Length>0 && args[0]=="--python")
 {
  PrePoMax.Python.PythonEngineManager.NativeRuntimeProfile=Path.GetFullPath(args[1]);
  var result=controller.RunPythonScript("print('phase-b Python engine')\nprint(pmx.model.name)\n");
  Console.WriteLine(result.Output);if(!string.IsNullOrEmpty(result.Error))throw new Exception(result.GetErrorText());
 }
 if(args.Length>0 && args[0]=="--open")
 {
  controller.Open(Path.GetFullPath(args[1]));
  Console.WriteLine("Opened: "+controller.Model.Name+"; materials="+controller.Model.Materials.Count+"; elements="+controller.Model.Mesh?.Elements.Count);
 }
}
catch(Exception error) {Console.Error.WriteLine(error);Environment.ExitCode=1;}
