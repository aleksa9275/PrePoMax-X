// Controls drawn from the model's own layout (ports of TreeWidget and CodeEditor in X/UI/original_controls.py): the
// original CodersLabTreeView and FastColoredTextBox keep their behaviour in the model (rows, node bounds, lines, style
// runs, selection, caret); these draw them and pass the mouse and the keys back as WinForms would.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Primitives;
using Avalonia.Input;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Threading;
using WinForms = System.Windows.Forms;

namespace PrePoMaxX.FrontEnd
{
    /// <summary>A canvas that draws itself below its child controls (Panel.Render is sealed): the drawing is a child
    /// that fills the canvas.</summary>
    internal abstract class DrawnCanvas : Canvas
    {
        sealed class Drawing : Control
        {
            readonly DrawnCanvas _owner;
            public Drawing(DrawnCanvas owner) { _owner = owner; IsHitTestVisible = false; }
            public override void Render(DrawingContext context) => _owner.Draw(context);
        }
        readonly Drawing _drawing;
        protected DrawnCanvas() { _drawing = new Drawing(this); Children.Add(_drawing); }
        protected abstract void Draw(DrawingContext context);
        public new void InvalidateVisual() => _drawing.InvalidateVisual();
        protected override Size ArrangeOverride(Size finalSize)
        {
            Size size = base.ArrangeOverride(finalSize);
            _drawing.Arrange(new Rect(finalSize));
            return size;
        }
    }

    /// <summary>TreeView drawn from the model rows: row height, indent, +/- boxes, images and label rectangles of the
    /// model, with the node colours the original CodersLabTreeView sets for its own selection.</summary>
    internal sealed class TreeViewView : Grid, IMirror
    {
        readonly WinForms.TreeView _tree;
        readonly Surface _surface;
        readonly ScrollBar _bar = new ScrollBar { Orientation = Orientation.Vertical, AllowAutoHide = false, Width = 14 };
        TextBox _editor;
        bool _syncing;

        public TreeViewView(WinForms.TreeView tree)
        {
            _tree = tree;
            _surface = new Surface(this);
            ColumnDefinitions = new ColumnDefinitions("*,Auto");
            Children.Add(_surface);
            Grid.SetColumn(_bar, 1);
            Children.Add(_bar);
            Focusable = false;
            _bar.Scroll += (s, e) => { if (!_syncing) { int top = (int)Math.Round(e.NewValue); Ui.Input(() => _tree.UserScroll(top)); } };
            Update();
        }

        public void Update()
        {
            int rows = _tree.RenderRows().Length;
            int page = Math.Max(1, (_tree.ClientSize.Height - 4) / Math.Max(1, _tree.ItemHeight));
            _syncing = true;
            try
            {
                _bar.Maximum = Math.Max(0, rows - page);
                _bar.ViewportSize = page;
                _bar.LargeChange = page;
                _bar.SmallChange = 1;
                _bar.Value = _tree.TopRow;
                _bar.IsVisible = rows > page;
            }
            finally { _syncing = false; }
            SyncEditor();
            _surface.InvalidateVisual();
        }
        public void Refresh(string property) => Update();

        void SyncEditor()
        {
            WinForms.TreeNode node = _tree.EditingNode;
            if (node == null)
            {
                if (_editor != null) { _surface.Editor = null; _editor = null; }
                return;
            }
            if (_editor == null)
            {
                _editor = new TextBox { Text = node.Text, Padding = new Thickness(1, 0), BorderThickness = new Thickness(1) };
                _editor.KeyDown += (s, e) =>
                {
                    if (e.Key == Key.Enter) { string text = _editor.Text; Ui.Input(() => _tree.UserEndEdit(false, text)); e.Handled = true; }
                    else if (e.Key == Key.Escape) { Ui.Input(() => _tree.UserEndEdit(true, null)); e.Handled = true; }
                };
                _editor.LostFocus += (s, e) => { if (_editor != null) { string text = _editor.Text; Ui.Input(() => _tree.UserEndEdit(false, text)); } };
                _surface.Editor = _editor;
                Dispatcher.UIThread.Post(() => { _editor?.Focus(); _editor?.SelectAll(); });
            }
            var b = node.Bounds;
            _surface.EditorBounds = new Rect(b.X, b.Y, Math.Max(b.Width + 40, 80), b.Height);
        }

