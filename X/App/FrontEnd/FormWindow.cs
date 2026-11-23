// The window of an original form: its client area as nested canvases, one per original control at the bounds the
// WinForms control model lays out, each holding the Avalonia control that draws it. Activation, focus, keys and the
// window's size and position go back to the form.
using System;
using System.Collections.Generic;
using System.Linq;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Input;
using Avalonia.Interactivity;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.VisualTree;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEnd
{
    /// <summary>A mirror whose content follows the model beyond bounds and state.</summary>
    internal interface IMirror
    {
        /// <summary>After the bounds and states of a sync.</summary>
        void Update();
        /// <summary>A notification of the control's content (Refresh, Items, SelectedObject, Text, ...).</summary>
        void Refresh(string property);
    }

    internal sealed class FormWindow : Window
    {
        internal readonly WinForms.Form Form;
        readonly bool _main;
        readonly Canvas _client = new Canvas { ClipToBounds = true };
        readonly Dictionary<WinForms.Control, Mirror> _mirrors = new Dictionary<WinForms.Control, Mirror>();
        bool _closingFromModel, _sizing, _shownOnce;
        WinForms.Control _focusedControl;
        internal IEnumerable<KeyValuePair<WinForms.Control, Mirror>> Mirrors => _mirrors;
        internal bool IsMain => _main;

        /// <summary>After an appearance switch: the form's own colours again, every mirror updated, everything redrawn
        /// (the shared brushes changed colour; drawn controls read the palette when they render).</summary>
        internal void Restyle()
        {
            _client.Background = Form.BackColor.A > 0 ? Ui.Brush(Form.BackColor) : Look.Control;
            foreach (Mirror mirror in _mirrors.Values)
                try { mirror.Content?.Update(); } catch (Exception e) { Console.Error.WriteLine(e); }
            foreach (Visual visual in this.GetVisualDescendants()) visual.InvalidateVisual();
            foreach (var toggle in this.GetVisualDescendants().OfType<AppearanceToggle>()) toggle.Tip();
            InvalidateVisual();
        }

        public FormWindow(WinForms.Form form, bool main)
        {
            Form = form; _main = main;
            Content = _client;
            _client.Background = form.BackColor.A > 0 ? Ui.Brush(form.BackColor) : Look.Control;
            Background = Look.Control;
            Title = form.Text;
            // The original forms carry the application's icon (on macOS this is also the Dock icon of the process)
            if (Ui.AppIcon != null) Icon = Ui.AppIcon;
            if (main)
            {
                Ui.Main = this;
                Ui.Windows[form] = this;
                // Load and Shown run in the WinForms context (Shown is posted, as WinForms posts it)
                Ui.Guard(() => form.Show());
                Ui.Step("form shown");
                Width = 1400; Height = 900;
                Opened += (s, e) =>
                {
                    Ui.Step("opened");
                    Services.UpdateScreens(this);
                    var area = Screens.ScreenFromWindow(this)?.WorkingArea;
                    double k = Screens.ScreenFromWindow(this)?.Scaling ?? 1;
                    if (area.HasValue) { Width = Math.Min(Width, area.Value.Width / k - 20); Height = Math.Min(Height, area.Value.Height / k - 60); }
                    Resized();
                    Probe.Start(this);
                };
                Shortcuts.Install(this);
            }
            else
            {
                ShowInTaskbar = false;
                CanResize = form.FormBorderStyle == WinForms.FormBorderStyle.Sizable || form.FormBorderStyle == WinForms.FormBorderStyle.SizableToolWindow;
                SyncSize();
            }
            Closing += (s, e) =>
            {
                if (_closingFromModel || !Form.Visible) return;
                // The window close button: the form decides (FormClosing may cancel, a property form hides)
                if (!Ui.Input(() => Form.CloseByUser())) e.Cancel = true;
                else if (_main) e.Cancel = false;
            };
            Activated += (s, e) =>
            {
                if (WinForms.Form.ActiveForm != Form && Form.Visible) Ui.Input(Form.Activate);
            };
            PositionChanged += (s, e) => ReportLocation();
            AddHandler(KeyDownEvent, PreviewKey, RoutingStrategies.Tunnel, true);
            AddHandler(KeyUpEvent, PreviewKey, RoutingStrategies.Tunnel, true);
            AddHandler(KeyDownEvent, DialogKey, RoutingStrategies.Bubble);
            AddHandler(PointerPressedEvent, (s, e) => Keyboard.SetModifiers(e.KeyModifiers), RoutingStrategies.Tunnel, true);
            AddHandler(PointerReleasedEvent, (s, e) => Keyboard.SetModifiers(e.KeyModifiers), RoutingStrategies.Tunnel, true);
            AddHandler(GotFocusEvent, (s, e) => FocusChanged(e.Source as Visual), RoutingStrategies.Bubble, true);
        }

        // Showing and closing ---------------------------------------------------------------------------------------------
        internal void ShowForForm()
        {
            if (_main) return;
            Title = Form.Text;
            // The window opens at the form's client size (a later sync may not come: the form changes nothing after Show)
            SyncSize();
            PlaceFromForm();
            Window owner = Services.ActiveWindow();
            if (owner == this || owner == null || !owner.IsVisible) owner = Ui.Main != null && Ui.Main.IsVisible ? Ui.Main : null;
            if (Form.Modal && owner != null) ShowDialog(owner);
            else if (owner != null) Show(owner);
            else Show();
            _shownOnce = true;
        }

        /// <summary>A shown form keeps its window (property forms hide and show again).</summary>
        internal void HideForForm()
        {
            if (!IsVisible) return;
            _closingFromModel = true;
            try { Hide(); } finally { _closingFromModel = false; }
        }

        internal void CloseForForm() { _closingFromModel = true; Close(); }

        void PlaceFromForm()
        {
            // The original positions most forms itself (StartPosition Manual, next to the main window); the others are
            // centred over their owner
            double k = Screens?.Primary?.Scaling ?? 1;
            var location = Form.Location;
            bool onScreen = WinForms.Screen.AllScreens.Any(s => s.Bounds.Contains(location.X + 20, location.Y + 20));
            if (Form.StartPosition == WinForms.FormStartPosition.Manual && onScreen && (!_shownOnce || Form.Location != _reportedLocation))
            {
                WindowStartupLocation = WindowStartupLocation.Manual;
                Position = new PixelPoint((int)(location.X * k), (int)(location.Y * k));
            }
            else if (!_shownOnce) WindowStartupLocation = Form.StartPosition == WinForms.FormStartPosition.CenterScreen ? WindowStartupLocation.CenterScreen : WindowStartupLocation.CenterOwner;
        }

        System.Drawing.Point _reportedLocation;
        void ReportLocation()
        {
            if (!IsVisible) return;
            double k = Screens?.Primary?.Scaling ?? 1;
            var location = new System.Drawing.Point((int)Math.Round(Position.X / k), (int)Math.Round(Position.Y / k));
            if (location == Form.Location) return;
            _reportedLocation = location;
            Ui.Guard(() => Form.Location = location);
        }

        // Size --------------------------------------------------------------------------------------------------------------
        protected override void OnPropertyChanged(AvaloniaPropertyChangedEventArgs change)
        {
            base.OnPropertyChanged(change);
            // Also raised by the base constructor, before this window has its form
            if (change.Property == ClientSizeProperty && Form != null) Resized();
        }

        void Resized()
        {
            if (_sizing) return;
            var size = new System.Drawing.Size((int)Math.Round(ClientSize.Width), (int)Math.Round(ClientSize.Height));
            if (size.Width <= 0 || size.Height <= 0) return;
            // The window system and the user size the window; the form follows (the main window is never sized from
            // the form, or the two would grow each other by the frame)
            if ((_main || IsVisible) && Form.ClientSize != size) Ui.Input(() => Form.ClientSize = size);
            Sync();
        }

        void SyncSize()
        {
            var minimum = Form.MinimumSize;
            var maximum = Form.MaximumSize;
            // WinForms' limits are window sizes; Avalonia's are client sizes
            MinWidth = Math.Max(0, minimum.Width - WinForms.Form.FrameWidth);
            MinHeight = Math.Max(0, minimum.Height - WinForms.Form.FrameHeight);
            MaxWidth = maximum.Width > 0 ? Math.Max(MinWidth, maximum.Width - WinForms.Form.FrameWidth) : double.PositiveInfinity;
            MaxHeight = maximum.Height > 0 ? Math.Max(MinHeight, maximum.Height - WinForms.Form.FrameHeight) : double.PositiveInfinity;
            var client = Form.ClientSize;
            // Width and Height are NaN until set (a comparison with NaN is false)
            if (client.Width > 0 && client.Height > 0 && (double.IsNaN(Width) || double.IsNaN(Height) ||
                                                          Math.Abs(Width - client.Width) > 0.5 || Math.Abs(Height - client.Height) > 0.5))
            {
                _sizing = true;
                try { Width = client.Width; Height = client.Height; } finally { _sizing = false; }
            }
        }

        // Mirroring -----------------------------------------------------------------------------------------------------------
        /// <summary>Mirrors the control tree: creates what is new, moves and updates what exists, drops what left.</summary>
        internal void Sync()
        {
            if (Form == null) return;
            if (Title != Form.Text) Title = Form.Text;
            IsEnabled = Form.Enabled;
            if (!_main) SyncSize();
            var seen = new HashSet<WinForms.Control>();
            SyncChildren(Form, _client, seen);
            foreach (var gone in _mirrors.Keys.Where(c => !seen.Contains(c)).ToList())
            {
                (_mirrors[gone].Frame.Parent as Panel)?.Children.Remove(_mirrors[gone].Frame);
                _mirrors.Remove(gone);
            }
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
                    mirror = new Mirror(control, Controls.Create(this, control));
                    _mirrors[control] = mirror;
                }
                if (mirror.Frame.Parent != target)
                {
                    (mirror.Frame.Parent as Panel)?.Children.Remove(mirror.Frame);
                    target.Children.Add(mirror.Frame);
                }
                mirror.Frame.ZIndex = mirror.Above ? 1000 + z : z;
                var b = control.Bounds;
                Canvas.SetLeft(mirror.Frame, b.X); Canvas.SetTop(mirror.Frame, b.Y);
                double w = Math.Max(0, b.Width), h = Math.Max(0, b.Height);
                if (mirror.Frame.Width != w) mirror.Frame.Width = w;
                if (mirror.Frame.Height != h) mirror.Frame.Height = h;
                if (mirror.Visual != null) { mirror.Visual.Width = w; mirror.Visual.Height = h; }
                // A tab control shows its selected page only
                bool visible = control.Visible && !(parent is WinForms.TabControl tabs && control is WinForms.TabPage && tabs.SelectedTab != control);
                if (mirror.Frame.IsVisible != visible) mirror.Frame.IsVisible = visible;
                bool enabled = control.Enabled;
                if (mirror.Frame.IsEnabled != enabled) mirror.Frame.IsEnabled = enabled;
                try { mirror.Content?.Update(); } catch (Exception e) { Console.Error.WriteLine(e); }
                if (visible && !mirror.Leaf) SyncChildren(control, mirror.Frame, seen);
            }
        }

        internal void Refresh(WinForms.Control control, string property)
        {
            if (!_mirrors.TryGetValue(control, out Mirror mirror)) return;
            if (property == "Focus")
            {
                if (mirror.Visual is InputElement element && element.Focusable && mirror.Frame.IsEffectivelyVisible) element.Focus();
                _focusedControl = control;
                return;
            }
            try { mirror.Content?.Refresh(property); } catch (Exception e) { Console.Error.WriteLine(e); }
        }

        internal Control VisualOf(WinForms.Control control) => _mirrors.TryGetValue(control, out Mirror mirror) ? (Control)mirror.Visual ?? mirror.Frame : null;

        internal sealed class Mirror
        {
            public readonly Canvas Frame = new Canvas { ClipToBounds = true };
            public readonly Control Visual;
            public readonly IMirror Content;
            /// <summary>The control draws its children itself (no child canvases).</summary>
            public readonly bool Leaf;
            public readonly bool Above;
            public Mirror(WinForms.Control control, Controls.Created created)
            {
                Frame.Tag = control;
                Visual = created.Visual;
                Content = created.Content ?? created.Visual as IMirror;
                Leaf = created.Leaf;
                Above = created.Above;
                if (Visual != null) Frame.Children.Add(Visual);
            }
        }

        // Focus and keys ------------------------------------------------------------------------------------------------------
        /// <summary>The original control of an Avalonia visual (the innermost mirrored control around it).</summary>
        internal static WinForms.Control ControlOf(Visual visual)
        {
            for (Visual v = visual; v != null; v = v.GetVisualParent())
                if (v is Canvas canvas && canvas.Tag is WinForms.Control control) return control;
            return null;
        }

        void FocusChanged(Visual source)
        {
            WinForms.Control control = ControlOf(source);
            if (control == _focusedControl) return;
            WinForms.Control previous = _focusedControl;
            _focusedControl = control;
            Ui.Input(() => { previous?.RaiseLeave(); control?.RaiseEnter(); });
        }

        /// <summary>Every key reaches the original low-level keyboard hook (FrmMain's KeyboardHook), as on Windows.</summary>
        void PreviewKey(object sender, KeyEventArgs e)
        {
            Keyboard.SetModifiers(e.KeyModifiers);
            WinForms.Keys code = Keyboard.Code(e.Key);
            if (code != WinForms.Keys.None) Ui.Input(() => WinForms.LowLevelKeyboardHook.Raise(code, e.RoutedEvent == KeyDownEvent));
            if (_main && e.RoutedEvent == KeyDownEvent && !e.Handled && Shortcuts.Handle(Form, Keyboard.Keys(e))) e.Handled = true;
        }

        /// <summary>A form's AcceptButton and CancelButton (Enter and Escape that no control took).</summary>
        void DialogKey(object sender, KeyEventArgs e)
        {
            if (_main || e.Handled) return;
            if (e.Key == Key.Escape) { Ui.Input(() => Form.ProcessDialogKeyInput(WinForms.Keys.Escape)); e.Handled = true; }
            else if (e.Key == Key.Enter && !(FocusManager?.GetFocusedElement() is Button)) { Ui.Input(() => Form.ProcessDialogKeyInput(WinForms.Keys.Enter)); e.Handled = true; }
        }
    }

    /// <summary>Avalonia keys as WinForms Keys.</summary>
    internal static class Keyboard
    {
        internal static WinForms.Keys Code(Key key)
        {
            switch (key)
            {
                case Key.None: return WinForms.Keys.None;
                case Key.LeftShift: case Key.RightShift: return WinForms.Keys.ShiftKey;
                case Key.LeftCtrl: case Key.RightCtrl: case Key.LWin: case Key.RWin: return WinForms.Keys.ControlKey;
                case Key.LeftAlt: case Key.RightAlt: return WinForms.Keys.Menu;
                case Key.Enter: return WinForms.Keys.Enter;
                case Key.Back: return WinForms.Keys.Back;
                case Key.PageUp: return WinForms.Keys.PageUp;
                case Key.PageDown: return WinForms.Keys.PageDown;
            }
            return Enum.TryParse(key.ToString(), true, out WinForms.Keys keys) ? keys : WinForms.Keys.None;
        }
        /// <summary>The key with its modifiers; the Command key of macOS is WinForms' Control, as for the menus.</summary>
        internal static WinForms.Keys Keys(KeyEventArgs e) => Code(e.Key) | Modifiers(e.KeyModifiers);
        internal static WinForms.Keys Modifiers(KeyModifiers modifiers)
        {
            WinForms.Keys keys = WinForms.Keys.None;
            if ((modifiers & KeyModifiers.Shift) != 0) keys |= WinForms.Keys.Shift;
            if ((modifiers & (KeyModifiers.Control | KeyModifiers.Meta)) != 0) keys |= WinForms.Keys.Control;
            if ((modifiers & KeyModifiers.Alt) != 0) keys |= WinForms.Keys.Alt;
            return keys;
        }
        internal static void SetModifiers(KeyModifiers modifiers) => WinForms.Control.ModifierKeys = Modifiers(modifiers);
        internal static WinForms.MouseButtons Button(PointerUpdateKind kind)
        {
            switch (kind)
            {
                case PointerUpdateKind.LeftButtonPressed: case PointerUpdateKind.LeftButtonReleased: return WinForms.MouseButtons.Left;
                case PointerUpdateKind.RightButtonPressed: case PointerUpdateKind.RightButtonReleased: return WinForms.MouseButtons.Right;
                case PointerUpdateKind.MiddleButtonPressed: case PointerUpdateKind.MiddleButtonReleased: return WinForms.MouseButtons.Middle;
                default: return WinForms.MouseButtons.None;
            }
        }
        /// <summary>A gesture for the display of a menu shortcut.</summary>
        internal static KeyGesture Gesture(WinForms.Keys keys)
        {
            if (keys == WinForms.Keys.None) return null;
            WinForms.Keys code = keys & WinForms.Keys.KeyCode;
            KeyModifiers modifiers = KeyModifiers.None;
            if ((keys & WinForms.Keys.Control) != 0) modifiers |= OperatingSystem.IsMacOS() ? KeyModifiers.Meta : KeyModifiers.Control;
            if ((keys & WinForms.Keys.Shift) != 0) modifiers |= KeyModifiers.Shift;
            if ((keys & WinForms.Keys.Alt) != 0) modifiers |= KeyModifiers.Alt;
            string name = code == WinForms.Keys.Enter ? "Enter" : code == WinForms.Keys.Oemplus ? "OemPlus" : code == WinForms.Keys.OemMinus ? "OemMinus" : code.ToString();
            return Enum.TryParse(name, true, out Key key) ? new KeyGesture(key, modifiers) : null;
        }
    }
}
