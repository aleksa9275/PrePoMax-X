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
add('FrmDistribution FrmAmplitude','X/UI/authoring_widgets.py','X/UI/Workbench/OriginalFormRules.g.cs','Full selection convenience, property focus/tab sequence, sizing and per-subtype interaction matrix require original-app comparison.')
add('FrmMaterial FrmSurfaceInteraction FrmStepControls FrmEquationParameters','X/UI/authoring_widgets.py','X/UI/Workbench/MaterialEditSession.cs; X/UI/Workbench/InteractionEditSession.cs','Core original properties and tables available; complete preview/simple-editor, curve-grid, property-menu and keyboard/focus comparison pending.')
add('','X/UI/geometry_widgets.py','X/UI/Workbench/OriginalGeometryRules.g.cs','Factories/validation/commands reused. Full picked-region conveniences, hover/preview/reset modes, all native backends and keyboard/focus acceptance pending.')
add('FrmBoundaryLayer FrmCaptureViewport FrmContactPair FrmElementSet FrmMergeCoincidentNodes FrmMirror FrmModelProperties FrmNodeSet FrmOffsetFace FrmPartProperties FrmRemeshingParameters FrmRepairGeometry FrmRotate FrmScale FrmSplitPeriodicFaces FrmSurface FrmSurfaceOperation FrmThickenShellMesh FrmTranslate FrmBC FrmConstraint FrmDefinedField FrmFieldOutput FrmHistoryOutput FrmInitialCondition FrmLoad FrmMeshSetupItem FrmNewModel FrmSection FrmSplitSolid FrmStep FrmSplitShell FrmCoordinateSystem FrmElementQuality FrmExportFileWithProperties FrmReferencePoint FrmSplitPartMeshUsingSurface FrmViewObjectProperties FrmSelectItemSet','X/UI/Workbench/OriginalForms (original form class compiled whole: X/UI/generate-original-forms.py); X/UI/original_forms.py renderer','X/UI/FormsCompat (headless WinForms control model); X/UI/Workbench/OriginalForms/OriginalFormHost.g.cs (FrmMain form hosting)','Original class, designer and handlers run unchanged; forms_gui_probe opens every FrmMain entry point at the designer geometry and runs edit/OK - New/Cancel rules (Mac ARM64). Side-by-side comparison with the original application, Linux/Windows runs and the property-grid autocomplete popup remain pending.')
add('FrmAnalyzeGeometry','X/UI/geometry_workbench.py','X/UI/Workbench/GeometrySession.cs','Representative measurement/highlight workflow available; full original control/input matrix pending.')
add('FrmAnalysis FrmMonitor FrmResultFieldOutput FrmResultHistoryOutput FrmViewResultHistoryOutput','X/UI/results_widgets.py; X/UI/history_widgets.py','X/UI/Workbench/OriginalResultsRules.g.cs','Original jobs/derived tools/data paths available; full complex/all-analysis/per-component matrix and original grid/plot interaction acceptance pending.')
add('FrmExplodedView FrmSectionView FrmTransformation','X/UI/presentation_widgets.py','X/UI/Workbench/PresentationEditSession.cs; X/UI/Workbench/OriginalResultsRules.g.cs','Original property rules available; complete preview/selection/animation/control comparison and section/picking matrices pending.')
add('FrmFollowerView FrmUserVew','X/UI/application_widgets.py; X/UI/application_workbench.py','X/UI/Workbench/OriginalApplicationRules.g.cs; X/UI/Workbench/OriginalFollowerCamera.g.cs','Original parameter/camera rules reused; full frame/input/lifecycle comparison pending.')
add('FrmEditCommands FrmCalculixKeywordEditor FrmMaterialLibrary FrmSettings FrmGetEnvVars','X/UI/application_widgets.py; X/UI/authoring_widgets.py','X/UI/Workbench/OriginalApplicationRules.g.cs; X/UI/Workbench/OriginalKeywordRules.g.cs','Original state/formats/rules reused with toolkit-neutral adapters; exhaustive row/context/clipboard/focus and cross-platform original-app comparison pending.')
add('FrmQuery FrmFind FrmSearchContactPairs','X/UI/application_workbench.py; X/UI/application_widgets.py','X/UI/Workbench/OriginalApplicationRules.g.cs; X/UI/Workbench/ContactSearchSession.cs','Original query calculations/search classes reused. Original query calculations, search, merge/highlight and rectangle/angle pickers connected; full subtype/input comparison pending.')
add('FrmAnimation','X/UI/results_workbench.py','PrePoMax/Forms/64_CaptureViewport/CaptureViewportProperties.cs','PNG/clipboard/magnification and portable AVI/OGV paths connected; Windows codec-chooser and full capture/video option/layout equivalence pending.')
add('FrmGetColor FrmGetValue FrmSelectEntity FrmRegenerate','X/UI/application_workbench.py; X/UI/authoring_widgets.py; X/UI/geometry_widgets.py','Original converters, PropertyDescriptors, Controller and Selection graph','Common Qt dialogs provide core actions. Box/angle/ID selection, nested original property inspection and regeneration options connected; exhaustive filters/input/focus comparison remains pending.')
add('FrmMain FrmPythonStop','X/UI/workbench.py; X/UI/application_workbench.py','Original Controller/Python engine/Rpc/Mcp; X/UI/Workbench/OriginalAdvisor.g.cs','Core menus/tree/side-panels/commands/automation connected; complete menu/control/shortcut/drag-drop/navigation/focus/DPI acceptance pending.')
add('FrmSplash','X/UI/workbench.py','Original engineering assemblies','Original splash artwork and native startup/about/home/sponsor links connected; full timing/layout/input comparison pending.')
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
