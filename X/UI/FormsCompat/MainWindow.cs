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
