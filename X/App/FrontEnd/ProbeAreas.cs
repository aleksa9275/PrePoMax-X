// The form-level checks of the workbench's GUI probe areas (X/UI/*_gui_probe.py on the Qt workbench), on the real
// application and the Avalonia front end: PREPOMAXX_UI_PROBE=avalonia with PREPOMAXX_UI_PROBE_AREA set to
//   forms     (-f a mesh deck)  menu parity in every view; every create form of the main menu opened through its
//             original entry point, drawn at its designer client size with every visible control mirrored at its
//             model bounds, Cancel changing nothing; authoring through FrmStep and FrmAmplitude (data grid, plot);
//             the code editor (FrmEditCommands)
//   geometry  (-f a CAD file)   the imported geometry, Netgen meshing through the original menu, the mesh drawn
//   results   (-f a project)    an analysis created through FrmAnalysis, CalculiX run through the original menu, the
//             original FrmMonitor, the results opened, the result controls and the view
//   elements  (-f an .inp)      the original element classes imported and drawn, the tree and the mesh form
// run_probe_areas.py runs the four and writes one report.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Avalonia.Controls;
using Avalonia.VisualTree;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEnd
{
    internal static partial class Probe
    {
        static readonly string s_area = Environment.GetEnvironmentVariable("PREPOMAXX_UI_PROBE_AREA");

        static dynamic Controller(WinForms.Form form) => form.GetType().GetProperty("Controller")?.GetValue(form);
        static int Commands(WinForms.Form main) { dynamic c = Controller(main); return (int)c.GetCommands().Count; }
        static WinForms.ToolStripItem MenuItem(WinForms.Form main, string name) =>
            Walk(main.MainMenuStrip.Items.Cast<WinForms.ToolStripItem>()).FirstOrDefault(i => i.Name == name);

        static List<WinForms.Form> ShownForms(WinForms.Form main) =>
            Ui.Windows.Where(p => p.Key != main && p.Key.Visible && p.Value.IsVisible).Select(p => p.Key).ToList();

        static IEnumerable<WinForms.Control> Ancestors(WinForms.Control control) { for (var c = control; c != null; c = c.Parent) yield return c; }
        static bool Shown(WinForms.Control control)
        {
            // WinForms shows only the selected page of a tab control
            for (var c = control; c != null; c = c.Parent)
            {
                if (!c.Visible) return false;
                if (c is WinForms.TabPage page && page.Parent is WinForms.TabControl tabs && tabs.SelectedTab != page) return false;
            }
            return true;
        }

        /// <summary>Every visible control of a form has its Avalonia frame at its model bounds (controls drawn by their
        /// parent, a leaf mirror, have none of their own).</summary>
        static void CheckMirrored(string name, WinForms.Form form)
        {
            FormWindow window = Ui.Windows[form];
            var mirrors = window.Mirrors.ToDictionary(p => p.Key, p => p.Value);
            var wrong = new List<string>();
            int count = 0;
            void Visit(WinForms.Control parent)
            {
                foreach (WinForms.Control c in parent.Controls)
                {
                    if (!Shown(c)) continue;
                    count++;
                    if (!mirrors.TryGetValue(c, out var mirror)) { wrong.Add(c.Name + " not mirrored"); continue; }
                    double left = Canvas.GetLeft(mirror.Frame), top = Canvas.GetTop(mirror.Frame);
                    if (left != c.Left || top != c.Top || mirror.Frame.Width != Math.Max(0, c.Width) || mirror.Frame.Height != Math.Max(0, c.Height))
                        wrong.Add(c.Name + " at " + left + "," + top + " " + mirror.Frame.Width + "x" + mirror.Frame.Height + " for " + c.Bounds);
                    else if (!mirror.Frame.IsEffectivelyVisible) wrong.Add(c.Name + " hidden");
                    if (!mirror.Leaf) Visit(c);
                }
            }
            Visit(form);
            Check(name, wrong.Count == 0 && count > 0, count + " controls" + (wrong.Count == 0 ? "" : "; " + string.Join("; ", wrong.Take(4))));
        }

        static async Task<WinForms.Form> OpenFromMenu(WinForms.Form main, string item, string type)
        {
            var entry = MenuItem(main, item);
            Check(item + " enabled", entry != null && entry.Enabled, entry == null ? "missing" : "disabled");
            var before = ShownForms(main);
            Ui.Input(entry.PerformClick);
            await Wait(() => ShownForms(main).Any(f => !before.Contains(f) && (type == null || f.GetType().Name == type)), 10, item + " opens " + (type ?? "a form"));
            return ShownForms(main).First(f => !before.Contains(f) && (type == null || f.GetType().Name == type));
        }

        static void Press(WinForms.Form form, params string[] names)
        {
            var button = names.Select(n => Field<WinForms.Button>(form, n)).FirstOrDefault(b => b != null) ?? form.CancelButton as WinForms.Button;
            Ui.Input(() => { if (button != null) button.PerformClick(); else form.Close(); });
        }

        static async Task RunArea(string area, FormWindow window, WinForms.Form main, string output)
        {
            await Pump(1);
            var host = window.GetVisualDescendants().OfType<ViewHost>().FirstOrDefault();
            await Wait(() => host != null && host.Attached && host.Control.NativeMirror != null, 20, "the original vtkControl in a native host");
            switch (area)
            {
                case "forms": await FormsArea(window, main); break;
                case "geometry": await GeometryArea(window, main, host, output); break;
                case "results": await ResultsArea(window, main, host, output); break;
                case "elements": await ElementsArea(window, main, host, output); break;
                default: Check("a known probe area", false, area); break;
            }
        }

        // Menu parity (menu_gui_probe), forms (forms_gui_probe and its child/composite/editor/grid steps), authoring
        static async Task FormsArea(FormWindow window, WinForms.Form main)
        {
            dynamic c = Controller(main);
            await Wait(() => c.Model?.Mesh != null && (int)c.Model.Mesh.Parts.Count > 0, 60, "the -f mesh is imported");
            // Menu parity: the Avalonia menu shows each original top menu with its text and state, in every view
            var menuView = window.GetVisualDescendants().OfType<MenuStripView>().First();
            foreach (string tab in new[] { "Geometry", "FE Model", "Results", "FE Model" })
            {
                var tabs = All(main).OfType<WinForms.TabControl>().FirstOrDefault(t => t.TabPages.Cast<WinForms.TabPage>().Any(p => p.Text == tab));
                if (tabs != null)
                {
                    int index = tabs.TabPages.Cast<WinForms.TabPage>().ToList().FindIndex(p => p.Text == tab);
                    Ui.Input(() => tabs.SelectedIndex = index);
                    await Pump(0.5);
                }
                var model = main.MainMenuStrip.Items.Cast<WinForms.ToolStripItem>().ToList();
                var shown = menuView.Items.Cast<MenuItem>().ToList();
                bool same = model.Count == shown.Count && model.Zip(shown, (m, a) =>
                    a.IsEnabled == m.Enabled && a.IsVisible == m.Visible && Equals(a.Header, Ui.AccessText(m.Text))).All(x => x);
                Check("menu parity in the " + tab + " view", same, string.Join(", ", model.Where(m => !m.Enabled).Select(m => m.Text.Replace("&", ""))) + " disabled");
            }
            // The original icons are found where the application runs (a package keeps them in app/resources)
            var withImages = Walk(main.MainMenuStrip.Items.Cast<WinForms.ToolStripItem>()).Where(i => i.Image != null).ToList();
            int drawn = withImages.Count(i => Ui.Bitmap(i.Image) != null);
            Check("the application icon loads", Ui.AppIcon != null, Ui.Root);
            Check("menu icons load", withImages.Count > 20 && drawn == withImages.Count, drawn + " of " + withImages.Count + " from " + Ui.Root);
            // Authoring first: a static step through FrmStep's list and OK (forms_gui_probe); the step entries below need it
            var step = await OpenFromMenu(main, "tsmiCreateStep", "FrmStep");
            var types = All(step).OfType<WinForms.ListView>().First(l => l.Visible);
            var staticItem = types.Items.Cast<WinForms.ListViewItem>().FirstOrDefault(i => i.Text == "Static Step");
            Check("FrmStep lists the original step types", staticItem != null, string.Join(", ", types.Items.Cast<WinForms.ListViewItem>().Select(i => i.Text)));
            Ui.Input(() => { staticItem.Selected = true; });
            await Pump(0.3);
            CheckMirrored("FrmStep with a step type: controls mirrored", step);
            var gridView = Ui.Windows[step].GetVisualDescendants().OfType<PropertyGridView>().FirstOrDefault(g => g.IsEffectivelyVisible);
            Check("FrmStep's property grid drawn with rows", gridView != null && gridView.RowCount > 2, gridView?.Describe());
            Press(step, "btnOK");
            await Pump(1);
            int steps = (int)c.GetAllSteps().Length;
            Check("OK runs the original OnApply: step created", steps >= 1 && !step.Visible, steps);
            // Every create form of the main menu: original entry point, designer client size, mirrored controls, Cancel
            bool Reachable(WinForms.ToolStripItem item)
            {
                for (var i = item; i != null; i = i.OwnerItem) if (!i.Enabled || !i.Visible) return false;
                return true;
            }
            var creates = Walk(main.MainMenuStrip.Items.Cast<WinForms.ToolStripItem>())
                .OfType<WinForms.ToolStripMenuItem>().Where(i => i.Name.StartsWith("tsmiCreate", StringComparison.Ordinal) && Reachable(i) && i.DropDownItems.Count == 0)
                .Select(i => i.Name).Distinct().ToList();
            Check("create entries enabled with a mesh", creates.Count >= 15, string.Join(", ", creates));
            foreach (string name in creates)
            {
                int commands = Commands(main);
                // An entry that asks for a file first (Create and Import) opens no form when the dialog is cancelled
                int dialogs = s_fileDialogs;
                var before = ShownForms(main);
                Ui.Input(MenuItem(main, name).PerformClick);
                DateTime end = DateTime.UtcNow.AddSeconds(10);
                while (DateTime.UtcNow < end && s_fileDialogs == dialogs && !ShownForms(main).Except(before).Any()) await Pump(0.1);
                if (s_fileDialogs != dialogs && !ShownForms(main).Except(before).Any())
                {
                    Check(name + ": asks for a file (dialog cancelled, nothing changed)", Commands(main) == commands);
                    continue;
                }
                Check(name + " opens a form", ShownForms(main).Except(before).Any());
                await Pump(0.5);
                // The form and the selection form it shows beside it (FrmSelectItemSet)
                foreach (var form in ShownForms(main).Except(before).OrderBy(f => f.GetType().Name == "FrmSelectItemSet" ? 1 : 0))
                {
                    var avalonia = Ui.Windows[form];
                    bool Sized() => avalonia.IsVisible && (int)avalonia.ClientSize.Width == form.ClientSize.Width && (int)avalonia.ClientSize.Height == form.ClientSize.Height;
                    DateTime until = DateTime.UtcNow.AddSeconds(3);
                    while (!Sized() && DateTime.UtcNow < until) await Pump(0.1);
                    Check(name + ": " + form.GetType().Name + " window at its client size", Sized(), avalonia.ClientSize + " for " + form.ClientSize + " min " + form.MinimumSize + " max " + form.MaximumSize + " avalonia min " + avalonia.MinWidth + "x" + avalonia.MinHeight + " max " + avalonia.MaxWidth + "x" + avalonia.MaxHeight + " size " + form.Size + " window W/H " + avalonia.Width + "x" + avalonia.Height + " state " + avalonia.WindowState + " fit " + avalonia.SizeToContent + " bounds " + avalonia.Bounds);
                    CheckMirrored(name + ": " + form.GetType().Name + " controls mirrored at their bounds", form);
                }
                var opened = ShownForms(main).Except(before).OrderBy(f => f.GetType().Name == "FrmSelectItemSet" ? 1 : 0).ToList();
                var form0 = opened.First();
                Press(form0, "btnCancel");
                await Pump(0.5);
                foreach (var other in ShownForms(main)) Press(other, "btnCancel", "btnClose");
                await Pump(0.3);
                Check(name + ": Cancel hides the forms and changes nothing", opened.All(f => !f.Visible && !Ui.Windows[f].IsVisible) && Commands(main) == commands,
                      string.Join(", ", opened.Where(f => f.Visible || Ui.Windows[f].IsVisible).Select(f => f.GetType().Name + (f.Visible ? "" : " (window only)"))) + " commands " + commands + " -> " + Commands(main));
            }
            // Authoring: an amplitude through the data grid; the plot of its rows (forms_gui_probe_grid)
            var amplitude = await OpenFromMenu(main, "tsmiCreateAmplitude", "FrmAmplitude");
            var dgv = All(amplitude).OfType<WinForms.DataGridView>().First();
            var tabsOf = All(amplitude).OfType<WinForms.TabControl>().First();
            Ui.Input(() => tabsOf.SelectedIndex = 1);
            await Pump(0.5);
            var gridDrawn = Ui.Windows[amplitude].GetVisualDescendants().OfType<DataGridView>().FirstOrDefault(g => g.IsEffectivelyVisible);
            Check("FrmAmplitude's data points drawn in their tab", gridDrawn != null && dgv.RowCount >= 1, dgv.RowCount);
            int rows = dgv.RowCount;
            Ui.Input(() => { dgv.CurrentCell = dgv[0, rows - 1]; dgv.BeginEdit(true); dgv.EditingControl.Text = "1"; dgv.EndEdit(); });
            Ui.Input(() => { dgv.CurrentCell = dgv[1, rows - 1]; dgv.BeginEdit(true); dgv.EditingControl.Text = "1"; dgv.EndEdit(); });
            await Pump(0.5);
            Check("a cell edit in the new row adds a data point", dgv.RowCount == rows + 1, dgv.RowCount);
            CheckMirrored("FrmAmplitude with its data points: controls mirrored", amplitude);
            Press(amplitude, "btnOK");
            await Pump(1);
            Check("OK created the amplitude", ((System.Collections.ICollection)c.GetAmplitudeNames()).Count >= 1 && !amplitude.Visible);
            // The original material library beside the application (materials.lib), read through the type allowlist; the
            // original shows it modally (ShowDialog), so it is inspected while open and then cancelled
            string libraryFile = Path.Combine(WinForms.Application.StartupPath, "materials.lib");
            string libraryForm = null; int libraryMaterials = -1; bool libraryListed = false;
            s_onModal = form =>
            {
                libraryForm = form.GetType().Name;
                var libraries = Field<WinForms.ListView>(form, "lvLibraries");
                libraryListed = libraries != null && libraries.Items.ContainsKey(libraryFile);
                if (!libraryListed) return;
                libraries.SelectedIndices.Clear();
                libraries.Items[libraryFile].Selected = true;
                libraryMaterials = 0;
                void CountNodes(WinForms.TreeNodeCollection nodes) { foreach (WinForms.TreeNode n in nodes) { if (n.Tag != null) libraryMaterials++; CountNodes(n.Nodes); } }
                CountNodes(Field<WinForms.TreeView>(form, "cltvLibrary").Nodes);
            };
            var libraryEntry = MenuItem(main, "tsmiMaterialLibrary");
            Check("tsmiMaterialLibrary enabled", libraryEntry != null && libraryEntry.Enabled);
            Ui.Input(libraryEntry.PerformClick);
            await Wait(() => libraryForm != null && !ShownForms(main).Any(f => f.GetType().Name == "FrmMaterialLibrary"), 15, "the material library opens and closes");
            Check("the original material library lists materials.lib with its materials", libraryForm == "FrmMaterialLibrary" && libraryListed && libraryMaterials >= 10,
                  libraryForm + "; " + (File.Exists(libraryFile) ? "" : libraryFile + " missing; ") + (libraryListed ? "" : "not listed; ") + libraryMaterials + " materials");
            // The code editor: FrmEditCommands with the history in the original editor (forms_gui_probe_editor)
            var editItem = Walk(main.MainMenuStrip.Items.Cast<WinForms.ToolStripItem>()).FirstOrDefault(i => i.Name == "tsmiEditCommands" || i.Name == "tsmiEditHistory");
            if (editItem != null && editItem.Enabled)
            {
                var edit = await OpenFromMenu(main, editItem.Name, null);
                List<CodeView> Codes() => Ui.Windows[edit].GetVisualDescendants().OfType<CodeView>().Where(v => v.IsEffectivelyVisible).ToList();
                // The history grid lists every command; View > Python shows the history as a script (forms_gui_probe_editor)
                var commandsGrid = Field<WinForms.DataGridView>(edit, "dgvCommands");
                Check("the history grid lists every command", commandsGrid != null && commandsGrid.Rows.Count == Commands(main), commandsGrid?.Rows.Count + " of " + Commands(main));
                var split = Field<WinForms.SplitContainer>(edit, "splMain");
                if (split != null && split.Panel2Collapsed)
                {
                    var show = Walk(edit.MainMenuStrip?.Items.Cast<WinForms.ToolStripItem>() ?? Enumerable.Empty<WinForms.ToolStripItem>()).FirstOrDefault(i => i.Name == "tsmiShowPython")
                               ?? Walk(All(edit).OfType<WinForms.MenuStrip>().SelectMany(m => m.Items.Cast<WinForms.ToolStripItem>())).FirstOrDefault(i => i.Name == "tsmiShowPython");
                    Check("View > Python in FrmEditCommands", show != null);
                    Ui.Input(show.PerformClick);
                }
                DateTime until = DateTime.UtcNow.AddSeconds(5);
                while (!Codes().Any(v => v.Code.LinesCount > 1) && DateTime.UtcNow < until) await Pump(0.2);
                var models = All(edit).OfType<FastColoredTextBoxNS.FastColoredTextBox>().ToList();
                Check("View > Python draws the history script in the code view", Codes().Any(v => v.Code.LinesCount > 1),
                      edit.GetType().Name + ": drawn " + string.Join(", ", Codes().Select(v => v.Code.LinesCount)) + "; model " +
                      string.Join(", ", models.Select(m => m.Name + " " + m.LinesCount + " lines" + (Shown(m) ? "" : " hidden by " +
                          string.Join(" < ", Ancestors(m).Where(a => !a.Visible || a is WinForms.TabPage).Select(a => a.GetType().Name + " " + a.Name + (a.Visible ? "" : " (not visible)")))))));
                CheckMirrored(edit.GetType().Name + ": controls mirrored", edit);
                Press(edit, "btnCancel", "btnClose");
                await Pump(0.5);
            }
            else Check("Edit - Commands in the menu", false, editItem == null ? "missing" : "disabled");
        }

        // CAD import and meshing (geometry_gui_probe)
        static async Task GeometryArea(FormWindow window, WinForms.Form main, ViewHost host, string output)
        {
            dynamic c = Controller(main);
            await Wait(() => c.Model?.Geometry != null && (int)c.Model.Geometry.Parts.Count > 0, 60, "the -f geometry is imported");
            Check("geometry parts", true, (int)c.Model.Geometry.Parts.Count);
            // Mesh > Create Mesh: one part is meshed at once (SelectMultipleEntities); several open FrmSelectEntity
            var entry = MenuItem(main, "tsmiCreateMesh");
            Check("Mesh > Create Mesh enabled with geometry", entry != null && entry.Enabled);
            var before = ShownForms(main);
            Ui.Input(entry.PerformClick);
            await Pump(1);
            foreach (var form in ShownForms(main).Except(before).ToList())
            {
                CheckMirrored(form.GetType().Name + ": controls mirrored", form);
                Press(form, "btnOK");
            }
            await Wait(() => c.Model?.Mesh != null && (int)c.Model.Mesh.Parts.Count > 0 && (int)c.Model.Mesh.Elements.Count > 0, 120, "Netgen meshes the part");
            Check("mesh elements", true, (int)c.Model.Mesh.Elements.Count);
            await ViewShows(host, output, "the view shows the mesh");
        }

        // Analysis, CalculiX, FrmMonitor and results (results_gui_probe)
        static async Task ResultsArea(FormWindow window, WinForms.Form main, ViewHost host, string output)
        {
            dynamic c = Controller(main);
            await Wait(() => c.Model?.Mesh != null && (int)c.Model.Mesh.Parts.Count > 0, 60, "the -f project is opened");
            var analysis = await OpenFromMenu(main, "tsmiCreateAnalysis", "FrmAnalysis");
            CheckMirrored("FrmAnalysis: controls mirrored", analysis);
            Press(analysis, "btnOK");
            await Pump(1);
            var names = ((IEnumerable<string>)c.GetJobNames()).ToList();
            Check("OK creates the analysis", names.Count >= 1 && !analysis.Visible, string.Join(", ", names));
            // Run through FrmMain.RunAnalysis (the tree's Run and the menu end there)
            var run = main.GetType().GetMethod("RunAnalysis", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public, null, new[] { typeof(string) }, null);
            Check("FrmMain.RunAnalysis", run != null);
            s_answer = WinForms.DialogResult.Yes;
            Ui.Input(() => run.Invoke(main, new object[] { names[0] }));
            await Wait(() => ShownForms(main).Any(f => f.GetType().Name == "FrmMonitor"), 20, "the original FrmMonitor shows the run");
            var monitor = ShownForms(main).First(f => f.GetType().Name == "FrmMonitor");
            CheckMirrored("FrmMonitor: controls mirrored", monitor);
            dynamic job = c.GetJob(names[0]);
            await Wait(() => job.JobStatus.ToString() != "Running" && job.JobStatus.ToString() != "None", 240, "CalculiX finishes");
            Check("the analysis completes", job.JobStatus.ToString() == "OK", job.JobStatus.ToString());
            Press(monitor, "btnResults");
            await Wait(() => c.CurrentResult != null && c.CurrentResult.Mesh != null, 60, "the results open");
            await Pump(1);
            var variable = Field<WinForms.ToolStripComboBox>(main, "tscbDeformationVariable");
            var increments = Field<WinForms.ToolStripComboBox>(main, "tscbStepAndIncrement");
            Check("the result controls list the variables and increments", variable != null && variable.Items.Count > 0 && variable.Enabled &&
                  increments != null && increments.Items.Count > 0, variable?.Items.Count + " variables, " + increments?.Items.Count + " increments");
            int fieldNodes = All(main).OfType<WinForms.TreeView>().Sum(tree => tree.GetNodeCount(true));
            Check("the results tree lists the fields", fieldNodes > 10, fieldNodes);
            Press(monitor, "btnClose");
            await ViewShows(host, output, "the view shows the result");
        }

        // The original element classes (elements_gui_probe)
        static async Task ElementsArea(FormWindow window, WinForms.Form main, ViewHost host, string output)
        {
            dynamic c = Controller(main);
            await Wait(() => c.Model?.Mesh != null && (int)c.Model.Mesh.Elements.Count > 0, 60, "the -f deck is imported");
            var kinds = ((IEnumerable<object>)c.Model.Mesh.Elements.Values).Select(e => e.GetType().Name).Distinct().ToList();
            Check("original element classes", kinds.Count >= 1, string.Join(", ", kinds));
            int nodes = All(main).OfType<WinForms.TreeView>().Sum(tree => tree.GetNodeCount(true));
            Check("the model tree shows the deck", nodes > 10, nodes);
            await ViewShows(host, output, "the view shows the elements");
            var set = await OpenFromMenu(main, "tsmiCreateElementSet", null);
            CheckMirrored(set.GetType().Name + ": controls mirrored", set);
            Press(set, "btnCancel");
            await Pump(0.5);
        }

        static async Task ViewShows(ViewHost host, string output, string name)
        {
            await Pump(1);
            string png = output + "-" + s_area + "-view.png";
            host.Capture(png);
            int colors = File.Exists(png) ? Colors(png) : 0;
            Check(name, colors > 10, colors);
        }
    }
}
