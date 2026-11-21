// Timers, scroll bars, drag and drop, common file dialogs and system metrics of the headless WinForms model
// (System.Windows.Forms semantics). The renderer (X/UI/original_forms.py) drives timers with toolkit timers,
// shows the file dialogs and feeds scroll and drop input back through the WinForms events.
using System;
using System.ComponentModel;
using System.Drawing;

namespace System.Windows.Forms
{
    /// <summary>UI-thread timer: Tick is raised on the UI thread every Interval ms while Enabled. The renderer
    /// subscribes to <see cref="StateChanged"/> and raises <see cref="RaiseTick"/>.</summary>
    public class Timer : Component
    {
        bool _enabled;
        int _interval = 100;
        public Timer() { }
        public Timer(IContainer container) : this() { container?.Add(this); }
        public static event Action<Timer> StateChanged;
        public event EventHandler Tick;
        public object Tag { get; set; }
        public bool Enabled { get => _enabled; set { if (_enabled == value) return; _enabled = value; RaiseStateChanged(); } }
        void RaiseStateChanged() { if (!ToolkitSynchronizationContext.Defer(() => StateChanged?.Invoke(this))) StateChanged?.Invoke(this); }
        public int Interval
        {
            get => _interval;
            set
            {
                if (value < 1) throw new ArgumentOutOfRangeException(nameof(Interval), $"Interval value '{value}' is not valid. Interval must be greater than 0.");
                if (_interval == value) return;
                _interval = value;
                if (_enabled) RaiseStateChanged();
            }
        }
        public void Start() => Enabled = true;
        public void Stop() => Enabled = false;
        protected virtual void OnTick(EventArgs e) => Tick?.Invoke(this, e);
        public void RaiseTick() { if (_enabled) OnTick(EventArgs.Empty); }
        protected override void Dispose(bool disposing) { Enabled = false; base.Dispose(disposing); }
    }

    public enum ScrollEventType { SmallDecrement, SmallIncrement, LargeDecrement, LargeIncrement, ThumbPosition, ThumbTrack, First, Last, EndScroll }
    public enum ScrollOrientation { HorizontalScroll, VerticalScroll }
    public class ScrollEventArgs : EventArgs
    {
        public ScrollEventType Type { get; }
        public int NewValue { get; set; }
        public int OldValue { get; }
        public ScrollOrientation ScrollOrientation { get; }
        public ScrollEventArgs(ScrollEventType type, int newValue) : this(type, -1, newValue) { }
        public ScrollEventArgs(ScrollEventType type, int oldValue, int newValue) { Type = type; OldValue = oldValue; NewValue = newValue; }
        public ScrollEventArgs(ScrollEventType type, int oldValue, int newValue, ScrollOrientation orientation) : this(type, oldValue, newValue) { ScrollOrientation = orientation; }
    }
    public delegate void ScrollEventHandler(object sender, ScrollEventArgs e);

    /// <summary>WinForms ScrollBar: Value in [Minimum, Maximum - LargeChange + 1] through user input; Scroll is
    /// raised before ValueChanged.</summary>
    public abstract class ScrollBar : Control
    {
        int _min, _max = 100, _value, _small = 1, _large = 10;
        public int Minimum { get => _min; set { _min = value; if (_max < value) _max = value; if (_value < value) Value = value; Notify("Range"); } }
        public int Maximum { get => _max; set { _max = value; if (_min > value) _min = value; if (_value > value) Value = value; Notify("Range"); } }
        public int SmallChange { get => _small; set { if (value < 0) throw new ArgumentOutOfRangeException(nameof(SmallChange)); _small = Math.Min(value, _large); Notify("Range"); } }
        public int LargeChange { get => _large; set { if (value < 0) throw new ArgumentOutOfRangeException(nameof(LargeChange)); _large = Math.Min(value, _max - _min + 1); if (_small > _large) _small = _large; Notify("Range"); } }
        public int Value
        {
            get => _value;
            set
            {
                if (value < _min || value > _max) throw new ArgumentOutOfRangeException(nameof(Value), $"Value of '{value}' is not valid for 'Value'. 'Value' should be between 'minimum' and 'maximum'.");
                if (_value == value) return;
                _value = value;
                Notify(nameof(Value));
                OnValueChanged(EventArgs.Empty);
            }
        }
        public event ScrollEventHandler Scroll;
        public event EventHandler ValueChanged;
        protected virtual void OnScroll(ScrollEventArgs e) => Scroll?.Invoke(this, e);
        protected virtual void OnValueChanged(EventArgs e) => ValueChanged?.Invoke(this, e);
        /// <summary>User input: the highest reachable value is Maximum - LargeChange + 1 (WinForms).</summary>
        public void UserScroll(ScrollEventType type, int newValue)
        {
            int top = Math.Max(_min, _max - _large + 1);
            newValue = Math.Max(_min, Math.Min(newValue, top));
            var e = new ScrollEventArgs(type, _value, newValue, this is HScrollBar ? ScrollOrientation.HorizontalScroll : ScrollOrientation.VerticalScroll);
            OnScroll(e);
            Value = Math.Max(_min, Math.Min(e.NewValue, _max));
        }
    }
    public class HScrollBar : ScrollBar { }
    public class VScrollBar : ScrollBar { }

