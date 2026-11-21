// Unattended checks of the original FrmMain on Avalonia (PREPOMAXX_UI_PROBE=avalonia, report in
// PREPOMAXX_UI_PROBE_OUTPUT.json with the view and window images): the checks of X/UI/app_gui_probe.py (menus, tool
// strips, view, the -f model, the tree, the view image, an original form from the menu) and those of M3-1a (the key
// hook's Escape, the view's context menu, the property grid, a modal form, a message box). Message boxes are answered
// with their first button (or the answer a check sets); file dialogs are cancelled.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Media.Imaging;
using Avalonia.Threading;
using Avalonia.VisualTree;
using vtkControl.Native;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEnd
{
    internal static class Probe
    {
        internal static bool Active => Ui.ProbeOutput != null;
        static readonly List<string> s_prompts = new List<string>();
        static readonly List<Dictionary<string, object>> s_checks = new List<Dictionary<string, object>>();
        static WinForms.DialogResult? s_answer;
        static string s_lastModal;

        internal static WinForms.DialogResult Prompt(string caption, string text, WinForms.DialogResult[] offered)
        {
            lock (s_prompts) s_prompts.Add((caption ?? "") + ": " + text);
            return s_answer.HasValue && offered.Contains(s_answer.Value) ? s_answer.Value : offered[0];
        }
        internal static WinForms.DialogResult FileDialog(WinForms.FileDialog dialog) => WinForms.DialogResult.Cancel;
        internal static void ModalShown(WinForms.Form form)
        {
            if (!Active) return;
            s_lastModal = form.GetType().Name;
            // Unattended: the modal form is closed by its cancel button (or Close) once it is drawn
            DispatcherTimer.RunOnce(() => Ui.Input(() =>
            {
                if (!form.Visible) return;
                if (form.CancelButton != null) form.CancelButton.PerformClick(); else form.Close();
            }), TimeSpan.FromSeconds(1));
        }

        class Failed : Exception { public Failed(string message) : base(message) { } }
        static void Check(string name, bool passed, object detail = null)
        {
            var entry = new Dictionary<string, object> { ["name"] = name, ["passed"] = passed };
            if (detail != null) entry["detail"] = detail;
            s_checks.Add(entry);
            if (!passed) throw new Failed(name + (detail == null ? "" : ": " + detail));
        }

        static async Task Pump(double seconds)
        {
            Ui.Step("probe pump " + seconds);
            DateTime end = DateTime.UtcNow.AddSeconds(seconds);
            while (DateTime.UtcNow < end) { Ui.Flush(); await Task.Delay(50); }
            Ui.Flush();
        }
        static async Task Wait(Func<bool> condition, double seconds, string name)
        {
            DateTime end = DateTime.UtcNow.AddSeconds(seconds);
            while (DateTime.UtcNow < end) { await Pump(0.1); if (condition()) return; }
            string shown = string.Join(", ", WinForms.Application.OpenForms.Cast<WinForms.Form>().Where(f => f.Visible && f != Ui.MainForm).Select(f => f.GetType().Name + " " + f.Text));
            Check(name, false, "timed out; open forms: " + shown);
        }
        static IEnumerable<WinForms.ToolStripItem> Walk(IEnumerable<WinForms.ToolStripItem> items)
        {
            foreach (var item in items)
            {
                yield return item;
                if (item is WinForms.ToolStripDropDownItem drop) foreach (var child in Walk(drop.DropDownItems.Cast<WinForms.ToolStripItem>())) yield return child;
            }
        }
        static IEnumerable<WinForms.Control> All(WinForms.Control control)
        {
            foreach (WinForms.Control child in control.Controls) { yield return child; foreach (var d in All(child)) yield return d; }
        }
        static int Colors(string png)
        {
            using var bitmap = new Bitmap(png);
            var size = bitmap.PixelSize;
            var pixels = new byte[size.Width * size.Height * 4];
            var handle = System.Runtime.InteropServices.GCHandle.Alloc(pixels, System.Runtime.InteropServices.GCHandleType.Pinned);
            try { bitmap.CopyPixels(new PixelRect(size), handle.AddrOfPinnedObject(), pixels.Length, size.Width * 4); }
            finally { handle.Free(); }
            var colors = new HashSet<int>();
            for (int y = 0; y < size.Height; y += Math.Max(1, size.Height / 40))
                for (int x = 0; x < size.Width; x += Math.Max(1, size.Width / 40))
                    colors.Add(BitConverter.ToInt32(pixels, (y * size.Width + x) * 4));
            return colors.Count;
        }
        static T Field<T>(object owner, string name) where T : class =>
            owner.GetType().GetField(name, System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public)?.GetValue(owner) as T;

        internal static void Start(FormWindow window)
        {
            if (!Active) return;
            string output = Ui.ProbeOutput;
            // A hung run ends with its report so far (as faulthandler's dump_traceback_later in the Qt probe)
            double timeout = double.TryParse(Environment.GetEnvironmentVariable("PREPOMAXX_UI_PROBE_TIMEOUT"), out double t) ? t : 240;
            new Thread(() => { Thread.Sleep(TimeSpan.FromSeconds(timeout)); Write(output, false, "timeout after " + timeout + " s"); Environment.Exit(3); }) { IsBackground = true }.Start();
            Dispatcher.UIThread.Post(async () => await Run(window, output), DispatcherPriority.Background);
        }

        static void Write(string output, bool success, string error)
        {
            var report = new Dictionary<string, object> { ["success"] = success, ["frontEnd"] = "avalonia", ["checks"] = s_checks.ToList() };
            if (error != null) report["error"] = error;
            lock (s_prompts) report["messageBoxes"] = s_prompts.ToList();
            File.WriteAllText(output + ".json", JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
        }

        static async Task Run(FormWindow window, string output)
        {
            bool success = false;
            string error = null;
            WinForms.Form form = window.Form;
            try
            {
                await Pump(1);
                var menu = form.MainMenuStrip;
                Check("the original menu strip", menu != null);
                var top = menu.Items.Cast<WinForms.ToolStripItem>().Select(i => i.Text.Replace("&", "")).ToList();
                Check("16 original menus", top.Count == 16, string.Join(", ", top));
                int strips = window.Mirrors.Count(m => m.Value.Visual is MenuStripView || m.Value.Visual is ToolStripView);
                Check("menu, 5 tool strips and the status strip", strips == 7, strips);
                var host = window.GetVisualDescendants().OfType<ViewHost>().FirstOrDefault();
                await Wait(() => host != null && host.Attached && host.Control.NativeMirror != null, 20, "the original vtkControl in a native host");
                Check("the original vtkControl in a native host", true);
                // FrmMain.Controller (the original assembly is not referenced here)
                int Parts() { dynamic controller = form.GetType().GetProperty("Controller")?.GetValue(form); return controller?.Model?.Mesh == null ? 0 : (int)controller.Model.Mesh.Parts.Count; }
                await Wait(() => Parts() > 0, 60, "the -f model is imported");
                Check("mesh parts", Parts() > 0, Parts());
                int nodes = All(form).OfType<WinForms.TreeView>().Sum(tree => tree.GetNodeCount(true));
                Check("the original model tree shows the model", nodes > 10, nodes);
                await Pump(1);
                string png = output + "-view.png";
                host.Capture(png);
                int colors = File.Exists(png) ? Colors(png) : 0;
                Check("the view shows the model", colors > 10, colors);
                // A middle-button drag turns the view (the pointer path of the native host)
                var centre = new Point(host.Bounds.Width / 2, host.Bounds.Height / 2);
                host.SendForProbe(VtkNativeInput.MouseMove, centre);
                host.SendForProbe(VtkNativeInput.MiddleButtonDown, centre);
                for (int i = 1; i <= 10; i++) host.SendForProbe(VtkNativeInput.MouseMove, new Point(centre.X + i * 15, centre.Y + i * 5));
                host.SendForProbe(VtkNativeInput.MiddleButtonUp, new Point(centre.X + 150, centre.Y + 50));
                await Pump(0.5);
                string turned = output + "-view-turned.png";
                host.Capture(turned);
                Check("a drag turns the view", File.Exists(turned) && !File.ReadAllBytes(turned).SequenceEqual(File.ReadAllBytes(png)));
                // An original form from the original menu (Property - Material - Create) with its property grid
                var item = Walk(menu.Items.Cast<WinForms.ToolStripItem>()).First(i => i.Name == "tsmiCreateMaterial");
                Check("Create Material enabled with a mesh", item.Enabled);
                Ui.Input(item.PerformClick);
                await Pump(1);
                var shown = Ui.Windows.Where(p => p.Key != form && p.Key.Visible && p.Value.IsVisible).Select(p => p.Key).ToList();
                Check("FrmMaterial shown from the menu", shown.Any(f => f.GetType().Name == "FrmMaterial"), string.Join(", ", shown.Select(f => f.GetType().Name)));
                var material = shown.First(f => f.GetType().Name == "FrmMaterial");
                // A material model (Elastic) chosen in the original tree and added: the grid shows its properties
                var models = Field<WinForms.TreeView>(material, "tvProperties");
                WinForms.TreeNode Find(WinForms.TreeNodeCollection nodes, string text)
                {
                    foreach (WinForms.TreeNode node in nodes) { if (node.Text == text) return node; var found = Find(node.Nodes, text); if (found != null) return found; }
                    return null;
                }
                var elastic = Find(models.Nodes, "Elastic");
                var b = elastic.Bounds;
                Ui.Input(() => { models.UserMouseDown(WinForms.MouseButtons.Left, 1, b.X + 5, b.Y + 5); models.UserMouseUp(WinForms.MouseButtons.Left, 1, b.X + 5, b.Y + 5); });
                Ui.Input(() => Field<WinForms.Button>(material, "btnAdd").PerformClick());
                await Pump(0.5);
                var grids = Ui.Windows[material].GetVisualDescendants().OfType<PropertyGridView>().ToList();
                Check("its property grid shows rows", grids.Sum(g => g.RowCount) > 2, string.Join("; ", grids.Select(g => g.Describe())));
                // Escape: the original key hook closes the property forms when FrmMain is the active form
                Ui.Input(form.Activate);
                Ui.Input(() => WinForms.LowLevelKeyboardHook.Raise(WinForms.Keys.Escape, true));
                Ui.Input(() => WinForms.LowLevelKeyboardHook.Raise(WinForms.Keys.Escape, false));
                await Pump(1);
                Check("Escape closes the forms (key hook)", !material.Visible);
                // The view's context menu: a right click in the view opens the original menu where it was clicked
                host.SendForProbe(VtkNativeInput.MouseMove, centre);
                host.SendForProbe(VtkNativeInput.RightButtonDown, centre);
                host.SendForProbe(VtkNativeInput.RightButtonUp, centre);
                await Pump(1);
                var cms = Field<WinForms.ContextMenuStrip>(form, "_cmsViewport");
                var at = cms?.ShownAt ?? System.Drawing.Point.Empty;
                Check("the view's context menu opens", cms != null && cms.Visible, cms?.Visible);
                Check("in control units", Math.Abs(at.X - centre.X) <= 3 && Math.Abs(at.Y - centre.Y) <= 3, at + " vs " + centre);
                Ui.Input(() => cms.Close());
                await Pump(0.5);
                // A modal form (Help - About) through the nested loop
                var about = Walk(menu.Items.Cast<WinForms.ToolStripItem>()).FirstOrDefault(i => i.Name == "tsmiAbout");
                if (about != null)
                {
                    s_lastModal = null;
                    Ui.Input(about.PerformClick);
                    await Pump(0.5);
                    Check("a modal form opens and closes", s_lastModal != null, s_lastModal);
                }
                // A tool strip button's checked state is drawn (a checked original button shows its checked face)
                var toggles = window.GetVisualDescendants().OfType<Avalonia.Controls.Primitives.ToggleButton>().Where(b => b.Classes.Contains("tool")).ToList();
                int checkedModel = All(form).OfType<WinForms.ToolStrip>().SelectMany(s => s.Items.Cast<WinForms.ToolStripItem>()).OfType<WinForms.ToolStripButton>().Count(b => b.Checked && b.Visible);
                Check("tool buttons show the checked state", toggles.Count(b => b.IsChecked == true && b.IsEffectivelyVisible) == checkedModel, checkedModel);
                success = true;
            }
            catch (Failed) { }
            catch (Exception e) { error = e.ToString(); }
            // Images of every open window (also after a failed check)
            int n = 0;
            foreach (var pair in Ui.Windows.ToList())
            {
                if (!pair.Value.IsVisible) continue;
                try
                {
                    var w = pair.Value;
                    var size = new PixelSize(Math.Max(1, (int)w.ClientSize.Width), Math.Max(1, (int)w.ClientSize.Height));
                    using (var bitmap = new RenderTargetBitmap(size)) { bitmap.Render(w); bitmap.Save(output + "-window-" + (n++) + "-" + pair.Key.GetType().Name + ".png"); }
                }
                catch (Exception e) { error = (error ?? "") + "\n" + e.Message; }
            }
            Write(output, success, error);
            // Closing: the original asks to save the changed model; the probe leaves it unsaved
            s_answer = WinForms.DialogResult.No;
            DispatcherTimer.RunOnce(() => window.Close(), TimeSpan.FromMilliseconds(100));
        }
    }
}
