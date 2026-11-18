#!/usr/bin/env python3
"""Compile the original PrePoMax form classes whole (D062).

Copies the original form sources (class, designer partial and base forms) into
X/UI/Workbench/OriginalForms/ so they build against the headless control model
in X/UI/FormsCompat. Only the reviewed rewrites below are applied; each output
records its source path and SHA256, and --check fails when an original changed
or an output was edited. Nothing else is paraphrased or reimplemented.
"""
import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'Workbench/OriginalForms'

# Base forms and original controls compiled whole.
BASE = [
    'UserControls/Forms/FrmProperties.cs', 'UserControls/Forms/FrmProperties.Designer.cs',
    'UserControls/Forms/FrmPropertyListView.cs', 'UserControls/Forms/FrmPropertyListView.Designer.cs',
    'UserControls/Forms/PrePoMaxChildForm.cs',
    'UserControls/ListView/ListViewWithSelection.cs', 'UserControls/ListView/ListViewWithSelection.Designer.cs',
    'UserControls/TextBoxes/UnitAwareTextBox.cs', 'UserControls/TextBoxes/UnitAwareTextBox.Designer.cs',
    'UserControls/TextBoxes/MultiIntegerTextBox.cs', 'UserControls/TextBoxes/MultiIntegerTextBox.Designer.cs',
    'PrePoMax/Forms/IFormBase.cs', 'PrePoMax/Forms/00_Common/ViewUnitSystem.cs',
    'PrePoMax/Selection/ItemSet/ItemSetDataEditor.cs', 'PrePoMax/Selection/ItemSet/SinglePointDataEditor.cs',
    'PrePoMax/Forms/00_Common/FrmSelectItemSet.cs', 'PrePoMax/Forms/00_Common/FrmSelectItemSet.Designer.cs',
    # Data grid forms (C10): the grid with copy/paste/plot and the plot window
    'UserControls/Forms/FrmPropertyDataListView.cs', 'UserControls/DataGridView/DataGridViewCopyPaste.cs',
    'UserControls/DiagramView/DiagramView.cs', 'UserControls/DiagramView/DiagramView.Designer.cs',
    # Child-window forms and dialogs (C11): their original controls
    'UserControls/Trees/CoderslabTreeView.cs',
    'UserControls/Trees/OrderedDictionary.cs',
    'UserControls/GroupBoxes/CollapsableGroupBox.cs', 'UserControls/GroupBoxes/CollapsableGroupBox.Designer.cs',
    'UserControls/TextBoxes/NumericTextBox.cs', 'UserControls/TextBoxes/NumericTextBox.Designer.cs',
    'UserControls/AnalysisProgressView.cs', 'UserControls/AnalysisProgressView.Designer.cs',
    'PrePoMax/Forms/00_Common/ViewDoubleValue.cs', 'PrePoMax/Forms/00_Common/ViewColor.cs',
    'PrePoMax/Forms/01_Edit/DataGridViewExtension.cs', 'PrePoMax/Forms/45_SurfaceInteraction/ListViewItemComparer.cs',
    'UserControls/MessageBoxes/AutoClosingMessageBox.cs', 'PrePoMax/Forms/61_Settings/EnvVarsUIEditor.cs',
    # 3.0.1 composite shell section (FrmSection Layers tab): the layup diagram panel
    'UserControls/SidePanel/DoubleBufferedPanel.cs',
    # Code editor forms (C12): the original text boxes on the FastColoredTextBox model
    'UserControls/TextBoxes/CalculixKeywordTextBox/CalculixInpTextBox.cs',
    'UserControls/TextBoxes/CalculixKeywordTextBox/ICalculixInpTextBox.cs',
    'UserControls/TextBoxes/PythonEditorTextBox/PythonEditorFastTextBox.cs',
    'UserControls/TextBoxes/PythonEditorTextBox/PythonEditorTextBox.cs',
    'UserControls/TextBoxes/PythonTextBox/PythonTextBoxCompletionHelper.cs',
    'UserControls/TextBoxes/PythonTextBox/PythonTextBoxAutocompleteEventArgs.cs',
    'UserControls/TextBoxes/PythonTextBox/PythonTextBoxCommandEventArgs.cs',
    'UserControls/TextBoxes/PythonTextBox/PythonTextBoxAutocompleteMenuHelper.cs',
    'UserControls/TextBoxes/PythonTextBox/PythonTextBoxScriptAnalyzer.cs',
    'UserControls/TextBoxes/PythonTextBox/PythonTextBoxSyntaxHighlighter.cs',
]
# Forms derived from FrmProperties / FrmPropertyListView / FrmPropertyDataListView.
FORMS = '''FrmBoundaryLayer FrmCaptureViewport FrmContactPair FrmElementSet FrmMergeCoincidentNodes FrmMirror
FrmModelProperties FrmNodeSet FrmOffsetFace FrmPartProperties FrmRemeshingParameters FrmRepairGeometry FrmRotate FrmScale
FrmSplitPeriodicFaces FrmSurface FrmSurfaceOperation FrmThickenShellMesh FrmTranslate FrmBC FrmConstraint FrmDefinedField
FrmFieldOutput FrmHistoryOutput FrmInitialCondition FrmLoad FrmMeshSetupItem FrmNewModel FrmSection FrmMaterialOrientation FrmSplitSolid FrmStep
FrmSplitShell FrmCoordinateSystem FrmElementQuality FrmExportFileWithProperties FrmReferencePoint
FrmSplitPartMeshUsingSurface FrmViewObjectProperties
FrmAmplitude FrmDistribution FrmResultFieldOutput FrmResultHistoryOutput
FrmGetColor FrmGetValue FrmRegenerate FrmSelectEntity FrmEquationParameters FrmExplodedView FrmFollowerView FrmSectionView FrmUserVew FrmAnalyzeGeometry FrmMaterial FrmMaterialLibrary FrmSurfaceInteraction FrmSearchContactPairs FrmStepControls FrmGetEnvVars FrmSettings FrmQuery FrmFind FrmAnalysis FrmMonitor FrmAnimation FrmViewResultHistoryOutput FrmTransformation FrmSplash
FrmCalculixKeywordEditor FrmEditCommands'''.split()

