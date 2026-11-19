// Headless WinForms control model for the original PrePoMax forms (D062).
// The original form classes are compiled unchanged against these types; a
// toolkit renderer (X/UI/original_forms.py) draws the control tree and feeds
// user input back through the same events WinForms would raise. Names and
// semantics follow System.Windows.Forms; only state and events are modelled.
using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Drawing;
using System.Linq;

namespace System.Windows.Forms
{
    /// <summary>Designer font description (System.Drawing.Font needs GDI+, which is Windows-only on .NET 10).</summary>
    public sealed class FontSpec
    {
        public string Name { get; }
        public float Size { get; }
        public FontStyle Style { get; }
        public bool Bold => (Style & FontStyle.Bold) != 0;
        public bool Italic => (Style & FontStyle.Italic) != 0;
        public bool Underline => (Style & FontStyle.Underline) != 0;
        public FontSpec(string name, float size) : this(name, size, FontStyle.Regular) { }
        public FontSpec(string name, float size, FontStyle style) { Name = name; Size = size; Style = style; }
        public FontSpec(string name, float size, FontStyle style, GraphicsUnit unit) : this(name, size, style) { }
        public FontSpec(string name, float size, FontStyle style, GraphicsUnit unit, byte charSet) : this(name, size, style) { }
        public FontSpec(FontSpec prototype, FontStyle style) : this(prototype?.Name ?? "Segoe UI", prototype?.Size ?? 9F, style) { }
        public static FontSpec Default { get; } = new FontSpec("Segoe UI", 9F);
        /// <summary>System.Drawing.Font is IDisposable; a description holds nothing.</summary>
        public void Dispose() { }
    }

    /// <summary>An original embedded image (Properties.Resources entry) by name and repository file.</summary>
    public sealed class ImageResource
    {
        public string Name { get; }
        public string Path { get; }
        /// <summary>Path is the image file, or the form's .resx for an image stored in it (Name = resx entry).</summary>
        public ImageResource(string name, string path) { Name = name; Path = path; }
        public override string ToString() => Name;
    }

    /// <summary>ComponentResourceManager stand-in for the designer images of a form: entries of the original .resx
    /// (base64 image bytes, read by the renderer; nothing is deserialized). Form icons are the application's.</summary>
    public sealed class ResxResources
    {
        public string Path { get; }
        public ResxResources(string path) { Path = path; }
        public object GetObject(string name) => new ImageResource(name, Path);
        public System.Drawing.Icon GetIcon(string name) => null;
        public string GetString(string name) => null;
        public void ApplyResources(object value, string objectName) { }
    }

    public enum ImageLayout { None, Tile, Center, Stretch, Zoom }
    public enum AnchorStyles { None = 0, Top = 1, Bottom = 2, Left = 4, Right = 8 }
    public enum DockStyle { None, Top, Bottom, Left, Right, Fill }
    public enum AutoScaleMode { None, Font, Dpi, Inherit }
    public enum FormStartPosition { Manual, CenterScreen, WindowsDefaultLocation, WindowsDefaultBounds, CenterParent }
    public enum FormBorderStyle { None, FixedSingle, Fixed3D, FixedDialog, Sizable, FixedToolWindow, SizableToolWindow }
    public enum CloseReason { None, WindowsShutDown, MdiFormClosing, UserClosing, TaskManagerClosing, FormOwnerClosing, ApplicationExitCall }
    public enum View { LargeIcon, Details, SmallIcon, List, Tile }
    public enum ColumnHeaderStyle { None, Nonclickable, Clickable }
    public enum HorizontalAlignment { Left, Right, Center }
    public enum Appearance { Normal, Button }
    public enum FlatStyle { Flat, Popup, Standard, System }
    public enum ScrollBars { None, Horizontal, Vertical, Both }
    public enum PropertySort { NoSort = 0, Alphabetical = 1, Categorized = 2, CategorizedAlphabetical = 3 }
    public enum GridItemType { Property, Category, ArrayValue, Root }
    public enum ToolStripItemDisplayStyle { None, Text, Image, ImageAndText }
    public enum ImeMode { Inherit = -1, NoControl = 0, On = 1, Off = 2, Disable = 3 }
    public enum RightToLeft { No, Yes, Inherit }
    public enum BorderStyle { None, FixedSingle, Fixed3D }
    public enum TabAlignment { Top, Bottom, Left, Right }
    public enum TabSizeMode { Normal, FillToRight, Fixed }
    public enum SizeType { AutoSize, Absolute, Percent }
    public enum AutoSizeMode { GrowAndShrink, GrowOnly }

    public struct Padding
    {
        public int Left, Top, Right, Bottom;
        public Padding(int all) { Left = Top = Right = Bottom = all; }
        public Padding(int left, int top, int right, int bottom) { Left = left; Top = top; Right = right; Bottom = bottom; }
        public int All { get => Left; set { Left = Top = Right = Bottom = value; } }
        public int Horizontal => Left + Right;
        public int Vertical => Top + Bottom;
        public static readonly Padding Empty = new Padding(0);
    }

    [Flags] public enum ControlStyles { ContainerControl = 1, UserPaint = 2, Opaque = 4, ResizeRedraw = 16, FixedWidth = 32, FixedHeight = 64, StandardClick = 256, Selectable = 512, UserMouse = 1024, SupportsTransparentBackColor = 2048, StandardDoubleClick = 4096, AllPaintingInWmPaint = 8192, CacheText = 16384, EnableNotifyMessage = 32768, DoubleBuffer = 65536, OptimizedDoubleBuffer = 131072, UseTextForAccessibility = 262144 }
    /// <summary>Text clipboard; the renderer installs the platform clipboard.</summary>
    public static class Clipboard
    {
        public static Func<string> GetTextHandler;
        public static Action<string> SetTextHandler;
        static string local = "";
        public static string GetText() => GetTextHandler != null ? GetTextHandler() ?? "" : local;
        public static void SetText(string text) { if (SetTextHandler != null) SetTextHandler(text); else local = text ?? ""; }
        public static bool ContainsText() => GetText().Length > 0;
        public static void Clear() => SetText("");
        // Data objects: the text goes to the platform clipboard; the object (with its private formats) is kept
        // while the clipboard still holds its text (WinForms keeps every format of a SetDataObject).
        static DataObject stored;
        public static void SetDataObject(object data) { stored = data as DataObject ?? new DataObject(data); SetText(stored.GetText()); }
        public static void SetDataObject(object data, bool copy) => SetDataObject(data);
        public static IDataObject GetDataObject()
        {
            string text = GetText();
            if (stored != null && stored.GetText() == text) return stored;
            return new DataObject(DataFormats.UnicodeText, text);
        }
    }
    public class CreateParams { public int ExStyle; public int Style; public int ClassStyle; public string Caption; public string ClassName; }

    public class ControlEventArgs : EventArgs { public Control Control { get; } public ControlEventArgs(Control control) { Control = control; } }
    public class KeyEventArgs : EventArgs
    {
        public Keys KeyData { get; }
        public Keys KeyCode => KeyData & Keys.KeyCode;
        public Keys Modifiers => KeyData & Keys.Modifiers;
        public bool Control => (KeyData & Keys.Control) != 0;
        public bool Shift => (KeyData & Keys.Shift) != 0;
        public bool Alt => (KeyData & Keys.Alt) != 0;
        public int KeyValue => (int)(KeyData & Keys.KeyCode);
        public bool Handled { get; set; }
        public bool SuppressKeyPress { get; set; }
        public KeyEventArgs(Keys keyData) { KeyData = keyData; }
    }
    public class KeyPressEventArgs : EventArgs { public char KeyChar { get; set; } public bool Handled { get; set; } public KeyPressEventArgs(char keyChar) { KeyChar = keyChar; } }
    public class FormClosingEventArgs : CancelEventArgs { public CloseReason CloseReason { get; } public FormClosingEventArgs(CloseReason reason, bool cancel) : base(cancel) { CloseReason = reason; } }
    public class FormClosedEventArgs : EventArgs { public CloseReason CloseReason { get; } public FormClosedEventArgs(CloseReason reason) { CloseReason = reason; } }
    public class PaintEventArgs : EventArgs { public Graphics Graphics { get; } public Rectangle ClipRectangle { get; } public PaintEventArgs(Graphics graphics, Rectangle clip) { Graphics = graphics; ClipRectangle = clip; } }
    public class ItemCheckEventArgs : EventArgs { public int Index { get; } public CheckState NewValue { get; set; } public CheckState CurrentValue { get; } public ItemCheckEventArgs(int index, CheckState newValue, CheckState currentValue) { Index = index; NewValue = newValue; CurrentValue = currentValue; } }
    public enum CheckState { Unchecked, Checked, Indeterminate }
    public class ListViewItemSelectionChangedEventArgs : EventArgs { public ListViewItem Item { get; } public int ItemIndex { get; } public bool IsSelected { get; } public ListViewItemSelectionChangedEventArgs(ListViewItem item, int index, bool selected) { Item = item; ItemIndex = index; IsSelected = selected; } }
    public class ToolStripItemClickedEventArgs : EventArgs { public ToolStripItem ClickedItem { get; } public ToolStripItemClickedEventArgs(ToolStripItem item) { ClickedItem = item; } }
    public class TabControlEventArgs : EventArgs { public TabPage TabPage { get; } public int TabPageIndex { get; } public TabControlEventArgs(TabPage page, int index) { TabPage = page; TabPageIndex = index; } }
    public class PreviewKeyDownEventArgs : EventArgs { public Keys KeyData { get; } public bool IsInputKey { get; set; } public PreviewKeyDownEventArgs(Keys keyData) { KeyData = keyData; } }

