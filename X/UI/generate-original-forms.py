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
# The original application compiled whole (M2, X/App): FrmMain, Program and the rest of the PrePoMax and UserControls
# assemblies beside the forms above. Generated into X/App/Original; the workbench build does not compile them.
APP = [
    'PrePoMax/Forms/FrmMain.cs', 'PrePoMax/Forms/FrmMain.Designer.cs', 'PrePoMax/Forms/FrmMain.Plotting.cs',
    'PrePoMax/Forms/FrmMain.ControllerHost.cs', 'PrePoMax/Forms/FrmPythonStop.cs', 'PrePoMax/Forms/FrmPythonStop.Designer.cs',
    'PrePoMax/Forms/00_Common/FileExporter/ViewExportFileProperties.cs', 'PrePoMax/Forms/00_Common/ViewStringValue.cs',
    'PrePoMax/Forms/00_Advisor/AdvisorCreator.cs', 'PrePoMax/Forms/11_MeshSetup/Base/MeshSetupItemTypes.cs',
    'PrePoMax/Forms/04_GeometryFeature/GeometryFeatureTypes.cs',
    'PrePoMax/Python/Engine/PythonStopWatchdog.cs', 'PrePoMax/Python/PythonScriptException.cs',
    'PrePoMax/Program.cs', 'PrePoMax/Settings/GeneralSettings.WinForms.cs',
    'CaeGlobals/KeyboardHook.cs', 'CaeGlobals/MouseHook.cs', 'CaeGlobals/Editors/FilteredFileNameEditor.cs',
    'UserControls/AutocompleteMenu/AutocompleteItem.cs', 'UserControls/AutocompleteMenu/AutocompleteItems.cs',
    'UserControls/AutocompleteMenu/AutocompleteListView.cs', 'UserControls/AutocompleteMenu/AutocompleteMenu.cs',
    'UserControls/AutocompleteMenu/AutocompleteMenuHost.cs', 'UserControls/AutocompleteMenu/Colors.cs',
    'UserControls/AutocompleteMenu/EventArgs.cs', 'UserControls/AutocompleteMenu/IAutocompleteListView.cs',
    'UserControls/AutocompleteMenu/ITextBoxWrapper.cs', 'UserControls/AutocompleteMenu/Range.cs',
    'UserControls/AutocompleteMenu/TextBoxWrapper.cs', 'UserControls/Buttons/MenuStyleButton.cs',
    'UserControls/MenuStrip/NoHighlightRenderer.cs', 'UserControls/NoBeepMessageFilter.cs',
    'UserControls/Forms/MainMouseWheelManagedForm.cs', 'UserControls/ListView/MyListView.cs',
    'UserControls/SidePanel/XYPlot/FrmXYPlotSettings.cs', 'UserControls/SidePanel/XYPlot/XYPlotSettings.ZedGraph.cs',
    'UserControls/SidePanel/XYPlot/XYPlot.cs', 'UserControls/SidePanel/XYPlot/XYPlot.Designer.cs',
    'UserControls/SidePanel/XYPlot/XYPlotPanel.cs', 'UserControls/SidePanel/XYPlot/XYPlotPanel.Designer.cs',
    'UserControls/SidePanel/PythonPanel.cs', 'UserControls/SidePanel/PythonPanel.Designer.cs',
    'UserControls/SidePanel/SidePanel.cs', 'UserControls/Panels/BorderColoredPanel.cs',
    'UserControls/TextBoxes/PythonConsoleTextBox/PythonConsoleFastTextBox.cs',
    'UserControls/TextBoxes/PythonConsoleTextBox/PythonConsoleTextBox.cs', 'UserControls/TextBoxes/OutputTextBox.cs',
    'UserControls/TextBoxes/ViewportEditorRichTextBox.cs',
    'UserControls/TextBoxes/UnitAwareToolStripTextBox.cs', 'UserControls/TextBoxes/UnitAwareToolStripTextBox.Designer.cs',
    'UserControls/TextBoxes/NumericToolStripTextBox.cs', 'UserControls/TextBoxes/NumericToolStripTextBox.Designer.cs',
    'UserControls/TextBoxes/ResizableTextBox.cs', 'UserControls/TextBoxes/SearchTextBox.cs',
    'UserControls/TextBoxes/SearchTextBox.Designer.cs', 'UserControls/MenuStrip/MenuStripFocus.cs',
    'UserControls/MenuStrip/MenuStripFocus.Designer.cs', 'UserControls/ModelTree.cs', 'UserControls/ModelTree.Designer.cs',
    'UserControls/ToolStrip/ToolStripFocus.cs',
    'UserControls/ToolStrip/ToolStripFocus.Designer.cs', 'UserControls/Trees/Extensions.cs',
    'UserControls/UITypeEditors/DampingRatiosAndValuesUIEditor.cs', 'UserControls/UITypeEditors/FlagsEnumEditor.cs',
    'UserControls/UITypeEditors/FrmGetDampingRatios.cs', 'UserControls/UITypeEditors/FrmGetDampingRatios.Designer.cs',
    'UserControls/Views/Sections/ViewSection.cs', 'UserControls/Views/Sections/ViewSolidSection.cs',
    'UserControls/Views/Step/ViewStaticStep.cs', 'UserControls/Views/Step/ViewStep.cs', 'UserControls/SidePanel/PanelPage.cs',
    'UserControls/SidePanel/AdvisorPanel.cs', 'UserControls/SidePanel/AdvisorPanel.Designer.cs',
    'UserControls/ViewportTextEditor.cs', 'UserControls/ViewportTextEditor.Designer.cs',
]
# Not compiled in X/App, with their counterparts: UserControls AutoScrollTextBox, TabEnabledPropertyGrid,
# ChildMouseWheelManagedForm, MySite, PropertyGridMissingValuePainter and ColorEditorEx reach WinForms internals through user32 or
# private reflection (stand-ins in X/UI/FormsCompat/UserControls.cs, the missing-value mark in the renderer);
# PrePoMax MesherMemory.Windows.cs, PythonEngineManager.Windows.cs (X/Controller/Host), Rpc/*.cs (their portable
# generated copies) and ViewNodeSet.Windows.cs (only the Windows forms build calls its overload); PrePoMax
# Settings.cs and Properties/Settings.Designer.cs, the empty Visual Studio application settings class nothing uses
# (System.Configuration.ApplicationSettingsBase is a separate package on .NET).
APP_OUT = ROOT / 'X/App/Original'
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
    (r'System\.ComponentModel\.ComponentResourceManager resources = new System\.ComponentModel\.ComponentResourceManager\(typeof\(\w+\)\)',
     lambda path: f'System.Windows.Forms.ResxResources resources = new System.Windows.Forms.ResxResources("{resx_of(path)}")',
     'Designer images are read from the original .resx by the renderer (base64 image bytes); no resource deserialization.'),
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
    (r'(?m)^using FastColoredTextBoxNS;$', lambda path: 'using FastColoredTextBoxNS; using Range = FastColoredTextBoxNS.Range;' if path.startswith('UserControls/') else None,
     '.NET adds System.Range (net48 has none); FastColoredTextBoxNS.Range is named by an alias on the same line.'),
    (r'\[System\.Runtime\.InteropServices\.DllImport\("user32\.dll"\)\]\n(\s*)public static extern bool LockWindowUpdate\(IntPtr hWndLock\);',
     r'// user32 LockWindowUpdate (rewritten, see header)\n\1public static bool LockWindowUpdate(IntPtr hWndLock) => true; // user32: suspends painting only; the renderer paints after the handler',
     'FrmCalculixKeywordEditor suspends window painting through user32 while it adds a node; the renderer repaints once the handler returns.'),
    (r'\[DllImport\("user32\.dll"\)\]\n(\s*)private static extern bool GetKeyboardState\(byte\[\] keyState\);',
     r'// user32 GetKeyboardState (rewritten, see header)\n\1private static bool GetKeyboardState(byte[] keyState) => System.Windows.Forms.KeyboardLayout.GetKeyboardState(keyState);',
     'PythonTextBoxAutocompleteMenuHelper maps a key to its character through user32; the renderer reports the character the platform keyboard layout produced.'),
    (r'\[DllImport\("user32\.dll"\)\]\n(\s*)private static extern uint MapVirtualKey\(uint code, uint mapType\);',
     r'// user32 MapVirtualKey (rewritten, see header)\n\1private static uint MapVirtualKey(uint code, uint mapType) => System.Windows.Forms.KeyboardLayout.MapVirtualKey(code, mapType);',
     'PythonTextBoxAutocompleteMenuHelper: user32 scan code lookup (the platform keyboard layout).'),
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Unicode\)\]\n(\s*)private static extern int ToUnicode\(uint virtualKeyCode, uint scanCode, byte\[\] keyState,\n\s*\[Out, MarshalAs\(UnmanagedType\.LPWStr\)\] StringBuilder receivingBuffer,\n\s*int bufferSize, uint flags\);',
     r'// user32 ToUnicode (rewritten, see header)\n\1//\n\1//\n\1private static int ToUnicode(uint virtualKeyCode, uint scanCode, byte[] keyState, StringBuilder receivingBuffer, int bufferSize, uint flags) => System.Windows.Forms.KeyboardLayout.ToUnicode(virtualKeyCode, keyState, receivingBuffer);',
     'PythonTextBoxAutocompleteMenuHelper: user32 ToUnicode (the character of the current key in the platform keyboard layout).'),
    # FrmMain and the rest of the application compiled whole (M2, X/App)
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Auto, SetLastError = true\)\]\n(\s*)private static extern IntPtr SetWindowsHookEx\(int idHook, KeyboardHookHandler lpfn, IntPtr hMod, uint dwThreadId\);',
     r'// user32 SetWindowsHookEx (rewritten, see header)\n\1private static IntPtr SetWindowsHookEx(int idHook, KeyboardHookHandler lpfn, IntPtr hMod, uint dwThreadId) => System.Windows.Forms.LowLevelKeyboardHook.Set(idHook, (n, w, l) => lpfn(n, w, l));',
     'KeyboardHook installs a user32 low-level keyboard hook; the renderer reports the application\'s keys to it with the same message codes.'),
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Auto, SetLastError = true\)\]\n(\s*)\[return: MarshalAs\(UnmanagedType\.Bool\)\]\n(\s*)private static extern bool UnhookWindowsHookEx\(IntPtr hhk\);',
     r'// user32 UnhookWindowsHookEx (rewritten, see header)\n\1//\n\2private static bool UnhookWindowsHookEx(IntPtr hhk) => System.Windows.Forms.LowLevelKeyboardHook.Unset(hhk);',
     'KeyboardHook: user32 hook removal.'),
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Auto, SetLastError = true\)\]\n(\s*)private static extern IntPtr CallNextHookEx\(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam\);',
     r'// user32 CallNextHookEx (rewritten, see header)\n\1private static IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam) => System.Windows.Forms.LowLevelKeyboardHook.CallNext(hhk, nCode, wParam, lParam);',
     'KeyboardHook: the next hook in the user32 chain (the renderer has none).'),
    (r'\[DllImport\("kernel32\.dll", CharSet = CharSet\.Auto, SetLastError = true\)\]\n(\s*)private static extern IntPtr GetModuleHandle\(string lpModuleName\);',
     r'// kernel32 GetModuleHandle (rewritten, see header)\n\1private static IntPtr GetModuleHandle(string lpModuleName) => IntPtr.Zero;',
     'KeyboardHook: the kernel32 module handle a user32 hook needs (unused by the renderer\'s hook).'),
    (r'(?m)^using System\.Runtime\.Remoting\.Metadata\.W3cXsd2001;$', '// using System.Runtime.Remoting.Metadata.W3cXsd2001; (net48 only, nothing of it is used)',
     'ModelTree names a .NET Framework remoting namespace that .NET 10 lacks; nothing of it is used.'),
    # Program (the original command line): kernel32 console, process and Ctrl+C entry points
    (r'\[DllImport\("kernel32\.dll"\)\]\n(\s*)private static extern IntPtr GetConsoleWindow\(\);',
     r'// kernel32 GetConsoleWindow (rewritten, see header)\n\1private static IntPtr GetConsoleWindow() => IntPtr.Zero;',
     'Program: kernel32 GetConsoleWindow (only in a comment); a Unix process has no console window.'),
    (r'\[DllImport\("kernel32\.dll"\)\]\n(\s*)static extern bool AttachConsole\(int dwProcessId\);',
     r'// kernel32 AttachConsole (rewritten, see header)\n\1static bool AttachConsole(int dwProcessId) => false;',
     'Program: a Unix process inherits the standard handles of its parent; there is no console to attach to.'),
    (r'\[DllImport\("kernel32\.dll"\)\]\n(\s*)private static extern IntPtr GetStdHandle\(int nStdHandle\);',
     r'// kernel32 GetStdHandle (rewritten, see header)\n\1private static IntPtr GetStdHandle(int nStdHandle) => new IntPtr(nStdHandle == STD_ERROR_HANDLE ? 2 : 1);',
     'Program: a Unix process always has its standard output and error (file descriptors 1 and 2).'),
    (r'\[DllImport\("kernel32\.dll"\)\]\n(\s*)private static extern bool SetStdHandle\(int nStdHandle, IntPtr hHandle\);',
     r'// kernel32 SetStdHandle (rewritten, see header)\n\1private static bool SetStdHandle(int nStdHandle, IntPtr hHandle) => true;',
     'Program: the standard handles stay the inherited ones.'),
    (r'\[DllImport\("kernel32\.dll"\)\]\n(\s*)private static extern IntPtr GetCurrentProcess\(\);',
     r'// kernel32 GetCurrentProcess (rewritten, see header)\n\1private static IntPtr GetCurrentProcess() => new IntPtr(-1);',
     'Program: the pseudo handle of the current process.'),
    (r'\[DllImport\("kernel32\.dll"\)\]\n(\s*)private static extern bool TerminateProcess\(IntPtr hProcess, uint uExitCode\);',
     r'// kernel32 TerminateProcess (rewritten, see header)\n\1private static bool TerminateProcess(IntPtr hProcess, uint uExitCode) { Environment.Exit((int)uExitCode); return true; }',
     'Program: the process ends with its exit code (Environment.Exit; the report and journal are written before).'),
    (r'\[DllImport\("kernel32\.dll"\)\]\n(\s*)private static extern bool SetConsoleCtrlHandler\(ConsoleCtrlHandler handler, bool add\);',
     r'// kernel32 SetConsoleCtrlHandler (rewritten, see header)\n\1private static bool SetConsoleCtrlHandler(ConsoleCtrlHandler handler, bool add) { s_sigint = System.Runtime.InteropServices.PosixSignalRegistration.Create(System.Runtime.InteropServices.PosixSignal.SIGINT, context => context.Cancel = handler(CTRL_C_EVENT)); return true; }\n\1private static System.Runtime.InteropServices.PosixSignalRegistration s_sigint;',
     'Program: Ctrl+C is SIGINT on Unix; the handler gets CTRL_C_EVENT and keeps the process alive when it handles it.'),
    (r'_cancelEvent = new EventWaitHandle\(false, EventResetMode\.ManualReset,\n(\s*)CancelEventNamePrefix \+ Process\.GetCurrentProcess\(\)\.Id\);',
     r'_cancelEvent = new EventWaitHandle(false, EventResetMode.ManualReset); // named on Windows (see header)\n\1//',
     'Program: on Windows the PrePoMax.com launcher signals a named event; on macOS/Linux PrePoMax.com is this same program and Ctrl+C reaches it as SIGINT (named events are Windows-only).'),
    # FrmMain: window redraw suspension and the search for open native dialogs
    (r'\[DllImport\("user32\.dll"\)\]\n(\s*)private static extern IntPtr SendMessage\(IntPtr hWnd, int msg, IntPtr wParam, IntPtr lParam\);\n(\s*)\[DllImport\("user32\.dll"\)\]\n(\s*)private static extern bool RedrawWindow\(IntPtr hWnd, IntPtr lprcUpdate, IntPtr hrgnUpdate, uint flags\);',
     r'// user32 SendMessage/RedrawWindow (rewritten, see header)\n\1private static IntPtr SendMessage(IntPtr hWnd, int msg, IntPtr wParam, IntPtr lParam) => IntPtr.Zero;\n\2//\n\3private static bool RedrawWindow(IntPtr hWnd, IntPtr lprcUpdate, IntPtr hrgnUpdate, uint flags) => true;',
     'FrmMain suspends window painting (WM_SETREDRAW) while it rebuilds the tree; the renderer paints once after the handler returns.'),
    (r'\[DllImport\("user32\.dll"\)\]\n(\s*)private static extern bool EnumThreadWindows\(int threadId, EnumThreadWindowsCallback callback, IntPtr parameter\);',
     r'// user32 EnumThreadWindows (rewritten, see header)\n\1private static bool EnumThreadWindows(int threadId, EnumThreadWindowsCallback callback, IntPtr parameter) => System.Windows.Forms.NativeDialogs.EnumThreadWindows((h, p) => callback(h, p), parameter);',
     'FrmMain finds an open message box or file dialog among its thread\'s windows; the toolkit\'s open native dialogs are enumerated instead.'),
    (r'\[DllImport\("kernel32\.dll"\)\]\n(\s*)private static extern int GetCurrentThreadId\(\);',
     r'// kernel32 GetCurrentThreadId (rewritten, see header)\n\1private static int GetCurrentThreadId() => Environment.CurrentManagedThreadId;',
     'FrmMain: the user-interface thread.'),
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Unicode\)\]\n(\s*)private static extern int GetClassName\(IntPtr windowHandle, StringBuilder className, int maxCount\);',
     r'// user32 GetClassName (rewritten, see header)\n\1private static int GetClassName(IntPtr windowHandle, StringBuilder className, int maxCount) => System.Windows.Forms.NativeDialogs.GetClassName(windowHandle, className);',
     'FrmMain: the dialog window class of an open native dialog.'),
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Unicode\)\]\n(\s*)private static extern int GetWindowText\(IntPtr windowHandle, StringBuilder text, int maxCount\);',
     r'// user32 GetWindowText (rewritten, see header)\n\1private static int GetWindowText(IntPtr windowHandle, StringBuilder text, int maxCount) => System.Windows.Forms.NativeDialogs.GetWindowText(windowHandle, text);',
     'FrmMain: the title of an open native dialog.'),
    (r'\[DllImport\("user32\.dll"\)\]\n(\s*)private static extern bool IsWindowVisible\(IntPtr windowHandle\);',
     r'// user32 IsWindowVisible (rewritten, see header)\n\1private static bool IsWindowVisible(IntPtr windowHandle) => System.Windows.Forms.NativeDialogs.IsWindowVisible(windowHandle);',
     'FrmMain: an open native dialog is visible.'),
    # CaeGlobals MouseHook (the autocomplete list closes on a click elsewhere)
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Auto, SetLastError = true\)\]\n(\s*)private static extern IntPtr SetWindowsHookEx\(int idHook,\n\s*MouseHookHandler lpfn, IntPtr hMod, uint dwThreadId\);',
     r'// user32 SetWindowsHookEx (rewritten, see header)\n\1//\n\1private static IntPtr SetWindowsHookEx(int idHook, MouseHookHandler lpfn, IntPtr hMod, uint dwThreadId) => System.Windows.Forms.LowLevelMouseHook.Set(idHook, (n, w, l) => lpfn(n, w, l));',
     'MouseHook installs a user32 low-level mouse hook; the renderer reports the application\'s mouse messages to it.'),
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Auto, SetLastError = true\)\]\n(\s*)\[return: MarshalAs\(UnmanagedType\.Bool\)\]\n(\s*)public static extern bool UnhookWindowsHookEx\(IntPtr hhk\);',
     r'// user32 UnhookWindowsHookEx (rewritten, see header)\n\1//\n\2public static bool UnhookWindowsHookEx(IntPtr hhk) => System.Windows.Forms.LowLevelMouseHook.Unset(hhk);',
     'MouseHook: user32 hook removal.'),
    (r'\[DllImport\("user32\.dll", CharSet = CharSet\.Auto, SetLastError = true\)\]\n(\s*)private static extern IntPtr CallNextHookEx\(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam\);\n\n(\s*)\[DllImport\("kernel32\.dll", CharSet = CharSet\.Auto, SetLastError = true\)\]\n(\s*)private static extern IntPtr GetModuleHandle\(string lpModuleName\);',
     r'// user32 CallNextHookEx, kernel32 GetModuleHandle (rewritten, see header)\n\1private static IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam) => System.Windows.Forms.LowLevelMouseHook.CallNext(hhk, nCode, wParam, lParam);\n\n\2//\n\3private static IntPtr GetModuleHandle(string lpModuleName) => IntPtr.Zero;',
     'MouseHook: the next hook (the renderer has none) and the module handle a user32 hook needs (unused).'),
    # ViewportEditorRichTextBox: paragraph line spacing and the scroll reset of the viewport text editor
    (r'\[DllImport\("user32", CharSet = CharSet\.Auto\)\]\n(\s*)private static extern IntPtr SendMessage\(HandleRef hWnd, int msg, int wParam, ref PARAFORMAT lParam\);',
     r'// user32 SendMessage EM_SETPARAFORMAT (rewritten, see header)\n\1private static IntPtr SendMessage(HandleRef hWnd, int msg, int wParam, ref PARAFORMAT lParam) { ((ViewportEditorRichTextBox)hWnd.Wrapper).LineSpacing = (lParam.bLineSpacingRule, lParam.dyLineSpacing); return IntPtr.Zero; }',
     'ViewportEditorRichTextBox sets the paragraph line spacing through a rich edit message; the renderer applies the recorded spacing.'),
    (r'\[return: MarshalAs\(UnmanagedType\.Bool\)\]\n(\s*)\[DllImport\("user32\.dll", SetLastError = true\)\]\n(\s*)private static extern bool PostMessage\(IntPtr hWnd, UInt32 Msg, IntPtr wParam, IntPtr lParam\);',
     r'// user32 PostMessage (rewritten, see header)\n\1//\n\2private static bool PostMessage(IntPtr hWnd, UInt32 Msg, IntPtr wParam, IntPtr lParam) => false;',
     'ViewportEditorRichTextBox posts WM_VSCROLL SB_TOP to undo a rich edit autoscroll; the call below scrolls the box instead.'),
    (r'PostMessage\(Handle, WM_VSCROLL, \(IntPtr\)SB_TOP, IntPtr\.Zero\);',
     r'BeginInvoke((System.Windows.Forms.MethodInvoker)VerticalScrollToTop); // WM_VSCROLL SB_TOP, posted',
     'ViewportEditorRichTextBox: the posted scroll to the top runs after the current message, as the posted WM_VSCROLL does.'),
    (r'(?<![\w.])MethodInvoker\b', 'System.Windows.Forms.MethodInvoker',
     '.NET adds System.Reflection.MethodInvoker (net48 has none); the original means the WinForms delegate.'),
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
    outputs.update({f: APP_OUT / (Path(f).with_suffix('').as_posix() + '.g.cs') for f in APP})
    expected = {o: render(f, o) for f, o in outputs.items()}
    for namespace, designer, resx in RESOURCES:
        expected[OUT / (Path(designer).with_suffix('').as_posix() + '.g.cs')] = resources(namespace, designer, resx)
    expected[OUT / 'OriginalFormHost.g.cs'] = host(args.extractor)
    stale = [p for p, t in expected.items() if not p.exists() or p.read_text(encoding='utf-8') != t]
    extra = [p for out in (OUT, APP_OUT) if out.exists() for p in out.rglob('*.g.cs') if p not in expected]
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