# (pattern, replacement, reason). Applied in order to every file.
REWRITES = [
    (r'new ViewNodeSet\(this, ', 'new ViewNodeSet(',
     'ViewNodeSet.Windows.cs (Windows build only) adds a Form overload that forwards to ViewNodeSet(FeNodeSet).'),
    (r'new System\.Drawing\.Font\(', 'new System.Windows.Forms.FontSpec(',
     'System.Drawing.Font needs GDI+, which .NET 10 provides only on Windows; designer fonts become font descriptions.'),
    (r'System\.ComponentModel\.ComponentResourceManager resources = new System\.ComponentModel\.ComponentResourceManager\(typeof\(\w+\)\)',
     lambda path: f'System.Windows.Forms.ResxResources resources = new System.Windows.Forms.ResxResources("{resx_of(path)}")',
     'Designer images are read from the original .resx by the renderer (base64 image bytes); no resource deserialization.'),
    (r'\(\(System\.Drawing\.Image\)\(resources\.GetObject\(', '((System.Windows.Forms.ImageResource)(resources.GetObject(',
     'A designer image is an ImageResource (System.Drawing.Image needs GDI+).'),
    (r'\(\(System\.Drawing\.Icon\)\(resources\.GetObject\(', '((System.Drawing.Icon)(resources.GetIcon(',
     'Form icons are the application icon in the renderer (System.Drawing.Icon needs GDI+).'),
    (r'(?<![\w.])OrderedDictionary<', lambda path: 'OrderedDictionary<' if path.startswith('UserControls/') else 'CaeGlobals.OrderedDictionary<',
     '.NET 9+ adds System.Collections.Generic.OrderedDictionary<,>; the original CaeGlobals type is named in full.'),
    (r'Image image = new Bitmap\(100, 100\);\n(\s*)Graphics g = Graphics\.FromImage\(image\);\n(\s*//.*\n)(\s*)SizeF textSize = g\.MeasureString\(',
     r'// GDI+ bitmap: not created\n\1// GDI+ graphics: not created\n\2\3SizeF textSize = System.Windows.Forms.TextRenderer.MeasureString(',
     'CollapsableGroupBox measures its caption on a GDI+ bitmap; the renderer\'s font metrics measure it instead.'),
    (r'_drawBrush = new SolidBrush\(ForeColor\);', '_drawBrush = null; // SolidBrush needs GDI+; the renderer paints the caption',
     'CollapsableGroupBox keeps an unused GDI+ brush (SolidBrush needs GDI+ on .NET 10).'),
    (r'\b\w+\.CreateGraphics\(\)\.MeasureString\(', 'System.Windows.Forms.TextRenderer.MeasureString(',
     'Graphics.MeasureString needs GDI+; the text is measured with the renderer\'s font metrics.'),
    (r'\[System\.Runtime\.InteropServices\.DllImport\("user32\.dll", SetLastError = true\)\]\n(\s*)static extern IntPtr FindWindow\(string lpClassName, string lpWindowName\);',
     r'\1static IntPtr FindWindow(string lpClassName, string lpWindowName) => System.Windows.Forms.MessageBox.FindOpen(lpClassName, lpWindowName);',
     'AutoClosingMessageBox finds and closes its box through user32; the toolkit message boxes are found by caption instead.'),
    (r'\[System\.Runtime\.InteropServices\.DllImport\("user32\.dll", CharSet = System\.Runtime\.InteropServices\.CharSet\.Auto\)\]\n(\s*)static extern IntPtr SendMessage\(IntPtr hWnd, UInt32 Msg, IntPtr wParam, IntPtr lParam\);',
     r'\1static IntPtr SendMessage(IntPtr hWnd, UInt32 Msg, IntPtr wParam, IntPtr lParam) => System.Windows.Forms.MessageBox.SendMessage(hWnd, Msg, wParam, lParam);',
     'AutoClosingMessageBox: WM_CLOSE goes to the toolkit message box.'),
    (r'GetScrollPos\(\(int\)this\.Handle, ', 'NativeGetScrollPos(',
     'CodersLabTreeView reads the native scroll position through user32; the TreeView model reports it.'),
    (r'Graphics g = this\.CreateGraphics\(\);', 'System.Windows.Forms.FocusSurface g = new System.Windows.Forms.FocusSurface(this);',
     'CodersLabTreeView draws its focus rectangle with GDI+; the renderer draws the focus the model records.'),
    (r'g\.DrawRectangle\(new Pen\(new SolidBrush\((\w+)\), 1\), ', r'g.DrawRectangle(\1, ',
     'CodersLabTreeView focus rectangle: the colour instead of a GDI+ pen.'),
    # Code editor text boxes (C12): FastColoredTextBox styles take brushes and the control a font
    (r'(?<![\w.])Brushes\.(\w+)', lambda path: r'new FastColoredTextBoxNS.StyleBrush(System.Drawing.Color.\1)' if path.startswith('UserControls/TextBoxes/') else None,
     'System.Drawing.Brushes needs GDI+ (Windows only on .NET 10); a FastColoredTextBox style brush is its colour.'),
    (r'new SolidBrush\(', lambda path: 'new FastColoredTextBoxNS.StyleBrush(' if path.startswith('UserControls/TextBoxes/') else None,
     'SolidBrush needs GDI+; a FastColoredTextBox style brush is its colour.'),
    (r'new Font\(', lambda path: 'new System.Windows.Forms.FontSpec(' if path.startswith('UserControls/TextBoxes/') or 'FrmCalculixKeywordEditor' in path else None,
     'System.Drawing.Font needs GDI+; fonts are font descriptions.'),
    (r'(?m)^using FastColoredTextBoxNS;$', lambda path: 'using FastColoredTextBoxNS; using Range = FastColoredTextBoxNS.Range;' if path.startswith('UserControls/') else None,
     '.NET adds System.Range (net48 has none); FastColoredTextBoxNS.Range is named by an alias on the same line.'),
    (r'(?m)^(\s*(?:private )?)Font (\w+(?: =|;))', lambda path: r'\1System.Windows.Forms.FontSpec \2' if 'FrmCalculixKeywordEditor' in path else None,
     'System.Drawing.Font needs GDI+; the keyword tree\'s emphasized node font is a font description.'),
    (r'\[System\.Runtime\.InteropServices\.DllImport\("user32\.dll"\)\]\n(\s*)public static extern bool LockWindowUpdate\(IntPtr hWndLock\);',
     r'// user32 LockWindowUpdate (rewritten, see header)\n\1public static bool LockWindowUpdate(IntPtr hWndLock) => true; // user32: suspends painting only; the renderer paints after the handler',
     'FrmCalculixKeywordEditor suspends window painting through user32 while it adds a node; the renderer repaints once the handler returns.'),
    (r'public override Font Font', 'public override System.Windows.Forms.FontSpec Font',
     'Control.Font is a font description (System.Drawing.Font needs GDI+).'),
    (r'\[DllImport\("user32\.dll"\)\]\n(\s*)private static extern bool GetKeyboardState\(byte\[\] keyState\);',
     r'// user32 GetKeyboardState (rewritten, see header)\n\1private static bool GetKeyboardState(byte[] keyState) => System.Windows.Forms.KeyboardLayout.GetKeyboardState(keyState);',
     'PythonTextBoxAutocompleteMenuHelper maps a key to its character through user32; the renderer reports the character the platform keyboard layout produced.'),
    (r'\[DllImport\("user32\.dll"\)\]\n(\s*)private static extern uint MapVirtualKey\(uint code, uint mapType\);',
     r'// user32 MapVirtualKey (rewritten, see header)\n\1private static uint MapVirtualKey(uint code, uint mapType) => System.Windows.Forms.KeyboardLayout.MapVirtualKey(code, mapType);',
     'PythonTextBoxAutocompleteMenuHelper: user32 scan code lookup (the platform keyboard layout).'),
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Unicode\)\]\n(\s*)private static extern int ToUnicode\(uint virtualKeyCode, uint scanCode, byte\[\] keyState,\n\s*\[Out, MarshalAs\(UnmanagedType\.LPWStr\)\] StringBuilder receivingBuffer,\n\s*int bufferSize, uint flags\);',
     r'// user32 ToUnicode (rewritten, see header)\n\1//\n\1//\n\1private static int ToUnicode(uint virtualKeyCode, uint scanCode, byte[] keyState, StringBuilder receivingBuffer, int bufferSize, uint flags) => System.Windows.Forms.KeyboardLayout.ToUnicode(virtualKeyCode, keyState, receivingBuffer);',
     'PythonTextBoxAutocompleteMenuHelper: user32 ToUnicode (the character of the current key in the platform keyboard layout).'),
]