    public delegate void KeyEventHandler(object sender, KeyEventArgs e);
    public delegate void KeyPressEventHandler(object sender, KeyPressEventArgs e);
    public delegate void MouseEventHandler(object sender, MouseEventArgs e);
    public delegate void FormClosingEventHandler(object sender, FormClosingEventArgs e);
    public delegate void FormClosedEventHandler(object sender, FormClosedEventArgs e);
    public delegate void PaintEventHandler(object sender, PaintEventArgs e);
    public delegate void LayoutEventHandler(object sender, LayoutEventArgs e);
    public sealed class LayoutEventArgs : EventArgs { public Control AffectedControl { get; } public string AffectedProperty { get; } public LayoutEventArgs(Control affectedControl, string affectedProperty) { AffectedControl = affectedControl; AffectedProperty = affectedProperty; } }
    public delegate void ControlEventHandler(object sender, ControlEventArgs e);
    public delegate void ItemCheckEventHandler(object sender, ItemCheckEventArgs e);
    public delegate void ListViewItemSelectionChangedEventHandler(object sender, ListViewItemSelectionChangedEventArgs e);
    public delegate void ToolStripItemClickedEventHandler(object sender, ToolStripItemClickedEventArgs e);
    public delegate void TabControlEventHandler(object sender, TabControlEventArgs e);
    public delegate void PreviewKeyDownEventHandler(object sender, PreviewKeyDownEventArgs e);
    public delegate void PropertyValueChangedEventHandler(object s, PropertyValueChangedEventArgs e);
    public delegate void SelectedGridItemChangedEventHandler(object sender, SelectedGridItemChangedEventArgs e);

    /// <summary>Raised for every state change a renderer must mirror (control, property name).</summary>
    public static class ControlNotifications
    {
        public static event Action<Control, string> Changed;
        internal static void Raise(Control control, string property) => Changed?.Invoke(control, property);
    }

    public class Control : Component, IWin32Window
    {
        string _text = "";
        Point _location;
        Size _size;
        bool _visible = true, _enabled = true;
        int _layoutSuspended;
        Control _parent;

        public Control() { Controls = CreateControlsInstance(); }
        protected virtual ControlCollection CreateControlsInstance() => new ControlCollection(this);
        IntPtr _nativeWindow;
        /// <summary>Zero, except for a control the renderer shows in a native window of its own (the 3D view).</summary>
        public IntPtr Handle => _nativeWindow;
        /// <summary>The renderer gives the control the native window it shows it in (a Qt widget's NSView or X11
        /// window); the control then gets OnHandleCreated, as a WinForms control does when its window is created.</summary>
        public void AttachNativeWindow(IntPtr window)
        {
            if (window == IntPtr.Zero) throw new ArgumentException("A native window is required.", nameof(window));
            if (_nativeWindow != IntPtr.Zero) throw new InvalidOperationException("The control already has a native window.");
            _nativeWindow = window;
            OnHandleCreated(EventArgs.Empty);
        }
        /// <summary>Before the renderer destroys the native window: OnHandleDestroyed, while the window still exists.</summary>
        public void DetachNativeWindow()
        {
            if (_nativeWindow == IntPtr.Zero) return;
            OnHandleDestroyed(EventArgs.Empty);
            _nativeWindow = IntPtr.Zero;
        }
        public bool IsHandleCreated => true;
        public bool IsDisposed { get; private set; }
        public bool Disposing => false;
        public string Name { get; set; } = "";
        public object Tag { get; set; }
        public virtual string Text { get => _text; set { value ??= ""; if (_text == value) return; _text = value; Notify(nameof(Text)); OnTextChanged(EventArgs.Empty); } }
        public Point Location { get => _location; set { if (_location == value) return; _location = value; UpdateAnchorInfo(); Notify(nameof(Location)); OnLocationChanged(EventArgs.Empty); } }
        public virtual Size Size { get => _size; set => SetSizeCore(value); }
        protected void SetSizeCore(Size value)
        {
            if (_size == value) return;
            _size = value;
            UpdateAnchorInfo();
            if (_layoutSuspended == 0) OnLayout(new LayoutEventArgs(this, "Bounds"));
            if (_dock != DockStyle.None) RelayoutParentForDock();
            Notify(nameof(Size));
            OnSizeChanged(EventArgs.Empty);
            OnResize(EventArgs.Empty);
        }

        // WinForms anchoring/docking: a child keeps its distances to the anchored edges of its parent's client
        // area. Distances are taken whenever the child's bounds are set or the parent's layout resumes, and
        // applied whenever the parent's size changes while its layout is not suspended.
        int _gapRight, _gapBottom;
        internal void UpdateAnchorInfo()
        {
            if (_parent == null) return;
            Size client = _parent.ClientSize;
            _gapRight = client.Width - Right;
            _gapBottom = client.Height - Bottom;
        }
        protected virtual void LayoutChildren()
        {
            Size client = ClientSize;
            // WinForms DefaultLayout: docked controls in reverse z-order (last in Controls first) take their edge of
            // the remaining client area (inside Padding); invisible controls take no space.
            Control[] children = Controls.Cast<Control>().ToArray();
            Rectangle remaining = new Rectangle(Padding.Left, Padding.Top, Math.Max(0, client.Width - Padding.Horizontal), Math.Max(0, client.Height - Padding.Vertical));
            for (int i = children.Length - 1; i >= 0; i--)
            {
                Control c = children[i];
                if (c.Dock == DockStyle.None || !c._visible) continue;
                switch (c.Dock)
                {
                    case DockStyle.Top: c.Bounds = new Rectangle(remaining.X, remaining.Y, remaining.Width, c.Height); remaining.Y += c.Height; remaining.Height = Math.Max(0, remaining.Height - c.Height); break;
                    case DockStyle.Bottom: c.Bounds = new Rectangle(remaining.X, remaining.Bottom - c.Height, remaining.Width, c.Height); remaining.Height = Math.Max(0, remaining.Height - c.Height); break;
                    case DockStyle.Left: c.Bounds = new Rectangle(remaining.X, remaining.Y, c.Width, remaining.Height); remaining.X += c.Width; remaining.Width = Math.Max(0, remaining.Width - c.Width); break;
                    case DockStyle.Right: c.Bounds = new Rectangle(remaining.Right - c.Width, remaining.Y, c.Width, remaining.Height); remaining.Width = Math.Max(0, remaining.Width - c.Width); break;
                    case DockStyle.Fill: c.Bounds = remaining; break;
                }
            }
            foreach (Control c in children)
            {
                if (c.Dock != DockStyle.None) continue;
                int gapRight = c._gapRight, gapBottom = c._gapBottom;
                int x = c.Left, y = c.Top, w = c.Width, h = c.Height;
                bool left = (c.Anchor & AnchorStyles.Left) != 0, right = (c.Anchor & AnchorStyles.Right) != 0;
                bool top = (c.Anchor & AnchorStyles.Top) != 0, bottom = (c.Anchor & AnchorStyles.Bottom) != 0;
                if (right) { if (left) w = Math.Max(0, client.Width - gapRight - x); else x = client.Width - gapRight - w; }
                if (bottom) { if (top) h = Math.Max(0, client.Height - gapBottom - y); else y = client.Height - gapBottom - h; }
                if (x != c.Left || y != c.Top || w != c.Width || h != c.Height) c.Bounds = new Rectangle(x, y, w, h);
                c._gapRight = gapRight; c._gapBottom = gapBottom;
            }
        }
        public Size ClientSize { get => ClientSizeCore; set => ClientSizeCore = value; }
        protected virtual Size ClientSizeCore { get => Size; set => Size = value; }
        public Rectangle ClientRectangle => new Rectangle(Point.Empty, ClientSize);
        public Rectangle Bounds { get => new Rectangle(Location, Size); set { Location = value.Location; Size = value.Size; } }
        public Rectangle DisplayRectangle => ClientRectangle;
        public int Left { get => Location.X; set => Location = new Point(value, Top); }
        public int Top { get => Location.Y; set => Location = new Point(Left, value); }
        public int Width { get => Size.Width; set => Size = new Size(value, Height); }
        public int Height { get => Size.Height; set => Size = new Size(Width, value); }
        public int Right => Left + Width;
        public int Bottom => Top + Height;
        public Size MinimumSize { get; set; }
        public Size MaximumSize { get; set; }
        public AnchorStyles Anchor { get; set; } = AnchorStyles.Top | AnchorStyles.Left;
        DockStyle _dock;
        bool _inParentLayout;
        public DockStyle Dock { get => _dock; set { if (_dock == value) return; _dock = value; RelayoutParentForDock(); } }
        void RelayoutParentForDock()
        {
            if (_parent != null && _parent._layoutSuspended != 0) _parent._layoutDeferred = true;
            if (_parent == null || _parent._layoutSuspended != 0 || _parent._inParentLayout) return;
            _parent._inParentLayout = true;
            try { _parent.PerformLayout(); } finally { _parent._inParentLayout = false; }
        }
        public Padding Margin { get; set; } = new Padding(3);
        public Padding Padding { get; set; }
        public int TabIndex { get; set; }
        public bool TabStop { get; set; } = true;
        public bool AutoSize { get; set; }
        public AutoSizeMode AutoSizeMode { get; set; }
        FontSpec _font = FontSpec.Default;
        public virtual FontSpec Font { get => _font; set => _font = value; }
        public Color BackColor { get; set; } = SystemColors.Control;
        public ImageLayout BackgroundImageLayout { get; set; }
        public Color ForeColor { get; set; } = SystemColors.ControlText;
        public ImageResource BackgroundImage { get; set; }
        public ImeMode ImeMode { get; set; }
        public RightToLeft RightToLeft { get; set; }
        public Cursor Cursor { get; set; }
        public bool CausesValidation { get; set; } = true;
        public bool UseWaitCursor { get; set; }
        public bool AllowDrop { get; set; }
        public ContextMenuStrip ContextMenuStrip { get; set; }
        public ControlCollection Controls { get; }
        public bool HasChildren => Controls.Count > 0;
        public Control Parent { get => _parent; set { if (_parent == value) return; _parent?.Controls.Remove(this); value?.Controls.Add(this); } }
        internal void SetParentInternal(Control parent) { _parent = parent; Notify(nameof(Parent)); }
        internal void SetVisibleCore(bool value) => _visible = value;
        public Form FindForm() { for (Control c = this; c != null; c = c._parent) if (c is Form f) return f; return null; }
        public Control TopLevelControl { get { Control c = this; while (c._parent != null) c = c._parent; return c; } }
        bool _focused;
        // WinForms Control.Focused is virtual (the original PythonPanel overrides it)
        public virtual bool Focused { get => _focused; }
        public bool ContainsFocus => _focused || Controls.Cast<Control>().Any(c => c.ContainsFocus);
        public BindingContext BindingContext { get; set; } = new BindingContext();
        public ControlBindingsCollection DataBindings { get; } = new ControlBindingsCollection();