    [Flags] public enum DragDropEffects { None = 0, Copy = 1, Move = 2, Link = 4, Scroll = -2147483648, All = -2147483645 }
    public class DragEventArgs : EventArgs
    {
        public IDataObject Data { get; }
        public int KeyState { get; }
        public int X { get; }
        public int Y { get; }
        public DragDropEffects AllowedEffect { get; }
        public DragDropEffects Effect { get; set; }
        public DragEventArgs(IDataObject data, int keyState, int x, int y, DragDropEffects allowedEffect, DragDropEffects effect)
        { Data = data; KeyState = keyState; X = x; Y = y; AllowedEffect = allowedEffect; Effect = effect; }
    }
    public delegate void DragEventHandler(object sender, DragEventArgs e);

    /// <summary>Common file dialog: ShowDialog asks the renderer (<see cref="ShowHandler"/>); headless it is Cancel.</summary>
    public abstract class FileDialog : Component
    {
        public static Func<FileDialog, IWin32Window, DialogResult> ShowHandler;
        public string FileName { get; set; } = "";
        public string[] FileNames { get; set; } = new string[0];
        public string Filter { get; set; } = "";
        public int FilterIndex { get; set; } = 1;
        public string InitialDirectory { get; set; } = "";
        public string Title { get; set; } = "";
        public string DefaultExt { get; set; } = "";
        public bool AddExtension { get; set; } = true;
        public bool CheckFileExists { get; set; }
        public bool CheckPathExists { get; set; } = true;
        public bool RestoreDirectory { get; set; }
        public bool ValidateNames { get; set; } = true;
        public bool SupportMultiDottedExtensions { get; set; }
        public abstract bool IsSave { get; }
        public DialogResult ShowDialog() => ShowDialog(null);
        public DialogResult ShowDialog(IWin32Window owner)
        {
            if (ShowHandler == null) return DialogResult.Cancel;
            IntPtr dialog = NativeDialogs.Opened(Title);
            try { return ToolkitSynchronizationContext.OnUiThread(() => ShowHandler(this, owner)); }
            finally { NativeDialogs.Closed(dialog); }
        }
        public void Reset() { FileName = ""; Filter = ""; Title = ""; InitialDirectory = ""; }
    }
    public class OpenFileDialog : FileDialog { public bool Multiselect { get; set; } public override bool IsSave => false; }
    public class SaveFileDialog : FileDialog { public bool OverwritePrompt { get; set; } = true; public bool CreatePrompt { get; set; } public override bool IsSave => true; }

    public static class SystemInformation
    {
        public static int DoubleClickTime => 500;
        public static Size DoubleClickSize => new Size(4, 4);
        public static Size DragSize => new Size(4, 4);
        public static int VerticalScrollBarWidth => 17;
        public static int HorizontalScrollBarHeight => 17;
        public static bool TerminalServerSession => false;
        public static Size BorderSize => new Size(1, 1);
        public static int MouseWheelScrollLines => 3;
        public static Rectangle VirtualScreen { get { Rectangle r = Rectangle.Empty; foreach (Screen s in Screen.AllScreens) r = r.IsEmpty ? s.Bounds : Rectangle.Union(r, s.Bounds); return r; } }
        public static Rectangle WorkingArea => Screen.PrimaryScreen.WorkingArea;
    }
}