        internal sealed class Surface : DrawnCanvas
        {
            readonly TreeViewView _owner;
            WinForms.MouseButtons _pressed;
            DateTime _lastRelease;
            Point _lastPosition;
            bool _double;
            TextBox _editor;
            public Surface(TreeViewView owner) { _owner = owner; Focusable = true; ClipToBounds = true; Background = Brushes.White; }
            WinForms.TreeView Tree => _owner._tree;
            internal TextBox Editor
            {
                set
                {
                    if (_editor != null) Children.Remove(_editor);
                    _editor = value;
                    if (value != null) Children.Add(value);
                }
            }
            internal Rect EditorBounds
            {
                set { if (_editor == null) return; SetLeft(_editor, value.X); SetTop(_editor, value.Y); _editor.Width = value.Width; _editor.Height = value.Height; }
            }

            IImage NodeImage(WinForms.TreeNode node, bool selected)
            {
                WinForms.ImageList images = Tree.ImageList;
                if (images == null) return null;
                string key = selected && !string.IsNullOrEmpty(node.SelectedImageKey) ? node.SelectedImageKey : !string.IsNullOrEmpty(node.ImageKey) ? node.ImageKey : Tree.ImageKey ?? "";
                int index = selected && node.SelectedImageIndex >= 0 ? node.SelectedImageIndex : node.ImageIndex;
                if (index < 0) index = Tree.ImageIndex;
                System.Drawing.Image image = null;
                if (!string.IsNullOrEmpty(key) && images.Images.ContainsKey(key)) image = images.Images[key];
                else if (index >= 0 && index < images.Images.Count) image = images.Images[index];
                else if (images.ImageStream != null) return Ui.Named(key);
                return Ui.Bitmap(image);
            }

            protected override void Draw(DrawingContext context)
            {
                var tree = Tree;
                context.FillRectangle(tree.BackColor.A > 0 && tree.BackColor != System.Drawing.SystemColors.Control ? Ui.Brush(tree.BackColor) : Brushes.White, new Rect(Bounds.Size));
                var rows = tree.RenderRows();
                int top = tree.TopRow, height = tree.ItemHeight, indent = tree.Indent;
                var selected = tree.SelectedNode;
                var gray = new Pen(new SolidColorBrush(Color.FromRgb(150, 150, 150)), 1);
                var black = new Pen(Brushes.Black, 1);
                for (int i = top; i < rows.Length; i++)
                {
                    var node = rows[i];
                    int y = 2 + (i - top) * height;
                    if (y > Bounds.Height) break;
                    int x = tree.NodeIndentX(node);
                    if (node.Nodes.Count > 0 && tree.ShowPlusMinus)
                    {
                        var box = new Rect(x - indent / 2 - 4 + 0.5, y + height / 2 - 4 + 0.5, 8, 8);
                        context.DrawRectangle(Brushes.White, gray, box);
                        context.DrawLine(black, new Point(box.Left + 2, box.Center.Y), new Point(box.Right - 2, box.Center.Y));
                        if (!node.IsExpanded) context.DrawLine(black, new Point(box.Center.X, box.Top + 2), new Point(box.Center.X, box.Bottom - 2));
                    }
                    IImage icon = NodeImage(node, node == selected);
                    if (icon != null)
                    {
                        var size = tree.ImageList.ImageSize;
                        context.DrawImage(icon, new Rect(x, y + (height - size.Height) / 2, size.Width, size.Height));
                    }
                    var b = node.Bounds;
                    IBrush back = node.BackColor.IsEmpty || node.BackColor.A == 0 ? null : Ui.Brush(node.BackColor);
                    IBrush fore = !node.ForeColor.IsEmpty && node.ForeColor.A > 0 ? Ui.Brush(node.ForeColor) :
                                  tree.ForeColor.A > 0 ? Ui.Brush(tree.ForeColor) : Brushes.Black;
                    if (node == selected && back == null && (IsFocused || !tree.HideSelection)) { back = Look.Highlight; fore = Brushes.White; }
                    if (back != null) context.FillRectangle(back, new Rect(b.X, b.Y, b.Width, b.Height));
                    var text = new FormattedText(node.Text ?? "", CultureInfo.CurrentCulture, FlowDirection.LeftToRight,
                                                 node.NodeFont != null && node.NodeFont.Bold ? new Typeface(FontFamily.Default, FontStyle.Normal, FontWeight.Bold) : Look.Typeface, Look.FontSize, fore);
                    context.DrawText(text, new Point(b.X + 3, b.Y + (b.Height - text.Height) / 2));
                }
            }

