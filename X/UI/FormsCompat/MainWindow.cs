using System.ComponentModel;
using System.Drawing;
using System.Runtime.InteropServices;

namespace System.Windows.Forms
{
    // Controls of the original main window (FrmMain.Designer.cs, M2): state only, the renderer draws them.

    /// <summary>The tool strip host of FrmMain: four edge panels and the content panel.</summary>
    public class ToolStripContainer : ContainerControl
    {
        public ToolStripContainer()
        {
            TopToolStripPanel = new ToolStripPanel { Dock = DockStyle.Top };
            BottomToolStripPanel = new ToolStripPanel { Dock = DockStyle.Bottom };
            LeftToolStripPanel = new ToolStripPanel { Dock = DockStyle.Left };
            RightToolStripPanel = new ToolStripPanel { Dock = DockStyle.Right };
            ContentPanel = new ToolStripContentPanel { Dock = DockStyle.Fill };
            Controls.Add(ContentPanel);
            Controls.Add(TopToolStripPanel);
            Controls.Add(BottomToolStripPanel);
            Controls.Add(LeftToolStripPanel);
            Controls.Add(RightToolStripPanel);
        }
        public ToolStripPanel TopToolStripPanel { get; }
        public ToolStripPanel BottomToolStripPanel { get; }
        public ToolStripPanel LeftToolStripPanel { get; }
        public ToolStripPanel RightToolStripPanel { get; }
        public ToolStripContentPanel ContentPanel { get; }
        public bool TopToolStripPanelVisible { get => TopToolStripPanel.Visible; set => TopToolStripPanel.Visible = value; }
        public bool BottomToolStripPanelVisible { get => BottomToolStripPanel.Visible; set => BottomToolStripPanel.Visible = value; }
        public bool LeftToolStripPanelVisible { get => LeftToolStripPanel.Visible; set => LeftToolStripPanel.Visible = value; }
        public bool RightToolStripPanelVisible { get => RightToolStripPanel.Visible; set => RightToolStripPanel.Visible = value; }
    }
    public class ToolStripPanel : ContainerControl
    {
        public Orientation Orientation { get; set; }
        public Padding RowMargin { get; set; }
        bool _arranging;
        /// <summary>WinForms ToolStripPanel: the visible tool strips in rows (by their designer location, top to
        /// bottom, left to right), each strip at the right of the one before; the panel is as high as its rows.</summary>
        protected override void LayoutChildren()
        {
            if (_arranging) return;
            _arranging = true;
            try
            {
                var strips = new System.Collections.Generic.List<Control>();
                foreach (Control c in Controls) if (c.Visible) strips.Add(c);
                strips.Sort((a, b) => a.Location.Y != b.Location.Y ? a.Location.Y.CompareTo(b.Location.Y) : a.Location.X.CompareTo(b.Location.X));
                int y = 0, rowTop = int.MinValue, rowHeight = 0, x = 0;
                foreach (Control strip in strips)
                {
                    if (strip.Location.Y != rowTop && rowTop != int.MinValue && strip.Location.Y >= rowTop + rowHeight / 2)
                    {
                        y += rowHeight; rowHeight = 0; x = 0;
                    }
                    if (rowTop == int.MinValue || x == 0) rowTop = strip.Location.Y;
                    x = Math.Max(x, strip.Location.X);
                    strip.Location = new Point(x, y);
                    x += strip.Width;
                    rowHeight = Math.Max(rowHeight, strip.Height);
                }
                int height = y + rowHeight;
                if (Orientation == Orientation.Horizontal && Height != height) Height = height;
            }
            finally { _arranging = false; }
        }
    }
    public class ToolStripContentPanel : Panel { }