        public bool Visible
        {
            get => _visible && (_parent == null || _parent.Visible);
            set
            {
                if (_visible == value) return;
                _visible = value;
                // WinForms: a control that is shown is created (CreateControl), which performs the layout deferred
                // while its layout was suspended (ResumeLayout(false) leaves it pending)
                if (value && Visible) PerformDeferredLayouts();
                Notify(nameof(Visible));
                if (_dock != DockStyle.None) RelayoutParentForDock();
                OnVisibleChanged(EventArgs.Empty);
            }
        }
        bool _layoutDeferred;
        /// <summary>The layouts deferred in this control and its children (STATE_LAYOUTDEFERRED), performed in order.</summary>
        internal void PerformDeferredLayouts()
        {
            if (_layoutSuspended != 0) return;
            if (_layoutDeferred) { _layoutDeferred = false; OnLayout(new LayoutEventArgs(this, null)); Notify("Layout"); }
            foreach (Control c in Controls) if (c._visible) c.PerformDeferredLayouts();
        }
        internal bool VisibleCore => _visible;
        public bool Enabled
        {
            get => _enabled && (_parent == null || _parent.Enabled);
            set { if (_enabled == value) return; _enabled = value; Notify(nameof(Enabled)); OnEnabledChanged(EventArgs.Empty); }
        }

        protected void Notify(string property) { if (_layoutSuspended == 0 || property == nameof(Visible)) ControlNotifications.Raise(this, property); }
        public void SuspendLayout() => _layoutSuspended++;
        public void ResumeLayout() => ResumeLayout(true);
        public void ResumeLayout(bool performLayout)
        {
            if (_layoutSuspended > 0 && --_layoutSuspended == 0)
            {
                foreach (Control c in Controls) c.UpdateAnchorInfo();
                if (performLayout) { _layoutDeferred = false; OnLayout(new LayoutEventArgs(this, null)); }
                Notify("Layout");
            }
        }
        public void PerformLayout() { OnLayout(new LayoutEventArgs(this, null)); Notify("Layout"); }
        /// <summary>WinForms: OnLayout runs the layout engine (anchoring/docking), then raises Layout.</summary>
        protected virtual void OnLayout(LayoutEventArgs levent) { LayoutChildren(); Layout?.Invoke(this, levent); }
        public void Show() => Visible = true;
        public void Hide() => Visible = false;
        public bool Focus() { _focused = true; Notify("Focus"); OnGotFocus(EventArgs.Empty); return true; }
        public void Select() => Focus();
        public virtual void Refresh() => Notify("Refresh");
        public void Invalidate() => Notify("Refresh");
        public void Invalidate(bool invalidateChildren) => Notify("Refresh");
        public void Invalidate(Rectangle rectangle) => Notify("Refresh");
        public void Invalidate(Rectangle rectangle, bool invalidateChildren) => Notify("Refresh");
        public void Update() { }
        public void BringToFront() => Notify("ZOrder");
        public void SendToBack() => Notify("ZOrder");
        public void CreateControl() { }
        // WinForms marshalling: Invoke runs on the UI thread and waits; BeginInvoke always queues to the UI thread's
        // message loop (also when called on it). The host installs its UI context; without one calls run inline.
        static System.Threading.SynchronizationContext _uiContext;
        static int _uiThread;
        public static void SetUiThreadContext(System.Threading.SynchronizationContext context) { _uiContext = context; _uiThread = Environment.CurrentManagedThreadId; }
        public object Invoke(Delegate method) => Invoke(method, null);
        public object Invoke(Delegate method, params object[] args)
        {
            if (!InvokeRequired) return method.DynamicInvoke(args);
            object result = null;
            _uiContext.Send(_ => result = method.DynamicInvoke(args), null);
            return result;
        }
        public IAsyncResult BeginInvoke(Delegate method) => BeginInvoke(method, null);
        public IAsyncResult BeginInvoke(Delegate method, params object[] args)
        {
            if (_uiContext == null) method.DynamicInvoke(args);
            else _uiContext.Post(_ => method.DynamicInvoke(args), null);
            return null;
        }
        public bool InvokeRequired => _uiContext != null && Environment.CurrentManagedThreadId != _uiThread;
        public Point PointToScreen(Point p) => p;
        public Point PointToClient(Point p) => p;
        /// <summary>A focus rectangle an original control drew over itself (FocusSurface); the renderer draws it.</summary>
        public Rectangle FocusRectangle { get; private set; }
        public Color FocusRectangleColor { get; private set; }
        internal void SetFocusRectangle(Color color, Rectangle rect) { FocusRectangle = rect; FocusRectangleColor = color; Notify("Refresh"); }
        public Graphics CreateGraphics() => throw new PlatformNotSupportedException("GDI+ drawing is not available; the renderer owns painting.");
        public void SetBounds(int x, int y, int width, int height) { Location = new Point(x, y); Size = new Size(width, height); }
        public bool SelectNextControl(Control ctl, bool forward, bool tabStopOnly, bool nested, bool wrap) => true;
        protected override void Dispose(bool disposing) { IsDisposed = true; base.Dispose(disposing); }