            (WinForms.MouseButtons, int, int) Args(PointerEventArgs e)
            {
                Point p = e.GetPosition(this);
                return (Keyboard.Button(e.GetCurrentPoint(this).Properties.PointerUpdateKind), (int)p.X, (int)p.Y);
            }

            protected override void OnPointerPressed(PointerPressedEventArgs e)
            {
                Keyboard.SetModifiers(e.KeyModifiers);
                Focus();
                var (button, x, y) = Args(e);
                _pressed = button;
                // Windows sends one WM_LBUTTONDBLCLK for the second press of a double click (no second down)
                _double = e.ClickCount >= 2;
                WinForms.Control.MouseButtons = button;
                Ui.Input(() => Tree.UserMouseDown(button, _double ? 2 : 1, x, y));
                InvalidateVisual();
                e.Handled = true;
            }

            protected override void OnPointerReleased(PointerReleasedEventArgs e)
            {
                Keyboard.SetModifiers(e.KeyModifiers);
                var (button, x, y) = Args(e);
                int clicks = _double ? 2 : 1;
                _double = false;
                WinForms.Control.MouseButtons = WinForms.MouseButtons.None;
                Ui.Input(() => Tree.UserMouseUp(button, clicks, x, y));
                InvalidateVisual();
                e.Handled = true;
            }

            protected override void OnPointerMoved(PointerEventArgs e)
            {
                Point p = e.GetPosition(this);
                Ui.Input(() => Tree.UserMouseMove((int)p.X, (int)p.Y));
            }

            protected override void OnPointerExited(PointerEventArgs e) => Ui.Input(Tree.RaiseMouseLeave);

            protected override void OnPointerWheelChanged(PointerWheelEventArgs e)
            {
                int top = Math.Max(0, Tree.TopRow - (int)Math.Round(e.Delta.Y * 3));
                Ui.Input(() => Tree.UserScroll(top));
                e.Handled = true;
            }

            protected override void OnKeyDown(KeyEventArgs e)
            {
                WinForms.Keys keys = Keyboard.Keys(e);
                if ((keys & WinForms.Keys.KeyCode) == WinForms.Keys.None) return;
                Keyboard.SetModifiers(e.KeyModifiers);
                Ui.Input(() => Tree.RaiseKeyDown(keys));
                e.Handled = e.Key != Key.Tab;
                InvalidateVisual();
            }

            protected override void OnGotFocus(Avalonia.Input.GotFocusEventArgs e) { base.OnGotFocus(e); InvalidateVisual(); }
            protected override void OnLostFocus(Avalonia.Interactivity.RoutedEventArgs e) { base.OnLostFocus(e); InvalidateVisual(); }
        }
    }

    /// <summary>FastColoredTextBox: the model's lines with their style runs, selection, caret, current line, line numbers
    /// and bookmarks; keys go to the model as WM_KEYDOWN/WM_CHAR and mouse positions as places. Also FrmMain's output
    /// window (OutputTextBox).</summary>
    internal sealed class CodeView : Grid, IMirror
    {
        readonly FastColoredTextBoxNS.FastColoredTextBox _code;
        readonly Surface _surface;
        readonly ScrollBar _vertical = new ScrollBar { Orientation = Orientation.Vertical, AllowAutoHide = false, Width = 14 };
        readonly ScrollBar _horizontal = new ScrollBar { Orientation = Orientation.Horizontal, AllowAutoHide = false, Height = 14 };
        bool _syncing;
        string _fontKey;
        Typeface _typeface;
        double _fontSize, _charWidth, _charHeight;