    public class ToolStripProgressBar : ToolStripItem
    {
        public ProgressBar ProgressBar { get; } = new ProgressBar();
        public bool AutoSize { get; set; } = true;
        public int MarqueeAnimationSpeed { get => ProgressBar.MarqueeAnimationSpeed; set => ProgressBar.MarqueeAnimationSpeed = value; }
        public ProgressBarStyle Style { get => ProgressBar.Style; set => ProgressBar.Style = value; }
        public int Minimum { get => ProgressBar.Minimum; set => ProgressBar.Minimum = value; }
        public int Maximum { get => ProgressBar.Maximum; set => ProgressBar.Maximum = value; }
        public int Value { get => ProgressBar.Value; set => ProgressBar.Value = value; }
    }

    public enum ToolStripDropDownCloseReason { AppFocusChange, AppClicked, ItemClicked, Keyboard, CloseCalled }
    public class ToolStripDropDownClosingEventArgs : CancelEventArgs
    {
        public ToolStripDropDownClosingEventArgs(ToolStripDropDownCloseReason reason) { CloseReason = reason; }
        public ToolStripDropDownCloseReason CloseReason { get; }
    }
    public delegate void ToolStripDropDownClosingEventHandler(object sender, ToolStripDropDownClosingEventArgs e);

    /// <summary>The menu colours of the WinForms professional renderer (Windows default theme values).</summary>
    public class ProfessionalColorTable
    {
        public virtual Color MenuItemSelected => Color.FromArgb(204, 232, 255);
        public virtual Color MenuItemBorder => Color.FromArgb(153, 204, 255);
        public virtual Color MenuItemPressedGradientBegin => Color.FromArgb(224, 224, 224);
        public virtual Color MenuItemPressedGradientEnd => Color.FromArgb(224, 224, 224);
        public virtual Color MenuItemSelectedGradientBegin => Color.FromArgb(204, 232, 255);
        public virtual Color MenuItemSelectedGradientEnd => Color.FromArgb(204, 232, 255);
        public virtual Color ToolStripBorder => Color.FromArgb(204, 206, 219);
        public bool UseSystemColors { get; set; }
    }

    [Flags]
    public enum TextFormatFlags
    {
        Default = 0, Top = 0, Left = 0, HorizontalCenter = 1, Right = 2, VerticalCenter = 4, Bottom = 8, WordBreak = 16,
        SingleLine = 32, ExpandTabs = 64, NoClipping = 256, ExternalLeading = 512, NoPrefix = 2048, Internal = 4096,
        TextBoxControl = 8192, PathEllipsis = 16384, EndEllipsis = 32768, ModifyString = 65536, RightToLeft = 131072,
        WordEllipsis = 262144, NoFullWidthCharacterBreak = 524288, HidePrefix = 1048576, PrefixOnly = 2097152,
        PreserveGraphicsClipping = 16777216, PreserveGraphicsTranslateTransform = 33554432, NoPadding = 268435456,
        LeftAndRightPadding = 536870912, GlyphOverhangPadding = 0,
    }
    public enum ButtonBorderStyle { None, Dotted, Dashed, Solid, Inset, Outset }

    /// <summary>The low-level keyboard hook of the original CaeGlobals.KeyboardHook (user32 WH_KEYBOARD_LL): the
    /// renderer reports every key press and release of the application; installed hooks receive them with the
    /// original message codes and a KBDLLHOOKSTRUCT whose first field is the virtual-key code.</summary>
    public static class LowLevelKeyboardHook
    {
        public delegate IntPtr Handler(int code, IntPtr wParam, IntPtr lParam);
        static readonly Collections.Generic.Dictionary<IntPtr, Handler> hooks = new Collections.Generic.Dictionary<IntPtr, Handler>();
        static long next;
        public static IntPtr Set(int idHook, Handler handler)
        {
            if (idHook != 13 || handler == null) return IntPtr.Zero; // WH_KEYBOARD_LL only
            IntPtr id = new IntPtr(Threading.Interlocked.Increment(ref next));
            lock (hooks) hooks[id] = handler;
            return id;
        }
        public static bool Unset(IntPtr id) { lock (hooks) return hooks.Remove(id); }
        public static IntPtr CallNext(IntPtr id, int code, IntPtr wParam, IntPtr lParam) => IntPtr.Zero;
        /// <summary>Renderer input: a key went down or up (Windows virtual-key code).</summary>
        public static void Raise(Keys keyCode, bool down, bool system = false)
        {
            Handler[] handlers;
            lock (hooks) handlers = new Collections.Generic.List<Handler>(hooks.Values).ToArray();
            if (handlers.Length == 0) return;
            IntPtr data = Marshal.AllocHGlobal(24); // KBDLLHOOKSTRUCT
            try
            {
                for (int i = 0; i < 24; i += 4) Marshal.WriteInt32(data, i, 0);
                Marshal.WriteInt32(data, (int)(keyCode & Keys.KeyCode));
                IntPtr message = new IntPtr(down ? (system ? 0x104 : 0x100) : (system ? 0x105 : 0x101));
                foreach (Handler handler in handlers) handler(0, message, data);
            }
            finally { Marshal.FreeHGlobal(data); }
        }
    }
}