def resx_of(path):
    """The .resx beside an original form source (Name.cs / Name.Designer.cs -> Name.resx)."""
    resx = (ROOT / path).with_name((ROOT / path).name.split('.')[0] + '.resx')
    if not resx.exists():
        raise SystemExit(f'{path}: no {resx.name}')
    return resx.relative_to(ROOT).as_posix()


def form_files():
    files = list(BASE)
    for name in FORMS:
        found = sorted(p for p in (ROOT / 'PrePoMax/Forms').rglob(name + '.cs'))
        if len(found) != 1:
            raise SystemExit(f'{name}: expected one source, found {found}')
        files.append(found[0].relative_to(ROOT).as_posix())
        designer = found[0].with_name(name + '.Designer.cs')
        if designer.exists():
            files.append(designer.relative_to(ROOT).as_posix())
    return files


def render(path, output):
    raw = (ROOT / path).read_bytes()
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    applied = []
    for pattern, replacement, reason in REWRITES:
        before = text
        if callable(replacement):
            if not re.search(pattern, text):
                continue
            value = replacement(path)
            if value is None:
                continue
            text, count = re.subn(pattern, value, text) if '\\' in value else re.subn(pattern, lambda m, v=value: v, text)
        else:
            text, count = re.subn(pattern, replacement, text)
        if count and text != before:
            applied.append(f'// Rewrite x{count}: {reason}')
    header = [f'// Generated by X/UI/generate-original-forms.py from {path}; do not edit.',
              f'// Original SHA256 {hashlib.sha256(raw).hexdigest()}',
              '// Original source: PrePoMax, Copyright (C) 2016-2026 Matej Borovinšek; root LICENSE.'] + applied
    # Compiler diagnostics point at the original file and line.
    original = os.path.relpath(ROOT / path, output.parent).replace(os.sep, '/')
    return '\n'.join(header) + '\n#line 1 "' + original + '"\n' + text