        public CodeView(FastColoredTextBoxNS.FastColoredTextBox code)
        {
            _code = code;
            _surface = new Surface(this);
            ColumnDefinitions = new ColumnDefinitions("*,Auto");
            RowDefinitions = new RowDefinitions("*,Auto");
            Children.Add(_surface);
            Grid.SetColumn(_vertical, 1); Children.Add(_vertical);
            Grid.SetRow(_horizontal, 1); Children.Add(_horizontal);
            _vertical.Scroll += (s, e) => Scrolled();
            _horizontal.Scroll += (s, e) => Scrolled();
            UpdateMetrics();
            Rebuild();
            Autocomplete.Install();
            Autocomplete.Editors[code] = this;
        }

        internal FastColoredTextBoxNS.FastColoredTextBox Code => _code;
        internal Visual SurfaceVisual => _surface;
        internal double CharHeight => _charHeight;

        public void Update() => Rebuild();
        public void Refresh(string property)
        {
            if (property == "ScrollPosition")
            {
                // A scroll position the model set (or the one reported here)
                if ((int)_vertical.Value != _code.VerticalScrollValue) { _vertical.Value = Math.Min(_vertical.Maximum, _code.VerticalScrollValue); _surface.InvalidateVisual(); }
                return;
            }
            Rebuild();
            if (property == "ScrollToCaret") ScrollToCaret(_code.ScrollTarget);
        }

        void UpdateMetrics()
        {
            var font = _code.Font;
            string key = font.Name + "/" + font.Size + "/" + _code.Zoom;
            if (key == _fontKey) return;
            _fontKey = key;
            _typeface = new Typeface(Look.Monospace);
            _fontSize = Math.Max(1, Math.Round(font.Size * 96 / 72 * (_code.Zoom > 0 ? _code.Zoom : 100) / 100.0));
            var probe = new FormattedText("WWWWWWWWWW", CultureInfo.InvariantCulture, FlowDirection.LeftToRight, _typeface, _fontSize, Brushes.Black);
            _charWidth = Math.Max(1, probe.WidthIncludingTrailingWhitespace / 10);
            _charHeight = Math.Max(1, Math.Ceiling(probe.Height));
        }

        double LineHeight => _charHeight + _code.LineInterval;

        double GutterWidth
        {
            get
            {
                if (!_code.ShowLineNumbers) return 0;
                int digits = Math.Max(_code.ReservedCountOfLineNumberChars, _code.LinesCount.ToString().Length);
                return digits * _charWidth + 12;
            }
        }

        void ReportGeometry()
        {
            // Only what changed: the model notifies each scroll position it is given
            int charWidth = (int)Math.Round(_charWidth), charHeight = (int)Math.Round(_charHeight), indent = (int)Math.Round(GutterWidth + 3);
            if (_code.CharWidth != charWidth) _code.CharWidth = charWidth;
            if (_code.CharHeight != charHeight) _code.CharHeight = charHeight;
            if (_code.LeftIndent != indent) _code.LeftIndent = indent;
            if (_code.VerticalScrollValue != (int)_vertical.Value) _code.VerticalScrollValue = (int)_vertical.Value;
            if (_code.HorizontalScrollValue != (int)_horizontal.Value) _code.HorizontalScrollValue = (int)_horizontal.Value;
        }