namespace System.Windows.Forms
{
    /// <summary>The application's low-level mouse hook (user32 WH_MOUSE_LL), fed by the renderer with the screen
    /// position of each mouse message, in the MSLLHOOKSTRUCT layout the hooks read.</summary>
    public static class LowLevelMouseHook
    {
        public delegate IntPtr Handler(int code, IntPtr wParam, IntPtr lParam);
        static readonly Collections.Generic.Dictionary<IntPtr, Handler> hooks = new Collections.Generic.Dictionary<IntPtr, Handler>();
        static long next = 1 << 20;
        public static IntPtr Set(int idHook, Handler handler)
        {
            if (idHook != 14 || handler == null) return IntPtr.Zero; // WH_MOUSE_LL only
            IntPtr id = new IntPtr(Threading.Interlocked.Increment(ref next));
            lock (hooks) hooks[id] = handler;
            return id;
        }
        public static bool Unset(IntPtr id) { lock (hooks) return hooks.Remove(id); }
        public static IntPtr CallNext(IntPtr id, int code, IntPtr wParam, IntPtr lParam) => IntPtr.Zero;
        public const int WM_MOUSEMOVE = 0x200, WM_LBUTTONDOWN = 0x201, WM_LBUTTONUP = 0x202, WM_RBUTTONDOWN = 0x204, WM_RBUTTONUP = 0x205,
                         WM_MBUTTONDOWN = 0x207, WM_MBUTTONUP = 0x208, WM_MOUSEWHEEL = 0x20A;
        /// <summary>Renderer input: a mouse message at a screen point (wheel delta in mouseData's high word).
        /// Returns false when a hook consumed it (returned non-zero without calling the next hook).</summary>
        public static bool Raise(int message, int screenX, int screenY, int wheelDelta = 0)
        {
            Handler[] handlers;
            lock (hooks) handlers = new Collections.Generic.List<Handler>(hooks.Values).ToArray();
            if (handlers.Length == 0) return true;
            IntPtr data = Marshal.AllocHGlobal(32); // MSLLHOOKSTRUCT: pt, mouseData, flags, time, dwExtraInfo
            try
            {
                for (int i = 0; i < 32; i += 4) Marshal.WriteInt32(data, i, 0);
                Marshal.WriteInt32(data, 0, screenX);
                Marshal.WriteInt32(data, 4, screenY);
                Marshal.WriteInt32(data, 8, wheelDelta << 16);
                Marshal.WriteInt32(data, 16, Environment.TickCount);
                bool passed = true;
                foreach (Handler handler in handlers) if (handler(0, new IntPtr(message), data) != IntPtr.Zero) passed = false;
                return passed;
            }
            finally { Marshal.FreeHGlobal(data); }
        }
    }
    /// <summary>The native dialogs the toolkit shows for the application (message boxes, file dialogs), for the
    /// original's search of its thread's dialog windows (class #32770).</summary>
    public static class NativeDialogs
    {
        static readonly Collections.Generic.Dictionary<IntPtr, string> open = new Collections.Generic.Dictionary<IntPtr, string>();
        static long next = 1 << 24;
        public static IntPtr Opened(string title) { IntPtr id = new IntPtr(Threading.Interlocked.Increment(ref next)); lock (open) open[id] = title ?? ""; return id; }
        public static void Closed(IntPtr id) { lock (open) open.Remove(id); }
        /// <summary>user32 EnumThreadWindows over the open native dialogs (all on the user-interface thread).</summary>
        public static bool EnumThreadWindows(Func<IntPtr, IntPtr, bool> callback, IntPtr parameter)
        {
            IntPtr[] ids;
            lock (open) ids = new Collections.Generic.List<IntPtr>(open.Keys).ToArray();
            foreach (IntPtr id in ids) if (!callback(id, parameter)) break;
            return true;
        }
        public static bool IsWindowVisible(IntPtr id) { lock (open) return open.ContainsKey(id); }
        public static int GetClassName(IntPtr id, Text.StringBuilder className) { className.Clear(); if (IsWindowVisible(id)) className.Append("#32770"); return className.Length; }
        public static int GetWindowText(IntPtr id, Text.StringBuilder text) { text.Clear(); lock (open) if (open.TryGetValue(id, out string title)) text.Append(title); return text.Length; }
    }

