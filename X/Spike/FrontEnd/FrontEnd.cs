// M3-1 toolkit spike (D065): FrmMain, compiled whole on the FormsCompat control model, drawn by Avalonia.
// What the spike answers (X/Spike/FrontEnd/README.md): one thread and one runtime for the control model and the
// renderer; the original vtkControl in an Avalonia NativeControlHost (an NSView on macOS, an X11 window on Linux);
// the input of the view; menus, tool strips and controls mirrored at the bounds the WinForms model lays out.
// Deliberately generic and incomplete: no property grid, data grid or paint replay - those follow the toolkit choice.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Input;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Media.Imaging;
using Avalonia.Platform;
using Avalonia.Threading;
using vtkControl.Native;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEndSpike
{
    internal static class FrontEnd
    {
        internal static WinForms.ToolkitSynchronizationContext Context;
        internal static readonly string Root = FindRoot();
        internal static readonly Probe Probe = new Probe();
        /// <summary>The window of every shown original form.</summary>
        internal static readonly Dictionary<WinForms.Form, FormWindow> Windows = new Dictionary<WinForms.Form, FormWindow>();
        internal static FormWindow Main;
        static bool s_dirty = true, s_syncing;
        static string FindRoot()
        {
            for (var d = new DirectoryInfo(AppContext.BaseDirectory); d != null; d = d.Parent)
                if (File.Exists(Path.Combine(d.FullName, "AGENTS.md")) && Directory.Exists(Path.Combine(d.FullName, "PrePoMax"))) return d.FullName;
            return Environment.GetEnvironmentVariable("PREPOMAXX_SOURCE_ROOT") ?? "";
        }

        /// <summary>Application.RunHandler: Avalonia's event loop on this (the main) thread is the WinForms message loop.</summary>
        internal static void Run(WinForms.Form form)
        {
            Context = WinForms.ToolkitSynchronizationContext.Install();
            CaeGlobals.MessageBoxes.UiDispatcher = Context.Dispatcher;
            WinForms.Form.CreateControlsOnShow = true;
            WinForms.Form.ShowDialogHandler = ShowDialog;
            SpikeApplication.MainForm = form;
            WinForms.Application.DoEventsHandler = () => { if (Context.IsUiThread) Dispatcher.UIThread.RunJobs(); };
            WinForms.Application.ExitHandler = () =>
                (Avalonia.Application.Current?.ApplicationLifetime as IClassicDesktopStyleApplicationLifetime)?.Shutdown();
            WinForms.ControlNotifications.Changed += Changed;
            if (Environment.GetEnvironmentVariable("PREPOMAXX_SPIKE_TRACE_LAYOUT") == "1")
            {
                // Diagnosis: every change of FrmMain's view/output splitter, with the stack that made it
                var split = (WinForms.SplitContainer)form.GetType().GetField("splitContainer2",
                    System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).GetValue(form);
                string last = null;
                WinForms.ControlNotifications.Changed += (c, p) =>
                {
                    if (c != split) return;
                    string now = "size=" + split.Size + " distance=" + split.SplitterDistance + " panel2=" + split.Panel2.Height;
                    if (now == last) return;
                    last = now;
                    Console.WriteLine("[layout] " + now + "\n" + string.Join("\n", Environment.StackTrace.Split('\n').Skip(3).Take(9)));
                };
            }
            try
            {
                AppBuilder.Configure<SpikeApplication>().UsePlatformDetect().LogToTrace()
                    .StartWithClassicDesktopLifetime(new string[0], ShutdownMode.OnMainWindowClose);
            }
            finally
            {
                WinForms.ControlNotifications.Changed -= Changed;
                WinForms.Form.ShowDialogHandler = null;
                WinForms.Application.ExitHandler = null;
                WinForms.Application.DoEventsHandler = null;
                CaeGlobals.MessageBoxes.UiDispatcher = null;
            }
        }

        /// <summary>The WinForms message queue on the Avalonia loop: posted and sent calls of other threads, timers;
        /// then the mirrors follow the control model.</summary>
        internal static void StartMessageQueue()
        {
            new DispatcherTimer(TimeSpan.FromMilliseconds(5), DispatcherPriority.Background, (s, e) =>
            {
                foreach (Exception error in Context.Drain()) Console.Error.WriteLine(error);
                if (s_dirty && !s_syncing)
                {
                    s_dirty = false; s_syncing = true;
                    try { foreach (FormWindow window in Windows.Values.ToList()) window.Sync(); }
                    finally { s_syncing = false; }
                }
            }).Start();
        }

        static void Changed(WinForms.Control control, string property)
        {
            s_dirty = true;
            if (!(control is WinForms.Form form) || form == SpikeApplication.MainForm) return;
            if (property == "Show" && form.Visible && !Windows.ContainsKey(form)) Open(form);
            else if ((property == "Close" || !form.Visible) && Windows.TryGetValue(form, out FormWindow window))
            {
                Windows.Remove(form);
                window.CloseFromModel();
            }
        }

        static FormWindow Open(WinForms.Form form)
        {
            var window = new FormWindow(form, Context, false);
            Windows[form] = window;
            Probe.Add("formWindows", 1);
            if (form.Modal && Main != null && Main.IsVisible) window.ShowDialog(Main);
            else window.Show();
            return window;
        }

        /// <summary>Form.ShowDialog on the user-interface thread: the form's window and a nested Avalonia loop until
        /// the form closes (a DialogResult or Close ends the WinForms modal loop).</summary>
        static WinForms.DialogResult ShowDialog(WinForms.Form form)
        {
            Probe.Add("modalForms", 1);
            form.Show();
            if (!Windows.ContainsKey(form) && form.Visible) Open(form);
            if (!string.IsNullOrEmpty(Environment.GetEnvironmentVariable("PREPOMAXX_SPIKE_PROBE")))
                // Unattended: the probe records the dialog, then presses its accept button (the nested loop must end)
                DispatcherTimer.RunOnce(() =>
                {
                    Probe.Set("modalForm", form.GetType().Name + " \"" + form.Text + "\" window=" + Windows.ContainsKey(form) +
                        " accept=" + (form.AcceptButton != null));
                    Context.Run(() => { if (form.AcceptButton != null) form.AcceptButton.PerformClick(); else form.Close(); });
                }, TimeSpan.FromSeconds(1.5));
            using (var done = new CancellationTokenSource())
            {
                var poll = new DispatcherTimer(TimeSpan.FromMilliseconds(20), DispatcherPriority.Background, (s, e) => { if (!form.Visible) done.Cancel(); });
                poll.Start();
                Dispatcher.UIThread.MainLoop(done.Token);
                poll.Stop();
            }
            return form.DialogResult;
        }
    }

    /// <summary>The window of an original form: its client area as nested canvases, one per original control at its
    /// bounds.</summary>
    internal sealed class FormWindow : Window
    {
        readonly WinForms.Form _form;
        readonly WinForms.ToolkitSynchronizationContext _ui;
        readonly Canvas _client = new Canvas();
        readonly Dictionary<WinForms.Control, Mirror> _mirrors = new Dictionary<WinForms.Control, Mirror>();
        static readonly Dictionary<string, Bitmap> s_images = new Dictionary<string, Bitmap>();
        bool _closingFromModel;
        Probe Probe => FrontEnd.Probe;

        public FormWindow(WinForms.Form form, WinForms.ToolkitSynchronizationContext ui, bool main)
        {
            _form = form; _ui = ui;
            Content = _client;
            _client.Background = Brushes.White;
            if (main)
            {
                Title = "PrePoMax (Avalonia spike)";
                FrontEnd.Main = this;
                FrontEnd.Windows[form] = this;
                var started = DateTime.UtcNow;
                // Load and Shown run in the WinForms synchronization context, as on the WinForms thread
                _ui.Run(() => _form.Show());
                Probe.Set("formShownSeconds", (DateTime.UtcNow - started).TotalSeconds);
                Width = Math.Min(1400, Math.Max(800, _form.Width));
                Height = Math.Min(900, Math.Max(600, _form.Height));
                Opened += (s, e) => { Resized(); Probe.Start(this); };
            }
            else
            {
                Title = form.Text;
                Width = Math.Max(100, form.ClientSize.Width);
                Height = Math.Max(60, form.ClientSize.Height);
                CanResize = form.FormBorderStyle == WinForms.FormBorderStyle.Sizable || form.FormBorderStyle == WinForms.FormBorderStyle.SizableToolWindow;
                WindowStartupLocation = WindowStartupLocation.CenterOwner;
                Opened += (s, e) => Sync();
            }
            Closing += (s, e) =>
            {
                if (_closingFromModel || !_form.Visible) return;
                // The window close button: the form decides (FormClosing may cancel)
                bool closed = false;
                _ui.Run(() => closed = _form.CloseByUser());
                if (!closed) e.Cancel = true;
            };
        }

        internal void CloseFromModel() { _closingFromModel = true; Close(); }

        protected override void OnPropertyChanged(AvaloniaPropertyChangedEventArgs change)
        {
            base.OnPropertyChanged(change);
            // Also raised by the base constructor, before this window has its form
            if (change.Property == ClientSizeProperty && _form != null) Resized();
        }

        void Resized()
        {
            var size = new System.Drawing.Size((int)Math.Round(ClientSize.Width), (int)Math.Round(ClientSize.Height));
            if (size.Width > 0 && size.Height > 0 && _form.ClientSize != size) _ui.Run(() => _form.ClientSize = size);
            Sync();
        }

        /// <summary>Mirrors the control tree: creates what is new, moves and updates what exists, drops what left.</summary>
        internal void Sync()
        {
            var seen = new HashSet<WinForms.Control>();
            SyncChildren(_form, _client, seen);
            foreach (var gone in _mirrors.Keys.Where(c => !seen.Contains(c)).ToList())
            {
                var mirror = _mirrors[gone];
                (mirror.Frame.Parent as Panel)?.Children.Remove(mirror.Frame);
                _mirrors.Remove(gone);
            }
            if (this == FrontEnd.Main) Probe.Set("mirroredControls", _mirrors.Count);
        }

        void SyncChildren(WinForms.Control parent, Canvas target, HashSet<WinForms.Control> seen)
        {
            var children = parent.Controls.Cast<WinForms.Control>().ToList();
            // WinForms: index 0 is in front; Avalonia draws later children in front
            for (int i = children.Count - 1, z = 0; i >= 0; i--, z++)
            {
                WinForms.Control control = children[i];
                seen.Add(control);
                if (!_mirrors.TryGetValue(control, out Mirror mirror))
                {
                    mirror = new Mirror(control, Create(control));
                    _mirrors[control] = mirror;
                }
                if (mirror.Frame.Parent != target)
                {
                    (mirror.Frame.Parent as Panel)?.Children.Remove(mirror.Frame);
                    target.Children.Add(mirror.Frame);
                }
                mirror.Frame.ZIndex = z;
                var b = control.Bounds;
                Canvas.SetLeft(mirror.Frame, b.X); Canvas.SetTop(mirror.Frame, b.Y);
                mirror.Frame.Width = Math.Max(0, b.Width); mirror.Frame.Height = Math.Max(0, b.Height);
                if (mirror.Visual != null) { mirror.Visual.Width = mirror.Frame.Width; mirror.Visual.Height = mirror.Frame.Height; }
                // A tab control shows its selected page only
                bool visible = control.Visible && !(parent is WinForms.TabControl tabs && control is WinForms.TabPage && tabs.SelectedTab != control);
                mirror.Frame.IsVisible = visible;
                mirror.Update?.Invoke();
                if (visible && !(control is vtkControl.vtkControl)) SyncChildren(control, mirror.Frame, seen);
            }
        }

        sealed class Mirror
        {
            public readonly Canvas Frame = new Canvas { ClipToBounds = true };
            public readonly Control Visual;
            public Action Update;
            public Mirror(WinForms.Control control, (Control Visual, Action Update) created)
            {
                Visual = created.Visual;
                if (Visual != null) Frame.Children.Add(Visual);
                Update = created.Update;
            }
        }

        (Control, Action) Create(WinForms.Control control)
        {
            switch (control)
            {
                case vtkControl.vtkControl view:
                    var host = new ViewHost(view, Probe);
                    return (host, null);
                case WinForms.MenuStrip menu:
                    var bar = new Menu();
                    var top = menu.Items.Cast<WinForms.ToolStripItem>().ToList();
                    var entries = top.Select(MenuEntry).ToList();
                    bar.ItemsSource = entries;
                    if (this == FrontEnd.Main) Probe.Add("menuItems", Count(menu.Items));
                    return (bar, () =>
                    {
                        for (int i = 0; i < top.Count; i++)
                            if (entries[i] is MenuItem m) { m.IsEnabled = top[i].Enabled; m.IsVisible = top[i].Visible; }
                    });
                case WinForms.StatusStrip status:
                    var labels = new StackPanel { Orientation = Orientation.Horizontal, Background = Brushes.WhiteSmoke };
                    return (labels, () =>
                    {
                        labels.Children.Clear();
                        foreach (WinForms.ToolStripItem item in status.Items)
                            if (item.Visible) labels.Children.Add(new TextBlock { Text = item.Text, Margin = new Thickness(4, 2), FontSize = 12 });
                    });
                case WinForms.ToolStrip strip:
                    var tools = new StackPanel { Orientation = Orientation.Horizontal, Background = Brushes.WhiteSmoke };
                    var items = strip.Items.Cast<WinForms.ToolStripItem>().ToList();
                    foreach (WinForms.ToolStripItem item in items) tools.Children.Add(ToolEntry(item));
                    if (this == FrontEnd.Main) Probe.Add("toolStripItems", strip.Items.Count);
                    return (tools, () =>
                    {
                        for (int i = 0; i < items.Count; i++)
                        {
                            tools.Children[i].IsEnabled = items[i].Enabled; tools.Children[i].IsVisible = items[i].Visible;
                            if (tools.Children[i] is Button { Content: TextBlock t }) t.Text = items[i].Text;
                        }
                    });
                case WinForms.Button button:
                    var b = new Button { Content = button.Text, Padding = new Thickness(2), FontSize = 12 };
                    b.Click += (s, e) => _ui.Run(() => button.PerformClick());
                    return (b, () => b.Content = button.Text);
                case WinForms.TextBoxBase text:
                    // TextBox, RichTextBox and FrmMain's output window (UserControls.OutputTextBox)
                    var box = new TextBox { Text = text.Text, FontSize = 12, Padding = new Thickness(2), MinHeight = 0,
                        IsReadOnly = text.ReadOnly, AcceptsReturn = text.Multiline, TextWrapping = text.Multiline ? TextWrapping.Wrap : TextWrapping.NoWrap };
                    box.LostFocus += (s, e) => _ui.Run(() => text.Text = box.Text);
                    return (box, () => { if (!box.IsFocused) box.Text = text.Text; });
                case WinForms.Label label:
                    var t = new TextBlock { Text = label.Text, FontSize = 12 };
                    return (t, () => t.Text = label.Text);
                case WinForms.TreeView tree:
                    var nodes = new TreeView { FontSize = 12 };
                    return (nodes, () => nodes.ItemsSource = tree.Nodes.Cast<WinForms.TreeNode>().Select(TreeEntry).ToList());
                case WinForms.TabControl tabs:
                    // The header row above the pages (FormsCompat lays the pages out below a 24-unit row)
                    var headers = new StackPanel { Orientation = Orientation.Horizontal, Height = 24, VerticalAlignment = VerticalAlignment.Top };
                    var tabFrame = new Canvas();
                    tabFrame.Children.Add(headers);
                    int selected = -2;
                    return (tabFrame, () =>
                    {
                        headers.Width = tabFrame.Width;
                        if (headers.Children.Count == tabs.TabPages.Count && selected == tabs.SelectedIndex) return;
                        selected = tabs.SelectedIndex;
                        headers.Children.Clear();
                        for (int i = 0; i < tabs.TabPages.Count; i++)
                        {
                            int index = i;
                            var header = new Button { Content = tabs.TabPages[i].Text, FontSize = 12, Padding = new Thickness(8, 2), Height = 24,
                                Background = i == tabs.SelectedIndex ? Brushes.White : Brushes.Gainsboro, CornerRadius = new CornerRadius(3, 3, 0, 0) };
                            header.Click += (s, e) => _ui.Run(() => tabs.SelectedIndex = index);
                            headers.Children.Add(header);
                        }
                    });
                case WinForms.SplitContainer split:
                    // The splitter bar between the panels: dragging it moves the splitter (SplitContainer.UserMoveSplitter)
                    // Above the panels (only the bar takes the mouse: the canvas has no background)
                    var splitFrame = new Canvas { ZIndex = 1000 };
                    bool vertical = split.Orientation == WinForms.Orientation.Vertical;
                    var splitBar = new Border { Background = Brushes.WhiteSmoke, Cursor = new Cursor(vertical ? StandardCursorType.SizeWestEast : StandardCursorType.SizeNorthSouth) };
                    splitFrame.Children.Add(splitBar);
                    bool dragging = false;
                    splitBar.PointerPressed += (s, e) => { dragging = true; e.Pointer.Capture(splitBar); e.Handled = true; };
                    splitBar.PointerReleased += (s, e) => { dragging = false; e.Pointer.Capture(null); e.Handled = true; };
                    splitBar.PointerMoved += (s, e) =>
                    {
                        if (!dragging) return;
                        Point p = e.GetPosition(splitFrame);
                        int distance = (int)Math.Round((vertical ? p.X : p.Y) - split.SplitterWidth / 2.0);
                        _ui.Run(() => split.UserMoveSplitter(distance));
                        e.Handled = true;
                    };
                    return (splitFrame, () =>
                    {
                        var r = split.SplitterRectangle;
                        splitBar.IsVisible = !split.Panel1Collapsed && !split.Panel2Collapsed;
                        // A few units wider than the splitter, so it is easy to take
                        Canvas.SetLeft(splitBar, vertical ? r.X - 2 : r.X); Canvas.SetTop(splitBar, vertical ? r.Y : r.Y - 2);
                        splitBar.Width = vertical ? r.Width + 4 : r.Width; splitBar.Height = vertical ? r.Height : r.Height + 4;
                    });
                case FastColoredTextBoxNS.FastColoredTextBox code:
                    // FrmMain's output window (UserControls.OutputTextBox) and the code editors: their text, read only here
                    var lines = new TextBox { IsReadOnly = true, FontFamily = new FontFamily("Menlo, Consolas, monospace"), FontSize = 11,
                        TextWrapping = TextWrapping.NoWrap, AcceptsReturn = true, BorderThickness = new Thickness(0), Padding = new Thickness(4, 2), MinHeight = 0 };
                    string shown = null;
                    return (lines, () =>
                    {
                        string text = code.Text;
                        if (text == shown) return;
                        shown = text;
                        lines.Text = text;
                        lines.CaretIndex = text.Length;     // the newest message, as the original scrolls to it
                    });
                default:
                    return (new Border { BorderBrush = Brushes.Gainsboro, BorderThickness = new Thickness(0) }, null);
            }
        }

        static int Count(WinForms.ToolStripItemCollection items) =>
            items.Cast<WinForms.ToolStripItem>().Sum(i => 1 + (i is WinForms.ToolStripDropDownItem d ? Count(d.DropDownItems) : 0));

        object MenuEntry(WinForms.ToolStripItem item)
        {
            if (item is WinForms.ToolStripSeparator) return new Separator();
            var entry = new MenuItem { Header = item.Text?.Replace("&", "_"), IsEnabled = item.Enabled, IsVisible = item.Visible, Icon = Icon(item.Image) };
            if (item is WinForms.ToolStripDropDownItem drop && drop.DropDownItems.Count > 0)
            {
                // The original fills some menus when they open (DropDownOpening)
                entry.SubmenuOpened += (s, e) =>
                {
                    if (e.Source != entry) return;
                    _ui.Run(() => drop.RaiseDropDownOpening());
                    entry.ItemsSource = drop.DropDownItems.Cast<WinForms.ToolStripItem>().Select(MenuEntry).ToList();
                };
                entry.ItemsSource = drop.DropDownItems.Cast<WinForms.ToolStripItem>().Select(MenuEntry).ToList();
            }
            else entry.Click += (s, e) => _ui.Run(() => item.PerformClick());
            return entry;
        }

        Control ToolEntry(WinForms.ToolStripItem item)
        {
            if (item is WinForms.ToolStripSeparator) return new Border { Width = 1, Margin = new Thickness(3, 2), Background = Brushes.Silver };
            Image icon = Icon(item.Image);
            var button = new Button
            {
                Content = icon != null ? icon : new TextBlock { Text = item.Text, FontSize = 12 },
                Padding = new Thickness(3), Background = Brushes.Transparent, IsEnabled = item.Enabled, IsVisible = item.Visible,
            };
            ToolTip.SetTip(button, string.IsNullOrEmpty(item.ToolTipText) ? item.Text : item.ToolTipText);
            button.Click += (s, e) => _ui.Run(() => item.PerformClick());
            return button;
        }

        object TreeEntry(WinForms.TreeNode node) =>
            new TreeViewItem { Header = node.Text, IsExpanded = node.IsExpanded, ItemsSource = node.Nodes.Cast<WinForms.TreeNode>().Select(TreeEntry).ToList() };

        /// <summary>An original resource image (an image file of the repository; .resx images are left out here).</summary>
        Image Icon(System.Drawing.Image image)
        {
            if (!(image is WinForms.ImageResource resource) || resource.Path.EndsWith(".resx", StringComparison.OrdinalIgnoreCase)) return null;
            if (!s_images.TryGetValue(resource.Path, out Bitmap bitmap))
            {
                string file = Path.Combine(FrontEnd.Root, resource.Path);
                bitmap = File.Exists(file) ? new Bitmap(file) : null;
                s_images[resource.Path] = bitmap;
            }
            return bitmap == null ? null : new Image { Source = bitmap, Width = 16, Height = 16 };
        }
    }

    /// <summary>The original vtkControl in a native child window of the Avalonia window: VTK creates its OpenGL view in
    /// it (VtkNativeHost.AttachNativeWindow); Avalonia's pointer and key events go to the interaction style.</summary>
    internal sealed class ViewHost : NativeControlHost, Avalonia.Rendering.ICustomHitTest
    {
        // Avalonia hit-tests what is drawn; the native view draws nothing in Avalonia's scene
        public bool HitTest(Point point) => new Rect(Bounds.Size).Contains(point);
        readonly vtkControl.vtkControl _control;
        readonly Probe _probe;
        bool _attached;
        int _wheel;
        DispatcherTimer _events;

        public ViewHost(vtkControl.vtkControl control, Probe probe)
        {
            _control = control; _probe = probe;
            Focusable = true;
        }

        protected override IPlatformHandle CreateNativeControlCore(IPlatformHandle parent)
        {
            IPlatformHandle handle = base.CreateNativeControlCore(parent);
            if (OperatingSystem.IsMacOS())
            {
                // Avalonia's native host view keeps the mouse to itself; transparent to hit testing, the clicks over the
                // view reach Avalonia's window and this control (VTK's own view is made transparent by VtkNativeHost)
                vtkControl.Native.CocoaPassThrough.ApplyToView(handle.Handle);
                // Device pixels (sharp on Retina), the view pinned to the host. The original's overlays (scale bar, axes)
                // are placed in control units, so they are misplaced until the DPI model is decided (M3-1 report)
                vtkControl.Native.VtkNativeHost.DeviceScale = TopLevel.GetTopLevel(this)?.RenderScaling ?? 1;
                vtkControl.Native.VtkNativeHost.FitViewToHost = true;
            }
            _probe.Set("viewHandleDescriptor", handle.HandleDescriptor);
            Dispatcher.UIThread.Post(() => Attach(handle.Handle), DispatcherPriority.Loaded);
            return handle;
        }

        void Attach(IntPtr window)
        {
            if (_attached) return;
            _attached = true;
            FrontEnd.Context.Run(() =>
            {
                _control.NativeHost.AttachNativeWindow(window);
                _control.RaiseLoad();
                _control.EnableNativeMirror(true);
            });
            _probe.Set("viewCreated", _control.NativeMirror != null);
            if (OperatingSystem.IsLinux())
            {
                _events = new DispatcherTimer(TimeSpan.FromMilliseconds(10), DispatcherPriority.Background, (s, e) => _control.NativeHost.ProcessEvents());
                _events.Start();
            }
        }

        protected override void DestroyNativeControlCore(IPlatformHandle control)
        {
            _events?.Stop();
            if (_attached) { _attached = false; FrontEnd.Context.Run(() => _control.NativeHost.DetachNativeWindow()); }
            base.DestroyNativeControlCore(control);
        }

        bool Send(VtkNativeInput input, Point position, KeyModifiers modifiers, int keyCode = 0, string symbol = null)
        {
            VtkNativeView view = _attached ? _control.NativeMirror : null;
            _probe.Add("viewInputs", 1);
            // PREPOMAXX_SPIKE_TRACE_INPUT=1: every input the view gets from Avalonia (moves only when a button is down)
            if (TraceInput && (input != VtkNativeInput.MouseMove || _buttonDown))
                Console.WriteLine("[view input] " + input + " at " + (int)position.X + "," + (int)position.Y + (view == null ? " (no view)" : ""));
            if (input == VtkNativeInput.LeftButtonDown || input == VtkNativeInput.MiddleButtonDown || input == VtkNativeInput.RightButtonDown) _buttonDown = true;
            else if (input == VtkNativeInput.LeftButtonUp || input == VtkNativeInput.MiddleButtonUp || input == VtkNativeInput.RightButtonUp) _buttonDown = false;
            if (view == null) return false;
            // VTK's display coordinates: device pixels (VtkNativeHost.DeviceScale)
            double ratio = vtkControl.Native.VtkNativeHost.DeviceScale;
            bool control = (modifiers & (KeyModifiers.Control | KeyModifiers.Meta)) != 0, shift = (modifiers & KeyModifiers.Shift) != 0;
            FrontEnd.Context.Run(() => view.HandleInput(input, (int)Math.Round(position.X * ratio),
                (int)Math.Round((Bounds.Height - position.Y) * ratio), control, shift, keyCode, symbol));
            return true;
        }

        internal WinForms.Control Original => _control;
        static readonly bool TraceInput = Environment.GetEnvironmentVariable("PREPOMAXX_SPIKE_TRACE_INPUT") == "1";
        bool _buttonDown;
        internal bool SendForProbe(VtkNativeInput input, Point position) => Send(input, position, KeyModifiers.None);

        protected override void OnPointerPressed(PointerPressedEventArgs e)
        {
            Focus();
            var kind = e.GetCurrentPoint(this).Properties.PointerUpdateKind;
            VtkNativeInput? input = kind == PointerUpdateKind.LeftButtonPressed ? VtkNativeInput.LeftButtonDown :
                kind == PointerUpdateKind.MiddleButtonPressed ? VtkNativeInput.MiddleButtonDown :
                kind == PointerUpdateKind.RightButtonPressed ? VtkNativeInput.RightButtonDown : (VtkNativeInput?)null;
            if (input.HasValue && Send(input.Value, e.GetPosition(this), e.KeyModifiers)) e.Handled = true;
        }

        protected override void OnPointerReleased(PointerReleasedEventArgs e)
        {
            var kind = e.GetCurrentPoint(this).Properties.PointerUpdateKind;
            VtkNativeInput? input = kind == PointerUpdateKind.LeftButtonReleased ? VtkNativeInput.LeftButtonUp :
                kind == PointerUpdateKind.MiddleButtonReleased ? VtkNativeInput.MiddleButtonUp :
                kind == PointerUpdateKind.RightButtonReleased ? VtkNativeInput.RightButtonUp : (VtkNativeInput?)null;
            if (input.HasValue && Send(input.Value, e.GetPosition(this), e.KeyModifiers)) e.Handled = true;
        }

        protected override void OnPointerMoved(PointerEventArgs e) { if (Send(VtkNativeInput.MouseMove, e.GetPosition(this), e.KeyModifiers)) e.Handled = true; }
        protected override void OnPointerExited(PointerEventArgs e) => Send(VtkNativeInput.Leave, default, e.KeyModifiers);

        protected override void OnPointerWheelChanged(PointerWheelEventArgs e)
        {
            // One wheel event per notch, as Win32 and Cocoa give them; trackpads add up
            _wheel += (int)Math.Round(e.Delta.Y * 120);
            while (Math.Abs(_wheel) >= 120)
            {
                int step = _wheel > 0 ? 120 : -120;
                _wheel -= step;
                Send(step > 0 ? VtkNativeInput.WheelForward : VtkNativeInput.WheelBackward, e.GetPosition(this), e.KeyModifiers);
            }
            e.Handled = true;
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            string symbol = e.Key switch
            {
                Key.Left => "Left", Key.Up => "Up", Key.Right => "Right", Key.Down => "Down", Key.Escape => "Escape",
                Key.Return => "Return", Key.Space => "space", Key.Delete => "Delete", _ => e.KeySymbol,
            };
            int code = e.KeySymbol is { Length: 1 } s && s[0] < 256 ? s[0] : 0;
            if (Send(VtkNativeInput.KeyPress, default, e.KeyModifiers, code, symbol)) e.Handled = true;
        }

        protected override void OnKeyUp(KeyEventArgs e) { if (Send(VtkNativeInput.KeyRelease, default, e.KeyModifiers)) e.Handled = true; }

        internal void Capture(string path) => FrontEnd.Context.Run(() => _control.NativeMirror?.WritePng(path, 1));
    }

    /// <summary>Unattended spike measurements (PREPOMAXX_SPIKE_PROBE = output JSON): start-up, mirrored controls, the
    /// view, a menu command, input to the view, and images of the view and the window.</summary>
    internal sealed class Probe
    {
        readonly Dictionary<string, object> _values = new Dictionary<string, object>();
        public void Set(string key, object value) { lock (_values) _values[key] = value; }
        public void Add(string key, int value) { lock (_values) _values[key] = (_values.TryGetValue(key, out object v) ? (int)v : 0) + value; }

        static IEnumerable<WinForms.Control> AllControls(WinForms.Control control)
        {
            foreach (WinForms.Control child in control.Controls)
            {
                yield return child;
                foreach (var d in AllControls(child)) yield return d;
            }
        }

        public void Start(FormWindow window)
        {
            string output = Environment.GetEnvironmentVariable("PREPOMAXX_SPIKE_PROBE");
            if (string.IsNullOrEmpty(output)) return;
            string folder = Path.GetDirectoryName(output);
            Set("mainThread", Environment.CurrentManagedThreadId);
            Set("renderScaling", window.RenderScaling);
            // For OS-level input (an external script posts real mouse events): the screen point of the view centre
            // in points, and the input count before them
            DispatcherTimer point = null;
            point = new DispatcherTimer(TimeSpan.FromMilliseconds(500), DispatcherPriority.Background, (s, e) =>
            {
                var view = window.GetVisualDescendantsOfType<ViewHost>().FirstOrDefault();
                if (view == null || view.Bounds.Width <= 0 || !view.IsEffectivelyVisible) return;
                point.Stop();
                PixelPoint p = view.PointToScreen(new Point(view.Bounds.Width / 2, view.Bounds.Height / 2));
                double scale = window.Screens.ScreenFromWindow(window)?.Scaling ?? window.RenderScaling;
                Add("viewInputs", 0);
                lock (_values) Set("viewInputsBeforeOsEvents", _values["viewInputs"]);
                File.WriteAllText(Path.Combine(folder, "view-point.txt"), (p.X / scale) + " " + (p.Y / scale));
            });
            point.Start();
            DispatcherTimer.RunOnce(() =>
            {
                try
                {
                    var host = window.GetVisualDescendantsOfType<ViewHost>().FirstOrDefault();
                    lock (_values) Set("viewInputsAfterOsEvents", _values.TryGetValue("viewInputs", out object n) ? n : 0);
                    host?.Capture(Path.Combine(folder, "view-os.png"));
                    Set("viewHostBounds", host == null ? null : host.Bounds.ToString());
                    var chain = new List<string>();
                    for (Visual v = host; v != null; v = Avalonia.VisualTree.VisualExtensions.GetVisualParent(v))
                        chain.Add(v.GetType().Name + " visible=" + v.IsVisible + " bounds=" + v.Bounds + (v is Layoutable l ? " size=" + l.Width + "x" + l.Height : ""));
                    Set("viewHostChain", chain);
                    var controls = new List<string>();
                    for (WinForms.Control c = host?.Original; c != null; c = c.Parent)
                        controls.Add(c.GetType().Name + " " + c.Name + " visible=" + c.Visible + " bounds=" + c.Bounds);
                    Set("viewControlChain", controls);
                    var menu = SpikeApplication.MainForm.Controls.Cast<WinForms.Control>().OfType<WinForms.MenuStrip>().FirstOrDefault()
                        ?? AllControls(SpikeApplication.MainForm).OfType<WinForms.MenuStrip>().FirstOrDefault();
                    Set("menuEnabled", menu?.Items.Cast<WinForms.ToolStripItem>().Select(i => i.Text + "=" + i.Enabled).ToList());
                    if (host != null)
                    {
                        host.Capture(Path.Combine(folder, "view-before.png"));
                        // A middle-button drag (PrePoMax turns the view with it) through the input path of the pointer events
                        var c = new Point(host.Bounds.Width / 2, host.Bounds.Height / 2);
                        host.SendForProbe(VtkNativeInput.MouseMove, c);
                        host.SendForProbe(VtkNativeInput.MiddleButtonDown, c);
                        for (int i = 1; i <= 10; i++) host.SendForProbe(VtkNativeInput.MouseMove, new Point(c.X + i * 15, c.Y + i * 5));
                        host.SendForProbe(VtkNativeInput.MiddleButtonUp, new Point(c.X + 150, c.Y + 50));
                        host.Capture(Path.Combine(folder, "view-after.png"));
                    }
                    var size = new PixelSize((int)window.ClientSize.Width, (int)window.ClientSize.Height);
                    using (var bitmap = new RenderTargetBitmap(size))
                    {
                        bitmap.Render(window);
                        bitmap.Save(Path.Combine(folder, "window.png"));
                    }
                    Set("formClientSize", SpikeApplication.MainForm.ClientSize.ToString());
                }
                catch (Exception e) { Set("error", e.ToString()); }
                lock (_values) File.WriteAllText(output, JsonSerializer.Serialize(_values, new JsonSerializerOptions { WriteIndented = true }));
                window.Close();
            }, TimeSpan.FromSeconds(double.TryParse(Environment.GetEnvironmentVariable("PREPOMAXX_SPIKE_PROBE_DELAY"), out double d) ? d : 4));
        }
    }

    internal static class VisualExtensions
    {
        public static IEnumerable<T> GetVisualDescendantsOfType<T>(this Visual visual) where T : Visual =>
            Avalonia.VisualTree.VisualExtensions.GetVisualDescendants(visual).OfType<T>();
    }
}