        void Rebuild()
        {
            UpdateMetrics();
            int lines = _code.LinesCount;
            double viewHeight = Math.Max(0, (Bounds.Height > 0 ? Bounds.Height : _code.ClientSize.Height) - 14);
            double viewWidth = Math.Max(0, (Bounds.Width > 0 ? Bounds.Width : _code.ClientSize.Width) - 14);
            // A read-only view (the output window) at its end stays there as lines are added
            bool follow = _code.ReadOnly && _vertical.Value >= _vertical.Maximum - 1;
            _syncing = true;
            try
            {
                _vertical.Maximum = Math.Max(0, lines * LineHeight - viewHeight + LineHeight);
                if (follow) _vertical.Value = _vertical.Maximum;
                _vertical.SmallChange = LineHeight;
                _vertical.LargeChange = Math.Max(LineHeight, viewHeight);
                _vertical.ViewportSize = Math.Max(LineHeight, viewHeight);
                int longest = lines < 20000 ? Enumerable.Range(0, lines).Select(i => _code.GetLineText(i).Length).DefaultIfEmpty(0).Max() : 400;
                _horizontal.Maximum = Math.Max(0, GutterWidth + longest * _charWidth + 40 - viewWidth);
                _horizontal.ViewportSize = Math.Max(1, viewWidth);
                _horizontal.LargeChange = Math.Max(1, viewWidth);
                _horizontal.IsVisible = _horizontal.Maximum > 0;
            }
            finally { _syncing = false; }
            ReportGeometry();
            _surface.InvalidateVisual();
        }

        internal void ScrollToCaret() => ScrollToCaret(_code.Selection.Start);
        void ScrollToCaret(FastColoredTextBoxNS.Place caret)
        {
            UpdateMetrics();
            double top = caret.iLine * LineHeight;
            double viewHeight = Math.Max(0, Bounds.Height - (_horizontal.IsVisible ? 14 : 0));
            if (top < _vertical.Value) _vertical.Value = top;
            else if (top + LineHeight > _vertical.Value + viewHeight) _vertical.Value = Math.Min(_vertical.Maximum, top + LineHeight - viewHeight);
            double x = GutterWidth + caret.iChar * _charWidth;
            double viewWidth = Math.Max(0, Bounds.Width - 14);
            if (x < _horizontal.Value + GutterWidth) _horizontal.Value = Math.Max(0, x - GutterWidth - 20);
            else if (x > _horizontal.Value + viewWidth - 10) _horizontal.Value = Math.Min(_horizontal.Maximum, x - viewWidth + 40);
            ReportGeometry();
            _surface.InvalidateVisual();
        }

        void Scrolled()
        {
            if (_syncing) return;
            ReportGeometry();
            _surface.InvalidateVisual();
            Ui.Input(_code.RaiseScroll);
        }

        internal sealed class Surface : Control
        {
            readonly CodeView _owner;
            bool _caretOn = true;
            readonly DispatcherTimer _blink;
            public Surface(CodeView owner)
            {
                _owner = owner;
                Focusable = true;
                ClipToBounds = true;
                Cursor = new Cursor(StandardCursorType.Ibeam);
                _blink = new DispatcherTimer(TimeSpan.FromMilliseconds(500), DispatcherPriority.Background, (s, e) => { _caretOn = !_caretOn; if (IsFocused) InvalidateVisual(); });
            }
            FastColoredTextBoxNS.FastColoredTextBox Code => _owner._code;

            protected override void OnAttachedToVisualTree(VisualTreeAttachmentEventArgs e) { base.OnAttachedToVisualTree(e); _blink.Start(); }
            protected override void OnDetachedFromVisualTree(VisualTreeAttachmentEventArgs e) { base.OnDetachedFromVisualTree(e); _blink.Stop(); }

            static IBrush Argb(int value) => new SolidColorBrush(Color.FromUInt32(unchecked((uint)value)));