    /// <summary>A control shown as a tool strip item (the original autocomplete menu hosts its list in one).</summary>
    public class ToolStripControlHost : ToolStripItem
    {
        public ToolStripControlHost(Control c)
        {
            Control = c ?? throw new ArgumentNullException(nameof(c));
            // WinForms raises the hosted control's events on the item
            c.KeyDown += (s, e) => OnKeyDown(e);
            c.KeyUp += (s, e) => OnKeyUp(e);
            c.KeyPress += (s, e) => OnKeyPress(e);
            c.Enter += (s, e) => OnEnter(e);
            c.Leave += (s, e) => OnLeave(e);
            c.GotFocus += (s, e) => OnGotFocus(e);
            c.LostFocus += (s, e) => OnLostFocus(e);
            c.TextChanged += (s, e) => OnTextChanged(e);
            c.Validating += (s, e) => Validating?.Invoke(this, e);
            c.Validated += (s, e) => Validated?.Invoke(this, e);
        }
        public Control Control { get; }
        public bool AutoToolTip { get; set; }
        public bool Focused => Control.Focused;
        public void Focus() => Control.Focus();
        public event KeyEventHandler KeyDown, KeyUp;
        public event KeyPressEventHandler KeyPress;
        public event EventHandler Enter, Leave, GotFocus, LostFocus, TextChanged, Validated;
        public event CancelEventHandler Validating;
        protected virtual void OnKeyDown(KeyEventArgs e) => KeyDown?.Invoke(this, e);
        protected virtual void OnKeyUp(KeyEventArgs e) => KeyUp?.Invoke(this, e);
        protected virtual void OnKeyPress(KeyPressEventArgs e) => KeyPress?.Invoke(this, e);
        protected virtual void OnEnter(EventArgs e) => Enter?.Invoke(this, e);
        protected virtual void OnLeave(EventArgs e) => Leave?.Invoke(this, e);
        protected virtual void OnGotFocus(EventArgs e) => GotFocus?.Invoke(this, e);
        protected virtual void OnLostFocus(EventArgs e) => LostFocus?.Invoke(this, e);
        protected virtual void OnTextChanged(EventArgs e) => TextChanged?.Invoke(this, e);
    }
    public class ToolStripItemRenderEventArgs : EventArgs
    {
        public ToolStripItemRenderEventArgs(Graphics g, ToolStripItem item) { Graphics = g; Item = item; }
        public Graphics Graphics { get; }
        public ToolStripItem Item { get; }
        public ToolStrip ToolStrip => Item?.Owner;
    }
    /// <summary>Tool strip painting: the renderer draws the strips; the original renderers override what they change.</summary>
    public abstract class ToolStripRenderer
    {
        protected virtual void OnRenderMenuItemBackground(ToolStripItemRenderEventArgs e) { }
        protected virtual void OnRenderButtonBackground(ToolStripItemRenderEventArgs e) { }
        protected virtual void OnRenderItemBackground(ToolStripItemRenderEventArgs e) { }
    }
    public class ToolStripProfessionalRenderer : ToolStripRenderer
    {
        public ToolStripProfessionalRenderer() { }
        public ToolStripProfessionalRenderer(ProfessionalColorTable professionalColorTable) { ColorTable = professionalColorTable; }
        public ProfessionalColorTable ColorTable { get; }
        public bool RoundedEdges { get; set; } = true;
    }
    public class ListBox : ListControl
    {
        int _selectedIndex = -1;
        public ListBox() { Items = new ComboBox.ObjectCollection(new ComboBox()); }
        public ComboBox.ObjectCollection Items { get; }
        public bool IntegralHeight { get; set; } = true;
        public BorderStyle BorderStyle { get; set; } = BorderStyle.Fixed3D;
        public int ItemHeight { get; set; } = 13;
        public DrawMode DrawMode { get; set; }
        public SelectionMode SelectionMode { get; set; } = SelectionMode.One;
        public int SelectedIndex
        {
            get => _selectedIndex;
            set
            {
                if (value < -1 || value >= Items.Count) throw new ArgumentOutOfRangeException(nameof(value));
                if (_selectedIndex == value) return;
                _selectedIndex = value;
                Notify(nameof(SelectedIndex));
                OnSelectedIndexChanged(EventArgs.Empty);
            }
        }
        public object SelectedItem => _selectedIndex >= 0 ? Items[_selectedIndex] : null;
        public event EventHandler SelectedIndexChanged;
        protected virtual void OnSelectedIndexChanged(EventArgs e) => SelectedIndexChanged?.Invoke(this, e);
        public void BeginUpdate() { }
        public void EndUpdate() => Notify("Items");
    }
    public enum SelectionMode { None, One, MultiSimple, MultiExtended }
    public enum DrawMode { Normal, OwnerDrawFixed, OwnerDrawVariable }
    public class CheckedListBox : ListBox
    {
        readonly System.Collections.Generic.Dictionary<object, CheckState> _states = new System.Collections.Generic.Dictionary<object, CheckState>();
        public bool CheckOnClick { get; set; }
        public event ItemCheckEventHandler ItemCheck;
        public CheckState GetItemCheckState(int index) => _states.TryGetValue(Items[index], out CheckState state) ? state : CheckState.Unchecked;
        public bool GetItemChecked(int index) => GetItemCheckState(index) != CheckState.Unchecked;
        public void SetItemChecked(int index, bool value) => SetItemCheckState(index, value ? CheckState.Checked : CheckState.Unchecked);
        /// <summary>WinForms raises ItemCheck before the state changes; a handler may change the new value.</summary>
        public void SetItemCheckState(int index, CheckState value)
        {
            CheckState current = GetItemCheckState(index);
            if (current == value) return;
            var e = new ItemCheckEventArgs(index, value, current);
            ItemCheck?.Invoke(this, e);
            _states[Items[index]] = e.NewValue;
            Notify("Items");
        }
    }
}