        public event EventHandler Click, DoubleClick, TextChanged, VisibleChanged, EnabledChanged, Resize, SizeChanged, LocationChanged, Move,
            GotFocus, LostFocus, Enter, Leave, Validated, MouseEnter, MouseLeave, MouseHover, HandleCreated, HandleDestroyed, ParentChanged, BackColorChanged, FontChanged;
        public event CancelEventHandler Validating;
        public event LayoutEventHandler Layout;
        public event DragEventHandler DragDrop, DragEnter, DragOver;
        public event EventHandler DragLeave;
        protected virtual void OnDragDrop(DragEventArgs e) => DragDrop?.Invoke(this, e);
        protected virtual void OnDragEnter(DragEventArgs e) => DragEnter?.Invoke(this, e);
        protected virtual void OnDragOver(DragEventArgs e) => DragOver?.Invoke(this, e);
        protected virtual void OnDragLeave(EventArgs e) => DragLeave?.Invoke(this, e);
        /// <summary>Drag source: the renderer runs the toolkit drag; returns the effect the drop target chose.</summary>
        public static Func<Control, object, DragDropEffects, DragDropEffects> DoDragDropHandler;
        public DragDropEffects DoDragDrop(object data, DragDropEffects allowedEffects) => DoDragDropHandler?.Invoke(this, data, allowedEffects) ?? DragDropEffects.None;
        public void RaiseDragEnter(DragEventArgs e) => OnDragEnter(e);
        public void RaiseDragOver(DragEventArgs e) => OnDragOver(e);
        public void RaiseDragDrop(DragEventArgs e) => OnDragDrop(e);
        public void RaiseDragLeave() => OnDragLeave(EventArgs.Empty);
        public event MouseEventHandler MouseDown, MouseUp, MouseMove, MouseClick, MouseDoubleClick, MouseWheel;
        public event KeyEventHandler KeyDown, KeyUp;
        public event KeyPressEventHandler KeyPress;
        public event PreviewKeyDownEventHandler PreviewKeyDown;
        public event PaintEventHandler Paint;
        public event ControlEventHandler ControlAdded, ControlRemoved;

        protected virtual void OnTextChanged(EventArgs e) => TextChanged?.Invoke(this, e);
        protected virtual void OnVisibleChanged(EventArgs e) { VisibleChanged?.Invoke(this, e); foreach (Control c in Controls.Cast<Control>().ToArray()) if (c._visible) c.OnParentVisibleChanged(e); }
        protected virtual void OnParentVisibleChanged(EventArgs e) => OnVisibleChanged(e);
        protected virtual void OnEnabledChanged(EventArgs e) => EnabledChanged?.Invoke(this, e);
        protected virtual void OnResize(EventArgs e) => Resize?.Invoke(this, e);
        protected virtual void OnSizeChanged(EventArgs e) => SizeChanged?.Invoke(this, e);
        protected virtual void OnLocationChanged(EventArgs e) { LocationChanged?.Invoke(this, e); Move?.Invoke(this, e); }
        protected virtual void OnClick(EventArgs e) => Click?.Invoke(this, e);
        protected virtual void OnDoubleClick(EventArgs e) => DoubleClick?.Invoke(this, e);
        protected virtual void OnGotFocus(EventArgs e) => GotFocus?.Invoke(this, e);
        protected virtual void OnLostFocus(EventArgs e) => LostFocus?.Invoke(this, e);
        protected virtual void OnEnter(EventArgs e) => Enter?.Invoke(this, e);
        protected virtual void OnLeave(EventArgs e) => Leave?.Invoke(this, e);
        protected virtual void OnMouseDown(MouseEventArgs e) => MouseDown?.Invoke(this, e);
        protected virtual void OnMouseUp(MouseEventArgs e) => MouseUp?.Invoke(this, e);
        protected virtual void OnMouseMove(MouseEventArgs e) => MouseMove?.Invoke(this, e);
        protected virtual void OnMouseClick(MouseEventArgs e) => MouseClick?.Invoke(this, e);
        protected virtual void OnMouseDoubleClick(MouseEventArgs e) => MouseDoubleClick?.Invoke(this, e);
        protected virtual void OnMouseEnter(EventArgs e) => MouseEnter?.Invoke(this, e);
        protected virtual void OnMouseLeave(EventArgs e) => MouseLeave?.Invoke(this, e);
        protected virtual void OnMouseWheel(MouseEventArgs e) => MouseWheel?.Invoke(this, e);
        protected virtual void OnKeyDown(KeyEventArgs e) => KeyDown?.Invoke(this, e);
        protected virtual void OnKeyUp(KeyEventArgs e) => KeyUp?.Invoke(this, e);
        protected virtual void OnKeyPress(KeyPressEventArgs e) => KeyPress?.Invoke(this, e);
        protected virtual void OnPreviewKeyDown(PreviewKeyDownEventArgs e) => PreviewKeyDown?.Invoke(this, e);
        protected virtual void OnPaint(PaintEventArgs e) => Paint?.Invoke(this, e);
        protected virtual void OnPaintBackground(PaintEventArgs e) { }
        protected virtual void OnMouseCaptureChanged(EventArgs e) => MouseCaptureChanged?.Invoke(this, e);
        public event EventHandler MouseCaptureChanged;
        protected virtual void OnHandleCreated(EventArgs e) => HandleCreated?.Invoke(this, e);
        protected virtual void OnHandleDestroyed(EventArgs e) => HandleDestroyed?.Invoke(this, e);
        protected virtual void OnValidating(CancelEventArgs e) => Validating?.Invoke(this, e);
        protected virtual void OnValidated(EventArgs e) => Validated?.Invoke(this, e);
        protected virtual void OnControlAdded(ControlEventArgs e) => ControlAdded?.Invoke(this, e);
        protected virtual void OnControlRemoved(ControlEventArgs e) => ControlRemoved?.Invoke(this, e);
        // WinForms: a command key goes to the focused control first and bubbles up through its parents to the form.
        protected virtual bool ProcessCmdKey(ref Message msg, Keys keyData) => _parent != null && _parent.ProcessCmdKey(ref msg, keyData);
        protected virtual void WndProc(ref Message m) { }
        protected virtual void DefWndProc(ref Message m) { }
        protected void SetStyle(ControlStyles flag, bool value) { }
        protected bool GetStyle(ControlStyles flag) => false;
        protected virtual bool DoubleBuffered { get; set; }
        protected virtual void OnCreateControl() { }
        protected void UpdateStyles() { }
        protected void RecreateHandle() { }
        public static Point MousePosition { get; set; }
        public static Keys ModifierKeys { get; set; }
        public static MouseButtons MouseButtons { get; set; }
        protected virtual bool ProcessDialogKey(Keys keyData) => false;
        protected virtual bool IsInputKey(Keys keyData) => false;

        // Renderer input: the same notifications WinForms raises for user actions.
        public void RaiseClick() { if (Enabled) OnClick(EventArgs.Empty); }
        public void RaiseDoubleClick() { if (Enabled) OnDoubleClick(EventArgs.Empty); }
        public void RaiseMouse(string kind, MouseButtons button, int clicks, int x, int y)
        {
            var e = new MouseEventArgs(button, clicks, x, y, 0);
            switch (kind)
            {
                case "down": OnMouseDown(e); break;
                case "up": OnMouseUp(e); break;
                case "click": OnMouseClick(e); break;
                case "doubleclick": OnMouseDoubleClick(e); break;
                case "move": OnMouseMove(e); break;
            }
        }
        public bool RaiseKeyDown(Keys keyData) => RaiseKeyInput(keyData, null);
        /// <summary>A key press: WM_KEYDOWN (command keys, KeyDown) and, unless the KeyDown suppressed it, the
        /// character the keyboard layout produced (WM_CHAR, KeyPress). Returns whether the key was handled.</summary>
        public bool RaiseKeyInput(Keys keyData, string text)
        {
            var message = new Message();
            if (ProcessCmdKey(ref message, keyData)) return true;
            var e = new KeyEventArgs(keyData);
            if (FindForm() is Form f && f.KeyPreview && f != this) f.OnKeyDownInternal(e);
            if (!e.Handled) OnKeyDown(e);
            if (!e.SuppressKeyPress && !string.IsNullOrEmpty(text))
                foreach (char c in text) ProcessCharInput(c, keyData & Keys.Modifiers);
            return e.Handled || e.SuppressKeyPress;
        }
        /// <summary>WM_CHAR: ProcessKeyMessage, then KeyPress.</summary>
        protected virtual void ProcessCharInput(char c, Keys modifiers) => OnKeyPress(new KeyPressEventArgs(c));
        public void RaiseKeyUp(Keys keyData) => OnKeyUp(new KeyEventArgs(keyData));
        public void RaiseEnter() { _focused = true; OnEnter(EventArgs.Empty); OnGotFocus(EventArgs.Empty); }
        public void RaiseLeave() { _focused = false; OnLeave(EventArgs.Empty); OnLostFocus(EventArgs.Empty); }
        public void RaiseMouseEnter() => OnMouseEnter(EventArgs.Empty);
        /// <summary>Whether the control paints itself (a Paint handler): the renderer shows its painting.</summary>
        public bool HasPaintHandler => Paint != null;
        /// <summary>Renderer input: WM_PAINT. The control paints its client area (OnPaintBackground, then OnPaint and
        /// its Paint handlers) on a recording surface, which the renderer replays with its own painter.</summary>
        public Graphics RenderPaint()
        {
            var graphics = new Graphics(ClientRectangle);
            var e = new PaintEventArgs(graphics, ClientRectangle);
            OnPaintBackground(e);
            OnPaint(e);
            return graphics;
        }
        public void RaiseMouseLeave() => OnMouseLeave(EventArgs.Empty);
        internal void OnKeyDownInternal(KeyEventArgs e) => OnKeyDown(e);