RESOURCES = [('PrePoMax', 'PrePoMax/Properties/Resources.Designer.cs', 'PrePoMax/Properties/Resources.resx'),
             ('UserControls', 'UserControls/Properties/Resources.Designer.cs', 'UserControls/Properties/Resources.resx')]


def resources(namespace, designer, resx):
    """Properties.Resources stand-in: each original image entry by name and its original file."""
    import xml.etree.ElementTree as ET
    names = re.findall(r'(?:public|internal) static System\.Drawing\.Bitmap (\w+) \{', (ROOT / designer).read_text(encoding='utf-8-sig'))
    files = {}
    for data in ET.parse(ROOT / resx).getroot().iter('data'):
        value = data.findtext('value') or ''
        if 'ResXFileRef' in (data.get('type') or ''):
            files[data.get('name')] = (Path(resx).parent / value.split(';')[0].replace('\\', '/')).as_posix()
    lines = [f'// Generated by X/UI/generate-original-forms.py from {designer} and {resx}; do not edit.',
             f'// Original SHA256 {hashlib.sha256((ROOT / designer).read_bytes()).hexdigest()} / {hashlib.sha256((ROOT / resx).read_bytes()).hexdigest()}',
             '// System.Drawing.Bitmap needs GDI+ (Windows only on .NET 10): entries name the original image file instead.',
             f'namespace {namespace}.Properties', '{', '    internal static class Resources', '    {']
    for name in names:
        path = os.path.normpath(files[name]).replace(os.sep, '/')
        if not (ROOT / path).exists():
            raise SystemExit(f'{designer}: {name} -> missing {path}')
        lines.append(f'        internal static System.Windows.Forms.ImageResource {name} {{ get; }} = new System.Windows.Forms.ImageResource("{name}", "{path}");')
    lines += ['    }', '}', '']
    return '\n'.join(lines)