            public override void Render(DrawingContext context)
            {
                var c = Code;
                var o = _owner;
                IBrush back = c.BackColor.IsEmpty ? Brushes.White : new SolidColorBrush(Color.FromRgb(c.BackColor.R, c.BackColor.G, c.BackColor.B));
                context.FillRectangle(back, new Rect(Bounds.Size));
                if (!c.Enabled) context.FillRectangle(new SolidColorBrush(Color.FromArgb(12, 0, 0, 0)), new Rect(Bounds.Size));
                double lineHeight = o.LineHeight, cw = o._charWidth;
                double top = o._vertical.Value, gutter = o.GutterWidth;
                double left = gutter + 3 - o._horizontal.Value;
                int first = Math.Max(0, (int)(top / lineHeight));
                int last = Math.Min(c.LinesCount - 1, (int)((top + Bounds.Height) / lineHeight) + 1);
                var selection = c.Selection;
                var start = selection.Start; var end = selection.End;
                if (start.iLine > end.iLine || start.iLine == end.iLine && start.iChar > end.iChar) { var t = start; start = end; end = t; }
                IBrush foreDefault = new SolidColorBrush(Color.FromRgb(c.ForeColor.R, c.ForeColor.G, c.ForeColor.B));
                IBrush currentLine = c.CurrentLineColor.IsEmpty || c.CurrentLineColor.A == 0 ? null : Ui.Brush(c.CurrentLineColor);
                Color selectionColor = c.SelectionColor.IsEmpty ? Color.FromArgb(60, 0, 0, 255) : Ui.ToColor(c.SelectionColor);
                if (selectionColor.A == 255) selectionColor = Color.FromArgb(60, selectionColor.R, selectionColor.G, selectionColor.B);
                IBrush selectionBrush = new SolidColorBrush(selectionColor);
                var bookmarks = new HashSet<int>(c.Bookmarks.Select(b => b.LineIndex));
                bool emptySelection = start.iLine == end.iLine && start.iChar == end.iChar;
                using (context.PushClip(new Rect(gutter, 0, Math.Max(0, Bounds.Width - gutter), Bounds.Height)))
                    for (int i = first; i <= last; i++)
                    {
                        double y = i * lineHeight - top;
                        if (currentLine != null && i == c.Selection.Start.iLine && emptySelection)
                            context.FillRectangle(currentLine, new Rect(0, y, Bounds.Width, lineHeight));
                        string text = c.GetLineText(i);
                        int[] runs = c.GetLineRuns(i);
                        for (int k = 0; k + 5 < runs.Length; k += 6)
                        {
                            int s = runs[k], n = runs[k + 1], fore = runs[k + 2], bg = runs[k + 3], style = runs[k + 4], marker = runs[k + 5];
                            double x = left + s * cw;
                            var rect = new Rect(x, y, n * cw, lineHeight);
                            if (bg != 0) context.FillRectangle(Argb(bg), rect);
                            if (marker != 0) context.DrawRectangle(Argb(marker), null, rect.Deflate(0.5), 3, 3);
                            if (s >= text.Length) continue;
                            string part = text.Substring(s, Math.Min(n, text.Length - s));
                            var typeface = new Typeface(Look.Monospace, (style & 2) != 0 ? FontStyle.Italic : FontStyle.Normal, (style & 1) != 0 ? FontWeight.Bold : FontWeight.Normal);
                            var formatted = new FormattedText(part, CultureInfo.InvariantCulture, FlowDirection.LeftToRight, typeface, o._fontSize, fore != 0 ? Argb(fore) : foreDefault);
                            if ((style & 4) != 0) formatted.SetTextDecorations(TextDecorations.Underline);
                            context.DrawText(formatted, new Point(x, y + (lineHeight - o._charHeight) / 2));
                        }
                        if (!emptySelection && start.iLine <= i && i <= end.iLine)
                        {
                            int a = i == start.iLine ? start.iChar : 0;
                            int b = i == end.iLine ? end.iChar : text.Length + 1;
                            context.FillRectangle(selectionBrush, new Rect(left + a * cw, y, Math.Max(0, b - a) * cw, lineHeight));
                        }
                    }
                // Gutter: line numbers and bookmarks
                if (gutter > 0)
                {
                    context.FillRectangle(back, new Rect(0, 0, gutter, Bounds.Height));
                    IBrush numbers = c.LineNumberColor.IsEmpty ? Brushes.Teal : Ui.Brush(c.LineNumberColor);
                    IBrush mark = c.BookmarkColor.IsEmpty ? Brushes.PowderBlue : Ui.Brush(c.BookmarkColor);
                    for (int i = first; i <= last; i++)
                    {
                        double y = i * lineHeight - top;
                        if (bookmarks.Contains(i)) context.FillRectangle(mark, new Rect(1, y + 1, 6, lineHeight - 2));
                        var number = new FormattedText((i + 1).ToString(), CultureInfo.InvariantCulture, FlowDirection.LeftToRight, o._typeface, o._fontSize, numbers);
                        context.DrawText(number, new Point(gutter - 6 - number.Width, y + (lineHeight - o._charHeight) / 2));
                    }
                    context.DrawLine(new Pen(c.ServiceLinesColor.IsEmpty ? Brushes.Silver : Ui.Brush(c.ServiceLinesColor)), new Point(gutter + 0.5, 0), new Point(gutter + 0.5, Bounds.Height));
                }
                // Caret
                if (IsFocused && _caretOn && c.CaretVisible)
                {
                    var caret = c.Selection.Start;
                    double x = left + caret.iChar * cw, y = caret.iLine * lineHeight - top;
                    context.FillRectangle(c.CaretColor.IsEmpty ? Brushes.Black : Ui.Brush(c.CaretColor), new Rect(x, y, c.IsReplaceMode ? cw : 2, lineHeight));
                }
            }