        public class ControlCollection : IList, IEnumerable<Control>
        {
            readonly Control owner;
            readonly List<Control> items = new List<Control>();
            public ControlCollection(Control owner) { this.owner = owner; }
            public Control Owner => owner;
            public int Count => items.Count;
            public Control this[int index] => items[index];
            public Control this[string key] => items.FirstOrDefault(c => c.Name == key);
            public void Add(Control value)
            {
                if (value == null || items.Contains(value)) return;
                value._parent?.Controls.Remove(value);
                items.Add(value);
                value.SetParentInternal(owner);
                value.UpdateAnchorInfo();
                // WinForms lays the parent out for an added control; while its layout is suspended the layout is
                // deferred (ResumeLayout(true) or the parent's creation performs it)
                owner._layoutDeferred = true;
                owner.OnControlAdded(new ControlEventArgs(value));
                owner.Notify("Controls");
                // A shown parent lays out now, and the added control is created and performs its deferred layouts
                if (owner.Visible) owner.PerformDeferredLayouts();
            }
            public void AddRange(Control[] controls) { foreach (Control c in controls) Add(c); }
            public void Remove(Control value)
            {
                if (!items.Remove(value)) return;
                value.SetParentInternal(null);
                owner.OnControlRemoved(new ControlEventArgs(value));
                owner.Notify("Controls");
            }
            public void RemoveAt(int index) => Remove(items[index]);
            public void Clear() { foreach (Control c in items.ToArray()) Remove(c); }
            public bool Contains(Control c) => items.Contains(c);
            public int IndexOf(Control c) => items.IndexOf(c);
            public int GetChildIndex(Control c) => items.IndexOf(c);
            public void SetChildIndex(Control c, int index) { if (!items.Remove(c)) return; items.Insert(Math.Min(index, items.Count), c); owner.Notify("ZOrder"); }
            public Control[] Find(string key, bool searchAllChildren)
            {
                var found = new List<Control>();
                foreach (Control c in items) { if (c.Name == key) found.Add(c); if (searchAllChildren) found.AddRange(c.Controls.Find(key, true)); }
                return found.ToArray();
            }
            public IEnumerator<Control> GetEnumerator() => items.GetEnumerator();
            IEnumerator IEnumerable.GetEnumerator() => items.GetEnumerator();
            int IList.Add(object value) { Add((Control)value); return items.Count - 1; }
            bool IList.Contains(object value) => items.Contains(value as Control);
            int IList.IndexOf(object value) => items.IndexOf(value as Control);
            void IList.Insert(int index, object value) => throw new NotSupportedException();
            void IList.Remove(object value) => Remove((Control)value);
            bool IList.IsFixedSize => false;
            bool IList.IsReadOnly => false;
            object IList.this[int index] { get => items[index]; set => throw new NotSupportedException(); }
            void ICollection.CopyTo(Array array, int index) => ((ICollection)items).CopyTo(array, index);
            bool ICollection.IsSynchronized => false;
            object ICollection.SyncRoot => this;
        }
    }

    public class Cursor { public static Point Position { get; set; } }
    public static class Cursors { public static readonly Cursor Default = new Cursor(), WaitCursor = new Cursor(), Hand = new Cursor(), Arrow = new Cursor(), SizeAll = new Cursor(), IBeam = new Cursor(), SizeWE = new Cursor(), SizeNS = new Cursor(), No = new Cursor(), Cross = new Cursor(); }
    public class BindingContext
    {
        public BindingManagerBase this[object dataSource] => new BindingManagerBase();
        public BindingManagerBase this[object dataSource, string dataMember] => new BindingManagerBase();
    }
    public class BindingManagerBase { public void CancelCurrentEdit() { } public void EndCurrentEdit() { } public int Position { get; set; } public int Count => 0; }
    public class ControlBindingsCollection : List<object> { public void Clear(bool ignored) => Clear(); }

    public class ScrollableControl : Control
    {
        public bool AutoScroll { get; set; }
        public Size AutoScrollMinSize { get; set; }
        public Point AutoScrollPosition { get; set; }
    }
    public class ContainerControl : ScrollableControl
    {
        public SizeF AutoScaleDimensions { get; set; }
        public AutoScaleMode AutoScaleMode { get; set; }
        public Control ActiveControl { get; set; }
        public bool Validate() => true;
        public bool ValidateChildren() => true;
    }
    public class UserControl : ContainerControl
    {
        bool _loaded;
        public BorderStyle BorderStyle { get; set; }
        public event EventHandler Load;
        protected virtual void OnLoad(EventArgs e) => Load?.Invoke(this, e);
        /// <summary>WinForms raises Load once, when the control is first created for display, after its children
        /// got their windows; the renderer calls this at that point.</summary>
        public void RaiseLoad() { if (_loaded) return; _loaded = true; OnLoad(EventArgs.Empty); }
    }
    public class Panel : ScrollableControl { public BorderStyle BorderStyle { get; set; } }
    public class FlowLayoutPanel : Panel { }
    /// <summary>WinForms Splitter: a docked bar that resizes the control docked before it; MinSize and MinExtra
    /// bound the sizes of that control and of the remaining space.</summary>
    public class Splitter : Control
    {
        public int MinExtra { get; set; } = 25;
        public int MinSize { get; set; } = 25;
        public int SplitPosition { get; set; } = -1;
        public BorderStyle BorderStyle { get; set; }
        public event SplitterEventHandler SplitterMoving, SplitterMoved;
        public void RaiseSplitterMoved(int x, int y, int splitX, int splitY)
        {
            SplitterMoving?.Invoke(this, new SplitterEventArgs(x, y, splitX, splitY));
            SplitterMoved?.Invoke(this, new SplitterEventArgs(x, y, splitX, splitY));
        }
    }
    /// <summary>WinForms SplitContainer: two panels side by side (Vertical) or stacked (Horizontal) around a
    /// splitter at SplitterDistance; a fixed panel keeps its size when the container resizes, otherwise the
    /// splitter keeps its proportion; a collapsed panel hides and the other fills the container.</summary>
    public class SplitContainer : ContainerControl, ISupportInitialize
    {
        int _distance = 50, _width = 4, _panel1Min = 25, _panel2Min = 25, _init;
        bool _p1Collapsed, _p2Collapsed;
        Orientation _orientation = Orientation.Vertical;
        Size _lastSize;
        public SplitterPanel Panel1 { get; } = new SplitterPanel();
        public SplitterPanel Panel2 { get; } = new SplitterPanel();
        public event SplitterEventHandler SplitterMoved;
        public event SplitterCancelEventHandler SplitterMoving;
        public SplitContainer() { Controls.Add(Panel1); Controls.Add(Panel2); }
        public Orientation Orientation { get => _orientation; set { _orientation = value; LayoutPanels(); } }
        public FixedPanel FixedPanel { get; set; }
        public bool IsSplitterFixed { get; set; }
        public int SplitterIncrement { get; set; } = 1;
        public int SplitterWidth { get => _width; set { _width = Math.Max(1, value); LayoutPanels(); } }
        public int Panel1MinSize { get => _panel1Min; set { _panel1Min = value; LayoutPanels(); } }
        public int Panel2MinSize { get => _panel2Min; set { _panel2Min = value; LayoutPanels(); } }
        public bool Panel1Collapsed { get => _p1Collapsed; set { if (_p1Collapsed == value) return; _p1Collapsed = value; Panel1.Visible = !value; LayoutPanels(); } }
        public bool Panel2Collapsed { get => _p2Collapsed; set { if (_p2Collapsed == value) return; _p2Collapsed = value; Panel2.Visible = !value; LayoutPanels(); } }
        int Extent => _orientation == Orientation.Vertical ? Width : Height;
        public Rectangle SplitterRectangle => _orientation == Orientation.Vertical ? new Rectangle(_distance, 0, _width, Height) : new Rectangle(0, _distance, Width, _width);
        public int SplitterDistance
        {
            get => _distance;
            set
            {
                if (_init == 0 && Extent > 0)
                {
                    if (value < _panel1Min || value + _width > Extent - _panel2Min)
                        throw new InvalidOperationException("SplitterDistance must be between Panel1MinSize and Width - Panel2MinSize.");
                }
                if (_distance == value) return;
                _distance = value;
                LayoutPanels();
                SplitterMoved?.Invoke(this, new SplitterEventArgs(0, 0, _distance, 0));
            }
        }
        public void BeginInit() => _init++;
        public void EndInit() { if (_init > 0) _init--; LayoutPanels(); }
        protected override void OnLayout(LayoutEventArgs levent)
        {
            Size size = Size;
            if (_lastSize != Size.Empty && size != _lastSize && _init == 0)
            {
                int oldExtent = _orientation == Orientation.Vertical ? _lastSize.Width : _lastSize.Height;
                int newExtent = Extent;
                if (FixedPanel == FixedPanel.Panel2) _distance += newExtent - oldExtent;
                else if (FixedPanel == FixedPanel.None && oldExtent > 0) _distance = (int)Math.Round(_distance * (double)newExtent / oldExtent);
                _distance = Math.Max(_panel1Min, Math.Min(_distance, newExtent - _panel2Min - _width));
            }
            _lastSize = size;
            LayoutPanels();
            base.OnLayout(levent);
        }
        void LayoutPanels()
        {
            int w = Width, h = Height;
            if (_p1Collapsed) { Panel2.Bounds = new Rectangle(0, 0, w, h); Notify("Layout"); return; }
            if (_p2Collapsed) { Panel1.Bounds = new Rectangle(0, 0, w, h); Notify("Layout"); return; }
            if (_orientation == Orientation.Vertical)
            {
                Panel1.Bounds = new Rectangle(0, 0, Math.Max(0, _distance), h);
                Panel2.Bounds = new Rectangle(_distance + _width, 0, Math.Max(0, w - _distance - _width), h);
            }
            else
            {
                Panel1.Bounds = new Rectangle(0, 0, w, Math.Max(0, _distance));
                Panel2.Bounds = new Rectangle(0, _distance + _width, w, Math.Max(0, h - _distance - _width));
            }
            Notify("Layout");
        }
        /// <summary>The user dragged the splitter to distance (renderer input; clamped to the minimum sizes).</summary>
        public void UserMoveSplitter(int distance)
        {
            if (IsSplitterFixed) return;
            int clamped = Math.Max(_panel1Min, Math.Min(distance, Extent - _panel2Min - _width));
            var moving = new SplitterCancelEventArgs(0, 0, clamped, 0);
            SplitterMoving?.Invoke(this, moving);
            if (moving.Cancel) return;
            SplitterDistance = clamped;
        }
    }
    public enum Orientation { Horizontal, Vertical }
    public enum FixedPanel { None, Panel1, Panel2 }
    public sealed class SplitterPanel : Panel { }
    public class SplitterEventArgs : EventArgs
    {
        public int X { get; } public int Y { get; } public int SplitX { get; set; } public int SplitY { get; set; }
        public SplitterEventArgs(int x, int y, int splitX, int splitY) { X = x; Y = y; SplitX = splitX; SplitY = splitY; }
    }
    public class SplitterCancelEventArgs : CancelEventArgs
    {
        public int MouseCursorX { get; } public int MouseCursorY { get; } public int SplitX { get; set; } public int SplitY { get; set; }
        public SplitterCancelEventArgs(int mouseCursorX, int mouseCursorY, int splitX, int splitY) { MouseCursorX = mouseCursorX; MouseCursorY = mouseCursorY; SplitX = splitX; SplitY = splitY; }
    }
    public delegate void SplitterEventHandler(object sender, SplitterEventArgs e);
    public delegate void SplitterCancelEventHandler(object sender, SplitterCancelEventArgs e);