namespace System.Windows.Forms.Design
{
    /// <summary>The file name editor of the property grid: the renderer asks InitializeDialog for its dialog settings.</summary>
    public class FileNameEditor : System.Drawing.Design.UITypeEditor
    {
        protected virtual void InitializeDialog(OpenFileDialog openFileDialog) { }
        public void Initialize(OpenFileDialog openFileDialog) => InitializeDialog(openFileDialog);
    }
    public sealed class FolderNameEditor : System.Drawing.Design.UITypeEditor { }
}

namespace System.Windows.Forms
{
    public enum ToolTipIcon { None, Info, Warning, Error }
    public enum ToolStripItemOverflow { Never, Always, AsNeeded }
    public abstract class ScrollProperties
    {
        readonly ScrollableControl _owner;
        int _value, _minimum, _maximum = 100;
        protected ScrollProperties(ScrollableControl owner) { _owner = owner; }
        public bool Enabled { get; set; } = true;
        public bool Visible { get; set; }
        public int Minimum { get => _minimum; set => _minimum = value; }
        public int Maximum { get => _maximum; set => _maximum = value; }
        public int SmallChange { get; set; } = 1;
        public int LargeChange { get; set; } = 10;
        /// <summary>The scroll position; set by the control or reported by the renderer (RaiseScroll).</summary>
        public int Value
        {
            get => _value;
            set
            {
                if (value < _minimum || value > _maximum) throw new ArgumentOutOfRangeException(nameof(Value));
                _value = value;
                ControlNotifications.Raise(_owner, "ScrollPosition");
            }
        }
    }
    public sealed class VScrollProperties : ScrollProperties { public VScrollProperties(ScrollableControl container) : base(container) { } }
    public sealed class HScrollProperties : ScrollProperties { public HScrollProperties(ScrollableControl container) : base(container) { } }
    public class HandledMouseEventArgs : MouseEventArgs
    {
        public HandledMouseEventArgs(MouseButtons button, int clicks, int x, int y, int delta) : base(button, clicks, x, y, delta) { }
        public HandledMouseEventArgs(MouseButtons button, int clicks, int x, int y, int delta, bool defaultValue) : base(button, clicks, x, y, delta) { Handled = defaultValue; }
        public bool Handled { get; set; }
    }
    /// <summary>ControlPaint: the drawing helpers record on the paint surface like the original GDI+ calls.</summary>
    public static class ControlPaint
    {
        public static void DrawBorder(Graphics graphics, Rectangle bounds, Color color, ButtonBorderStyle style)
        {
            if (style == ButtonBorderStyle.None) return;
            using (var pen = new Pen(color))
            {
                if (style == ButtonBorderStyle.Dotted) pen.DashStyle = System.Drawing.Drawing2D.DashStyle.Dot;
                else if (style == ButtonBorderStyle.Dashed) pen.DashStyle = System.Drawing.Drawing2D.DashStyle.Dash;
                graphics.DrawRectangle(pen, bounds.X, bounds.Y, bounds.Width - 1, bounds.Height - 1);
            }
        }
        /// <summary>The image drawn disabled (greyed): recorded as the image with the disabled flag for the renderer.</summary>
        public static void DrawImageDisabled(Graphics graphics, Image image, int x, int y, Color background)
            => graphics.DrawImage(new DisabledImage(image), x, y);
        public static Color Dark(Color baseColor) => Dark(baseColor, 0.5f);
        public static Color Dark(Color baseColor, float percOfDarkDark)
            => Color.FromArgb(baseColor.A, (int)(baseColor.R * (1 - percOfDarkDark * 0.5f)), (int)(baseColor.G * (1 - percOfDarkDark * 0.5f)), (int)(baseColor.B * (1 - percOfDarkDark * 0.5f)));
        public static Color Light(Color baseColor) => Light(baseColor, 0.5f);
        public static Color Light(Color baseColor, float percOfLightLight)
            => Color.FromArgb(baseColor.A, baseColor.R + (int)((255 - baseColor.R) * percOfLightLight * 0.5f), baseColor.G + (int)((255 - baseColor.G) * percOfLightLight * 0.5f), baseColor.B + (int)((255 - baseColor.B) * percOfLightLight * 0.5f));
    }
    /// <summary>An image to draw greyed (ControlPaint.DrawImageDisabled).</summary>
    public sealed class DisabledImage : Bitmap
    {
        public DisabledImage(Image image) : base(image) { }
    }
}