            (int, int) Place(PointerEventArgs e) { Point p = e.GetPosition(this); return ((int)p.X, (int)p.Y); }

            protected override void OnPointerPressed(PointerPressedEventArgs e)
            {
                Keyboard.SetModifiers(e.KeyModifiers);
                Focus();
                var (x, y) = Place(e);
                var button = Keyboard.Button(e.GetCurrentPoint(this).Properties.PointerUpdateKind);
                _owner.ReportGeometry();
                if (e.ClickCount == 2) Ui.Input(() => Code.RaiseMouse("doubleclick", WinForms.MouseButtons.Left, 2, x, y));
                else Ui.Input(() => Code.RaiseMouse("down", button, 1, x, y));
                e.Pointer.Capture(this);
                InvalidateVisual();
                e.Handled = true;
            }
            protected override void OnPointerMoved(PointerEventArgs e)
            {
                if (!e.GetCurrentPoint(this).Properties.IsLeftButtonPressed) return;
                var (x, y) = Place(e);
                Ui.Input(() => Code.RaiseMouse("move", WinForms.MouseButtons.Left, 0, x, y));
                InvalidateVisual();
            }
            protected override void OnPointerReleased(PointerReleasedEventArgs e)
            {
                e.Pointer.Capture(null);
                var (x, y) = Place(e);
                var button = Keyboard.Button(e.GetCurrentPoint(this).Properties.PointerUpdateKind);
                Ui.Input(() => { Code.RaiseMouse("up", button, 1, x, y); Code.RaiseMouse("click", button, 1, x, y); });
                if (button == WinForms.MouseButtons.Right && Code.ContextMenuStrip != null) Ui.Input(() => Code.ContextMenuStrip.Show(Code, new System.Drawing.Point(x, y)));
                InvalidateVisual();
            }
            protected override void OnPointerWheelChanged(PointerWheelEventArgs e)
            {
                _owner._vertical.Value = Math.Max(0, Math.Min(_owner._vertical.Maximum, _owner._vertical.Value - e.Delta.Y * 3 * _owner.LineHeight));
                _owner._horizontal.Value = Math.Max(0, Math.Min(_owner._horizontal.Maximum, _owner._horizontal.Value - e.Delta.X * 3 * _owner._charWidth));
                _owner.ReportGeometry();
                Ui.Input(Code.RaiseScroll);
                InvalidateVisual();
                e.Handled = true;
            }

            protected override void OnKeyDown(KeyEventArgs e)
            {
                // Tab is an editor key (AcceptsTab), not a focus move; Ctrl+key gives no character
                if (e.Key == Key.Tab && !Code.AcceptsTab) return;
                WinForms.Keys keys = Keyboard.Keys(e);
                Keyboard.SetModifiers(e.KeyModifiers);
                _caretOn = true;
                // A key with a character arrives as text (TextInput) with its key; keys without one arrive here
                if ((e.KeyModifiers & (KeyModifiers.Control | KeyModifiers.Meta)) == 0 && e.KeySymbol is { Length: 1 } s && !char.IsControl(s[0])) { _pendingKeys = keys; return; }
                Ui.Input(() => { WinForms.KeyboardLayout.SetCurrent(keys, ""); Code.RaiseKeyInput(keys, ""); });
                Ui.Flush();
                _owner.ScrollToCaret();
                e.Handled = true;
            }
            WinForms.Keys _pendingKeys;
            protected override void OnTextInput(TextInputEventArgs e)
            {
                if (string.IsNullOrEmpty(e.Text)) return;
                WinForms.Keys keys = _pendingKeys;
                _pendingKeys = WinForms.Keys.None;
                string text = e.Text;
                Ui.Input(() => { WinForms.KeyboardLayout.SetCurrent(keys, text); Code.RaiseKeyInput(keys, text); });
                Ui.Flush();
                _owner.ScrollToCaret();
                e.Handled = true;
            }
            protected override void OnGotFocus(GotFocusEventArgs e) { base.OnGotFocus(e); InvalidateVisual(); }
            protected override void OnLostFocus(Avalonia.Interactivity.RoutedEventArgs e)
            {
                base.OnLostFocus(e);
                InvalidateVisual();
            }
        }
    }