namespace System.Windows.Forms
{
    public enum TableLayoutPanelCellBorderStyle { None, Single, Inset, InsetDouble, Outset, OutsetDouble, OutsetPartial }
    public enum TableLayoutPanelGrowStyle { FixedSize, AddRows, AddColumns }
    public abstract class TableLayoutStyle { public SizeType SizeType { get; set; } }
    public class ColumnStyle : TableLayoutStyle { public float Width { get; set; } public ColumnStyle() { } public ColumnStyle(SizeType sizeType) { SizeType = sizeType; } public ColumnStyle(SizeType sizeType, float width) { SizeType = sizeType; Width = width; } }
    public class RowStyle : TableLayoutStyle { public float Height { get; set; } public RowStyle() { } public RowStyle(SizeType sizeType) { SizeType = sizeType; } public RowStyle(SizeType sizeType, float height) { SizeType = sizeType; Height = height; } }
    public class TableLayoutColumnStyleCollection : System.Collections.Generic.List<ColumnStyle> { }
    public class TableLayoutRowStyleCollection : System.Collections.Generic.List<RowStyle> { }

    /// <summary>WinForms TableLayoutPanel: Absolute sizes first, AutoSize from the cell contents, the rest shared by
    /// Percent; each child is placed in its cell by Dock/Anchor inside its Margin.</summary>
    public class TableLayoutPanel : Panel
    {
        readonly System.Collections.Generic.Dictionary<Control, (int Column, int Row)> _cells = new System.Collections.Generic.Dictionary<Control, (int, int)>();
        public int ColumnCount { get; set; }
        public int RowCount { get; set; }
        public TableLayoutColumnStyleCollection ColumnStyles { get; } = new TableLayoutColumnStyleCollection();
        public TableLayoutRowStyleCollection RowStyles { get; } = new TableLayoutRowStyleCollection();
        public TableLayoutPanelCellBorderStyle CellBorderStyle { get; set; }
        // WinForms TableLayoutPanel cell border widths
        int CellBorderWidth => CellBorderStyle == TableLayoutPanelCellBorderStyle.None ? 0 :
                               CellBorderStyle == TableLayoutPanelCellBorderStyle.Single ? 1 :
                               CellBorderStyle == TableLayoutPanelCellBorderStyle.Inset || CellBorderStyle == TableLayoutPanelCellBorderStyle.Outset ? 2 : 3;
        public TableLayoutPanelGrowStyle GrowStyle { get; set; } = TableLayoutPanelGrowStyle.AddRows;
        public new TableLayoutControlCollection Controls => (TableLayoutControlCollection)base.Controls;
        protected override ControlCollection CreateControlsInstance() => new TableLayoutControlCollection(this);
        public void SetCellPosition(Control control, int column, int row) { _cells[control] = (column, row); PerformLayout(); }
        public void SetColumn(Control control, int column) => SetCellPosition(control, column, GetRow(control));
        public void SetRow(Control control, int row) => SetCellPosition(control, GetColumn(control), row);
        public int GetColumn(Control control) => _cells.TryGetValue(control, out var c) ? c.Column : -1;
        public int GetRow(Control control) => _cells.TryGetValue(control, out var c) ? c.Row : -1;
        internal void Place(Control control, int column, int row)
        {
            if (column < 0 || row < 0)
            {
                // Next free cell, row by row.
                int columns = Math.Max(1, ColumnCount);
                for (int i = 0; ; i++)
                {
                    (int c, int r) cell = (i % columns, i / columns);
                    if (!System.Linq.Enumerable.Any(_cells.Values, v => v == cell)) { column = cell.c; row = cell.r; break; }
                }
            }
            _cells[control] = (column, row);
        }
        static int[] Sizes(int count, int total, System.Func<int, TableLayoutStyle> style, System.Func<int, float> value, System.Func<int, int> auto)
        {
            var sizes = new int[count];
            int used = 0;
            float percent = 0;
            for (int i = 0; i < count; i++)
            {
                TableLayoutStyle s = style(i);
                if (s == null || s.SizeType == SizeType.AutoSize) { sizes[i] = auto(i); used += sizes[i]; }
                else if (s.SizeType == SizeType.Absolute) { sizes[i] = (int)value(i); used += sizes[i]; }
                else percent += value(i);
            }
            int rest = Math.Max(0, total - used), given = 0, last = -1;
            for (int i = 0; i < count; i++)
                if (style(i)?.SizeType == SizeType.Percent) { sizes[i] = percent > 0 ? (int)(rest * value(i) / percent) : 0; given += sizes[i]; last = i; }
            // WinForms TableLayout: the last percent strip takes what the rounding left
            if (last >= 0 && percent > 0) sizes[last] += rest - given;
            return sizes;
        }
        protected override void LayoutChildren()
        {
            int columns = Math.Max(1, ColumnCount), rows = Math.Max(1, RowCount);
            foreach (var cell in _cells.Values) { columns = Math.Max(columns, cell.Column + 1); rows = Math.Max(rows, cell.Row + 1); }
            Size client = ClientSize;
            int border = CellBorderWidth;
            int AutoWidth(int column) { int w = 0; foreach (var p in _cells) if (p.Value.Column == column && p.Key.Visible) w = Math.Max(w, p.Key.Width + p.Key.Margin.Horizontal); return w; }
            int AutoHeight(int row) { int h = 0; foreach (var p in _cells) if (p.Value.Row == row && p.Key.Visible) h = Math.Max(h, p.Key.Height + p.Key.Margin.Vertical); return h; }
            int[] widths = Sizes(columns, client.Width - Padding.Horizontal - border * (columns + 1), i => i < ColumnStyles.Count ? ColumnStyles[i] : null, i => i < ColumnStyles.Count ? ColumnStyles[i].Width : 0, AutoWidth);
            int[] heights = Sizes(rows, client.Height - Padding.Vertical - border * (rows + 1), i => i < RowStyles.Count ? RowStyles[i] : null, i => i < RowStyles.Count ? RowStyles[i].Height : 0, AutoHeight);
            foreach (var p in _cells)
            {
                Control c = p.Key;
                int x = Padding.Left + border, y = Padding.Top + border;
                for (int i = 0; i < p.Value.Column; i++) x += widths[i] + border;
                for (int i = 0; i < p.Value.Row; i++) y += heights[i] + border;
                var cell = new Rectangle(x + c.Margin.Left, y + c.Margin.Top, Math.Max(0, widths[p.Value.Column] - c.Margin.Horizontal), Math.Max(0, heights[p.Value.Row] - c.Margin.Vertical));
                if (c.Dock == DockStyle.Fill) { c.Bounds = cell; continue; }
                bool l = (c.Anchor & AnchorStyles.Left) != 0, r = (c.Anchor & AnchorStyles.Right) != 0, t = (c.Anchor & AnchorStyles.Top) != 0, b = (c.Anchor & AnchorStyles.Bottom) != 0;
                int w = l && r ? cell.Width : c.Width, h = t && b ? cell.Height : c.Height;
                int cx = l ? cell.X : r ? cell.Right - w : cell.X + (cell.Width - w) / 2;
                int cy = t ? cell.Y : b ? cell.Bottom - h : cell.Y + (cell.Height - h) / 2;
                c.Bounds = new Rectangle(cx, cy, w, h);
            }
        }
    }
    public class TableLayoutControlCollection : Control.ControlCollection
    {
        public TableLayoutControlCollection(TableLayoutPanel container) : base(container) { }
        public TableLayoutPanel Container => (TableLayoutPanel)Owner;
        public void Add(Control control, int column, int row) { Container.Place(control, column, row); base.Add(control); }
        public new void Add(Control control) { Container.Place(control, -1, -1); base.Add(control); }
    }
}