HOST = 'PrePoMax/Forms/FrmMain.cs'
# FrmMain members that host the forms (FrmMain.cs): form registration/placement, the selection and highlight
# routing, and each create/edit entry point of a compiled form.
HOST_METHODS = ['AddFormToAllForms', 'CloseAllForms', 'SetFormLocation', 'ShowForm', 'SaveFormLocation', 'itemForm_Move',
                'itemForm_VisibleChanged', 'SelectionChanged', 'UpdateHighlight',
                # Operations the compiled forms start through FrmMain callbacks
                'TranslateGeometryPartsAsync', 'RotateGeometryPartsAsync', 'MirrorGeometryPartsAsync',
                'ScaleGeometryPartsAsync', 'RunGeometryTransformAsync', 'PreviewEdgeMeshAsync', 'SplitPartMeshUsingSurface',
                'ExportUsingFileProperties', 'GetDefaultCaptureViewportProperties',
                # New model properties (FrmNewModel, modal)
                'SelectNewModelProperties', 'SetNewModelProperties', 'IfNeededSelectAndSetNewModelProperties',
                # Menu handlers of the data grid forms (the model tree's create calls them too)
                'tsmiCreateDistribution_Click', 'tsmiCreateAmplitude_Click', 'tsmiCreateResultFieldOutput_Click',
                'tsmiCreateResultHistoryOutput_Click',
                # Child-window forms and dialogs (C11): their FrmMain entry points and callbacks
                'KillAnalysis', 'TryGetRegenerateType', 'TurnSectionViewOnOff', 'AnalyzeGeometry', 'SearchContactPairs',
                'SetColorForGeometryParts', 'SetColorForModelParts', 'SetColorForResultParts',
                'SetTransparencyForGeometryParts', 'SetTransparencyForModelParts', 'SetTransparencyForResultParts',
                'FindEdgesByAngleForGeometryParts', 'FindEdgesByAngleForModelParts', 'SetUpFrmGetValueForEdgeAngle',
                'tsmiRenumberAllNodes_Click', 'tsmiRenumberAllElements_Click', 'CreateSimpleMaterial', 'ShowMaterialLibrary',
                'tsmiSettings_Click', 'ShowColorBarSettings', 'ShowAnnotationSettings', 'ShowLegendSettings',
                'tsmiCoorSysSettings_Click', 'ShowStatusBlockSettings', 'tsmiEditParameters_Click', 'tsmiQuery_Click',
                'tsmiFind_Click', 'MonitorAnalysis', 'CloseMonitorWindow', 'UpdateAnalysisProgress', 'GetDefaultJob',
                'ViewResultHistoryOutputData', 'tsmiAbout_Click', 'SelectOneEntity', 'SelectOneEntityInStep',
                'SelectMultipleEntities', 'SelectMultipleEntitiesInStep', 'tsbAnimate_Click', 'ClearSelection',
                'AddNonpositiveJacobianElementSet', 'GetMeshIdentityOrNull', 'tsmiMaterialLibrary_Click',
                'tsmiSearchContactPairs_Click',
                # Code editor forms (C12)
                'tsmiEditHistory_Click', 'tsmiEditCalculiXKeywords_Click', 'EditCalculiXKeywords', 'CheckValidity']
