#!/usr/bin/env python3
"""Audit every original form and designer control; availability is not acceptance."""
import argparse,hashlib,json,re,subprocess,importlib.util
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--extractor',type=Path,default=H/'FormSourceGen/bin/Release/net10.0/FormSourceGen.dll');p.add_argument('--output',type=Path,default=R/'.project/reports/phase-c5-ui-audit.json');p.add_argument('--check',action='store_true');a=p.parse_args()
spec=importlib.util.spec_from_file_location('inventory',R/'.project/scripts/parity-inventory.py');inventory=importlib.util.module_from_spec(spec);spec.loader.exec_module(inventory)
forms=inventory.sections()[2][1];wanted={n for values in forms.values() for n in values}
raw=json.loads(subprocess.check_output(['dotnet',str(a.extractor),str(R),'--audit'],text=True));sources={name:[] for name in wanted}
for entry in raw:
 for c in entry['classes']:
  if c['name'] in wanted:sources[c['name']].append((entry,c))
# All mappings name reviewable source files. The control audit deliberately keeps
# unmatched original event handlers explicit rather than interpreting an adapter as a pass.
mapping={}
def add(names,adapter,reuse,remaining):
 for name in names.split():mapping[name]={'adapter':adapter,'reuse':reuse,'remaining':remaining}
add('FrmBoundaryLayer FrmCaptureViewport FrmContactPair FrmElementSet FrmMergeCoincidentNodes FrmMirror FrmModelProperties FrmNodeSet FrmOffsetFace FrmPartProperties FrmRemeshingParameters FrmRepairGeometry FrmRotate FrmScale FrmSplitPeriodicFaces FrmSurface FrmSurfaceOperation FrmThickenShellMesh FrmTranslate FrmBC FrmConstraint FrmDefinedField FrmFieldOutput FrmHistoryOutput FrmInitialCondition FrmLoad FrmMeshSetupItem FrmNewModel FrmSection FrmSplitSolid FrmStep FrmSplitShell FrmCoordinateSystem FrmElementQuality FrmExportFileWithProperties FrmReferencePoint FrmSplitPartMeshUsingSurface FrmViewObjectProperties FrmSelectItemSet FrmDistribution FrmAmplitude FrmResultFieldOutput FrmResultHistoryOutput FrmGetColor FrmGetValue FrmRegenerate FrmSelectEntity FrmEquationParameters FrmExplodedView FrmFollowerView FrmSectionView FrmUserVew FrmAnalyzeGeometry FrmMaterial FrmMaterialLibrary FrmSurfaceInteraction FrmSearchContactPairs FrmStepControls FrmGetEnvVars FrmSettings FrmQuery FrmFind FrmAnalysis FrmMonitor FrmAnimation FrmViewResultHistoryOutput FrmTransformation FrmSplash','X/UI/Workbench/OriginalForms (original form class compiled whole: X/UI/generate-original-forms.py); X/UI/original_forms.py renderer','X/UI/FormsCompat (headless WinForms control model incl. DataGridView/BindingSource, TreeView, ZedGraph panes); X/UI/Workbench/OriginalForms/OriginalFormHost.g.cs (FrmMain form hosting)','Original class, designer and handlers run unchanged (data-grid forms with the original DataGridViewCopyPaste and FrmDiagramView); forms_gui_probe opens every FrmMain entry point at the designer geometry and runs edit/OK - New/Cancel rules and the amplitude grid edit/copy/paste/plot/delete workflow; results_gui_probe drives the result field/history forms and the original FrmAnalysis/FrmMonitor with a real solve; the C11 child-window forms and dialogs open through their FrmMain entry points (CodersLabTreeView, modal value/colour/parameter/library dialogs) (Mac ARM64). Side-by-side comparison with the original application, Linux/Windows runs, the autocomplete popup look and owner-drawn paint handlers remain pending.')
add('FrmEditCommands FrmCalculixKeywordEditor','X/UI/application_widgets.py; X/UI/authoring_widgets.py','X/UI/Workbench/OriginalApplicationRules.g.cs; X/UI/Workbench/OriginalKeywordRules.g.cs','Original state/formats/rules reused with toolkit-neutral adapters; exhaustive row/context/clipboard/focus and cross-platform original-app comparison pending.')
add('FrmMain FrmPythonStop','X/UI/workbench.py; X/UI/application_workbench.py','Original Controller/Python engine/Rpc/Mcp; X/UI/Workbench/OriginalAdvisor.g.cs','Core menus/tree/side-panels/commands/automation connected; complete menu/control/shortcut/drag-drop/navigation/focus/DPI acceptance pending.')
if set(mapping)!=wanted:raise ValueError({'missingMappings':sorted(wanted-set(mapping)),'unexpectedMappings':sorted(set(mapping)-wanted)})
records=[]
for name in sorted(wanted):
 entries=sources[name];controls=[];events=[];methods=[];files=[]
 for entry,c in entries:
  path=R/entry['file'];files.append({'path':entry['file'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
  if entry['file'].endswith('.Designer.cs'):controls+=c['controls']
  events+=c['events'];methods+=c['methods']
 record={'form':name,**mapping[name],'compiledWhole':'OriginalForms' in mapping[name]['adapter'],'originalSources':files,'declaredDesignerFields':controls,'eventSubscriptions':events,'methods':methods,'fullFormAccepted':False,'controlComparison':'pending'}
 records.append(record)
report={'schemaVersion':1,'scope':'Complete source inventory and explicit adapter/gap audit. Static source coverage is not behavioral acceptance. Forms compiled whole run the original class on the headless control model; V (original-app comparison) is pending for all 72.','forms':records,'counts':{'forms':len(records),'designerFields':sum(len(r['declaredDesignerFields']) for r in records),'eventSubscriptions':sum(len(r['eventSubscriptions']) for r in records),'fullFormsAccepted':0,'compiledWhole':sum(1 for r in records if r['compiledWhole'])}}
text=json.dumps(report,indent=2)+'\n';out=a.output.resolve()
if a.check:
 if not out.exists() or out.read_text()!=text:raise SystemExit('The C5 form/control audit is stale.')
else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
print(json.dumps(report['counts']))