namespace System.Windows.Forms
{
    /// <summary>WinForms MessageBox: shown by the cross-platform presenter of CaeGlobals.MessageBoxes. Open boxes are
    /// tracked by caption so the original Win32 close-by-caption path (AutoClosingMessageBox) can close them.</summary>
    public static class MessageBox
    {
        static readonly System.Collections.Generic.Dictionary<IntPtr, string> open = new System.Collections.Generic.Dictionary<IntPtr, string>();
        static long next;
        /// <summary>Renderer hook: closes the open box shown for the given handle (as WM_CLOSE: the Cancel/OK result).</summary>
        public static Action<IntPtr> CloseHandler;
        [ThreadStatic] static IntPtr showing;
        public static IntPtr CurrentHandle => showing;
        public static DialogResult Show(string text) => Show(null, text, "", MessageBoxButtons.OK, MessageBoxIcon.None);
        public static DialogResult Show(string text, string caption) => Show(null, text, caption, MessageBoxButtons.OK, MessageBoxIcon.None);
        public static DialogResult Show(string text, string caption, MessageBoxButtons buttons) => Show(null, text, caption, buttons, MessageBoxIcon.None);
        public static DialogResult Show(string text, string caption, MessageBoxButtons buttons, MessageBoxIcon icon) => Show(null, text, caption, buttons, icon);
        public static DialogResult Show(IWin32Window owner, string text, string caption, MessageBoxButtons buttons, MessageBoxIcon icon)
        {
            var presenter = CaeGlobals.MessageBoxes.InteractivePresenter;
            if (presenter == null) return CaeGlobals.MessageBoxes.ShowCrossThread(text, caption, buttons, icon);
            IntPtr handle = (IntPtr)System.Threading.Interlocked.Increment(ref next);
            lock (open) open[handle] = caption ?? "";
            IntPtr previous = showing;
            showing = handle;
            IntPtr dialog = NativeDialogs.Opened(caption);
            try { return presenter(owner, text, caption, buttons, icon); }
            finally { showing = previous; lock (open) open.Remove(handle); NativeDialogs.Closed(dialog); }
        }
        /// <summary>user32 FindWindow("#32770", caption) for message boxes.</summary>
        public static IntPtr FindOpen(string className, string caption)
        {
            if (className != "#32770") return IntPtr.Zero;
            lock (open) foreach (var p in open) if (p.Value == caption) return p.Key;
            return IntPtr.Zero;
        }
        /// <summary>user32 SendMessage(WM_CLOSE) to an open message box.</summary>
        public static IntPtr SendMessage(IntPtr handle, uint message, IntPtr wParam, IntPtr lParam)
        {
            const uint WM_CLOSE = 0x0010;
            bool known;
            lock (open) known = open.ContainsKey(handle);
            if (known && message == WM_CLOSE) CloseHandler?.Invoke(handle);
            return IntPtr.Zero;
        }
    }
}