    public class GroupBox : Control { public FlatStyle FlatStyle { get; set; } }
    public class Label : Control
    {
        public ContentAlignment TextAlign { get; set; } = ContentAlignment.TopLeft;
        public BorderStyle BorderStyle { get; set; }
        public ImageResource Image { get; set; }
        public ContentAlignment ImageAlign { get; set; } = ContentAlignment.MiddleCenter;
        public bool UseMnemonic { get; set; } = true;
    }
    /// <summary>WinForms LinkLabel is an IButtonControl: as a form's Accept/Cancel button it raises LinkClicked.</summary>
    public class LinkLabel : Label, IButtonControl
    {
        public event LinkLabelLinkClickedEventHandler LinkClicked;
        public Color LinkColor { get; set; } = Color.FromArgb(0, 0, 255);
        public Color ActiveLinkColor { get; set; } = Color.Red;
        public Color VisitedLinkColor { get; set; } = Color.FromArgb(128, 0, 128);
        public bool LinkVisited { get; set; }
        public DialogResult DialogResult { get; set; }
        public void NotifyDefault(bool value) { }
        public void PerformClick() => RaiseLinkClicked();
        public void RaiseLinkClicked() => LinkClicked?.Invoke(this, new LinkLabelLinkClickedEventArgs());
    }
    public class LinkLabelLinkClickedEventArgs : EventArgs { }
    public delegate void LinkLabelLinkClickedEventHandler(object sender, LinkLabelLinkClickedEventArgs e);

    public abstract class ButtonBase : Control
    {
        public FlatStyle FlatStyle { get; set; }
        public ImageResource Image { get; set; }
        public ContentAlignment ImageAlign { get; set; } = ContentAlignment.MiddleCenter;
        public ContentAlignment TextAlign { get; set; } = ContentAlignment.MiddleCenter;
        public TextImageRelation TextImageRelation { get; set; }
        public bool UseVisualStyleBackColor { get; set; }
        public bool UseMnemonic { get; set; } = true;
        public FlatButtonAppearance FlatAppearance { get; } = new FlatButtonAppearance();
        public ImageList ImageList { get; set; }
        public int ImageIndex { get; set; } = -1;
        public string ImageKey { get; set; } = "";
    }
    public enum TextImageRelation { Overlay = 0, ImageAboveText = 1, TextAboveImage = 2, ImageBeforeText = 4, TextBeforeImage = 8 }
    public class FlatButtonAppearance { public int BorderSize { get; set; } = 1; public Color BorderColor { get; set; } public Color MouseOverBackColor { get; set; } public Color MouseDownBackColor { get; set; } public Color CheckedBackColor { get; set; } }
    public class Button : ButtonBase, IButtonControl
    {
        public DialogResult DialogResult { get; set; }
        public void PerformClick() => RaiseClick();
        public void NotifyDefault(bool value) { }
        protected override void OnClick(EventArgs e)
        {
            if (DialogResult != DialogResult.None && FindForm() is Form form) form.DialogResult = DialogResult;
            base.OnClick(e);
        }
    }
    public interface IButtonControl { DialogResult DialogResult { get; set; } void NotifyDefault(bool value); void PerformClick(); }
    public class CheckBox : ButtonBase
    {
        bool _checked;
        public Appearance Appearance { get; set; }
        public bool AutoCheck { get; set; } = true;
        public bool ThreeState { get; set; }
        public ContentAlignment CheckAlign { get; set; } = ContentAlignment.MiddleLeft;
        public bool Checked { get => _checked; set { if (_checked == value) return; _checked = value; Notify(nameof(Checked)); CheckedChanged?.Invoke(this, EventArgs.Empty); CheckStateChanged?.Invoke(this, EventArgs.Empty); } }
        public CheckState CheckState { get => _checked ? CheckState.Checked : CheckState.Unchecked; set => Checked = value != CheckState.Unchecked; }
        public event EventHandler CheckedChanged, CheckStateChanged;
        protected override void OnClick(EventArgs e) { if (AutoCheck) Checked = !Checked; base.OnClick(e); }
    }
    public class RadioButton : ButtonBase
    {
        bool _checked;
        public Appearance Appearance { get; set; }
        public bool AutoCheck { get; set; } = true;
        public ContentAlignment CheckAlign { get; set; } = ContentAlignment.MiddleLeft;
        public bool Checked
        {
            get => _checked;
            set
            {
                if (_checked == value) return;
                _checked = value;
                if (value && AutoCheck && Parent != null)
                    foreach (Control c in Parent.Controls) if (c is RadioButton r && r != this && r.AutoCheck) r.Checked = false;
                Notify(nameof(Checked));
                CheckedChanged?.Invoke(this, EventArgs.Empty);
            }
        }
        public event EventHandler CheckedChanged;
        protected override void OnClick(EventArgs e) { if (AutoCheck) Checked = true; base.OnClick(e); }
    }

