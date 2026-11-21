// The toolkit services of the WinForms control model, supplied by Avalonia (as X/UI/original_controls.py
// ToolkitServices did with Qt): modal forms, message boxes, timers, file dialogs, text measurement, the clipboard,
// the screens, DoEvents and Exit.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Platform.Storage;
using Avalonia.Threading;
using CaeGlobals;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEnd
{
    internal static class Services
    {
        static readonly Dictionary<WinForms.Timer, DispatcherTimer> s_timers = new Dictionary<WinForms.Timer, DispatcherTimer>();

        internal static void Install()
        {
            CaeGlobals.MessageBoxes.UiDispatcher = Ui.Context.Dispatcher;
            MessageBoxes.InteractivePresenter = MessageBoxWindow.Present;
            MessageBoxes.Mode = MessageBoxModeEnum.Interactive;
            WinForms.MessageBox.CloseHandler = handle => Dispatcher.UIThread.Post(MessageBoxWindow.CloseActive);
            // WinForms creates the controls of a shown form at once: FrmMain.Load adds the view, which loads there
            WinForms.Form.CreateControlsOnShow = true;
            WinForms.Form.ShowDialogHandler = Ui.ShowDialog;
            WinForms.Application.DoEventsHandler = () => { if (Ui.Context.IsUiThread) { Dispatcher.UIThread.RunJobs(); Ui.Flush(); } };
            WinForms.Application.ExitHandler = () =>
                (Application.Current?.ApplicationLifetime as IClassicDesktopStyleApplicationLifetime)?.Shutdown();
            WinForms.Timer.StateChanged += TimerChanged;
            WinForms.FileDialog.ShowHandler = FileDialog;
            WinForms.TextRenderer.MeasureHandler = (text, font) => Measure(text, font);
            System.Drawing.Graphics.MeasureHandler = (text, font) =>
            {
                var size = Measure(text, font as System.Drawing.Font ?? WinForms.Control.DefaultFont);
                return new System.Drawing.SizeF(size.Width, size.Height);
            };
            WinForms.Clipboard.GetTextHandler = () => Ui.Wait(TopLevel.GetTopLevel(Ui.Main)?.Clipboard?.GetTextAsync() ?? System.Threading.Tasks.Task.FromResult("")) ?? "";
            WinForms.Clipboard.SetTextHandler = text => { var c = TopLevel.GetTopLevel(Ui.Main)?.Clipboard; if (c != null) Ui.Wait(c.SetTextAsync(text ?? "")); };
        }

        internal static void Uninstall()
        {
            WinForms.Timer.StateChanged -= TimerChanged;
            foreach (DispatcherTimer timer in s_timers.Values) timer.Stop();
            s_timers.Clear();
            WinForms.Form.ShowDialogHandler = null;
            WinForms.Application.ExitHandler = null;
            WinForms.Application.DoEventsHandler = null;
            WinForms.FileDialog.ShowHandler = null;
            WinForms.MessageBox.CloseHandler = null;
            WinForms.Clipboard.GetTextHandler = null;
            WinForms.Clipboard.SetTextHandler = null;
            CaeGlobals.MessageBoxes.UiDispatcher = null;
            MessageBoxes.InteractivePresenter = null;
        }

        /// <summary>The screens in control units (the window system's points).</summary>
        internal static void UpdateScreens(Window window)
        {
            var screens = window.Screens?.All;
            if (screens == null || screens.Count == 0) return;
            var ordered = screens.OrderByDescending(s => s.IsPrimary).Select(s =>
            {
                PixelRect r = s.WorkingArea;
                double k = s.Scaling;
                return new System.Drawing.Rectangle((int)(r.X / k), (int)(r.Y / k), (int)(r.Width / k), (int)(r.Height / k));
            }).ToArray();
            WinForms.Screen.SetScreens(ordered);
        }

        // Timers --------------------------------------------------------------------------------------------------------
        static void TimerChanged(WinForms.Timer timer)
        {
            // A timer may be started on another thread; its ticks run on the main thread, as WinForms' do
            Dispatcher.UIThread.Post(() =>
            {
                s_timers.TryGetValue(timer, out DispatcherTimer avalonia);
                if (!timer.Enabled) { avalonia?.Stop(); return; }
                if (avalonia == null)
                {
                    avalonia = new DispatcherTimer(DispatcherPriority.Normal);
                    avalonia.Tick += (s, e) => Ui.Input(timer.RaiseTick);
                    s_timers[timer] = avalonia;
                }
                avalonia.Interval = TimeSpan.FromMilliseconds(Math.Max(1, timer.Interval));
                avalonia.Stop();
                avalonia.Start();
            });
        }

        // Text measurement --------------------------------------------------------------------------------------------
        static readonly Dictionary<(string, float, bool), double> s_lineHeights = new Dictionary<(string, float, bool), double>();
        internal static System.Drawing.Size Measure(string text, System.Drawing.Font font)
        {
            double size = Math.Max(1, Math.Round(font.Size * 96 / 72));
            var typeface = new Typeface(FontFamily.Default, FontStyle.Normal, font.Bold ? FontWeight.Bold : FontWeight.Normal);
            var formatted = new FormattedText(text ?? "", System.Globalization.CultureInfo.InvariantCulture, FlowDirection.LeftToRight, typeface, size, Brushes.Black);
            return new System.Drawing.Size((int)Math.Ceiling(formatted.WidthIncludingTrailingWhitespace), (int)Math.Ceiling(formatted.Height));
        }

        // File dialogs ---------------------------------------------------------------------------------------------------
        /// <summary>"Text files|*.txt;*.csv|All|*.*" as the file types of the platform dialog.</summary>
        static List<FilePickerFileType> Filters(string filter)
        {
            var types = new List<FilePickerFileType>();
            string[] parts = (filter ?? "").Split('|');
            for (int i = 0; i + 1 < parts.Length; i += 2)
                types.Add(new FilePickerFileType(parts[i]) { Patterns = parts[i + 1].Split(';').Select(p => p.Trim()).Where(p => p.Length > 0).ToList() });
            return types;
        }

        static WinForms.DialogResult FileDialog(WinForms.FileDialog dialog, WinForms.IWin32Window owner)
        {
            if (Probe.Active) return Probe.FileDialog(dialog);
            TopLevel top = ActiveWindow();
            IStorageProvider storage = top?.StorageProvider;
            if (storage == null) return WinForms.DialogResult.Cancel;
            string start = !string.IsNullOrEmpty(dialog.FileName) && Path.IsPathRooted(dialog.FileName) ? Path.GetDirectoryName(dialog.FileName) : dialog.InitialDirectory;
            IStorageFolder folder = !string.IsNullOrEmpty(start) && Directory.Exists(start) ? Ui.Wait(storage.TryGetFolderFromPathAsync(start)) : null;
            List<FilePickerFileType> types = Filters(dialog.Filter);
            if (dialog.FilterIndex > 1 && dialog.FilterIndex <= types.Count)
            {
                // WinForms' FilterIndex (1-based) is the selected type: the platform dialog takes the first
                var chosen = types[dialog.FilterIndex - 1];
                types.RemoveAt(dialog.FilterIndex - 1);
                types.Insert(0, chosen);
            }
            string[] paths;
            if (dialog.IsSave)
            {
                IStorageFile file = Ui.Wait(storage.SaveFilePickerAsync(new FilePickerSaveOptions
                {
                    Title = string.IsNullOrEmpty(dialog.Title) ? "Save As" : dialog.Title,
                    SuggestedFileName = Path.GetFileName(dialog.FileName ?? ""),
                    SuggestedStartLocation = folder,
                    DefaultExtension = dialog.DefaultExt,
                    FileTypeChoices = types,
                    ShowOverwritePrompt = (dialog as WinForms.SaveFileDialog)?.OverwritePrompt ?? true,
                }));
                paths = file == null ? new string[0] : new[] { file.TryGetLocalPath() };
            }
            else
            {
                var files = Ui.Wait(storage.OpenFilePickerAsync(new FilePickerOpenOptions
                {
                    Title = string.IsNullOrEmpty(dialog.Title) ? "Open" : dialog.Title,
                    AllowMultiple = (dialog as WinForms.OpenFileDialog)?.Multiselect ?? false,
                    SuggestedStartLocation = folder,
                    FileTypeFilter = types,
                }));
                paths = files.Select(f => f.TryGetLocalPath()).ToArray();
            }
            paths = paths.Where(p => !string.IsNullOrEmpty(p)).ToArray();
            if (paths.Length == 0) return WinForms.DialogResult.Cancel;
            dialog.FileName = paths[0];
            dialog.FileNames = paths;
            return WinForms.DialogResult.OK;
        }

        internal static string Folder(string current)
        {
            IStorageProvider storage = ActiveWindow()?.StorageProvider;
            if (storage == null) return null;
            IStorageFolder start = !string.IsNullOrEmpty(current) && Directory.Exists(current) ? Ui.Wait(storage.TryGetFolderFromPathAsync(current)) : null;
            var folders = Ui.Wait(storage.OpenFolderPickerAsync(new FolderPickerOpenOptions { Title = "Select folder", SuggestedStartLocation = start }));
            return folders.Count > 0 ? folders[0].TryGetLocalPath() : null;
        }

        internal static string OpenFile(string current, bool save)
        {
            var dialog = save ? (WinForms.FileDialog)new WinForms.SaveFileDialog() : new WinForms.OpenFileDialog();
            dialog.FileName = current ?? "";
            dialog.Filter = "All files|*.*";
            return FileDialog(dialog, null) == WinForms.DialogResult.OK ? dialog.FileName : null;
        }

        internal static Window ActiveWindow()
        {
            if (Application.Current?.ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
                return desktop.Windows.FirstOrDefault(w => w.IsActive) ?? Ui.Main;
            return Ui.Main;
        }
    }

    /// <summary>A message box of the original (MessageBoxes, MessageBox.Show): a modal window with the text, the icon
    /// and the buttons, on the main thread.</summary>
    internal sealed class MessageBoxWindow : Window
    {
        static readonly List<MessageBoxWindow> s_open = new List<MessageBoxWindow>();
        WinForms.DialogResult _result = WinForms.DialogResult.Cancel;
        readonly WinForms.DialogResult _escape;

        static (string, WinForms.DialogResult)[] Choices(WinForms.MessageBoxButtons buttons)
        {
            switch (buttons)
            {
                case WinForms.MessageBoxButtons.OKCancel: return new[] { ("OK", WinForms.DialogResult.OK), ("Cancel", WinForms.DialogResult.Cancel) };
                case WinForms.MessageBoxButtons.YesNo: return new[] { ("Yes", WinForms.DialogResult.Yes), ("No", WinForms.DialogResult.No) };
                case WinForms.MessageBoxButtons.YesNoCancel: return new[] { ("Yes", WinForms.DialogResult.Yes), ("No", WinForms.DialogResult.No), ("Cancel", WinForms.DialogResult.Cancel) };
                case WinForms.MessageBoxButtons.RetryCancel: return new[] { ("Retry", WinForms.DialogResult.Retry), ("Cancel", WinForms.DialogResult.Cancel) };
                case WinForms.MessageBoxButtons.AbortRetryIgnore: return new[] { ("Abort", WinForms.DialogResult.Abort), ("Retry", WinForms.DialogResult.Retry), ("Ignore", WinForms.DialogResult.Ignore) };
                default: return new[] { ("OK", WinForms.DialogResult.OK) };
            }
        }

        internal static WinForms.DialogResult Present(WinForms.IWin32Window owner, string text, string caption, WinForms.MessageBoxButtons buttons, WinForms.MessageBoxIcon icon)
        {
            var choices = Choices(buttons);
            if (Probe.Active) return Probe.Prompt(caption, text, choices.Select(c => c.Item2).ToArray());
            var box = new MessageBoxWindow(text, caption, icon, choices);
            Window parent = Services.ActiveWindow();
            using (var done = new CancellationTokenSource())
            {
                box.Closed += (s, e) => done.Cancel();
                s_open.Add(box);
                if (parent != null && parent.IsVisible) box.ShowDialog(parent); else box.Show();
                Dispatcher.UIThread.MainLoop(done.Token);
                s_open.Remove(box);
            }
            return box._result;
        }

        /// <summary>WM_CLOSE to the open box (AutoClosingMessageBox): its Escape answer.</summary>
        internal static void CloseActive()
        {
            MessageBoxWindow box = s_open.LastOrDefault();
            if (box != null) { box._result = box._escape; box.Close(); }
        }

        MessageBoxWindow(string text, string caption, WinForms.MessageBoxIcon icon, (string Label, WinForms.DialogResult Value)[] choices)
        {
            Title = string.IsNullOrEmpty(caption) ? "PrePoMax" : caption;
            SizeToContent = SizeToContent.WidthAndHeight;
            CanResize = false;
            WindowStartupLocation = WindowStartupLocation.CenterOwner;
            Background = Look.Window;
            MaxWidth = 640;
            _escape = choices.Any(c => c.Value == WinForms.DialogResult.Cancel) ? WinForms.DialogResult.Cancel :
                      choices.Any(c => c.Value == WinForms.DialogResult.No) ? WinForms.DialogResult.No : choices[0].Value;
            _result = _escape;
            string glyph = icon == WinForms.MessageBoxIcon.Error ? "⛔" : icon == WinForms.MessageBoxIcon.Warning ? "⚠" :
                           icon == WinForms.MessageBoxIcon.Question ? "?" : icon == WinForms.MessageBoxIcon.Information ? "ℹ" : null;
            var body = new DockPanel { Margin = new Thickness(16, 14, 16, 12) };
            var row = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Spacing = 8, Margin = new Thickness(0, 14, 0, 0) };
            DockPanel.SetDock(row, Dock.Bottom);
            foreach (var (label, value) in choices)
            {
                var button = new Button { Content = label, MinWidth = 75, Height = 23, IsDefault = value == choices[0].Value,
                                          IsCancel = value == _escape };
                button.Click += (s, e) => { _result = value; Close(); };
                row.Children.Add(button);
            }
            body.Children.Add(row);
            if (glyph != null)
            {
                var mark = new TextBlock { Text = glyph, FontSize = 26, Margin = new Thickness(0, 0, 12, 0), VerticalAlignment = VerticalAlignment.Top,
                                           Foreground = icon == WinForms.MessageBoxIcon.Error ? Brushes.Firebrick : icon == WinForms.MessageBoxIcon.Warning ? Brushes.DarkOrange : Look.Highlight };
                DockPanel.SetDock(mark, Dock.Left);
                body.Children.Add(mark);
            }
            body.Children.Add(new SelectableTextBlock { Text = text ?? "", TextWrapping = TextWrapping.Wrap, VerticalAlignment = VerticalAlignment.Center, MinWidth = 220 });
            Content = body;
        }
    }
}