    /// <summary>The FCTB AutocompleteMenu of whichever editor the model opens it for: the visible items under the
    /// fragment; the focussed item is the model's.</summary>
    internal static class Autocomplete
    {
        internal static readonly Dictionary<FastColoredTextBoxNS.FastColoredTextBox, CodeView> Editors = new Dictionary<FastColoredTextBoxNS.FastColoredTextBox, CodeView>();
        static bool s_installed;
        static Popup s_popup;
        static ListBox s_list;
        static FastColoredTextBoxNS.AutocompleteMenu s_menu;

        internal static void Install()
        {
            if (s_installed) return;
            s_installed = true;
            FastColoredTextBoxNS.AutocompleteMenu.Changed += Changed;
        }

        static void Changed(FastColoredTextBoxNS.AutocompleteMenu menu, string kind) => Dispatcher.UIThread.Post(() => Apply(menu, kind));

        static void Apply(FastColoredTextBoxNS.AutocompleteMenu menu, string kind)
        {
            if (!Editors.TryGetValue(menu.TextBox, out CodeView editor)) return;
            if (kind == "Close") { if (s_menu == menu && s_popup != null) s_popup.IsOpen = false; return; }
            if (s_popup == null)
            {
                s_list = new ListBox { FontFamily = Look.Monospace, FontSize = 12, MaxHeight = 180, MinWidth = 120, Focusable = false, Background = Brushes.White };
                s_list.AddHandler(InputElement.PointerPressedEvent, (s, e) =>
                {
                    int index = s_list.SelectedIndex;
                    var m = s_menu;
                    if (index >= 0 && m != null) Ui.Input(() => m.Items.UserClickItem(index, e.ClickCount >= 2));
                }, Avalonia.Interactivity.RoutingStrategies.Bubble, true);
                s_popup = new Popup { Child = new Border { Child = s_list, BorderBrush = Look.Frame, BorderThickness = new Thickness(1) }, IsLightDismissEnabled = false,
                                      Placement = PlacementMode.AnchorAndGravity, PlacementAnchor = Avalonia.Controls.Primitives.PopupPositioning.PopupAnchor.TopLeft,
                                      PlacementGravity = Avalonia.Controls.Primitives.PopupPositioning.PopupGravity.BottomRight };
            }
            s_menu = menu;
            var items = menu.Items.VisibleItems.Select(i => i.ToString()).ToList();
            if (!(s_list.ItemsSource is List<string> shown && shown.SequenceEqual(items))) s_list.ItemsSource = items;
            int focussed = menu.Items.FocussedItemIndex;
            s_list.SelectedIndex = focussed >= 0 && focussed < items.Count ? focussed : -1;
            if (s_list.SelectedIndex >= 0) s_list.ScrollIntoView(s_list.SelectedIndex);
            var location = menu.Location;
            s_popup.PlacementTarget = (Control)editor.SurfaceVisual;
            s_popup.PlacementRect = new Rect(location.X, location.Y + editor.CharHeight + 2, 1, 1);
            if (s_popup.Parent == null && TopLevel.GetTopLevel(editor) is Window window && window.Content is Panel panel) panel.Children.Add(s_popup);
            s_popup.IsOpen = true;
        }
    }
}