    public class TextBoxBase : Control
    {
        public bool ReadOnly { get; set; }
        public bool Multiline { get; set; }
        public bool WordWrap { get; set; } = true;
        public BorderStyle BorderStyle { get; set; } = BorderStyle.Fixed3D;
        public int MaxLength { get; set; } = 32767;
        public int SelectionStart { get; set; }
        public int SelectionLength { get; set; }
        public bool HideSelection { get; set; } = true;
        public bool ShortcutsEnabled { get; set; } = true;
        public bool Modified { get; set; }
        public string[] Lines { get => Text.Split('\n'); set => Text = string.Join(Environment.NewLine, value ?? new string[0]); }
        public void SelectAll() { SelectionStart = 0; SelectionLength = Text.Length; Notify("Selection"); }
        public void Select(int start, int length) { SelectionStart = start; SelectionLength = length; Notify("Selection"); }
        public void AppendText(string text) => Text += text;
        public void Clear() => Text = "";
        public void ScrollToCaret() { }
        public void DeselectAll() => SelectionLength = 0;
        public void Copy() { }
        public void Paste() { }
        public void Cut() { }
        public void Undo() { }
    }
    public class TextBox : TextBoxBase
    {
        public HorizontalAlignment TextAlign { get; set; }
        public ScrollBars ScrollBars { get; set; }
        public char PasswordChar { get; set; }
        public bool AcceptsReturn { get; set; }
        public bool AcceptsTab { get; set; }
        public CharacterCasing CharacterCasing { get; set; }
        // Renderer input: committed user text.
        public void SetUserText(string text) { Text = text; Modified = true; }
    }
    public enum CharacterCasing { Normal, Upper, Lower }
    public class RichTextBox : TextBoxBase
    {
        public string Rtf { get; set; }
        public RichTextBoxScrollBars ScrollBars { get; set; }
        public event EventHandler VScroll;
        protected virtual void OnVScroll(EventArgs e) => VScroll?.Invoke(this, e);
    }
    public enum RichTextBoxScrollBars { None, Horizontal, Vertical, Both, ForcedHorizontal, ForcedVertical, ForcedBoth }

    public class ListControl : Control
    {
        public string DisplayMember { get; set; } = "";
        public string ValueMember { get; set; } = "";
        public object DataSource { get; set; }
    }
    public class ComboBox : ListControl
    {
        int _selectedIndex = -1;
        public ObjectCollection Items { get; }
        public ComboBox() { Items = new ObjectCollection(this); }
        public ComboBoxStyle DropDownStyle { get; set; } = ComboBoxStyle.DropDown;
        public int DropDownWidth { get; set; }
        public int MaxDropDownItems { get; set; } = 8;
        public bool FormattingEnabled { get; set; }
        public bool Sorted { get; set; }
        public int SelectedIndex
        {
            get => _selectedIndex;
            set
            {
                if (value < -1 || value >= Items.Count) throw new ArgumentOutOfRangeException(nameof(value));
                if (_selectedIndex == value) return;
                _selectedIndex = value;
                base.Text = value >= 0 ? Convert.ToString(Items[value], Globalization.CultureInfo.CurrentCulture) : "";
                Notify(nameof(SelectedIndex));
                SelectedIndexChanged?.Invoke(this, EventArgs.Empty);
                SelectedValueChanged?.Invoke(this, EventArgs.Empty);
            }
        }
        public object SelectedItem { get => _selectedIndex >= 0 ? Items[_selectedIndex] : null; set => SelectedIndex = value == null ? -1 : Items.IndexOf(value); }
        public override string Text { get => base.Text; set { int index = Items.IndexOf(value); if (index >= 0) SelectedIndex = index; else base.Text = value; } }
        public event EventHandler SelectedIndexChanged, SelectedValueChanged, SelectionChangeCommitted, DropDown, DropDownClosed;
        public void RaiseSelectionChangeCommitted(int index) { SelectedIndex = index; SelectionChangeCommitted?.Invoke(this, EventArgs.Empty); }
        public class ObjectCollection : IList
        {
            readonly ComboBox owner;
            readonly List<object> items = new List<object>();
            public ObjectCollection(ComboBox owner) { this.owner = owner; }
            public int Count => items.Count;
            public object this[int index] { get => items[index]; set { items[index] = value; owner.Notify("Items"); } }
            public int Add(object item) { items.Add(item); owner.Notify("Items"); return items.Count - 1; }
            public void AddRange(object[] values) { items.AddRange(values); owner.Notify("Items"); }
            public void Clear() { items.Clear(); owner._selectedIndex = -1; owner.Notify("Items"); }
            public void Insert(int index, object item) { items.Insert(index, item); owner.Notify("Items"); }
            public void Remove(object item) { items.Remove(item); owner.Notify("Items"); }
            public void RemoveAt(int index) { items.RemoveAt(index); owner.Notify("Items"); }
            public bool Contains(object item) => items.Contains(item);
            public int IndexOf(object item) => items.IndexOf(item);
            public IEnumerator GetEnumerator() => items.GetEnumerator();
            bool IList.IsFixedSize => false;
            bool IList.IsReadOnly => false;
            void ICollection.CopyTo(Array array, int index) => ((ICollection)items).CopyTo(array, index);
            bool ICollection.IsSynchronized => false;
            object ICollection.SyncRoot => this;
        }
    }
    public enum ComboBoxStyle { Simple, DropDown, DropDownList }
    /// <summary>WinForms NumericUpDown: Minimum/Maximum keep Value in range; a Value outside it throws except during
    /// designer initialization (BeginInit/EndInit), whose end constrains it. User input is constrained.</summary>
    public class NumericUpDown : Control, ISupportInitialize
    {
        decimal _value, _min, _max = 100;
        bool _initializing;
        public decimal Minimum { get => _min; set { _min = value; if (_min > _max) _max = _min; if (!_initializing) Value = Constrain(_value); } }
        public decimal Maximum { get => _max; set { _max = value; if (_min > _max) _min = _max; if (!_initializing) Value = Constrain(_value); } }
        public decimal Increment { get; set; } = 1;
        public int DecimalPlaces { get; set; }
        public bool ThousandsSeparator { get; set; }
        public bool Hexadecimal { get; set; }
        public bool ReadOnly { get; set; }
        public bool InterceptArrowKeys { get; set; } = true;
        public HorizontalAlignment TextAlign { get; set; }
        public LeftRightAlignment UpDownAlign { get; set; } = LeftRightAlignment.Right;
        public BorderStyle BorderStyle { get; set; } = BorderStyle.Fixed3D;
        public decimal Value
        {
            get => _value;
            set
            {
                if (!_initializing && (value < _min || value > _max))
                    throw new ArgumentOutOfRangeException(nameof(Value), $"Value of '{value}' is not valid for 'Value'. 'Value' should be between 'Minimum' and 'Maximum'.");
                if (_value == value) return;
                _value = value;
                base.Text = _value.ToString((ThousandsSeparator ? "N" : "F") + DecimalPlaces, System.Globalization.CultureInfo.CurrentCulture);
                Notify(nameof(Value));
                if (!_initializing) OnValueChanged(EventArgs.Empty);
            }
        }
        decimal Constrain(decimal value) => Math.Max(_min, Math.Min(_max, value));
        public event EventHandler ValueChanged;
        protected virtual void OnValueChanged(EventArgs e) => ValueChanged?.Invoke(this, e);
        public void BeginInit() => _initializing = true;
        public void EndInit() { _initializing = false; Value = Constrain(_value); }
        public void UpButton() => Value = Constrain(_value + Increment);
        public void DownButton() => Value = Constrain(_value - Increment);
        /// <summary>User input (typed or spun): constrained to the range as WinForms does.</summary>
        public void UserSetValue(decimal value) { if (Enabled && !ReadOnly) Value = Constrain(value); }
    }
    public enum LeftRightAlignment { Left, Right }
    /// <summary>WinForms TrackBar: Value in [Minimum, Maximum] (code outside it throws); user input raises Scroll, then
    /// ValueChanged.</summary>
    public class TrackBar : Control, ISupportInitialize
    {
        int _value, _min, _max = 10;
        bool _initializing;
        public int Minimum { get => _min; set { _min = value; if (_min > _max) _max = _min; if (_value < _min) Value = _min; } }
        public int Maximum { get => _max; set { _max = value; if (_min > _max) _min = _max; if (_value > _max) Value = _max; } }
        public int SmallChange { get; set; } = 1;
        public int LargeChange { get; set; } = 5;
        public int TickFrequency { get; set; } = 1;
        public TickStyle TickStyle { get; set; } = TickStyle.BottomRight;
        public Orientation Orientation { get; set; }
        public int Value
        {
            get => _value;
            set
            {
                if (!_initializing && (value < _min || value > _max))
                    throw new ArgumentOutOfRangeException(nameof(Value), $"Value of '{value}' is not valid for 'Value'. 'Value' should be between 'Minimum' and 'Maximum'.");
                if (_value == value) return;
                _value = value;
                Notify(nameof(Value));
                OnValueChanged(EventArgs.Empty);
            }
        }
        public event EventHandler ValueChanged, Scroll;
        protected virtual void OnValueChanged(EventArgs e) => ValueChanged?.Invoke(this, e);
        protected virtual void OnScroll(EventArgs e) => Scroll?.Invoke(this, e);
        public void BeginInit() => _initializing = true;
        public void EndInit() { _initializing = false; Value = Math.Max(_min, Math.Min(_max, _value)); }
        public void UserScroll(int value)
        {
            value = Math.Max(_min, Math.Min(_max, value));
            if (value == _value) return;
            OnScroll(EventArgs.Empty);
            Value = value;
        }
    }
    public enum TickStyle { None, TopLeft, BottomRight, Both }
    public class ProgressBar : Control
    {
        int _value;
        public int Minimum { get; set; }
        public int Maximum { get; set; } = 100;
        public int Value { get => _value; set { if (value < Minimum || value > Maximum) throw new ArgumentOutOfRangeException(nameof(Value)); if (_value == value) return; _value = value; Notify(nameof(Value)); } }
        public int Step { get; set; } = 10;
        public int MarqueeAnimationSpeed { get; set; } = 100;
        public ProgressBarStyle Style { get; set; }
        public void PerformStep() => Increment(Step);
        public void Increment(int value) => Value = Math.Max(Minimum, Math.Min(Maximum, _value + value));
    }
    public enum ProgressBarStyle { Blocks, Continuous, Marquee }
    public class PictureBox : Control { public ImageResource Image { get; set; } public PictureBoxSizeMode SizeMode { get; set; } public BorderStyle BorderStyle { get; set; } }
    public enum PictureBoxSizeMode { Normal, StretchImage, AutoSize, CenterImage, Zoom }