namespace System.Windows.Forms.VisualStyles
{
    public enum GroupBoxState { Normal = 1, Disabled = 2 }
}
namespace System.Windows.Forms
{
    /// <summary>GDI+ painting entry points of original OnPaint overrides. The renderer draws controls itself and
    /// does not raise Paint, so these are reached only if a paint handler is called directly.</summary>
    public static class GroupBoxRenderer
    {
        public static void DrawGroupBox(Graphics g, Rectangle bounds, VisualStyles.GroupBoxState state) => throw new PlatformNotSupportedException("GDI+ painting: the renderer draws group boxes.");
    }
}

namespace System.Windows.Forms
{
    /// <summary>The platform keyboard layout for code that maps keys to characters itself (user32 ToUnicode):
    /// the renderer reports the key it is delivering and the text the platform produced for it.</summary>
    public static class KeyboardLayout
    {
        static Keys currentKey;
        static string currentText;
        public static void SetCurrent(Keys keyCode, string text) { currentKey = keyCode & Keys.KeyCode; currentText = text; }
        public static bool GetKeyboardState(byte[] keyState) => keyState != null;
        public static uint MapVirtualKey(uint code, uint mapType) => code;
        public static int ToUnicode(uint virtualKeyCode, byte[] keyState, System.Text.StringBuilder buffer)
        {
            if ((Keys)virtualKeyCode != currentKey || string.IsNullOrEmpty(currentText)) return 0;
            buffer.Append(currentText);
            return currentText.Length;
        }
    }
}
