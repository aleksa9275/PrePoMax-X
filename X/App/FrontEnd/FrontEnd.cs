// The front end of the original application (M3-1a, D065/D067): FrmMain and every original form, compiled whole on
// the headless WinForms control model (X/UI/FormsCompat), drawn by Avalonia on the application's main thread. The
// control model lays the controls out and owns every behaviour; each control is mirrored by an Avalonia control at
// its bounds, and user input goes back through the events WinForms raises (PerformClick, SelectedIndex, the key hook,
// ...). This is the C# successor of the Qt renderer (X/UI/main_form.py, original_forms.py, original_controls.py):
// one runtime, no CPython in the drawing path.
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Styling;
using Avalonia.Themes.Fluent;
using Avalonia.Threading;
using CaeGlobals;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEnd
{
    /// <summary>Application.RunHandler of the original Program: the main form through Avalonia.</summary>
    public static class AvaloniaFrontEnd
    {
        public static void Run(WinForms.Form mainForm) => Ui.Run(mainForm);
        /// <summary>Unattended checks (PREPOMAXX_UI_PROBE=avalonia): set before Run, reported to the given file.</summary>
        public static string ProbeOutput { get => Ui.ProbeOutput; set => Ui.ProbeOutput = value; }
    }

    internal sealed class FrontEndApplication : Application
    {
        public override void Initialize()
        {
            Name = "PrePoMax";
            Styles.Add(new FluentTheme { DensityStyle = DensityStyle.Compact });
            Styles.Add(new Avalonia.Markup.Xaml.Styling.StyleInclude(new Uri("avares://PrePoMaxX.FrontEnd/"))
                { Source = new Uri("avares://Avalonia.Controls.ColorPicker/Themes/Fluent/Fluent.xaml") });
            RequestedThemeVariant = ThemeVariant.Light;
            Look.Add(Styles);
        }
        public override void OnFrameworkInitializationCompleted()
        {
            if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
            {
                Ui.StartMessageQueue();
                Ui.Step("framework ready");
                desktop.MainWindow = new FormWindow(Ui.MainForm, true);
                Ui.Step("main window made");
            }
            base.OnFrameworkInitializationCompleted();
        }
    }

    internal static class Ui
    {
        internal static WinForms.ToolkitSynchronizationContext Context;
        internal static WinForms.Form MainForm;
        internal static FormWindow Main;
        internal static string ProbeOutput;
        /// <summary>The window of every original form that was shown.</summary>
        internal static readonly Dictionary<WinForms.Form, FormWindow> Windows = new Dictionary<WinForms.Form, FormWindow>();
        static readonly ConcurrentQueue<(WinForms.Control Control, string Property)> s_changes = new ConcurrentQueue<(WinForms.Control, string)>();
        static int s_syncPosted;
        static bool s_syncing;
        internal static readonly string Root = FindRoot();
        internal static readonly bool Trace = Environment.GetEnvironmentVariable("PREPOMAXX_TRACE_EXCEPTIONS") == "1";
        static readonly bool s_traceStart = Environment.GetEnvironmentVariable("PREPOMAXX_TRACE_FRONT_END") == "1";
        internal static void Step(string text) { if (s_traceStart) Console.Error.WriteLine("[front end " + DateTime.Now.ToString("HH:mm:ss.fff") + "] " + text); }

        static string FindRoot()
        {
            string root = Environment.GetEnvironmentVariable("PREPOMAXX_SOURCE_ROOT");
            if (!string.IsNullOrEmpty(root)) return root;
            // A package keeps the original resource images below its application folder (local_app.py)
            string resources = Path.Combine(AppContext.BaseDirectory, "resources");
            if (Directory.Exists(resources)) return resources;
            for (var d = new DirectoryInfo(AppContext.BaseDirectory); d != null; d = d.Parent)
                if (File.Exists(Path.Combine(d.FullName, "AGENTS.md")) && Directory.Exists(Path.Combine(d.FullName, "PrePoMax"))) return d.FullName;
            return AppContext.BaseDirectory;
        }

        // Run -------------------------------------------------------------------------------------------------------------
        internal static void Run(WinForms.Form form)
        {
            MainForm = form;
            Context = WinForms.ToolkitSynchronizationContext.Install();
            Services.Install();
            WinForms.ControlNotifications.Changed += Changed;
            Step("run");
            try
            {
                AppBuilder builder = AppBuilder.Configure<FrontEndApplication>().UsePlatformDetect().LogToTrace();
                string family = Look.LayoutFamily();
                if (family != null) builder = builder.With(new FontManagerOptions { DefaultFamilyName = family });
                builder.StartWithClassicDesktopLifetime(new string[0], ShutdownMode.OnMainWindowClose);
            }
            finally
            {
                WinForms.ControlNotifications.Changed -= Changed;
                Services.Uninstall();
                if (form.Visible) Guard(() => form.Close());
            }
        }

        /// <summary>The WinForms message queue on the Avalonia loop: the calls other threads post or send
        /// (Control.Invoke/BeginInvoke, awaits) and the WinForms timers' work run here, on the main thread.</summary>
        internal static void StartMessageQueue()
        {
            new DispatcherTimer(TimeSpan.FromMilliseconds(5), DispatcherPriority.Background, (s, e) =>
            {
                foreach (Exception error in Context.Drain()) Console.Error.WriteLine(error);
                if (!s_changes.IsEmpty) Sync();
            }).Start();
            WindowCapture.Start();
        }

        // Notifications ---------------------------------------------------------------------------------------------------
        static void Changed(WinForms.Control control, string property)
        {
            s_changes.Enqueue((control, property));
            if (Interlocked.Exchange(ref s_syncPosted, 1) == 0) Dispatcher.UIThread.Post(Sync, DispatcherPriority.Normal);
        }

        /// <summary>Applies the notifications so far: windows of shown and hidden forms, refreshed contents, bounds and
        /// states of every mirrored control.</summary>
        internal static void Sync()
        {
            Interlocked.Exchange(ref s_syncPosted, 0);
            if (s_syncing) return;
            if (s_traceStart) Step("sync " + string.Join(", ", s_changes.ToArray().GroupBy(c => c.Control.GetType().Name + "." + c.Property).Select(g => g.Key + "x" + g.Count()).Take(8)));
            s_syncing = true;
            try
            {
                var forms = new HashSet<WinForms.Form>();
                var refresh = new List<(WinForms.Control, string)>();
                while (s_changes.TryDequeue(out var change))
                {
                    WinForms.Control control = change.Control;
                    if (control is WinForms.ToolStripDropDown dropDown)
                    {
                        if (change.Property == "Show") ContextMenus.Show(dropDown);
                        else if (change.Property == "Close") ContextMenus.Close(dropDown);
                        continue;
                    }
                    WinForms.Form form = control.FindForm();
                    if (form == null) continue;
                    forms.Add(form);
                    if (!(control is WinForms.Form)) refresh.Add((control, change.Property));
                }
                foreach (WinForms.Form form in forms)
                {
                    Windows.TryGetValue(form, out FormWindow window);
                    if (form.Visible && !form.IsDisposed)
                    {
                        if (window == null)
                        {
                            window = new FormWindow(form, false);
                            Windows[form] = window;
                        }
                        window.Sync();
                        if (!window.IsVisible) window.ShowForForm();
                    }
                    else if (window != null && form != MainForm) window.HideForForm();
                }
                foreach (var (control, property) in refresh)
                {
                    WinForms.Form form = control.FindForm();
                    if (form != null && Windows.TryGetValue(form, out FormWindow window)) window.Refresh(control, property);
                }
            }
            catch (Exception e) { Console.Error.WriteLine(e); }
            finally { s_syncing = false; }
        }

        /// <summary>Pending notifications applied now (modal forms and probes).</summary>
        internal static void Flush()
        {
            for (int i = 0; i < 5 && !s_changes.IsEmpty; i++) Sync();
        }

        // Input -------------------------------------------------------------------------------------------------------------
        /// <summary>Runs user input in the WinForms context of the main thread (its awaits resume there); an exception
        /// the original handlers do not catch is shown as WinForms shows it, through the original message boxes.</summary>
        internal static T Guard<T>(Func<T> action)
        {
            T result = default;
            try { Context.Run(() => result = action()); }
            catch (Exception e)
            {
                if (Trace) Console.Error.WriteLine(e);
                Exception inner = e is System.Reflection.TargetInvocationException t && t.InnerException != null ? t.InnerException : e;
                try { MessageBoxes.ShowError(inner.Message); } catch (Exception again) { Console.Error.WriteLine(again); }
            }
            return result;
        }
        internal static void Guard(Action action) => Guard(() => { action(); return 0; });
        internal static void Input(Action action) { Guard(action); RequestSync(); }
        internal static T Input<T>(Func<T> action) { T result = Guard(action); RequestSync(); return result; }
        internal static void RequestSync()
        {
            if (Interlocked.Exchange(ref s_syncPosted, 1) == 0) Dispatcher.UIThread.Post(Sync, DispatcherPriority.Normal);
        }

        /// <summary>A nested event loop until the task completes (WinForms' calls are synchronous: file dialogs,
        /// clipboard, modal forms).</summary>
        internal static T Wait<T>(Task<T> task)
        {
            if (!task.IsCompleted)
                using (var done = new CancellationTokenSource())
                {
                    task.ContinueWith(_ => Dispatcher.UIThread.Post(() => done.Cancel()), TaskScheduler.Default);
                    Dispatcher.UIThread.MainLoop(done.Token);
                }
            return task.GetAwaiter().GetResult();
        }
        internal static void Wait(Task task) => Wait(task.ContinueWith(t => { t.GetAwaiter().GetResult(); return 0; }, TaskScheduler.Default));

        // Modal forms -------------------------------------------------------------------------------------------------------
        /// <summary>Form.ShowDialog on the main thread: the form's window, modal to the active window, and a nested
        /// Avalonia loop until the form closes (a DialogResult or Close ends the WinForms modal loop).</summary>
        internal static WinForms.DialogResult ShowDialog(WinForms.Form form)
        {
            form.Show();
            Flush();
            if (Windows.TryGetValue(form, out FormWindow window) && form.Visible)
                using (var done = new CancellationTokenSource())
                {
                    var poll = new DispatcherTimer(TimeSpan.FromMilliseconds(20), DispatcherPriority.Background, (s, e) => { if (!form.Visible) done.Cancel(); });
                    poll.Start();
                    Probe.ModalShown(form);
                    Dispatcher.UIThread.MainLoop(done.Token);
                    poll.Stop();
                }
            if (Windows.TryGetValue(form, out window))
            {
                // A modal window is not reused (Avalonia keeps the modality of a window)
                Windows.Remove(form);
                window.CloseForForm();
            }
            return form.DialogResult;
        }

        // Resources ---------------------------------------------------------------------------------------------------------
        static readonly Dictionary<string, Bitmap> s_bitmaps = new Dictionary<string, Bitmap>();
        static readonly Dictionary<System.Drawing.Image, Bitmap> s_drawn = new Dictionary<System.Drawing.Image, Bitmap>();
        /// <summary>An original image: a resource file of the repository, a designer image of a form's .resx (base64
        /// bytes, nothing is deserialized), encoded bytes, or a bitmap made from one of these.</summary>
        internal static Bitmap Bitmap(System.Drawing.Image image)
        {
            switch (image)
            {
                case null: return null;
                case WinForms.ImageResource resource:
                    string key = resource.Path.EndsWith(".resx", StringComparison.OrdinalIgnoreCase) ? resource.Path + "#" + resource.Name : resource.Path;
                    if (!s_bitmaps.TryGetValue(key, out Bitmap bitmap))
                    {
                        try { bitmap = key.Contains('#') ? ResxImage(resource.Path, resource.Name) : Load(Path.Combine(Root, resource.Path)); }
                        catch (Exception e) { if (Trace) Console.Error.WriteLine(e); bitmap = null; }
                        s_bitmaps[key] = bitmap;
                    }
                    return bitmap;
                case System.Drawing.EncodedImage encoded:
                    if (!s_drawn.TryGetValue(encoded, out Bitmap decoded))
                    {
                        try { decoded = new Bitmap(new MemoryStream(encoded.Bytes)); } catch { decoded = null; }
                        s_drawn[encoded] = decoded;
                    }
                    return decoded;
                case System.Drawing.Bitmap made when made.Source != null:
                    return Bitmap(made.Source);
                case System.Drawing.Bitmap drawn when drawn.Drawing != null && drawn.Width > 0 && drawn.Height > 0:
                    // Drawn by the original code (Graphics.FromImage): the recorded drawing, rasterized
                    var target = new RenderTargetBitmap(new PixelSize(drawn.Width, drawn.Height));
                    using (DrawingContext context = target.CreateDrawingContext())
                        Painting.Replay(context, drawn.Drawing.Commands, new Size(drawn.Width, drawn.Height));
                    return target;
                default: return null;
            }
        }
        static Dictionary<string, string> s_named;
        /// <summary>An image of an image list by its key name (a designer image list keeps its images in a serialized
        /// .resx stream, which is not read; its keys are the names of the original icon files).</summary>
        internal static Bitmap Named(string name)
        {
            if (string.IsNullOrEmpty(name)) return null;
            if (s_named == null)
            {
                s_named = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
                foreach (string folder in new[] { "UserControls/Resources", "PrePoMax/Icons", "PrePoMax/Resources" })
                {
                    string path = Path.Combine(Root, folder);
                    if (!Directory.Exists(path)) continue;
                    foreach (string file in Directory.EnumerateFiles(path, "*.*", SearchOption.AllDirectories))
                        if (!s_named.ContainsKey(Path.GetFileName(file))) s_named[Path.GetFileName(file)] = Path.GetRelativePath(Root, file);
                }
            }
            return s_named.TryGetValue(name, out string relative) ? Bitmap(new WinForms.ImageResource(name, relative)) : null;
        }
        static WindowIcon s_appIcon;
        static bool s_appIconRead;
        /// <summary>The original application icon (PrePoMax/main.ico).</summary>
        internal static WindowIcon AppIcon
        {
            get
            {
                if (!s_appIconRead)
                {
                    s_appIconRead = true;
                    string file = Path.Combine(Root, "PrePoMax/main.ico");
                    try { if (File.Exists(file)) s_appIcon = new WindowIcon(file); }
                    catch (Exception e) { if (Trace) Console.Error.WriteLine(e); }
                }
                return s_appIcon;
            }
        }
        static Bitmap Load(string file) => File.Exists(file) ? new Bitmap(file) : null;
        static Bitmap ResxImage(string path, string name)
        {
            string file = Path.Combine(Root, path);
            if (!File.Exists(file)) return null;
            foreach (var data in System.Xml.Linq.XDocument.Load(file).Root.Elements("data"))
                if ((string)data.Attribute("name") == name && ((string)data.Attribute("mimetype") ?? "").Contains("base64"))
                {
                    string text = string.Concat(((string)data.Element("value") ?? "").Where(c => !char.IsWhiteSpace(c)));
                    return new Bitmap(new MemoryStream(Convert.FromBase64String(text)));
                }
            return null;
        }

        internal static Image Icon(System.Drawing.Image image, double size = 16)
        {
            Bitmap bitmap = Bitmap(image);
            return bitmap == null ? null : new Image { Source = bitmap, Width = size, Height = size, Stretch = Stretch.Uniform };
        }

        internal static IBrush Brush(System.Drawing.Color color) => new SolidColorBrush(ToColor(color));
        /// <summary>A colour; system colours are those of Windows 10, which the original is designed with (.NET's table
        /// on macOS and Linux has the Windows XP values).</summary>
        internal static Color ToColor(System.Drawing.Color color)
        {
            if (color.IsSystemColor)
                switch (color.ToKnownColor())
                {
                    case System.Drawing.KnownColor.Control: case System.Drawing.KnownColor.ButtonFace: case System.Drawing.KnownColor.Menu:
                    case System.Drawing.KnownColor.MenuBar: return Color.FromRgb(0xF0, 0xF0, 0xF0);
                    case System.Drawing.KnownColor.Window: case System.Drawing.KnownColor.ControlLightLight: case System.Drawing.KnownColor.ButtonHighlight:
                    case System.Drawing.KnownColor.HighlightText: return Colors.White;
                    case System.Drawing.KnownColor.ControlText: case System.Drawing.KnownColor.WindowText: case System.Drawing.KnownColor.MenuText:
                    case System.Drawing.KnownColor.InfoText: return Colors.Black;
                    case System.Drawing.KnownColor.ControlDark: case System.Drawing.KnownColor.ButtonShadow: return Color.FromRgb(0xA0, 0xA0, 0xA0);
                    case System.Drawing.KnownColor.ControlDarkDark: return Color.FromRgb(0x69, 0x69, 0x69);
                    case System.Drawing.KnownColor.ControlLight: return Color.FromRgb(0xE3, 0xE3, 0xE3);
                    case System.Drawing.KnownColor.Highlight: case System.Drawing.KnownColor.HotTrack: return Color.FromRgb(0x00, 0x78, 0xD7);
                    case System.Drawing.KnownColor.GrayText: return Color.FromRgb(0x6D, 0x6D, 0x6D);
                    case System.Drawing.KnownColor.AppWorkspace: return Color.FromRgb(0xAB, 0xAB, 0xAB);
                    case System.Drawing.KnownColor.Info: return Color.FromRgb(0xFF, 0xFF, 0xE1);
                    case System.Drawing.KnownColor.ActiveCaption: return Color.FromRgb(0x99, 0xB4, 0xD1);
                    case System.Drawing.KnownColor.InactiveBorder: return Color.FromRgb(0xF4, 0xF7, 0xFC);
                    case System.Drawing.KnownColor.ScrollBar: return Color.FromRgb(0xC8, 0xC8, 0xC8);
                }
            return Color.FromArgb(color.A, color.R, color.G, color.B);
        }
        internal static string Visible(string text) => WinForms.OrderedNameComparer.Visible(text ?? "");
        /// <summary>A WinForms text with '&' mnemonics as an Avalonia access text ('_').</summary>
        internal static string AccessText(string text) =>
            Visible(text).Replace("_", "__").Replace("&&", "\u0001").Replace("&", "_").Replace("\u0001", "&");
    }
}