    public class ToolTip : Component
    {
        readonly Dictionary<Control, string> tips = new Dictionary<Control, string>();
        public ToolTip() { }
        public ToolTip(IContainer container) { container?.Add(this); }
        public int AutoPopDelay { get; set; } = 5000;
        public int InitialDelay { get; set; } = 500;
        public int ReshowDelay { get; set; } = 100;
        public bool ShowAlways { get; set; }
        public bool IsBalloon { get; set; }
        public void SetToolTip(Control control, string caption) { tips[control] = caption; ControlNotifications.Raise(control, "ToolTip"); }
        public string GetToolTip(Control control) => tips.TryGetValue(control, out string text) ? text : "";
        public void RemoveAll() => tips.Clear();
    }

    public class ImageList : Component
    {
        public ImageList() { }
        public ImageList(IContainer container) { container?.Add(this); }
        public ImageCollection Images { get; } = new ImageCollection();
        public Size ImageSize { get; set; } = new Size(16, 16);
        public ColorDepth ColorDepth { get; set; }
        public Color TransparentColor { get; set; }
        public ImageListStreamer ImageStream { get; set; }
        public class ImageCollection : List<ImageResource>
        {
            readonly Dictionary<string, ImageResource> keyed = new Dictionary<string, ImageResource>();
            public void Add(string key, ImageResource image) { keyed[key] = image; Add(image); }
            public void SetKeyName(int index, string name) { }
            public ImageResource this[string key] => keyed.TryGetValue(key, out ImageResource image) ? image : null;
            public bool ContainsKey(string key) => keyed.ContainsKey(key);
        }
    }
    public enum ColorDepth { Depth4Bit = 4, Depth8Bit = 8, Depth16Bit = 16, Depth24Bit = 24, Depth32Bit = 32 }
    public sealed class ImageListStreamer { }

    public class Screen
    {
        public Rectangle Bounds { get; private set; }
        public Rectangle WorkingArea { get; private set; }
        public bool Primary { get; private set; }
        static Rectangle[] screens = { new Rectangle(0, 0, 1920, 1080) };
        /// <summary>The renderer reports the desktop geometry.</summary>
        public static void SetScreens(Rectangle[] bounds) => screens = bounds != null && bounds.Length > 0 ? bounds : screens;
        public static Screen[] AllScreens => screens.Select((b, i) => new Screen { Bounds = b, WorkingArea = b, Primary = i == 0 }).ToArray();
        public static Screen PrimaryScreen => AllScreens[0];
        public static Screen FromControl(Control control) => PrimaryScreen;
        public static Screen FromPoint(Point point) => AllScreens.FirstOrDefault(s => s.Bounds.Contains(point)) ?? PrimaryScreen;
    }
}
namespace System.Windows.Forms
{
    /// <summary>ActiveX host; named by a using static directive of the original vtkControl.cs, never created.</summary>
    public abstract class AxHost : Control { protected AxHost(string clsid) { } }
}
namespace System.Windows.Forms.VisualStyles
{
    public static class VisualStyleElement
    {
        public static class TaskbarClock { }
        // Named by using static directives of the original ModelTree.cs; nothing of it is used
        public static class TextBox { }
        // Named by using static directives of the original vtkControl.cs; nothing of them is used
        public static class ProgressBar { }
        public static class TreeView { }
        public static class Window { }
    }
}
namespace System.Management.Instrumentation
{
    /// <summary>Keeps the namespace of a using directive of the original vtkControl.cs (nothing of it is used).</summary>
    public static class NamespacePlaceholder { }
}
namespace AutocompleteMenuNS
{
    // Stand-in for the original autocomplete popup (UserControls/AutocompleteMenu, a Win32 popup list): it keeps
    // the item list, the attached edit control and the Enabled rule the original code sets; the renderer completes.
    public class AutocompleteItem
    {
        public AutocompleteItem() { }
        public AutocompleteItem(string text) { Text = text; }
        public string Text { get; set; }
        public string MenuText { get; set; }
        public string ToolTipTitle { get; set; }
        public string ToolTipText { get; set; }
        public int ImageIndex { get; set; } = -1;
        public object Tag { get; set; }
        public override string ToString() => MenuText ?? Text;
    }
    /// <summary>Original (AutocompleteItems.cs): a snippet with '^' marking the caret position after insertion.</summary>
    public class SnippetAutocompleteItem : AutocompleteItem
    {
        public SnippetAutocompleteItem(string snippet) { Text = snippet.Replace("\r", ""); ToolTipTitle = "Code snippet:"; ToolTipText = Text; }
        public override string ToString() => MenuText ?? Text.Replace("\n", " ").Replace("^", "");
    }
    public class AutocompleteMenu : System.ComponentModel.Component
    {
        static readonly System.Collections.Generic.Dictionary<System.Windows.Forms.Control, AutocompleteMenu> attached =
            new System.Collections.Generic.Dictionary<System.Windows.Forms.Control, AutocompleteMenu>();
        public AutocompleteMenu() { }
        public bool AllowsTabKey { get; set; }
        public System.Windows.Forms.FontSpec Font { get; set; }
        public System.Windows.Forms.ImageList ImageList { get; set; }
        public string[] Items { get; set; } = new string[0];
        public System.Drawing.Size MaximumSize { get; set; }
        public int MinFragmentLength { get; set; } = 2;
        public string SearchPattern { get; set; } = @"[\w\.]";
        public object TargetControlWrapper { get; set; }
        public bool Enabled { get; set; } = true;
        public bool Visible { get; set; }
        public AutocompleteItem[] SourceItems { get; private set; } = new AutocompleteItem[0];
        public void SetAutocompleteItems(System.Collections.Generic.IEnumerable<AutocompleteItem> items) => SourceItems = System.Linq.Enumerable.ToArray(items);
        public void SetAutocompleteItems(System.Collections.Generic.IEnumerable<string> items) => SourceItems = System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(items, i => new AutocompleteItem(i)));
        public void SetAutocompleteMenu(System.Windows.Forms.Control control, AutocompleteMenu menu)
        {
            if (menu == null) attached.Remove(control); else attached[control] = menu;
        }
        public AutocompleteMenu GetAutocompleteMenu(System.Windows.Forms.Control control) => attached.TryGetValue(control, out var menu) ? menu : null;
        /// <summary>Renderer: the menu attached to an edit control, when enabled (null otherwise).</summary>
        public static AutocompleteMenu ActiveFor(System.Windows.Forms.Control control) => control != null && attached.TryGetValue(control, out var menu) && menu.Enabled ? menu : null;
    }
}