# FrmMain fields the members above use (declarations copied verbatim).
HOST_FIELDS = ['_nonpositiveJacobianSetsAwaited', '_isNonpositiveJacobianSetAwaited']
HOST_REWRITES = [
    (r'(?<![\w.])OrderedDictionary<', 'CaeGlobals.OrderedDictionary<',
     '.NET 9+ adds System.Collections.Generic.OrderedDictionary<,> (and UserControls has its own); FrmMain uses CaeGlobals\'.'),
    (r'_frmAnimation\.PrepareForm\(this, _controller\)', '_frmAnimation.PrepareForm((FrmMain)_controller.Host, _controller)',
     'FrmAnimation drives the viewport through FrmMain; the headless FrmMain host forwards those calls to the renderer.'),
    (r'PythonPanel pythonPanel = _visibleSidePanel as PythonPanel;\n(\s*)if \(pythonPanel != null && pythonPanel\.Focused\)\n(\s*)\{\n(\s*)pythonPanel\.ShowFind\(\);',
     r'// The Python side panel is the workbench\'s: its Find when it has the focus.\n\1if (PythonPanelShowFind())\n\2{',
     'The Python side panel belongs to the workbench; FrmMain asks it to show its Find when it has the focus.'),
]


def host(extractor):
    """OriginalFormHost.g.cs: the FrmMain form plumbing, extracted verbatim by Roslyn."""
    import json
    import subprocess
    data = json.loads(subprocess.check_output(['dotnet', str(extractor), str(ROOT)], text=True))
    methods = [m for f in data if f['name'] == 'FrmMain' and f['file'] == HOST for m in f['methods']]
    source = (ROOT / HOST).read_text(encoding='utf-8-sig').replace('\r\n', '\n')
    classes = set(FORMS) | {'FrmSelectItemSet'}
    fields = dict(re.findall(r'^        private (Frm\w+) (_frm\w+);$', source, re.M))
    fields = {name: kind for kind, name in ((k, n) for k, n in fields.items())}
    ours = {name for name, kind in fields.items() if kind in classes}
    # Form construction: FrmMain constructor groups "_frmX = new FrmX(...); ...; AddFormToAllForms(_frmX);".
    start = source.index('                _formLocation = new Point(100, 100);')
    end = source.index('                // Deformation toolstrip', start)
    groups = [g.strip('\n') for g in re.split(r'\n\s*//\n', source[start:end])]
    create = []
    for group in groups:
        head = re.match(r'\s*(_frm\w+) = new (\w+)\(', group)
        if head is None or head.group(1) in ours:
            create.append(group)
    skipped_forms = sorted(set(fields) - ours)

    def strip_other_forms(code):
        # Routing lines of forms that are not compiled yet are omitted (listed in the header).
        return re.sub(r'\n[ \t]*if \((_frm\w+) != null && \1\.Visible\)(?:\s*\n\s*|\s)\1\.\w+\(ids\);',
                      lambda m: m.group(0) if m.group(1) in ours else '', code)
    chosen = [m for m in methods if m['name'] in HOST_METHODS]
    for m in methods:
        shown = [c['arguments'][0] for c in m['calls'] if c['expression'] == 'ShowForm']
        if shown and m['name'] != 'ShowForm' and all(f in ours for f in shown):
            chosen.append(m)
    picked = [m for m in methods if m['name'] == '_vtk_SelectPointOrArea'][0]['code']
    picked_lines = [line.strip() for line in picked.split('\n') if re.match(r'\s*if \((_frm\w+) != null && \1\.Visible\) \1\.PickedIds\(ids\);', line)
                    and re.search(r'\((_frm\w+) ', line).group(1) in ours]
    raw = (ROOT / HOST).read_bytes()
    out = [f'// Generated by X/UI/generate-original-forms.py from {HOST} (form hosting members); do not edit.',
           f'// Original SHA256 {hashlib.sha256(raw).hexdigest()}',
           '// Original source: PrePoMax, Copyright (C) 2016-2026 Matej Borovinšek; root LICENSE.',
           '// Forms not compiled yet (their routing lines are omitted): ' + ', '.join(skipped_forms),
           'using System;', 'using System.Collections.Generic;', 'using System.Drawing;', 'using System.Linq;',
           'using System.Windows.Forms;', 'using CaeGlobals;', 'using CaeJob;', 'using CaeMesh;', 'using CaeModel;', 'using CaeResults;',
           'using PrePoMax.Commands;', 'using PrePoMax.Forms;', 'using PrePoMax.Python;', 'using UserControls;', '',
           'namespace PrePoMax', '{', '    public sealed partial class OriginalFormHost', '    {',
           '        private Point _formLocation;', '        private List<Form> _allForms;']
    out += [f'        private {fields[name]} {name};' for name in sorted(ours, key=list(fields).index)]
    for field in HOST_FIELDS:
        match = re.search(r'^        private [^;=]*\b' + field + r'\b[^;]*;', source, re.M | re.S)
        if match is None:
            raise SystemExit(f'{field}: no declaration in {HOST}')
        out.append(match.group(0))
    out += ['        // FrmMain constructor: form creation', '        private void CreateForms()', '        {']
    out += ['    ' + line[8:] if line.startswith('        ') else line for line in '\n                //\n'.join(create).split('\n')]
    out += ['        }', '        // FrmMain._vtk_SelectPointOrArea: point picks of the transformation forms',
            '        public void PickedIds(int[] ids)', '        {'] + ['            ' + l for l in picked_lines] + ['        }']
    seen = set()
    for m in chosen:
        if m['code'] in seen:
            continue
        seen.add(m['code'])
        out.append('        ' + strip_other_forms(m['code']))
    # Menu items whose text the extracted handlers use (ShowForm titles): FrmMain.Designer.cs text.
    designer = (ROOT / 'PrePoMax/Forms/FrmMain.Designer.cs').read_text(encoding='utf-8-sig')
    body = '\n'.join(out)
    items = sorted(set(re.findall(r'\b((?:tsmi|tsb)\w+)\.Text\b', body)))
    if items:
        out.append('        // FrmMain.Designer.cs: menu items whose Text the handlers above use')
        for item in items:
            match = re.search(r'this\.' + item + r'\.Text = (".*?");', designer)
            if match is None:
                raise SystemExit(f'{item}: no Text in FrmMain.Designer.cs')
            out.append(f'        private readonly ToolStripMenuItem {item} = new ToolStripMenuItem({match.group(1)});')
    out += ['    }', '}', '']
    text = '\n'.join(out)
    notes = []
    for pattern, replacement, reason in HOST_REWRITES:
        text, count = re.subn(pattern, replacement, text)
        if count:
            notes.append(f'// Rewrite x{count}: {reason}')
    return text.replace('using System;\n', '\n'.join(notes) + '\nusing System;\n', 1) if notes else text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--extractor', type=Path, default=HERE / 'FormSourceGen/bin/Release/net10.0/FormSourceGen.dll')
    args = parser.parse_args()
    outputs = {f: OUT / (Path(f).with_suffix('').as_posix() + '.g.cs') for f in form_files()}
    expected = {o: render(f, o) for f, o in outputs.items()}
    for namespace, designer, resx in RESOURCES:
        expected[OUT / (Path(designer).with_suffix('').as_posix() + '.g.cs')] = resources(namespace, designer, resx)
    expected[OUT / 'OriginalFormHost.g.cs'] = host(args.extractor)
    stale = [p for p, t in expected.items() if not p.exists() or p.read_text(encoding='utf-8') != t]
    extra = [p for p in OUT.rglob('*.g.cs') if p not in expected] if OUT.exists() else []
    if args.check:
        if stale or extra:
            raise SystemExit('Stale original forms: run X/UI/generate-original-forms.py\n' +
                             '\n'.join(str(p.relative_to(ROOT)) for p in stale + extra))
        print(f'original forms current ({len(expected)} files)')
        return
    for p in extra:
        p.unlink()
    for p, t in expected.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(t, encoding='utf-8')
    print(f'wrote {len(expected)} original form files')


if __name__ == '__main__':
    main()
